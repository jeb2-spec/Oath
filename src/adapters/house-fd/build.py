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

# What attributed a row is said on the row, apart from whether its document was read: the
# document's own header, or the maintainer's recorded decision. A decided row's document is
# read like any other, and `extraction_confidence` says only that (the Council's fourth
# reading of S.1b, Seats E and G: a decision's mark was lost when its document was read).
BY_HEADER = "Attributed by the document's own header"
BY_DECISION = "Attributed by the maintainer's recorded decision"

# The facts of a transaction row that a report's own bytes state, as against the ones the
# register derived from the index (`id`, `filing_id`, `officeholder_id`). Which of the two a
# fact is decides how far a recorded correction of it reaches: see as_corrected.
FROM_THE_DOCUMENT = frozenset(
    {
        "owner",
        "asset",
        "asset_normalized",
        "asset_code",
        "action",
        "transaction_date",
        "notified_date",
        "amount_range",
        "filing_status",
        "notes",
    }
)

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
        # The roster's date is this member's own, not the day the Congress convened, and the two
        # differ for a member sworn in mid-term. "The swearing-in for the Congress that the roster
        # records" read as the day the Congress convened on the page of a member sworn eleven
        # months later (the Council's fifth reading of S.1b, Seat F). And the register says only
        # what it can see: where it holds another officeholder at this seat, it does not claim to
        # be as silent as the roster (the fifth reading, Seat D).
        return (
            "held",
            f"the index dates the filing {filed_at}, before the swearing-in the roster records "
            f"for this member of {which} ({sworn}); the roster does not say who held the seat "
            "before that date" + ("" if others else ", so the register does not"),
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


# A row at the seat of a Member the roster no longer lists, under that Member's surname. The
# name join attributes no row to a member the roster does not list, and the roster's absence
# is not a fact about the row: a row the register set aside while the roster listed them keeps
# the reason it was set aside for, which its document gave while the build still read it, and a
# row set aside since says only what the register knows. The maintainer's recorded decision can
# attribute one the index dates on or before the last roster read the register built from that
# listed them, and none dated after it (SUBJECTS.md §1; the Council's third reading of S.1b).
DEPARTED = "the roster no longer lists the member at this seat whose surname the row carries"
DEPARTED_KEPT = DEPARTED + "; while it did, the row was set aside because "
DEPARTED_OPEN = (
    DEPARTED + ", and the name join attributes no row to a member the roster does not list; the "
    "maintainer's recorded decision can, for a filing the index dates on or before the last "
    "roster read the register built from that listed them"
)
DEPARTED_SHUT = (
    DEPARTED + ", and the index dates the filing after the last roster read the register built "
    "from that listed them; the register cannot show them in office then, so no row dated after "
    "it is attributed to them while the roster does not list them"
)
# A row under the surname carrying another given name. For a member the roster lists, the
# document decides such a row; at the seat of one it no longer lists, no document is read, and
# saying only that a decision can attribute it framed a relative's filing as the member's (the
# Council's fourth reading of S.1b, Seats B, D and E).
DEPARTED_OTHER_NAME = (
    DEPARTED + ", and the row carries another given name; the name join attributes no row to a "
    "member the roster does not list, and the register has not read the document that would say "
    "who filed it"
)


def given_of(person: dict) -> str:
    """The first given name of a roster person, folded, honorifics and suffixes dropped."""
    return next((fold(p) for p in person["first"].split() if fold(p) and fold(p) not in NOISE), "")


def departed_of(
    row: dict, kept: dict[str, dict], held: dict | None, filed_at: str | None = None
) -> dict | None:
    """The officeholder the roster no longer lists whose seat the row names and whose surname it
    carries, or None. Where a member the roster lists at that seat bears the surname too (a
    successor of the same name), a row is the departed member's when it carries their given name;
    a row carrying neither given name is theirs too where the index dates it no later than the
    last roster read that listed them and before the successor was sworn, because the successor
    cannot have filed it. The rest are the listed member's, whose document decides them.

    Without that second rule, a departed member whose successor shares their surname got a
    different account of their own held rows from one whose successor does not: the reason was
    re-derived from a roster holding somebody else, so the document's own words left their page
    and the page invited a decision in their place (the Council's fifth reading of S.1b, Seats A
    and D). A reason travels with the row."""
    row_last = tokens(row["last"])
    near = [
        k
        for k in kept.values()
        if k["seat"] == row["state_dst"] and tokens(k["last"]) and tokens(k["last"]) <= row_last
    ]
    if len(near) > 1 or (near and held is not None and held["seat"] == row["state_dst"]):
        printed = tokens(row["first"])
        same = [k for k in near if given_of(k) and given_of(k) in printed]
        theirs = held is not None and given_of(held) and given_of(held) in printed
        if not same and filed_at and not theirs:
            sworn = sworn_iso(held) if held else None
            same = [
                k
                for k in near
                if k.get("_until") and filed_at <= k["_until"] and (not sworn or filed_at < sworn)
            ]
        near = same
    return near[0] if len(near) == 1 else None


# The specifics a set-aside reason carries, and the plain words a group says in their place: the
# roster name and seat of the member whose surname a row shares, a swearing-in or filing date, the
# name and status a document prints for its filer, a seat, and a Filing ID. A group describes a
# condition of the register; it never names a person or places them.
SPECIFICS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r" ?\([^()]*(?:[A-Z]{2}\d{2}|\d{4}-\d{2}-\d{2}|oh:)[^()]*\)"), ""),
    (
        re.compile(r"Status '[^']*' for the filer named '[^']*' at [A-Z]{2}\d{2}, not Member"),
        "a Status other than Member for the filer the document names, at the seat it prints",
    ),
    (re.compile(r"Status '[^']*'"), "a Status other than Member"),
    (re.compile(r"the filer as '[^']*'"), "the filer under a name"),
    (re.compile(r"prints '[^']*'"), "prints a name"),
    (re.compile(r"Filing ID \d+, not this row's DocID"), "a Filing ID other than this row's DocID"),
    (
        re.compile(r"says Filing ID \d+; the index row is DocID \d+"),
        "says a Filing ID other than the index row's DocID",
    ),
    (
        re.compile(
            r"says State/District [A-Z]{2}\d{2}; the officeholder it was attributed to holds "
            r"[A-Z]{2}\d{2}"
        ),
        "says a State/District other than the one the officeholder it was attributed to holds",
    ),
    (
        re.compile(r"State/District [A-Z]{2}\d{2}, not the member's [A-Z]{2}\d{2}"),
        "a State/District other than the member's",
    ),
    (re.compile(r"State/District [A-Z]{2}\d{2}"), "a State/District"),
    (re.compile(r"dates the filing \d{4}-\d{2}-\d{2}, before"), "dates the filing before"),
    (re.compile(r"\b(?:19|20)\d{2}-\d{2}-\d{2}\b"), "that date"),
)
# What no group may carry, whatever a later reason says: a seat, a date, a DocID or Filing ID, an
# officeholder's id, or a value a source printed, which the adapter quotes. A possessive is not a
# quote, so the opening mark must follow something other than a letter; a filing year is a fact
# about the build, so only a longer run of digits (a DocID, a Filing ID) is a specific. Checked on
# every build, because the run record and the sealed sentence derived from it are published and
# sealed, and a sealed row stays.
A_SPECIFIC = re.compile(r"[A-Z]{2}\d{2}|\d{4}-\d{2}-\d{2}|\d{5,}|oh:us:|(?<![A-Za-z])'[^']+'")


