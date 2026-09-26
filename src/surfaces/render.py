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

# Why a row at a member's own seat under the member's surname waits, read from the
# reason the adapter wrote. Each kind has the clause the page prints for it.
HELD_KINDS = (
    ("no_filing_id", "carries no Filing ID line"),
    ("status", "not Member"),
    ("before_sworn", "before the swearing-in"),
    ("not_captured", "has not been captured"),
)

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


def load_changes(root: Path) -> dict[str, dict]:
    """Each published row's latest recorded change, by row id: what a later capture of the
    source showed about a row the register had already published (data/changes.ndjson)."""
    latest: dict[str, dict] = {}
    rows = read_ndjson(root / "data" / "changes.ndjson")
    for change in sorted(rows, key=lambda c: (c["capture"]["retrieved_at"], c["id"])):
        latest[change["row_id"]] = change
    return latest


def not_listed(changes: dict[str, dict], rows: str) -> dict[str, str]:
    """The rows of one file the source last showed as not listed, with that capture's date.
    Such a row stays, exactly as published; the page says so beside it."""
    return {
        row_id: change["capture"]["retrieved_at"][:10]
        for row_id, change in changes.items()
        if change["rows"] == rows and change["change"] == "not listed"
    }


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


def held_at_seat(rejected: list[dict], holders: list[dict]) -> dict[str, dict[str, int]]:
    """Rows set aside under a member's surname, by the member's seat and by why they wait.

    A fact about the index, not a score. A row counts at a seat when its state-district
    is that holder's seat and its surname carries every word of that holder's surname,
    whatever reason the adapter gave, so the count is zero only when no such row exists.
    A held row whose reason names the member but whose state-district is another seat
    counts under "elsewhere" for that member, without naming the other seat.
    """
    tokens_of_seat = {}
    for holder in holders:
        for office in holder.get("offices", []):
            tokens_of_seat[office.get("seat", "")] = surname_tokens(holder)
    counts: dict[str, dict[str, int]] = {}
    for row in rejected:
        source = row.get("source_row", {})
        seat = source.get("state_dst", "").strip()
        reason = row.get("reason", "")
        words = folded_words(source.get("last") or "")
        if seat in tokens_of_seat and tokens_of_seat[seat] and tokens_of_seat[seat] <= words:
            kind = held_kind(reason)
            counts.setdefault(seat, {})[kind] = counts.get(seat, {}).get(kind, 0) + 1
            continue
        named = HELD_REASON.search(reason)
        if named and named.group(2) != seat:
            member_seat = named.group(2)
            counts.setdefault(member_seat, {})["elsewhere"] = (
                counts.get(member_seat, {}).get("elsewhere", 0) + 1
            )
    return counts


def held_reports_at_seat(rejected: list[dict], holders: list[dict]) -> dict[str, int]:
    """Set-aside rows coded P at a holder's seat under the holder's surname, by seat: the
    transaction reports the page must say are set aside and not read."""
    tokens_of_seat = {}
    for holder in holders:
        for office in holder.get("offices", []):
            tokens_of_seat[office.get("seat", "")] = surname_tokens(holder)
    counts: dict[str, int] = {}
    for row in rejected:
        source = row.get("source_row", {})
        seat = source.get("state_dst", "").strip()
        if source.get("filing_type") != "P" or seat not in tokens_of_seat:
            continue
        words = folded_words(source.get("last") or "")
        if tokens_of_seat[seat] and tokens_of_seat[seat] <= words:
            counts[seat] = counts.get(seat, 0) + 1
    return counts


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
        f"<p>Build <code>{esc(build_label(meta))}</code>, sealed "
        f"<code>{esc(meta.get('built_at'))}</code>. {anchor_line}</p>\n"
        "<p>Cite the build, not the page. Verify it: <code>python tools/verify.py</code>. "
        "The digest proves these pages are unchanged since sealing; it does not prove the "
        "Clerk's index is right.</p>\n"
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
        "dated before the swearing-in for this Congress the roster records, which is not the "
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
    """The row this one corrects, when it is a correction."""
    return next((f for f in findings if f.get("superseded_by") == row["id"]), None)


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
    return (
        f'<p class="quiet">Corrected {correction_why(row)}: this row supersedes '
        f"<code>{esc(prior['id'])}</code>, first produced from the record as retrieved "
        f"{esc(prior.get('fired_at', ''))}, which stays in the ledger, "
        f"<code>data/findings.ndjson</code>.{reason}</p>\n"
    )


