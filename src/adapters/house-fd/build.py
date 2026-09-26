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
    not the day a given member was sworn. Under the Twentieth Amendment, section 1
    (https://constitution.congress.gov/constitution/amendment-20/), the terms of
    Representatives end at noon on 3 January and their successors' terms then begin, so from
    the 74th Congress (1935) the nth Congress's terms begin at noon on 3 January of
    1787 + 2n: the 119th on 2025-01-03, the 120th on 2027-01-03. A Congress may convene on
    another day; its terms do not move."""
    if congress < 74:
        raise SystemExit(f"the {congress}th Congress predates the Twentieth Amendment's terms")
    return f"{1787 + 2 * congress}-01-03"


def congress_of(year: int) -> int:
    """The Congress whose terms run through a filing year: the 119th for 2025 and 2026. In an
    odd year the Congress before holds the days until noon on 3 January; an index is a
    year's, and the register takes the Congress that holds the rest of it."""
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
    head: dict,
    row: dict,
    member: dict,
    filed_at: str | None,
    others: list[tuple[str, frozenset[str]]] = (),
    congress: int | None = None,
) -> tuple[str, str]:
    """Whether the document's own header settles a held row at the member's own seat.

    The index placed the row at the member's seat and the surnames agree; the given
    names do not. The document settles it when it prints Status Member, that seat, this
    row's DocID as its Filing ID, and a filer name carrying the roster surname, and the
    index dates the filing no earlier than the swearing-in the roster records for this
    Congress. A printed name carrying the given name and surname of another officeholder
    the register holds at the seat (`others`, as (given name, surname tokens)), and not the
    member's given name, holds the row too: a Member who left files after their successor
    is sworn in, and the surname alone would give the report to the successor. Returns
    (status, clause): status is "attributed" or "held"; the clause is what the document
    printed, for the filing row's notes or the held row's reason. The register never says
    who a filer is not; a document that prints another status holds the row with that
    status quoted, and a person decides it.
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
    printed = tokens(head["name"])
    given = next((fold(p) for p in member["first"].split() if fold(p) not in NOISE), "")
    if given not in printed and any(
        name and name in printed and surname <= printed for name, surname in others
    ):
        return (
            "held",
            f"the document prints the filer as {head['name']!r}, which carries the given name "
            "and surname of another officeholder the register holds at this seat",
        )
    sworn = sworn_iso(member)
    if filed_at and sworn and filed_at < sworn:
        which = f"the {ordinal(congress)} Congress" if congress else "this Congress"
        return (
            "held",
            f"the index dates the filing {filed_at}, before the swearing-in for {which} "
            f"that the roster records ({sworn}); the roster does not say who held the seat "
            "before that date, so the register does not",
        )
    return (
        "attributed",
        f"the document prints {head['name']!r}, Status Member, State/District "
        f"{head['seat']}, Filing ID {head['filing_id']}",
    )


def collapse_duplicates(
    rows: list[dict],
    rejected: list[dict],
    index_capture: dict,
    published_docs: set[str] | frozenset[str] = frozenset(),
) -> tuple[list[dict], dict[str, int]]:
    """One row per DocID. The Clerk's index has listed a DocID twice, identically; such a
    row is carried once and says so. A DocID listed more than once with differing rows is
    attributed from none of them, every copy set aside with the reason; a published one keeps
    the row the register published, as published."""
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
                            "rows; "
                            + (
                                "the register keeps the row it published, as published"
                                if doc_id in published_docs
                                else "the register carries none of them"
                            )
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
# stays, byte for byte (CHARTER Vow V; INVARIANTS §14). So a build reads the published rows
# first, and what it derives from its captures only adds to them:
#
#   - a published row is written back exactly as published. A fact it did not yet carry (a
#     null, a missing key, a term at the end of a list) is filled when a capture shows it;
#     no fact it carries moves;
#   - where a capture later than the one a published row was read from shows the row
#     otherwise, that is a new fact about the source. It is written as its own row in
#     data/changes.ndjson, with the capture that shows it, and the bytes of that capture are
#     kept under data/captures/sha256/, named by their SHA-256, so the change can be checked
#     from the repository alone once the source serves something else: "not listed" and "listed
#     again" (the roster no longer lists an officeholder, or the index a filing, or lists
#     them again), "read otherwise" (the source gives one of the row's facts another value),
#     and "replaced" (the Clerk serves other bytes for a document, and they read otherwise);
#   - where the bytes a published row was read from now read otherwise, the source did not
#     change; the register's reading did. The build refuses, because a change to the
#     register's code must not rewrite what it published: a person reverts it, or corrects
#     the rows with tools/correct.py, citing the evidence;
#   - the join attributes new rows only. A build that would attribute a published filing to
#     another officeholder refuses, and a person decides it with tools/correct.py.
#
# A person's correction is a change row too ("corrected"): tools/correct.py moves the fact
# and keeps what it was, and tools/check-removals.py lets a moved fact through only where
# such a row names it. So a Member who leaves office keeps their rows and their page; a
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
CAPTURES = Path("data/captures/sha256")
FRAME = "Presence in the register is not evidence of wrongdoing."
NOT_LISTED, LISTED_AGAIN = "not listed", "listed again"
READ_OTHERWISE, REPLACED, CORRECTED = "read otherwise", "replaced", "corrected"
# The facts of a filing that the Clerk's index row states, and of an officeholder that the
# roster states, weighed against the published row when a later capture lists it again.
INDEX_FACTS = ("filed_at", "form_type", "source_form_code")
ROSTER_FACTS = ("legal_name", "common_name", "party", "sworn_at")
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


def published_set_aside(year: int) -> list[dict]:
    """The rows of this year's index the tree's last build set aside, with their reasons."""
    rows: list[dict] = []
    for path in sorted(Path("data/rejected/house-fd").glob(f"{year}-*.ndjson")):
        rows += [json.loads(line) for line in path.read_text("utf-8").splitlines() if line]
    return rows


def published_run(year: int) -> dict:
    """The tree's run record for this year, from the last build; empty when there is none."""
    for path in sorted(Path("data/adapter-runs").glob(f"house-fd-{year}-*.ndjson")):
        lines = [line for line in path.read_text("utf-8").splitlines() if line.strip()]
        if lines:
            return json.loads(lines[-1])
    return {}


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


