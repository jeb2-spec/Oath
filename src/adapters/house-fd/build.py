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


def capture_key(index_capture: dict, roster_capture: dict, docs_hash: str | None = None) -> str:
    """Twelve hex characters naming these captures. Same bytes in, same key out.

    The document manifest joins the key when it exists, so a week that captured new
    documents is a changed record even when the index and roster did not move.
    """
    joined = f"{index_capture['sha256']}\n{roster_capture['sha256']}"
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


def build(year: int, dry_run: bool = False) -> int:
    roster_capture = read_capture("MemberData.xml")
    index_capture = read_capture(f"{year}FD.zip")
    seats, people = load_roster(CACHE / "MemberData.xml")
    rows = load_index(CACHE / f"{year}FD.xml")
    adjudications, adjudications_hash = load_adjudications(ADJUDICATIONS)
    documents, docs_hash = load_docs_manifest()

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

    ptr = load_ptr() if documents else None
    filings, rejected, adjudicated, attributed_by_document = [], [], 0, 0
    index_rows = len(rows)
    rows, duplicated = collapse_duplicates(rows, rejected, index_capture)
    for row in rows:
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
            if person is None:
                raise SystemExit(
                    f"adjudication for DocID {row['doc_id']} names "
                    f"{decided['officeholder_id']}, which is not in the roster"
                )
            confidence, adjudicated = "manual", adjudicated + 1
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
                        "action": tx["action"],
                        "transaction_date": tx["transaction_date"],
                        "notified_date": tx["notified_date"],
                        "amount_range": tx["amount"],
                        "notes": ptr.notes(tx),
                    }
                )
            kept.append(filing)
        filings = kept
    transactions.sort(key=lambda t: (t["officeholder_id"], t["filing_id"], t["id"]))

    filings.sort(key=lambda f: (f["officeholder_id"], f["filed_at"], f["id"]))
    officeholders.sort(key=lambda h: h["id"])
    offices.sort(key=lambda o: o["id"])

    attributed = len({f["officeholder_id"] for f in filings})
    quiet = len(people) - attributed
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
    print(f"accepted      {len(filings)} filings against {attributed} officeholders")
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
            f"{len(transactions)} transactions"
        )

    if dry_run:
        print("\ndry run: nothing written")
        return 0

    write(Path("data/offices.ndjson"), offices)
    write(Path("data/officeholders.ndjson"), officeholders)
    write(Path("data/filings.ndjson"), filings)
    write(Path("data/transactions.ndjson"), transactions)
    # Named for the captures the rows came from, never for the day the build ran: the
    # same bytes rebuild the same file, so an unchanged source is an unchanged tree and
    # the seal holds. Rejections from earlier captures live in git history.
    key = capture_key(index_capture, roster_capture, docs_hash)
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
            "transactions": len(transactions),
        },
        "counts": {
            "seats": len(seats),
            "filled": len(people),
            "vacant": len(seats) - len(people),
            "index_rows": index_rows,
            "index_rows_duplicated": len(duplicated),
            "accepted": len(filings),
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
        "data/transactions.ndjson"
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
        print(
            capture_key(
                read_capture(f"{args.year}FD.zip"), read_capture("MemberData.xml"), docs_hash
            )
        )
        return 0
    return build(args.year, args.dry_run)


if __name__ == "__main__":
    sys.exit(main())