def reason_group(reason: str) -> str:
    """A set-aside reason as the run record groups it, and the sealed sentence quotes: the words
    that say why a row waits, with every specific that names a person or places them replaced by
    plain words. The build refuses rather than write a group that still carries one.

    Cut at the first parenthesis and a row kept from a departed member's seat lost the clause that
    explains it, so the one sentence about the build gave half a reason; and the rows of one member
    the roster stopped listing filled three groups, each small enough to be a count about that
    person (the Council's fourth reading of S.1b, Seats A, B and F). Cutting the trailing
    parenthesis alone then left the name and seat of a sitting member inside the key, so on the
    real index the run record and the sealed sentence carried seventy-four groups naming a member,
    thirty-seven of them counts of one row, and one naming a private filer: the count that was a
    person, at scale (the fifth reading, Seats A, C, D and E). A scrub that has to keep up with the
    next reason's wording is the same defect waiting, so a group that still carries a specific
    stops the build instead of being sealed. Every row keeps its own reason, with its specifics, in
    the set-aside file, where it is a row about a row and not a figure about a person.
    """
    if reason.startswith(DEPARTED):
        return DEPARTED + ", each with the reason the register gave the row"
    words = reason
    for pattern, plainly in SPECIFICS:
        words = pattern.sub(plainly, words)
    group = re.sub(r"\s+", " ", words).strip()
    if A_SPECIFIC.search(group):
        raise SystemExit(
            "refusing to build: the words this reason would be grouped under name a person or "
            f"place them, and the group is sealed as a figure about the register: {group!r}. Give "
            "the specific a plain-words stand-in in build.py SPECIFICS, or move it into the "
            "parentheses the row carries. The reason on the row is unaffected."
        )
    return group


