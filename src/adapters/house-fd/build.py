#!/usr/bin/env python3
"""House Financial Disclosure adapter, index layer. NEXT.md Phase 3 I.1a.

Reads two captures written by `fetch.py` and writes canonical rows:

  MemberData.xml   the Clerk's roster. Authoritative for *who holds a seat*.
  <year>FD.xml     the Clerk's filing index. Authoritative for *what was filed*.

It writes offices, officeholders and filings from the two captures, and, from the
documents `documents.py` captured, the transactions the reports list (I.1b). It
writes no holdings and produces no Findings; no Signal is defined.

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
with the reason, including the case where a surname matches a sitting member but
the given names disagree. That case is almost certainly the same person, and the
adapter still does not accept it on the name, because "almost certainly" is not
the standard the Charter's fourth vow sets. Where the index places such a row at
the member's own seat, the Clerk's document decides it by its printed header
(`attribute_by_header`); what the document cannot settle, a human adjudicates. The
adapter never guesses a row into the register.

    python src/adapters/house-fd/build.py --year 2025
    python src/adapters/house-fd/build.py --year 2025 --dry-run
"""

from __future__ import annotations

import argparse
import collections
import hashlib
import importlib.util
import json
import re
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

# What documents.py captured: the bytes and headers of each filing's document, by DocID.
# When a filing's document is here, the build reads it, checks it against the roster, and
# writes its transactions; when it is not, the filing stays an index row.
DOCS = Path("data/cache/house-fd/docs")
DOCS_MANIFEST = DOCS / "captures.json"


def term_start(congress: int) -> str:
    """The day the seats' terms of a Congress begin: the term start of an office, which is
    not the day a given member was sworn. Under the Twentieth Amendment, section 1, the
    terms of Representatives end at noon on 3 January and their successors' terms then
    begin, so from the 74th Congress (1935) the nth Congress's terms begin on 3 January of
    1787 + 2n: the 119th on 2025-01-03, the 120th on 2027-01-03. A Congress may convene on
    another day; its terms do not move."""
    if congress < 74:
        raise SystemExit(f"the {congress}th Congress predates the Twentieth Amendment's terms")
    return f"{1787 + 2 * congress}-01-03"


def congress_of(year: int) -> int:
    """The Congress whose terms run through a filing year: the 119th for 2025 and 2026. A
    year's first two days belong to the Congress before; an index is a year's, and the
    register takes the Congress that holds all but those two days."""
    return (year - 1787) // 2


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


HELD_SUFFIX = "; a human decides this one"


def surname_neighbour(row: dict, by_surname: dict) -> dict | None:
    """The sitting member the row's surname points at, or None.

    A member is near when every token of the roster surname is in the row's surname, so
    a shared particle (De, Van) is not a shared name. The one near member; or, when
    several are near (Johnson, Davis), the one of them who holds the seat the row names.
    The seat corroborates the pick and the document then decides the row; the name
    alone decides nothing here.
    """
    parts = row["last"].split()
    if not parts:
        return None
    row_tokens = tokens(row["last"])
    near = [p for p in by_surname.get(fold(parts[0]), []) if tokens(p["last"]) <= row_tokens]
    if len(near) == 1:
        return near[0]
    at_seat = [p for p in near if p["seat"] == row.get("state_dst")]
    return at_seat[0] if len(at_seat) == 1 else None


def sworn_iso(person: dict) -> str | None:
    """The roster's sworn date as ISO, or None when the roster carries none."""
    sworn = person.get("sworn") or ""
    return f"{sworn[:4]}-{sworn[4:6]}-{sworn[6:]}" if len(sworn) == 8 else None


