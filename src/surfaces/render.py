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
import re
import sys
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

HELD_REASON = re.compile(
    r"surname matches exactly one sitting member \((.+?), ([A-Z]{2}\d{2})\) but"
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


def held_at_seat(rejected: list[dict]) -> dict[str, int]:
    """Rows set aside whose surname matches the sitting member at that very seat, by seat.

    A fact about the index, not a score: the reason string the adapter wrote names the
    member and the seat, and the row's own state-district must be the same seat.
    """
    counts: dict[str, int] = {}
    for row in rejected:
        match = HELD_REASON.search(row.get("reason", ""))
        if match and row.get("source_row", {}).get("state_dst", "").strip() == match.group(2):
            counts[match.group(2)] = counts.get(match.group(2), 0) + 1
    return counts


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


def footer(meta: dict, home: bool) -> str:
    anchor = meta.get("anchor", {}).get("state", "none")
    anchor_line = (
        "Anchor: none yet; the build has not been timestamped by an outside service."
        if anchor == "none"
        else f"Anchor: {esc(anchor)}."
    )
    back = "" if home else '<p><a href="../index.html">Every seat in the register</a></p>\n'
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
    f'Pub. L. 112-105</a>. <a href="{STANDARDS_S2}">STANDARDS.md S.2</a>. The Act does not '
    "prohibit the transactions it requires reported; a report listed below is the requirement "
    "being met, as the Clerk records it.</dd>\n"
    "</dl>\n</section>"
)