def departed_reason(
    gone: dict, filed_at: str | None, before: str | None, same_given: bool = True
) -> str:
    """Why a row at a departed member's seat under their surname is set aside. `before` is the
    reason the tree's last build gave it, if it set the row aside: one given while the roster
    listed them is kept, prefixed, and one given since is kept as it is. `same_given` is
    whether the row carries their given name."""
    specifics = f" ({gone['namelist']}, {gone['seat']}; last listed {gone['_until']})"
    if before and before.startswith(DEPARTED_KEPT):
        return before
    if before and not before.startswith(DEPARTED):
        return DEPARTED_KEPT + before + specifics
    if filed_at and filed_at > gone["_until"]:
        return DEPARTED_SHUT + specifics
    if not same_given:
        return DEPARTED_OTHER_NAME + specifics
    return DEPARTED_OPEN + specifics


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


def decision_note(decision: dict) -> str:
    """What a decided row says of how it was attributed: the decision's date and its evidence,
    and the maintainer's note where there is one. Its document, where it reads, is read as any
    other's, so the row says both what attributed it and what it lists."""
    note = (decision.get("note") or "").strip().rstrip(".")
    return (
        f"{BY_DECISION} of {str(decision['decided_at'])[:10]}, citing "
        f"{decision['evidence_url']}" + (f": {note}" if note else "") + "."
    )


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
    fact; it never silences a change the source's own bytes show.

    `by_last_read` says the caller weighs each row's entry against the entry the register
    last read for it (the run record's `entries_read`), not only the one the row was first
    read from, which a change elsewhere in the entry would leave behind (the Council's third
    reading of S.1b, Seat C). A build after one that recorded no such entries weighs it
    against the last change to the same fact, or the row's own."""

    def __init__(
        self,
        published_changes: list[dict],
        before: dict | None = None,
        before_hash: dict | None = None,
        by_last_read: bool = False,
    ) -> None:
        self.before = before or {}  # by source URL: when the register last built from it
        self.before_hash = before_hash or {}  # by source URL: the bytes it last built from
        self.by_last_read = by_last_read
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

    def add(self, row: dict, path: Path | None) -> None:
        """Record a change; `path` names bytes to keep, and None a filed document, which the
        register never keeps: a decision of the Council's third reading of S.1b (Seat B), which
        NEXT.md D.4 carries into the doctrine, where EVIDENCE.md §7 and INVARIANTS.md §16 still
        say the register may keep a filing's bytes."""
        self.new.append(row)
        self.past.setdefault(self.thread(row), []).append(row)
        if path is not None:
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
                f"refusing to build: the plain pattern finds {'an' if carried else 'no'} entry "
                f"for {row_id} in the source's bytes, and this build's parser "
                f"{'does not list' if not listed else 'lists'} it. The two readings of the same "
                "bytes disagree: either the register's reading changed, or the shape of the "
                "source's bytes did, and neither is a change at the source to record. Revert a "
                "change to the reader, or adapt both readings to the new shape."
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
        the row's entry in these bytes; `row_entry`, of the entry the register last read for
        the row, or, before builds recorded that, the entry the row was read from."""
        last = self.last((row_id, READ_OTHERWISE, field))
        if last and capture["retrieved_at"] <= last["capture"]["retrieved_at"]:
            return
        expected = last["now"] if last else was
        if now == expected:
            return
        known = row_entry if self.by_last_read or not last else last.get("entry_sha256")
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

    def replaced(self, row_id: str, was: str, capture: dict, differs: list[dict]) -> None:
        """The Clerk serves other bytes for a published filing's document. Recorded when they
        read otherwise than the rows published from it, when the file the register first read is
        served again, and when the Clerk serves a third; with which rows read otherwise and in
        which facts, by id and field name and never by value. The bytes are not kept: a filed
        document can carry the names of private people, and a kept copy would outlast the Clerk's
        withdrawal or redaction of it, a decision of the Council's third reading of S.1b (Seat B)
        that NEXT.md D.4 carries into the doctrine. Each file is named by its SHA-256."""
        last = self.last((row_id, REPLACED, "source.content_hash"))
        if last and capture["retrieved_at"] <= last["capture"]["retrieved_at"]:
            return
        seen = last["now"] if last else was
        if capture["content_hash"] == seen:
            return
        # Every file the Clerk serves for a published report that is not the one last seen is a
        # row of its own, whether or not its rows read otherwise: a reader who finds that file
        # elsewhere has a row saying the register saw it, and a row of two fingerprints keeps
        # nothing private (the Council's fourth reading of S.1b, Seats B, C and G).
        self.add(
            change_row(
                row_id,
                "filings",
                REPLACED,
                capture,
                field="source.content_hash",
                was=was,
                now=capture["content_hash"],
                differs=differs,
            ),
            None,
        )


def decided(changes: list[dict], row_id: str, field: str) -> bool:
    """Whether a person has recorded a decision about this fact of this row."""
    return any(
        c["change"] == CORRECTED and c["row_id"] == row_id and c.get("field") == field
        for c in changes
    )


def fingerprint(value) -> str:
    """The SHA-256 of a value as canonical JSON: the form in which tools/correct.py keeps what a
    filer's own text was, and tools/check-removals.py matches it."""
    return hashlib.sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True).encode()
    ).hexdigest()