def attribute_by_header(
    head: dict, row: dict, member: dict, filed_at: str | None
) -> tuple[str, str]:
    """Whether the document's own header settles a held row at the member's own seat.

    The index placed the row at the member's seat and the surnames agree; the given
    names do not. The document settles it when it prints Status Member, that seat, this
    row's DocID as its Filing ID, and a filer name carrying the roster surname, and the
    index dates the filing no earlier than the swearing-in the roster records for this
    Congress. Returns (status, clause): status is "attributed" or "held"; the clause is
    what the document printed, for the filing row's notes or the held row's reason. The
    register never says who a filer is not; a document that prints another status holds
    the row with that status quoted, and a person decides it.
    """
    if not head["filing_id"]:
        return (
            "held",
            "the document carries no Filing ID line (scanned paper, or a form that prints "
            "none) and cannot confirm the filer",
        )
    if head["filing_id"] != str(row["doc_id"]):
        return (
            "held",
            f"the document prints Filing ID {head['filing_id']}, not this row's DocID",
        )
    if head["status"] != "Member":
        return (
            "held",
            f"the document prints Status {head['status']!r} for the filer named "
            f"{head['name']!r} at {head['seat']}, not Member; the header does not attribute "
            "the row to the seat's member",
        )
    if head["seat"] != member["seat"]:
        return (
            "held",
            f"the document prints State/District {head['seat']}, not the member's {member['seat']}",
        )
    if not tokens(member["last"]) <= tokens(head["name"]):
        return (
            "held",
            f"the document prints the filer as {head['name']!r}, which does not carry the "
            "roster surname",
        )
    sworn = sworn_iso(member)
    if filed_at and sworn and filed_at < sworn:
        return (
            "held",
            f"the index dates the filing {filed_at}, before the swearing-in for this Congress "
            f"that the roster records ({sworn}); the roster does not say who held the seat "
            "before that date, so the register does not",
        )
    return (
        "attributed",
        f"the document prints {head['name']!r}, Status Member, State/District "
        f"{head['seat']}, Filing ID {head['filing_id']}",
    )


