#!/usr/bin/env python3
"""Render the register as static pages. NEXT.md Phase 3 I.4, I.5 and I.5b.

Reads the sealed store and writes `docs/build/`: one landing page and one page per
officeholder, shaped by ECOSYSTEM.md §1.3 and §1.4, each officeholder page carrying
its own struck seal from `tools/strike-mark.py`. Standard library. No template
engine, no client-side script, no font request, no image request. A page is one
self-contained file that says what the rows say and nothing more.

The register speaks to a reader who is not an expert and should not have to be, and
it speaks about people, so the Council's first reading of these pages (PR #27) set
three rules this file keeps:

  - A quiet page is a gap in the register's matching, never a statement about what a
    person filed, and it says so in those words with the count of rows set aside at
    that seat.
  - Every citation is a link: to the Standard in this repository and to the statute
    at its publisher. Every count on the landing is about the register or the chamber
    as a whole, and the chart shows every matched row, not a selected year.
  - The Clerk's codes are printed bare and called the Clerk's; the register does not
    name them.

Two invariants live at render time, stated here and checked by their own gates:

  §7   every officeholder page opens with the frame, inside its first header;
  §13  the roll is in seat order, an order of offices and not of persons, and no
       number on the landing is about a person.

What the page does not show: party. The row holds it; ECOSYSTEM.md §1.3 does not
list it and CLAUDE.md asks that the reader-facing register carry no party label.

    python src/surfaces/render.py
    python src/surfaces/render.py --out docs/build
"""

from __future__ import annotations

import argparse
import html
import importlib.util
import json
import os
import posixpath
import re
import sys
import unicodedata
from pathlib import Path

FRAME = "Presence in the register is not evidence of wrongdoing."
CLERK_SITE = "https://disclosures-clerk.house.gov/FinancialDisclosure"
HOUSE_FINDER = "https://www.house.gov/representatives/find-your-representative"
REPO = "https://github.com/jeb2-spec/Oath/blob/main/"
CHARTER = REPO + "CHARTER.md"
SOURCES_F1 = REPO + "SOURCES.md"
SUBJECTS_3 = REPO + "SUBJECTS.md#3-what-is-excluded-and-why"
SUBJECTS_1 = REPO + "SUBJECTS.md#1-the-rule"
STANDARDS_C1 = REPO + "STANDARDS.md#c1-oath-of-office"
STANDARDS_S1 = REPO + "STANDARDS.md#s1-ethics-in-government-act-of-1978"
STANDARDS_S2 = REPO + "STANDARDS.md#s2-stop-trading-on-congressional-knowledge-stock-act-of-2012"
USC_3331 = (
    "https://uscode.house.gov/view.xhtml?req=granuleid:USC-prelim-title5-section3331"
    "&num=0&edition=prelim"
)
USC_CH131 = (
    "https://uscode.house.gov/view.xhtml?req=granuleid:USC-prelim-title5-chapter131"
    "&num=0&edition=prelim"
)
STOCK_ACT = "https://www.govinfo.gov/app/details/PLAW-112publ105"
# The regulator's own statement of the rule and the form that defines the columns the
# register carries. Both read 2026-09-23; STANDARDS.md S.2 records them.
ETHICS_FD = "https://ethics.house.gov/financial-disclosure"
PTR_FORM = "https://ethics.house.gov/wp-content/uploads/2026/02/Final-CY-2025-PTR-Form-1.pdf"
# The Committee's memorandum on the reports' due dates, and the codified deadline. STANDARDS.md
# S.2 records both, and records that neither was read at its source by the session that cited
# them; a reading at the source is owed before the first Signal publishes.
PTR_DUE_MEMO = (
    "https://ethics.house.gov/wp-content/uploads/2023/01/FINAL-PTR-Due-Date-Pink-Sheet.pdf"
)
USC_13105 = (
    "https://uscode.house.gov/view.xhtml?req=granuleid:USC-prelim-title5-section13105"
    "&num=0&edition=prelim"
)
# What each Standard a Signal cites links to, in the order a reader walks them.
STANDARD_LINKS = {
    "S.2": (
        ("5 U.S.C. § 13105(l)", USC_13105),
        ("STOCK Act of 2012, Pub. L. 112-105", STOCK_ACT),
        ("the Committee on Ethics", ETHICS_FD),
        ("its form and instructions for CY 2025", PTR_FORM),
        ("its memorandum on due dates", PTR_DUE_MEMO),
        ("STANDARDS.md S.2", STANDARDS_S2),
    ),
}
ASSET_LEGEND = "https://fd.house.gov/reference/asset-type-codes.aspx"
LIMITATIONS_9 = REPO + "LIMITATIONS.md#9-private-citizens-are-out-of-scope"
# Where the course carries what the sealed doctrine should say about a filed document the
# register keeps no copy of: EVIDENCE §7 says the register may keep the bytes, and INVARIANTS
# §16 plans a bundle that holds them, so the practice cites the decision, not a section that
# says otherwise (the Council's fourth reading of S.1b, Seats A, C and G).
NEXT_D4 = REPO + "NEXT.md"
BYLAWS_5 = REPO + "BYLAWS.md#5-corrections"
BYLAWS_6 = REPO + "BYLAWS.md#6-corrections-and-supersessions-facts-stay-change-is-shown"

# The oath every member takes, verbatim. STANDARDS.md C.1; 5 U.S.C. § 3331, verified against
# uscode.house.gov on 2026-09-22; U.S. Const. Art. VI § 3. The same words for everyone.
OATH = (
    "I, ___, do solemnly swear (or affirm) that I will support and defend the Constitution "
    "of the United States against all enemies, foreign and domestic; that I will bear true "
    "faith and allegiance to the same; that I take this obligation freely, without any "
    "mental reservation or purpose of evasion; and that I will well and faithfully "
    "discharge the duties of the office on which I am about to enter. So help me God."
)
OATH_CITE = (
    f'The oath of office. <a href="{USC_3331}">5 U.S.C. § 3331</a>; U.S. Const. Art. VI § 3. '
    f'<a href="{STANDARDS_C1}">STANDARDS.md C.1</a>.'
)

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
REPRESENTATIVE = "United States Representative"

STATE_NAMES = {
    "AK": "Alaska",
    "AL": "Alabama",
    "AR": "Arkansas",
    "AZ": "Arizona",
    "CA": "California",
    "CO": "Colorado",
    "CT": "Connecticut",
    "DE": "Delaware",
    "FL": "Florida",
    "GA": "Georgia",
    "HI": "Hawaii",
    "IA": "Iowa",
    "ID": "Idaho",
    "IL": "Illinois",
    "IN": "Indiana",
    "KS": "Kansas",
    "KY": "Kentucky",
    "LA": "Louisiana",
    "MA": "Massachusetts",
    "MD": "Maryland",
    "ME": "Maine",
    "MI": "Michigan",
    "MN": "Minnesota",
    "MO": "Missouri",
    "MS": "Mississippi",
    "MT": "Montana",
    "NC": "North Carolina",
    "ND": "North Dakota",
    "NE": "Nebraska",
    "NH": "New Hampshire",
    "NJ": "New Jersey",
    "NM": "New Mexico",
    "NV": "Nevada",
    "NY": "New York",
    "OH": "Ohio",
    "OK": "Oklahoma",
    "OR": "Oregon",
    "PA": "Pennsylvania",
    "RI": "Rhode Island",
    "SC": "South Carolina",
    "SD": "South Dakota",
    "TN": "Tennessee",
    "TX": "Texas",
    "UT": "Utah",
    "VA": "Virginia",
    "VT": "Vermont",
    "WA": "Washington",
    "WI": "Wisconsin",
    "WV": "West Virginia",
    "WY": "Wyoming",
    "DC": "District of Columbia",
    "PR": "Puerto Rico",
    "GU": "Guam",
    "VI": "Virgin Islands",
    "AQ": "American Samoa",
    "AS": "American Samoa",
    "MP": "Northern Mariana Islands",
}

# A tile map: each state one square, placed roughly where it sits, every square the same
# size on purpose. (column, row). Codes without a place take the last row.
TILES = {
    "AK": (0, 0),
    "ME": (10, 0),
    "WI": (5, 1),
    "VT": (9, 1),
    "NH": (10, 1),
    "WA": (0, 2),
    "ID": (1, 2),
    "MT": (2, 2),
    "ND": (3, 2),
    "MN": (4, 2),
    "IL": (5, 2),
    "MI": (6, 2),
    "NY": (8, 2),
    "MA": (9, 2),
    "OR": (0, 3),
    "NV": (1, 3),
    "WY": (2, 3),
    "SD": (3, 3),
    "IA": (4, 3),
    "IN": (5, 3),
    "OH": (6, 3),
    "PA": (7, 3),
    "NJ": (8, 3),
    "CT": (9, 3),
    "RI": (10, 3),
    "CA": (0, 4),
    "UT": (1, 4),
    "CO": (2, 4),
    "NE": (3, 4),
    "MO": (4, 4),
    "KY": (5, 4),
    "WV": (6, 4),
    "VA": (7, 4),
    "MD": (8, 4),
    "DE": (9, 4),
    "AZ": (1, 5),
    "NM": (2, 5),
    "KS": (3, 5),
    "AR": (4, 5),
    "TN": (5, 5),
    "NC": (6, 5),
    "SC": (7, 5),
    "DC": (8, 5),
    "OK": (3, 6),
    "LA": (4, 6),
    "MS": (5, 6),
    "AL": (6, 6),
    "GA": (7, 6),
    "HI": (0, 7),
    "TX": (3, 7),
    "FL": (8, 7),
}

HELD_REASON = re.compile(r"surname matches a sitting member \((.+?), ([A-Z]{2}\d{2})\) but")
BY_HEADER = "Attributed by the document's own header"
BY_DECISION = "Attributed by the maintainer's recorded decision"

# Why a row at a member's own seat under the member's surname waits, read from the
# reason the adapter wrote; the first marker found names the kind. Each kind has the clause
# the page prints for it.
HELD_KINDS = (
    ("after_term", "the maintainer's recorded decision names an officeholder"),
    ("closed_after", "the index dates this row after those terms"),
    ("closed_open", "dated within those terms only by the maintainer's recorded decision"),
    ("no_filing_id", "carries no Filing ID line"),
    ("status", "not Member"),
    ("before_sworn", "before the swearing-in"),
    ("not_captured", "has not been captured"),
    ("left_other_name", "the row carries another given name"),
)
# Rows no decision can attribute: the register cannot show the officeholder in office when
# the index dates them (SUBJECTS.md §1). A page never says these wait for a decision.
UNDECIDABLE = frozenset({"after_term", "left_closed", "closed_after"})
# Kinds that say what a document printed while the register still read it; a Member the
# roster no longer lists keeps them for the rows set aside while it listed them.
DOC_KINDS = frozenset({"no_filing_id", "status", "before_sworn"})
HONORIFICS = frozenset({"jr", "sr", "ii", "iii", "iv", "v", "mr", "mrs", "ms", "miss", "dr", "hon"})

CSS = """
:root {
  color-scheme: light dark;
  --paper: #f7f4ec; --ink: #1c1b16; --ink-2: #605c50; --rule: #cfc9b8; --link: #1f3f9a;
  --serif: "Iowan Old Style", "Palatino Linotype", Palatino, Georgia, "Times New Roman", serif;
  --mono: ui-monospace, "SF Mono", Menlo, Consolas, "Liberation Mono", monospace;
  --measure: 46rem;
}
@media (prefers-color-scheme: dark) {
  :root { --paper: #141410; --ink: #e9e5d8; --ink-2: #a8a394; --rule: #3a382f; --link: #9ab6f5; }
}
* { box-sizing: border-box; }
html { background: var(--paper); color: var(--ink); font: 17px/1.55 var(--serif); }
body { max-width: var(--measure); margin: 0 auto; padding: 1.25rem 1rem 4rem; }
a { color: var(--link); text-decoration-thickness: 1px; text-underline-offset: .15em; }
a:focus-visible { outline: 2px solid var(--link); outline-offset: 2px; }
.skip { position: absolute; left: -999px; }
.skip:focus { left: 1rem; top: 1rem; background: var(--paper); padding: .5rem; }
/* rule-weight hierarchy: heavy under the masthead, hairline between sections,
   medium above the foot */
header.frame { border-bottom: 3px solid var(--ink); padding-bottom: 1rem; margin-bottom: 1.75rem; }
p.frame { margin: 0 0 1rem; color: var(--ink-2); font-style: italic;
          border-bottom: 1px solid var(--rule); padding-bottom: .5rem; }
.masthead { display: grid; grid-template-columns: 1fr auto; gap: 1.25rem; align-items: start; }
.kicker, h2, th, .door div p:first-child, tr.state th {
  font-variant-caps: all-small-caps; letter-spacing: .06em; color: var(--ink-2);
  font-weight: normal; }
.kicker { margin: 0 0 .25rem; font-size: .95rem; }
h1 { font-size: 2.1rem; line-height: 1.15; margin: 0 0 .35rem; font-weight: normal; }
p.office { margin: 0; color: var(--ink-2); }
p.lede { margin: .75rem 0 0; max-width: 34rem; }
figure.seal { margin: 0; width: 104px; }
figure.seal svg { width: 104px; height: 104px; display: block; margin: 0 auto .35rem; }
figcaption { font-size: .78rem; line-height: 1.35; color: var(--ink-2); }
blockquote.oath { margin: .25rem 0 1rem; padding: .6rem 1rem; border-left: 3px solid var(--rule); }
blockquote.oath p { margin: 0; font-style: italic; }
blockquote.oath footer { border: 0; margin: .4rem 0 0; padding: 0; font-size: .8rem; }
section { border-top: 1px solid var(--rule); padding-top: .9rem; margin-top: 1.75rem; }
h2 { font-size: 1rem; margin: 0 0 .6rem; }
.door { display: grid; grid-template-columns: repeat(auto-fit, minmax(13rem, 1fr)); gap: 1rem; }
.door div p { margin: 0; }
table { border-collapse: collapse; width: 100%; font-size: .95rem; }
caption { text-align: left; caption-side: bottom; padding: .5rem 0 0; font-size: .85rem;
          color: var(--ink-2); }
th, td { text-align: left; padding: .45rem .6rem .45rem 0; border-bottom: 1px solid var(--rule);
         vertical-align: top; }
th { font-size: .85rem; }
td.idx { font-family: var(--mono); font-size: .88rem; color: var(--ink-2); white-space: nowrap;
         width: 5.5rem; }
td.code { font-family: var(--mono); }
p.quiet { color: var(--ink-2); max-width: 36rem; }
h3 { font-size: 1rem; font-weight: 600; margin: 1.4rem 0 .3rem; }
h3 a { font-weight: 400; }
nav.reports { font-size: .85rem; color: var(--ink-2); line-height: 1.7; }
span.note { display: block; font-size: .82rem; color: var(--ink-2); }
td.amt { white-space: nowrap; }
dl.terms { display: grid; grid-template-columns: max-content 1fr; gap: .35rem 1rem; margin: 0; }
dl.terms dt, dl.terms dd { margin: 0; }
dl.terms dt { color: var(--ink); }
dl.terms dd { color: var(--ink-2); }
dl.terms dd b { font-weight: normal; color: var(--ink); font-variant-caps: all-small-caps;
                letter-spacing: .05em; }
/* the door: a tile map of states; equal squares on purpose */
.tiles { display: grid; grid-template-columns: repeat(11, minmax(0, 1fr)); gap: 4px;
         max-width: 34rem; margin-top: .5rem; }
.tile { aspect-ratio: 1; display: flex; flex-direction: column; align-items: center;
        justify-content: center; border: 1px solid var(--rule); text-decoration: none;
        color: var(--ink); font-family: var(--mono); font-size: .72rem; line-height: 1.1; }
.tile small { color: var(--ink-2); font-size: .6rem; }
.tile:hover, .tile:focus-visible { border-color: var(--ink); outline: none; }
.tile.nv { border-style: dashed; }
/* the state of the record: bars and a rhythm, numbers about the register, never about a person */
.record dl { display: grid; grid-template-columns: max-content 1fr; gap: .5rem 1rem;
             margin: 0 0 1rem; }
.record dt { font-family: var(--mono); font-variant-numeric: tabular-nums; text-align: right;
             color: var(--ink); }
.record dd { margin: 0; color: var(--ink-2); }
.bar { display: block; height: 6px; background: var(--rule); margin-top: .3rem; max-width: 24rem; }
.bar i { display: block; height: 100%; background: var(--ink); opacity: .55; }
.rhythm svg { width: 100%; max-width: 40rem; height: auto; display: block; color: var(--ink); }
figure.rhythm { margin: .5rem 0 0; }
tr.state th { padding-top: 1.1rem; color: var(--ink); border-bottom: 1px solid var(--ink); }
tr.vacant td { color: var(--ink-2); font-style: italic; }
footer { margin-top: 2.5rem; padding-top: .9rem; border-top: 2px solid var(--ink);
         font-size: .85rem; color: var(--ink-2); }
footer p { margin: .25rem 0; }
code { font-family: var(--mono); font-size: .88em; overflow-wrap: anywhere; }
@media (max-width: 40rem) {
  table { display: block; max-width: 100%; overflow-x: auto; }
  caption { position: sticky; left: 0; max-width: calc(100vw - 2rem); }
  .masthead { grid-template-columns: 1fr; }
  figure.seal { width: 88px; } figure.seal svg { width: 88px; height: 88px; }
  dl.terms, .record dl { grid-template-columns: 1fr; }
  .record dt { text-align: left; }
}
@media print {
  html { font-size: 11pt; background: #fff; color: #000; }
  .skip { display: none; } a { color: inherit; }
  figure.seal { width: 28mm; } figure.seal svg { width: 28mm; height: 28mm; }
  table, figure { break-inside: avoid; }
}
"""


# ---- reading --------------------------------------------------------------------------