def as_corrected(read: list[dict], changes: list[dict], sha256: str) -> list[dict]:
    """A document's rows as this build reads them, with each fact the maintainer's recorded
    decision answered taken as the decision left it: a correction was made against a reading
    of the bytes, and the next reading of them gives what the correction says the row carried
    (its `was`, or the fingerprint of it), so that reading is no difference. Without this, the
    next refresh after a correction of a report's own rows compared the reading with the
    corrected row and refused every week (the Council's fourth reading of S.1b, Seats A and C).

    A decision answers only the reading it was made against. For a fact the document's own
    bytes state, that is the capture the correction cites: these bytes, whose SHA-256 is
    `sha256`. Another file that states the fact otherwise is a difference the register records,
    and a decision made against other bytes does not speak for it (the Council's fifth reading
    of S.1b, Seat G). For a fact the register derived rather than read (the attribution, the
    report it belongs to), no document's bytes state it, so the decision answers every reading
    of it."""
    answered: dict[tuple[str, str], list[dict]] = collections.defaultdict(list)
    for c in changes:
        if c["change"] == CORRECTED and c.get("rows") == "transactions" and c.get("field"):
            answered[(c["row_id"], c["field"])].append(c)
    out = []
    for row in read:
        row = dict(row)
        for field in list(row):
            for c in answered.get((row["id"], field), []):
                hashed = "was_sha256" in c  # a filer's own text, kept as its fingerprint alone
                these = (c.get("capture") or {}).get("content_hash") == sha256
                if field in FROM_THE_DOCUMENT and not these:
                    continue

                def was(value, c=c, hashed=hashed) -> bool:
                    return fingerprint(value) == c["was_sha256"] if hashed else value == c["was"]

                if was(c["now"]):  # the published value stands
                    if these:
                        row[field] = c["now"]
                elif was(row[field]):
                    row[field] = c["now"]
        out.append(row)
    return out


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


def name_tokens(holder: dict) -> frozenset[str]:
    """The comparable tokens of the name a published officeholder row carries: the name the
    register published them, and their filings, under."""
    common = holder.get("common_name") or holder["legal_name"]
    last, first = (common.split(",", 1) + [""])[:2] if "," in common else (common, "")
    return tokens(last, first)


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
        "_tokens": name_tokens(holder),
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


def wanted_from_rows(
    rows: list[dict], people: list[dict], decided: set[str] | frozenset[str] = frozenset()
) -> list[dict]:
    """Which documents a build will want, from the index and the roster alone.

    The document behind every row the name join attributes (the capture stage filters
    those by code), and the document behind every row held at a member's own seat
    under the member's surname, whatever its code, because the header decides those.
    Reads no canonical row, so the capture stage stays pure with respect to the
    register and a build is never a cycle behind its own source. One entry per DocID.

    And the document behind every row the maintainer's recorded decision names
    (`decided`, the DocIDs of adjudications.ndjson, an input a person writes), whatever the
    join says and whatever its code: a decision may attribute a row to a Member the roster no
    longer lists, or in a closed year, and a decided report the register never fetched would
    otherwise be described as one it could not read (the Council's third reading of S.1b,
    Seats D and E).
    """
    by_surname = index_people(people)
    out: dict[str, dict] = {}
    for row in rows:
        if row["doc_id"] in out:
            continue
        person, reason = match(row, people, by_surname) if people else (None, "")
        if row["doc_id"] in decided:
            why, seat = "decided", person["seat"] if person else row["state_dst"]
        elif person is not None:
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
    """`wanted_from_rows` over the captures on disk. What `documents.py` asks. For a closed
    year, whose rows are carried as published, only the documents of rows a decision names."""
    decided = set(load_adjudications(ADJUDICATIONS)[0])
    rows = load_index(CACHE / f"{year}FD.xml")
    if closed_year(year, roster_congress(CACHE / "MemberData.xml")):
        return wanted_from_rows(rows, [], decided)
    _, people = load_roster(CACHE / "MemberData.xml")
    return wanted_from_rows(rows, people, decided)