def collapse_duplicates(
    rows: list[dict], rejected: list[dict], index_capture: dict
) -> tuple[list[dict], dict[str, int]]:
    """One row per DocID. The Clerk's index has listed a DocID twice, identically; such a
    row is carried once and says so. A DocID listed more than once with differing rows is
    carried not at all, every copy set aside with the reason."""
    groups: dict[str, list[dict]] = {}
    for row in rows:
        groups.setdefault(row["doc_id"], []).append(row)
    kept, duplicated = [], {}
    for doc_id, group in groups.items():
        if len(group) == 1:
            kept.append(group[0])
        elif all(g == group[0] for g in group):
            kept.append(group[0])
            duplicated[doc_id] = len(group)
        else:
            for g in group:
                rejected.append(
                    {
                        "adapter": "house-fd",
                        "reason": (
                            "the Clerk's index lists this DocID more than once with differing "
                            "rows; the register carries none of them"
                        ),
                        "source_row": g,
                        "source": {
                            "url": index_capture["url"],
                            "retrieved_at": index_capture["retrieved_at"],
                            "content_hash": index_capture["sha256"],
                        },
                    }
                )
    return kept, duplicated


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
    held = surname_neighbour(row, by_surname)
    if held is not None:
        return None, (
            f"surname matches a sitting member ({held['namelist']}, {held['seat']}) but the "
            f"given names differ{HELD_SUFFIX}"
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


def capture_key(
    index_capture: dict, roster_capture: dict | None, docs_hash: str | None = None
) -> str:
    """Twelve hex characters naming these captures. Same bytes in, same key out.

    The document manifest joins the key when it exists, so a week that captured new
    documents is a changed record even when the index and roster did not move. A closed
    year's rows owe nothing to the roster or the documents, so its key names the index
    alone, and a roster that moves on does not rebuild a year it cannot change.
    """
    joined = index_capture["sha256"]
    if roster_capture is not None:
        joined += f"\n{roster_capture['sha256']}"
    if docs_hash:
        joined += f"\n{docs_hash}"
    return hashlib.sha256(joined.encode()).hexdigest()[:12]


def load_docs_manifest() -> tuple[dict, str | None]:
    """The captured documents by DocID, and the manifest's hash; empty when none captured."""
    if not DOCS_MANIFEST.is_file():
        return {}, None
    raw = DOCS_MANIFEST.read_bytes()
    return json.loads(raw.decode("utf-8")), hashlib.sha256(raw).hexdigest()


def load_ptr():
    """The transaction-report reader beside this file, loaded by path so tests can too."""
    spec = importlib.util.spec_from_file_location(
        "house_fd_ptr", Path(__file__).with_name("ptr.py")
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


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


# ---- the published register, an input to every build --------------------------------------
#
# A row the register has published is a fact it recorded from a primary source, and it
# stays (CHARTER Vow V; INVARIANTS §14). So a build reads the published rows first and
# weighs them against what it derives from the captures:
#
#   - where the build re-derives a published row, the derived row stands, and
#     tools/check-removals.py holds it to every fact the published row carries;
#   - a published row the build does not re-derive is carried exactly as published;
#   - where the build read the source and the source no longer lists the row, that is a
#     new fact, written as its own row in data/changes.ndjson with the capture that shows
#     it ("not listed", and "listed again" should the source list it once more); where the
#     build did not read the source, nothing was observed and nothing is written;
#   - a published attribution stands: the join may attribute a new row, never move a
#     published one, and a build that would move one refuses.
#
# So a Member who leaves office keeps the rows the register published, and a page; a
# filing the Clerk's index stops listing stays, with the change shown beside it; and a
# filing year whose Congress has ended is carried as published, never re-derived from the
# next Congress's roster, whose swearing-in dates would put every transaction before them.

PUBLISHED = {
    "offices": Path("data/offices.ndjson"),
    "officeholders": Path("data/officeholders.ndjson"),
    "filings": Path("data/filings.ndjson"),
    "transactions": Path("data/transactions.ndjson"),
    "changes": Path("data/changes.ndjson"),
}
NOT_LISTED, LISTED_AGAIN = "not listed", "listed again"
YEAR_IN_URL = re.compile(rf"^{re.escape(CLERK)}/(?:ptr-pdfs|financial-pdfs)/(\d{{4}})/\w+\.pdf$")


def ordinal(n: int) -> str:
    suffix = "th" if 11 <= n % 100 <= 13 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


def read_published() -> dict[str, list[dict]]:
    """The rows the register holds before this build, by file; empty where there are none."""
    return {
        name: (
            [json.loads(line) for line in path.read_text("utf-8").splitlines() if line.strip()]
            if path.is_file()
            else []
        )
        for name, path in PUBLISHED.items()
    }


def index_year(filing: dict) -> int:
    """The index a filing row came from, as the Clerk's own URL for its document names it
    (`doc_url`; SOURCES.md F.1). A build refuses a row whose URL does not."""
    found = YEAR_IN_URL.match(filing["source"]["url"])
    if found is None:
        raise SystemExit(
            f"refusing to build: {filing['id']} has a source URL that does not name the "
            "Clerk's index year, so this build cannot tell which year's row it is"
        )
    return int(found.group(1))


def doc_of(row_id: str) -> str:
    """The DocID at the end of a filing id, or of a transaction's filing id."""
    return row_id.rsplit(":", 1)[1]


def latest_changes(changes: list[dict]) -> dict[str, dict]:
    """Each row's latest recorded change, by the time of the capture that showed it."""
    latest: dict[str, dict] = {}
    for change in sorted(changes, key=lambda c: (c["capture"]["retrieved_at"], c["id"])):
        latest[change["row_id"]] = change
    return latest


def change_row(row_id: str, rows: str, change: str, capture: dict) -> dict:
    """A change the source made to a published row, with the capture that shows it."""
    return {
        "id": f"ch:{change.replace(' ', '-')}:{row_id}:{capture['retrieved_at']}",
        "row_id": row_id,
        "rows": rows,
        "change": change,
        "capture": {
            "url": capture["url"],
            "retrieved_at": capture["retrieved_at"],
            "content_hash": capture["content_hash"],
        },
    }


def carry_forward(
    published: dict[str, list[dict]],
    built: dict[str, list[dict]],
    year: int,
    observed: dict,
) -> tuple[dict[str, list[dict]], list[dict], dict[str, int]]:
    """The rows to write, the change rows this build adds, and what it carried, counted.

    `built` is what this build derived from its captures, by file. `observed` is what it
    read, as source blocks ({url, retrieved_at, content_hash}): "roster", when it read a
    roster of the filing year's Congress, else None; "index", and "index_doc_ids", every
    DocID the index lists; "documents", every document it read, by DocID. Filings and
    transactions of other years are untouched.
    """
    latest = latest_changes(published["changes"])
    changes: list[dict] = []

    def record(row_id: str, rows: str, listed: bool, capture: dict) -> None:
        was = latest.get(row_id, {}).get("change")
        if not listed and was != NOT_LISTED:
            changes.append(change_row(row_id, rows, NOT_LISTED, capture))
        elif listed and was == NOT_LISTED:
            changes.append(change_row(row_id, rows, LISTED_AGAIN, capture))

    out: dict[str, list[dict]] = {}
    carried = {"offices": 0, "officeholders": 0, "filings": 0, "transactions": 0}

    for name in ("offices", "officeholders"):
        made = {row["id"] for row in built[name]}
        kept = [row for row in published[name] if row["id"] not in made]
        out[name] = built[name] + kept
        carried[name] = len(kept)
        if name == "officeholders" and observed["roster"] is not None:
            for row in kept:
                record(row["id"], name, False, observed["roster"])
            for row in built[name]:
                record(row["id"], name, True, observed["roster"])

    others = [row for row in published["filings"] if index_year(row) != year]
    mine = {row["id"]: row for row in published["filings"] if index_year(row) == year}
    filings = []
    for row in built["filings"]:
        was = mine.get(row["id"])
        if was is None:
            filings.append(row)
            continue
        if (was["officeholder_id"], was["office_id"]) != (row["officeholder_id"], row["office_id"]):
            raise SystemExit(
                f"refusing to build: {row['id']} is published as {was['officeholder_id']}'s "
                f"({was['office_id']}), and this build's join attributes it to "
                f"{row['officeholder_id']} ({row['office_id']}). The join never moves a "
                "published attribution; a person does, with the evidence, as a correction."
            )
        read_before = was.get("extraction_confidence") or was["source"].get("content_hash")
        if read_before and doc_of(row["id"]) not in observed["documents"]:
            # This build did not read the document behind a row an earlier build read. The
            # published row stands, with the transactions read from it.
            filings.append(was)
        else:
            filings.append(row)
    made = {row["id"] for row in built["filings"]}
    kept = [row for filing_id, row in mine.items() if filing_id not in made]
    carried["filings"] = len(kept)
    filings += kept
    for row in filings:
        listed = doc_of(row["id"]) in observed["index_doc_ids"]
        record(row["id"], "filings", listed, observed["index"])
    out["filings"] = filings + others

    this_year = {row["id"] for row in filings}
    made = {row["id"] for row in built["transactions"]}
    kept = [row for row in published["transactions"] if row["id"] not in made]
    for row in kept:
        if row["filing_id"] not in this_year:
            continue
        carried["transactions"] += 1
        document = observed["documents"].get(doc_of(row["filing_id"]))
        if document is not None:
            record(row["id"], "transactions", False, document)
    for row in built["transactions"]:
        record(row["id"], "transactions", True, observed["documents"][doc_of(row["filing_id"])])
    out["transactions"] = built["transactions"] + kept
    return out, changes, carried


def index_people(people: list[dict]) -> dict[str, list[dict]]:
    """Give each roster person their comparable tokens and index them by surname word."""
    by_surname: dict[str, list[dict]] = collections.defaultdict(list)
    for person in people:
        person["_tokens"] = tokens(person["last"], person["first"])
        by_surname[fold(person["last"].split()[0])].append(person)
    return by_surname


def wanted_from_rows(rows: list[dict], people: list[dict]) -> list[dict]:
    """Which documents a build will want, from the index and the roster alone.

    The document behind every row the name join attributes (the capture stage filters
    those by code), and the document behind every row held at a member's own seat
    under the member's surname, whatever its code, because the header decides those.
    Reads no canonical row, so the capture stage stays pure with respect to the
    register and a build is never a cycle behind its own source. One entry per DocID.
    """
    by_surname = index_people(people)
    out: dict[str, dict] = {}
    for row in rows:
        if row["doc_id"] in out:
            continue
        person, reason = match(row, people, by_surname)
        if person is not None:
            why, seat = "attributed", person["seat"]
        else:
            held = surname_neighbour(row, by_surname) if reason.endswith(HELD_SUFFIX) else None
            if held is None or row["state_dst"] != held["seat"]:
                continue
            why, seat = "held at the member's own seat", held["seat"]
        out[row["doc_id"]] = {
            "doc_id": row["doc_id"],
            "url": doc_url(row),
            "code": row["filing_type"],
            "seat": seat,
            "why": why,
        }
    return list(out.values())


def wanted_documents(year: int) -> list[dict]:
    """`wanted_from_rows` over the captures on disk. What `documents.py` asks. None for a
    closed year, whose rows are carried as published and whose documents are not read."""
    if closed_year(year, roster_congress(CACHE / "MemberData.xml")):
        return []
    _, people = load_roster(CACHE / "MemberData.xml")
    rows = load_index(CACHE / f"{year}FD.xml")
    return wanted_from_rows(rows, people)


def roster_congress(path: Path) -> int:
    """The Congress the Clerk's roster lists, as its own title-info says."""
    return int(text_of(ET.parse(path).getroot().find("title-info"), "congress-num"))


def closed_year(year: int, congress: int) -> bool:
    """Whether a filing year's Congress has ended, by the roster this build reads. A roster
    of an earlier Congress than the year's refuses the build: the year's roster is not out."""
    if congress < congress_of(year):
        raise SystemExit(
            f"refusing to build: the roster this build read lists the {ordinal(congress)} "
            f"Congress, and filing year {year} falls in the {ordinal(congress_of(year))}"
        )
    return congress > congress_of(year)


def build(year: int, dry_run: bool = False) -> int:
    roster_capture = read_capture("MemberData.xml")
    index_capture = read_capture(f"{year}FD.zip")
    seats, people = load_roster(CACHE / "MemberData.xml")
    rows = load_index(CACHE / f"{year}FD.xml")
    adjudications, adjudications_hash = load_adjudications(ADJUDICATIONS)
    documents, docs_hash = load_docs_manifest()
    published = read_published()
    published_ids = {row["id"] for row in published["filings"] if index_year(row) == year}
    listed_doc_ids = {row["doc_id"] for row in rows}

    # A filing year is built against the roster of its own Congress. Once the roster lists
    # a later one, the year is closed: its rows are carried as published, and no new row of
    # it is attributed, because the later roster's seats and swearing-in dates are not the
    # year's. Nothing of the roster or the documents shapes a closed year's rows.
    congress = roster_congress(CACHE / "MemberData.xml")
    closed = closed_year(year, congress)
    closed_reason = (
        f"filing year {year} is of the {ordinal(congress_of(year))} Congress, and the roster "
        f"this build read lists the {ordinal(congress)}; the register holds the "
        f"{ordinal(congress_of(year))} Congress's roster only as the rows it published, so it "
        "attributes no new row of that year"
    )
    if closed:
        seats, people, documents, docs_hash = [], [], {}, None

    by_surname = index_people(people)

    roster_source = {
        "url": roster_capture["url"],
        "retrieved_at": roster_capture["retrieved_at"],
        "content_hash": roster_capture["sha256"],
    }

    offices, office_of_seat = [], {}
    for seat in seats:
        start = term_start(seat["congress"])
        office = {
            "id": f"of:us:house-{seat['seat'].lower()}:{start[:4]}",
            "jurisdiction": "us:federal",
            "branch": "legislative",
            "chamber": "house",
            "state": seat["seat"][:2],
            "district": seat["seat"][2:],
            "seat": seat["seat"],
            "title": seat["title"],
            "term_start": start,
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
            # The roster's own sworn date, as data, for any Signal that asks whether a rule
            # applied to this person on a date; the note below says the same in prose.
            "sworn_at": sworn_iso(person),
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

    ptr = load_ptr() if documents else None
    filings, rejected, adjudicated, attributed_by_document = [], [], 0, 0
    index_rows = len(rows)
    rows, duplicated = collapse_duplicates(rows, rejected, index_capture)
    for row in rows:
        filing_id = f"fl:house-clerk:{row['filing_type'] or 'none'}:{row['doc_id']}"
        if closed:
            if filing_id not in published_ids:
                rejected.append(
                    {
                        "adapter": "house-fd",
                        "reason": closed_reason,
                        "source_row": row,
                        "source": {
                            "url": index_capture["url"],
                            "retrieved_at": index_capture["retrieved_at"],
                            "content_hash": index_capture["sha256"],
                        },
                    }
                )
            continue
        person, reason = match(row, people, by_surname)
        confidence = None  # an index row; the document itself has not been read
        notes = None
        filed_at = iso(row["filing_date"])
        held = surname_neighbour(row, by_surname) if reason.endswith(HELD_SUFFIX) else None
        document_block = None
        dup_note = (
            f"The Clerk's index lists this DocID {duplicated[row['doc_id']]} times, identically; "
            "the register keeps one row for it."
            if row["doc_id"] in duplicated
            else None
        )
        if person is None and held is not None and row["state_dst"] == held["seat"]:
            # The index placed the row at the member's own seat under the member's
            # surname. The document decides it; a human decides what the document cannot.
            pdf = DOCS / f"{row['doc_id']}.pdf"
            capture = documents.get(row["doc_id"])
            if ptr is not None and capture is not None and pdf.is_file():
                head = ptr.header(ptr.extract_text(pdf))
                verdict, clause = attribute_by_header(head, row, held, filed_at)
                document_block = {
                    "url": capture["url"],
                    "retrieved_at": capture["retrieved_at"],
                    "content_hash": capture["sha256"],
                }
                if verdict == "attributed":
                    person = held
                    attributed_by_document += 1
                    index_name = f"{row['first']} {row['last']} {row.get('suffix', '')}".strip()
                    roster_name = held["official_name"] or f"{held['first']} {held['last']}"
                    notes = (
                        "Attributed by the document's own header: the Clerk's index writes the "
                        f"filer as {index_name!r}; {clause}; the Clerk's roster names the holder "
                        f"of {held['seat']} {roster_name.strip()!r}."
                    )
                else:
                    reason = f"{reason.removesuffix(HELD_SUFFIX)}; {clause}{HELD_SUFFIX}"
            else:
                reason = (
                    f"{reason.removesuffix(HELD_SUFFIX)}; the document has not been captured"
                    f"{HELD_SUFFIX}"
                )
        decided = adjudications.get(row["doc_id"]) if person is None else None
        if decided is not None:
            person = person_of_id.get(decided["officeholder_id"])
            if person is None and filing_id in published_ids:
                continue  # published on that decision; its officeholder's rows are carried
            if person is None:
                raise SystemExit(
                    f"adjudication for DocID {row['doc_id']} names "
                    f"{decided['officeholder_id']}, which is not in the roster"
                )
            confidence, adjudicated = "manual", adjudicated + 1
        if (person is None or filed_at is None) and filing_id in published_ids:
            continue  # published with its attribution, which stands; carry_forward keeps it
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
                    **({"document": document_block} if document_block else {}),
                    **({"notes": dup_note} if dup_note else {}),
                }
            )
            continue
        holder = holder_of_bioguide[person["bioguide"]]
        if dup_note:
            notes = " ".join(part for part in (notes, dup_note) if part)
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
                "notes": notes,
            }
        )

    # The document layer. For every filing whose document was captured: read it, require
    # it to agree with the roster seat and the DocID it was attributed to, and write its
    # transactions. A document that disagrees refuses the filing row itself, because the
    # document is the primary record and the index row's attribution is what it contradicts.
    # One exception, recorded rather than guessed: when only the printed seat differs and
    # the printed name confirms the officeholder by the join's own test, the row stands
    # and carries the discrepancy in its notes.
    transactions: list[dict] = []
    documents_read = documents_refused = documents_unreadable = documents_discrepant = 0
    documents_header_only = 0
    read_documents: dict[str, dict] = {}
    if documents:
        kept = []
        for filing in filings:
            doc_id = filing["id"].rsplit(":", 1)[1]
            capture = documents.get(doc_id)
            pdf = DOCS / f"{doc_id}.pdf"
            if capture is None or not pdf.is_file():
                kept.append(filing)
                continue
            text, pages = ptr.read(pdf)
            read_documents[doc_id] = {
                "url": capture["url"],
                "retrieved_at": capture["retrieved_at"],
                "content_hash": capture["sha256"],
            }
            person = person_of_id[filing["officeholder_id"]]
            status, reason = ptr.verify(
                text,
                person["seat"],
                doc_id,
                name_confirms=lambda printed, p=person: p["_tokens"] <= tokens(printed),
            )
            if status == "unreadable":
                # The row stands; the document was captured and hashed but not read.
                documents_unreadable += 1
                filing["source"]["content_hash"] = capture["sha256"]
                kept.append(filing)
                continue
            if status == "contradiction" and filing["id"] in published_ids:
                raise SystemExit(
                    f"refusing to build: the document behind the published filing {filing['id']} "
                    f"now refuses its attribution ({reason}). The register does not drop a "
                    "published row; a person decides, with the evidence, as a correction."
                )
            if status == "contradiction":
                documents_refused += 1
                rejected.append(
                    {
                        "adapter": "house-fd",
                        "reason": f"the document refused the attribution: {reason}",
                        "source_row": {"doc_id": doc_id, "filing_id": filing["id"]},
                        "source": {
                            "url": capture["url"],
                            "retrieved_at": capture["retrieved_at"],
                            "content_hash": capture["sha256"],
                        },
                    }
                )
                continue
            if status == "discrepancy":
                documents_discrepant += 1
                discrepancy = (
                    f"The document prints State/District {ptr.header(text)['seat']}; the "
                    f"Clerk's roster lists this officeholder at {person['seat']}. The "
                    "attribution rests on the filer's printed name and the Filing ID, which "
                    "both agree with the Clerk's index."
                )
                filing["notes"] = " ".join(p for p in (filing["notes"], discrepancy) if p)
            filing["source"]["content_hash"] = capture["sha256"]
            if filing["source_form_code"] != PTR_CODE:
                # An annual report or another form: its header was read and its hash
                # recorded; the register does not yet read its schedules.
                documents_header_only += 1
                kept.append(filing)
                continue
            documents_read += 1
            filing["extraction_confidence"] = "structured"
            for n, tx in enumerate(ptr.transactions(pages), 1):
                transactions.append(
                    {
                        "id": f"tx:house-clerk:{doc_id}:{n:03d}",
                        "filing_id": filing["id"],
                        "officeholder_id": filing["officeholder_id"],
                        "owner": tx["owner"],
                        "asset": tx["asset"],
                        "asset_normalized": tx["ticker"],
                        "asset_code": tx.get("asset_code"),
                        "action": tx["action"],
                        "transaction_date": tx["transaction_date"],
                        "notified_date": tx["notified_date"],
                        "amount_range": tx["amount"],
                        "filing_status": tx.get("filing_status"),
                        "notes": ptr.notes(tx),
                    }
                )
            kept.append(filing)
        filings = kept

    # What this build read and attributed, before anything published is carried.
    attributed = len({f["officeholder_id"] for f in filings})
    quiet = len(people) - attributed
    accepted = len(filings)
    written = len(transactions)

    observed = {
        "roster": None if closed else roster_source,
        "index": {
            "url": index_capture["url"],
            "retrieved_at": index_capture["retrieved_at"],
            "content_hash": index_capture["sha256"],
        },
        "index_doc_ids": listed_doc_ids,
        "documents": read_documents,
    }
    built = {
        "offices": offices,
        "officeholders": officeholders,
        "filings": filings,
        "transactions": transactions,
    }
    rows_out, new_changes, carried = carry_forward(published, built, year, observed)
    offices, officeholders = rows_out["offices"], rows_out["officeholders"]
    filings, transactions = rows_out["filings"], rows_out["transactions"]
    new_changes.sort(key=lambda c: c["id"])
    changes = published["changes"] + new_changes
    changed = dict(collections.Counter(c["change"] for c in new_changes))

    transactions.sort(key=lambda t: (t["officeholder_id"], t["filing_id"], t["id"]))
    filings.sort(key=lambda f: (f["officeholder_id"], f["filed_at"], f["id"]))
    officeholders.sort(key=lambda h: h["id"])
    offices.sort(key=lambda o: o["id"])
    reasons = dict(collections.Counter(r["reason"].split(" (")[0] for r in rejected))
    print(
        f"roster        {len(seats)} seats, {len(people)} filled, {len(seats) - len(people)} vacant"
    )
    print(
        f"index         {index_rows} rows for {year}"
        + (
            f", {len(duplicated)} DocID{'s' if len(duplicated) != 1 else ''} listed more than "
            "once identically and carried once"
            if duplicated
            else ""
        )
    )
    if closed:
        print(f"closed        {closed_reason}")
    print(f"accepted      {accepted} filings against {attributed} officeholders")
    if adjudicated:
        print(f"              {adjudicated} of them by a person's adjudication, citing evidence")
    if attributed_by_document:
        print(
            f"              {attributed_by_document} of them by the document's own header: "
            "Status Member at the seat, Filing ID agreeing"
        )
    print(f"rejected      {len(rejected)} rows")
    for reason, count in sorted(reasons.items(), key=lambda item: -item[1]):
        print(f"              {count:5d}  {reason}")
    print(f"quiet         {quiet} sitting members have no filing in this index")
    if documents:
        print(
            f"documents     {documents_read} read ({documents_discrepant} with a seat "
            f"discrepancy noted on the row), {documents_unreadable} captured but unreadable "
            f"(scanned), {documents_header_only} header read and hashed, contents not yet "
            f"read, {documents_refused} refused as contradicting; "
            f"{written} transactions"
        )
    if any(carried.values()):
        print(
            f"carried       as published: {carried['officeholders']} officeholders, "
            f"{carried['offices']} offices, {carried['filings']} filings and "
            f"{carried['transactions']} transactions this build did not re-derive"
        )
    for change, count in sorted(changed.items()):
        print(f"changes       {count} published rows the source now shows as {change}")

    if dry_run:
        print("\ndry run: nothing written")
        return 0

    write(Path("data/offices.ndjson"), offices)
    write(Path("data/officeholders.ndjson"), officeholders)
    write(Path("data/filings.ndjson"), filings)
    write(Path("data/transactions.ndjson"), transactions)
    if changes:
        write(PUBLISHED["changes"], changes)
    # Named for the captures the rows came from, never for the day the build ran: the
    # same bytes rebuild the same file, so an unchanged source is an unchanged tree and
    # the seal holds. Rejections from earlier captures live in git history.
    key = capture_key(index_capture, None if closed else roster_capture, docs_hash)
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
        "documents": {
            "manifest_sha256": docs_hash,
            "captured": len(documents),
            "read": documents_read,
            "seat_discrepancies": documents_discrepant,
            "unreadable": documents_unreadable,
            "header_only": documents_header_only,
            "refused": documents_refused,
            "transactions": written,
        },
        "congress": {"filing_year": congress_of(year), "roster": congress, "closed": closed},
        "carried": carried,
        "changes": changed,
        "counts": {
            "seats": len(seats),
            "filled": len(people),
            "vacant": len(seats) - len(people),
            "index_rows": index_rows,
            "index_rows_duplicated": len(duplicated),
            "accepted": accepted,
            "reports": sum(1 for f in built["filings"] if f["form_type"] == "House-PTR"),
            "adjudicated": adjudicated,
            "attributed_by_document": attributed_by_document,
            "officeholders_with_a_filing": attributed,
            "quiet": quiet,
            "rejected": len(rejected),
        },
        "rejected_by_reason": reasons,
    }
    # One run record per adapter and year in the tree, like the set-aside file: the
    # record of an earlier capture lives in git history with the build it sealed. Two
    # records in the tree once let a page read the wrong one by filename order.
    runs_dir = Path("data/adapter-runs")
    for old in runs_dir.glob(f"house-fd-{year}-*.ndjson"):
        if old.name != f"house-fd-{year}-{key}.ndjson":
            old.unlink()
    write(runs_dir / f"house-fd-{year}-{key}.ndjson", [run])
    print(
        "\nwrote data/offices.ndjson, data/officeholders.ndjson, data/filings.ndjson, "
        "data/transactions.ndjson" + (", data/changes.ndjson" if changes else "")
    )
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
        _, docs_hash = load_docs_manifest()
        closed = closed_year(args.year, roster_congress(CACHE / "MemberData.xml"))
        print(
            capture_key(
                read_capture(f"{args.year}FD.zip"),
                None if closed else read_capture("MemberData.xml"),
                None if closed else docs_hash,
            )
        )
        return 0
    return build(args.year, args.dry_run)


if __name__ == "__main__":
    sys.exit(main())