def read_ndjson(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


# The Congress the pages speak of, with its terms, and the reads they rest on. main() sets it
# from the rows before anything renders, so no sentence leans on "this Congress" or on a
# roster whose date it does not give (the Council's reading of S.1b, Seats F and G).
ERA: dict = {
    "congress": 119,
    "began": "2025-01-03",
    "ends": "2027-01-03",
    "closed": False,
    "next": None,
    "roster_read": "",
    "last_roster_read": "",
    "first_read": "",
    "year": 2025,
}
# The captures the register keeps, by SHA-256, as paths in the repository.
KEPT: dict[str, str] = {}
# Every officeholder's name as the Clerk's roster listed it, by id, so a note about a row that
# moved names the other page in words and a link, never by an id (Seats A, D, E and F).
NAMES: dict[str, str] = {}
# The whole ledger of Findings: a correction can move a report, and its Finding with it, from
# one officeholder's page to another's, and each page names the other row of the chain.
LEDGER: list[dict] = []
# The day of the maintainer's recorded decision behind each report a decision attributed, by
# filing id, so the Signal page marks a Finding on such a report as it marks a moved one (the
# Council's fourth reading of S.1b, Seat D).
DECIDED: dict[str, str] = {}
DECIDED_ON = re.compile(r"Attributed by the maintainer's recorded decision of (\d{4}-\d{2}-\d{2})")
# The repository at the commit the pages are rendered from, for a file the next build replaces
# (the set-aside rows); main for everything that is kept for good (Seat G, third reading).
REPO_AT = {"commit": REPO}


def ordinal(n: int) -> str:
    suffix = "th" if 11 <= n % 100 <= 13 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


def era_of(run: dict, holders: list[dict]) -> dict:
    """The Congress of the register's rows and the reads behind them, from the rows and the
    adapter's run record; nothing typed."""
    congress = run.get("congress", {})
    starts = sorted({o["term_start"] for h in holders for o in h.get("offices", [])[:1]})
    n = congress.get("filing_year") or ((int(starts[0][:4]) - 1787) // 2 if starts else 119)
    roster = next((s for s in run.get("sources", []) if s["name"] == "MemberData.xml"), {})
    last = congress.get("last_roster_read") or roster.get("retrieved_at") or ""
    reads = [h.get("source", {}).get("retrieved_at", "") for h in holders]
    return {
        "congress": n,
        "began": f"{1787 + 2 * n}-01-03",
        "ends": f"{1789 + 2 * n}-01-03",
        "closed": bool(congress.get("closed")),
        "next": congress.get("roster"),
        "roster_read": (roster.get("retrieved_at") or last)[:10],
        "index_read": (
            next((s for s in run.get("sources", []) if s["name"].endswith("FD.zip")), {}).get(
                "retrieved_at"
            )
            or ""
        )[:10],
        "index_rows": run.get("counts", {}).get("index_rows"),
        "last_roster_read": last[:10],
        "closed_by": ((congress.get("closed_by") or {}).get("retrieved_at") or "")[:10],
        "first_read": min((r for r in reads if r), default="")[:10],
        "year": run.get("year", 2025),
    }


def congress_words(terms: bool = False) -> str:
    """ "the 119th Congress", with its terms when a reader needs the dates."""
    words = f"the {ordinal(ERA['congress'])} Congress"
    if terms:
        words += f" (terms from noon, {long_date(ERA['began'])}, to noon, {long_date(ERA['ends'])})"
    return words


def long_date(iso: str) -> str:
    months = [
        "January",
        "February",
        "March",
        "April",
        "May",
        "June",
        "July",
        "August",
        "September",
        "October",
        "November",
        "December",
    ]
    return f"{int(iso[8:10])} {months[int(iso[5:7]) - 1]} {iso[:4]}" if len(iso) >= 10 else iso


def load_changes(root: Path) -> dict[str, list[dict]]:
    """Every recorded change, by row id, oldest first: what a later capture of a source showed
    about a row the register had already published, and what a person corrected
    (data/changes.ndjson)."""
    out: dict[str, list[dict]] = {}
    rows = read_ndjson(root / "data" / "changes.ndjson")
    for change in sorted(rows, key=known_at):
        out.setdefault(change["row_id"], []).append(change)
    return out


def known_at(change: dict) -> tuple[str, str]:
    """When a change became known, to order it among the others: a read by the time it was
    read, a correction by the time it was decided, never by its evidence's retrieval, which can
    be earlier than the read it answers (the Council's third reading of S.1b, Seats B and G)."""
    return (change.get("decided_at") or change["capture"]["retrieved_at"], change["id"])


def listing(history: list[dict]) -> list[dict]:
    return [c for c in history if c["change"] in ("not listed", "listed again")]


def not_listed(changes: dict[str, list[dict]], rows: str) -> dict[str, dict]:
    """The rows of one file whose latest listing change is "not listed", with that change.
    Such a row stays, exactly as published; the page says so beside it."""
    out = {}
    for row_id, history in changes.items():
        seen = listing(history)
        if seen and seen[-1]["rows"] == rows and seen[-1]["change"] == "not listed":
            out[row_id] = seen[-1]
    return out


def capture_link(change: dict, words: str | None = None) -> str:
    """A link to the copy of the source a change cites: the copy the register kept, where it
    keeps one, else the source's own URL, and the words say which. Never "capture", which
    translates as an arrest or a seizure (the Council's second reading of S.1b, Seat F)."""
    sha = change["capture"]["content_hash"]
    kept = sha in KEPT
    href = REPO + KEPT[sha] if kept else change["capture"]["url"]
    words = words or ("the copy the register kept" if kept else "the source's own copy")
    return f'<a href="{esc(href)}">{esc(words)}</a>'


def when(change: dict) -> str:
    """The date of the read a change was recorded from; for a correction, of the decision."""
    moment = change.get("decided_at") or change["capture"]["retrieved_at"]
    return esc(moment[:10])


def recorded(change: dict) -> str:
    """The build that first sealed a change, for the end of the sentence that states it: a
    build named mid-sentence reads, translated, as the sentence's subject (Seat F)."""
    return f" (recorded in build {esc(change['build'])})" if change.get("build") else ""


def built_note(change: dict) -> str:
    return f"; recorded in build {esc(change['build'])}" if change.get("build") else ""


def earlier_builds(change: dict) -> str:
    """Where a reader finds a filer's own text as filed, after a correction moved it. The
    fingerprint the change row keeps is not the text, and saying only that would tell the
    reader the text is gone: every sealed build stays in this repository's history, and the
    builds before the one that sealed the correction carry the line (the Council's fourth
    reading of S.1b, Seats B, E and G)."""
    return (
        f"the builds before <code>{esc(change['build'])}</code>"
        if change.get("build")
        else "every build sealed before this correction"
    )


def cited(change: dict, words: str | None = None) -> str:
    """The copy a change cites and the build that first sealed it, in one parenthesis at the
    end of the sentence that states the change."""
    return f"({capture_link(change, words)}{built_note(change)})"


def latest_state(history: list[dict]) -> dict[str, dict]:
    """What the latest reads show about one row, by kind: the latest listing change, the
    latest replacement still in force, and, for each fact, the latest read that gives it
    otherwise than the row now carries, with the maintainer's decision about it where one was
    recorded after that read ("settled:<field>"). A decision answers the reads before it,
    never one after it; a read that gives what the row now carries shows as nothing (the
    Council's third reading of S.1b, Seats B, F and G)."""
    state: dict[str, dict] = {}
    listed = listing(history)
    if listed and listed[-1]["change"] == "not listed":
        state["not listed"] = listed[-1]
    replaced = [c for c in history if c["change"] == "replaced"]
    if replaced and replaced[-1]["now"] != replaced[-1]["was"]:
        state["replaced"] = replaced[-1]
    reads = {c["field"]: c for c in history if c["change"] == "read otherwise"}
    for field, c in reads.items():
        decisions = [d for d in history if d["change"] == "corrected" and d.get("field") == field]
        carried = decisions[-1]["now"] if decisions else c["was"]
        if c["now"] == carried:
            continue
        state[f"read otherwise:{field}"] = c
        answered = [d for d in decisions if known_at(d) >= known_at(c)]
        if answered:
            state[f"settled:{field}"] = answered[-1]
    return state


def decided_words(decision: dict) -> str:
    """What the maintainer decided about a fact a read gave otherwise, in a clause."""
    if decision["now"] == decision.get("was"):
        return f"the maintainer recorded on {when(decision)} that the published value stands"
    return f"the maintainer corrected it on {when(decision)}"


def moved_here(history: list[dict], holder_id: str) -> dict | None:
    """The correction that moved a filing's attribution to this officeholder, if one did."""
    moves = [
        c
        for c in history
        if c["change"] == "corrected"
        and c.get("field") == "officeholder_id"
        and c["now"] != c["was"]
    ]
    return moves[-1] if moves and moves[-1]["now"] == holder_id else None


def page_of(holder_id: str, to_root: str = "") -> str:
    """A link to an officeholder's page, named as the Clerk's roster listed them."""
    return (
        f'<a href="{to_root}{esc(slug(holder_id))}.html">{esc(NAMES.get(holder_id, holder_id))}</a>'
    )


def office_words(office_id: str) -> str:
    """An office id in words: its seat and the Congress whose terms began that year."""
    found = re.match(r"^of:us:house-([a-z]{2}\d{2}):(\d{4})$", office_id)
    if found is None:
        return esc(office_id)
    n = (int(found.group(2)) - 1787) // 2
    return f"{found.group(1).upper()} in the {ordinal(n)} Congress"


def esc(text: object) -> str:
    return html.escape(str(text) if text is not None else "", quote=True)


def slug(officeholder_id: str) -> str:
    return officeholder_id.replace(":", "-")


def load_striker(root: Path):
    spec = importlib.util.spec_from_file_location("strike_mark", root / "tools" / "strike-mark.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def folded_words(text: str) -> frozenset[str]:
    """The words of a name, folded: lowercase letters only, diacritics removed."""
    out = set()
    for word in re.split(r"[\s,.\-]+", text):
        folded = "".join(c for c in unicodedata.normalize("NFKD", word).lower() if c.isalpha())
        if folded:
            out.add(folded)
    return frozenset(out)


def surname_tokens(holder: dict) -> frozenset[str]:
    """The folded words of the roster surname: from the roster's own "Last, First" when the
    row carries it, else the last word of the legal name without a suffix."""
    common = holder.get("common_name") or ""
    if "," in common:
        return folded_words(common.split(",")[0])
    legal = re.sub(r",?\s+(Jr\.?|Sr\.?|II|III|IV)$", "", holder.get("legal_name", ""))
    return folded_words(legal.split()[-1]) if legal.split() else frozenset()


def held_kind(reason: str) -> str:
    for kind, marker in HELD_KINDS:
        if marker in reason:
            return kind
    return "other"


def held_kind_for(reason: str, source: dict, until: str = "", sworn: str = "") -> str:
    """A set-aside row's kind for one holder: `until`, where the roster stopped listing them,
    is the last roster read the register built from that listed them; `sworn`, where it lists
    them, the swearing-in it records."""
    kind = held_kind(reason)
    if kind in ("after_term", "closed_after"):
        return kind
    filed = iso_of(source.get("filing_date") or "")
    if not until:
        # A holder the roster lists: a row the index dates before their swearing-in is said by
        # that date, which is what a reader needs, rather than by what a document could not
        # confirm (the Council's fourth reading of S.1b, Seat F).
        if sworn and filed and filed < sworn and kind not in ("before_sworn", "closed_open"):
            return "before_sworn"
        return kind
    if filed and filed > until:
        return "left_closed"
    # A document kind is this holder's only where the register set the row aside while the
    # roster still listed them; the header check of a successor at the seat is about the
    # successor (the Council's fourth reading of S.1b, Seat D).
    kept = "; while it did, the row was set aside because " in reason
    if kept and (kind in DOC_KINDS or (kind == "other" and "the document prints" in reason)):
        return kind
    return "left_other_name" if kind == "left_other_name" else "left_open"


def current_office(holder: dict) -> dict:
    """The office a page shows: the latest term, and within it the one recorded last. A list
    of offices only grows at its end, earliest first (INVARIANTS.md §14)."""
    offices = holder.get("offices") or []
    if not offices:
        return {}
    return max(enumerate(offices), key=lambda p: (p[1].get("term_start") or "", p[0]))[1]


def seats_held(holder: dict) -> set[str]:
    return {o["seat"] for o in holder.get("offices", []) if o.get("seat")}


def holders_by_seat(holders: list[dict]) -> dict[str, list[dict]]:
    """Every officeholder the register holds at each seat. More than one when the roster no
    longer lists a Member whose rows the register keeps and lists another at the seat."""
    at: dict[str, list[dict]] = {}
    for holder in holders:
        for seat in seats_held(holder):
            at.setdefault(seat, []).append(holder)
    return at


def carries_surname(holder: dict, surname: str) -> bool:
    mine = surname_tokens(holder)
    return bool(mine) and mine <= folded_words(surname)


def given_name(holder: dict) -> str:
    """The first given name, folded: from the roster's own "Last, First" when the row carries
    it, else the first word of the legal name, honorifics and suffixes dropped."""
    common = holder.get("common_name") or ""
    given = common.split(",", 1)[1] if "," in common else holder.get("legal_name", "")
    words = [w for w in folded_words_list(given) if w not in HONORIFICS]
    return words[0] if words else ""


def folded_words_list(text: str) -> list[str]:
    return [
        "".join(c for c in unicodedata.normalize("NFKD", w).lower() if c.isalpha())
        for w in re.split(r"[\s,.\-]+", text)
        if w
    ]


def theirs(holders: list[dict], source: dict) -> list[dict]:
    """The holders of a row's seat whose surname the row carries; where two do (a successor of
    the same surname), the one whose given name it carries, and both only where it carries
    neither's (the Council's third reading of S.1b, Seat A)."""
    mine = [h for h in holders if carries_surname(h, source.get("last") or "")]
    if len(mine) > 1:
        first = folded_words(source.get("first") or "")
        named = [h for h in mine if given_name(h) and given_name(h) in first]
        mine = named or mine
    return mine


def iso_of(clerk_date: str) -> str:
    """A date as the Clerk's index writes it, M/D/YYYY, as YYYY-MM-DD; empty if it will not
    parse, and then no row is said to fall on either side of a day."""
    found = re.match(r"^(\d{1,2})/(\d{1,2})/(\d{4})$", clerk_date.strip())
    if found is None:
        return ""
    return f"{found.group(3)}-{int(found.group(1)):02d}-{int(found.group(2)):02d}"


def held_by_holder(
    rejected: list[dict], holders: list[dict], until: dict[str, str] | None = None
) -> dict[str, dict[str, int]]:
    """Rows set aside under an officeholder's surname, by officeholder and by why they wait.

    A fact about the index, not a score. A row counts for a holder when its state-district
    is a seat the holder holds in the register and its surname carries every word of that
    holder's surname, whatever reason the adapter gave, so the count is zero only when no
    such row exists. Two holders of one seat each count only the rows under their own
    surname. A held row whose reason names a member at a seat other than the row's own
    counts under "elsewhere" for that member, without naming the other seat.

    `until` gives, for each officeholder the roster stopped listing, the last roster read the
    register built from that listed them. For them a row is classed by what is known of it,
    whatever the adapter's reason begins with (the Council's third reading of S.1b): one the
    index dates after that day is not attributed to them while the roster does not list them
    ("left_closed"); one a document's header set aside while the register still read it keeps
    what the document printed; and any other the maintainer's recorded decision can attribute
    ("left_open"). A row is never said to be listed "since" they left: the register re-joins
    every row each build, and the roster's absence is not a fact about the row.
    """
    until = until or {}
    at = holders_by_seat(holders)
    counts: dict[str, dict[str, int]] = {}

    def add(holder_id: str, kind: str) -> None:
        mine = counts.setdefault(holder_id, {})
        mine[kind] = mine.get(kind, 0) + 1

    for row in rejected:
        source = row.get("source_row", {})
        seat = source.get("state_dst", "").strip()
        reason = row.get("reason", "")
        mine = theirs(at.get(seat, []), source)
        for holder in mine:
            add(
                holder["id"],
                held_kind_for(
                    reason,
                    source,
                    until.get(holder["id"], ""),
                    "" if holder["id"] in until else (holder.get("sworn_at") or ""),
                ),
            )
        if mine:
            continue
        named = HELD_REASON.search(reason)
        if named and named.group(2) != seat:
            for holder in at.get(named.group(2), []):
                if carries_surname(holder, named.group(1)):
                    add(holder["id"], "elsewhere")
    return counts


def held_reports_by_holder(rejected: list[dict], holders: list[dict]) -> dict[str, int]:
    """Set-aside rows coded P at a holder's seat under the holder's surname, by officeholder:
    the transaction reports the page must say are set aside and not read. Split by given name
    as the filings line is, so a successor of the same surname is not told that the Member
    before them filed a report of theirs (the Council's fourth reading of S.1b, Seat A)."""
    at = holders_by_seat(holders)
    counts: dict[str, int] = {}
    for row in rejected:
        source = row.get("source_row", {})
        if source.get("filing_type") != "P":
            continue
        for holder in theirs(at.get(source.get("state_dst", "").strip(), []), source):
            counts[holder["id"]] = counts.get(holder["id"], 0) + 1
    return counts


def held_rows_at_own_seat(rejected: list[dict], holders: list[dict]) -> int:
    """Of the rows the adapter holds for a person because the surname matches a member, those
    at a holder's own seat under that holder's surname, each counted once however many
    holders of the seat it could concern: the landing's "N of them" is counted from the same
    rows as its total (the Council's second reading of S.1b, Seats A, D and E)."""
    at = holders_by_seat(holders)
    return sum(
        1
        for row in rejected
        if row.get("reason", "").startswith("surname matches a sitting member")
        and any(
            carries_surname(h, row.get("source_row", {}).get("last") or "")
            for h in at.get(row.get("source_row", {}).get("state_dst", "").strip(), [])
        )
    )


def set_aside_counts(
    rejected: list[dict], holders: list[dict], until: dict[str, str] | None = None
) -> dict[str, int]:
    """The rows set aside, counted as the pages class them (the Council's third reading of
    S.1b, Seats A, D and E): those the maintainer's decision can attribute ("waits"), and of
    them those at an officeholder's own seat under their surname ("at_seat"); and those no
    decision attributes, because the register cannot show the officeholder in office on the
    date the index gives them ("shut"). A row under no officeholder's name is neither."""
    until = until or {}
    at = holders_by_seat(holders)
    out = {"waits": 0, "at_seat": 0, "shut": 0}
    for row in rejected:
        reason = row.get("reason", "")
        source = row.get("source_row", {})
        mine = theirs(at.get(source.get("state_dst", "").strip(), []), source)
        if mine:
            kinds = {held_kind_for(reason, source, until.get(h["id"], "")) for h in mine}
            if kinds <= UNDECIDABLE:
                out["shut"] += 1
            else:
                out["waits"] += 1
                out["at_seat"] += 1
        elif held_kind(reason) in UNDECIDABLE:
            out["shut"] += 1
        elif reason.startswith("surname matches a sitting member"):
            out["waits"] += 1
    return out


def held_total(at_seat: dict) -> int:
    """Rows set aside at members' own seats, from kinds dicts or bare counts; rows that
    sit at another seat are not at the member's own seat and are not counted here."""
    return sum(
        sum(n for k, n in v.items() if k != "elsewhere") if isinstance(v, dict) else int(v)
        for v in at_seat.values()
    )


def sworn_date(holder: dict) -> str:
    match = re.search(r"Sworn (\d{4}-\d{2}-\d{2})", holder.get("notes") or "")
    return match.group(1) if match else ""


def build_label(meta: dict) -> str:
    """One form for the build everywhere: id, then the first twelve hex of the digest."""
    return f"{meta.get('build', '')} (digest {str(meta.get('digest', ''))[:12]})"


def plural(n: int, one: str, many: str) -> str:
    return one if n == 1 else many


# ---- shared pieces ----------------------------------------------------------------------


def page(title: str, body: str) -> str:
    return (
        '<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f"<title>{esc(title)} · Oath</title>\n<style>{CSS}</style>\n</head>\n<body>\n"
        '<a class="skip" href="#main">Skip to the record</a>\n'
        f"{body}\n</body>\n</html>\n"
    )


def load_anchor(root: Path):
    spec = importlib.util.spec_from_file_location("anchor", root / "tools" / "anchor.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def anchor_of(root: Path, build: str) -> dict:
    """This build's anchor as its proof says it, read by tools/anchor.py's own reader. The
    state is never sealed, because a proof is completed after the seal (NEXT.md S.4)."""
    for b in load_anchor(root).builds(root):
        if b["build"] == build:
            return {"state": b["state"], "block": b["block"]}
    return {"state": "none", "block": None}


def anchor_words(meta: dict) -> str:
    anchor = meta.get("anchor", {})
    state, block = anchor.get("state", "none"), anchor.get("block")
    ledger = f'<a href="{REPO}ANCHORS.md">ANCHORS.md</a>'
    if state == "confirmed":
        return (
            f"Anchor: the digest is in Bitcoin block {block:,}, by OpenTimestamps; the proof "
            f"is beside the build's manifest, and {ledger} lists every build's."
        )
    if state == "pending":
        return (
            "Anchor: stamped with OpenTimestamps; the calendars hold the digest, awaiting a "
            f"Bitcoin block ({ledger})."
        )
    if state == "owed":
        return (
            "Anchor: the stamp is owed; the manifest is written and the OpenTimestamps "
            f"calendars have not yet taken it ({ledger})."
        )
    return "Anchor: none yet; the build has not been timestamped by an outside service."


def footer(meta: dict, home: bool, to_root: str = "../") -> str:
    anchor_line = anchor_words(meta)
    back = "" if home else f'<p><a href="{to_root}index.html">Every seat in the register</a></p>\n'
    return (
        "<footer>\n"
        f"{back}"
        f"<p>Build <code>{esc(build_label(meta))}</code>, from the sources as read up to "
        f"<code>{esc(meta.get('built_at'))}</code>; its anchor, a timestamp proof, fixes when it "
        f"provably existed. {anchor_line}</p>\n"
        "<p>Cite the build, not the page. Verify it: <code>python tools/verify.py</code>. "
        "The digest proves the rows these pages are rendered from are unchanged since sealing; "
        "it does not prove the Clerk's index is right. All dates the register read something "
        "are UTC; the dates the Clerk gives are the Clerk's.</p>\n"
        "</footer>"
    )


def seal_figure(svg: str, caption: str) -> str:
    return f'<figure class="seal">\n{svg}<figcaption>{esc(caption)}</figcaption>\n</figure>'


REQUIRES = (
    '<section class="requires">\n<h2>What this office requires</h2>\n'
    '<p class="quiet">The same for every member of the House. Each line cites the rule it '
    "comes from and links to it.</p>\n"
    f'<blockquote class="oath"><p>{esc(OATH)}</p><footer>{OATH_CITE}</footer></blockquote>\n'
    '<dl class="terms">\n'
    "<dt>Annual public financial disclosure</dt><dd>Required by the Ethics in Government Act "
    f'of 1978 (<a href="{USC_CH131}">5 U.S.C. chapter 131</a>); the House Committee on Ethics '
    f'administers it and the Clerk publishes it. <a href="{STANDARDS_S1}">STANDARDS.md S.1</a>.'
    "</dd>\n"
    "<dt>A report of each purchase, sale, or exchange of any stock, bond, commodity future, "
    "or other security over $1,000</dt><dd>Within 30 days of receiving notice of the "
    f'transaction and no later than 45 days after it. <a href="{STOCK_ACT}">STOCK Act of 2012, '
    f'Pub. L. 112-105</a>. <a href="{STANDARDS_S2}">STANDARDS.md S.2</a>. The House Committee '
    "on Ethics states it as the earlier of 30 days from being made aware of the transaction "
    f'or 45 days from the transaction (<a href="{ETHICS_FD}">Financial Disclosure</a>). '
    "The Committee's instructions keep some assets off these reports, among them widely held "
    "investment funds, real property and the Thrift Savings Plan, though some reports list them "
    f'(<a href="{PTR_FORM}">its form and instructions</a>). The Act does not '
    "prohibit the transactions it requires reported; a report listed below is a filing made "
    "under that requirement, as the Clerk records it.</dd>\n"
    "</dl>\n</section>"
)

# ---- signals ---------------------------------------------------------------------------

# Why a row was not evaluated, in the words a page uses; the Signal's own reason is the key.
NOT_EVALUATED_WORDS = {
    "dated before this Congress's swearing-in": (
        "dated before the swearing-in the roster records for the Congress, which is not the "
        "start of anyone's service"
    ),
    "marked Amended": "marked Amended by the filer",
    "marked Deleted": "marked Deleted by the filer",
    "no filing status printed": "with no filing status printed",
    "transaction dated after the report": "whose transaction is dated after the report",
    "transaction date not read": "whose transaction date could not be read",
    "no swearing-in date recorded": "for which the roster records no swearing-in date",
    "report date not read": "on a report whose date could not be read",
    "no asset code printed": "whose asset carries no code",
    "coded as a stock, named as an ETF": (
        "coded as a stock but named as an ETF, a widely held fund the Committee's instructions "
        "keep off these reports"
    ),
    "$1,000 or less": "of $1,000 or less, which the rule does not reach",
    "deadline before 2025": "whose deadline falls before 2025, under instructions not read here",
}
ASSET_CODED = re.compile(r"^asset coded (\w+)$")
SET_BY_WORDS = {"notification": "30 days after notice", "transaction": "45 days after the trade"}
CORRECTION_KIND = {"source": "the source changed", "register": "the register erred"}
NOT_A_DETERMINATION = (
    "A Finding describes a report against the rule it cites. It is not a determination by the "
    "House Committee on Ethics, which decides whether a report was late and what follows, and "
    "the register sees none of its decisions."
)
QUIET_NOT_A_DETERMINATION = (
    "A signal that did not fire is not a determination either: whether a report was on time is "
    "for the House Committee on Ethics, and the register sees none of its decisions."
)
MD_INLINE = re.compile(r"\[([^\]]+)\]\(([^)\s]+)\)|`([^`]+)`")
CORRECTION = re.compile(r":c\d+$")


def records_a_firing(row: dict) -> bool:
    """A ledger row that records a firing. A correction recording that a Signal does not fire
    on a report carries evidence with no row after the deadline (docs/signals/README.md)."""
    return bool((row.get("evidence") or {}).get("after", 1))


def fired_now(findings: list[dict], signal_id: str | None = None) -> list[dict]:
    """The Findings a page shows as fired: the current row of each chain, where that row
    records a firing. A superseded row stays in the ledger and is reached from its correction."""
    return [
        f
        for f in findings
        if f.get("superseded_by") is None
        and records_a_firing(f)
        and (signal_id is None or f["signal_id"] == signal_id)
    ]


def withdrawn_now(findings: list[dict], signal_id: str) -> list[dict]:
    """Current rows that record a Signal does not fire on a report it once fired on: a
    published Finding, withdrawn by correction. Shown as a withdrawal, never as a Finding."""
    return [
        f
        for f in findings
        if f.get("superseded_by") is None
        and not records_a_firing(f)
        and f["signal_id"] == signal_id
    ]


def supersedes(row: dict, findings: list[dict]) -> dict | None:
    """The row this one corrects, when it is a correction, found in the whole ledger: a
    correction that moved a report moved its Finding's chain across two officeholders' pages
    (the Council's third reading of S.1b, Seat E)."""
    return next((f for f in (LEDGER or findings) if f.get("superseded_by") == row["id"]), None)


def correction_why(row: dict) -> str:
    kind = CORRECTION_KIND.get(row.get("correction") or "")
    return f"because {kind}" if kind else "by correction"


def correction_line(row: dict, findings: list[dict]) -> str:
    """What a correction says about the row it replaces: its kind, and the reason in the
    correction's own words."""
    prior = supersedes(row, findings)
    if not CORRECTION.search(row["id"]) or prior is None:
        return ""
    reason = f" {esc(row['notes'])}" if row.get("notes") else ""
    elsewhere = (
        f", on the page of {page_of(prior['officeholder_id'])}, to whom the register had "
        "attributed the report"
        if prior.get("officeholder_id") not in (None, row.get("officeholder_id"))
        else ""
    )
    return (
        f'<p class="quiet">Corrected {correction_why(row)}: this row supersedes '
        f"<code>{esc(prior['id'])}</code>, first produced from the record as retrieved "
        f"{esc(prior.get('fired_at', ''))}{elsewhere}, which stays in the ledger, "
        f"<code>data/findings.ndjson</code>.{reason}</p>\n"
    )


def moved_findings_line(findings: list[dict], signal_id: str) -> str:
    """A Finding this page showed whose report the maintainer's correction attributes to
    another officeholder: said here, where it was, never simply gone (Seat E, third reading)."""
    lines = []
    for f in sorted(findings, key=lambda f: f["id"]):
        if f["signal_id"] != signal_id or not f.get("superseded_by"):
            continue
        head = next((g for g in LEDGER if g["id"] == f["superseded_by"]), None)
        if head is None or head.get("officeholder_id") in (None, f["officeholder_id"]):
            continue
        lines.append(
            f"The Finding <code>{esc(f['id'])}</code>, on the report the Clerk's index dates "
            f"{esc(f['evidence']['filed_at'])}, is superseded: the maintainer's recorded "
            f"correction attributes the report to {page_of(head['officeholder_id'])}, whose "
            "page shows the row that supersedes it; both rows stay in the ledger, "
            "<code>data/findings.ndjson</code>."
        )
    return "".join(f'<p class="quiet">{line}</p>\n' for line in lines)


def withdrawal_line(row: dict, findings: list[dict], filings_by_id: dict[str, dict]) -> str:
    report = filings_by_id.get(row["producing_filings"][0], {})
    prior = supersedes(row, findings)
    # The date the Finding was produced on, not the date a correction set (Seat B, N6).
    filed = (
        ((prior or {}).get("evidence") or {}).get("filed_at")
        or (row.get("evidence") or {}).get("filed_at")
        or report.get("filed_at", "")
    )
    first = CORRECTION.sub("", row["id"])
    reason = f" {esc(row['notes'])}" if row.get("notes") else ""
    return (
        f'<p class="quiet">On the report the Clerk\'s index dates {esc(filed)}, this signal '
        f"produced the Finding <code>{esc(first)}</code>"
        + (f", first produced {esc(prior.get('fired_at', ''))}" if prior else "")
        + f"; the correction <code>{esc(row['id'])}</code>, written {correction_why(row)}, "
        "records that it does not fire there on the register's rows as they now stand."
        f"{reason} Every row of the chain stays in the ledger, "
        "<code>data/findings.ndjson</code>.</p>\n"
    )


def signal_page_path(signal: dict) -> str:
    """Where a Signal's page lives in the site, per ECOSYSTEM.md §1.2."""
    return f"signals/{signal['slug']}/v{signal['version']}.html"


def md_href(href: str, base: str) -> str:
    """A link in a definition file, as a reader of the site can follow it: repository paths
    resolve against the file's own folder and open on GitHub."""
    if href.startswith(("http://", "https://", "#")):
        return href
    path, _, fragment = href.partition("#")
    resolved = posixpath.normpath(posixpath.join(base, path))
    return REPO + resolved + (f"#{fragment}" if fragment else "")


def md_inline(text: str, base: str) -> str:
    out, pos = [], 0
    for m in MD_INLINE.finditer(text):
        out.append(esc(text[pos : m.start()]))
        if m.group(1) is not None:
            label = re.sub(r"`([^`]+)`", r"<code>\1</code>", esc(m.group(1)))
            out.append(f'<a href="{esc(md_href(m.group(2), base))}">{label}</a>')
        else:
            out.append(f"<code>{esc(m.group(3))}</code>")
        pos = m.end()
    out.append(esc(text[pos:]))
    return "".join(out)


def md_blocks(text: str, base: str = "docs/signals/") -> str:
    """The definition's own words as HTML: paragraphs, links, code, and indented code blocks.
    Nothing else of Markdown is read, because a definition needs nothing else."""
    blocks = []
    for block in re.split(r"\n\s*\n", text.strip()):
        lines = block.split("\n")
        if all(line.startswith("    ") or not line.strip() for line in lines):
            code = "\n".join(line[4:] for line in lines)
            blocks.append(f"<pre><code>{esc(code)}</code></pre>")
        else:
            blocks.append(f"<p>{md_inline(' '.join(line.strip() for line in lines), base)}</p>")
    return "\n".join(blocks)


def first_paragraph(text: str) -> str:
    return re.split(r"\n\s*\n", text.strip())[0]


def standard_links(signal: dict) -> str:
    links = STANDARD_LINKS.get(signal["standard"]["id"], ())
    return "; ".join(f'<a href="{esc(url)}">{esc(label)}</a>' for label, url in links)


def reason_clause(counts: dict[str, int], sworn: str | None = None) -> str:
    """Rows not evaluated, by reason, in the page's words; the asset codes a Signal does not
    evaluate are gathered into one clause, each with its count."""
    coded = {m.group(1): n for reason, n in counts.items() if (m := ASSET_CODED.match(reason))}
    rest = {reason: n for reason, n in counts.items() if not ASSET_CODED.match(reason)}
    parts = []
    for reason, n in sorted(rest.items(), key=lambda item: (-item[1], item[0])):
        words = NOT_EVALUATED_WORDS.get(reason, reason).replace(
            "for the Congress", f"for {congress_words()}"
        )
        if reason == "dated before this Congress's swearing-in" and sworn:
            words = (
                f"dated before {sworn}, the swearing-in the roster records for "
                f"{congress_words()}, which does not say whether this officeholder served before it"
            )
        parts.append(f"{n:,} {words}")
    if coded:
        total = sum(coded.values())
        listed = ", ".join(
            f"{code} {n:,}" for code, n in sorted(coded.items(), key=lambda i: (-i[1], i[0]))
        )
        parts.append(
            f"{total:,} whose asset the report codes as a kind this signal does not evaluate "
            f"({listed}, in the Clerk's asset codes)"
        )
    return "; ".join(parts)


def which_quiet(
    outcomes: list[dict],
    held_reports: int = 0,
    sworn: str | None = None,
    fetched: set[str] | None = None,
) -> str:
    """What one Signal did with one officeholder's reports, fired or not: the silence named.
    `fetched` names the reports whose document the register holds; a report the Signal did not
    read and the register never fetched is said as not fetched, never as scanned paper (the
    Council's third reading of S.1b, Seats D and E)."""
    held = (
        f"{held_reports:,} {plural(held_reports, 'transaction report', 'transaction reports')} "
        f"at this seat under this surname {plural(held_reports, 'is', 'are')} set aside, not "
        "attributed to this officeholder and not evaluated."
        if held_reports
        else ""
    )
    if not outcomes:
        return (
            "No transaction report is attributed to this officeholder in the register, so there "
            "was nothing to evaluate. That is a fact about the register's matching, not a "
            "statement that no report was due." + (f" {held}" if held else "")
        )
    evaluated = [o for o in outcomes if o["state"] == "evaluated"]
    unread = [o for o in outcomes if o["state"] == "not read"]
    unfetched = [o for o in unread if fetched is not None and o.get("filing_id") not in fetched]
    unread = [o for o in unread if o not in unfetched]
    rows = sum(o["evaluated"] for o in outcomes)
    fired = [o for o in outcomes if o["finding_id"]]
    skipped: dict[str, int] = {}
    for o in outcomes:
        for reason, n in o["not_evaluated"].items():
            skipped[reason] = skipped.get(reason, 0) + n
    none_after = (
        "does the Clerk's index date the report later than the deadline the rule sets from the "
        "dates the report prints"
    )
    parts = []
    if rows:
        reports = sum(1 for o in evaluated if o["evaluated"])
        opening = (
            f"It evaluated {rows:,} {plural(rows, 'row', 'rows')} on {reports:,} "
            f"{plural(reports, 'report', 'reports')} attributed to this officeholder"
        )
        if fired and reports > len(fired):
            others = reports - len(fired)
            parts.append(
                f"{opening} and fired on {len(fired):,} of them, shown below; on the "
                f"{others:,} {plural(others, 'other', 'others')}, for none of the rows it "
                f"evaluated {none_after}."
            )
        elif fired:
            parts.append(
                f"{opening} and fired on {plural(len(fired), 'it', 'each of them')}, shown below."
            )
        else:
            parts.append(f"{opening}; for none of them {none_after}.")
    elif evaluated or unread or unfetched:
        parts.append("It could evaluate no row on the reports attributed to this officeholder.")
    if skipped:
        n = sum(skipped.values())
        parts.append(
            f"{n:,} {plural(n, 'row was', 'rows were')} not evaluated: "
            f"{reason_clause(skipped, sworn)}."
        )
    if unread:
        n = len(unread)
        parts.append(
            f"{n:,} {plural(n, 'report is', 'reports are')} fetched and not read: scanned "
            "paper, whose transaction dates are printed in the document, and the register reads "
            "no scanned document."
        )
    if unfetched:
        n = len(unfetched)
        parts.append(
            f"{n:,} {plural(n, 'report has', 'reports have')} not been fetched, so "
            f"{plural(n, 'it was', 'they were')} not read."
        )
    if held:
        parts.append(held)
    return " ".join(parts)


def which_silence(outcomes: list[dict], held_reports: int = 0) -> str:
    """The checklist's few words for a Signal that did not fire: which silence it is."""
    rows = sum(o["evaluated"] for o in outcomes)
    if rows == 1:
        return (
            "for the one row it evaluated, the Clerk's index does not date the report after the "
            "deadline"
        )
    if rows:
        return (
            f"for none of the {rows:,} rows it evaluated does the Clerk's index date the report "
            "after the deadline"
        )
    if outcomes and all(o["state"] == "not read" for o in outcomes):
        return "the reports attributed were not read: scanned paper, or not fetched"
    if outcomes:
        return "it could evaluate no row, for the reasons below"
    if held_reports:
        return "no transaction report is attributed; those at this seat are set aside"
    return "no transaction report is attributed"


def falls_on_words(falls_on: str) -> str:
    return f"a {falls_on}" if falls_on in ("Saturday", "Sunday") else f"{falls_on}, a holiday"


def finding_rows_table(finding: dict) -> str:
    """The rows after the deadline, grouped where their dates agree, so a report of eighty
    identical rows reads as one line with its count."""
    groups: dict[tuple, int] = {}
    for row in finding["evidence"]["rows"]:
        key = (
            row["transaction_date"],
            row["notified_date"],
            row["notification"],
            row["deadline"],
            row["set_by"],
            row["deadline_falls_on"],
            row["first_business_day_after"],
            row["notified_after_limit"],
            row["days_after_notice"],
            row["days_after"],
        )
        groups[key] = groups.get(key, 0) + 1
    body = []
    for key, n in sorted(groups.items(), key=lambda item: (item[0][3], item[0][0])):
        traded, notified, notification, deadline, set_by, falls_on, next_day, late, gap, days = key
        notice = esc(notified) if notified else "not printed"
        if notification != "applied":
            notice += f' <span class="note">not applied: {esc(notification)}</span>'
        elif late:
            after_notice = "the same day" if gap == 0 else f"{gap:,} {plural(gap, 'day', 'days')}"
            notice += (
                '<span class="note">after the 45-day limit had passed; the report is dated '
                f"{after_notice} after it</span>"
                if gap
                else '<span class="note">after the 45-day limit had passed; the report is '
                "dated the same day</span>"
            )
        due = esc(deadline)
        if falls_on:
            due += (
                f'<span class="note">{esc(falls_on_words(falls_on))}; the first business day '
                f"after it is {esc(next_day)}</span>"
            )
        body.append(
            "<tr>"
            f'<td class="idx">{n:,}</td>'
            f'<td class="idx">{esc(traded)}</td>'
            f'<td class="idx">{notice}</td>'
            f'<td class="idx">{due}</td>'
            f"<td>{esc(SET_BY_WORDS.get(set_by, set_by))}</td>"
            f'<td class="idx">{days:,}</td>'
            "</tr>"
        )
    rows = finding["evidence"]["after"]
    return (
        "<table>\n"
        f"<caption>The {rows:,} {plural(rows, 'row', 'rows')} of this report after the "
        "deadline, grouped where the dates agree. The deadline is the earlier of 30 days after "
        "the notification date the report prints and 45 days after the transaction date; it does "
        "not move for a weekend or a holiday. Days after count from the deadline to the date the "
        f"Clerk's index gives the report, {esc(finding['evidence']['filed_at'])}.</caption>\n"
        "<thead><tr><th>Rows</th><th>Transaction</th><th>Notified</th><th>Deadline</th>"
        "<th>Set by</th><th>Days after</th></tr></thead>\n"
        f"<tbody>\n{''.join(body)}\n</tbody>\n</table>"
    )


def finding_changes(finding: dict, changes: dict[str, list[dict]] | None) -> str:
    """What the latest reads show about the report a Finding was produced from, beside the
    Finding: the Finding stands as produced until the maintainer's correction supersedes it."""
    state = latest_state((changes or {}).get(finding["producing_filings"][0], []))
    lines = []
    if "not listed" in state:
        c = state["not listed"]
        lines.append(
            f"The Clerk's index read {when(c)} no longer lists this report, and does not say "
            f"why{recorded(c)}"
        )
    for key, c in state.items():
        if key.startswith("read otherwise:"):
            settled = state.get(f"settled:{c['field']}")
            lines.append(
                f"The Clerk's index read {when(c)} gives "
                f"{FIELD_WORDS.get(c['field'], c['field'])} as {esc(c['now'])}, where the "
                f"register published {esc(c['was'])}{recorded(c)}"
                + (f"; {decided_words(settled)}, citing the evidence" if settled else "")
            )
    if "replaced" in state:
        c = state["replaced"]
        lines.append(
            f"The Clerk's copy of this report read {when(c)} was a different file from the one "
            f"the register first read, and {differs_words(c)}; the Clerk does not say why"
            f"{recorded(c)}"
        )
    if not lines:
        return ""
    return (
        '<p class="quiet">'
        + "; ".join(lines)
        + ". This Finding stands as produced from the record as the register published it, "
        "until the maintainer's recorded correction, which cites the evidence and is published "
        f'with it, supersedes it (<a href="{BYLAWS_5}">BYLAWS.md §5</a> and '
        f'<a href="{BYLAWS_6}">§6</a>).</p>\n'
    )


def finding_mark(changes: dict[str, list[dict]], filing_id: str) -> str:
    """A report's mark on the Signal page, carrying its own guard, from the latest reads only:
    a row lifted alone must not read as a story (Seats A and F). Each read is dated (Seat G), a
    decision that answers it is said after it (Seats B, F and G), a report moved here by
    correction says so (Seat E), and so does one a recorded decision attributed (Seat D)."""
    history = changes.get(filing_id, [])
    state = latest_state(history)
    marks = []
    if "not listed" in state:
        marks.append(f"the index read {when(state['not listed'])} no longer lists it")
    if "replaced" in state:
        marks.append(f"the Clerk's copy read {when(state['replaced'])} was a different file")
    reads = [c for k, c in state.items() if k.startswith("read otherwise:")]
    settled = None
    if reads:
        c = max(reads, key=known_at)
        settled = state.get(f"settled:{c['field']}")
        marks.append(f"the index read {when(c)} gives one of its facts otherwise")
    out = ""
    if marks:
        out = (
            " ("
            + "; ".join(marks)
            + "; the Clerk gives no reason"
            + (f"; {decided_words(settled)}" if settled else "")
            + ")"
        )
    moves = [
        m
        for m in history
        if m["change"] == "corrected"
        and m.get("field") == "officeholder_id"
        and m["now"] != m["was"]
    ]
    if moves:
        out += f" (attributed here by the maintainer's correction of {when(moves[-1])})"
    elif filing_id in DECIDED:
        out += f" (attributed by the maintainer's recorded decision of {DECIDED[filing_id]})"
    return out


def finding_block(
    finding: dict,
    report: dict | None,
    findings: list[dict] | None = None,
    changes: dict[str, list[dict]] | None = None,
) -> str:
    doc_id = finding["producing_filings"][0].rsplit(":", 1)[1]
    copy = (
        f' · <a href="{esc(report["source"]["url"])}">the Clerk\'s copy</a>'
        if report and report.get("source", {}).get("url")
        else ""
    )
    return (
        f'<article class="finding" id="finding-{esc(doc_id)}">\n'
        f"<h4>Report the Clerk's index dates {esc(finding['evidence']['filed_at'])} · "
        f'<a href="#report-{esc(doc_id)}">its rows, as filed</a>{copy}</h4>\n'
        f"<p>{esc(finding['description'])}</p>\n"
        f"{finding_changes(finding, changes)}"
        f"{correction_line(finding, findings or [])}"
        f"{finding_rows_table(finding)}\n"
        f'<p class="quiet">Finding <code>{esc(finding["id"])}</code>, first produced from the '
        f"record as retrieved {esc(finding['fired_at'])}, from rows whose digest is "
        f"<code>{esc(finding['build_hash'][:12])}</code>. Regenerate it from the rows it names: "
        f"<code>python tools/rebuild.py {esc(finding['id'])}</code></p>\n"
        "</article>"
    )


def older_versions(signal: dict, all_signals: list[dict], findings: list[dict]) -> list[dict]:
    """Earlier versions of this Signal whose Findings on this page are still current rows."""
    return [
        s
        for s in sorted(all_signals, key=lambda s: s["version"])
        if s["slug"] == signal["slug"]
        and s["version"] < signal["version"]
        and (fired_now(findings, s["id"]) or withdrawn_now(findings, s["id"]))
    ]


def signals_section(
    signals: list[dict],
    findings: list[dict],
    outcomes: dict[str, list[dict]],
    filings_by_id: dict[str, dict],
    to_root: str = "../",
    held_reports: int = 0,
    sworn: str | None = None,
    all_signals: list[dict] | None = None,
    changes: dict[str, list[dict]] | None = None,
) -> str:
    """Signals that fired and Signals that did not, for one officeholder, grouped by Signal
    and never by severity (ECOSYSTEM.md §1.3; METHODOLOGY.md §10). Every defined Signal is
    named on every page, so silence is shown rather than assumed, and says which it is. A
    Finding an earlier version produced stays on the page, under that version, as published."""
    fired, quiet = [], []
    fetched = {
        fid for fid, f in filings_by_id.items() if (f.get("source") or {}).get("content_hash")
    }

    def blocks_for(signal_id: str) -> tuple[str, str]:
        mine = sorted(
            fired_now(findings, signal_id), key=lambda f: (f["evidence"]["filed_at"], f["id"])
        )
        withdrawn = "".join(
            withdrawal_line(f, findings, filings_by_id)
            for f in sorted(withdrawn_now(findings, signal_id), key=lambda f: f["id"])
        ) + moved_findings_line(findings, signal_id)
        found = "\n".join(
            finding_block(f, filings_by_id.get(f["producing_filings"][0]), findings, changes)
            for f in mine
        )
        return withdrawn, found

    for signal in signals:
        withdrawn, found = blocks_for(signal["id"])
        head = (
            f'<h3 id="signal-{esc(signal["slug"])}">{esc(signal["name"])}, version '
            f"{signal['version']}</h3>\n"
            f'<p class="quiet">{standard_links(signal)}. '
            f'<a href="{to_root}{signal_page_path(signal)}">What it reads, how, and what it does '
            "not say</a>. "
            f"{esc(which_quiet(outcomes.get(signal['id'], []), held_reports, sworn, fetched))}"
            "</p>\n"
        )
        earlier = ""
        for old in older_versions(signal, all_signals or [], findings):
            old_withdrawn, old_found = blocks_for(old["id"])
            earlier += (
                f'<h4 class="version">Version {old["version"]}, which version '
                f"{signal['version']} replaced</h4>\n"
                f'<p class="quiet">What version {old["version"]} produced on this officeholder\'s '
                "reports stays as published; version "
                f"{signal['version']}'s reading of the same reports is the one above.</p>\n"
                f"{old_withdrawn}{old_found}\n"
            )
        if found:
            said = md_inline(first_paragraph(signal.get("not_saying", "")), "docs/signals/")
            fired.append(
                head
                + (f'<p class="quiet">{said}</p>\n' if said else "")
                + withdrawn
                + found
                + earlier
            )
        else:
            quiet.append(
                head
                + f'<p class="quiet">{esc(QUIET_NOT_A_DETERMINATION)}</p>\n'
                + withdrawn
                + earlier
            )
    fired_html = (
        f'<p class="quiet">{esc(NOT_A_DETERMINATION)}</p>\n' + "\n".join(fired)
        if fired
        else '<p class="quiet">None, on the Signals defined in this build.</p>'
    )
    n = len(signals)
    quiet_html = (
        "\n".join(quiet)
        if quiet
        else '<p class="quiet">None: '
        + ("the one signal" if n == 1 else f"each of the {n:,} signals")
        + " defined in this build fired, above.</p>"
    )
    if not signals:
        fired_html = '<p class="quiet">None. No signal is defined in this build.</p>'
        quiet_html = '<p class="quiet">None to list.</p>'
    return (
        f'<section id="signals">\n<h2>Signals that fired</h2>\n{fired_html}\n</section>\n'
        f"<section>\n<h2>Signals that did not fire</h2>\n{quiet_html}\n</section>"
    )


def signal_check_line(
    signals: list[dict],
    findings: list[dict],
    outcomes: dict[str, list[dict]] | None = None,
    held_reports: int = 0,
) -> str:
    """The checklist's line for Signals on one officeholder's page, naming which silence."""
    if not signals:
        return "<b>none defined</b> · so none can fire, for anyone."
    parts = []
    for signal in signals:
        n = len(fired_now(findings, signal["id"]))
        state = (
            f'fired on {n:,} {plural(n, "report", "reports")}, <a href="#signals">below</a>'
            if n
            else "did not fire: "
            + which_silence((outcomes or {}).get(signal["id"], []), held_reports)
        )
        parts.append(f"{esc(signal['name'])}, version {signal['version']}: {state}")
    n = len(signals)
    return f"<b>{n} defined</b> · " + "; ".join(parts) + "."


class Raw(str):
    """A glossary entry that carries its own links; every other entry is escaped."""


def how_to_read(person: bool) -> str:
    rows = [
        (
            "The oath",
            "The words every member speaks on taking the seat, printed as the statute gives them "
            "and linked to it. It is the standard the register sets the record beside.",
        ),
        (
            "The Clerk",
            "The Clerk of the U.S. House of Representatives, the House officer who publishes "
            "Members' financial disclosures and the list of Members by seat.",
        ),
        (
            "The roster",
            "That list, as the Clerk publishes it, read on the date shown. It lists who holds each "
            "seat when it is read; it does not say when or why a person no longer does.",
        ),
        (
            "A Congress",
            f"The House's numbered two-year term: the {ordinal(ERA['congress'])} is the term from "
            f"noon on {long_date(ERA['began'])} to noon on {long_date(ERA['ends'])} (U.S. Const. "
            "amend. XX, section 1).",
        ),
        (
            "Dates",
            "A date on which the register read something is a UTC date. A date the Clerk gives, "
            "for a filing or a transaction, is the Clerk's or the filer's own.",
        ),
        (
            "A note beside a row",
            "What a later reading of the source showed about a row the register had published "
            "(no longer listed, listed again, a fact stated otherwise, or a different file for "
            "a document), or the maintainer's correction citing the evidence, with the date, and "
            "a link to the copy of the roster or the index the register kept, or to the evidence. "
            "The row itself stays as published, unless the maintainer's correction moved a fact, "
            "which the note says. The source does not say why a row changed, and the register "
            "does not guess.",
        ),
        (
            "A copy the register kept",
            "The Clerk's roster or index as the register read it on the date shown, kept in its "
            "repository and named by its SHA-256 fingerprint, so anyone can check that a note "
            "says what that copy shows, after the Clerk serves something else. The register "
            "keeps the copies its notes cite, and no filed document; it does not keep every read.",
        ),
    ]
    if person:
        rows += [
            (
                "A row of the index",
                "A line in the Clerk's public index of financial disclosure documents that the "
                "register attributed to this officeholder, listed as the Clerk lists it.",
            ),
            (
                "How",
                "What attributed the row. Name: the name on the form matched the roster exactly. "
                "Document: the index wrote the name in another form, and the Clerk's document "
                "prints Status Member at this seat with this Filing ID. Decision: the "
                "maintainer's recorded decision, which cites the evidence and is published with "
                "it. Correction: the maintainer's recorded correction moved the row here from "
                "another officeholder, and the note beside it says why.",
            ),
            (
                "The document",
                Raw(
                    "The Clerk's own copy, which the register links to and keeps no copy of. A "
                    "document can carry the names of private people, and a kept copy would "
                    "outlast the Clerk's withdrawal or redaction of it; a private name a filer "
                    "wrote into a report's lines stays bound to that report and the Clerk's own "
                    f'copy, and is on no other page (<a href="{LIMITATIONS_9}">LIMITATIONS.md '
                    "§9</a>). Keeping no document is the register's own practice, decided at the "
                    f'Council\'s third reading of this change (<a href="{NEXT_D4}">NEXT.md '
                    "D.4</a> carries what the doctrine should say). Where a later read found the "
                    "Clerk serving a different file, the register records both files' "
                    "fingerprints and which rows read otherwise, never what they say."
                ),
            ),
            (
                "Fetched",
                "The day the register read the Clerk's index for this row as it published it. A "
                "row kept from an earlier build keeps that day; a later reading that showed the "
                "row otherwise is noted beside it.",
            ),
            (
                "A row of a report",
                Raw(
                    "One line of a transaction report, as the officeholder filed it: what was "
                    "bought, sold or exchanged, in which category of value, on what date, and when "
                    "the filer was notified. A line the filer marked Amended or Deleted in the "
                    "report's filing-status column is shown with that mark. The bracketed code "
                    "after an asset is the Clerk's asset type code "
                    f'(<a href="{ASSET_LEGEND}">legend</a>). The report\'s ID column, its '
                    "capital-gains mark and its IPO statement are not read by the register and do "
                    "not appear. A name a filer wrote into a report's own lines is carried as "
                    f'filed; <a href="{LIMITATIONS_9}">LIMITATIONS.md §9</a> says what the '
                    "register "
                    "does and does not do with it. The form that defines each column is linked "
                    "above the rows."
                ),
            ),
            (
                "Owner, as marked",
                "SP, DC or JT when the filer marked the asset as a spouse's, a dependent child's "
                'or jointly held. The form does not require the mark, so "not marked" says '
                "nothing about who holds the asset.",
            ),
        ]
    else:
        rows += [
            (
                "The roll",
                f"Every seat of the House in {congress_words()}, in seat order, with the name "
                "the Clerk's roster lists on the date the table gives. Seat order is an order of "
                "offices, not of people.",
            )
        ]
    rows += [
        (
            "Set aside",
            "A row of the Clerk's index that neither the name on the form nor the Clerk's "
            "document could attribute to an officeholder. It waits for the maintainer to decide "
            "by hand, with evidence, unless the page says no decision can attribute it; it is "
            "never guessed.",
        ),
        (
            "A signal",
            "A condition written down in advance, citing the rule it comes from, with a page that "
            "says what it reads, how it counts, and what it does not say. A change to one is a new "
            "version; the old one stays readable.",
        ),
        (
            "A finding",
            "One report on which a signal fired: the report, the rows, their dates and the "
            "arithmetic, and the command that regenerates it from the rows it names. It describes "
            "the report against the rule; it is not a determination by the House Committee on "
            "Ethics, which decides whether a report was late.",
        ),
        (
            "The seal",
            (
                "Struck from the officeholder's identifier and the build's digest. It changes with "
                "every build. It says nothing about the person."
                if person
                else "Every officeholder page carries one, struck from that officeholder's "
                "identifier and the build's digest. It changes with every build. It says nothing "
                "about the person."
            ),
        ),
        (
            "The build",
            "One sealed reading of the record, with a digest anyone can recompute. Cite the build, "
            "not the page.",
        ),
        (
            "The anchor",
            "A timestamp proof, made with OpenTimestamps and completed in a Bitcoin block, that a "
            "build's digest existed by a certain time. The footer says whether its stamp is "
            "owed, waiting for a block, or confirmed.",
        ),
        (
            "The maintainer",
            "The person who runs the register and answers for it. The maintainer's decisions and "
            "corrections cite the evidence, are rows of their own, and are published with the "
            "build.",
        ),
    ]
    body = "\n".join(
        f"<dt>{esc(k)}</dt><dd>{v if isinstance(v, Raw) else esc(v)}</dd>" for k, v in rows
    )
    return (
        '<section class="how" id="how-to-read">\n<h2>How to read this page</h2>\n'
        '<dl class="terms">\n'
        f"{body}\n</dl>\n</section>"
    )


# ---- the officeholder page --------------------------------------------------------------


HELD_CLAUSES = {
    "no_filing_id": "whose {docs} {carry} no Filing ID line (scanned paper, or a form that "
    "prints none) and cannot confirm the filer",
    "status": "whose {docs} {print} a filer status other than Member",
    "before_sworn": "dated by the index before the swearing-in the roster records for the Congress",
    "not_captured": "whose {docs} the register has not yet fetched",
    "other": "whose {docs} {print} another seat or another Filing ID, or were set aside for "
    "another recorded reason",
    "left_open": "dated on or before {until}, the last roster read the register built from "
    "that listed them: the name join attributes no row to a member the roster does not list, "
    "and the maintainer's recorded decision can attribute {it}",
    "closed_open": "listed by the index after the register closed the year and dated within "
    "the Congress's terms, whose {docs} the register has not read: the maintainer's recorded "
    "decision can attribute {it}",
    "left_other_name": "under another given name, whose {docs} the register has not read: the "
    "name join attributes no row to a member the roster does not list",
    "left_closed": "dated after {until}, the last roster read the register built from that "
    "listed them, which no decision attributes to them while the roster does not list them",
    "after_term": "that the maintainer's recorded decision attributes to them, dated by the "
    "index after the last day the register can show them in office",
    "closed_after": "dated by the index after the Congress's terms ended",
}


def aside_sentence(held_here, until: str = "") -> str:
    """The rows at this seat under this surname that wait, and why, from the adapter's
    reasons, and apart from them the rows no decision can attribute. `held_here` is the
    kinds dict from held_at_seat, or a bare count; `until`, for an officeholder the roster
    stopped listing, the last roster read that listed them."""
    kinds = dict(
        held_here if isinstance(held_here, dict) else ({"unknown": held_here} if held_here else {})
    )
    elsewhere = kinds.pop("elsewhere", 0)
    away = (
        f" {elsewhere} {plural(elsewhere, 'row', 'rows')} of the index under this surname "
        f"{plural(elsewhere, 'sits', 'sit')} at another seat; the register holds "
        f"{plural(elsewhere, 'it', 'them')} because the surname alone matched, and does not say "
        f"whose {plural(elsewhere, 'it is', 'they are')}."
        if elsewhere
        else ""
    )
    total = sum(kinds.values())
    if not total:
        return away

    def said(which: dict[str, int]) -> list[str]:
        return [
            f"{n} "
            + HELD_CLAUSES[kind].format(
                docs=plural(n, "document", "documents"),
                carry=plural(n, "carries", "carry"),
                mark=plural(n, "marks", "mark"),
                print=plural(n, "prints", "print"),
                until=esc(until),
                it=plural(n, "it", "them"),
            )
            for kind, n in which.items()
            if kind in HELD_CLAUSES
        ]

    waiting = {k: n for k, n in kinds.items() if k not in UNDECIDABLE}
    shut = {k: n for k, n in kinds.items() if k in UNDECIDABLE}
    opening = (
        f" {total} {plural(total, 'row', 'rows')} of the index at this seat "
        f"{plural(total, 'carries', 'carry')} this surname"
    )
    if not shut:
        why = f": {'; '.join(said(waiting))}" if said(waiting) else ""
        return (
            f"{opening} and {plural(total, 'is', 'are')} set aside for the maintainer to decide "
            f"by hand{why}." + away
        )
    parts = []
    if waiting:
        n = sum(waiting.values())
        why = f": {'; '.join(said(waiting))}" if said(waiting) else ""
        parts.append(
            f"{n} {plural(n, 'is', 'are')} set aside for the maintainer to decide by hand{why}"
        )
    n = sum(shut.values())
    parts.append(
        f"{n} {plural(n, 'is', 'are')} not attributed here: {'; '.join(said(shut))} "
        f'(<a href="{SUBJECTS_1}">SUBJECTS.md §1</a>)'
    )
    return f"{opening}. " + "; and ".join(parts) + "." + away


def quiet_words(sworn: str | None = None) -> str:
    """Which quiet a page with no attributed row is: an index that lists nothing, a Member the
    roster records as sworn after the Congress's terms began, or a gap in the matching; never
    a statement about what was filed (the Council's third reading of S.1b, Seat E)."""
    if ERA.get("index_rows") == 0:
        return (
            f"The Clerk's index as the register read it on {esc(ERA['index_read'])} lists no row, "
            "so there was nothing to match; this is not a statement about what was filed."
        )
    if sworn and ERA.get("began") and sworn > ERA["began"]:
        return (
            f"The Clerk's roster records their swearing-in on {esc(sworn)}, after the Congress's "
            "terms began; the register does not say whether a report was due from them, and "
            "this is not a statement about what was filed."
        )
    return "This is a gap in the register's name-matching, not a statement about what was filed."


def how_attributed(filing: dict, changes: dict[str, list[dict]] | None = None) -> str:
    """By the name on the form, by the document's own header, by a person's decision, or by
    the maintainer's correction that moved it here from another officeholder (the Council's
    third reading of S.1b, Seats B, F and G). What attributed a row is read from the row's own
    words, never from whether its document was read (the fourth reading, Seats C, E and G)."""
    if moved_here((changes or {}).get(filing["id"], []), filing["officeholder_id"]):
        return "correction"
    notes = filing.get("notes") or ""
    if notes.startswith(BY_HEADER):
        return "document"
    if notes.startswith(BY_DECISION):
        return "decision"
    return "name"


def documents_read(filings: list[dict]) -> tuple[int, int]:
    """How many of these filings' documents the register read, and how many it fetched
    but did not read: scanned paper, or a form whose schedules the register does not
    yet read. A read document carries a content hash and a structured extraction; an
    unread one carries the hash alone.
    """
    read = scanned = 0
    for filing in filings:
        if not filing.get("source", {}).get("content_hash"):
            continue
        if filing.get("extraction_confidence") == "structured":
            read += 1
        else:
            scanned += 1
    return read, scanned


def checks_section(
    holder: dict,
    filings: list[dict],
    held_here,
    signal_line: str = "",
    until: str = "",
    listings: str = "",
    changes: dict[str, list[dict]] | None = None,
) -> str:
    """What the register can and cannot check here. Identical in shape for everyone."""
    roster_read = holder.get("source", {}).get("retrieved_at", "")[:10]
    n = len(filings)
    if n:
        # Counted as the How column says it, a moved report as the correction that moved it,
        # never as the header of a document that printed another seat (the Council's fourth
        # reading of S.1b, Seat B), and a decided report as a decision (Seats C, E and G).
        how = [how_attributed(f, changes) for f in filings]
        clauses = []
        if how.count("document"):
            clauses.append(
                f"{how.count('document')} of them by the document's own header: the index writes "
                "the name in another form, and the Clerk's document prints Status Member at this "
                "seat with this Filing ID"
            )
        if how.count("decision"):
            clauses.append(
                f"{how.count('decision')}{'' if clauses else ' of them'} by the maintainer's "
                "recorded decision, which cites its evidence"
            )
        route = ", " + "; ".join(clauses) if clauses else ""
        index_line = (
            f"<b>in the register</b> · {n} {plural(n, 'row', 'rows')} of the Clerk's "
            f"{ERA['year']} index attributed to this officeholder{route}."
            f"{aside_sentence(held_here, until)}"
        )
        read, scanned = documents_read(filings)
        pending = n - read - scanned
        if read == n:
            documents = (
                "<b>read</b> · the register read each document, recorded its hash, and confirmed "
                "the seat and filing ID printed inside it against the roster; the transactions "
                "the reports list are below, as filed."
            )
        elif read or scanned:
            parts = [f"<b>partly read</b> · {read} of {n} documents read and hashed"]
            if scanned:
                parts.append(
                    f"{scanned} fetched and hashed, not read: scanned paper, or a form the "
                    "register does not yet read"
                )
            if pending:
                parts.append(f"{pending} not fetched")
            documents = "; ".join(parts) + ". Each link below opens the Clerk's own copy."
        else:
            documents = (
                "<b>not yet</b> · the register has not read the documents; each link below opens "
                "the Clerk's own copy."
            )
    else:
        aside = aside_sentence(held_here, until) or (
            " No row of the index at this seat carries this surname; rows the register could not "
            "match anywhere are counted in the state of the record."
        )
        index_line = (
            "<b>not yet matched</b> · the register attributes a row only on an exact name match "
            "against the Clerk's roster, or on the Clerk's document printing Status Member at "
            f"this seat with this Filing ID.{aside} "
            f"{quiet_words(holder.get('sworn_at'))}"
        )
        documents = "<b>not yet</b> · the register has not read any document for this record."
    return (
        '<section class="checks">\n<h2>What the register can check here</h2>\n'
        '<p class="quiet">The register reads what was filed and when. It does not read how this '
        "officeholder voted or what they decided, or what those decisions did, in the United "
        "States or beyond it; a quiet page says nothing about any of that.</p>\n"
        '<dl class="terms">\n'
        f"<dt>Identity</dt><dd><b>in the register</b> · from the Clerk's roster, read "
        f"{esc(roster_read)}.{listings}</dd>\n"
        f"<dt>Filings index</dt><dd>{index_line}</dd>\n"
        f"<dt>Documents</dt><dd>{documents}</dd>\n"
        f"<dt>Signals</dt><dd>{signal_line or signal_check_line([], [])}</dd>\n"
        "</dl>\n</section>"
    )


IDENTITY_FIELDS = ("legal_name", "common_name", "sworn_at")
FIELD_WORDS = {
    "filed_at": "the date filed",
    "source_form_code": "the code",
    "form_type": "the form",
    "officeholder_id": "the attribution",
    "office_id": "the office",
    "source.content_hash": "the document's bytes",
    "asset": "the asset, as named",
    "notes": "the report's own lines",
    "owner": "the owner, as marked",
    "transaction_date": "the transaction date",
    "notified_date": "the notification date",
    "legal_name": "the name",
    "common_name": "the name as listed",
    "sworn_at": "the swearing-in date",
}


def differs_words(change: dict) -> str:
    """What a later file of a document reads differently, from the change row's record of it:
    which rows and which facts, never what they say (the Council's third reading, Seat B)."""
    differs = change.get("differs")
    if differs is None:
        return "reads differently"
    if not differs:
        return "reads as the rows the register published from the first"
    fields = sorted({f for d in differs for f in d.get("fields", [])})
    changed = sum(1 for d in differs if d.get("fields"))
    gone = sum(1 for d in differs if d.get("only_in") == "the file first read")
    more = sum(1 for d in differs if d.get("only_in") == "this file")
    parts = []
    if any("header" in d for d in differs):
        parts.append("its header prints what does not attribute the report to this officeholder")
    if changed:
        named = ", ".join(FIELD_WORDS.get(f, f) for f in fields)
        parts.append(
            f"{changed} of the rows the register published read otherwise there, in {named}"
        )
    if gone:
        parts.append(f"{gone} of them {plural(gone, 'is', 'are')} not in it")
    if more:
        parts.append(f"it lists {more} {plural(more, 'row', 'rows')} the first file does not")
    return "; ".join(parts)


def cited_evidence(change: dict) -> str:
    """The evidence a correction cites: the copy the register kept, or, for a filed document,
    which the register never keeps, the source's own URL."""
    return cited(
        change,
        "the evidence, as the register kept it"
        if change["capture"]["content_hash"] in KEPT
        else "the evidence, at its source",
    )


def change_notes(history: list[dict], holder_id: str = "") -> str:
    """Every recorded change to one row, in the register's own voice, beside the row: what
    the source showed and when, that it does not say why, and the copy the register kept;
    and what the maintainer decided, why, and the evidence. The row itself stays as published
    unless a correction moved a fact, and the note says which."""
    notes = []
    for c in history:
        field = FIELD_WORDS.get(c.get("field", ""), c.get("field", ""))
        words = None
        if c["change"] == "not listed":
            doc_id = c["row_id"].rsplit(":", 1)[-1]
            what = (
                f"No longer in the Clerk's index read {when(c)}, which does not say why; the "
                "register keeps its row as published. The link opens the Clerk's copy while the "
                f'Clerk serves it, and <a href="{CLERK_SITE}">the Clerk\'s disclosure site</a> '
                f"can be searched for DocID {esc(doc_id)}"
            )
            words = "the copy of that index the register kept, a ZIP archive"
        elif c["change"] == "listed again":
            what = f"Listed again in the Clerk's index read {when(c)}"
            words = "the copy of that index the register kept, a ZIP archive"
        elif c["change"] == "read otherwise":
            later = [
                d
                for d in history
                if d["change"] == "corrected"
                and d.get("field") == c.get("field")
                and known_at(d) >= known_at(c)
            ]
            what = (
                f"The Clerk's index read {when(c)} gives {field} as {esc(c['now'])}; the register "
                f"published {esc(c['was'])}"
                + (
                    f", and the maintainer decided on {when(later[0])}, below"
                    if later
                    else ", and keeps it until the maintainer decides, citing the evidence"
                )
            )
            words = "the copy of that index the register kept, a ZIP archive"
        elif c["change"] == "replaced" and c["now"] != c["was"]:
            what = (
                f"The Clerk's copy of this document read {when(c)} was a different file from the "
                f"one the register first read, and {differs_words(c)}; the Clerk does not say "
                "why. The rows below are from the file first read. The register keeps neither "
                "file, because a filed document can carry the names of private people "
                f'(<a href="#how-to-read">the document</a>); the change row names each '
                "by its fingerprint"
            )
            words = "the Clerk's copy"
        elif c["change"] == "replaced":
            what = f"The Clerk's copy read {when(c)} was again the file the register first read"
            words = "the Clerk's copy"
        elif c.get("field") == "transactions":
            what = (
                f"The maintainer recorded on {when(c)} that this report's own file lists "
                f"{esc(c['now'])} rows, more than the {esc(c['was'])} the register first read "
                "from it; the rest were found by a later reading of the same file, and entered "
                f"by this decision: {esc(c.get('because', ''))}"
            )
        elif c.get("field") == "office_id" and any(
            d is not c
            and d["change"] == "corrected"
            and d.get("field") == "officeholder_id"
            and d.get("decided_at") == c.get("decided_at")
            for d in history
        ):
            continue  # the office moves with its attribution, in the note on the attribution
        elif c["now"] == c.get("was"):
            what = (
                f"The maintainer recorded on {when(c)} that {field} stands as published: "
                f"{esc(c.get('because', ''))}"
            )
        elif c.get("field") == "officeholder_id":
            what = (
                f"Corrected by the maintainer on {when(c)}: the register had attributed this "
                f"report to {page_of(c['was'])}, and this correction attributes it "
                + ("here" if c["now"] == holder_id else f"to {page_of(c['now'])}")
                + f". {esc(c.get('because', ''))}"
            )
        elif c.get("field") == "office_id":
            what = (
                f"Corrected by the maintainer on {when(c)}: the office was "
                f"{office_words(c['was'])}. {esc(c.get('because', ''))}"
            )
        elif "was_sha256" in c:
            what = (
                f"Corrected by the maintainer on {when(c)}: {field}, the filer's own text. The "
                "correction keeps a fingerprint of what it said, not the text; "
                f"{earlier_builds(c)} carry the line as filed, and every sealed build stays in "
                f"this repository's history. {esc(c.get('because', ''))}"
            )
        else:
            what = (
                f"Corrected by the maintainer on {when(c)}: {field} was {esc(c['was'])}. "
                f"{esc(c.get('because', ''))}"
            )
        cite = cited_evidence(c) if c["change"] == "corrected" else cited(c, words)
        notes.append(f'<span class="note">{what.rstrip(".")} {cite}.</span>')
    return "".join(notes)


def moved_away_line(moved_away: list[tuple[dict, dict]]) -> str:
    """Reports the register published on this page that the maintainer's correction attributes
    to another officeholder: named on the page they left, with the date, the reason and the
    evidence, never simply gone (the Council's third reading of S.1b, Seats A, D, E, F, G)."""
    if not moved_away:
        return ""
    n = len(moved_away)
    items = "; ".join(
        f"the report the Clerk's index dates {esc(filing['filed_at'])}, now on the page of "
        f"{page_of(filing['officeholder_id'])}, by the correction of {when(c)}: "
        f"{esc(c.get('because', '').rstrip('.'))} {cited_evidence(c)}"
        for filing, c in sorted(moved_away, key=lambda p: (p[0]["filed_at"], p[0]["id"]))
    )
    return (
        f'<p class="quiet">{n} {plural(n, "report", "reports")} the register published on this '
        f"page {plural(n, 'is', 'are')} attributed to another officeholder by the maintainer's "
        f"recorded correction, which cites the evidence: {items}. The rows stay in the register, "
        f'with the correction beside them (<a href="{BYLAWS_6}">BYLAWS.md §6</a>).</p>\n'
    )


def filings_section(
    filings: list[dict],
    held_here,
    changes: dict[str, list[dict]] | None = None,
    until: str = "",
    moved_away: list[tuple[dict, dict]] | None = None,
    holder_id: str = "",
    sworn: str | None = None,
) -> str:
    heading = "<h2>What the Clerk's index lists for this officeholder</h2>\n"
    year = ERA["year"]
    away = moved_away_line(moved_away or [])
    if not filings:
        return (
            f"<section>\n{heading}"
            f'<p class="quiet">The register has not yet matched any row of the Clerk\'s {year} '
            f"index to this name. {quiet_words(sworn)}{aside_sentence(held_here, until)} "
            f'<a href="{CLERK_SITE}">Search the Clerk\'s disclosure site directly.</a></p>\n'
            f"{away}</section>"
        )
    changes = changes or {}
    rows = []
    for f in sorted(filings, key=lambda f: (f["filed_at"], f["id"])):
        rows.append(
            "<tr>"
            f'<td class="idx">{esc(f["filed_at"])}</td>'
            f'<td class="code">{esc(f.get("source_form_code") or "")}</td>'
            f'<td><a href="{esc(f["source"]["url"])}">Open the Clerk\'s copy</a>'
            + change_notes(changes.get(f["id"], []), holder_id)
            + "</td>"
            f'<td class="idx">{esc(f["source"]["retrieved_at"][:10])}</td>'
            f'<td class="code">{how_attributed(f, changes)}</td>'
            "</tr>"
        )
    n = len(rows)

    def with_kind(*kinds: str) -> int:
        return sum(
            1 for f in filings if any(c["change"] in kinds for c in changes.get(f["id"], []))
        )

    reads, files, decided = (
        with_kind("not listed", "listed again", "read otherwise"),
        with_kind("replaced"),
        with_kind("corrected"),
    )
    return (
        f"<section>\n{heading}<table>\n"
        f"<caption>{n} {plural(n, 'row', 'rows')} of the Clerk's {year} index attributed to this "
        'officeholder, oldest first. "How" says what attributed the row: the name on the form '
        "matching the roster; the Clerk's document printing Status Member at this seat with this "
        "Filing ID; the maintainer's recorded decision, which cites the evidence and is "
        "published with it; or the maintainer's correction, which moved the row here from "
        "another officeholder and says why beside it. "
        "The one-letter code is the Clerk's own and the Clerk does not publicly "
        "define it; the register does not interpret it. Open the document to see what it is. "
        "Rows coded P are served from the Clerk's transaction-report path, which is the one code "
        f'the register files as a transaction report (<a href="{SOURCES_F1}">SOURCES.md F.1</a>).'
        + (
            f" A later read of the Clerk's index shows {reads} of them otherwise; each note "
            "says what and when, and links the copy of the index the register kept."
            if reads
            else ""
        )
        + (
            f" For {files} of them a later read found the Clerk serving a different file; each "
            "note says which rows read otherwise, and the register keeps neither file."
            if files
            else ""
        )
        + (
            f" For {decided} of them the maintainer recorded a correction, or that a value "
            "stands, citing the evidence; each note says what, when and why."
            if decided
            else ""
        )
        + "</caption>\n"
        "<thead><tr><th>Date filed</th><th>The Clerk's code</th>"
        "<th>The document</th><th>Fetched</th><th>How</th></tr></thead>\n<tbody>\n"
        + "\n".join(rows)
        + f"\n</tbody>\n</table>\n{away}</section>"
    )


TYPE_WORDS = {
    "purchase": "purchase",
    "sale": "sale",
    "sale-partial": "partial sale",
    "exchange": "exchange",
}
OWNER_WORDS = {
    "unmarked": "not marked",
    "spouse": "SP, spouse",
    "joint": "JT, jointly held",
    "dependent": "DC, dependent child",
}
LABELS_IN_NOTES = re.compile(
    r"(?=(?:Subholding of|Location, as filed|Description, as filed|Comments, as filed|"
    r"Filing status|Asset text unconfirmed|Amount printed as))"
)
NOTE_LEAD = re.compile(
    r"^Asset code (\S+) per the Clerk's legend \([^)]*\); type printed as [^.]+\.\s*"
)
EXACT = re.compile(r"Amount printed as (\$[\d,]+(?:\.\d{2})?)")


def amount_text(tx: dict) -> str:
    """The category of value as the form prints it, or the exact figure a filer entered."""
    exact = EXACT.search(tx.get("notes") or "")
    if exact:
        return exact.group(1)
    band = tx.get("amount_range") or {}
    low, high = band.get("min"), band.get("max")
    if low is None:
        return "not printed"
    if high is None:
        return f"Over ${low:,}"
    return f"${low:,} - ${high:,}"


def asset_cell(tx: dict) -> str:
    """The asset as named, the Clerk's code after it, and each of the report's own labelled
    lines beneath it on a line of its own. The filing status is shown in the Type cell and
    the exact-figure note in the Amount cell, so neither repeats here."""
    notes = tx.get("notes") or ""
    lead = NOTE_LEAD.match(notes)
    code = lead.group(1) if lead and lead.group(1) != "none" else ""
    rest = notes[lead.end() :].strip() if lead else notes.strip()
    cell = esc(tx.get("asset") or "")
    if code:
        cell += f' <span class="code">[{esc(code)}]</span>'
    for line in LABELS_IN_NOTES.split(rest):
        line = line.strip()
        if not line or line.startswith(("Filing status", "Amount printed as")):
            continue
        cell += f'<span class="note">{esc(line)}</span>'
    return cell


def type_cell(tx: dict) -> str:
    """The type as the form's box names it, with the row's filing status where the report
    marks one other than New."""
    word = TYPE_WORDS.get(tx["action"], tx["action"])
    status = (tx.get("filing_status") or "").strip()
    if status and status.lower() != "new":
        return f"{esc(word)}, marked {esc(status)}"
    return esc(word)


def marked_counts(rows: list[dict]) -> dict[str, int]:
    """How many rows the report marks with a filing status other than New, by status."""
    out: dict[str, int] = {}
    for t in rows:
        status = (t.get("filing_status") or "").strip()
        if status and status.lower() != "new":
            out[status] = out.get(status, 0) + 1
    return out


def marked_clause(rows: list[dict]) -> str:
    counts = marked_counts(rows)
    if not counts:
        return ""
    return ", " + ", ".join(f"{n} marked {esc(status)}" for status, n in sorted(counts.items()))


def transactions_section(
    filings: list[dict],
    transactions: list[dict],
    held_reports: int = 0,
    changes: dict[str, list[dict]] | None = None,
) -> str:
    """What the reports the register read list, as filed, grouped by report.

    The record, not a judgement of it: no total of amounts, no average, no comparison.
    A row the filer marked Amended or Deleted is shown with the mark in its Type cell and
    counted as a row. A report fetched and not read is named by its filed date and its
    rows are absent rather than guessed. A page with no transaction report attributed
    says so, and says how many such reports at the seat are set aside.
    """
    lead = (
        "<p>Every transaction listed in the reports the register has read, as filed. A Periodic "
        "Transaction Report is the form on which a member reports each purchase, sale or "
        "exchange of a stock, bond, commodity future or other security over $1,000, whether "
        "held by the member, the member's spouse or a dependent child "
        f'(<a href="{ETHICS_FD}">House Committee on Ethics</a>; <a href="{PTR_FORM}">the form and '
        f'its instructions</a>; <a href="{STANDARDS_S2}">STANDARDS.md S.2</a>). The Act does not '
        "prohibit the transactions it requires reported.</p>\n"
        "<p>Each row is one line of a report as the officeholder filed it: the date of the "
        "transaction, the date the filer was notified, the type marked, the owner marked, the "
        "asset as named, and the category of value the form provides for the total purchase or "
        "sale price, or the fair market value of an exchange. That category is the size of the "
        "transaction, not a gain or loss, which the form says is irrelevant to it; where a filer "
        "printed an exact figure instead of a category, the row carries the figure as the filer "
        "printed it. The form lets a filer mark an asset as a spouse's, a dependent child's or "
        "jointly held and does not require the mark, so a row that is not marked says nothing "
        "about ownership. A row the filer marked Amended or Deleted in the report's "
        "filing-status column is listed as filed with the mark shown; the register merges "
        "nothing, so a transaction reported on more than one report appears under each. The "
        "register interprets nothing here.</p>\n"
    )
    reports = sorted(
        (f for f in filings if f.get("source_form_code") == "P"),
        key=lambda f: (f["filed_at"], f["id"]),
    )
    held = (
        f'<p class="quiet">{held_reports} transaction '
        f"{plural(held_reports, 'report', 'reports')} at "
        f"this seat under this surname {plural(held_reports, 'is', 'are')} set aside and not "
        "attributed to this officeholder (see What the register can check here); none is read."
        "</p>\n"
        if held_reports
        else ""
    )
    if not reports:
        return (
            f'<section id="transactions">\n<h2>Transactions reported</h2>\n{lead}'
            f'<p class="quiet">No transaction report in the Clerk\'s {ERA["year"]} index is '
            f"attributed to this officeholder.</p>\n{held}</section>"
        )
    read = [f for f in reports if f.get("extraction_confidence") == "structured"]
    unread = [f for f in reports if f.get("extraction_confidence") != "structured"]
    unfetched = [f for f in unread if not (f.get("source") or {}).get("content_hash")]
    unread = [f for f in unread if f not in unfetched]
    by_report: dict[str, list[dict]] = {}
    for tx in transactions:
        by_report.setdefault(tx["filing_id"], []).append(tx)
    parts = [lead]
    if unread:
        dates = ", ".join(esc(f["filed_at"]) for f in unread)
        n = len(unread)
        parts.append(
            f'<p class="quiet">The {plural(n, "report", "reports")} filed {dates} '
            f"{plural(n, 'is', 'are')} fetched and not read (no Filing ID line: scanned paper, "
            f"or a form that prints none); {plural(n, 'its', 'their')} transactions are not listed "
            "here. "
            f"{plural(n, 'It is', 'They are')} linked above.</p>\n"
        )
    if unfetched:
        dates = ", ".join(esc(f["filed_at"]) for f in unfetched)
        n = len(unfetched)
        parts.append(
            f'<p class="quiet">The {plural(n, "report", "reports")} filed {dates} '
            f"{plural(n, 'has', 'have')} not been fetched, so {plural(n, 'its', 'their')} "
            f"transactions are not listed here. {plural(n, 'It is', 'They are')} linked "
            "above.</p>\n"
        )
    parts.append(held)
    if len(read) > 1:
        links = " · ".join(
            f'<a href="#report-{esc(f["id"].rsplit(":", 1)[1])}">{esc(f["filed_at"])} '
            f"({len(by_report.get(f['id'], []))})</a>"
            for f in read
        )
        parts.append(f'<nav class="reports">Reports, by date filed (rows): {links}</nav>\n')
    for f in read:
        doc_id = f["id"].rsplit(":", 1)[1]
        rows = sorted(by_report.get(f["id"], []), key=lambda t: (t["transaction_date"], t["id"]))
        n = len(rows)
        parts.append(
            f'<h3 id="report-{esc(doc_id)}">Report filed {esc(f["filed_at"])} · {n} '
            f"{plural(n, 'row', 'rows')}{marked_clause(rows)} · "
            f'<a href="{esc(f["source"]["url"])}">Open the Clerk\'s copy</a></h3>\n'
        )
        history = (changes or {}).get(f["id"], [])
        replaced = [c for c in history if c["change"] == "replaced"]
        if replaced:
            parts.append(f'<p class="quiet">{change_notes(replaced[-1:])}</p>\n')
        moved = moved_here(history, f["officeholder_id"])
        if moved:
            parts.append(
                f'<p class="quiet">Attributed to this officeholder by the maintainer\'s '
                f"correction of {when(moved)}, with the report's {n} "
                f"{plural(n, 'row', 'rows')}; the note beside the report above says why.</p>\n"
            )
        accepted = [
            c for c in history if c["change"] == "corrected" and c.get("field") == "transactions"
        ]
        first = accepted[-1]["was"] if accepted else None
        if accepted:
            parts.append(
                f'<p class="quiet">The rows after the first {esc(first)}, as the register numbers '
                "them, were found by a later reading of the same file and entered by the "
                f"maintainer's recorded decision of {when(accepted[-1])}; the note beside the "
                "report above says why.</p>\n"
            )
        if not rows:
            continue

        def noted(t: dict, accepted: list[dict] = accepted, first=first) -> str:
            own = [
                c
                for c in (changes or {}).get(t["id"], [])
                if not (c["change"] == "corrected" and c.get("field") == "officeholder_id")
            ]
            late = (
                f'<span class="note">Entered by the maintainer\'s recorded decision of '
                f"{when(accepted[-1])}.</span>"
                if first is not None and int(t["id"].rsplit(":", 1)[1]) > int(first)
                else ""
            )
            return change_notes(own) + late

        body = "\n".join(
            "<tr>"
            f'<td class="idx">{esc(t["transaction_date"])}</td>'
            f'<td class="idx">{esc(t["notified_date"])}</td>'
            f"<td>{type_cell(t)}</td>"
            f"<td>{esc(OWNER_WORDS.get(t['owner'], t['owner']))}</td>"
            f"<td>{asset_cell(t)}{noted(t)}</td>"
            f'<td class="amt">{esc(amount_text(t))}</td>'
            "</tr>"
            for t in rows
        )
        parts.append(
            f"<table>\n<caption>{n} {plural(n, 'row', 'rows')} of the report, oldest transaction "
            "date first; the report itself may list them in another order.</caption>\n"
            "<thead><tr><th>Transaction date</th><th>Notified</th><th>Type</th>"
            "<th>Owner, as marked</th><th>Asset, as named</th><th>Amount</th></tr></thead>\n"
            f"<tbody>\n{body}\n</tbody>\n</table>\n"
        )
    return (
        '<section id="transactions">\n<h2>Transactions reported</h2>\n'
        + "".join(parts)
        + "</section>"
    )


def render_officeholder(
    holder: dict,
    filings: list[dict],
    meta: dict,
    striker,
    held_here=0,
    transactions: list[dict] | None = None,
    held_reports: int = 0,
    signals: list[dict] | None = None,
    findings: list[dict] | None = None,
    outcomes: dict[str, list[dict]] | None = None,
    all_signals: list[dict] | None = None,
    changes: dict[str, list[dict]] | None = None,
    rejected_url: str = REPO + "data/rejected/house-fd/",
    moved_away: list[tuple[dict, dict]] | None = None,
) -> str:
    signals, findings, outcomes = signals or [], findings or [], outcomes or {}
    changes = changes or {}
    office = current_office(holder)
    seal = striker.strike(holder["id"], meta.get("digest", ""), ticks=0, bars=0)
    roster_read = holder.get("source", {}).get("retrieved_at", "")[:10]
    sworn = holder.get("sworn_at") or sworn_date(holder)
    off_roster = not_listed(changes, "officeholders").get(holder["id"])
    # The last roster read the register built from that listed them: the register cannot
    # show them in office after it, so no report the index dates later is attributed to them
    # while the roster does not list them (SUBJECTS.md §1). Not the last read that listed
    # them: a refresh that read the same bytes, or was not published, records no read
    # (the Council's third reading of S.1b, Seats B, D, E, F and G).
    until = (off_roster.get("before") or roster_read)[:10] if off_roster else ""
    office_line = (
        f"{esc(office.get('title', ''))} for {esc(office.get('seat', ''))} in "
        f"{esc(congress_words(terms=True))}"
    )
    if sworn:
        office_line += (
            f' · sworn in {esc(sworn)}, per <a href="#how-to-read">the Clerk\'s roster</a> read '
            f"{esc(roster_read)}"
        )
    identity_noted = any(
        key.startswith("read otherwise:") and c["field"] in IDENTITY_FIELDS
        for key, c in latest_state(changes.get(holder["id"], [])).items()
    )
    if (
        not off_roster
        and not ERA["closed"]
        and ERA["roster_read"] > roster_read
        and not identity_noted
    ):
        office_line += (
            f"; listed on the roster read {esc(ERA['roster_read'])}, the latest read in this build"
        )
    lines = []
    listings = ""
    if off_roster:
        before = (off_roster.get("before") or "")[:10]
        kept_before = off_roster.get("before_content_hash") in KEPT
        kept_copy = capture_link(
            off_roster,
            f"the copy of that roster the register kept; search it for {office.get('seat', '')}",
        )
        lines.append(
            f"The Clerk's roster read {when(off_roster)} no longer lists this officeholder "
            f"({kept_copy}{built_note(off_roster)})"
            + (
                f"; the last roster read the register built from before it, on {esc(before)}, "
                "listed them"
                + ("" if kept_before else ", and the register kept no copy of that one")
                if before
                else ""
            )
            + ". The roster does not say when or why a person leaves a "
            "seat, and neither does the register. Every row on this page was published while "
            "the roster listed them, or was attributed later by the maintainer's recorded "
            "decision or correction and is marked so; a note beside a row says what a later read "
            "showed. As for every officeholder, a published row stays "
            f"(<a href=\"{CHARTER}\">the Charter's fifth vow</a>). A report the Clerk's index "
            f"dates after {esc(until)}, the last roster read the register built from that listed "
            "them, is not attributed to them while the roster does not list them: the register "
            f'cannot show them in office then (<a href="{SUBJECTS_1}">SUBJECTS.md §1</a>). One '
            "dated earlier and listed by the index later can be, by the maintainer's recorded "
            "decision, which cites the evidence and is published with it; until then it is among "
            f'<a href="{rejected_url}">the rows set aside</a>, with the reason. Later reports: '
            f'<a href="{CLERK_SITE}">the Clerk\'s disclosure site</a>. Who holds this seat '
            f'now: <a href="{HOUSE_FINDER}">the House\'s own finder</a>.'
        )
    else:
        # A roster that stopped listing a Member and listed them again: a matter of record,
        # said where the page says what it can check, not in the masthead, where a lapse the
        # Clerk may have made would read as a departure (Seats A and D).
        episodes = listing(changes.get(holder["id"], []))
        if episodes:
            listings = (
                " "
                + " ".join(
                    f"The Clerk's roster read {when(c)} "
                    + ("did not list them" if c["change"] == "not listed" else "lists them again")
                    + f" {cited(c, 'the copy of that roster the register kept')}."
                    for c in episodes
                )
                + " The roster does not say why, and neither does the register."
            )
    # A name or a swearing-in date a later roster states otherwise, and the maintainer's
    # decision about it, said where the page says what it can check; a party is shown on no
    # page (Seats A, D and F; the Council's third reading, Seats B and F).
    state = latest_state(changes.get(holder["id"], []))
    for key, c in state.items():
        if key.startswith("read otherwise:") and c["field"] in IDENTITY_FIELDS:
            settled = state.get(f"settled:{c['field']}")
            listings += (
                f" The Clerk's roster read {when(c)} gives {FIELD_WORDS[c['field']]} as "
                f"{esc(c['now'])}; the register published {esc(c['was'])}"
                + (
                    f", and {decided_words(settled)}, citing the evidence"
                    if settled
                    else ", and keeps it until the maintainer decides, citing the evidence"
                )
                + f" {cited(c, 'the copy of that roster the register kept')}."
            )
    for c in changes.get(holder["id"], []):
        if c["change"] != "corrected" or c.get("field") not in IDENTITY_FIELDS:
            continue
        field = FIELD_WORDS[c["field"]]
        listings += (
            f" The maintainer recorded on {when(c)} that {field} stands as published: "
            if c["now"] == c.get("was")
            else f" Corrected by the maintainer on {when(c)}: {field} was {esc(c['was'])}. "
        ) + f"{esc(c.get('because', '').rstrip('.'))} {cited_evidence(c)}."
    if ERA["closed"]:
        lines.append(
            f"The {ordinal(ERA['congress'])} Congress's terms ended at noon on "
            f"{long_date(ERA['ends'])} "
            f"(U.S. Const. amend. XX, section 1). This page keeps what the register published "
            "for it."
            + (
                ""
                if off_roster
                else " A report the Clerk's index dates after the Congress's terms ended is not "
                "attributed here; one dated within them and listed by the index later can be, by "
                "the maintainer's recorded decision, which cites the evidence and is published "
                "with it."
            )
        )
    history = f'<p class="office">{" ".join(lines)}</p>\n' if lines else ""
    check_line = signal_check_line(signals, findings, outcomes, held_reports)
    section = signals_section(
        signals,
        findings,
        outcomes,
        {f["id"]: f for f in filings},
        "../",
        held_reports,
        sworn,
        all_signals or signals,
        changes,
    )
    head = (
        '<header class="frame">\n'
        f'<p class="frame">{esc(FRAME)}</p>\n'
        '<div class="masthead">\n<div>\n'
        '<p class="kicker">Oath · the register</p>\n'
        f"<h1>{esc(holder['legal_name'])}</h1>\n"
        f'<p class="office">{office_line}</p>\n'
        f"{history}"
        "</div>\n"
        + seal_figure(
            seal,
            f"Seal of this page at build {build_label(meta)}, struck from the officeholder's "
            "identifier and the build digest. It changes with every build. It says nothing about "
            "the person.",
        )
        + "\n</div>\n</header>"
    )
    body = (
        f'{head}\n<main id="main">\n{REQUIRES}\n'
        f"{checks_section(holder, filings, held_here, check_line, until, listings, changes)}\n"
        f"{filings_section(filings, held_here, changes, until, moved_away, holder['id'], sworn)}\n"
        f"{transactions_section(filings, transactions or [], held_reports, changes)}\n"
        f"{section}\n"
        f"{how_to_read(True)}\n"
        "</main>\n"
        f"{footer(meta, home=False)}"
    )
    return page(holder["legal_name"], body)


# ---- the landing page -------------------------------------------------------------------


def seats_by_state(offices: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for o in offices:
        counts[o["state"]] = counts.get(o["state"], 0) + 1
    return counts


def tile_map(offices: list[dict]) -> str:
    """The door. Every state in the data gets a tile; dashed tiles hold seats without a vote."""
    counts = seats_by_state(offices)
    voting = {o["state"] for o in offices if o.get("title") == REPRESENTATIVE}
    tiles, extra_col = [], 0
    for code in sorted(counts):
        n = counts[code]
        if code in TILES:
            col, row = TILES[code]
        else:
            col, row, extra_col = extra_col, 8, extra_col + 1
        cls = "tile" if code in voting else "tile nv"
        name = STATE_NAMES.get(code, code)
        tiles.append(
            f'<a class="{cls}" href="#state-{esc(code)}" '
            f'style="grid-column:{col + 1};grid-row:{row + 1}" '
            f'title="{esc(name)}, {n} {plural(n, "seat", "seats")}">'
            f"{esc(code)}<small>{n}</small></a>"
        )
    heading = (
        f"Find who represented you in the {ordinal(ERA['congress'])} Congress"
        if ERA["closed"]
        else "Find your representative"
    )
    return (
        f'<section class="finder" id="find">\n<h2>{esc(heading)}</h2>\n'
        '<p class="quiet">Choose your state to go to its delegation. Each square is one state, '
        "placed roughly where it sits, and every square is the same size on purpose. The small "
        "number is how many House seats the state has, which is a fact about the office and not "
        "about anyone in it. Dashed squares hold seats without a floor vote: the delegates and "
        f'the Resident Commissioner. Not sure of your district? <a href="{HOUSE_FINDER}">The '
        "House's own finder</a> takes a ZIP code.</p>\n"
        f'<div class="tiles" role="navigation" aria-label="States">{"".join(tiles)}</div>\n'
        "</section>"
    )


def rhythm_chart(filings: list[dict]) -> tuple[str, str, str, int]:
    """Every matched row by the month it was filed: the svg, first month, last month, total."""
    months: dict[str, int] = {}
    for f in filings:
        key = f.get("filed_at", "")[:7]
        if len(key) == 7 and key[4] == "-" and key[:4].isdigit() and key[5:].isdigit():
            months[key] = months.get(key, 0) + 1
    if not months:
        return "", "", "", 0
    first, last = min(months), max(months)
    year, month = int(first[:4]), int(first[5:])
    keys = []
    while f"{year:04d}-{month:02d}" <= last:
        keys.append(f"{year:04d}-{month:02d}")
        month += 1
        if month == 13:
            year, month = year + 1, 1
    counts = [months.get(k, 0) for k in keys]
    top = max(counts) or 1
    w, h, pad = 600, 190, 30
    bw = (w - 2 * pad) / len(keys)
    parts = [
        f'<line x1="{pad}" y1="{h - pad}" x2="{w - pad}" y2="{h - pad}" '
        'stroke="currentColor" stroke-width="0.8"/>'
    ]
    for i, (key, c) in enumerate(zip(keys, counts, strict=True)):
        bh = (h - 2 * pad) * c / top
        x = pad + i * bw + 2
        y = h - pad - bh
        mid = x + (bw - 4) / 2
        parts.append(
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{bw - 4:.1f}" height="{bh:.1f}" '
            'fill="currentColor" fill-opacity="0.35"/>'
        )
        if i % 3 == 0 or i == len(keys) - 1:
            label = f"{MONTHS[int(key[5:]) - 1]} {key[2:4]}"
            parts.append(
                f'<text x="{mid:.1f}" y="{h - pad + 14}" text-anchor="middle" font-size="9" '
                f'fill="currentColor">{label}</text>'
            )
        if c:
            parts.append(
                f'<text x="{mid:.1f}" y="{y - 3:.1f}" text-anchor="middle" font-size="9" '
                f'fill="currentColor">{c}</text>'
            )
    label_first = f"{MONTHS[int(first[5:]) - 1]} {first[:4]}"
    label_last = f"{MONTHS[int(last[5:]) - 1]} {last[:4]}"
    svg = (
        f'<svg viewBox="0 0 {w} {h}" role="img" aria-label="Matched index rows by month filed, '
        f'{label_first} to {label_last}, whole chamber">{"".join(parts)}</svg>'
    )
    return svg, label_first, label_last, sum(counts)


def bar(part: int, whole: int) -> str:
    pct = 0 if not whole else int(100 * part / whole)
    return f'<span class="bar"><i style="width:{pct}%"></i></span>'


def scanned_clause(scanned: int) -> str:
    """The landing's aside for documents fetched but not read, or nothing."""
    if not scanned:
        return ""
    return (
        f"; {scanned} more fetched and hashed, not read: scanned paper, or a form the "
        "register does not yet read"
    )


def state_of_record(
    meta: dict,
    run: dict,
    holders: list[dict],
    filings: list[dict],
    offices: list[dict],
    at_seat_total: int | dict,
    rejected_url: str,
    transactions: list[dict] | None = None,
    signal_runs: list[tuple[dict, dict]] | None = None,
    reach: dict[str, dict[str, int]] | None = None,
    changes: dict[str, list[dict]] | None = None,
    seated: int | None = None,
) -> str:
    """Numbers about the register and the chamber as a whole: each counts rows the register
    holds or seats of the chamber, and none is sorted by anything the register computes about a
    person. A Member the roster stopped listing is named in a list, never counted in a line
    that reads as about the chamber (the Council's third reading of S.1b, Seats B and F)."""
    transactions = transactions or []
    signal_lines = ""
    for signal, summary in signal_runs or []:
        by_state = summary.get("reports_by_state", {})
        read_reports = by_state.get("evaluated", 0)
        skipped = sum(summary.get("rows_not_evaluated", {}).values())
        fired = summary["reports_with_a_finding"]
        signal_lines += (
            f"<dt>{fired:,}</dt><dd>of the {read_reports:,} transaction reports read, on which the "
            f'signal <a href="{signal_page_path(signal)}">{esc(signal["name"])}</a>, version '
            f"{signal['version']}, fired: for {summary['rows_after']:,} of the "
            f"{summary['rows_evaluated']:,} rows it evaluated, the Clerk's index dates the report "
            f"after the deadline the rule sets, on reports attributed to "
            f"{summary['officeholders_with_a_finding']:,} officeholders. {skipped:,} rows were not "
            f"evaluated, each with a reason, and {by_state.get('not read', 0):,} reports were not "
            "read. "
            + (
                f"{coverage_sentence(reach[signal['id']])} "
                if reach and signal["id"] in reach
                else ""
            )
            + "A count about the register; no page ranks anyone by it"
            f"{bar(fired, read_reports)}</dd>\n"
        )
    if not signal_runs:
        signal_lines = (
            "<dt>0</dt><dd>signals defined, so 0 fired; silence is a legitimate result</dd>\n"
        )
    marked = sum(marked_counts(transactions).values())
    marked_note = f" ({marked} of them marked Amended or Deleted by the filer)" if marked else ""
    ERA.update(era_of(run, holders))
    changes = changes or {}
    every = [c for h in changes.values() for c in h]
    reads = sum(1 for c in every if c["change"] != "corrected")
    decisions = len(
        {
            (c.get("decided_at"), c.get("decided_by"), c.get("because"))
            for c in every
            if c["change"] == "corrected"
        }
    )
    gone = bool(not_listed(changes, "officeholders"))
    changes_line = ""
    if reads:
        # Said by kind: a read of the roster or the index cites bytes the register keeps, and a
        # read of a document cites both files' fingerprints and keeps neither (the Council's
        # fourth reading of S.1b, Seats F and G).
        docs = sum(1 for history in changes.values() for c in history if c["change"] == "replaced")
        cites = (
            "each a row of its own citing the read, with the copy of the roster or the index the "
            "register kept"
            if not docs
            else (
                "each a row of its own citing the read: the copy of the roster or the index the "
                "register kept, or, for a document, both files' fingerprints, since the register "
                "keeps no filed document"
            )
        )
        changes_line += (
            f"<dt>{reads:,}</dt><dd>{plural(reads, 'change', 'changes')} a later read of the "
            "Clerk's roster, index or documents showed about rows the register had published, "
            f"{cites}; a page shows each beside the row it concerns, except a party, which "
            "no page shows</dd>\n"
        )
    if decisions:
        changes_line += (
            f"<dt>{decisions:,}</dt><dd>{plural(decisions, 'decision', 'decisions')} the "
            "maintainer recorded, correcting a published fact or recording that it stands, each "
            "citing the evidence and shown beside the rows it concerns, except a party, which "
            "no page shows</dd>\n"
        )
    if reads or decisions:
        changes_line += (
            "<dt></dt><dd>A published row stays, gaining only facts it lacked; a fact it carries "
            "moves only by a correction the maintainer records with the evidence "
            f'(<a href="{REPO}data/changes.ndjson">the changes, as data</a>)</dd>\n'
        )
    # The seats are the offices the register holds; a seat is filled when the roster the
    # register last read lists someone at it, so a Member it no longer lists fills none.
    counts = run.get("counts", {})
    seats = len(offices) if ERA["closed"] else counts.get("seats", len(offices))
    filled = seated if seated is not None else counts.get("filled", len(holders))
    voting = sum(1 for o in offices if o.get("title") == REPRESENTATIVE)
    delegates = sum(1 for o in offices if o.get("title") == "Delegate")
    commissioners = sum(1 for o in offices if o.get("title") == "Resident Commissioner")
    # Over every officeholder the register holds, a Member the roster stopped listing among
    # them, as the sealed sentence counts (the Council's fourth reading of S.1b, Seat E).
    held_ids = {h["id"] for h in holders}
    with_row = len({f["officeholder_id"] for f in filings} & held_ids)
    matched = len(filings)
    read, scanned = documents_read(filings)
    how = [how_attributed(f, changes) for f in filings]
    by_header, by_decision = how.count("document"), how.count("decision")
    if isinstance(at_seat_total, dict):
        held, shut, at_seat_total = (
            at_seat_total["waits"],
            at_seat_total["shut"],
            at_seat_total["at_seat"],
        )
    else:
        held = run.get("rejected_by_reason", {}).get("surname matches a sitting member", 0)
        shut = 0
    sources = {s["name"]: s for s in run.get("sources", [])}
    year = run.get("year", 2025)
    index_src = sources.get(f"{year}FD.zip", {})
    roster_src = sources.get("MemberData.xml", {})
    fresh = ""
    if index_src:
        roster_words = (
            f"the {ordinal(ERA['congress'])} Congress's roster was last read "
            f"{esc(ERA['last_roster_read'])}, and the Clerk's roster read "
            f"{esc(ERA['closed_by'] or ERA['roster_read'])} listed the "
            f"{ordinal(ERA['congress'] + 1)}"
            if ERA["closed"]
            else f"the roster was read {esc(roster_src.get('retrieved_at', '')[:10])}"
        )
        fresh = (
            "When this build was made, the register read "
            f'<a href="{CLERK_SITE}">the Clerk\'s disclosure site</a>: its {year} index was last '
            f"modified {esc(index_src.get('last_modified', 'unknown'))} and the register read it "
            f"{esc(index_src.get('retrieved_at', '')[:10])}; {roster_words}. It read its sources "
            "every Monday at 09:17 UTC and published a new build when a source had changed and "
            "the maintainer merged it, or when the maintainer published a correction, dated "
            "beside the row it concerns; a refresh that failed published nothing. A date here is "
            "when a source was read, not when the build was published. "
        )
    svg, first, last, total = rhythm_chart(filings)
    nonvoting = ""
    if delegates or commissioners:
        nonvoting = (
            f"; {voting} with a floor vote, {delegates} delegate "
            f"{plural(delegates, 'seat', 'seats')} and {commissioners} resident commissioner "
            "without one"
        )
    chart = ""
    if svg:
        chart = (
            f'<figure class="rhythm">{svg}<figcaption>All {total:,} matched index rows by the '
            f"month they were filed, {esc(first)} to {esc(last)}, across every member. This is the "
            "rhythm of disclosure in the chamber; it is not a measure of anyone, and no "
            "person's count appears anywhere on this page.</figcaption></figure>\n"
        )
    return (
        '<section class="record" id="record">\n<h2>The state of the record</h2>\n'
        f'<p class="quiet">What the register holds at build <code>{esc(build_label(meta))}</code>. '
        "Every number here counts rows the register holds or seats of the chamber; none is a "
        "measure of anyone, and nothing here is sorted by anything the register computes about "
        "a person.</p>\n"
        "<dl>\n"
        f"<dt>{seats:,}</dt><dd>seats in the House in {esc(congress_words())}{nonvoting}; "
        f"{filled:,} filled and {seats - filled:,} vacant on the Clerk's roster read "
        f"{esc(ERA['roster_read'])}{bar(filled, seats)}</dd>\n"
        f"<dt>{with_row:,}</dt><dd>of the {len(held_ids):,} officeholders the register holds "
        f"for {esc(congress_words())} have at least one row of the Clerk's {year} index "
        f"attributed to them{bar(with_row, len(held_ids))}</dd>\n"
        f"<dt>{matched:,}</dt><dd>index rows the register holds, attributed and each linked to "
        f"the Clerk's own document; {by_header:,} of them by the document's own header where "
        "the index wrote the name in another form"
        + (
            f"; {by_decision:,} by the maintainer's recorded decision, which cites its evidence"
            if by_decision
            else ""
        )
        + "</dd>\n"
        f"<dt>{read:,}</dt><dd>of those {matched:,} documents read by the register so far, each "
        f"checked against the seat and filing ID printed inside it{scanned_clause(scanned)}; "
        f"the links open the Clerk's copies{bar(read, matched)}</dd>\n"
        f"<dt>{len(transactions):,}</dt><dd>rows the read reports list, as filed{marked_note}, "
        "each on its officeholder's page grouped by report; no page sums the amounts, averages "
        "them, or compares them with anyone else's</dd>\n"
        f"<dt>{held:,}</dt><dd>index rows set aside for the maintainer to decide by hand, "
        f"because the register does not guess; {at_seat_total:,} of them sit at an "
        "officeholder's own seat under their surname"
        + (
            f"; {shut:,} more {plural(shut, 'is', 'are')} not attributed, because the register "
            "cannot show the "
            "officeholder in office on the date the index gives them "
            f'(<a href="{SUBJECTS_1}">SUBJECTS.md §1</a>)'
            if shut
            else ""
        )
        + ". Whether a page is quiet is decided by whether the "
        "name on the form matched the roster, or the Clerk's document confirmed the filer at "
        "that seat, "
        f'not by what was filed. <a href="{rejected_url}">The '
        "rows, with reasons</a>; every row there is a line of the Clerk's index the register did "
        "not attribute, and presence in that file is not evidence of anything about anyone.</dd>\n"
        f"{changes_line}"
        f"{signal_lines}"
        "</dl>\n"
        + (
            f'<p class="quiet">Members of {esc(congress_words())} the Clerk\'s roster stopped '
            "listing during that Congress keep their pages, with everything the register "
            'published, <a href="#not-listed">listed below the seats</a> with the reads that '
            "last listed them and first did not.</p>\n"
            if gone
            else ""
        )
        + f'<p class="quiet">{fresh}The seal fixes exactly this reading.</p>\n'
        f"{chart}</section>"
    )


def signals_lede(signal_runs: list[tuple[dict, dict]]) -> str:
    if not signal_runs:
        return (
            '<p class="lede">This build holds no signals: no condition has been written against '
            "the record yet, so no page reports one. A page with no signal fired is the expected "
            "page. Quiet means no written condition is present in the record.</p>\n"
        )
    names = "; ".join(
        f'<a href="{signal_page_path(s)}">{esc(s["name"])}</a>, version {s["version"]}'
        for s, _ in signal_runs
    )
    n = len(signal_runs)
    return (
        f'<p class="lede">This build holds {n} {plural(n, "signal", "signals")}, written down in '
        f"advance and citing the rule {plural(n, 'it comes', 'they come')} from: {names}. "
        "Where one fires, the officeholder's page shows the report, the dates and the arithmetic, "
        "and what the signal does not say. A page where it did not fire says which silence it "
        "is: rows evaluated and none of them dated after the deadline, rows not evaluated and "
        "why, reports fetched and not read, or nothing to evaluate. None of it is a "
        "determination, which is the Committee on Ethics' to make.</p>\n"
    )


def coverage(
    outcomes: list[dict],
    rejected: list[dict],
    holders: list[dict] | None = None,
    until: dict[str, str] | None = None,
    fetched: set[str] | None = None,
) -> dict[str, int]:
    """Who a signal's run cannot reach, in counts, never in names: officeholders whose reports
    are all fetched and not read, those with some, those with rows dated before the
    Congress's swearing-in, and the transaction reports the index sets aside, split by whether
    the name on the row carries the surname of an officeholder the register holds, read from
    the rows and not from the adapter's reasons, which a closed year may set otherwise."""
    states: dict[str, set[str]] = {}
    before: set[str] = set()
    unfetched = 0
    for o in outcomes:
        state = o["state"]
        if state == "not read" and fetched is not None and o.get("filing_id") not in fetched:
            state, unfetched = "not fetched", unfetched + 1
        states.setdefault(o["officeholder_id"], set()).add(state)
        if o["not_evaluated"].get("dated before this Congress's swearing-in"):
            before.add(o["officeholder_id"])
    ptr = [r for r in rejected if r.get("source_row", {}).get("filing_type") == "P"]
    shut = 0
    if holders is None:
        held = sum(
            1 for r in ptr if r.get("reason", "").startswith("surname matches a sitting member")
        )
    else:
        at, until = holders_by_seat(holders), until or {}
        held = 0
        for r in ptr:
            source = r["source_row"]
            mine = theirs(at.get(source.get("state_dst", "").strip(), []), source)
            kinds = {
                held_kind_for(r.get("reason", ""), source, until.get(h["id"], "")) for h in mine
            }
            if mine and kinds <= UNDECIDABLE:
                shut += 1
            elif mine or any(carries_surname(h, source.get("last") or "") for h in holders):
                held += 1
    return {
        "paper_only": sum(1 for s in states.values() if s == {"not read"}),
        "some_paper": sum(1 for s in states.values() if "not read" in s and s != {"not read"}),
        "not_fetched": unfetched,
        "before_swearing_in": len(before),
        "set_aside_held": held,
        "set_aside_shut": shut,
        "set_aside_other": len(ptr) - held - shut,
    }


def coverage_sentence(c: dict[str, int]) -> str:
    """Who cannot appear among those on which a signal fired, and why, in counts."""
    paper, some, before = c["paper_only"], c["some_paper"], c["before_swearing_in"]
    held, other = c["set_aside_held"], c["set_aside_other"]
    shut, unfetched = c.get("set_aside_shut", 0), c.get("not_fetched", 0)
    aside = held + other + shut
    return (
        f"It cannot reach {paper:,} {plural(paper, 'officeholder', 'officeholders')} whose "
        "transaction reports are all scanned paper, which it does not read, or some of the "
        f"reports of {some:,} more"
        + (
            f"; it has not read {unfetched:,} "
            f"{plural(unfetched, 'report', 'reports')} the register has not fetched"
            if unfetched
            else ""
        )
        + "; it does not evaluate the rows dated before the swearing-in "
        f"the roster records for {congress_words()} on the reports of {before:,} "
        f"{plural(before, 'officeholder', 'officeholders')}; and it does not see the "
        f"{aside:,} {plural(aside, 'transaction report', 'transaction reports')} the index sets "
        f"aside, {held:,} under the surname of an officeholder the register holds, for the "
        "maintainer to decide by hand, "
        + (
            f"{shut:,} under such a surname and dated when the register cannot show that "
            "officeholder in office, which no decision attributes, "
            if shut
            else ""
        )
        + f"and {other:,} under names no officeholder the register holds bears, "
        "among them any report of a candidate, and of a Member who left before the register "
        f"first read the roster, on {esc(ERA['first_read'])} "
        f'(<a href="{SUBJECTS_1}">SUBJECTS.md §1</a>).'
    )


def render_signal_page(
    signal: dict,
    summary: dict,
    findings: list[dict],
    holders: list[dict],
    meta: dict,
    outcomes: list[dict] | None = None,
    reach: dict[str, int] | None = None,
    changes: dict[str, list[dict]] | None = None,
) -> str:
    """A signal's page (ECOSYSTEM.md §1.2; PIPELINE.md Stage 5): its definition in its own words,
    what it did in this build, who it cannot reach, and every report on which it fired, in
    seat order. A Member the roster no longer lists stays in seat order, marked, and a report
    a later capture shows otherwise is marked beside its date."""
    outcomes = outcomes or []
    changes = changes or {}
    off_roster = not_listed(changes, "officeholders")
    by_state = summary.get("reports_by_state", {})
    read_reports = by_state.get("evaluated", 0)
    fired = summary["reports_with_a_finding"]
    with_rows = sum(1 for o in outcomes if o["state"] == "evaluated" and o["evaluated"])
    no_rows = sum(1 for o in outcomes if o["state"] == "evaluated" and not o["evaluated"])
    skipped = summary.get("rows_not_evaluated", {})
    holder_of = {h["id"]: h for h in holders}
    current = fired_now(findings, signal["id"])
    withdrawn = len(withdrawn_now(findings, signal["id"]))
    by_holder: dict[str, list[dict]] = {}
    for f in current:
        by_holder.setdefault(f["officeholder_id"], []).append(f)
    rows = []
    for oid in sorted(by_holder, key=lambda i: (current_office(holder_of[i])["seat"], i)):
        holder = holder_of[oid]
        seat = current_office(holder)["seat"]
        page_url = f"../../officeholders/{esc(slug(oid))}.html"
        reports = ", ".join(
            f'<a href="{page_url}#finding-{esc(f["producing_filings"][0].rsplit(":", 1)[1])}">'
            f"{esc(f['evidence']['filed_at'])}</a>"
            + finding_mark(changes, f["producing_filings"][0])
            for f in sorted(by_holder[oid], key=lambda f: (f["evidence"]["filed_at"], f["id"]))
        )
        gone = off_roster.get(oid)
        mark = (
            '<span class="note">not on the Clerk\'s roster read '
            f"{esc(gone['capture']['retrieved_at'][:10])}, which gives no reason</span>"
            if gone
            else ""
        )
        rows.append(
            f'<tr data-id="{esc(oid)}" data-seat="{esc(seat)}">'
            f'<td class="idx">{esc(seat)}</td>'
            f'<td><a href="{page_url}#signal-{esc(signal["slug"])}">'
            f"{esc(holder['legal_name'])}</a>{mark}</td>"
            f"<td>{reports}</td></tr>"
        )
    table = (
        '<table id="fired" data-order="seat" data-lists="officeholders">\n'
        "<caption>Every report on which this signal fired in this build, under the officeholder "
        "the register attributes it to, in seat order, which is an order of offices and not of "
        "persons. "
        "An officeholder with more than one such report is listed once, with each report's date. "
        "Nothing here is a ranking and no number stands beside a name; each report is on its "
        "officeholder's page with its dates, its arithmetic, and what the signal does not say. "
        "Who cannot appear here, and why, is counted above: an officeholder whose transaction "
        "reports are all scanned paper cannot, whatever the reports show. What the register "
        "cannot read does not fall evenly across officeholders, so a count of Findings, or its "
        "absence, says nothing about any group of them. A name marked is one a roster the "
        f"register read for {esc(congress_words())} did not list, on the date the mark gives; "
        "the roster does not say why. A report marked is one a later read or the maintainer's "
        "correction shows otherwise, on the date the mark gives.</caption>\n"
        "<thead><tr><th>Seat</th><th>Name, as the Clerk's roster listed it</th>"
        "<th>Reports it fired on, by the date the Clerk's index gives them</th></tr></thead>\n"
        f"<tbody>\n{''.join(rows)}\n</tbody>\n</table>"
        if rows
        else '<p class="quiet">It fired on no report in this build.</p>'
    )
    skipped_n = sum(skipped.values())
    head = (
        '<header class="frame">\n'
        f'<p class="frame">{esc(FRAME)}</p>\n'
        '<div class="masthead">\n<div>\n'
        '<p class="kicker">Oath · a signal</p>\n'
        f"<h1>{esc(signal['name'])}</h1>\n"
        f'<p class="office">Version {signal["version"]} · <code>{esc(signal["id"])}</code> · '
        f"{standard_links(signal)}</p>\n"
        "</div>\n</div>\n</header>"
    )
    c = reach or {}
    reach_rows = (
        f"<dt>{c['paper_only']:,}</dt><dd>officeholders whose transaction reports are all "
        "scanned paper, which it does not read, so they cannot appear below whatever the reports "
        f"show; {c['some_paper']:,} more have some</dd>\n"
        f"<dt>{c['before_swearing_in']:,}</dt><dd>officeholders with rows dated before the "
        f"swearing-in the roster records for {congress_words()}, which it does not evaluate: "
        "the roster records that date, not the start of anyone's service, and the register "
        "holds no earlier index</dd>\n"
        f"<dt>{c['set_aside_held'] + c['set_aside_other'] + c.get('set_aside_shut', 0):,}</dt>"
        "<dd>transaction reports the index sets aside, not attributed to an officeholder, which "
        f"it does not see: {c['set_aside_held']:,} under the surname of an officeholder the "
        "register holds, for the maintainer to decide by hand, "
        + (
            f"{c['set_aside_shut']:,} under such a surname and dated when the register cannot "
            "show that officeholder in office, which no decision attributes, "
            if c.get("set_aside_shut")
            else ""
        )
        + f"and {c['set_aside_other']:,} under names no officeholder the register holds bears, "
        "among them any report of a candidate, and of a Member who left before the register "
        f"first read the roster, on {esc(ERA['first_read'])} "
        f'(<a href="{SUBJECTS_1}">SUBJECTS.md §1</a>)</dd>\n'
        if reach
        else ""
    )
    record = (
        '<section class="record">\n<h2>What it did in this build</h2>\n<dl>\n'
        f"<dt>{read_reports:,}</dt><dd>transaction reports read: on {with_rows:,} it evaluated at "
        f"least one row, and it fired on {fired:,} of those; on {no_rows:,} it evaluated no row, "
        f"for the reasons below{bar(fired, read_reports)}</dd>\n"
        f"<dt>{summary['rows_evaluated']:,}</dt><dd>rows evaluated; for "
        f"{summary['rows_after']:,} of them the Clerk's index dates the report after the "
        "deadline</dd>\n"
        f"<dt>{skipped_n:,}</dt><dd>rows not evaluated: "
        f"{esc(reason_clause(skipped)) or 'none'}</dd>\n"
        f"<dt>{by_state.get('not read', 0) - c.get('not_fetched', 0):,}</dt><dd>reports fetched "
        "and not read: scanned paper, whose transaction dates are printed in the document, and "
        "the register reads no scanned document</dd>\n"
        + (
            f"<dt>{c['not_fetched']:,}</dt><dd>reports not read because the register has not "
            "fetched them</dd>\n"
            if c.get("not_fetched")
            else ""
        )
        + f"{reach_rows}"
        f"<dt>{summary['officeholders_with_a_finding']:,}</dt><dd>officeholders the reports it "
        "fired on are attributed to. A count about the register; no page ranks anyone by it</dd>\n"
        + (
            f"<dt>{withdrawn:,}</dt><dd>Findings it once produced and a correction withdrew; each "
            "stays in the ledger with its reason, and on its officeholder's page</dd>\n"
            if withdrawn
            else ""
        )
        + "</dl>\n</section>"
    )
    body = (
        f'{head}\n<main id="main">\n'
        f"<section>\n<h2>What it describes</h2>\n{md_blocks(signal['description'])}\n"
        f'<p class="quiet">{esc(NOT_A_DETERMINATION)}</p>\n'
        f'<p class="quiet">{esc(QUIET_NOT_A_DETERMINATION)}</p>\n</section>\n'
        f"<section>\n<h2>How it counts</h2>\n{md_blocks(signal['criteria'])}\n"
        + (
            f'<p class="quiet">Where this definition says "this Congress", it means '
            f"{esc(congress_words(terms=True))}, whose filing year the register holds; a "
            "definition is frozen with its version, and its words are not changed.</p>\n"
            if ERA["closed"]
            else ""
        )
        + "</section>\n"
        f"<section>\n<h2>What it does not say</h2>\n{md_blocks(signal['not_saying'])}\n</section>\n"
        f"{record}\n"
        f"<section>\n<h2>Where it fired</h2>\n{table}\n</section>\n"
        f"<section>\n<h2>Worked example</h2>\n{md_blocks(signal['worked_example']['expected'])}\n"
        "</section>\n"
        "<section>\n<h2>Check it yourself</h2>\n"
        '<p class="quiet">Every Finding regenerates from the rows it names, and every file the '
        "signal writes regenerates from the rows and this definition:</p>\n"
        "<pre><code>python tools/rebuild.py &lt;finding-id&gt;\n"
        "python tools/rebuild.py\n"
        "python tools/verify.py</code></pre>\n</section>\n"
        f"</main>\n{footer(meta, home=False, to_root='../../')}"
    )
    return page(signal["name"], body)


def render_index(
    holders: list[dict],
    offices: list[dict],
    filings: list[dict],
    run: dict,
    meta: dict,
    striker,
    held_rows: int | dict = 0,
    rejected_url: str = REPO + "data/rejected/house-fd/",
    transactions: list[dict] | None = None,
    signal_runs: list[tuple[dict, dict]] | None = None,
    reach: dict[str, dict[str, int]] | None = None,
    changes: dict[str, list[dict]] | None = None,
) -> str:
    ERA.update(era_of(run, holders))
    # A seat shows who the roster lists. Whom it no longer lists is kept, with every row the
    # register published, listed below the seats and named at their seat as listed there
    # until a date, with a link, never as holding it.
    off_roster = not_listed(changes or {}, "officeholders")
    holder_by_seat = {current_office(h)["seat"]: h for h in holders if h["id"] not in off_roster}
    kept_by_seat: dict[str, list[dict]] = {}
    for h in holders:
        if h["id"] in off_roster:
            kept_by_seat.setdefault(current_office(h)["seat"], []).append(h)
    office_by_seat = {o["seat"]: o for o in offices}
    seats = sorted(office_by_seat)
    counts = seats_by_state(offices)
    # Every officeholder of this Congress the register holds at a seat, whatever office they
    # hold now, so a seat another held earlier is never said to have had no one (Seat C, N-3).
    holders_at = {
        seat: [
            h
            for h in held
            if any(o.get("term_start") == ERA["began"] for o in h.get("offices", []))
        ]
        for seat, held in holders_by_seat(holders).items()
    }
    rows, current = [], None
    for seat in seats:
        state = seat[:2]
        if state != current:
            current = state
            n = counts.get(state, 0)
            rows.append(
                f'<tr class="state" id="state-{esc(state)}"><th colspan="3" scope="rowgroup">'
                f"{esc(state)} · {esc(STATE_NAMES.get(state, state))} · "
                f"{n} {plural(n, 'seat', 'seats')}</th></tr>"
            )
        h = holder_by_seat.get(seat)
        office = office_by_seat[seat]
        kept = "".join(
            '<span class="note">Last listed here on the roster read '
            f"{esc((off_roster[k['id']].get('before') or ERA['first_read'])[:10])}, and not on "
            f"the one read {esc(off_roster[k['id']]['capture']['retrieved_at'][:10])}: "
            f'<a href="officeholders/{esc(slug(k["id"]))}.html">{esc(k["legal_name"])}</a>; their '
            "page stays, with every row the register attributed to them.</span>"
            for k in kept_by_seat.get(seat, [])
        )
        sworn_late = h is not None and (h.get("sworn_at") or "") > ERA["began"]
        earlier = [k for k in holders_at.get(seat, []) if h is None or k["id"] != h["id"]]
        if sworn_late and not earlier:
            kept += (
                f'<span class="note">Sworn in {esc(h["sworn_at"])}; the register holds no earlier '
                "holder of this seat in that Congress, and any filing by one is among the rows set "
                "aside.</span>"
            )
        if h is None and not earlier:
            kept += (
                '<span class="note">The register holds no Member of this seat in that Congress; '
                "a filing by one who left before the register first read the roster is among the "
                "rows set aside, as the caption below says.</span>"
            )
        if h is None:
            rows.append(
                f'<tr class="vacant" data-id="{esc(office["id"])}" data-seat="{esc(seat)}">'
                f'<td class="idx">{esc(seat)}</td>'
                f"<td>Vacant on the Clerk's roster read {esc(ERA['roster_read'])}{kept}</td>"
                f"<td>{esc(office.get('title', ''))}</td></tr>"
            )
            continue
        rows.append(
            f'<tr data-id="{esc(h["id"])}" data-seat="{esc(seat)}">'
            f'<td class="idx">{esc(seat)}</td>'
            f'<td><a href="officeholders/{esc(slug(h["id"]))}.html">{esc(h["legal_name"])}</a>'
            f"{kept}</td>"
            f"<td>{esc(office.get('title', ''))}</td>"
            "</tr>"
        )
    digest = meta.get("digest", "")
    mark = striker.strike(digest, digest, with_wordmark=True)
    ordered = sorted(
        (h for h in holders if h["id"] not in off_roster),
        key=lambda h: (current_office(h)["seat"], h["id"]),
    )
    first = ordered[0] if ordered else None
    example = (
        f'<a href="officeholders/{esc(slug(first["id"]))}.html">{esc(first["legal_name"])}</a>'
        if first
        else "none yet"
    )
    ended = (
        f'<p class="lede">The {ordinal(ERA["congress"])} Congress\'s terms ended at noon on '
        f"{long_date(ERA['ends'])} (U.S. Const. amend. XX, section 1). This register holds that "
        "Congress: every seat, with the Member the Clerk's roster listed when the register last "
        f"read it for that Congress, {esc(ERA['last_roster_read'])}. Members of the "
        f"{ordinal(ERA['congress'] + 1)} Congress are not in this build; to find who holds each "
        f'seat now, use <a href="{HOUSE_FINDER}">the House\'s own finder</a>.</p>\n'
        if ERA["closed"]
        else ""
    )
    head = (
        '<header class="frame">\n'
        f'<p class="frame">{esc(FRAME)}</p>\n'
        '<div class="masthead">\n<div>\n'
        '<p class="kicker">A public register</p>\n'
        "<h1>Oath</h1>\n"
        f"{ended}"
        f'<p class="lede">Every seat of the U.S. House in {esc(congress_words(terms=True))} '
        f"is listed here, with each row of the Clerk's {ERA['year']} filing index the register "
        "could match to the name on the Clerk's roster, linked to the Clerk's own copy. The "
        "register draws no conclusion about anyone. It shows what the index lists, when, and "
        "where to read it yourself.</p>\n"
        f"{signals_lede(signal_runs or [])}"
        f'<blockquote class="oath"><p>{esc(OATH)}</p><footer>{OATH_CITE} Every member took it. '
        "The register sets the record beside it.</footer></blockquote>\n"
        "</div>\n"
        + seal_figure(
            mark,
            f"The mark of build {build_label(meta)}, struck from its digest. Every officeholder "
            "page carries its own.",
        )
        + "\n</div>\n</header>"
    )
    door = (
        '<section class="door">\n'
        + (
            f"<div><p>Find who represented you in the {ordinal(ERA['congress'])} Congress</p>"
            if ERA["closed"]
            else "<div><p>Find your representative</p>"
        )
        + '<p><a href="#find">Choose your state</a> on the map, then the seat.'
        + (
            f" Members the Clerk's roster stopped listing during {esc(congress_words())} are "
            '<a href="#not-listed">below the seats</a>, with their pages.'
            if off_roster
            else ""
        )
        + "</p></div>\n"
        f"<div><p>Read one page in full</p><p>{example}, first in seat order.</p></div>\n"
        f'<div><p>Understand the discipline</p><p><a href="{CHARTER}">The Charter</a>: five vows, '
        "short on purpose.</p></div>\n</section>"
    )
    table = (
        "<section>\n<h2>Every seat in the register</h2>\n"
        '<table id="officeholders" data-order="seat">\n'
        f"<caption>{len(seats)} seats of {esc(congress_words())} in seat order, grouped by state, "
        + (
            "with the name the Clerk's roster listed when the register last read it for that "
            f"Congress, {esc(ERA['last_roster_read'])}. "
            if ERA["closed"]
            else "with each name as the Clerk's roster listed it when the register first "
            "published it; a name a later roster gives otherwise is said on the Member's page. "
        )
        + "The order says nothing about anyone. Candidates who did not win are not in the "
        f'register (<a href="{SUBJECTS_3}">SUBJECTS.md §3</a>). The register first read the '
        f"roster on {esc(ERA['first_read'])}; a Member of {esc(congress_words())} who left "
        "before then is not in it, and any filing under their name is among the rows set aside "
        f'(<a href="{SUBJECTS_1}">SUBJECTS.md §1</a>).</caption>\n'
        "<thead><tr><th>Seat</th><th>Name, as the Clerk's roster listed it</th><th>Office</th>"
        "</tr></thead>\n"
        "<tbody>\n" + "\n".join(rows) + "\n</tbody>\n</table>\n</section>"
    )
    kept = sorted(
        (h for h in holders if h["id"] in off_roster),
        key=lambda h: (current_office(h)["seat"], h["id"]),
    )
    if kept:
        kept_rows = "\n".join(
            f'<tr data-id="{esc(h["id"])}" data-seat="{esc(current_office(h)["seat"])}">'
            f'<td class="idx">{esc(current_office(h)["seat"])}</td>'
            f'<td><a href="officeholders/{esc(slug(h["id"]))}.html">{esc(h["legal_name"])}</a></td>'
            f'<td class="idx">{esc(off_roster[h["id"]].get("before", "")[:10])}</td>'
            f'<td class="idx">{esc(off_roster[h["id"]]["capture"]["retrieved_at"][:10])}</td>'
            "</tr>"
            for h in kept
        )
        title = f"No longer listed on the Clerk's roster during {congress_words()}"
        table += (
            f"\n<section>\n<h2>{esc(title)}</h2>\n"
            '<table id="not-listed" data-order="seat">\n'
            f"<caption>Officeholders of {esc(congress_words())} whose rows the register "
            "published and whom a later roster it read does not list, in seat order, each with "
            "the last roster read the register built from that listed them and the first that "
            "did not. The change fell between the two: the roster does not say when or why a "
            "person leaves a seat, and the register does not know. The register keeps every row it "
            "attributed to them, as published, a fact moving only by a correction the maintainer "
            "records with the evidence, and their pages. The list holds only "
            "Members the roster stopped listing after the register first read it, "
            f'{esc(ERA["first_read"])} (<a href="{SUBJECTS_1}">SUBJECTS.md §1</a>). The order '
            "says nothing about anyone, and neither does a name here.</caption>\n"
            "<thead><tr><th>Seat</th><th>Name, as the Clerk's roster listed it</th>"
            "<th>Last listed, roster read</th><th>Not listed, roster read</th></tr></thead>\n"
            f"<tbody>\n{kept_rows}\n</tbody>\n</table>\n</section>"
        )
    record = state_of_record(
        meta,
        run,
        holders,
        filings,
        offices,
        held_rows,
        rejected_url,
        transactions,
        signal_runs,
        reach,
        changes,
        len(holder_by_seat),
    )
    body = (
        f'{head}\n<main id="main">\n{door}\n{tile_map(offices)}\n{record}\n{table}\n'
        f"{how_to_read(False)}\n</main>\n{footer(meta, home=True)}"
    )
    return page("Every seat in the register", body)


# ---- main ---------------------------------------------------------------------------------


def load_signals(
    root: Path,
) -> tuple[list[dict], list[dict], list[tuple[dict, dict]], dict[str, dict[str, list[dict]]]]:
    """The current version of each signal, the Findings ledger, each signal's run summary, and
    its report outcomes by officeholder, all from the sealed store."""
    rows = read_ndjson(root / "data" / "signals.ndjson")
    latest: dict[str, dict] = {}
    for row in rows:
        if row["version"] >= latest.get(row["slug"], {}).get("version", 0):
            latest[row["slug"]] = row
    signals = sorted(latest.values(), key=lambda s: s["id"])
    findings = read_ndjson(root / "data" / "findings.ndjson")
    signal_runs, outcomes_by = [], {}
    for signal in signals:
        record = read_ndjson(
            root / "data" / "signal-runs" / f"{signal['slug']}-v{signal['version']}.ndjson"
        )
        if not record:
            continue
        signal_runs.append((signal, record[0]))
        by_oh: dict[str, list[dict]] = {}
        for outcome in record[1:]:
            by_oh.setdefault(outcome["officeholder_id"], []).append(outcome)
        outcomes_by[signal["id"]] = by_oh
    return signals, findings, signal_runs, outcomes_by


def unpaged_officeholders(findings: list[dict], holders: list[dict]) -> list[str]:
    """Officeholders the ledger's current rows name and the rows no longer hold. A published
    Finding stays on a page, so a render that would leave one without a page refuses."""
    named = {f["officeholder_id"] for f in findings if f.get("superseded_by") is None}
    return sorted(named - {h["id"] for h in holders})


def pick_run(root: Path) -> tuple[dict, list[Path]]:
    """The run record this tree's rows came from, and the set-aside files.

    The tree carries one run record per adapter and year, `house-fd-<year>-<key>`, and
    one set-aside file per year named `<year>-<key>` for the same capture key. A record
    is the build's when a set-aside file pairs with it by year and key. A tree with no
    pair, or with more than one (a record whose set-aside file is gone, or two years,
    which the landing has no design for yet), is refused rather than guessed, because a
    page once read a superseded record that happened to sort last.
    """
    runs = sorted((root / "data" / "adapter-runs").glob("house-fd-*.ndjson"))
    rejected_files = sorted((root / "data" / "rejected" / "house-fd").glob("*.ndjson"))
    if not runs:
        return {}, rejected_files
    pairs = {path.stem for path in rejected_files}
    paired = [path for path in runs if path.stem.removeprefix("house-fd-") in pairs]
    if len(paired) != 1:
        raise SystemExit(
            f"{len(runs)} run records in data/adapter-runs and {len(paired)} pair with a set-aside "
            "file by year and key; the tree should carry one run record per adapter and year, "
            "each with its set-aside file, and the landing reads one year"
        )
    return read_ndjson(paired[0])[0], rejected_files


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("root", nargs="?", default=".", help="repository root (default: .)")
    parser.add_argument(
        "--out", default="docs/build", help="output directory (default: docs/build)"
    )
    args = parser.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    root = Path(args.root).resolve()
    out = (root / args.out).resolve()
    striker = load_striker(root)

    meta = json.loads((root / "data" / "meta.json").read_text(encoding="utf-8"))
    # The pages' view of the build: the sealed meta, with the anchor as the proof now says it.
    meta = {**meta, "anchor": {**meta.get("anchor", {}), **anchor_of(root, meta["build"])}}
    holders = read_ndjson(root / "data" / "officeholders.ndjson")
    filings = read_ndjson(root / "data" / "filings.ndjson")
    offices = read_ndjson(root / "data" / "offices.ndjson")
    transactions_path = root / "data" / "transactions.ndjson"
    transactions = read_ndjson(transactions_path) if transactions_path.is_file() else []
    tx_by_holder: dict[str, list[dict]] = {}
    for t in transactions:
        tx_by_holder.setdefault(t["officeholder_id"], []).append(t)
    run, rejected_files = pick_run(root)
    rejected = read_ndjson(rejected_files[-1]) if rejected_files else []
    ERA.update(era_of(run, holders))
    KEPT.clear()
    folder = root / "data" / "captures" / "sha256"
    if folder.is_dir():
        KEPT.update(
            {p.name.split(".")[0]: f"data/captures/sha256/{p.name}" for p in folder.iterdir()}
        )
    changes = load_changes(root)
    NAMES.clear()
    NAMES.update({h["id"]: h["legal_name"] for h in holders})
    commit = os.environ.get("OATH_PAGES_COMMIT", "").strip()
    REPO_AT["commit"] = (
        f"https://github.com/jeb2-spec/Oath/blob/{commit}/"
        if re.fullmatch(r"[0-9a-f]{40}", commit)
        else REPO
    )
    source_read = {h["id"]: h.get("source", {}).get("retrieved_at", "") for h in holders}
    until = {
        hid: (c.get("before") or source_read.get(hid, ""))[:10]
        for hid, c in not_listed(changes, "officeholders").items()
    }
    held_here = held_by_holder(rejected, holders, until)
    held_reports = held_reports_by_holder(rejected, holders)
    # The set-aside file is named for the build's captures and replaced by the next build, so
    # a page links it at the commit the pages are rendered from, where one is given (Seat G).
    rejected_url = (
        REPO_AT["commit"] + rejected_files[-1].relative_to(root).as_posix()
        if rejected_files
        else REPO + "data/rejected/house-fd/"
    )
    by_holder: dict[str, list[dict]] = {}
    for f in filings:
        by_holder.setdefault(f["officeholder_id"], []).append(f)
    signals, findings, signal_runs, outcomes_by = load_signals(root)
    LEDGER.clear()
    LEDGER.extend(findings)
    DECIDED.clear()
    DECIDED.update(
        {f["id"]: m.group(1) for f in filings if (m := DECIDED_ON.match(f.get("notes") or ""))}
    )
    filing_of = {f["id"]: f for f in filings}
    moved_away: dict[str, list[tuple[dict, dict]]] = {}
    for row_id, history in changes.items():
        moves = [
            c
            for c in history
            if c["change"] == "corrected"
            and c.get("field") == "officeholder_id"
            and c["now"] != c["was"]
        ]
        filing = filing_of.get(row_id)
        if filing is None:
            continue
        for c in moves:
            if filing["officeholder_id"] != c["was"]:
                moved_away.setdefault(c["was"], []).append((filing, c))
    all_signals = read_ndjson(root / "data" / "signals.ndjson")
    findings_by: dict[str, list[dict]] = {}
    for f in findings:
        findings_by.setdefault(f["officeholder_id"], []).append(f)
    unpaged = unpaged_officeholders(findings, holders)
    if unpaged:
        raise SystemExit(
            "refusing to render: the ledger's current Findings name "
            f"{len(unpaged)} officeholders the rows no longer hold ({', '.join(unpaged)}); a "
            "published Finding stays on a page, so the register must keep their rows (NEXT.md)"
        )
    fetched = {f["id"] for f in filings if (f.get("source") or {}).get("content_hash")}
    reach = {
        signal["id"]: coverage(
            [o for group in outcomes_by.get(signal["id"], {}).values() for o in group],
            rejected,
            holders,
            until,
            fetched,
        )
        for signal, _ in signal_runs
    }

    (out / "officeholders").mkdir(parents=True, exist_ok=True)
    for h in holders:
        target = out / "officeholders" / f"{slug(h['id'])}.html"
        target.write_text(
            render_officeholder(
                h,
                by_holder.get(h["id"], []),
                meta,
                striker,
                held_here.get(h["id"], {}),
                tx_by_holder.get(h["id"], []),
                held_reports.get(h["id"], 0),
                signals,
                findings_by.get(h["id"], []),
                {sid: by_oh.get(h["id"], []) for sid, by_oh in outcomes_by.items()},
                all_signals,
                changes,
                rejected_url,
                moved_away.get(h["id"], []),
            ),
            encoding="utf-8",
            newline="\n",
        )
    (out / "index.html").write_text(
        render_index(
            holders,
            offices,
            filings,
            run,
            meta,
            striker,
            set_aside_counts(rejected, holders, until),
            rejected_url,
            transactions,
            signal_runs,
            reach,
            changes,
        ),
        encoding="utf-8",
        newline="\n",
    )
    for signal, summary in signal_runs:
        target = out / signal_page_path(signal)
        target.parent.mkdir(parents=True, exist_ok=True)
        outcomes_all = [o for group in outcomes_by.get(signal["id"], {}).values() for o in group]
        target.write_text(
            render_signal_page(
                signal,
                summary,
                findings,
                holders,
                meta,
                outcomes_all,
                reach[signal["id"]],
                changes,
            ),
            encoding="utf-8",
            newline="\n",
        )
    digest = meta.get("digest", "")
    (out / "mark.svg").write_text(
        striker.strike(digest, digest, with_wordmark=True), encoding="utf-8", newline="\n"
    )
    written = {out / "officeholders" / f"{slug(h['id'])}.html" for h in holders}
    written |= {out / signal_page_path(signal) for signal, _ in signal_runs}
    for folder in ("officeholders", "signals"):
        for stale in sorted((out / folder).rglob("*.html")) if (out / folder).is_dir() else []:
            if stale not in written:
                stale.unlink()
        for empty in sorted((out / folder).rglob("*"), reverse=True):
            if empty.is_dir() and not any(empty.iterdir()):
                empty.rmdir()

    quiet = sum(1 for h in holders if not by_holder.get(h["id"]))
    shown = out.relative_to(root).as_posix() if out.is_relative_to(root) else str(out)
    print(
        f"rendered {len(holders)} pages, the index, {len(signal_runs)} signal "
        f"{plural(len(signal_runs), 'page', 'pages')} and mark.svg to {shown}"
    )
    print(f"{quiet} pages have no matched row; each says so, with the count set aside at its seat")
    print("Now run: python tools/lint-frame-presence.py && python tools/lint-no-ranking.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
