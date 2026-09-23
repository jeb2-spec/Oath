#!/usr/bin/env python3
"""House Financial Disclosure adapter, index layer. NEXT.md Phase 3 I.1a.

Reads two captures written by `fetch.py` and writes canonical rows:

  MemberData.xml   the Clerk's roster. Authoritative for *who holds a seat*.
  <year>FD.xml     the Clerk's filing index. Authoritative for *what was filed*.

It writes offices, officeholders, and filings. It writes no transactions and no
holdings, because the index carries neither; those live inside the documents and
are I.1b. It therefore produces no Findings, which is the point of shipping it
on its own.

The join is the whole problem. The filing index carries no person identifier, so
a filing reaches an officeholder only through a name and a state-district. Two
measured facts about the 2025 index shape the rule below:

  1. Most of the index is not officeholders. Of 2,939 rows, 1,718 sit at a real
     seat under a surname that is not the member's: they are candidates for that
     seat. SUBJECTS.md §3 excludes candidates, so the majority of the file is out
     of scope and must be dropped rather than ingested.
  2. Seats move and names differ. Two sitting members swapped districts between
     the roster and the index; four carry diacritics the index drops; four more
     have multi-part surnames the two sources split differently.

So the rule matches on the *name* and treats the seat as corroboration, never the
other way around. A row is accepted only when the roster's name tokens equal the
index's or are a subset of them. Anything weaker is written to `data/rejected/`
with the reason, including the case where a surname is unique in the roster but
the given names disagree. That case is almost certainly the same person, and the
adapter still refuses it, because "almost certainly" is not the standard the
Charter's fourth vow sets. A human adjudicates a rejected row; the adapter never
guesses one into the register.

    python src/adapters/house-fd/build.py --year 2025
    python src/adapters/house-fd/build.py --year 2025 --dry-run
"""

from __future__ import annotations

import argparse
import collections
import hashlib
import json
import sys
import unicodedata
import xml.etree.ElementTree as ET
from datetime import date, datetime
from pathlib import Path

CACHE = Path("data/cache/house-fd")
CLERK = "https://disclosures-clerk.house.gov/public_disc"

# Human decisions about which held row belongs to which officeholder, one per line,
# each citing its evidence. Lives beside the adapter, not under data/, because it is
# an input a person writes; its hash is carried into every run record it shaped.
ADJUDICATIONS = Path("src/adapters/house-fd/adjudications.ndjson")

# The 119th Congress convened on this date under the Twentieth Amendment. It is the
# term start of the seat, which is not the same as the day a given member was sworn.
CONGRESS_START = {119: "2025-01-03"}

# The index carries a one-letter code whose meanings no Clerk page defines; see
# SOURCES.md F.1. Only P is mapped, and only because the Clerk itself files those
# documents under a ptr-pdfs path while every other code is served from
# financial-pdfs. Every other code is carried verbatim and interpreted nowhere.
PTR_CODE = "P"

# Dropped before comparing names: honorifics and generational suffixes, which the
# two sources supply inconsistently.
NOISE = {"jr", "sr", "ii", "iii", "iv", "v", "mr", "mrs", "ms", "miss", "dr", "hon"}


def fold(text: str) -> str:
    """Lowercase, strip diacritics, keep letters. Sánchez and Sanchez fold alike."""
    stripped = unicodedata.normalize("NFKD", text)
    return "".join(c for c in stripped.lower() if c.isalpha())


def tokens(*parts: str) -> frozenset[str]:
    """The comparable name tokens of a person, honorifics and suffixes removed."""
    out = set()
    for part in parts:
        for raw in part.replace(",", " ").replace(".", " ").replace("-", " ").split():
            token = fold(raw)
            if token and token not in NOISE:
                out.add(token)
    return frozenset(out)


def text_of(node: ET.Element | None, tag: str) -> str:
    """The text of a child element, or the empty string when absent or empty."""
    if node is None:
        return ""
    child = node.find(tag)
    return (child.text or "").strip() if child is not None else ""


def read_capture(name: str) -> dict:
    """What fetch.py recorded about one retrieval: its url, time, and hash."""
    manifest = json.loads((CACHE / "capture.json").read_text(encoding="utf-8"))
    if name not in manifest:
        raise SystemExit(f"{name} is not in {CACHE / 'capture.json'}; run fetch.py first")
    return manifest[name]