SIGNALS = (
    "<section>\n<h2>Signals that fired</h2>\n"
    '<p class="quiet">None. No signal is defined in this build, so none has fired for anyone.</p>\n'
    "</section>\n<section>\n<h2>Signals that did not fire</h2>\n"
    '<p class="quiet">None to list. When signals exist, every one that did not fire is named here '
    "with its version, so silence is shown rather than assumed.</p>\n</section>"
)


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
                "register matched to this officeholder's name on the roster, listed as the Clerk "
                "lists it.",
            ),
            (
                "The document",
                "The Clerk's own copy. The register links to it and does not host it.",
            ),
            ("Fetched", "The day the register last read the Clerk's index."),
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
            "A row of the Clerk's index the register could not match to a name beyond an exact "
            "match. It waits for the maintainer to decide by hand, with evidence; it is never "
            "guessed.",
        ),
        (
            "A signal",
            "A condition written down in advance, citing the rule it comes from. None is defined "
            "in this build, so none can fire.",
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
    body = "\n".join(f"<dt>{esc(k)}</dt><dd>{esc(v)}</dd>" for k, v in rows)
    return (
        '<section class="how">\n<h2>How to read this page</h2>\n<dl class="terms">\n'
        f"{body}\n</dl>\n</section>"
    )


# ---- the officeholder page --------------------------------------------------------------


def aside_sentence(held_here: int) -> str:
    if not held_here:
        return ""
    return (
        f" {held_here} {plural(held_here, 'row', 'rows')} of the index at this seat "
        f"{plural(held_here, 'carries', 'carry')} this surname and "
        f"{plural(held_here, 'is', 'are')} set aside for the maintainer to decide by hand."
    )


def documents_read(filings: list[dict]) -> tuple[int, int]:
    """How many of these filings' documents the register read, and how many it captured
    but could not read because they are scanned images. A read document carries a
    content hash and a structured extraction; a scanned one carries the hash alone.
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


def checks_section(holder: dict, filings: list[dict], held_here: int) -> str:
    """What the register can and cannot check here. Identical in shape for everyone."""
    roster_read = holder.get("source", {}).get("retrieved_at", "")[:10]
    n = len(filings)
    if n:
        index_line = (
            f"<b>in the register</b> · {n} {plural(n, 'row', 'rows')} of the Clerk's 2025 index "
            "matched to this name."
        )
        read, scanned = documents_read(filings)
        pending = n - read - scanned
        if read == n:
            documents = (
                "<b>read</b> · the register read each document, recorded its hash, and confirmed "
                "the seat and filing ID printed inside it against the roster; the transactions "
                "the reports list are in the register's rows and not yet shown here, pending "
                "the Council's reading of that surface."
            )
        elif read or scanned:
            parts = [f"<b>partly read</b> · {read} of {n} documents read and hashed"]
            if scanned:
                parts.append(
                    f"{scanned} {plural(scanned, 'is a', 'are')} scanned "
                    f"{plural(scanned, 'image', 'images')} the register captured, hashed and "
                    "does not read"
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
            f"against the Clerk's roster.{aside} This is a gap in the register's matching, not a "
            "statement that no filing was made."
        )
        documents = "<b>not yet</b> · the register has not read any document for this record."
    return (
        '<section class="checks">\n<h2>What the register can check here</h2>\n<dl class="terms">\n'
        f"<dt>Identity</dt><dd><b>in the register</b> · from the Clerk's roster, read "
        f"{esc(roster_read)}.</dd>\n"
        f"<dt>Filings index</dt><dd>{index_line}</dd>\n"
        f"<dt>Documents</dt><dd>{documents}</dd>\n"
        "<dt>Signals</dt><dd><b>none defined</b> · so none can fire, for anyone.</dd>\n"
        "</dl>\n</section>"
    )


def filings_section(filings: list[dict], held_here: int) -> str:
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
            f'<td><a href="{esc(f["source"]["url"])}">Open the Clerk\'s copy</a></td>'
            f'<td class="idx">{esc(f["source"]["retrieved_at"][:10])}</td>'
            "</tr>"
        )
    n = len(rows)
    return (
        f"<section>\n{heading}<table>\n"
        f"<caption>{n} {plural(n, 'row', 'rows')} of the Clerk's 2025 index matched to this name, "
        "oldest first. The one-letter code is the Clerk's own and the Clerk does not publicly "
        "define it; the register does not interpret it. Open the document to see what it is. "
        "Rows coded P are served from the Clerk's transaction-report path, which is the one code "
        f'the register files as a transaction report (<a href="{SOURCES_F1}">SOURCES.md F.1</a>).'
        "</caption>\n"
        "<thead><tr><th>Date filed</th><th>The Clerk's code</th>"
        "<th>The document</th><th>Fetched</th></tr></thead>\n<tbody>\n"
        + "\n".join(rows)
        + "\n</tbody>\n</table>\n</section>"
    )


def render_officeholder(
    holder: dict, filings: list[dict], meta: dict, striker, held_here: int = 0
) -> str:
    office = holder["offices"][0] if holder.get("offices") else {}
    seal = striker.strike(holder["id"], meta.get("digest", ""), ticks=0, bars=0)
    roster_read = holder.get("source", {}).get("retrieved_at", "")[:10]
    sworn = sworn_date(holder)
    office_line = f"{esc(office.get('title', ''))} · seat {esc(office.get('seat', ''))}"
    if sworn:
        office_line += f" · sworn {esc(sworn)}, per the roster read {esc(roster_read)}"
    head = (
        '<header class="frame">\n'
        f'<p class="frame">{esc(FRAME)}</p>\n'
        '<div class="masthead">\n<div>\n'
        '<p class="kicker">Oath · the register</p>\n'
        f"<h1>{esc(holder['legal_name'])}</h1>\n"
        f'<p class="office">{office_line}</p>\n'
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
        f'{head}\n<main id="main">\n{REQUIRES}\n{checks_section(holder, filings, held_here)}\n'
        f"{filings_section(filings, held_here)}\n{SIGNALS}\n{how_to_read(True)}\n</main>\n"
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
        f"; {scanned} more {plural(scanned, 'is a', 'are')} scanned "
        f"{plural(scanned, 'image', 'images')} the register captured, hashed and does not read"
    )


def state_of_record(
    meta: dict,
    run: dict,
    holders: list[dict],
    filings: list[dict],
    offices: list[dict],
    at_seat_total: int,
    rejected_url: str,
) -> str:
    """Numbers about the register and the chamber as a whole. None is about a person."""
    counts = run.get("counts", {})
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
    held = run.get("rejected_by_reason", {}).get("surname matches exactly one sitting member", 0)
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
        f"{year} index matched to their name{bar(with_row, filled)}</dd>\n"
        f"<dt>{matched}</dt><dd>index rows matched, each linked to the Clerk's own document</dd>\n"
        f"<dt>{read}</dt><dd>of {matched} documents read by the register so far, each checked "
        f"against the seat and filing ID printed inside it{scanned_clause(scanned)}; the links "
        f"open the Clerk's copies{bar(read, matched)}</dd>\n"
        f"<dt>{held}</dt><dd>index rows set aside for the maintainer to decide by hand, because "
        f"the register does not guess; {at_seat_total} of them sit at a member's own seat under "
        "the member's surname. Whether a page is quiet is decided by whether the name on the "
        f'form matched the roster exactly, not by what was filed. <a href="{rejected_url}">The '
        "rows, with reasons</a>.</dd>\n"
        "<dt>0</dt><dd>signals defined, so 0 fired; silence is a legitimate result</dd>\n"
        "</dl>\n"
        f'<p class="quiet">{fresh}The seal fixes exactly this reading.</p>\n'
        f"{chart}</section>"
    )


def render_index(
    holders: list[dict],
    offices: list[dict],
    filings: list[dict],
    run: dict,
    meta: dict,
    striker,
    at_seat: dict[str, int] | None = None,
    rejected_url: str = REPO + "data/rejected/house-fd/",
) -> str:
    at_seat = at_seat or {}
    holder_by_seat = {h["offices"][0]["seat"]: h for h in holders}
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
        '<p class="lede">This build holds no signals: no condition has been written against the '
        "record yet, so no page reports one. A page with no signal fired is the expected page. "
        "Quiet means no written condition is present in the record.</p>\n"
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
    record = state_of_record(
        meta, run, holders, filings, offices, sum(at_seat.values()), rejected_url
    )
    body = (
        f'{head}\n<main id="main">\n{door}\n{tile_map(offices)}\n{record}\n{table}\n'
        f"{how_to_read(False)}\n</main>\n{footer(meta, home=True)}"
    )
    return page("Every seat in the register", body)


# ---- main ---------------------------------------------------------------------------------


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
    holders = read_ndjson(root / "data" / "officeholders.ndjson")
    filings = read_ndjson(root / "data" / "filings.ndjson")
    offices = read_ndjson(root / "data" / "offices.ndjson")
    runs = sorted((root / "data" / "adapter-runs").glob("house-fd-*.ndjson"))
    run = read_ndjson(runs[-1])[0] if runs else {}
    rejected_files = sorted((root / "data" / "rejected" / "house-fd").glob("*.ndjson"))
    rejected = read_ndjson(rejected_files[-1]) if rejected_files else []
    at_seat = held_at_seat(rejected)
    rejected_url = (
        REPO + rejected_files[-1].relative_to(root).as_posix()
        if rejected_files
        else REPO + "data/rejected/house-fd/"
    )
    by_holder: dict[str, list[dict]] = {}
    for f in filings:
        by_holder.setdefault(f["officeholder_id"], []).append(f)

    (out / "officeholders").mkdir(parents=True, exist_ok=True)
    for h in holders:
        seat = h["offices"][0]["seat"] if h.get("offices") else ""
        target = out / "officeholders" / f"{slug(h['id'])}.html"
        target.write_text(
            render_officeholder(h, by_holder.get(h["id"], []), meta, striker, at_seat.get(seat, 0)),
            encoding="utf-8",
            newline="\n",
        )
    (out / "index.html").write_text(
        render_index(holders, offices, filings, run, meta, striker, at_seat, rejected_url),
        encoding="utf-8",
        newline="\n",
    )
    digest = meta.get("digest", "")
    (out / "mark.svg").write_text(
        striker.strike(digest, digest, with_wordmark=True), encoding="utf-8", newline="\n"
    )

    quiet = sum(1 for h in holders if not by_holder.get(h["id"]))
    shown = out.relative_to(root).as_posix() if out.is_relative_to(root) else str(out)
    print(f"rendered {len(holders)} pages, the index, and mark.svg to {shown}")
    print(f"{quiet} pages have no matched row; each says so, with the count set aside at its seat")
    print("Now run: python tools/lint-frame-presence.py && python tools/lint-no-ranking.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