def sha256_of(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


# Each row's own entry in the source's bytes, found without the XML parser. A change in the
# register's own reading must never be recorded as a change at the source (COUNCIL.md §5,
# mode 10): an entry whose bytes are unchanged can say nothing new, and a row whose entry the
# bytes still carry is listed, whatever the parser makes of it (the Council's second reading
# of S.1b). The patterns are deliberately plain, so they change far less often than the
# parser and can check it.
INDEX_ENTRY = re.compile(rb"<Member>.*?</Member>", re.S)
INDEX_ID = re.compile(rb"<DocID>\s*([^<\s]+)\s*</DocID>")
ROSTER_ENTRY = re.compile(rb"<member>.*?</member>", re.S)
ROSTER_SEAT = re.compile(rb"<statedistrict>.*?</statedistrict>", re.S)
ROSTER_INFO = re.compile(rb"<member-info>.*?</member-info>", re.S)
ROSTER_ID = re.compile(rb"<bioguideID>\s*([^<\s]+)\s*</bioguideID>")


def index_entries(path: Path) -> dict[str, str]:
    """Each DocID of the Clerk's index and the SHA-256 of its <Member> entry, as served."""
    out: dict[str, str] = {}
    for block in INDEX_ENTRY.finditer(path.read_bytes() if path.is_file() else b""):
        found = INDEX_ID.search(block.group(0))
        if found:
            out.setdefault(found.group(1).decode("utf-8"), sha256_of(block.group(0)))
    return out


def roster_entries(path: Path) -> dict[str, str]:
    """Each bioguide ID on the Clerk's roster and the SHA-256 of the bytes that state its seat
    and its member-info, which hold every fact the register reads. The rest of the entry
    (committee assignments among it) changes often and says nothing the register reads."""
    out: dict[str, str] = {}
    for block in ROSTER_ENTRY.finditer(path.read_bytes() if path.is_file() else b""):
        info = ROSTER_INFO.search(block.group(0))
        found = ROSTER_ID.search(info.group(0)) if info else None
        if found:
            seat = ROSTER_SEAT.search(block.group(0))
            stated = (seat.group(0) if seat else b"") + info.group(0)
            out.setdefault(found.group(1).decode("utf-8"), sha256_of(stated))
    return out


def keep_capture(path: Path, sha256: str) -> str:
    """Keep the bytes of a capture a change row cites, write-once, named by their SHA-256,
    and return where. A cache that no longer holds the bytes its record names refuses."""
    target = CAPTURES / f"{sha256}{path.suffix}"
    if target.is_file():
        return target.as_posix()
    body = path.read_bytes() if path.is_file() else b""
    if hashlib.sha256(body).hexdigest() != sha256:
        raise SystemExit(
            f"refusing to build: {path} does not hold the bytes its capture record names "
            f"({sha256[:12]}), and a change row must cite bytes the register keeps"
        )
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(body)
    return target.as_posix()


def change_row(row_id: str, rows: str, change: str, capture: dict, **facts) -> dict:
    """A change a later capture showed about a published row, with the capture that shows
    it. `facts` carries the field and its values where the change is about one fact, and
    `before`, when the register last built from a capture of the same source: the change
    fell between the two reads, and the register does not know when."""
    field = f":{facts['field']}" if change == READ_OTHERWISE else ""
    for optional in ("before", "before_content_hash", "entry_sha256"):
        if not facts.get(optional):
            facts.pop(optional, None)
    return {
        "id": f"ch:{change.replace(' ', '-')}:{row_id}{field}:{capture['retrieved_at']}",
        "row_id": row_id,
        "rows": rows,
        "change": change,
        **facts,
        "capture": {
            "url": capture["url"],
            "retrieved_at": capture["retrieved_at"],
            "content_hash": capture["content_hash"],
        },
        "frame": FRAME,
    }


class Refusal(SystemExit):
    """A build that would record the register's own reading as a change at the source."""


class Observed:
    """The change rows this build adds. One per row, kind, field and capture, and only from a
    capture later than the latest one already recorded for that row and kind, so a capture
    re-read, or read out of order, never writes a second change or reverses a later one.

    A change is the source's only when the source's bytes for the row changed. So a change is
    refused, never recorded, when it would come from the very bytes the register last built
    from, or from a row's own entry unchanged since the register last read it; and a row is
    "not listed" only when the source's bytes no longer carry its entry, whatever the parser
    makes of them. A person's recorded decision about a fact silences the refusal for that
    fact; it never silences a change the source's own bytes show."""

    def __init__(
        self,
        published_changes: list[dict],
        before: dict | None = None,
        before_hash: dict | None = None,
    ) -> None:
        self.before = before or {}  # by source URL: when the register last built from it
        self.before_hash = before_hash or {}  # by source URL: the bytes it last built from
        self.past: dict[tuple, list[dict]] = {}
        for change in sorted(
            published_changes, key=lambda c: (c["capture"]["retrieved_at"], c["id"])
        ):
            self.past.setdefault(self.thread(change), []).append(change)
        self.new: list[dict] = []
        self.bytes: dict[str, Path] = {}

    @staticmethod
    def thread(change: dict) -> tuple:
        kind = change["change"]
        if kind in (NOT_LISTED, LISTED_AGAIN):
            return (change["row_id"], "listed")
        return (change["row_id"], kind, change.get("field"))

    def last(self, key: tuple) -> dict | None:
        return self.past[key][-1] if self.past.get(key) else None

    def add(self, row: dict, path: Path) -> None:
        self.new.append(row)
        self.past.setdefault(self.thread(row), []).append(row)
        self.bytes[row["capture"]["content_hash"]] = path

    def same_bytes(self, capture: dict) -> bool:
        """Whether the capture holds the very bytes the register last built from."""
        return capture["content_hash"] == self.before_hash.get(capture["url"])

    def facts(self, capture: dict, **more) -> dict:
        return {
            "before": self.before.get(capture["url"]),
            "before_content_hash": self.before_hash.get(capture["url"]),
            **more,
        }

    def listed(
        self, row_id: str, rows: str, listed: bool, capture: dict, path: Path, carried: bool
    ) -> None:
        """`listed` is the parser's word; `carried`, whether the bytes hold the row's entry."""
        if listed != carried:
            raise Refusal(
                f"refusing to build: the source's bytes {'carry' if carried else 'do not carry'} "
                f"an entry for {row_id}, and this build's reading "
                f"{'does not list' if not listed else 'lists'} it. The source did not change "
                "that; the register's reading did, and a change to the register's code must "
                "not be recorded as a change at the source. Revert it."
            )
        last = self.last((row_id, "listed"))
        if last and capture["retrieved_at"] <= last["capture"]["retrieved_at"]:
            return
        if listed == (last is None or last["change"] == LISTED_AGAIN):
            return
        if self.same_bytes(capture):
            raise Refusal(
                f"refusing to build: {row_id} would be recorded as "
                f"{'listed again' if listed else 'not listed'} from the very bytes the register "
                "last built from. The source did not change; the register's reading did."
            )
        kind = LISTED_AGAIN if listed else NOT_LISTED
        self.add(change_row(row_id, rows, kind, capture, **self.facts(capture)), path)

    def read(
        self,
        row_id: str,
        rows: str,
        field: str,
        was,
        now,
        capture: dict,
        path: Path,
        entry: str | None = None,
        row_entry: str | None = None,
        decided: bool = False,
    ) -> None:
        """What the source states for one fact of a published row. `entry` is the SHA-256 of
        the row's entry in these bytes; `row_entry`, of the entry the row was read from."""
        last = self.last((row_id, READ_OTHERWISE, field))
        if last and capture["retrieved_at"] <= last["capture"]["retrieved_at"]:
            return
        expected = last["now"] if last else was
        if now == expected:
            return
        known = last.get("entry_sha256") if last else row_entry
        if self.same_bytes(capture) or (entry is not None and entry == known):
            if decided:
                return
            raise Refusal(
                f"refusing to build: the source's entry {row_id} was last read from is "
                f"unchanged, and this build reads its {field} as {now!r} where the register "
                f"holds {expected!r}. The source did not change; the register's reading did, "
                "and a change to the register's code must not rewrite what it published. "
                "Revert it, or correct the row with tools/correct.py, citing the evidence."
            )
        self.add(
            change_row(
                row_id,
                rows,
                READ_OTHERWISE,
                capture,
                field=field,
                was=was,
                now=now,
                **self.facts(capture, entry_sha256=entry),
            ),
            path,
        )

    def replaced(self, row_id: str, was: str, capture: dict, path: Path, differs: bool) -> None:
        """The Clerk serves other bytes for a published filing's document. Recorded when they
        read otherwise than the rows published from it, or when a recorded replacement ends."""
        last = self.last((row_id, REPLACED, "source.content_hash"))
        if last and capture["retrieved_at"] <= last["capture"]["retrieved_at"]:
            return
        seen = last["now"] if last else was
        if capture["content_hash"] == seen or not (differs or last):
            return
        self.add(
            change_row(
                row_id,
                "filings",
                REPLACED,
                capture,
                field="source.content_hash",
                was=was,
                now=capture["content_hash"],
            ),
            path,
        )


def decided(changes: list[dict], row_id: str, field: str) -> bool:
    """Whether a person has recorded a decision about this fact of this row."""
    return any(
        c["change"] == CORRECTED and c["row_id"] == row_id and c.get("field") == field
        for c in changes
    )


def accrue(published: dict, derived: dict) -> dict:
    """The published row with every fact it lacked filled from the derived one: a null, a
    missing key, the end of a longer list. No fact it carries moves."""
    if not isinstance(published, dict) or not isinstance(derived, dict):
        return published
    out = dict(published)
    for key, value in derived.items():
        if key not in out or out[key] is None:
            out[key] = value
        elif isinstance(out[key], dict):
            out[key] = accrue(out[key], value)
        elif isinstance(out[key], list) and isinstance(value, list) and len(value) > len(out[key]):
            out[key] = out[key] + value[len(out[key]) :]
    return out


def given_and_surname(name: str) -> tuple[str, frozenset[str]]:
    """The first given name, folded, and the surname tokens of a published officeholder's
    common name ("Last, First") or legal name ("First M. Last, Jr.")."""
    if "," in name and not name.rstrip().endswith((", Jr.", ", Sr.", ", II", ", III", ", IV")):
        last, first = name.split(",", 1)
    else:
        parts = [p for p in name.replace(",", " ").split() if fold(p) not in NOISE]
        last, first = (parts[-1], parts[0]) if parts else ("", "")
    given = next((fold(p) for p in first.split() if fold(p) and fold(p) not in NOISE), "")
    return given, tokens(last)


def person_kept(holder: dict, office: dict) -> dict:
    """A published officeholder the roster no longer lists, in the roster's shape, so a
    person's adjudication can still attribute a row to them and their document be read."""
    common = holder.get("common_name") or holder["legal_name"]
    last, first = (common.split(",", 1) + [""])[:2] if "," in common else (common, "")
    sworn = (holder.get("sworn_at") or "").replace("-", "")
    return {
        "bioguide": holder["biographical_ids"]["bioguide_id"],
        "last": last.strip(),
        "first": first.strip(),
        "seat": office["seat"],
        "sworn": sworn,
        "official_name": holder["legal_name"],
        "namelist": common,
        "_tokens": tokens(last, first),
        "_kept": holder["id"],
        "_office": office["id"],
    }


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
    listed_doc_ids = {row["doc_id"] for row in rows}
    last_run = published_run(year)
    last_read = {s["url"]: s["retrieved_at"] for s in last_run.get("sources", [])}

    # A filing year is built against the roster of its own Congress. Once the roster lists a
    # later one, the year is closed. The roster is not read for it, because the later
    # roster's seats and swearing-in dates are not the year's; its rows are carried as
    # published; a row set aside keeps the reason it was set aside for; a row new to the
    # index is set aside, unless a person's decision attributes it to an officeholder the
    # register holds; and the offices of the ended Congress get the day their terms ended.
    congress = roster_congress(CACHE / "MemberData.xml")
    closed = closed_year(year, congress)
    ours = congress_of(year)
    began, ended = term_start(ours), term_start(ours + 1)
    # The roster read that closed the year: recorded by the first build that read a later
    # Congress's roster, its bytes kept, and carried after, so the year's record says which
    # read closed it, never which roster the register happens to read now (the Council's
    # second reading of S.1b).
    closed_by = None
    if closed:
        closed_by = last_run.get("congress", {}).get("closed_by") or {
            "url": roster_capture["url"],
            "retrieved_at": roster_capture["retrieved_at"],
            "sha256": roster_capture["sha256"],
            "congress": congress,
        }
        if closed_by["sha256"] == roster_capture["sha256"]:
            keep_capture(CACHE / "MemberData.xml", closed_by["sha256"])
    closed_reason = (
        f"filing year {year} is of the {ordinal(ours)} Congress, whose terms ended at noon on "
        f"{ended}, and the Clerk's roster read {closed_by['retrieved_at'][:10]} lists the "
        f"{ordinal(closed_by['congress'])}; the register attributes a new row of that year only "
        "by the maintainer's recorded decision, which cites the evidence"
        if closed_by
        else ""
    )
    if closed:
        seats, people, documents, docs_hash = [], [], {}, None

    by_surname = index_people(people)
    roster_source = {
        "url": roster_capture["url"],
        "retrieved_at": roster_capture["retrieved_at"],
        "content_hash": roster_capture["sha256"],
    }
    index_source = {
        "url": index_capture["url"],
        "retrieved_at": index_capture["retrieved_at"],
        "content_hash": index_capture["sha256"],
    }
    roster_bytes, index_bytes = CACHE / "MemberData.xml", CACHE / f"{year}FD.zip"
    last_hash = {s["url"]: s["sha256"] for s in last_run.get("sources", [])}
    seen = Observed(published["changes"], last_read, last_hash)
    # Each row's own entry in the bytes this build reads, found without the parser.
    roster_now = {} if closed else roster_entries(CACHE / "MemberData.xml")
    index_now = index_entries(CACHE / f"{year}FD.xml")
    last_roster_read = (
        last_run.get("congress", {}).get("last_roster_read") or last_read.get(roster_capture["url"])
        if closed
        else roster_capture["retrieved_at"]
    )

    # Offices: every published one kept, a new one added; nothing the roster says moves a
    # published office. A closed year's offices get the day their terms ended.
    offices_by_id = {o["id"]: o for o in published["offices"]}
    office_of_seat = {}
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
        offices_by_id[office["id"]] = accrue(offices_by_id.get(office["id"], office), office)
        office_of_seat[seat["seat"]] = offices_by_id[office["id"]]

    def ended_term(office: dict) -> dict:
        if closed and office.get("term_start") == began and office.get("term_end") is None:
            return {**office, "term_end": ended}
        return office

    offices_by_id = {oid: ended_term(o) for oid, o in offices_by_id.items()}

    # Officeholders: every published one kept as published; the roster may add a new one, a
    # term at the end of one's list, and a fact one lacked. A roster that states one of their
    # facts otherwise is a change of its own, never an edit.
    holders_by_id = {h["id"]: h for h in published["officeholders"]}
    holder_of_bioguide, person_of_id = {}, {}
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
            "roster_entry_sha256": roster_now.get(person["bioguide"]),
            "notes": (
                f"Sworn {date(int(sworn[:4]), int(sworn[4:6]), int(sworn[6:])).isoformat()}. "
                if len(sworn) == 8
                else ""
            )
            + FRAME,
        }
        if holder["roster_entry_sha256"] is None:
            del holder["roster_entry_sha256"]
        holder_of_bioguide[person["bioguide"]] = holder["id"]
        person_of_id[holder["id"]] = person
        was = holders_by_id.get(holder["id"])
        if was is None:
            holders_by_id[holder["id"]] = holder
            continue
        # The row's entry in these bytes, against the one it was read from: an unchanged
        # entry can say nothing new, and a row read before entries were kept is weighed
        # against the bytes it was read from.
        entry = roster_now.get(person["bioguide"])
        row_entry = was.get("roster_entry_sha256") or (
            entry if was["source"].get("content_hash") == roster_capture["sha256"] else None
        )
        reads_as_published = True
        for field in ROSTER_FACTS:
            if was.get(field) is None:
                continue
            reads_as_published &= holder[field] == was[field]
            seen.read(
                holder["id"],
                "officeholders",
                field,
                was[field],
                holder[field],
                roster_source,
                roster_bytes,
                entry=entry,
                row_entry=row_entry,
                decided=decided(published["changes"], holder["id"], field),
            )
        if not reads_as_published:
            holder.pop(
                "roster_entry_sha256", None
            )  # gained only from an entry that reads as published
        terms = [o["id"] for o in was.get("offices", [])]
        grown = was
        if office["id"] not in terms:
            grown = {**was, "offices": [*was.get("offices", []), office]}
        holders_by_id[holder["id"]] = accrue(grown, holder)

    for hid, holder in holders_by_id.items():
        terms = [ended_term(o) for o in holder.get("offices", [])]
        if terms != holder.get("offices", []):
            holders_by_id[hid] = {**holder, "offices": terms}
    of_this_congress = {
        hid
        for hid, h in holders_by_id.items()
        if any(o.get("term_start") == began for o in h.get("offices", []))
    }
    if not closed:
        for hid in sorted(of_this_congress):
            bioguide = holders_by_id[hid]["biographical_ids"]["bioguide_id"]
            seen.listed(
                hid,
                "officeholders",
                hid in person_of_id,
                roster_source,
                roster_bytes,
                carried=bioguide in roster_now,
            )

    # Whom a person's decision may name besides the roster's members: an officeholder of this
    # Congress the register holds and the roster no longer lists, at their own seat, for a
    # filing the index dates no later than the last roster read that listed them, or the end
    # of the Congress's terms. SUBJECTS.md §1 enters no new filing for an officeholder after
    # their term; the roster does not say when a term ended, so the register takes the last
    # day it can show the person still listed.
    kept_people = {}
    for hid in of_this_congress - set(person_of_id):
        holder = holders_by_id[hid]
        office = next(o for o in holder["offices"] if o.get("term_start") == began)
        last = seen.last((hid, "listed"))
        until = ended
        if last and last["change"] == NOT_LISTED:
            until = min(until, (last.get("before") or holder["source"]["retrieved_at"])[:10])
        kept_people[hid] = dict(person_kept(holder, office), _until=until)
    names_at_seat: dict[str, list[tuple[str, str, frozenset]]] = {}
    for hid in of_this_congress:
        holder = holders_by_id[hid]
        given, surname = given_and_surname(holder.get("common_name") or holder["legal_name"])
        for office in holder["offices"]:
            names_at_seat.setdefault(office["seat"], []).append((hid, given, surname))

    # Filings. A DocID the register published is never attributed again: the index row is
    # weighed against the published row, and what it states otherwise is a change of its own.
    published_by_doc = {doc_of(f["id"]): f for f in published["filings"]}
    filings_by_id = {f["id"]: f for f in published["filings"]}
    set_aside_before = (
        {
            canonical(r["source_row"]): r
            for r in published_set_aside(year)
            if "doc_id" in r.get("source_row", {})
        }
        if closed
        else {}
    )
    set_aside_by_doc = {
        r["source_row"]["doc_id"]: r
        for r in set_aside_before.values()
        if "filing_id" in r["source_row"]
    }
    ptr = load_ptr() if documents else None
    new_filings, rejected, adjudicated_now, attributed_by_document_now = [], [], 0, 0
    index_rows = len(rows)
    rows, duplicated = collapse_duplicates(rows, rejected, index_capture, set(published_by_doc))
    for row in rows:
        filing_id = f"fl:house-clerk:{row['filing_type'] or 'none'}:{row['doc_id']}"
        was = published_by_doc.get(row["doc_id"])
        if was is not None:
            facts = {
                "filed_at": iso(row["filing_date"]),
                "form_type": "House-PTR" if row["filing_type"] == PTR_CODE else "other",
                "source_form_code": row["filing_type"] or None,
            }
            # The row's entry in these bytes, against the one it was read from. A row read
            # before entries were kept is weighed against the index row it was read from, where
            # it carries one; an unchanged entry can say nothing new.
            entry = index_now.get(row["doc_id"])
            row_entry = was.get("index_entry_sha256") or (
                entry if "index_row" in was and was["index_row"] == row else None
            )
            reads_as_published = True
            for field in INDEX_FACTS:
                if was.get(field) is None:
                    continue
                reads_as_published &= facts[field] == was[field]
                seen.read(
                    was["id"],
                    "filings",
                    field,
                    was[field],
                    facts[field],
                    index_source,
                    index_bytes,
                    entry=entry,
                    row_entry=row_entry,
                    decided=decided(published["changes"], was["id"], field),
                )
            if reads_as_published:
                # What the index row and its entry were, for a row read before they were
                # kept: gained only from an entry that states the facts the row carries.
                gained = {"index_row": row, "index_entry_sha256": entry}
                filings_by_id[was["id"]] = accrue(
                    filings_by_id[was["id"]], {k: v for k, v in gained.items() if v}
                )
            if (
                not closed
                and row["doc_id"] not in adjudications
                and not decided(published["changes"], was["id"], "officeholder_id")
            ):
                person, _ = match(row, people, by_surname)
                joined = holder_of_bioguide[person["bioguide"]] if person else None
                if joined is not None and joined != was["officeholder_id"]:
                    raise SystemExit(
                        f"refusing to build: {was['id']} is published as "
                        f"{was['officeholder_id']}'s, and this build's join attributes it to "
                        f"{joined}. The join never moves a published attribution. If it is "
                        "wrong, correct it with tools/correct.py, citing the primary source; if "
                        "it stands, record that with tools/correct.py --stands, and the build "
                        "goes on."
                    )
            continue
        if row["year"] != str(year):
            rejected.append(
                {
                    "adapter": "house-fd",
                    "reason": (
                        f"the Clerk's {year} index lists this row under year "
                        f"{row['year'] or 'none'}; the register attributes a row of an index only "
                        "where the row's year is the index's own"
                    ),
                    "source_row": row,
                    "source": index_source,
                }
            )
            continue
        if closed and row["doc_id"] not in adjudications:
            # A row the document refused carries its DocID, not the index row, so it is found
            # by its DocID where the index row itself is not (Seat C, second reading).
            before = set_aside_before.get(canonical(row)) or set_aside_by_doc.get(row["doc_id"])
            rejected.append(
                before
                if before is not None
                else {
                    "adapter": "house-fd",
                    "reason": closed_reason,
                    "source_row": row,
                    "source": index_source,
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
                others = [
                    (given, surname)
                    for hid, given, surname in names_at_seat.get(held["seat"], [])
                    if hid != holder_of_bioguide[held["bioguide"]]
                ]
                verdict, clause = attribute_by_header(head, row, held, filed_at, others, ours)
                document_block = {
                    "url": capture["url"],
                    "retrieved_at": capture["retrieved_at"],
                    "content_hash": capture["sha256"],
                }
                if verdict == "attributed":
                    person = held
                    attributed_by_document_now += 1
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
        decision = adjudications.get(row["doc_id"]) if person is None else None
        if decision is not None:
            person = person_of_id.get(decision["officeholder_id"]) or kept_people.get(
                decision["officeholder_id"]
            )
            if person is None:
                raise SystemExit(
                    f"adjudication for DocID {row['doc_id']} names "
                    f"{decision['officeholder_id']}, whom the register does not hold as an "
                    f"officeholder of the {ordinal(ours)} Congress"
                )
            until = person.get("_until")
            if until and filed_at and filed_at > until:
                specifics = f"({decision['officeholder_id']}; dated {filed_at}; "
                reason = (
                    "the maintainer's recorded decision names an officeholder for a filing the "
                    f"index dates after the {ordinal(ours)} Congress's terms ended; the register "
                    "attributes a row of this filing year only within that Congress's terms "
                    + specifics
                    + f"terms ended {until})"
                    if until == ended
                    else "the maintainer's recorded decision names an officeholder the roster "
                    "stopped listing, for a filing the index dates after the last roster read "
                    "that listed them; the register cannot show them in office after that read, "
                    "and under SUBJECTS.md §1 it enters no new filing for an officeholder after "
                    "their term " + specifics + f"last listed {until})"
                )
                person = None
            else:
                confidence, adjudicated_now = "manual", adjudicated_now + 1
        if person is None or filed_at is None:
            rejected.append(
                {
                    "adapter": "house-fd",
                    "reason": reason if person is None else "the filing date will not parse",
                    "source_row": row,
                    "source": index_source,
                    **({"document": document_block} if document_block else {}),
                    **({"notes": dup_note} if dup_note else {}),
                }
            )
            continue
        if dup_note:
            notes = " ".join(part for part in (notes, dup_note) if part)
        kept_id = person.get("_kept")
        new_filings.append(
            {
                "id": filing_id,
                "officeholder_id": kept_id or holder_of_bioguide[person["bioguide"]],
                "office_id": person["_office"] if kept_id else office_of_seat[person["seat"]]["id"],
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
                "index_row": row,
                **(
                    {"index_entry_sha256": index_now[row["doc_id"]]}
                    if row["doc_id"] in index_now
                    else {}
                ),
            }
        )
    for filing in published["filings"]:
        if index_year(filing) == year:
            seen.listed(
                filing["id"],
                "filings",
                doc_of(filing["id"]) in listed_doc_ids,
                index_source,
                index_bytes,
                carried=doc_of(filing["id"]) in index_now,
            )

    # The document layer. A new filing's document is read, required to agree with the
    # officeholder and the DocID it was attributed to, and its transactions written; a
    # document that disagrees refuses the new row, because the document is the primary
    # record and the index row's attribution is what it contradicts. One exception, recorded
    # rather than guessed: when only the printed seat differs and the printed name confirms
    # the officeholder by the join's own test, the row stands and carries the discrepancy in
    # its notes. A published filing's document is read again: the same bytes must read as
    # they did, and other bytes that read otherwise are a change of their own, "replaced",
    # with the rows published from the first bytes carried as they are.
    published_tx: dict[str, list[dict]] = collections.defaultdict(list)
    for tx in published["transactions"]:
        published_tx[tx["filing_id"]].append(tx)
    transactions_by_id = {t["id"]: t for t in published["transactions"]}
    documents_refused = documents_replaced = documents_same_reading = 0
    read_documents: dict[str, dict] = {}
    if documents:
        kept_new = []
        this_year = [f for f in filings_by_id.values() if index_year(f) == year] + new_filings
        for filing in this_year:
            doc_id = doc_of(filing["id"])
            capture = documents.get(doc_id)
            pdf = DOCS / f"{doc_id}.pdf"
            is_new = filing["id"] not in filings_by_id
            if capture is None or not pdf.is_file():
                if is_new:
                    kept_new.append(filing)
                continue
            person = person_of_id.get(filing["officeholder_id"]) or kept_people.get(
                filing["officeholder_id"]
            )
            if person is None:
                if is_new:
                    kept_new.append(filing)
                continue
            seat = (
                person["seat"]
                if is_new or filing["office_id"] not in offices_by_id
                else offices_by_id[filing["office_id"]]["seat"]
            )
            text, pages = ptr.read(pdf)
            doc_source = {
                "url": capture["url"],
                "retrieved_at": capture["retrieved_at"],
                "content_hash": capture["sha256"],
            }
            read_documents[doc_id] = doc_source
            status, reason = ptr.verify(
                text,
                seat,
                doc_id,
                name_confirms=lambda printed, p=person: p["_tokens"] <= tokens(printed),
            )
            derived = dict(filing, source=dict(filing["source"], content_hash=capture["sha256"]))
            rows_read: list[dict] = []
            if status == "discrepancy":
                discrepancy = (
                    f"The document prints State/District {ptr.header(text)['seat']}; the "
                    f"Clerk's roster lists this officeholder at {seat}. The "
                    "attribution rests on the filer's printed name and the Filing ID, which "
                    "both agree with the Clerk's index."
                )
                derived["notes"] = " ".join(p for p in (filing["notes"], discrepancy) if p)
            if status in ("ok", "discrepancy") and filing["source_form_code"] == PTR_CODE:
                derived["extraction_confidence"] = "structured"
                rows_read = [
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
                    for n, tx in enumerate(ptr.transactions(pages), 1)
                ]
            if is_new:
                if status == "contradiction":
                    documents_refused += 1
                    rejected.append(
                        {
                            "adapter": "house-fd",
                            "reason": f"the document refused the attribution: {reason}",
                            "source_row": {"doc_id": doc_id, "filing_id": filing["id"]},
                            "source": doc_source,
                        }
                    )
                    continue
                kept_new.append(derived)
                for tx in rows_read:
                    transactions_by_id[tx["id"]] = tx
                continue
            # A published filing: weigh this reading against what was published from it.
            was = filing
            before = sorted(published_tx.get(was["id"], []), key=lambda t: t["id"])
            differs = status == "contradiction" or reads_otherwise(before, rows_read)
            if was["source"].get("content_hash") not in (None, capture["sha256"]):
                seen.replaced(was["id"], was["source"]["content_hash"], doc_source, pdf, differs)
                documents_replaced += 1 if differs else 0
                documents_same_reading += 0 if differs else 1
                continue
            first_read = was["source"].get("content_hash") is None
            if status == "contradiction" and not decided(
                published["changes"], was["id"], "officeholder_id"
            ):
                raise SystemExit(
                    f"refusing to build: the document behind the published filing {was['id']} "
                    f"{'now ' if not first_read else ''}refuses its attribution ({reason}). The "
                    "register does not drop or move a published row: if the attribution is "
                    "wrong, correct it with tools/correct.py, citing the document; if it "
                    "stands, record that with tools/correct.py --stands, and the build goes on."
                )
            if before and differs and was.get("extraction_confidence") == "structured":
                raise SystemExit(
                    f"refusing to build: the document behind {was['id']} holds the bytes its "
                    "rows were published from, and this build reads them otherwise. The source "
                    "did not change; the register's reading did, and a change to the "
                    "register's code must not rewrite what it published. Revert it, or correct "
                    "the rows with tools/correct.py, citing the evidence."
                )
            filings_by_id[was["id"]] = accrue(filings_by_id[was["id"]], derived)
            for tx in rows_read:
                transactions_by_id[tx["id"]] = accrue(transactions_by_id.get(tx["id"], tx), tx)
        new_filings = kept_new

    filings = list(filings_by_id.values()) + new_filings
    transactions = list(transactions_by_id.values())
    transactions.sort(key=lambda t: (t["officeholder_id"], t["filing_id"], t["id"]))
    filings.sort(key=lambda f: (f["officeholder_id"], f["filed_at"], f["id"]))
    officeholders = sorted(holders_by_id.values(), key=lambda h: h["id"])
    offices = sorted(offices_by_id.values(), key=lambda o: o["id"])
    new_changes = sorted(seen.new, key=lambda c: c["id"])
    changes = published["changes"] + new_changes

    # The register's own figures for this year, over the rows it holds after this build, so a
    # second build from the same captures writes the same record (not this build's deltas).
    mine = [f for f in filings if index_year(f) == year]
    mine_ids = {f["id"] for f in mine}
    listed_now = {hid for hid in of_this_congress if latest_listing(changes, hid) != NOT_LISTED}
    with_a_filing = {f["officeholder_id"] for f in mine}
    reasons = dict(collections.Counter(r["reason"].split(" (")[0] for r in rejected))
    counts = {
        "seats": len(seats),
        "filled": len(people),
        "vacant": len(seats) - len(people),
        "index_rows": index_rows,
        "index_rows_duplicated": len(duplicated),
        "filings": len(mine),
        "reports": sum(1 for f in mine if f["form_type"] == "House-PTR"),
        "adjudicated": sum(1 for f in mine if doc_of(f["id"]) in adjudications),
        "attributed_by_document": sum(
            1 for f in mine if (f.get("notes") or "").startswith("Attributed by the document")
        ),
        "officeholders_with_a_filing": len(with_a_filing),
        "quiet": len(listed_now - with_a_filing),
        "rejected": len(rejected),
    }
    reports = [f for f in mine if f["form_type"] == "House-PTR"]
    documents_count = {
        "manifest_sha256": docs_hash,
        "captured": len(documents),
        "read": sum(1 for f in reports if f.get("extraction_confidence") == "structured"),
        "seat_discrepancies": sum(
            1 for f in mine if "The document prints State/District" in (f.get("notes") or "")
        ),
        "unreadable": sum(
            1
            for f in reports
            if f["source"].get("content_hash") and f.get("extraction_confidence") != "structured"
        ),
        "header_only": sum(
            1 for f in mine if f["form_type"] != "House-PTR" and f["source"].get("content_hash")
        ),
        "refused": documents_refused,
        "transactions": sum(1 for t in transactions if t["filing_id"] in mine_ids),
    }

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
    print(
        f"register      {len(mine)} filings of {year} against {len(with_a_filing)} officeholders; "
        f"{len(new_filings)} new in this build"
    )
    if adjudicated_now:
        print(f"              {adjudicated_now} new by a person's adjudication, citing evidence")
    if attributed_by_document_now:
        print(
            f"              {attributed_by_document_now} new by the document's own header: "
            "Status Member at the seat, Filing ID agreeing"
        )
    print(f"rejected      {len(rejected)} rows")
    for reason, count in sorted(reasons.items(), key=lambda item: -item[1]):
        print(f"              {count:5d}  {reason}")
    print(f"quiet         {counts['quiet']} listed officeholders have no filing of {year}")
    if documents:
        print(
            f"documents     {len(read_documents)} read in this build; {documents_refused} "
            f"refused as contradicting; {documents_replaced} published ones served in other "
            f"bytes that read otherwise, {documents_same_reading} in other bytes that read "
            "the same"
        )
    for change, count in sorted(collections.Counter(c["change"] for c in new_changes).items()):
        print(f"changes       {count} new: {change}")

    if dry_run:
        print("\ndry run: nothing written")
        return 0

    for sha256, path in seen.bytes.items():
        print(f"kept          {keep_capture(path, sha256)}")
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
                *((("MemberData.xml", roster_capture),) if not closed else ()),
                (f"{year}FD.zip", index_capture),
            )
        ],
        "adjudications_sha256": adjudications_hash,
        "documents": documents_count,
        "congress": {
            "filing_year": ours,
            "roster": congress,
            "closed": closed,
            "last_roster_read": last_roster_read,
            **({"closed_by": closed_by} if closed_by else {}),
        },
        "changes": dict(collections.Counter(c["change"] for c in changes)),
        "counts": counts,
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


def reads_otherwise(published: list[dict], read: list[dict]) -> bool:
    """Whether a document's rows, as this build reads them, differ from those published from
    it: a published row missing or out of its place, or a fact a published row carries given
    another value. A fact a published row lacked is not a difference, and neither is a row
    read after every published one: both accrue, as facts the register lacked, never as a
    change at the source (the Council's second reading of S.1b)."""
    if [t["id"] for t in read[: len(published)]] != [t["id"] for t in published]:
        return bool(published) or bool(read)
    for was, now in zip(published, read, strict=False):
        for key, value in now.items():
            if was.get(key) is not None and was[key] != value:
                return True
    return False


def latest_listing(changes: list[dict], row_id: str) -> str | None:
    """The latest "not listed" or "listed again" recorded for a row, or None."""
    listing = [
        c for c in changes if c["row_id"] == row_id and c["change"] in (NOT_LISTED, LISTED_AGAIN)
    ]
    if not listing:
        return None
    return max(listing, key=lambda c: (c["capture"]["retrieved_at"], c["id"]))["change"]


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