def load_roster(path: Path) -> tuple[list[dict], list[dict]]:
    """Seats and the people in them. A seat with no member data is a vacancy."""
    root = ET.parse(path).getroot()
    congress = int(text_of(root.find("title-info"), "congress-num"))
    seats, people = [], []
    for member in root.findall("./members/member"):
        seat = text_of(member, "statedistrict")
        info = member.find("member-info")
        bioguide = text_of(info, "bioguideID")
        kind = text_of(info, "district")
        title = (
            kind
            if kind in ("Delegate", "Resident Commissioner")
            else "United States Representative"
        )
        seats.append({"seat": seat, "congress": congress, "vacant": not bioguide, "title": title})
        if not bioguide:
            continue
        people.append(
            {
                "seat": seat,
                "congress": congress,
                "bioguide": bioguide,
                "last": text_of(info, "lastname"),
                "first": text_of(info, "firstname"),
                "middle": text_of(info, "middlename"),
                "official_name": text_of(info, "official-name"),
                "namelist": text_of(info, "namelist"),
                "party": text_of(info, "party"),
                "sworn": (
                    sworn.get("date", "")
                    if (sworn := (info.find("sworn-date") if info is not None else None))
                    is not None
                    else ""
                ),
            }
        )
    return seats, people


def load_index(path: Path) -> list[dict]:
    """Every row of the Clerk's filing index, verbatim."""
    root = ET.parse(path).getroot()
    rows = []
    for member in root.findall("Member"):
        rows.append(
            {
                "last": text_of(member, "Last"),
                "first": text_of(member, "First"),
                "suffix": text_of(member, "Suffix"),
                "filing_type": text_of(member, "FilingType"),
                "state_dst": text_of(member, "StateDst"),
                "year": text_of(member, "Year"),
                "filing_date": text_of(member, "FilingDate"),
                "doc_id": text_of(member, "DocID"),
            }
        )
    return rows


def match(row: dict, people: list[dict], by_surname: dict) -> tuple[dict | None, str]:
    """Return the officeholder this filing belongs to, or None and the reason why not."""
    row_tokens = tokens(row["last"], row["first"])
    if not row_tokens:
        return None, "the index row carries no usable name"
    exact = [p for p in people if p["_tokens"] == row_tokens]
    if len(exact) == 1:
        return exact[0], "name tokens match the roster exactly"
    subset = [p for p in people if p["_tokens"] <= row_tokens]
    if len(subset) == 1:
        return subset[0], "the roster's name tokens are contained in the index row's"
    if len(exact) > 1 or len(subset) > 1:
        return None, "the name matches more than one sitting member"
    surname = fold(row["last"].split()[0]) if row["last"].split() else ""
    near = by_surname.get(surname, [])
    if len(near) == 1:
        held = near[0]
        return None, (
            f"surname matches exactly one sitting member ({held['namelist']}, "
            f"{held['seat']}) but the given names differ; a human decides this one"
        )
    return None, "no sitting member has this name; the row is a candidate or a former member"


def iso(us_date: str) -> str | None:
    """M/D/YYYY as the Clerk writes it, to an ISO date. None when it will not parse."""
    try:
        return datetime.strptime(us_date.strip(), "%m/%d/%Y").date().isoformat()
    except ValueError:
        return None


def doc_url(row: dict) -> str:
    """Where the Clerk serves this filing's document."""
    folder = "ptr-pdfs" if row["filing_type"] == PTR_CODE else "financial-pdfs"
    return f"{CLERK}/{folder}/{row['year']}/{row['doc_id']}.pdf"