def decided_documents(documents: dict, decided: dict) -> tuple[dict, str | None]:
    """A closed year's captured documents: those of rows a decision names, and the SHA-256 of
    their manifest entries, which joins the capture key only when there is one, so a closed
    year with no decided document keeps the key that names its index alone."""
    mine = {doc_id: documents[doc_id] for doc_id in sorted(documents) if doc_id in decided}
    return mine, (hashlib.sha256(canonical(mine).encode()).hexdigest() if mine else None)


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


# More rows than this recorded as no longer listed by one read is refused until the maintainer
# confirms it: a source that stops listing that many at once is likelier a change in the shape
# of its bytes, or a fault in serving them, than as many departures or withdrawals, and a
# change row is never undone (the Council's third reading of S.1b, Seats B and C).
MANY_NOT_LISTED = 10


def build(year: int, dry_run: bool = False, expect_not_listed: int = 0) -> int:
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
    # Bytes to keep once the build is written, never on a dry run (Seat G, third reading).
    keeps: dict[str, Path] = {}
    if closed_by and closed_by["sha256"] == roster_capture["sha256"]:
        keeps[closed_by["sha256"]] = CACHE / "MemberData.xml"
    # A closed year's new row dated within its Congress's terms waits for a decision; one the
    # index dates after them is attributed by nothing (the Council's third reading, Seat G).
    closing = (
        f"filing year {year} is of the {ordinal(ours)} Congress, whose terms ended at noon on "
        f"{ended}, and the Clerk's roster read {closed_by['retrieved_at'][:10]} lists the "
        f"{ordinal(closed_by['congress'])}; "
        if closed_by
        else ""
    )
    closed_reason = (
        closing + "the register attributes a new row of that year dated within those terms only "
        "by the maintainer's recorded decision, which cites the evidence"
    )
    closed_after = (
        closing + "the index dates this row after those terms, and the register attributes no "
        "row of that year dated after them, by the name join or by any decision"
    )
    if closed:
        seats, people = [], []
        documents, docs_hash = decided_documents(documents, adjudications)

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
    # The entry the register last read for each row, where it differed from the row's own:
    # recorded by every build since the Council's third reading of S.1b (Seat C).
    last_entries = last_run.get("entries_read")
    seen = Observed(published["changes"], last_read, last_hash, last_entries is not None)
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
    published_holders = dict(holders_by_id)
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
        # The row's entry in these bytes, against the one the register last read for it: an
        # unchanged entry can say nothing new. A row read before entries were kept has none,
        # and only the very bytes the last build read (`same_bytes`) protect it.
        entry = roster_now.get(person["bioguide"])
        row_entry = (last_entries or {}).get(holder["id"]) or was.get("roster_entry_sha256")
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
    # filing the index dates no later than the last roster read the register built from that
    # listed them, or the end of the Congress's terms. SUBJECTS.md §1 enters no new filing for
    # an officeholder after their term; the roster does not say when a term ended, so the
    # register takes the last day it can show the person still listed.
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
    aside_published = published_set_aside(year)
    set_aside_before = (
        {
            canonical(r["source_row"]): r
            for r in aside_published
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
    # The reason the tree's last build gave each row it set aside, for a row at the seat of a
    # member the roster no longer lists: found by the index row; by its DocID where the name
    # and the seat agree; or, for a row its document refused, by its DocID alone.
    reason_before: dict = {}
    for r in aside_published if not closed else ():
        src = r.get("source_row", {})
        if "last" in src and "doc_id" in src:
            reason_before[canonical(src)] = r["reason"]
            key = (src["doc_id"], src["last"], src.get("first", ""), src.get("state_dst", ""))
            reason_before.setdefault(key, r["reason"])
        elif "filing_id" in src and "doc_id" in src:
            reason_before.setdefault(("refused", src["doc_id"]), r["reason"])
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
            # The row's entry in these bytes, against the one the register last read for it; an
            # unchanged entry can say nothing new.
            entry = index_now.get(row["doc_id"])
            row_entry = (last_entries or {}).get(was["id"]) or was.get("index_entry_sha256")
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
            late = (iso(row["filing_date"]) or "") > ended
            rejected.append(
                before
                if before is not None
                else {
                    "adapter": "house-fd",
                    "reason": closed_after if late else closed_reason,
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
                        f"{BY_HEADER}: the Clerk's index writes the "
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
                    "the register built from that listed them; the register cannot show them in "
                    "office after that read, and under SUBJECTS.md §1 it enters no new filing for "
                    "an officeholder after their term " + specifics + f"last listed {until})"
                )
                person = None
            else:
                adjudicated_now += 1
                notes = decision_note(decision)
        if person is None and decision is None and not closed and kept_people:
            gone = departed_of(row, kept_people, held, filed_at)
            if gone is not None:
                reason = departed_reason(
                    gone,
                    filed_at,
                    reason_before.get(canonical(row))
                    or reason_before.get(
                        (row["doc_id"], row["last"], row["first"], row["state_dst"])
                    )
                    or reason_before.get(("refused", row["doc_id"])),
                    same_given=bool(given_of(gone)) and given_of(gone) in tokens(row["first"]),
                )
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
            # The printed name confirms the officeholder where it carries the name the register
            # published them under, or the roster's name now: a name the roster restates later
            # is not a reason to refuse a report the register read and published (the Council's
            # fourth reading of S.1b, Seat C).
            names = [person["_tokens"]]
            if filing["officeholder_id"] in published_holders:
                names.append(name_tokens(published_holders[filing["officeholder_id"]]))
            # Or the maintainer's recorded decision, citing its evidence, names this officeholder
            # for this DocID: the confirmation the join's test could not make, which is what the
            # route exists for. The README promised a decision could settle "a filing at a seat
            # other than the member's", and the refusal below reached such a row before any
            # decision was read, so the route was unreachable for the case it names. The Filing ID
            # must still agree, and is checked first (the Council's second reading of the annual
            # Signal, Seat A).
            by_decision = (
                adjudications.get(doc_id, {}).get("officeholder_id") == filing["officeholder_id"]
            )
            status, reason = ptr.verify(
                text,
                seat,
                doc_id,
                name_confirms=lambda printed, names=names, by_decision=by_decision: (
                    by_decision or any(known <= tokens(printed) for known in names)
                ),
            )
            derived = dict(filing, source=dict(filing["source"], content_hash=capture["sha256"]))
            # A report that is not a transaction report gains what its own header prints about
            # it (its type, year and date; on an extension, its length and due dates), because a
            # Signal about an annual report reads the document's words and never the index's code
            # (docs/design/the-annual-report-signal.md). The document's hash is the row's own
            # source.content_hash, so every field read sits beside the bytes it was read from.
            if filing["source_form_code"] != PTR_CODE:
                facts = ptr.printed(text)
                if facts:
                    derived["printed"] = facts
            rows_read: list[dict] = []
            if status == "discrepancy":
                confirmed = any(known <= tokens(ptr.header(text)["name"]) for known in names)
                discrepancy = (
                    f"The document prints State/District {ptr.header(text)['seat']}; the "
                    f"Clerk's roster lists this officeholder at {seat}. The "
                    + (
                        "attribution rests on the filer's printed name and the Filing ID, which "
                        "both agree with the Clerk's index."
                        if confirmed
                        else "attribution rests on the maintainer's recorded decision and the "
                        "Filing ID, which agrees with the Clerk's index."
                    )
                )
                derived["notes"] = " ".join(p for p in (filing["notes"], discrepancy) if p)
            # A document whose header refuses the attribution has its rows read once the
            # maintainer has recorded a decision about that attribution, and not before. Leaving
            # the entry instead, as the fourth reading's fix did, discarded the reading whole, so
            # a reader that drifted or found a row was answered by no guard for exactly the
            # reports that already carry a recorded dispute, and the route the refusal names was
            # unreachable for them (the Council's fifth reading of S.1b, Seat C).
            settled = status != "contradiction" or decided(
                published["changes"], filing["id"], "officeholder_id"
            )
            if settled and filing["source_form_code"] == PTR_CODE:
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
            first_read = was["source"].get("content_hash") is None
            rows_read = as_corrected(rows_read, published["changes"], capture["sha256"])
            if not first_read and was["source"]["content_hash"] != capture["sha256"]:
                # Other bytes: a different file, compared strictly, a row more included (the
                # Council's third reading of S.1b, Seat G); what differs is recorded by row id
                # and field name, never by value, and the bytes are not kept (Seat B).
                differs = differences(before, rows_read)
                if status == "contradiction":
                    differs = [{"row": was["id"], "header": reason}, *differs]
                seen.replaced(was["id"], was["source"]["content_hash"], doc_source, differs)
                documents_replaced += 1 if differs else 0
                documents_same_reading += 0 if differs else 1
                continue
            if not first_read:
                # The file the register first read, served again: a recorded replacement ends,
                # and the page said a different file was the latest state for good (the
                # Council's fourth reading of S.1b, Seats B and C).
                seen.replaced(was["id"], was["source"]["content_hash"], doc_source, [])
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
            # The header's dispute is absorbed here, and only it: an attribution the maintainer
            # has decided is not refused again, and the build goes on, as the refusal above
            # promises (the Council's fourth reading of S.1b, Seat C). What the document's own
            # rows say still answers to the guards below.
            differs = reads_otherwise(before, rows_read, extend=True)
            if before and differs and was.get("extraction_confidence") == "structured":
                raise SystemExit(
                    f"refusing to build: the document behind {was['id']} holds the bytes its "
                    "rows were published from, and this build reads them otherwise. The source "
                    "did not change; the register's reading did, and a change to the "
                    "register's code must not rewrite what it published. Revert it; or, where "
                    "the document lists otherwise than the published rows, correct them with "
                    "tools/correct.py citing it, or record with --stands that a published value "
                    "stands, and the build goes on."
                )
            # Rows read after every published one from the very bytes the rows were published
            # from: the register's reading found them, the source did not change, and a reader
            # can find a row a report does not list. They enter only where the maintainer's
            # recorded decision says the report lists that many rows (the Council's third
            # reading of S.1b, Seat C). A document read for the first time adds its rows.
            accepted = accepted_rows(published["changes"], was["id"], capture["sha256"])
            if not first_read and len(rows_read) > len(before) and accepted != len(rows_read):
                extra = [t["id"] for t in rows_read[len(before) :]]
                raise SystemExit(
                    f"refusing to build: the document behind {was['id']} holds the bytes its "
                    f"rows were published from, and this build reads {len(extra)} "
                    f"{'row' if len(extra) == 1 else 'rows'} after every published one "
                    f"({', '.join(extra)}). The source did not change; the register's reading "
                    "did, and a row is not published on the reading's word. If the report "
                    f"lists {'it' if len(extra) == 1 else 'them'}, the maintainer records that "
                    f"it lists {len(rows_read)} rows: tools/correct.py --row {was['id']} "
                    f"--field transactions --now {len(rows_read)} --json --kind register, with "
                    "--because, --decided-by, --decided-at and the evidence flags "
                    "correct.py --help lists; --evidence-file must be the document these rows "
                    "were published from, whose SHA-256 the tool checks against the filing's "
                    "own source.content_hash. If the report does not list "
                    f"{'it' if len(extra) == 1 else 'them'}, revert the change to the reader."
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
    gone = collections.Counter(c["rows"] for c in new_changes if c["change"] == NOT_LISTED)
    confirmed = {}
    for rows_kind, n in sorted(gone.items()):
        if n > MANY_NOT_LISTED and expect_not_listed >= n:
            # The guard stopped this read, and a person let it through: every other decision in
            # the register is a row with a reason, and this one left no trace (the Council's
            # fourth reading of S.1b, Seats C and G).
            confirmed[rows_kind] = {"rows": n, "confirmed": expect_not_listed}
        if n > MANY_NOT_LISTED and n > expect_not_listed:
            raise Refusal(
                f"refusing to build: this read would record {n:,} rows of {rows_kind} as no "
                "longer listed by the source at once. A source that stops listing that many is "
                "likelier a change in the shape of its bytes, or a fault in serving them, than as "
                "many departures or withdrawals, and a change row is never undone. If the source "
                "no longer lists them, the maintainer confirms it: python "
                f"src/adapters/house-fd/build.py --year {year} --expect-not-listed {n}"
            )

    # The register's own figures for this year, over the rows it holds after this build, so a
    # second build from the same captures writes the same record (not this build's deltas).
    mine = [f for f in filings if index_year(f) == year]
    mine_ids = {f["id"] for f in mine}
    listed_now = {hid for hid in of_this_congress if latest_listing(changes, hid) != NOT_LISTED}
    with_a_filing = {f["officeholder_id"] for f in mine}
    reasons = dict(collections.Counter(reason_group(r["reason"]) for r in rejected))
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

    # The entry the register read this time for each row, where it differs from the entry the
    # row carries; a row this read did not find keeps the one read before. The next build
    # weighs a row's entry against this, the entry the register last read (Seat C).
    def entries_of(rows_: list[dict], now_of, key: str) -> dict[str, str]:
        out: dict[str, str] = {}
        for row_ in rows_:
            now = now_of(row_)
            if now is None:
                if (last_entries or {}).get(row_["id"]):
                    out[row_["id"]] = last_entries[row_["id"]]
            elif now != row_.get(key):
                out[row_["id"]] = now
        return out

    entries_read = {
        **entries_of(
            officeholders,
            lambda h: roster_now.get(h["biographical_ids"]["bioguide_id"]),
            "roster_entry_sha256",
        ),
        **entries_of(mine, lambda f: index_now.get(doc_of(f["id"])), "index_entry_sha256"),
    }
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
        # When the register read each document. A filing's source carries the document's URL and
        # fingerprint but the index's time, so nothing dated the read a replacement is measured
        # from (the Council's fourth reading of S.1b, Seat G).
        "read_at": {doc: source["retrieved_at"] for doc, source in sorted(read_documents.items())},
        **({"reader": ptr.reader_version()} if hasattr(ptr, "reader_version") else {}),
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

    for sha256, path in {**keeps, **seen.bytes}.items():
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
        **({"confirmed_not_listed": confirmed} if confirmed else {}),
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
        "entries_read": dict(sorted(entries_read.items())),
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


def accepted_rows(changes: list[dict], filing_id: str, sha256: str) -> int | None:
    """How many rows the maintainer's latest recorded decision says a report's bytes list,
    where one names these bytes; None where none does."""
    named = [
        c
        for c in changes
        if c["change"] == CORRECTED
        and c["row_id"] == filing_id
        and c.get("field") == "transactions"
        and c["capture"]["content_hash"] == sha256
    ]
    return named[-1]["now"] if named else None


def differences(published: list[dict], read: list[dict]) -> list[dict]:
    """Which rows of a document read otherwise than the rows published from it, by id and
    field name, never by value: a published row the reading does not list, a row it lists that
    none published, and each fact a published row carries that it gives another value (the
    Council's third reading of S.1b, Seat B). Empty when the reading is the published rows."""
    now = {t["id"]: t for t in read}
    out: list[dict] = []
    for was in published:
        got = now.get(was["id"])
        if got is None:
            out.append({"row": was["id"], "only_in": "the file first read"})
            continue
        fields = sorted(k for k, v in got.items() if was.get(k) is not None and was[k] != v)
        if fields:
            out.append({"row": was["id"], "fields": fields})
    ids = {t["id"] for t in published}
    out += [{"row": t["id"], "only_in": "this file"} for t in read if t["id"] not in ids]
    return out


def reads_otherwise(published: list[dict], read: list[dict], extend: bool = False) -> bool:
    """Whether a document's rows, as this build reads them, differ from those published from
    it: a published row missing or out of its place, or a fact a published row carries given
    another value. A fact a published row lacked is not a difference. With `extend`, for the
    very bytes the rows were published from, neither is a row read after every published
    one here; the build then asks whether the maintainer's decision accepts it (the Council's
    third reading of S.1b, Seat C). Other bytes are compared strictly by `differences`."""
    kept = read[: len(published)] if extend else read
    if [t["id"] for t in kept] != [t["id"] for t in published]:
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
        "--expect-not-listed",
        type=int,
        default=0,
        help="confirm that this read may record up to N rows of a file as no longer listed",
    )
    parser.add_argument(
        "--capture-key",
        action="store_true",
        help="print the key of the recorded captures and exit; same bytes, same key",
    )
    args = parser.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if args.capture_key:
        documents, docs_hash = load_docs_manifest()
        closed = closed_year(args.year, roster_congress(CACHE / "MemberData.xml"))
        if closed:
            _, docs_hash = decided_documents(documents, load_adjudications(ADJUDICATIONS)[0])
        print(
            capture_key(
                read_capture(f"{args.year}FD.zip"),
                None if closed else read_capture("MemberData.xml"),
                docs_hash,
            )
        )
        return 0
    return build(args.year, args.dry_run, args.expect_not_listed)


if __name__ == "__main__":
    sys.exit(main())