def withdrawal_line(row: dict, findings: list[dict], filings_by_id: dict[str, dict]) -> str:
    report = filings_by_id.get(row["producing_filings"][0], {})
    filed = (row.get("evidence") or {}).get("filed_at") or report.get("filed_at", "")
    prior = supersedes(row, findings)
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
        words = NOT_EVALUATED_WORDS.get(reason, reason)
        if reason == "dated before this Congress's swearing-in" and sworn:
            words = (
                f"dated before {sworn}, the swearing-in for this Congress the roster records, "
                "which does not say whether this officeholder served before it"
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


def which_quiet(outcomes: list[dict], held_reports: int = 0, sworn: str | None = None) -> str:
    """What one Signal did with one officeholder's reports, fired or not: the silence named."""
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
    elif evaluated or unread:
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
            f"{n:,} {plural(n, 'report is', 'reports are')} captured and not read: scanned "
            "paper, whose transaction dates are printed in the document, and the register reads "
            "no scanned document."
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
        return "the reports attributed are scanned paper, which it does not read"
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


def finding_block(finding: dict, report: dict | None, findings: list[dict] | None = None) -> str:
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
) -> str:
    """Signals that fired and Signals that did not, for one officeholder, grouped by Signal
    and never by severity (ECOSYSTEM.md §1.3; METHODOLOGY.md §10). Every defined Signal is
    named on every page, so silence is shown rather than assumed, and says which it is. A
    Finding an earlier version produced stays on the page, under that version, as published."""
    fired, quiet = [], []

    def blocks_for(signal_id: str) -> tuple[str, str]:
        mine = sorted(
            fired_now(findings, signal_id), key=lambda f: (f["evidence"]["filed_at"], f["id"])
        )
        withdrawn = "".join(
            withdrawal_line(f, findings, filings_by_id)
            for f in sorted(withdrawn_now(findings, signal_id), key=lambda f: f["id"])
        )
        found = "\n".join(
            finding_block(f, filings_by_id.get(f["producing_filings"][0]), findings) for f in mine
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
            f"{esc(which_quiet(outcomes.get(signal['id'], []), held_reports, sworn))}</p>\n"
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
            f"fired on {n:,} {plural(n, 'report', 'reports')}, below"
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
        )
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
                "prints Status Member at this seat with this Filing ID. Decision: a person's "
                "cited adjudication.",
            ),
            (
                "The document",
                "The Clerk's own copy. The register links to it and does not host it.",
            ),
            ("Fetched", "The day the register last read the Clerk's index."),
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
                "Every seat of the House in seat order, with the name the Clerk's roster lists. "
                "Seat order is an order of offices, not of people.",
            )
        ]
    rows += [
        (
            "Set aside",
            "A row of the Clerk's index that neither the name on the form nor the Clerk's "
            "document could attribute to an officeholder. It waits for the maintainer to decide "
            "by hand, with evidence; it is never guessed.",
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
    ]
    body = "\n".join(
        f"<dt>{esc(k)}</dt><dd>{v if isinstance(v, Raw) else esc(v)}</dd>" for k, v in rows
    )
    return (
        '<section class="how">\n<h2>How to read this page</h2>\n<dl class="terms">\n'
        f"{body}\n</dl>\n</section>"
    )


# ---- the officeholder page --------------------------------------------------------------


HELD_CLAUSES = {
    "no_filing_id": "whose {docs} {carry} no Filing ID line (scanned paper, or a form that "
    "prints none) and cannot confirm the filer",
    "status": "whose {docs} {print} a filer status other than Member",
    "before_sworn": "dated by the index before the swearing-in the roster records for this "
    "Congress",
    "not_captured": "whose {docs} the register has not yet captured",
    "other": "whose {docs} {print} another seat or another Filing ID, or were set aside for "
    "another recorded reason",
}


def aside_sentence(held_here) -> str:
    """The rows at this seat under this surname that wait, and why, from the adapter's
    reasons. `held_here` is the kinds dict from held_at_seat, or a bare count."""
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
    clauses = []
    for kind, n in kinds.items():
        if kind in HELD_CLAUSES:
            clauses.append(
                f"{n} "
                + HELD_CLAUSES[kind].format(
                    docs=plural(n, "document", "documents"),
                    carry=plural(n, "carries", "carry"),
                    mark=plural(n, "marks", "mark"),
                    print=plural(n, "prints", "print"),
                )
            )
    why = f": {'; '.join(clauses)}" if clauses else ""
    return (
        f" {total} {plural(total, 'row', 'rows')} of the index at this seat "
        f"{plural(total, 'carries', 'carry')} this surname and "
        f"{plural(total, 'is', 'are')} set aside for the maintainer to decide by hand{why}." + away
    )


def how_attributed(filing: dict) -> str:
    """By the name on the form, by the document's own header, or by a person's decision."""
    if (filing.get("notes") or "").startswith(BY_HEADER):
        return "document"
    if filing.get("extraction_confidence") == "manual":
        return "decision"
    return "name"


def documents_read(filings: list[dict]) -> tuple[int, int]:
    """How many of these filings' documents the register read, and how many it captured
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


def checks_section(holder: dict, filings: list[dict], held_here, signal_line: str = "") -> str:
    """What the register can and cannot check here. Identical in shape for everyone."""
    roster_read = holder.get("source", {}).get("retrieved_at", "")[:10]
    n = len(filings)
    if n:
        by_header = sum(1 for f in filings if how_attributed(f) == "document")
        route = (
            f", {by_header} of them by the document's own header: the index writes the name "
            "in another form, and the Clerk's document prints Status Member at this seat with "
            "this Filing ID"
            if by_header
            else ""
        )
        index_line = (
            f"<b>in the register</b> · {n} {plural(n, 'row', 'rows')} of the Clerk's 2025 index "
            f"attributed to this officeholder{route}.{aside_sentence(held_here)}"
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
                    f"{scanned} captured and hashed, not read: scanned paper, or a form the "
                    "register does not yet read"
                )
            if pending:
                parts.append(f"{pending} not yet captured")
            documents = "; ".join(parts) + ". Each link below opens the Clerk's own copy."
        else:
            documents = (
                "<b>not yet</b> · the register has not read the documents; each link below opens "
                "the Clerk's own copy."
            )
    else:
        aside = aside_sentence(held_here) or (
            " No row of the index at this seat carries this surname; rows the register could not "
            "match anywhere are counted in the state of the record."
        )
        index_line = (
            "<b>not yet matched</b> · the register attributes a row only on an exact name match "
            "against the Clerk's roster, or on the Clerk's document printing Status Member at "
            f"this seat with this Filing ID.{aside} This is a gap in the register's matching, "
            "not a statement that no filing was made."
        )
        documents = "<b>not yet</b> · the register has not read any document for this record."
    return (
        '<section class="checks">\n<h2>What the register can check here</h2>\n<dl class="terms">\n'
        f"<dt>Identity</dt><dd><b>in the register</b> · from the Clerk's roster, read "
        f"{esc(roster_read)}.</dd>\n"
        f"<dt>Filings index</dt><dd>{index_line}</dd>\n"
        f"<dt>Documents</dt><dd>{documents}</dd>\n"
        f"<dt>Signals</dt><dd>{signal_line or signal_check_line([], [])}</dd>\n"
        "</dl>\n</section>"
    )


def filings_section(filings: list[dict], held_here, gone: dict[str, str] | None = None) -> str:
    heading = "<h2>What the Clerk's index lists for this officeholder</h2>\n"
    if not filings:
        return (
            f"<section>\n{heading}"
            '<p class="quiet">The register has not yet matched any row of the Clerk\'s 2025 index '
            "to this name. This is a gap in the register's name-matching, not a statement about "
            f"what was filed.{aside_sentence(held_here)} "
            f'<a href="{CLERK_SITE}">Search the Clerk\'s disclosure site directly.</a></p>\n'
            "</section>"
        )
    rows = []
    for f in sorted(filings, key=lambda f: (f["filed_at"], f["id"])):
        rows.append(
            "<tr>"
            f'<td class="idx">{esc(f["filed_at"])}</td>'
            f'<td class="code">{esc(f.get("source_form_code") or "")}</td>'
            f'<td><a href="{esc(f["source"]["url"])}">Open the Clerk\'s copy</a>'
            + (
                f'<span class="note">not in the index read {esc(gone[f["id"]])}; kept as '
                "published</span>"
                if f["id"] in (gone or {})
                else ""
            )
            + "</td>"
            f'<td class="idx">{esc(f["source"]["retrieved_at"][:10])}</td>'
            f'<td class="code">{how_attributed(f)}</td>'
            "</tr>"
        )
    n = len(rows)
    return (
        f"<section>\n{heading}<table>\n"
        f"<caption>{n} {plural(n, 'row', 'rows')} of the Clerk's 2025 index attributed to this "
        'officeholder, oldest first. "How" says what attributed the row: the name on the form '
        "matching the roster; the Clerk's document printing Status Member at this seat with this "
        "Filing ID; or a person's cited decision. "
        "The one-letter code is the Clerk's own and the Clerk does not publicly "
        "define it; the register does not interpret it. Open the document to see what it is. "
        "Rows coded P are served from the Clerk's transaction-report path, which is the one code "
        f'the register files as a transaction report (<a href="{SOURCES_F1}">SOURCES.md F.1</a>).'
        "</caption>\n"
        "<thead><tr><th>Date filed</th><th>The Clerk's code</th>"
        "<th>The document</th><th>Fetched</th><th>How</th></tr></thead>\n<tbody>\n"
        + "\n".join(rows)
        + "\n</tbody>\n</table>\n</section>"
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
    gone: dict[str, str] | None = None,
) -> str:
    """What the reports the register read list, as filed, grouped by report.

    The record, not a judgement of it: no total of amounts, no average, no comparison.
    A row the filer marked Amended or Deleted is shown with the mark in its Type cell and
    counted as a row. A report captured and not read is named by its filed date and its
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
            '<p class="quiet">No transaction report in the Clerk\'s 2025 index is attributed to '
            f"this officeholder.</p>\n{held}</section>"
        )
    read = [f for f in reports if f.get("extraction_confidence") == "structured"]
    unread = [f for f in reports if f.get("extraction_confidence") != "structured"]
    by_report: dict[str, list[dict]] = {}
    for tx in transactions:
        by_report.setdefault(tx["filing_id"], []).append(tx)
    parts = [lead]
    if unread:
        dates = ", ".join(esc(f["filed_at"]) for f in unread)
        n = len(unread)
        parts.append(
            f'<p class="quiet">The {plural(n, "report", "reports")} filed {dates} '
            f"{plural(n, 'is', 'are')} captured and not read (no Filing ID line: scanned paper, "
            f"or a form that prints none); {plural(n, 'its', 'their')} transactions are not listed "
            "here. "
            f"{plural(n, 'It is', 'They are')} linked above.</p>\n"
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
        if not rows:
            continue
        body = "\n".join(
            "<tr>"
            f'<td class="idx">{esc(t["transaction_date"])}</td>'
            f'<td class="idx">{esc(t["notified_date"])}</td>'
            f"<td>{type_cell(t)}</td>"
            f"<td>{esc(OWNER_WORDS.get(t['owner'], t['owner']))}</td>"
            f"<td>{asset_cell(t)}"
            + (
                f'<span class="note">not in the report as read {esc(gone[t["id"]])}; kept as '
                "published</span>"
                if t["id"] in (gone or {})
                else ""
            )
            + "</td>"
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
    changes: dict[str, dict] | None = None,
) -> str:
    signals, findings, outcomes = signals or [], findings or [], outcomes or {}
    changes = changes or {}
    office = holder["offices"][0] if holder.get("offices") else {}
    seal = striker.strike(holder["id"], meta.get("digest", ""), ticks=0, bars=0)
    roster_read = holder.get("source", {}).get("retrieved_at", "")[:10]
    sworn = holder.get("sworn_at") or sworn_date(holder)
    office_line = f"{esc(office.get('title', ''))} · seat {esc(office.get('seat', ''))}"
    if sworn:
        office_line += (
            f" · sworn in for this Congress {esc(sworn)}, per the roster read {esc(roster_read)}"
        )
    off_roster = not_listed(changes, "officeholders").get(holder["id"])
    off_line = (
        f'<p class="office">The Clerk\'s roster read {esc(off_roster)} does not list this '
        "officeholder. The register keeps every row it published about them, exactly as "
        f"published; the roster read {esc(roster_read)} is the last that listed them.</p>\n"
        if off_roster
        else ""
    )
    check_line = signal_check_line(signals, findings, outcomes, held_reports)
    gone_rows = not_listed(changes, "transactions")
    section = signals_section(
        signals,
        findings,
        outcomes,
        {f["id"]: f for f in filings},
        "../",
        held_reports,
        sworn,
        all_signals or signals,
    )
    head = (
        '<header class="frame">\n'
        f'<p class="frame">{esc(FRAME)}</p>\n'
        '<div class="masthead">\n<div>\n'
        '<p class="kicker">Oath · the register</p>\n'
        f"<h1>{esc(holder['legal_name'])}</h1>\n"
        f'<p class="office">{office_line}</p>\n'
        f"{off_line}"
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
        f"{checks_section(holder, filings, held_here, check_line)}\n"
        f"{filings_section(filings, held_here, not_listed(changes, 'filings'))}\n"
        f"{transactions_section(filings, transactions or [], held_reports, gone_rows)}\n"
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
    return (
        '<section class="finder" id="find">\n<h2>Find your representative</h2>\n'
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
    """The landing's aside for documents captured but not read, or nothing."""
    if not scanned:
        return ""
    return (
        f"; {scanned} more captured and hashed, not read: scanned paper, or a form the "
        "register does not yet read"
    )


def state_of_record(
    meta: dict,
    run: dict,
    holders: list[dict],
    filings: list[dict],
    offices: list[dict],
    at_seat_total: int,
    rejected_url: str,
    transactions: list[dict] | None = None,
    signal_runs: list[tuple[dict, dict]] | None = None,
    reach: dict[str, dict[str, int]] | None = None,
) -> str:
    """Numbers about the register and the chamber as a whole. None is about a person."""
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
    carried = run.get("carried", {})
    carried_line = ""
    if any(carried.get(k) for k in ("officeholders", "filings", "transactions")):
        congress = run.get("congress", {})
        what = (
            f"officeholders of filing year {run.get('year', '')}, whose Congress has ended, and "
            if congress.get("closed")
            else "officeholders the Clerk's roster no longer lists, and "
        )
        carried_line = (
            f"<dt>{carried.get('officeholders', 0)}</dt><dd>{what}"
            f"{carried.get('filings', 0)} filings and {carried.get('transactions', 0)} "
            "transactions this build did not derive again, each kept exactly as the register "
            "published it: a published row stays, and a change is shown beside it, never by "
            f'removal (<a href="{REPO}data/changes.ndjson">the changes, each with the capture '
            "that shows it</a>)</dd>\n"
        )
    # A closed year's build derived nothing from the roster, so its counts are the rows the
    # register holds for that year, not the build's (which are none by construction).
    counts = {} if run.get("congress", {}).get("closed") else run.get("counts", {})
    seats = counts.get("seats", len(offices))
    filled = counts.get("filled", len(holders))
    voting = sum(1 for o in offices if o.get("title") == REPRESENTATIVE)
    delegates = sum(1 for o in offices if o.get("title") == "Delegate")
    commissioners = sum(1 for o in offices if o.get("title") == "Resident Commissioner")
    with_row = counts.get(
        "officeholders_with_a_filing", len({f["officeholder_id"] for f in filings})
    )
    matched = counts.get("accepted", len(filings))
    read, scanned = documents_read(filings)
    by_header = sum(1 for f in filings if how_attributed(f) == "document")
    held = run.get("rejected_by_reason", {}).get("surname matches a sitting member", 0)
    sources = {s["name"]: s for s in run.get("sources", [])}
    year = run.get("year", 2025)
    index_src = sources.get(f"{year}FD.zip", {})
    roster_src = sources.get("MemberData.xml", {})
    fresh = ""
    if index_src:
        fresh = (
            f'The register reads <a href="{CLERK_SITE}">the Clerk\'s disclosure site</a>. '
            f"Its {year} index was last modified {esc(index_src.get('last_modified', 'unknown'))} "
            f"and the register read it {esc(index_src.get('retrieved_at', '')[:10])}; "
            f"the roster was read {esc(roster_src.get('retrieved_at', '')[:10])}. "
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
            f'<figure class="rhythm">{svg}<figcaption>All {total} matched index rows by the month '
            f"they were filed, {esc(first)} to {esc(last)}, across every member. This is the "
            "rhythm of disclosure in the chamber; it is not a measure of anyone, and no "
            "person's count appears anywhere on this page.</figcaption></figure>\n"
        )
    return (
        '<section class="record" id="record">\n<h2>The state of the record</h2>\n'
        f'<p class="quiet">What the register holds at build <code>{esc(build_label(meta))}</code>. '
        "Every number here is about the register or the chamber as a whole. None is about a "
        "person, and nothing here is sorted by anything the register computes about one.</p>\n"
        "<dl>\n"
        f"<dt>{seats}</dt><dd>seats in the House{nonvoting}; {filled} filled, {seats - filled} "
        f"vacant{bar(filled, seats)}</dd>\n"
        f"<dt>{with_row}</dt><dd>of {filled} officeholders have at least one row of the Clerk's "
        f"{year} index attributed to them{bar(with_row, filled)}</dd>\n"
        f"<dt>{matched}</dt><dd>index rows attributed, each linked to the Clerk's own document; "
        f"{by_header} of them by the document's own header where the index wrote the name in "
        "another form</dd>\n"
        f"<dt>{read}</dt><dd>of {matched} documents read by the register so far, each checked "
        f"against the seat and filing ID printed inside it{scanned_clause(scanned)}; the links "
        f"open the Clerk's copies{bar(read, matched)}</dd>\n"
        f"<dt>{len(transactions)}</dt><dd>rows the read reports list, as filed{marked_note}, each "
        "on its officeholder's page grouped by report; no page sums the amounts, averages them, "
        "or compares them with anyone else's</dd>\n"
        f"<dt>{held}</dt><dd>index rows set aside for the maintainer to decide by hand, because "
        f"the register does not guess; {at_seat_total} of them sit at a member's own seat under "
        "the member's surname. Whether a page is quiet is decided by whether the name on the "
        "form matched the roster, or the Clerk's document confirmed the filer at that seat, "
        f'not by what was filed. <a href="{rejected_url}">The '
        "rows, with reasons</a>; every row there is a line of the Clerk's index the register did "
        "not attribute, and presence in that file is not evidence of anything about anyone.</dd>\n"
        f"{carried_line}"
        f"{signal_lines}"
        "</dl>\n"
        f'<p class="quiet">{fresh}The seal fixes exactly this reading.</p>\n'
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
        "why, reports captured and not read, or nothing to evaluate. None of it is a "
        "determination, which is the Committee on Ethics' to make.</p>\n"
    )


def coverage(outcomes: list[dict], rejected: list[dict]) -> dict[str, int]:
    """Who a signal's run cannot reach, in counts, never in names: officeholders whose reports
    are all captured and not read, those with some, those with rows dated before this
    Congress's swearing-in, and the transaction reports the index sets aside."""
    states: dict[str, set[str]] = {}
    before: set[str] = set()
    for o in outcomes:
        states.setdefault(o["officeholder_id"], set()).add(o["state"])
        if o["not_evaluated"].get("dated before this Congress's swearing-in"):
            before.add(o["officeholder_id"])
    ptr = [r for r in rejected if r.get("source_row", {}).get("filing_type") == "P"]
    held = sum(1 for r in ptr if r.get("reason", "").startswith("surname matches a sitting member"))
    return {
        "paper_only": sum(1 for s in states.values() if s == {"not read"}),
        "some_paper": sum(1 for s in states.values() if "not read" in s and s != {"not read"}),
        "before_swearing_in": len(before),
        "set_aside_held": held,
        "set_aside_other": len(ptr) - held,
    }


def coverage_sentence(c: dict[str, int]) -> str:
    """Who cannot appear among those on which a signal fired, and why, in counts."""
    paper, some, before = c["paper_only"], c["some_paper"], c["before_swearing_in"]
    held, other = c["set_aside_held"], c["set_aside_other"]
    aside = held + other
    return (
        f"It cannot reach {paper:,} {plural(paper, 'officeholder', 'officeholders')} whose "
        "transaction reports are all scanned paper, which it does not read, or some of the "
        f"reports of {some:,} more; it does not evaluate the rows dated before this Congress's "
        f"swearing-in on the reports of {before:,} "
        f"{plural(before, 'officeholder', 'officeholders')}; and it does not see the "
        f"{aside:,} {plural(aside, 'transaction report', 'transaction reports')} the index sets "
        f"aside, {held:,} under a sitting member's surname, for a person to decide, and "
        f"{other:,} under names no sitting member bears."
    )


def render_signal_page(
    signal: dict,
    summary: dict,
    findings: list[dict],
    holders: list[dict],
    meta: dict,
    outcomes: list[dict] | None = None,
    reach: dict[str, int] | None = None,
) -> str:
    """A signal's page (ECOSYSTEM.md §1.2; PIPELINE.md Stage 5): its definition in its own words,
    what it did in this build, who it cannot reach, and every report on which it fired, in
    seat order."""
    outcomes = outcomes or []
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
    for oid in sorted(by_holder, key=lambda i: (holder_of[i]["offices"][0]["seat"], i)):
        holder = holder_of[oid]
        seat = holder["offices"][0]["seat"]
        page_url = f"../../officeholders/{esc(slug(oid))}.html"
        reports = ", ".join(
            f'<a href="{page_url}#finding-{esc(f["producing_filings"][0].rsplit(":", 1)[1])}">'
            f"{esc(f['evidence']['filed_at'])}</a>"
            for f in sorted(by_holder[oid], key=lambda f: (f["evidence"]["filed_at"], f["id"]))
        )
        rows.append(
            f'<tr data-id="{esc(oid)}" data-seat="{esc(seat)}">'
            f'<td class="idx">{esc(seat)}</td>'
            f'<td><a href="{page_url}#signal-{esc(signal["slug"])}">'
            f"{esc(holder['legal_name'])}</a></td>"
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
        "reports are all scanned paper cannot, whatever the reports show.</caption>\n"
        "<thead><tr><th>Seat</th><th>Name, as the Clerk lists it</th>"
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
        f"<dt>{c['before_swearing_in']:,}</dt><dd>officeholders with rows dated before this "
        "Congress's swearing-in, which it does not evaluate: the roster records that date, not "
        "the start of anyone's service, and the register holds no earlier index</dd>\n"
        f"<dt>{c['set_aside_held'] + c['set_aside_other']:,}</dt><dd>transaction reports the "
        "index sets aside, not attributed to a sitting member, which it does not see: "
        f"{c['set_aside_held']:,} under a sitting member's surname, for a person to decide, and "
        f"{c['set_aside_other']:,} under names no sitting member bears</dd>\n"
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
        f"<dt>{by_state.get('not read', 0):,}</dt><dd>reports captured and not read: scanned "
        "paper, whose transaction dates are printed in the document, and the register reads no "
        "scanned document</dd>\n"
        f"{reach_rows}"
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
        f"<section>\n<h2>How it counts</h2>\n{md_blocks(signal['criteria'])}\n</section>\n"
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
    at_seat: dict[str, dict[str, int]] | None = None,
    rejected_url: str = REPO + "data/rejected/house-fd/",
    transactions: list[dict] | None = None,
    signal_runs: list[tuple[dict, dict]] | None = None,
    reach: dict[str, dict[str, int]] | None = None,
    changes: dict[str, dict] | None = None,
) -> str:
    at_seat = at_seat or {}
    # A seat shows who the roster lists. Whom it no longer lists is kept, with every row the
    # register published, and listed below the seats, never at a seat they do not hold.
    off_roster = not_listed(changes or {}, "officeholders")
    holder_by_seat = {h["offices"][0]["seat"]: h for h in holders if h["id"] not in off_roster}
    office_by_seat = {o["seat"]: o for o in offices}
    seats = sorted(office_by_seat)
    counts = seats_by_state(offices)
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
        if h is None:
            rows.append(
                f'<tr class="vacant" data-id="{esc(office["id"])}" data-seat="{esc(seat)}">'
                f'<td class="idx">{esc(seat)}</td><td>Vacant</td>'
                "<td>no officeholder in this build</td></tr>"
            )
            continue
        rows.append(
            f'<tr data-id="{esc(h["id"])}" data-seat="{esc(seat)}">'
            f'<td class="idx">{esc(seat)}</td>'
            f'<td><a href="officeholders/{esc(slug(h["id"]))}.html">{esc(h["legal_name"])}</a></td>'
            f"<td>{esc(office.get('title', ''))}</td>"
            "</tr>"
        )
    digest = meta.get("digest", "")
    mark = striker.strike(digest, digest, with_wordmark=True)
    ordered = sorted(holders, key=lambda h: (h["offices"][0]["seat"], h["id"]))
    first = ordered[0] if ordered else None
    example = (
        f'<a href="officeholders/{esc(slug(first["id"]))}.html">{esc(first["legal_name"])}</a>'
        if first
        else "none yet"
    )
    head = (
        '<header class="frame">\n'
        f'<p class="frame">{esc(FRAME)}</p>\n'
        '<div class="masthead">\n<div>\n'
        '<p class="kicker">A public register</p>\n'
        "<h1>Oath</h1>\n"
        '<p class="lede">Every seat of the U.S. House is listed here, with each row of the '
        "Clerk's 2025 filing index the register could match to the name on the Clerk's roster, "
        "linked to the Clerk's own copy. The register draws no conclusion about anyone. It shows "
        "what the index lists, when, and where to read it yourself.</p>\n"
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
        '<div><p>Find your representative</p><p><a href="#find">Choose your state</a> on the map, '
        "then the seat.</p></div>\n"
        f"<div><p>Read one page in full</p><p>{example}, first in seat order.</p></div>\n"
        f'<div><p>Understand the discipline</p><p><a href="{CHARTER}">The Charter</a>: five vows, '
        "short on purpose.</p></div>\n</section>"
    )
    table = (
        "<section>\n<h2>Every seat in the register</h2>\n"
        '<table id="officeholders" data-order="seat">\n'
        f"<caption>{len(seats)} seats in seat order, grouped by state, with the name the Clerk "
        "lists. The order says nothing about anyone. Candidates who did not win are not in the "
        f'register (<a href="{SUBJECTS_3}">SUBJECTS.md §3</a>).</caption>\n'
        "<thead><tr><th>Seat</th><th>Name, as the Clerk lists it</th><th>Office</th></tr></thead>\n"
        "<tbody>\n" + "\n".join(rows) + "\n</tbody>\n</table>\n</section>"
    )
    kept = sorted(
        (h for h in holders if h["id"] in off_roster),
        key=lambda h: (h["offices"][0]["seat"], h["id"]),
    )
    if kept:
        kept_rows = "\n".join(
            f'<tr data-id="{esc(h["id"])}" data-seat="{esc(h["offices"][0]["seat"])}">'
            f'<td class="idx">{esc(h["offices"][0]["seat"])}</td>'
            f'<td><a href="officeholders/{esc(slug(h["id"]))}.html">{esc(h["legal_name"])}</a></td>'
            f'<td class="idx">{esc(off_roster[h["id"]])}</td>'
            "</tr>"
            for h in kept
        )
        table += (
            "\n<section>\n<h2>No longer on the Clerk's roster</h2>\n"
            '<table id="not-listed" data-order="seat">\n'
            "<caption>Officeholders the register published whom the Clerk's roster, as last read, "
            "does not list, in seat order, each with the date of the first roster read that did "
            "not. The register keeps every row it published about them, exactly as published, "
            "and their pages. The order says nothing about anyone, and neither does a name here: "
            "the roster lists who holds a seat, and does not say why a person no longer does."
            "</caption>\n"
            "<thead><tr><th>Seat</th><th>Name, as the Clerk listed it</th>"
            "<th>Not on the roster read</th></tr></thead>\n"
            f"<tbody>\n{kept_rows}\n</tbody>\n</table>\n</section>"
        )
    record = state_of_record(
        meta,
        run,
        holders,
        filings,
        offices,
        held_total(at_seat),
        rejected_url,
        transactions,
        signal_runs,
        reach,
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
    at_seat = held_at_seat(rejected, holders)
    held_reports = held_reports_at_seat(rejected, holders)
    rejected_url = (
        REPO + rejected_files[-1].relative_to(root).as_posix()
        if rejected_files
        else REPO + "data/rejected/house-fd/"
    )
    by_holder: dict[str, list[dict]] = {}
    for f in filings:
        by_holder.setdefault(f["officeholder_id"], []).append(f)
    signals, findings, signal_runs, outcomes_by = load_signals(root)
    all_signals = read_ndjson(root / "data" / "signals.ndjson")
    changes = load_changes(root)
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
    reach = {
        signal["id"]: coverage(
            [o for os in outcomes_by.get(signal["id"], {}).values() for o in os], rejected
        )
        for signal, _ in signal_runs
    }

    (out / "officeholders").mkdir(parents=True, exist_ok=True)
    for h in holders:
        seat = h["offices"][0]["seat"] if h.get("offices") else ""
        target = out / "officeholders" / f"{slug(h['id'])}.html"
        target.write_text(
            render_officeholder(
                h,
                by_holder.get(h["id"], []),
                meta,
                striker,
                at_seat.get(seat, {}),
                tx_by_holder.get(h["id"], []),
                held_reports.get(seat, 0),
                signals,
                findings_by.get(h["id"], []),
                {sid: by_oh.get(h["id"], []) for sid, by_oh in outcomes_by.items()},
                all_signals,
                changes,
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
            at_seat,
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
        outcomes_all = [o for os in outcomes_by.get(signal["id"], {}).values() for o in os]
        target.write_text(
            render_signal_page(
                signal, summary, findings, holders, meta, outcomes_all, reach[signal["id"]]
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