def canonical(obj: dict) -> str:
    """One NDJSON line, stable across runs and platforms."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n"


def capture_key(index_capture: dict, roster_capture: dict) -> str:
    """Twelve hex characters naming this pair of captures. Same bytes in, same key out."""
    joined = f"{index_capture['sha256']}\n{roster_capture['sha256']}".encode()
    return hashlib.sha256(joined).hexdigest()[:12]


def load_adjudications(path: Path) -> tuple[dict[str, dict], str | None]:
    """Human decisions keyed by DocID, and the file's hash for the run record.

    Each line carries doc_id, officeholder_id, evidence_url, decided_by and decided_at,
    and may carry a note. A line missing any of the five stops the build: a decision
    without its evidence is not a decision the register can carry.
    """
    if not path.is_file() or path.stat().st_size == 0:
        return {}, None
    required = ("doc_id", "officeholder_id", "evidence_url", "decided_by", "decided_at")
    raw = path.read_bytes()
    decisions: dict[str, dict] = {}
    for number, line in enumerate(raw.decode("utf-8").splitlines(), 1):
        if not line.strip():
            continue
        row = json.loads(line)
        missing = [key for key in required if not row.get(key)]
        if missing:
            raise SystemExit(f"{path}:{number}: adjudication lacks {', '.join(missing)}")
        decisions[str(row["doc_id"])] = row
    return decisions, hashlib.sha256(raw).hexdigest()


def build(year: int, dry_run: bool = False) -> int:
    roster_capture = read_capture("MemberData.xml")
    index_capture = read_capture(f"{year}FD.zip")
    seats, people = load_roster(CACHE / "MemberData.xml")
    rows = load_index(CACHE / f"{year}FD.xml")
    adjudications, adjudications_hash = load_adjudications(ADJUDICATIONS)

    for person in people:
        person["_tokens"] = tokens(person["last"], person["first"])
    by_surname: dict[str, list[dict]] = collections.defaultdict(list)
    for person in people:
        by_surname[fold(person["last"].split()[0])].append(person)

    roster_source = {
        "url": roster_capture["url"],
        "retrieved_at": roster_capture["retrieved_at"],
        "content_hash": roster_capture["sha256"],
    }

    offices, office_of_seat = [], {}
    for seat in seats:
        term_start = CONGRESS_START.get(seat["congress"])
        if term_start is None:
            raise SystemExit(f"no recorded start date for the {seat['congress']}th Congress")
        office = {
            "id": f"of:us:house-{seat['seat'].lower()}:{term_start[:4]}",
            "jurisdiction": "us:federal",
            "branch": "legislative",
            "chamber": "house",
            "state": seat["seat"][:2],
            "district": seat["seat"][2:],
            "seat": seat["seat"],
            "title": seat["title"],
            "term_start": term_start,
            "term_end": None,
        }
        offices.append(office)
        office_of_seat[seat["seat"]] = office

    officeholders, holder_of_bioguide, person_of_id = [], {}, {}
    for person in people:
        office = office_of_seat[person["seat"]]
        sworn = person["sworn"]
        holder = {
            "id": f"oh:us:house:{person['bioguide'].lower()}",
            "legal_name": person["official_name"] or f"{person['first']} {person['last']}".strip(),
            "common_name": person["namelist"] or None,
            "party": person["party"] or None,
            "offices": [office],
            "biographical_ids": {
                "bioguide_id": person["bioguide"],
                "fec_id": None,
                "opensecrets_id": None,
                "ballotpedia_slug": None,
            },
            "source": roster_source,
            "notes": (
                f"Sworn {date(int(sworn[:4]), int(sworn[4:6]), int(sworn[6:])).isoformat()}. "
                if len(sworn) == 8
                else ""
            )
            + "Presence in the register is not evidence of wrongdoing.",
        }
        officeholders.append(holder)
        holder_of_bioguide[person["bioguide"]] = holder
        person_of_id[holder["id"]] = person

    filings, rejected, adjudicated = [], [], 0
    for row in rows:
        person, reason = match(row, people, by_surname)
        confidence = None  # an index row; the document itself has not been read
        decided = adjudications.get(row["doc_id"]) if person is None else None
        if decided is not None:
            person = person_of_id.get(decided["officeholder_id"])
            if person is None:
                raise SystemExit(
                    f"adjudication for DocID {row['doc_id']} names "
                    f"{decided['officeholder_id']}, which is not in the roster"
                )
            confidence, adjudicated = "manual", adjudicated + 1
        filed_at = iso(row["filing_date"])
        if person is None or filed_at is None:
            rejected.append(
                {
                    "adapter": "house-fd",
                    "reason": reason if person is None else "the filing date will not parse",
                    "source_row": row,
                    "source": {
                        "url": index_capture["url"],
                        "retrieved_at": index_capture["retrieved_at"],
                        "content_hash": index_capture["sha256"],
                    },
                }
            )
            continue
        holder = holder_of_bioguide[person["bioguide"]]
        filings.append(
            {
                "id": f"fl:house-clerk:{row['filing_type'] or 'none'}:{row['doc_id']}",
                "officeholder_id": holder["id"],
                "office_id": office_of_seat[person["seat"]]["id"],
                "form_type": "House-PTR" if row["filing_type"] == PTR_CODE else "other",
                "source_form_code": row["filing_type"] or None,
                "filed_at": filed_at,
                "covers_period_start": None,
                "covers_period_end": None,
                "amends": None,
                "source": {
                    "url": doc_url(row),
                    "retrieved_at": index_capture["retrieved_at"],
                    "content_hash": None,
                },
                "extraction_confidence": confidence,
            }
        )

    filings.sort(key=lambda f: (f["officeholder_id"], f["filed_at"], f["id"]))
    officeholders.sort(key=lambda h: h["id"])
    offices.sort(key=lambda o: o["id"])

    attributed = len({f["officeholder_id"] for f in filings})
    quiet = len(people) - attributed
    reasons = dict(collections.Counter(r["reason"].split(" (")[0] for r in rejected))
    print(
        f"roster        {len(seats)} seats, {len(people)} filled, {len(seats) - len(people)} vacant"
    )
    print(f"index         {len(rows)} rows for {year}")
    print(f"accepted      {len(filings)} filings against {attributed} officeholders")
    if adjudicated:
        print(f"              {adjudicated} of them by a person's adjudication, citing evidence")
    print(f"rejected      {len(rejected)} rows")
    for reason, count in sorted(reasons.items(), key=lambda item: -item[1]):
        print(f"              {count:5d}  {reason}")
    print(f"quiet         {quiet} sitting members have no filing in this index")

    if dry_run:
        print("\ndry run: nothing written")
        return 0

    write(Path("data/offices.ndjson"), offices)
    write(Path("data/officeholders.ndjson"), officeholders)
    write(Path("data/filings.ndjson"), filings)
    # Named for the captures the rows came from, never for the day the build ran: the
    # same bytes rebuild the same file, so an unchanged source is an unchanged tree and
    # the seal holds. Rejections from earlier captures live in git history.
    key = capture_key(index_capture, roster_capture)
    rejected_dir = Path("data/rejected/house-fd")
    rejected_dir.mkdir(parents=True, exist_ok=True)
    for old in rejected_dir.glob(f"{year}-*.ndjson"):
        if old.name != f"{year}-{key}.ndjson":
            old.unlink()
    write(rejected_dir / f"{year}-{key}.ndjson", rejected)
    run = {
        "adapter": "house-fd",
        "year": year,
        "capture_key": key,
        "sources": [
            {
                "name": name,
                "url": capture["url"],
                "retrieved_at": capture["retrieved_at"],
                "sha256": capture["sha256"],
                "last_modified": capture.get("last_modified"),
            }
            for name, capture in (
                ("MemberData.xml", roster_capture),
                (f"{year}FD.zip", index_capture),
            )
        ],
        "adjudications_sha256": adjudications_hash,
        "counts": {
            "seats": len(seats),
            "filled": len(people),
            "vacant": len(seats) - len(people),
            "index_rows": len(rows),
            "accepted": len(filings),
            "adjudicated": adjudicated,
            "officeholders_with_a_filing": attributed,
            "quiet": quiet,
            "rejected": len(rejected),
        },
        "rejected_by_reason": reasons,
    }
    write(Path(f"data/adapter-runs/house-fd-{year}-{key}.ndjson"), [run])
    print("\nwrote data/offices.ndjson, data/officeholders.ndjson, data/filings.ndjson")
    print(f"wrote data/rejected/house-fd/{year}-{key}.ndjson")
    print(f"wrote data/adapter-runs/house-fd-{year}-{key}.ndjson")
    print("Re-seal in this commit: python tools/seal.py --build <id> --built-at <time>")
    return 0


def write(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(canonical(row))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--year", type=int, required=True, help="filing year, e.g. 2025")
    parser.add_argument("--dry-run", action="store_true", help="report and write nothing")
    parser.add_argument(
        "--capture-key",
        action="store_true",
        help="print the key of the recorded captures and exit; same bytes, same key",
    )
    args = parser.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if args.capture_key:
        print(capture_key(read_capture(f"{args.year}FD.zip"), read_capture("MemberData.xml")))
        return 0
    return build(args.year, args.dry_run)


if __name__ == "__main__":
    sys.exit(main())
