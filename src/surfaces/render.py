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
import math
import os
import posixpath
import re
import sys
import unicodedata
from datetime import date, timedelta
from pathlib import Path

FRAME = "Presence in the register is not evidence of wrongdoing."
# The three pages at the site's root, named once: the footer's back link, every cross-link
# and each page's own title read from here, so none can drift from another.
HOME_TITLE = "The oath and the record"
SEATS_TITLE = "Every seat in the register"
SEATS_PAGE = "seats.html"
RECORD_TITLE = "How this register was built"
RECORD_PAGE = "record.html"
CLERK_SITE = "https://disclosures-clerk.house.gov/FinancialDisclosure"
# Where the Clerk serves each document the index lists by DocID, codes other than P
# (SOURCES.md F.1).
CLERK_BASE = "https://disclosures-clerk.house.gov/"
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
NEXT_ENDS = REPO + "NEXT.md#e1-the-committees-own-record-the-source-the-register-does-not-read"
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
# The route BYLAWS §6 promises a subject, which no page named until now: the correction form and
# the pull request, both of which already existed, and neither of which a person reading about
# themselves could find (the Council's second reading of the built answer, Seat B).
CORRECTION_FORM = "https://github.com/jeb2-spec/Oath/issues/new?template=correction.yml"
SECURITY_MD = REPO + "SECURITY.md"
# Where the course carries what the sealed doctrine should say about a filed document the
# register keeps no copy of: EVIDENCE §7 says the register may keep the bytes, and INVARIANTS
# §16 plans a bundle that holds them, so the practice cites the decision, not a section that
# says otherwise (the Council's fourth reading of S.1b, Seats A, C and G).
# The anchor, not the file: a private person reading about a name in a report needs the
# paragraph, and NEXT.md is long enough that the top of it is not an answer (the Council's
# fifth reading of S.1b, Seats C and F).
NEXT_D4 = REPO + "NEXT.md#d4-doctrine-catch-up"
CHANGES_DATA = REPO + "data/changes.ndjson"
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
  --spot: #f2dc7d; --spot-ink: #1c1b16;
  --letter: "Avenir Next", "Trebuchet MS", "Segoe UI", "Helvetica Neue", Arial, sans-serif;
}
@media (prefers-color-scheme: dark) {
  :root { --paper: #141410; --ink: #e9e5d8; --ink-2: #a8a394; --rule: #3a382f; --link: #9ab6f5;
          --spot: #4a3f17; --spot-ink: #f3ead0; }
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
td.idx span.note { white-space: normal; min-width: 8rem; }
td.setby { min-width: 7.5rem; }
span.note.clash { color: var(--ink); border-left: 3px solid var(--ink); padding-left: .35rem;
                  margin-top: .2rem; }
p.quiet { color: var(--ink-2); max-width: 36rem; }
h3 { font-size: 1rem; font-weight: 600; margin: 1.4rem 0 .3rem; }
h3 a { font-weight: 400; }
nav.reports { font-size: .85rem; color: var(--ink-2); line-height: 1.7; }
span.note { display: block; font-size: .82rem; color: var(--ink-2); }
td.amt { white-space: nowrap; }
dl.terms { display: grid; grid-template-columns: fit-content(15rem) minmax(0, 1fr);
           gap: .35rem 1rem; margin: 0; }
dl.terms dt, dl.terms dd { margin: 0; }
dl.terms dt { color: var(--ink); }
dl.terms dd { color: var(--ink-2); }
dl.terms dd b { font-weight: normal; color: var(--ink); font-variant-caps: all-small-caps;
                letter-spacing: .05em; }
/* the answer first: the same shape on every page, whatever the signal found */
section.answer { border-top: 0; margin-top: 0; padding-top: 0; }
section.answer p { max-width: 38rem; margin: 0 0 .6rem; }
section.answer p.quiet { font-size: .95rem; }
nav.jump { font-size: .9rem; margin: .2rem 0 .5rem; line-height: 1.7; }
p.check { font-size: .85rem; color: var(--ink-2); }
/* The frame and the sentence that carries it are not fine print: reduced contrast at the
   end of a paragraph is how every writing system marks an aside, and a reader scanning a
   translated page discounts it (the second reading of the built answer, Seat F). */
p.either, span.either { color: var(--ink); }
p.rule { font-size: .9rem; color: var(--ink-2); max-width: 38rem; margin: 0 0 .5rem; }
/* the comic layer: the institution's and the process's, never a person's */
h1.comic { font: 900 3.6rem/1 var(--letter); text-transform: uppercase; letter-spacing: .03em;
           position: relative; isolation: isolate; margin: .1rem 0 .5rem; }
h1.comic::before { content: attr(data-text); position: absolute; left: .06em; top: .07em;
                   z-index: -1; color: transparent;
                   background-image: radial-gradient(var(--ink-2) 34%, transparent 38%);
                   background-size: 5px 5px; -webkit-background-clip: text; background-clip: text; }
span.tag { display: inline-block; background: var(--spot); color: var(--spot-ink);
           border: 2px solid var(--ink); padding: .15rem .5rem; font: 700 .8rem/1.3 var(--letter);
           letter-spacing: .06em; text-transform: uppercase; box-shadow: 3px 3px 0 var(--ink); }
section.howto, section.glance { border-top: 0; }
ol.strip { list-style: none; padding: 0; margin: .9rem 0 .6rem; display: grid; gap: .7rem;
           grid-template-columns: repeat(4, minmax(0, 1fr)); }
li.panel { border: 3px solid var(--ink); background: var(--paper); box-shadow: 4px 4px 0 var(--ink);
           display: flex; flex-direction: column; }
li.panel p.cap { margin: 0; background: var(--spot); color: var(--spot-ink);
                 border-bottom: 3px solid var(--ink); padding: .35rem .5rem;
                 font: 700 .78rem/1.2 var(--letter); text-transform: uppercase;
                 letter-spacing: .04em; }
li.panel span.no { display: inline-block; min-width: 1.3em; height: 1.3em; line-height: 1.3em;
                   text-align: center; border-radius: 50%; background: var(--ink);
                   color: var(--paper); margin-right: .25rem; }
li.panel > svg { display: block; width: 100%; height: auto; padding: .4rem .5rem 0; }
li.panel p:last-child { margin: .25rem .55rem .55rem; font-size: .82rem; line-height: 1.4;
                        color: var(--ink-2); }
li.panel .ln { fill: none; stroke: var(--ink); stroke-width: 3; stroke-linecap: round;
               stroke-linejoin: round; }
li.panel .ln.thin { stroke-width: 1.8; }
li.panel .paper { fill: var(--paper); }
li.panel .ink { fill: var(--ink); }
li.panel .ht { fill: url(#benday); }
li.panel .bar { fill: var(--ink-2); opacity: .75; }
li.panel text { font: 700 11px var(--letter); fill: var(--ink); }
p.punch { font: 700 1.02rem/1.45 var(--letter); max-width: 40rem; margin: .8rem 0 0; }
@media (max-width: 40rem) {
  ol.strip { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  h1.comic { font-size: 3rem; }
}
/* closing the loop: the chain, and the pieces that would mend it */
figure.loop { margin: .6rem 0 .3rem; }
svg.loop { width: 100%; max-width: 34rem; height: auto; display: block; }
.link.held { fill: var(--ink); fill-opacity: .16; stroke: var(--ink); stroke-width: 2.2; }
.link.open { fill: none; stroke: var(--ink-2); stroke-width: 1.4; stroke-dasharray: 4 3; }
.lbrace { stroke: var(--ink-2); stroke-width: 1; }
svg.loop text { font: 700 9px var(--letter); fill: var(--ink-2); }
svg.loop text.lct { font-size: 8px; }
nav.parts ul { list-style: none; margin: .6rem 0 0; padding: 0; display: flex;
  flex-wrap: wrap; gap: .3rem 1.1rem; font-size: .9rem; }
div.want { margin: 1.1rem 0 0; padding-top: .7rem; border-top: 1px solid var(--rule); }
div.want h3 { margin: 0 0 .25rem; font: 700 1.06rem/1.35 var(--letter); }
p.tags { margin: 0 0 .5rem; display: flex; flex-wrap: wrap; gap: .35rem .5rem;
  align-items: baseline; font-size: .82rem; }
span.tag2 { border: 1px solid var(--rule); padding: .04rem .38rem; color: var(--ink-2); }
div.want dl { margin: 0; display: grid; grid-template-columns: minmax(8rem, 12rem) 1fr;
  gap: .18rem .9rem; font-size: .94rem; }
div.want dt { font: 700 .78rem/1.5 var(--letter); letter-spacing: .04em;
  text-transform: uppercase; color: var(--ink-2); }
div.want dd { margin: 0; }
@media (max-width: 34rem) { div.want dl { grid-template-columns: 1fr; }
  div.want dd { margin: 0 0 .4rem; } }
/* where the record ends */
section.ends { border-top: 0; }
figure.ends { margin: .6rem 0 .3rem; }
svg.ends { width: 100%; max-width: 36rem; height: auto; display: block; }
.esq { fill: var(--ink); }
.evoid { fill: none; stroke: var(--ink-2); stroke-width: 1; stroke-dasharray: 4 3; }
.eline { stroke: var(--ink); stroke-width: 2.2; stroke-linecap: round; }
.eaxis { stroke: var(--ink); stroke-width: 2.4; stroke-linecap: round; }
svg.ends text { font: 700 9px var(--letter); fill: var(--ink-2); }
svg.ends text.eq { font: 700 22px var(--letter); fill: var(--ink-2); }
ul.squarekey svg.key .evoid { stroke-width: 1.6; stroke-dasharray: 3 2; }
/* the deadline: by it, or after it */
section.deadline { border-top: 0; }
figure.deadline { margin: .6rem 0 .3rem; }
svg.deadline { width: 100%; max-width: 36rem; height: auto; display: block; }
.dl.by { fill: url(#benday50); stroke: var(--ink); stroke-width: 1.6; }
.dl.after { fill: var(--ink); }
.dshadow { fill: var(--ink); }
.dpaper, .dlabel { fill: var(--paper); }
.dlabel { stroke: var(--ink); stroke-width: 1; }
.dtag { fill: var(--spot); stroke: var(--ink); stroke-width: 1.2; }
svg.deadline text.dtagt { font: 700 7.5px var(--letter); letter-spacing: .06em;
  text-transform: uppercase; fill: var(--spot-ink); }
.dfan { fill: url(#benday); fill-opacity: .35; stroke: var(--ink-2); stroke-width: .6; }
.dline { stroke: var(--ink); stroke-width: 2.2; stroke-linecap: round; }
.daxis { stroke: var(--ink); stroke-width: 2.4; stroke-linecap: round; }
.dtick { stroke: var(--ink-2); stroke-width: .8; }
svg.deadline text { font: 700 9px var(--letter); fill: var(--ink-2); }
svg.deadline text.don { font-size: 10px; fill: var(--ink); }
svg.deadline text.doff { font-size: 10px; fill: var(--paper); }
figure svg text.stamp { font: 600 6px var(--mono); letter-spacing: .02em; fill: var(--ink-2); }
.stampwave { fill: none; stroke: var(--ink-2); stroke-width: .35; }
/* the annual report: the report's date beside the due date and the latest date the law allows */
section.annual { border-top: 0; }
figure.annual, figure.annualchart { margin: .6rem 0 .3rem; }
figure.annual > svg, svg.annualchart { width: 100%; max-width: 36rem; height: auto;
  display: block; }
figure.annual figcaption { max-width: 36rem; margin-top: .35rem; }
.abracket { fill: none; stroke: var(--ink); stroke-width: 1.2; }
.aline { stroke: var(--ink); stroke-width: 1.6; }
.aaxis { stroke: var(--ink); stroke-width: 2.2; stroke-linecap: round; }
.atick { stroke: var(--ink-2); stroke-width: .8; }
.amark { stroke: var(--ink); stroke-width: 1.4; }
.amark.after, .acol.after { fill: var(--ink); }
.amark.compared, .acol.compared { fill: url(#benday50); }
.amark.read, .acol.read { fill: url(#benday); }
.acol.compared, .acol.read { stroke: var(--ink); stroke-width: .3; }
figure svg text.alaw, figure svg text.afiled, svg.annualchart text.amonth {
  font: 700 8px var(--letter); fill: var(--ink-2); }
figure svg text.afiled { fill: var(--ink); }
/* a person's year, drawn: every report on one line of time, in the landing's own grammar */
figure.year { margin: .8rem 0 .4rem; }
figure.year .yscroll { overflow-x: auto; max-width: 44rem; }
figure.year .yscroll > svg { width: 100%; min-width: 31rem; height: auto; display: block; }
.amark.void { fill: var(--paper); stroke: var(--ink); stroke-width: 1.2; stroke-dasharray: 2 1.5; }
.amark.unread { fill: none; stroke: var(--ink-2); stroke-width: 1; stroke-dasharray: 1.4 1.2; }
.ysworn { fill: var(--ink); }
.yearkey .amark.after { fill: var(--ink); opacity: 1; }
figure.year figcaption { max-width: 38rem; margin-top: .35rem; }
ul.yearkey { display: grid; grid-template-columns: repeat(auto-fill, minmax(15rem, 1fr));
  gap: .1rem 1rem; max-width: 44rem; font-size: .82rem; margin: .4rem 0 .2rem; }
.ybound { stroke: var(--ink-2); stroke-width: .8; stroke-dasharray: 2 2; }
.yspan { stroke: var(--ink); stroke-width: .9; }
.ytrade { fill: var(--ink); }
.yearly { fill: none; stroke: var(--ink); stroke-width: 1.2; stroke-linejoin: round; }
.yafter { fill: var(--ink); }
.ydead { stroke: var(--ink); stroke-width: 1.4; }
figure.year .sq { stroke: var(--ink); stroke-width: .9; }
figure.year .sq.s-unchecked { fill: var(--paper); stroke: var(--ink-2); stroke-width: .9;
  stroke-dasharray: 1.6 1.2; }
figure.year a:focus-visible rect { stroke: var(--link); stroke-width: 2.5; }
figure svg text.ylane { font: 700 9px var(--letter); letter-spacing: .08em;
  text-transform: uppercase; fill: var(--ink-2); }
figure svg text.ymonth { font: 700 9.5px var(--letter); fill: var(--ink-2); }
.yvoid { fill: none; stroke: var(--ink-2); stroke-width: .9; stroke-dasharray: 3 2; }
figure svg text.yvoidt { font: 700 9px var(--letter); fill: var(--ink-2); }
figure svg text.yyear { font: 700 9.5px var(--letter); fill: var(--ink); }
ul.notices { margin: .2rem 0 .7rem; padding-left: 1.1rem; font-size: .9rem; }
span.printed { color: var(--ink); }
/* the notice clock */
section.noticeclock { border-top: 0; }
figure.noticeclock { margin: .6rem 0 .3rem; }
svg.noticeclock { width: 100%; max-width: 36rem; height: auto; display: block; }
.nb.within { fill: url(#benday50); stroke: var(--ink); stroke-width: .4; }
.nb.past { fill: var(--ink); }
.nb.before { fill: none; stroke: var(--ink); stroke-width: .8; stroke-dasharray: 1.4 1.2; }
.nl { stroke: var(--ink); stroke-width: 2.2; stroke-linecap: round; }
.nl.thirty { stroke-width: 1.2; stroke-dasharray: 3 2; }
.na { stroke: var(--ink); stroke-width: 2.4; stroke-linecap: round; }
/* the strip's caption box, for a line the rule draws on a figure */
.stag { fill: var(--spot); stroke: var(--ink); stroke-width: 1.2; }
svg text.stagt { font: 700 7px var(--letter); letter-spacing: .06em; text-transform: uppercase;
  fill: var(--spot-ink); }
svg.noticeclock text { font: 700 9px var(--letter); fill: var(--ink-2); }
/* the house at a glance */
p.glance { font-size: 1.12rem; line-height: 1.5; max-width: 38rem; margin: 0 0 .5rem; }
figure.glance { margin: .5rem 0 .2rem; }
figure.glance svg.squares { width: 100%; max-width: 30rem; }
/* where the record narrows: the register's own reach, in the page's own ink */
figure.narrows { margin: 1rem 0 .4rem; }
figure.narrows svg { width: 100%; max-width: 34rem; height: auto; display: block;
                     color: var(--ink); }
figure.narrows text { font: 13px var(--mono); }
figure.narrows text.in { fill: var(--paper); }
.nrshadow { fill: var(--ink); }
.nrpaper { fill: var(--paper); }
.nr { stroke: var(--ink); stroke-width: 1.6; }
.nr.listed { fill: var(--paper); }
.nr.read { fill: url(#benday); }
.nr.compared { fill: url(#benday50); }
.nr.after { fill: var(--ink); }
figure.narrows text.out { fill: var(--ink); }
dl.narrows { margin: .3rem 0 .6rem; display: grid; grid-template-columns: auto 1fr;
             gap: .35rem .75rem; max-width: 40rem; font-size: .92rem; }
dl.narrows dt { font-family: var(--mono); text-align: right; white-space: nowrap; }
dl.narrows dd { margin: 0; }
@media (max-width: 40rem) {
  dl.narrows { grid-template-columns: 1fr; gap: .1rem; }
  dl.narrows dt { text-align: left; }
  dl.narrows dd { margin: 0 0 .5rem; }
}
/* the route a person named here takes to dispute a fact, in the page's own terms style */
section.disputes dl { display: grid; grid-template-columns: minmax(12rem, 18rem) 1fr;
                      gap: .45rem 1.1rem; margin: .6rem 0 0; }
section.disputes dt { font-weight: 600; }
section.disputes dd { margin: 0; }
@media (max-width: 46rem) {
  section.disputes dl { grid-template-columns: 1fr; gap: .1rem; }
  section.disputes dd { margin: 0 0 .7rem; }
}
/* the reports as squares, the same on the landing and on a person's page */
svg.squares { display: block; max-width: 100%; height: auto; margin: .3rem 0 .4rem; }
.sq.s-after { fill: var(--ink); }
.sq.s-checked { fill: url(#benday50); }
.sq.s-unchecked { fill: none; stroke: var(--ink-2); stroke-width: .8; stroke-dasharray: 1.5 1.5; }
svg.squares a:focus-visible rect { stroke: var(--link); stroke-width: 2.5; }
div.reportline { display: flex; flex-wrap: wrap; align-items: center; gap: .2rem 1rem;
                 margin: 0 0 .7rem; }
div.reportline svg.squares { margin: 0; }
ul.squarekey { list-style: none; margin: .2rem 0 .6rem; padding: 0; font-size: .88rem;
               color: var(--ink-2); }
ul.squarekey.short { display: flex; flex-wrap: wrap; gap: .1rem 1rem; margin: 0; }
ul.squarekey b { font-family: var(--mono); font-weight: normal; color: var(--ink); }
ul.squarekey svg.key { width: .85em; height: .85em; vertical-align: -.08em; }
/* a Finding's dates on a line, drawn from its rows; inked from the page's own tokens */
figure.dates { margin: .9rem 0 .4rem; }
figure.dates > svg { width: 100%; max-width: 34rem; height: auto; display: block; }
figure.dates figcaption { max-width: 36rem; margin-top: .35rem; }
.dates .window, .key .window { stroke: var(--ink-2); stroke-width: 1.4; }
.dates .after, .key .after { fill: var(--ink-2); opacity: .55; }
.dates .deadline, .key .deadline { stroke: var(--ink); stroke-width: 1.6; }
.dates .next, .key .next { fill: var(--paper); stroke: var(--ink); stroke-width: 1.3; }
.dates .trade, .key .trade { fill: var(--ink); }
.dates .notice, .key .notice { fill: var(--paper); stroke: var(--ink); stroke-width: 1.2; }
.dates .filed { stroke: var(--ink); stroke-width: 1.2; }
.dates .axis { stroke: var(--ink-2); stroke-width: 1; }
.dates text { font-family: var(--mono); font-size: 12px; fill: var(--ink-2); }
figure.dates > svg { direction: ltr; }
.dates text.days { fill: var(--ink); }
svg.key { width: 1.1em; height: .8em; vertical-align: -.05em; overflow: visible; }
details { margin: .2rem 0 .8rem; }
summary { cursor: pointer; font-size: .9rem; color: var(--link); padding: .25rem 0; }
summary:focus-visible { outline: 2px solid var(--link); outline-offset: 2px; }
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
  figure.seal { width: auto; display: flex; gap: .8rem; align-items: center; }
  header .masthead figure.seal figcaption { display: none; }
  figure.seal svg { width: 64px; height: 64px; margin: 0; flex: none; }
  dl.terms, .record dl { grid-template-columns: 1fr; }
  .record dt { text-align: left; }
}
@media print {
  html { font-size: 11pt; background: #fff; color: #000; }
  .skip { display: none; } a { color: inherit; }
  figure.seal { width: 28mm; } figure.seal svg { width: 28mm; height: 28mm; }
  table, figure { break-inside: avoid; }
  details::details-content { content-visibility: visible; display: block; }
  nav.jump { display: none; }
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


def year_of(run: dict) -> int:
    """The filing year the adapter's run record states. A sentence about a year is not renderable
    without one: a build with no run record, or one whose record does not state its year, published
    four hundred and thirty-nine pages each asserting a fact about a specific year's Clerk index,
    sourced to a Python default argument (the Council's second reading of the built answer, Seat
    G)."""
    year = run.get("year")
    if not isinstance(year, int):
        raise SystemExit(
            "refusing to render: no adapter run record states the filing year, and every page "
            "names it. The year is what dates the answer's claim about the Clerk's index, so a "
            "page cannot be rendered without it. Build the rows first "
            "(src/adapters/house-fd/build.py), or say which run record to read."
        )
    return year


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
        # The one durable anchor in every page's answer, so it must not default.
        "year": year_of(run),
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


def earlier_builds(change: dict, history: list[dict] = ()) -> str:
    """Where a reader finds a filer's own text as filed, after a correction moved it. The
    fingerprint the change row keeps is not the text, and saying only that would tell the
    reader the text is gone: every sealed build stays in this repository's history, and the
    builds before the one that sealed the correction carry the line (the Council's fourth
    reading of S.1b, Seats B, E and G).

    The build named is the one that sealed the FIRST correction of this fact, not this one.
    Where a filer's own text was corrected twice, the builds before the second carry the
    maintainer's first wording and not the line as filed, so naming this correction's build
    sent a reader to builds that do not hold what the sentence promises (the Council's fifth
    reading of S.1b, Seats C and F)."""
    first = min(
        (
            c
            for c in (history or ())
            if c["change"] == "corrected"
            and c.get("field") == change.get("field")
            and "was_sha256" in c
            and c.get("build")
        ),
        key=lambda c: (c.get("decided_at") or "", c.get("build") or ""),
        default=change,
    )
    return (
        f"the builds before <code>{esc(first['build'])}</code>"
        if first.get("build")
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
    """A link to an officeholder's page, named as the Clerk's roster listed them. Every caller
    names the officeholder a correction moved a report from or to, and the link says so, so the
    no-ranking gate can hold every other link off a person's page (INVARIANTS §13)."""
    return (
        f'<a href="{to_root}{esc(slug(holder_id))}.html" data-cross="correction">'
        f"{esc(NAMES.get(holder_id, holder_id))}</a>"
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
    back = "" if home else f'<p><a href="{to_root}index.html">{esc(HOME_TITLE)}</a></p>\n'
    return (
        "<footer>\n"
        f"{back}"
        f"<p>Build <code>{esc(build_label(meta))}</code>, from the sources as read up to "
        f"<code>{esc(meta.get('built_at'))}</code>; its anchor, a timestamp proof, fixes when it "
        f"provably existed. {anchor_line}</p>\n"
        '<p id="verify">Cite the build, not the page. Verify it: '
        "<code>python tools/verify.py</code>. "
        "The digest proves the rows these pages are rendered from are unchanged since sealing; "
        "it does not prove the Clerk's index is right. All dates the register read something "
        "are UTC; the dates the Clerk gives are the Clerk's.</p>\n"
        "</footer>"
    )


def seal_figure(svg: str, caption: str) -> str:
    """The mark with its caption. The mark carries its own title and description, because it is
    also served on its own as mark.svg; inside a captioned figure those make a screen reader say
    the same three sentences twice, so here the caption is the one voice and the drawing is
    presentational (the Council's fifth reading of S.1b, Seat E)."""
    quiet = svg.replace('role="img" aria-labelledby="t d"', 'role="presentation"', 1)
    return f'<figure class="seal">\n{quiet}<figcaption>{esc(caption)}</figcaption>\n</figure>'


REQUIRES = (
    '<section id="requires" class="requires">\n<h2>What this office requires</h2>\n'
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
    "prohibit the transactions it requires reported; a report listed on this page is a filing made "
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
            f"{n:,} {plural(n, 'report is', 'reports are')} fetched and not read: the "
            "register found no Filing ID line in the text it extracted, and reads nothing "
            "from such a document, so the transactions printed in it are not listed here."
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
        return "the reports attributed were not read: no Filing ID line to read, or not fetched"
    if outcomes:
        return "it could evaluate no row, for the reasons below"
    if held_reports:
        return "no transaction report is attributed; those at this seat are set aside"
    return "no transaction report is attributed"


def falls_on_words(falls_on: str) -> str:
    return f"a {falls_on}" if falls_on in ("Saturday", "Sunday") else f"{falls_on}, a holiday"


def finding_groups(finding: dict) -> list[tuple[tuple, int]]:
    """A Finding's rows after the deadline, grouped where their dates agree, in the order the
    table prints them and the figure draws them: one list, so the two cannot disagree."""
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
    return sorted(groups.items(), key=lambda item: (item[0][3], item[0][0]))


# The figure of a Finding's dates. The viewBox is about a phone's width, so a phone draws it
# near one to one and its dates stay legible at 360px; a wider screen scales it up to the
# column's width. The right margin holds the count of days after, the only number in a line.
FIG_W, FIG_LEFT, FIG_RIGHT, FIG_TOP, FIG_ROW, FIG_AXIS = 360, 8, 40, 10, 18, 32
KEY_MARKS = {
    "trade": '<circle class="trade" cx="7" cy="5" r="2.7"/>',
    "notice": '<path class="notice" d="M7 .4 11.6 5 7 9.6 2.4 5Z"/>',
    "deadline": '<line class="deadline" x1="7" y1="0.5" x2="7" y2="9.5"/>',
    "next": '<circle class="next" cx="7" cy="5" r="3.4"/>',
    "after": '<rect class="after" x="1" y="2" width="12" height="6"/>',
}


def key_mark(name: str) -> str:
    """One of the figure's marks, drawn the same way in its caption, for a sighted reader;
    the caption's words carry it for everyone else."""
    return (
        f'<svg class="key" viewBox="0 0 14 10" aria-hidden="true" focusable="false">'
        f"{KEY_MARKS[name]}</svg>"
    )


def dates_figure(finding: dict) -> str:
    """The dates a Finding rests on, on a line: each row of its table drawn to scale in days,
    from the earliest date the rows print to the date the Clerk's index gives the report.
    Derived from the Finding's own rows and nothing else, so it regenerates with them (RUBRIC
    gate 4). No script, no font, no colour a theme does not set; the caption says what the
    figure shows and what it does not."""
    groups = finding_groups(finding)
    filed = date.fromisoformat(finding["evidence"]["filed_at"])
    marks = []
    for key, _n in groups:
        traded, notified, notification, deadline = key[0], key[1], key[2], key[3]
        marks += [date.fromisoformat(traded), date.fromisoformat(deadline)]
        if notified and notification == "applied":
            marks.append(date.fromisoformat(notified))
        if key[5] and key[6]:
            marks.append(date.fromisoformat(key[6]))
    start, end = min(marks + [filed]), max(marks + [filed])
    span = max((end - start).days, 1)
    inner = FIG_W - FIG_LEFT - FIG_RIGHT

    def x(day: date) -> float:
        return FIG_LEFT + (day - start).days / span * inner

    def f(value: float) -> str:
        return f"{value:.1f}".rstrip("0").rstrip(".")

    rows_end = FIG_TOP + len(groups) * FIG_ROW
    height = rows_end + FIG_AXIS
    parts, rings, spoken = [], [], []
    for i, (key, _n) in enumerate(groups):
        traded, notified, notification, deadline = key[0], key[1], key[2], key[3]
        falls_on, next_day, days = key[5], key[6], key[9]
        y = FIG_TOP + i * FIG_ROW + FIG_ROW / 2
        t, d = x(date.fromisoformat(traded)), x(date.fromisoformat(deadline))
        right = x(filed)
        parts.append(f'<line class="window" x1="{f(t)}" y1="{f(y)}" x2="{f(d)}" y2="{f(y)}"/>')
        parts.append(
            f'<rect class="after" x="{f(d)}" y="{f(y - 3)}" width="{f(max(right - d, 2))}" '
            'height="6"/>'
        )
        if falls_on and next_day:
            # Drawn last, on top of the upright line, so it shows exactly where it decides.
            rings.append((x(date.fromisoformat(next_day)), y))
        spoken.append(f"{days:,}")
        parts.append(
            f'<line class="deadline" x1="{f(d)}" y1="{f(y - 6)}" x2="{f(d)}" y2="{f(y + 6)}"/>'
        )
        # The diamond first and wider than the dot, so a notice on the day of the trade reads
        # as a dot inside a diamond rather than hiding it.
        if notified and notification == "applied":
            n = x(date.fromisoformat(notified))
            parts.append(
                f'<path class="notice" d="M{f(n)} {f(y - 4.6)} {f(n + 4.6)} {f(y)} '
                f'{f(n)} {f(y + 4.6)} {f(n - 4.6)} {f(y)}Z"/>'
            )
        parts.append(f'<circle class="trade" cx="{f(t)}" cy="{f(y)}" r="2.7"/>')
        parts.append(
            f'<text class="days" x="{f(FIG_W - FIG_RIGHT + 12)}" y="{f(y + 4)}">{days:,}</text>'
        )
    # The axis: the first of each month as a tick, the two ends as dates.
    axis_y = rows_end + 5
    ticks = []
    month = date(start.year, start.month, 1)
    while month <= end:
        if month > start:
            ticks.append(
                f'<line class="axis" x1="{f(x(month))}" y1="{f(axis_y)}" x2="{f(x(month))}" '
                f'y2="{f(axis_y + 4)}"/>'
            )
        month = date(month.year + month.month // 12, month.month % 12 + 1, 1)
    right = x(filed)
    parts.append(
        f'<line class="filed" x1="{f(right)}" y1="{f(FIG_TOP - 4)}" x2="{f(right)}" '
        f'y2="{f(axis_y + 4)}"/>'
    )
    parts += [f'<circle class="next" cx="{f(rx)}" cy="{f(ry)}" r="3.6"/>' for rx, ry in rings]
    parts.append(
        f'<line class="axis" x1="{f(FIG_LEFT)}" y1="{f(axis_y)}" x2="{f(right)}" y2="{f(axis_y)}"/>'
    )
    parts += ticks
    parts.append(
        f'<text x="{f(FIG_LEFT)}" y="{f(axis_y + 18)}">{esc(start.isoformat())}</text>'
        f'<text x="{f(right)}" y="{f(axis_y + 18)}" text-anchor="end">'
        f"{esc(filed.isoformat())}</text>"
    )
    days_across = (filed - start).days
    caption = (
        "The dates this Finding rests on, to scale in days, one line for each row of the table "
        f"below and in the same order: the transaction (a dot {key_mark('trade')}), the date the "
        f"report says the filer was notified (a diamond {key_mark('notice')}), the deadline the "
        f"rule sets (a tick {key_mark('deadline')}, and a ring {key_mark('next')} at the first "
        "business day after a deadline that falls on a weekend or holiday), and the days "
        f"from the deadline to the date the Clerk's index gives the report (a bar "
        f"{key_mark('after')}, its count at the end of the line). The upright line is that date, "
        f"{esc(filed.isoformat())}; the left edge is {esc(start.isoformat())}, {days_across:,} "
        f"{plural(days_across, 'day', 'days')} earlier; a tick on the axis marks the first of "
        "each month. "
        + (
            "Where a ring sits on the upright line, the report is dated on that first business "
            "day. "
            if any(abs(rx - x(filed)) < 0.05 for rx, _ in rings)
            else ""
        )
        + "The figure shows a span of days. It does not show why the span is what it "
        "is, whether notice reached the filer when the report says, or anything the House "
        "Committee on Ethics has determined."
    )
    label = (
        f"{len(groups):,} {plural(len(groups), 'line', 'lines')}; days from the deadline to the "
        f"report's date, {filed.isoformat()}: {', '.join(spoken)}"
    )
    cap = "dates-" + re.sub(r"[^a-z0-9]+", "-", finding["id"].lower()).strip("-")
    return (
        f'<figure class="dates">\n<svg viewBox="0 0 {FIG_W} {f(height)}" direction="ltr" '
        f'role="img" aria-label="{esc(label)}" aria-describedby="{cap}">'
        + "".join(parts)
        + f'</svg>\n<figcaption id="{cap}">{caption}</figcaption>\n</figure>'
    )


def finding_rows_table(finding: dict) -> str:
    """The rows after the deadline, grouped where their dates agree, so a report of eighty
    identical rows reads as one line with its count."""
    body = []
    for key, n in finding_groups(finding):
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
            f'<td class="setby">{esc(SET_BY_WORDS.get(set_by, set_by))}</td>'
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
        # A different file whose rows read as the published ones is not a file that reads
        # otherwise. This mark is lifted alone and set beside a Finding, where a bare "was a
        # different file" read as the document having changed under it (the Council's fifth
        # reading of S.1b, Seats C, D and F).
        replaced = state["replaced"]
        marks.append(
            f"the Clerk's copy read {when(replaced)} was a different file, which "
            + (
                "reads as the rows the register published"
                if not replaced.get("differs")
                else "reads otherwise"
            )
        )
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
        f"{dates_figure(finding)}\n"
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
    held_notices: list[dict] | None = None,
) -> str:
    """Signals that fired and Signals that did not, for one officeholder, grouped by Signal
    and never by severity (ECOSYSTEM.md §1.3; METHODOLOGY.md §10). Every defined Signal is
    named on every page, so silence is shown rather than assumed, and says which it is. A
    Finding an earlier version produced stays on the page, under that version, as published."""
    fired, quiet = [], []
    fetched = {
        fid for fid, f in filings_by_id.items() if (f.get("source") or {}).get("content_hash")
    }

    def blocks_for(signal_id: str, block=finding_block) -> tuple[str, str]:
        mine = sorted(
            fired_now(findings, signal_id), key=lambda f: (f["evidence"]["filed_at"], f["id"])
        )
        withdrawn = "".join(
            withdrawal_line(f, findings, filings_by_id)
            for f in sorted(withdrawn_now(findings, signal_id), key=lambda f: f["id"])
        ) + moved_findings_line(findings, signal_id)
        found = "\n".join(
            block(f, filings_by_id.get(f["producing_filings"][0]), findings, changes) for f in mine
        )
        return withdrawn, found

    for signal in signals:
        annual = voice(signal) == ANNUAL_VOICE
        block = annual_finding_block if annual else finding_block
        withdrawn, found = blocks_for(signal["id"], block)
        mine = outcomes.get(signal["id"], [])
        quiet_words = (
            annual_quiet(mine, findings, signal["id"])
            if annual
            else which_quiet(mine, held_reports, sworn, fetched)
        )
        notices = annual_notices(list(filings_by_id.values()), held_notices) if annual else ""
        head = (
            f'<h3 id="signal-{esc(signal["slug"])}">{esc(signal["name"])}, version '
            f"{signal['version']}</h3>\n"
            f'<p class="quiet">{standard_links(signal)}. '
            f'<a href="{to_root}{signal_page_path(signal)}">What it reads, how, and what it does '
            "not say</a>. "
            f"{esc(quiet_words)}"
            "</p>\n"
            f"{notices}"
        )
        earlier = ""
        for old in older_versions(signal, all_signals or [], findings):
            old_withdrawn, old_found = blocks_for(old["id"], block)
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
    sworn: str | None = None,
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
            + (
                annual_silence((outcomes or {}).get(signal["id"], []), sworn)
                if voice(signal) == ANNUAL_VOICE
                else which_silence((outcomes or {}).get(signal["id"], []), held_reports)
            )
        )
        parts.append(f"{esc(signal['name'])}, version {signal['version']}: {state}")
    n = len(signals)
    return f"<b>{n} defined</b> · " + "; ".join(parts) + "."


class Raw(str):
    """A glossary entry that carries its own links; every other entry is escaped."""


def disputes_section(person: bool, brief: bool = False) -> str:
    """How a person named here disputes a fact about themselves, on every page.

    `brief` is the landing's form: the same route in one paragraph, linking the whole of it on the
    apparatus page. Seat B's requirement is that a person who does not know whose page they are on
    still finds the route from the front door; it is not that the front door recite all of it. The
    full form stays where an adverse sentence about a person actually appears, which is that
    person's own page, and on the apparatus page a reader can open.

    BYLAWS §6 promises a subject two routes and describes them in detail: a correction where a row
    states a fact incorrectly, and a supersession where a later primary filing shows the condition
    addressed. `.github/ISSUE_TEMPLATE/correction.yml` has asked for exactly what the bylaw requires
    since the founding. Neither was named on any surface, so a person reading an adverse sentence
    about themselves had no way to reach either, and the promise was one the pages broke (the
    Council's second reading of the built answer, Seat B).

    It is a section rather than a line in the glossary, because a person disputing a fact about
    themselves should not have to find the route in a list of terms, and the answer links it.

    Every line states what the bylaw states, and the register promises no outcome: a correction
    needs a primary source, as every row here does, and the maintainer decides.
    """
    who = (
        "Read as the officeholder this page names, or as anyone whose name a filer wrote into a "
        "report's lines: there is a route, it is the same one for everybody, and it runs in the "
        "open."
        if person
        else "The same route for everyone named in this register, and for anyone whose name a "
        "filer wrote into a report's lines."
    )
    rows = [
        (
            f'<a href="{CORRECTION_FORM}">A row states a fact incorrectly</a>',
            "Wrong person, wrong filing, wrong asset, wrong date, wrong amount. Name the row, say "
            "what is wrong, and cite the primary source that shows it: a claim with no primary "
            "source cannot enter the register, which is the rule that protects every other row "
            "here too. The form asks for nothing else, and anyone may open it on a subject's "
            f'behalf (<a href="{BYLAWS_6}">BYLAWS.md §6</a>).',
        ),
        (
            "A later filing shows the condition addressed",
            "Point to the later primary-source filing. A supersession row cites it and says in one "
            "sentence what changed. The original stays, the supersession stays, and a reader sees "
            "both: the register shows a change rather than replacing the record with it "
            f'(<a href="{BYLAWS_6}">§6</a>).',
        ),
        (
            "What a correction does not do",
            "It does not delete the original, hide the condition that fired when it fired, or "
            f'alter the signal. Facts stay and change is shown (<a href="{CHARTER}">the Charter\'s '
            "fifth vow</a>). Where one moves a filer's own text, the register keeps a fingerprint "
            "of what the line said and not the text, and the builds sealed before it still carry "
            "the line, because every sealed build stays in this repository's history.",
        ),
        (
            "Nothing is honoured off the record",
            # Never "from any party": the word must not appear on an officeholder's page at all,
            # whatever sense it carries, and a test pins that (the reading of P.1, Seat A).
            "The maintainer acts on no private request from anyone, which cuts both ways and is "
            "meant to: nothing is quietly removed, and nothing is quietly added. Every change is a "
            f'row a reader can see, with its evidence and its date (<a href="{BYLAWS_6}">§6</a>).',
        ),
        (
            "What the register cannot do",
            "It cannot change what was filed. Only the filer can, by amending the report with the "
            "Clerk, and the register then reads what the Clerk serves. It does not decide whether "
            "a report was late: that is the House Committee on Ethics's, and the register sees "
            "none of its decisions. Where the Clerk withdraws a filing, the row says so with the "
            "date and keeps displaying, so a citation to it still resolves.",
        ),
        (
            f'<a href="{SECURITY_MD}">Something that should not be public at all</a>',
            "A private person's name, an address, an account number. Report it privately, by the "
            "route SECURITY.md gives, rather than on the record.",
        ),
    ]
    if brief:
        return (
            '<section id="disputes" class="disputes">\n'
            "<h2>If a fact here is wrong</h2>\n"
            f'<p>{who} <a href="{CORRECTION_FORM}">Name the row, say what is wrong, and cite '
            "the primary source that shows it</a>; anyone may open it on a subject's behalf. The "
            "maintainer acts on no private request from anyone, which cuts both ways and is meant "
            "to: nothing is quietly removed, and nothing is quietly added. "
            f'<a href="{RECORD_PAGE}#disputes">The whole route</a>, and what a correction does '
            f'and does not do. For <a href="{SECURITY_MD}">something that should not be public at '
            "all</a>, report it privately rather than on the record.</p>\n"
            "</section>"
        )
    listed = "\n".join(f"<dt>{term}</dt><dd>{body}</dd>" for term, body in rows)
    return (
        '<section id="disputes" class="disputes">\n'
        "<h2>If a fact here is wrong</h2>\n"
        f"<p>{who}</p>\n"
        f"<dl>\n{listed}\n</dl>\n"
        "</section>"
    )


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
                    "fingerprints and which rows read otherwise, never what they say. A "
                    "fingerprint proves that a copy a reader holds is or is not the file the "
                    "register read; it does not reproduce either file, and nobody who lacks a "
                    "copy can recover one from it. Both are in "
                    f'<a href="{CHANGES_DATA}">the changes, as data</a>.'
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
            "A transaction report",
            Raw(
                "The form a member files within 30 days of being notified of a purchase, sale or "
                "exchange over $1,000 in a stock, bond or other security, in their own account or "
                "a spouse's or dependent child's, and no later than 45 days after the transaction "
                f'(<a href="{USC_13105}">5 U.S.C. § 13105(l)</a>). The Clerk calls it a Periodic '
                "Transaction Report and publishes it as filed. It lists the trades and not the "
                "holdings, so the register counts reports and trades and never anyone's wealth: no "
                "page here sums an amount, averages one, or sets one beside another person's. The "
                "annual report, which does list holdings, is a different form, and this register "
                "reads its header and not its schedules."
            ),
        ),
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
    terms = f'<dl class="terms">\n{body}\n</dl>\n'
    # On a person's page the terms fold under their heading: they are the same on all of them,
    # and the drawing and the rows above are what the page is for. The record page keeps them open.
    if person:
        terms = (
            f"<details>\n<summary>The {len(rows)} terms this page uses, each in a line</summary>\n"
            f"{terms}</details>\n"
        )
    return (
        f'<section class="how" id="how-to-read">\n<h2>How to read this page</h2>\n{terms}</section>'
    )


# ---- the officeholder page --------------------------------------------------------------


HELD_CLAUSES = {
    "no_filing_id": "whose {docs} {carry} no Filing ID line (scanned paper, or a form that "
    "prints none) and cannot confirm the filer",
    "status": "whose {docs} {print} a filer status other than Member",
    # The roster records a swearing-in for each member, and for one sworn in mid-term it is not
    # the day the Congress convened. Saying "for the Congress" read, on the page of a member
    # sworn eleven months in, as a date the row is plainly after (the Council's fifth reading
    # of S.1b, Seat F). One shape for everyone: the date is the officeholder's own, whichever
    # it is.
    "before_sworn": "dated by the index before the swearing-in the roster records for this "
    "officeholder",
    "not_captured": "whose {docs} the register has not fetched",
    "other": "whose {docs} {print} another seat or another Filing ID, or were set aside for "
    "another recorded reason",
    "left_open": "dated on or before {until}, the last roster read the register built from "
    "that listed them: the name join attributes no row to a member the roster does not list, "
    "and the maintainer's recorded decision can attribute {it}",
    "closed_open": "first read by the register when or after it closed the year, and dated "
    "within the Congress's terms, whose {docs} the register has not read: the maintainer's "
    "recorded decision can attribute {it}",
    # The row carries the name; the person did not. "Under another given name" on a named
    # person's page read as that person having filed under one (the Council's fifth reading of
    # S.1b, Seat F).
    "left_other_name": "that {carry} a given name other than this officeholder's, whose "
    "{docs} the register has not read: the name join attributes no row to a member the roster "
    "does not list",
    "left_closed": "dated after {until}, the last roster read the register built from that "
    "listed them, which no decision attributes to them: the register cannot show them in office "
    "then",
    "after_term": "that the maintainer's recorded decision names them for, which the register "
    "does not attribute: the index dates it after the last day the register can show them in "
    "office",
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
        # The date, and nothing about what it obliged: an on-time Member's quiet page calls the
        # quiet the register's own, and this one asked what the Member may have owed, on a
        # register whose one Signal is about reports dated late (the Council's fourth reading of
        # S.1b, Seat A).
        return (
            f"The Clerk's roster records their swearing-in on {esc(sworn)}, after the Congress's "
            "terms began. Whether the Clerk's index lists nothing of theirs for "
            f"{ERA['year']} or lists a row in a form the register did not match, this is not a "
            "statement about what was filed."
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


def headers_read(filings: list[dict]) -> int:
    """Documents fetched and not read as a transaction report whose own header the register did
    read, and recorded (filing.printed): an annual report or an extension form says what it is,
    and a page that counted it as unread would say a Finding rests on a document it never read
    (the Council's second reading of the annual Signal, Seat A)."""
    return sum(
        1
        for f in filings
        if f.get("printed")
        and f.get("source", {}).get("content_hash")
        and f.get("extraction_confidence") != "structured"
    )


def documents_read(filings: list[dict]) -> tuple[int, int]:
    """How many of these filings' documents the register read, and how many it fetched but did
    not read: ones whose extracted text carries no Filing ID line, or a form whose schedules
    the register does not yet read. A read document carries a content hash and a structured
    extraction; an unread one carries the hash alone.
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
        header = headers_read(filings)
        scanned -= header
        if read == n:
            documents = (
                "<b>read</b> · the register read each document, recorded its hash, and confirmed "
                "the seat and filing ID printed inside it against the roster; the transactions "
                "the reports list are below, as filed."
            )
        elif read or scanned or header:
            parts = [f"<b>partly read</b> · {read} of {n} documents read and hashed"]
            if header:
                its, prints = plural(header, "its", "their"), plural(header, "prints", "print")
                parts.append(
                    f"{header} fetched and hashed, and read for what {its} own header {prints} "
                    f"{plural(header, 'it is', 'they are')}"
                )
            if scanned:
                parts.append(
                    f"{scanned} fetched and hashed, not read: no Filing ID line in the text "
                    "the register extracted, or a form it does not yet read"
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
    "asset": "the asset as named",
    "notes": "the notes the register wrote from the report's lines",
    "action": "the type of transaction",
    "amount_range": "the category of value",
    "asset_code": "the Clerk's asset type code",
    "asset_normalized": "the ticker the register read from the asset",
    "filing_status": "the filer's own mark on the line",
    "owner": "the owner as marked",
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
                f'Clerk serves it; <a href="{CLERK_SITE}">search the Clerk\'s disclosure site</a> '
                f"by the filer's name and {ERA['year']}, and this report's link ends "
                f"{esc(doc_id)}.pdf"
            )
            words = "the copy of that index the register kept, a ZIP archive"
        elif c["change"] == "listed again":
            what = f"Listed again in the Clerk's index read {when(c)}"
            words = "the copy of that index the register kept, a ZIP archive"
        elif c["change"] == "read otherwise" and c["was"] == c["now"]:
            # The source states again what the register published. Written as a disagreement
            # awaiting the maintainer, it read as a dispute over a value the two agree on (the
            # Council's fourth reading of S.1b, Seats A, B and F).
            what = (
                f"The Clerk's index read {when(c)} again gives {field} as the register published it"
            )
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
                f"{earlier_builds(c, history)} carry the line as filed, and every sealed build "
                f"stays in "
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


def printed_words(filing: dict) -> str:
    """What a document's own header prints it is, in its words, where the register read it: the
    index's one-letter code is the Clerk's and is interpreted nowhere, and the header is how a
    reader learns what a row is without opening it."""
    p = filing.get("printed") or {}
    said = [p.get("filing_type") or ""]
    if p.get("extension_length_days") or p.get("new_due_date"):
        # The Committee's extension form prints no Filing Type line; it is named by the fields
        # it prints, never by the index's code.
        said = [
            "an extension"
            + (f" of {p['extension_length_days']:,} days" if p.get("extension_length_days") else "")
            + (f" to {p['new_due_date']}" if p.get("new_due_date") else "")
            + (f", for the {p['report_type_due']}" if p.get("report_type_due") else "")
        ]
    if p.get("filing_year"):
        said.append(f"filing year {p['filing_year']}")
    said = [w for w in said if w]
    if not said:
        return ""
    return f'<span class="printed">Its header: {esc(", ".join(said))}.</span> '


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
            f"<td>{printed_words(f)}"
            f'<a href="{esc(f["source"]["url"])}">Open the Clerk\'s copy</a>'
            + change_notes(changes.get(f["id"], []), holder_id)
            + "</td>"
            f'<td class="idx">{esc(f["source"]["retrieved_at"][:10])}</td>'
            f'<td class="code">{how_attributed(f, changes)}</td>'
            "</tr>"
        )
    n = len(rows)

    def with_kind(*kinds: str) -> int:
        # A read that gives back the value the row carries is not one that shows the row
        # otherwise, and the caption counts what it says (the Council's fourth reading, Seat A).
        return sum(
            1
            for f in filings
            if any(
                c["change"] in kinds
                and not (c["change"] == "read otherwise" and c["was"] == c["now"])
                for c in changes.get(f["id"], [])
            )
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
            " Where the register read a document's own header, the row gives what the header "
            "prints it is, in its words; a filing year is the calendar year the report covers."
            if any(f.get("printed") for f in filings)
            else ""
        )
        + (
            f" A later read of the Clerk's index showed {reads} of them otherwise; each note "
            "says what and when, whether a later read gave the published value back, and what "
            "the maintainer decided, and links the copy of the index the register kept."
            if reads
            else ""
        )
        + (
            f" For {files} of them a later read found the Clerk serving a different file; each "
            "note says whether its rows read as the ones the register published or otherwise, "
            "and in which facts, and the register keeps neither file."
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


# A report of more rows than this folds behind its own summary; the year figure above is the
# page's overview of them all, and a report a Finding rests on stays open whatever its length.
FOLD_AT = 5


def dates_disagree(tx: dict, report: dict) -> str:
    """A note beside a row whose own dates cannot all be right, as the report prints them: a
    notice dated before the trade, or a trade dated after the report that lists it. The register
    annotates the filed row; it does not say which date is wrong, or why."""
    traded, notified, filed = (
        tx.get("transaction_date"),
        tx.get("notified_date"),
        report.get("filed_at"),
    )
    said = []
    if traded and notified and notified < traded:
        said.append("the notice is dated before the trade")
    if traded and filed and traded > filed:
        said.append("the trade is dated after the report that lists it")
    if not said:
        return ""
    return (
        f'<span class="note clash">As printed, {" and ".join(said)}: these dates cannot all be '
        "right, and the report does not say which is wrong.</span>"
    )


def transactions_section(
    filings: list[dict],
    transactions: list[dict],
    held_reports: int = 0,
    changes: dict[str, list[dict]] | None = None,
    fired_reports: set[str] | None = None,
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
        '<details class="howrow">\n<summary>How to read a row</summary>\n'
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
        "register interprets nothing here.</p>\n</details>\n"
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
            f'<p class="quiet">The {plural(n, "report", "reports")} filed {dates}: the register '
            f"has not fetched {plural(n, 'its document', 'their documents')}, so "
            f"{plural(n, 'its', 'their')} "
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
            f'<td class="idx">{esc(t["transaction_date"])}{dates_disagree(t, f)}</td>'
            f'<td class="idx">{esc(t["notified_date"])}</td>'
            f"<td>{type_cell(t)}</td>"
            f"<td>{esc(OWNER_WORDS.get(t['owner'], t['owner']))}</td>"
            f"<td>{asset_cell(t)}{noted(t)}</td>"
            f'<td class="amt">{esc(amount_text(t))}</td>'
            "</tr>"
            for t in rows
        )
        table = (
            f"<table>\n<caption>{n} {plural(n, 'row', 'rows')} of the report, oldest transaction "
            "date first; the report itself may list them in another order.</caption>\n"
            "<thead><tr><th>Transaction date</th><th>Notified</th><th>Type</th>"
            "<th>Owner, as marked</th><th>Asset, as named</th><th>Amount</th></tr></thead>\n"
            f"<tbody>\n{body}\n</tbody>\n</table>\n"
        )
        # A long report folds, so a page of a thousand rows can be walked; every row stays in the
        # page, and a report a Finding rests on stays open, so nothing a reader needs is behind
        # a click they must know to make (docs/design/pages-a-reader-can-use.md §2.4).
        if n > FOLD_AT:
            rests = f["id"] in (fired_reports or set())
            table = (
                f"<details{' open' if rests else ''}>\n<summary>The {n:,} rows of this report, as "
                f"filed{'; a Finding rests on this report' if rests else ''}</summary>\n"
                f"{table}</details>\n"
            )
        parts.append(table)
    return (
        '<section id="transactions">\n<h2>Transactions reported</h2>\n'
        + "".join(parts)
        + "</section>"
    )


# ---- the reports as squares: one visual language, from the chamber to the person -----------

SQUARE, SQUARE_GAP, SQUARE_COLUMNS = 10, 2, 30
# Ben-Day dots: the halftone of the old four-colour comic press, inked from the page's own token.
# Defined once in the squares' drawing; every other drawing on the page refers to it by id.
BENDAY = (
    '<defs><pattern id="benday" width="2.6" height="2.6" patternUnits="userSpaceOnUse">'
    '<circle cx="1.3" cy="1.3" r=".85" fill="var(--ink-2)"/></pattern>'
    # The same screen at 50% coverage in the page's own ink, for the one square whose
    # halftone carries meaning rather than depth. At r=.85 in ink-2 the square that holds
    # the reassuring answer measured 1.64:1 against the paper in light mode and 1.89:1 in
    # dark, against 15.69:1 for the square that holds the adverse one, so the grid's whole
    # visual weight ran one way; WCAG 2.1 SC 1.4.11 asks 3:1 of a graphic a reader needs,
    # and these squares are also links. A 50% screen in --ink measures 3.27:1 and 4.48:1
    # (the second reading of the built answer, Seat E). The comic panels and the notice
    # clock keep the lighter screen, where the halftone is depth and carries nothing.
    '<pattern id="benday50" width="2.6" height="2.6" patternUnits="userSpaceOnUse">'
    '<circle cx="1.3" cy="1.3" r="1.04" fill="var(--ink)"/></pattern></defs>'
)
SQUARE_WORDS = {
    "after": (
        "dated by the Clerk's index after the STOCK Act deadline for at least one trade compared"
    ),
    "checked": "compared against the deadline, and none dated after it",
    # Never "no trade the rule reaches": of 1,156 rows the register set aside on the 2025
    # record, one was out of the rule's reach by amount and the rest are the register's own
    # limits (the Council's second reading of the built answer, Seat B).
    "unchecked": (
        "no row on it compared: the register did not read it, or it compared none of its "
        "rows, which is a limit of the register except where the rule itself does not "
        "reach a row"
    ),
}


def report_states(outcomes: list[dict], findings: list[dict], signal_id: str) -> list[tuple]:
    """Each report the Signal read or tried to read, in the order the Clerk's index dates them,
    as (filed_at, filing_id, state): `after` where a current Finding rests on it, `checked` where
    a row was evaluated and none is after, `unchecked` otherwise. The same numbers the answer
    states, one report at a time."""
    fired = {f["producing_filings"][0] for f in fired_now(findings, signal_id)}
    out = []
    for o in outcomes:
        state = "after" if o["filing_id"] in fired else "checked" if o["evaluated"] else "unchecked"
        out.append((o.get("filed_at") or "", o["filing_id"], state))
    return sorted(out)


def squares(
    states: list[tuple],
    label: str,
    link: bool = False,
    columns: int = SQUARE_COLUMNS,
    size: int = SQUARE,
):
    """One square per report, left to right in the order filed: filled dark, filled light, or
    an outline. Inline SVG, inked from the page's tokens; on a person's page each square links
    to its report. Its words are in `label`, read by a screen reader and a translation alike."""
    step = size + SQUARE_GAP + (1 if size > SQUARE else 0)
    cols = min(columns, max(len(states), 1))
    rows = (len(states) + cols - 1) // cols
    parts = []
    for i, (filed, filing_id, state) in enumerate(states):
        x, y = (i % cols) * step + 1, (i // cols) * step + 1
        cell = f'<rect class="sq s-{state}" x="{x}" y="{y}" width="{size}" height="{size}"/>'
        if link:
            doc = filing_id.rsplit(":", 1)[1]
            target = f"finding-{doc}" if state == "after" else f"report-{doc}"
            if state == "after" or state == "checked":
                cell = f'<a href="#{esc(target)}"><title>{esc(filed)}</title>{cell}</a>'
            else:
                cell = f"<g><title>{esc(filed)}</title>{cell}</g>"
        parts.append(cell)
    width, height = cols * step + 1, rows * step + 1
    return (
        f'<svg class="squares" viewBox="0 0 {width} {height}" width="{width}" height="{height}" '
        f'role="img" aria-label="{esc(label)}">{BENDAY}' + "".join(parts) + "</svg>"
    )


SHORT_WORDS = {
    "after": "dated after the deadline",
    "checked": "compared, none after",
    "unchecked": "no row compared",
}


def square_key(counts: dict[str, int] | None = None) -> str:
    """The key beside the squares: each state drawn as it is drawn there, with its words, and on
    the landing its count. Every state is named, even one with no report, so every key has the
    same three lines on every page."""
    lines = []
    for state in ("after", "checked", "unchecked"):
        swatch = (
            '<svg class="key" viewBox="0 0 12 12" aria-hidden="true" focusable="false">'
            f'<rect class="sq s-{state}" x="1" y="1" width="10" height="10"/></svg>'
        )
        words = (
            f"<b>{counts.get(state, 0):,}</b> {esc(SQUARE_WORDS[state])}"
            if counts is not None
            else esc(SHORT_WORDS[state])
        )
        lines.append(f"<li>{swatch} {words}</li>")
    return (
        f'<ul class="squarekey{"" if counts is not None else " short"}">' + "".join(lines) + "</ul>"
    )


def square_label(states: list[tuple], noun: tuple[str, str]) -> str:
    counts = {k: sum(1 for s in states if s[2] == k) for k in SQUARE_WORDS}
    n = len(states)
    return (
        f"{n:,} {plural(n, *noun)}, one square each in the order filed: "
        + "; ".join(f"{counts[k]:,} {SQUARE_WORDS[k]}" for k in SQUARE_WORDS)
        + "."
    )


# What each Signal checks, in the words the answer at the top of a page uses. A Signal with no
# entry here is named in the answer by its checklist line, never summarised in words written
# for another Signal.
# What each Signal compares, in the words the answer at the top of a page uses, keyed by slug
# AND version: a version's criteria and the words that describe them move together, or a v2
# publishes v1's account of the rule, which is INVARIANTS §11's silent redefinition moved into the
# sentence a reader actually meets (the second reading of the built answer, Seats C and G).
ANSWER_WORDS = {
    ("stock-act-ptr-after-deadline", 1): {
        "reports": ("transaction report", "transaction reports"),
        "against": f'the STOCK Act deadline (<a href="{USC_13105}">5 U.S.C. § 13105(l)</a>)',
        "rule": (
            "The rule: a member reports each trade over $1,000 within 30 days of being notified "
            "of it, and no later than 45 days after it. The law requires trades reported; it does "
            "not prohibit them."
        ),
    },
}
# The two sentences after every result, split where the Council's two findings actually point.
# Seat D: the frame must sit inside the result's own paragraph, so no crop of the answer carries
# the result without it. Seat E: that paragraph ran eighty to a hundred and fifty words and on no
# page of four hundred and thirty-nine did it fit a phone's first screen. Both hold. The sentence
# that must never travel alone is the shortest one, so the frame stays in the paragraph and the
# thirty words about who decides go to the next, adjacent and inseparable under the same seal.
NOT_A_RULING = (
    "This is not a ruling by anyone: what the deadline means for a filer is for the House "
    "Committee on Ethics to decide, and the register sees none of its decisions."
)
EITHER_WAY = NOT_A_RULING + " " + FRAME
# What every figure on the landing would otherwise say in its own caption, said once before the
# first of them. Each caption keeps what is true of it alone (its unit, its scale, what it cannot
# show); these are true of all four, and four tellings of them were a quarter of the captions.
HOW_TO_READ = (
    "How to read the figures from here: each is drawn from this build's sealed rows, names no "
    "one, and orders nothing by anything about a person; and each says whether it counts trades "
    "or reports, because one report can list hundreds of trades."
)


def finding_facts(findings: list[dict], signal_id: str) -> dict:
    """What the current Findings' own rows say that decides them, for the answer: the least and
    most days after the deadline; how many Findings rest only on deadlines that fell on a weekend
    or holiday, with the report dated by the next business day; and how many print a notice date
    after the 45-day limit had passed (the Council's reading of P.1, Seats A and B)."""
    current = fired_now(findings, signal_id)
    days = [r["days_after"] for f in current for r in f["evidence"]["rows"]]
    weekend = notice = 0
    for f in current:
        rows, filed = f["evidence"]["rows"], f["evidence"]["filed_at"]
        if rows and all(
            r["deadline_falls_on"] and filed <= (r["first_business_day_after"] or "") for r in rows
        ):
            weekend += 1
        if any(r["notified_after_limit"] for r in rows):
            notice += 1
    return {
        "days": (min(days, default=0), max(days, default=0)),
        "weekend": weekend,
        "notice": notice,
        "trades": len(days),
    }


# Why the register compared no row on a report it read, in its own words rather than the rule's.
# The answer said "no trade the rule reaches" of every such report, and on seventeen pages not one
# skipped row was skipped on a ground about the rule's reach: they were dated before the swearing-in
# the roster records, or the report marks them amended, or the transaction is dated after the report
# itself. On the whole 2025 record, of 1,156 rows the register set aside, exactly one was out of the
# rule's reach by amount. The Signal's own criteria say a returning Member's earlier trades "were
# under the same rule" and that the register has not read the instructions that would settle where
# government securities belong. So the register says what it did not do, never what the law does not
# cover: a sentence that flatters a person falsely is the same defect as one that condemns them
# falsely (the Council's second reading of the built answer, Seat B).
UNCHECKED_WORDS = {
    "dated before this Congress's swearing-in": (
        "the register did not compare, being dated before the swearing-in the roster records, "
        "which does not say whether this officeholder served before it"
    ),
    "marked Amended": "the report marks as amended",
    "marked Deleted": "the report marks as deleted",
    "transaction dated after the report": "dated after the report that lists them",
    "coded as a stock, named as an ETF": "whose printed name and printed code disagree",
    "$1,000 or less": "at or under the $1,000 the rule sets",
}
AN_ASSET_KIND = "a kind of asset the register does not evaluate"


def unchecked_reason(reason: str) -> str:
    """One recorded reason a row was not evaluated, in the register's own voice. An asset code the
    Signal does not evaluate is the register's own limit and is grouped as one; a reason this
    version has no words for is given as the run record writes it, and attributed to the register,
    never to the rule: saying the rule does not reach a row it may well reach is the falsehood that
    flatters."""
    if reason.startswith("asset coded"):
        return AN_ASSET_KIND
    return UNCHECKED_WORDS.get(reason, f"the register did not evaluate, recorded as {reason}")


def unchecked_words(outcomes: list[dict]) -> str:
    """Why rows on the reports the register read were not compared, grouped as the reader needs and
    in the register's own voice, commonest first."""
    counts: dict[str, int] = {}
    for o in outcomes:
        for reason, n in (o.get("not_evaluated") or {}).items():
            key = unchecked_reason(reason)
            counts[key] = counts.get(key, 0) + n
    said = []
    for key, n in sorted(counts.items(), key=lambda i: (-i[1], i[0])):
        if key.startswith("the register did not compare"):
            said.append(f"{n:,} {key.removeprefix('the register did not compare, being ')}")
        else:
            said.append(f"{n:,} {key}")
    return "; ".join(said)


def answer_counts(
    outcomes: list[dict], findings: list[dict], signal_id: str
) -> tuple[int, int, int, int]:
    """The four numbers the answer states, from the Signal's own run record and the Findings
    the page shows: reports attributed, reports read, reports checked (a row evaluated on
    them), and reports a current Finding rests on. A report a Finding rests on counts as
    checked, so the last number is never more than the one before it."""
    fired = {f["producing_filings"][0] for f in fired_now(findings, signal_id)}
    read = sum(1 for o in outcomes if o["state"] == "evaluated")
    checked = {o["filing_id"] for o in outcomes if o["evaluated"]} | fired
    attributed = {o["filing_id"] for o in outcomes} | fired
    return len(attributed), read, len(checked), len(fired)


def answer_section(
    signals: list[dict],
    findings: list[dict],
    outcomes: dict[str, list[dict]],
    meta: dict,
    held_reports: int = 0,
    sworn: str | None = None,
    filings: list[dict] | None = None,
    held_all: int = 0,
    transactions: list[dict] | None = None,
) -> str:
    """What the register read and what it found, first, in sentences whose shape is the same
    for everyone: the register's own coverage before any result, the result in the same words
    whether a Signal fired or not, and the same sentence after it on every page. The frame stays
    above it, in the header (INVARIANTS §7). docs/design/pages-a-reader-can-use.md §2.1."""
    paragraphs, rules = [], []
    drawn = {"ptr": [], "annual": []}
    # The transaction reports first and the annual report after, the order the year figure
    # draws them and the order the landing tells them.
    signals = sorted(signals, key=lambda s: voice(s) != PTR_VOICE)
    for signal in signals:
        if voice(signal) == ANNUAL_VOICE:
            drawn["annual"] = outcomes.get(signal["id"], [])
            for p in annual_answer(
                signal,
                outcomes.get(signal["id"], []),
                findings,
                filings or [],
                held_all,
                sworn,
                meta,
            ):
                (rules if p.startswith('<p class="rule">') else paragraphs).append(p)
            continue
        if voice(signal) == PTR_VOICE:
            drawn["ptr"] = outcomes.get(signal["id"], [])
        words = ANSWER_WORDS.get((signal["slug"], signal["version"]))
        if words is None:
            # A Signal the answer has no words for used to be named with its firing count alone:
            # no coverage number, no standard, and a shape that differed according to whether it
            # fired, which is a verdict by placement (COUNCIL §5 mode 6). A page that cannot
            # state a Signal's coverage and its standard does not state its firing count either
            # (the second reading of the built answer, Seats C and G).
            raise SystemExit(
                "refusing to render: the answer has no words for signal "
                f"{signal['slug']} version {signal['version']}, so it could state its firing "
                "count but not its coverage or its standard. Add an entry to ANSWER_WORDS in "
                "src/surfaces/render.py keyed by (slug, version), with `reports`, `against` and "
                "`rule`; a version's own words move with its criteria (INVARIANTS §11)."
            )
        one, many = words["reports"]
        n, read, checked, fired = answer_counts(
            outcomes.get(signal["id"], []), findings, signal["id"]
        )
        year = ERA["year"]
        if not n:
            # The limit before the count, because on a phone the sentence that prevents the
            # wrong conclusion was the one below the fold; and the register attributes, where
            # saying the index does put the Clerk's name behind the register's own undecided
            # matching (the Council's second reading of the built answer, Seats B and E). The
            # last sentence is what makes a quiet page honest and it does not come out.
            text = (
                "The register found nothing to compare here, which is a fact about its own "
                f"matching and not about what was filed: it attributes no {one} in the Clerk's "
                f"{year} index to this officeholder, so it compared none against "
                f"{words['against']}. It says nothing about whether this officeholder made any "
                "trade the rule requires reported."
            )
            if sworn and ERA.get("began") and sworn > ERA["began"]:
                text += (
                    f" The Clerk's roster records their swearing-in on {esc(sworn)}, after the "
                    "Congress's terms began."
                )
        else:
            text = (
                f"The register read {read:,} of {n:,} {plural(n, one, many)} it attributes "
                f"to this officeholder from the Clerk's {year} index and compared {checked:,} "
                f"against "
                f"{words['against']}. "
            )
            # min() clamped a discrepancy where an assertion belongs. A Finding whose
            # report this build's run record marks unread made the answer say, in one paragraph,
            # that the register read none of the reports, compared one, found that one after the
            # deadline, and could not read it (the Council's second reading, Seat C).
            if checked > read or read > n:
                raise SystemExit(
                    f"refusing to render: the answer would say the register read {read} of {n} "
                    f"reports and compared {checked}, which cannot all be true. A Finding rests "
                    "on a report this build's run record did not read, or on one the record does "
                    "not hold. Re-run the Signal (src/signals/run.py) so the record covers every "
                    "report a current Finding names, or supersede the Finding "
                    "(src/signals/run.py --correct), citing the evidence."
                )
            unread, empty = n - read, read - checked
            if not checked:
                why = unchecked_words(outcomes.get(signal["id"], []))
                # A report the register read that lists no transaction row at all leaves both
                # clauses empty, and the sentence then read "It compared no row on any of them:
                # That is a fact about what the register could read": a colon before a capital,
                # with nothing between. True of no report in the 2025 record, and reachable by an
                # empty filing, which is why it is said rather than left to the first one.
                none_read = not unread and not why
                text += (
                    "It compared no row on any of them: "
                    + (
                        f"{unread:,} {plural(unread, 'is', 'are')} in a form it does not read"
                        + (", and of the rows on the rest, " if why else ". ")
                        if unread
                        else "it read no transaction row from them. "
                        if none_read
                        else ("of the rows on them, " if why else "")
                    )
                    + (f"{why}. " if why else "")
                    + "That is a fact about what the register could read, not about what was "
                    "filed."
                )
            else:
                if fired:
                    facts = finding_facts(findings, signal["id"])
                    low, high = facts["days"]
                    span = (
                        f"{low:,} {plural(low, 'day', 'days')}"
                        if low == high
                        else f"{low:,} to {high:,} days"
                    )
                    text += (
                        f"The Clerk's index dates {fired:,} "
                        f"{plural(fired, 'report', 'reports')} it compared after the deadline: "
                        f"{facts['trades']:,} {plural(facts['trades'], 'trade', 'trades')} on "
                        f"{plural(fired, 'it', 'them')}, {span} past "
                        f"{plural(fired, 'its own deadline', 'their own deadlines')}."
                    )
                    for count, clause in (
                        (
                            facts["weekend"],
                            "the deadline fell on a weekend or holiday and the report is dated by "
                            "the next business day; the 2025 form says such a deadline does not "
                            "move",
                        ),
                        (
                            facts["notice"],
                            "the notice date printed is more than 45 days after the trade, so the "
                            "45-day limit had passed before that notice",
                        ),
                    ):
                        if count:
                            who = (
                                "that report"
                                if fired == 1
                                else f"all {fired:,}"
                                if count == fired
                                else f"{count:,} of the {fired:,}"
                            )
                            text += f" For {who}, {clause}."
                else:
                    text += (
                        "The Clerk's index dates none of the reports it compared after the "
                        "deadline."
                    )
                missing = []
                if unread:
                    missing.append(f"{unread:,} in a form it does not read")
                if empty:
                    missing.append(f"{empty:,} on which it compared no row")
                if missing:
                    text += f" No row compared: {'; '.join(missing)}."
            gone = len(withdrawn_now(findings, signal["id"]))
            if gone:
                text += (
                    f" {gone:,} {plural(gone, 'Finding', 'Findings')} once published here "
                    f"{plural(gone, 'was', 'were')} withdrawn by the maintainer's correction, "
                    "said below with the signal."
                )
            if held_reports:
                text += (
                    f" {held_reports:,} more {plural(held_reports, one, many)} at this seat under "
                    f"this surname {plural(held_reports, 'is', 'are')} set aside, not attributed "
                    "to this officeholder, and no row on them compared."
                )
        if not n and held_reports:
            text += (
                f" {held_reports:,} {plural(held_reports, one, many)} at this seat under this "
                f"surname {plural(held_reports, 'is', 'are')} set aside, not attributed to this "
                "officeholder, and no row on them compared."
            )
        # The result and its coverage are one short paragraph and the sentence that frames
        # them is the next, adjacent and inseparable in the source and under the seal (Seat D).
        # They were one paragraph of eighty to a hundred and fifty words, of which forty were a
        # sentence the reader had already met at word four, and on no page of four hundred and
        # thirty-nine did it fit a phone's first screen: a reader on a phone saw the coverage
        # clause cut mid-sentence and nothing else (the second reading, Seat E).
        paragraphs.append(f'<p>{text} <span class="either">{esc(FRAME)}</span></p>')
        if words.get("rule"):
            rules.append(f'<p class="rule">{words["rule"]}</p>')
    # Every report on one line of time, in place of a strip of squares per Signal and a figure
    # per annual report: the reader sees the year the sentences describe (Jared, 2026-09-27:
    # illustrate the record, do not describe it). Who decides is said once, after the drawing.
    # The same links on every page, in the same words, whatever the signal found, right under the
    # sentences they lead from, so the route to dispute a fact comes before the drawing.
    jumps = " · ".join(
        [
            '<a href="#signals">Report by report</a>',
            '<a href="#transactions">The record</a>',
            '<a href="#requires">The oath and the rules</a>',
            '<a href="#disputes">If a fact here is wrong</a>',
        ]
    )
    # Who decides, once, under the sentences it is about and before the links and the drawing
    # (the Council's reading of the year figure, Seat B).
    if signals:
        paragraphs.append(f'<p class="either">{esc(NOT_A_RULING)}</p>')
    paragraphs.append(f'<nav class="jump" aria-label="On this page">{jumps}</nav>')
    # The practical thing, in the reader's path: beside the links and before the drawing, so a
    # long key never pushes it down the page (NEXT.md P.1 §2.5).
    paragraphs.append(
        '<p class="check">Check it yourself: every report on this page links to the Clerk\'s '
        "own copy, "
        "and every Finding prints the command that regenerates it. This page is rendered from "
        f'build <code translate="no">{esc(build_label(meta))}</code>; <code translate="no">python '
        "tools/verify.py</code> checks "
        'that its rows are unchanged since it was sealed (<a href="#verify">more</a>).</p>'
    )
    if signals:
        voices = {voice(s) for s in signals}
        paragraphs.append(
            year_figure(
                filings or [],
                transactions or [],
                drawn["ptr"],
                drawn["annual"],
                findings,
                meta,
                (PTR_VOICE in voices, ANNUAL_VOICE in voices),
                sworn,
            )
        )
        paragraphs += rules
    if not signals:
        paragraphs.append(
            "<p>No signal is defined in this build, so none can fire, for anyone.</p>"
        )
    return (
        '<section id="answer" class="answer">\n<h2>What the register found</h2>\n'
        + "\n".join(paragraphs)
        + "\n</section>"
    )


# ---- a person's year, drawn: the record itself, on one line of time --------------------------

YEAR_W, YEAR_L, YEAR_R = 520, 8, 8
YEAR_ROW, YEAR_SQ = 13, 9
MONTH_LETTERS = "JFMAMJJASOND"


def month_after(day: date) -> date:
    return date(day.year + day.month // 12, day.month % 12 + 1, 1)


def year_span(meta: dict | None) -> tuple[date, date]:
    """The same line of time on every page of a build: from the first day of the filing year to the
    end of the month that holds the build, or the latest date any annual report in the build could
    reach, whichever is later. One scale for every page, so the same days are the same length on
    every page (the Council's reading of the year figure, Seat A)."""
    start = date(ERA["year"], 1, 1)
    built = ((meta or {}).get("built_at") or "")[:10]
    last = [date.fromisoformat(built)] if built else [date(ERA["year"], 12, 31)]
    if ERA.get("drawn_to"):
        last.append(date.fromisoformat(ERA["drawn_to"]))
    return start, month_after(max(last)) - timedelta(days=1)


def annual_mark(outcome: dict, fired: set[str]) -> tuple[str, str]:
    """An annual report's mark on the year figure and the words for it, from the run record alone:
    the three the landing draws, and an outline where the Signal did not evaluate it for a reason
    other than the time an extension may cover, which says that reason (the Council's reading of
    the year figure, Seats A and E: the day after the latest date had been drawn as in between)."""
    if outcome["filing_id"] in fired:
        return "after", "after the latest date an extension could reach"
    if outcome.get("evaluated"):
        return "compared", "on or before its original due date"
    reasons = list((outcome.get("not_evaluated") or {}).keys())
    if reasons and reasons[0] != ANNUAL_WITHIN:
        return "void", annual_reason(reasons[0])
    return "read", "within the time an extension may cover, which the register does not decide"


def year_figure(
    filings: list[dict],
    transactions: list[dict],
    ptr_outcomes: list[dict],
    annual_outcomes: list[dict],
    findings: list[dict],
    meta: dict | None = None,
    lanes: tuple[bool, bool] = (True, True),
    sworn: str | None = None,
) -> str:
    """One officeholder's record for the filing year, as the Clerk's index lists it and the
    reports print it, drawn on one line of time in the landing's own grammar: a trade is a dot,
    the date the index gives a report is its square, and where that date falls after a deadline
    the days between are a solid bar. Each transaction report is a row; the annual report sits
    beside its original due date and the latest date an extension could reach; a document whose
    header the register could not read is an outline where the index dates it. What the register
    did not read is drawn as an outline that says so, never left blank. Everything drawn comes
    from the sealed rows and the Signals' own run records and Findings; the figure computes no
    deadline of its own. It names no one: the page does."""
    ptr_on, annual_on = lanes
    if not ptr_on and not annual_on:
        return ""
    fired = {f["producing_filings"][0]: f for f in fired_now(findings)}
    fired_annual = {k for k, v in fired.items() if "annual" in v["signal_id"]}
    state_of = {o["filing_id"]: o for o in ptr_outcomes}
    reports = sorted(
        (f for f in filings if f.get("source_form_code") == "P"),
        key=lambda f: (f["filed_at"], f["id"]),
    )
    drawable = sorted(
        (o for o in annual_outcomes if o.get("original_due") and o.get("latest") and one_day(o)),
        key=lambda o: (o["filed_at"], o["filing_id"]),
    )
    unread = sorted(
        (
            f
            for f in filings
            if f.get("source_form_code") != "P"
            and (f.get("source") or {}).get("content_hash")
            and not f.get("printed")
        ),
        key=lambda f: (f["filed_at"], f["id"]),
    )
    start, end = year_span(meta)
    turn = date(ERA["year"] + 1, 1, 1)
    index_end = min(date.fromisoformat(ERA["index_last"]) if ERA.get("index_last") else turn, end)
    began = date.fromisoformat(sworn) if sworn else None
    span = max((end - start).days, 1)
    inner = YEAR_W - YEAR_L - YEAR_R

    def x(day: date) -> float:
        return YEAR_L + min(max((day - start).days, 0), span) / span * inner

    def f(v: float) -> str:
        return f"{v:.1f}".rstrip("0").rstrip(".")

    def words_at(left: float, right: float, top: float, height: float, lines: list[str]) -> list:
        # Words inside the outline where they fit, and before it where they do not, so no word is
        # cut at the edge of the drawing (the Council's reading of the year figure, Seat E).
        need = max(len(line) for line in lines) * 9 * 0.56 + 8
        if right - left >= need:
            anchor, at = "start", left + 4
        elif left - YEAR_L >= need:
            anchor, at = "end", left - 4
        else:
            anchor, at = "start", YEAR_L + 2
        first = top + height / 2 - (len(lines) - 1) * 5.5 + 3.2
        return [
            f'<text class="yvoidt" x="{f(at)}" y="{f(first + i * 11)}" text-anchor="{anchor}">'
            f"{esc(line)}</text>"
            for i, line in enumerate(lines)
        ]

    def outline(left: float, right: float, top: float, height: float) -> str:
        return (
            f'<rect class="yvoid" x="{f(left)}" y="{f(top)}" width="{f(max(right - left, 0))}" '
            f'height="{f(height)}"/>'
        )

    by_report: dict[str, list[dict]] = {}
    for t in transactions:
        by_report.setdefault(t["filing_id"], []).append(t)
    parts = [BENDAY]
    said: list[str] = []
    counts = {"after": 0, "checked": 0, "unchecked": 0}
    y = 4
    if ptr_on:
        parts.append(f'<text class="ylane" x="{YEAR_L}" y="{y + 7}">transaction reports</text>')
        y += 14
        top = y
        height = max(len(reports) * YEAR_ROW, 28)
        # What the register did not read of the transaction reports: everything after the last day
        # the one index it reads lists a report, outlined across the lane and said.
        if index_end < end:
            # A band along the top of the lane, not a box its full height: it says what was not
            # read without becoming the largest shape on a page whose record is the point.
            left = x(index_end + timedelta(days=1))
            parts.append(outline(left, x(end), top, 26))
            parts += words_at(
                left,
                x(end),
                top,
                26,
                [f"the Clerk's {ERA['year'] + 1} index:", "not read in this build"],
            )
        if not reports:
            # From the swearing-in where it falls inside what the index covers, else the year's
            # start, so the words never land in the part the register did not read.
            left = x(began) if began and start < began < index_end else x(start)
            right = x(index_end)
            if right - left > 12:
                parts.append(outline(left, right, top, 26))
            parts += words_at(left, right, top, 26, ["no transaction report attributed here"])
            said.append("no transaction report attributed here")
    for report in reports:
        doc = report["id"].rsplit(":", 1)[1]
        filed = date.fromisoformat(report["filed_at"])
        outcome = state_of.get(report["id"])
        state = (
            "after"
            if report["id"] in fired
            else "checked"
            if outcome and outcome.get("evaluated")
            else "unchecked"
        )
        counts[state] += 1
        mid = y + YEAR_ROW / 2
        # One dot a date, not a trade: a report can list hundreds on one day. A row the filer
        # marked Deleted is not drawn as a trade (the Council's reading, Seat E).
        days = sorted(
            {
                date.fromisoformat(t["transaction_date"])
                for t in by_report.get(report["id"], [])
                if t.get("transaction_date") and t.get("filing_status") != "Deleted"
            }
        )
        row = [f"<title>Report dated {esc(report['filed_at'])}</title>"]
        if days:
            row.append(
                f'<line class="yspan" x1="{f(x(min(days[0], filed)))}" y1="{f(mid)}" '
                f'x2="{f(x(max(days[-1], filed)))}" y2="{f(mid)}"/>'
            )
        finding = fired.get(report["id"])
        if finding and "annual" not in finding["signal_id"]:
            passed = sorted(
                {
                    date.fromisoformat(r["deadline"])
                    for r in finding.get("evidence", {}).get("rows", [])
                    if r.get("deadline") and (r.get("days_after") or 0) > 0
                }
            )
            if passed:
                row.append(
                    f'<rect class="yafter" x="{f(x(passed[0]))}" y="{f(mid - 2.5)}" '
                    f'width="{f(max(x(filed) - x(passed[0]), 1.5))}" height="5"/>'
                )
                row += [
                    f'<line class="ydead" x1="{f(x(d))}" y1="{f(mid - 5)}" x2="{f(x(d))}" '
                    f'y2="{f(mid + 5)}"/>'
                    for d in passed
                ]
        for day in days:
            if day < start:
                # A trade the report dates before the year begins, at the line's edge, pointing
                # out of it: drawn as printed, never moved inside the year.
                row.append(
                    f'<path class="yearly" d="M{f(YEAR_L + 4)} {f(mid - 3)} L{f(YEAR_L)} {f(mid)} '
                    f'L{f(YEAR_L + 4)} {f(mid + 3)}"/>'
                )
            else:
                row.append(f'<circle class="ytrade" cx="{f(x(day))}" cy="{f(mid)}" r="2.2"/>')
        target = f"finding-{doc}" if state == "after" else f"report-{doc}"
        square = (
            f'<rect class="sq s-{state}" x="{f(x(filed) - YEAR_SQ / 2)}" '
            f'y="{f(mid - YEAR_SQ / 2)}" width="{YEAR_SQ}" height="{YEAR_SQ}"/>'
        )
        if state == "unchecked" and not by_report.get(report["id"]):
            row.append(square)
        else:
            row.append(f'<a href="#{esc(target)}">{square}</a>')
        parts.append("<g>" + "".join(row) + "</g>")
        y += YEAR_ROW
    if ptr_on:
        y = max(y, top + 28)
    if reports:
        n = len(reports)
        said.append(
            f"{n} transaction {plural(n, 'report', 'reports')}: {counts['after']} dated after the "
            f"deadline, {counts['checked']} compared with none after, "
            f"{counts['unchecked']} with no row compared"
        )
    if annual_on:
        y += 8
        parts.append(f'<text class="ylane" x="{YEAR_L}" y="{y + 7}">annual report</text>')
        y += 22
        mid = y + 6
        for o in drawable:
            filed = date.fromisoformat(o["filed_at"])
            due = date.fromisoformat(o["original_due"])
            latest = date.fromisoformat(o["latest"])
            state, words = annual_mark(o, fired_annual)
            # An annual Finding carries its days past the latest date as a bar, the same grammar
            # as a transaction report's, so the two Signals' Findings are drawn alike (the
            # Council's reading of the year figure, Seat D).
            if state == "after":
                parts.append(
                    f'<rect class="yafter" x="{f(x(latest))}" y="{f(mid - 2.5)}" '
                    f'width="{f(max(x(filed) - x(latest), 1.5))}" height="5"/>'
                )
            parts += [
                law_tag(x(due), y - 14, "15 May", 28),
                law_tag(x(latest), y - 14, "+90", 20),
                f'<path class="abracket" d="M{f(x(due))} {f(mid + 4)} V{f(mid - 5)} '
                f'H{f(x(latest))} V{f(mid + 4)}"/>',
                f'<circle class="amark {state}" cx="{f(x(filed))}" cy="{f(mid)}" r="4.5">'
                f"<title>Annual report dated {esc(o['filed_at'])}</title></circle>",
            ]
            said.append(
                f"the annual report: {words}"
                if state == "void"
                else f"the annual report, dated {words}"
            )
        for doc in unread:
            parts.append(
                f'<circle class="amark unread" cx="{f(x(date.fromisoformat(doc["filed_at"])))}" '
                f'cy="{f(mid)}" r="3.6"><title>A document dated {esc(doc["filed_at"])} whose '
                "header the register could not read</title></circle>"
            )
        if unread:
            n = len(unread)
            said.append(
                f"{n} {plural(n, 'document', 'documents')} attributed here whose header the "
                "register could not read, so it cannot tell whether "
                f"{plural(n, 'it is', 'any is')} an annual report"
            )
        if not drawable and not unread:
            year = ERA["year"]
            empty = (
                "its dates disagree, so no one date is drawn"
                if annual_outcomes
                else f"sworn in {sworn}, after {year}: no annual report for {year} asked"
                if began and began >= turn
                else f"sworn in {sworn}: 60 days or fewer of {year}, no annual report asked"
                if served_briefly(sworn, year)
                else "no annual report attributed here by its own header"
            )
            left, right = x(min(turn, end)), x(end)
            parts.append(outline(left, right, mid - 8, 16))
            parts += words_at(left, right, mid - 8, 16, [empty])
            said.append(empty)
        y += YEAR_ROW + 6
    axis = y + 6
    if turn <= end:
        parts.append(
            f'<line class="ybound" x1="{f(x(turn))}" y1="4" x2="{f(x(turn))}" y2="{axis}"/>'
        )
    parts.append(
        f'<line class="aaxis" x1="{YEAR_L}" y1="{axis}" x2="{YEAR_W - YEAR_R}" y2="{axis}"/>'
    )
    month = start
    while month <= end:
        parts.append(
            f'<line class="atick" x1="{f(x(month))}" y1="{axis}" x2="{f(x(month))}" '
            f'y2="{axis + (7 if month.month == 1 else 4)}"/>'
        )
        middle = x(month) + (x(month_after(month)) - x(month)) / 2
        parts.append(
            f'<text class="ymonth" x="{f(middle)}" y="{axis + 12}" text-anchor="middle">'
            f"{MONTH_LETTERS[month.month - 1]}</text>"
        )
        if month.month == 1:
            parts.append(
                f'<text class="yyear" x="{f(x(month) + 1)}" y="{axis + 23}">{month.year}</text>'
            )
        month = month_after(month)
    height = axis + 38
    # When service began, where it began after the year did: the reader sees which part of the
    # line was theirs to fill (the Council's reading of the year figure, Seats A and E).
    if began and ERA.get("began") and sworn > ERA["began"] and began <= end:
        sx = x(began)
        parts += [
            f'<path class="ysworn" d="M{f(sx)} {axis + 26} l-3.5 6 h7 z"/>',
            f'<text class="ymonth" x="{f(sx + (6 if sx < YEAR_W * 0.7 else -6))}" '
            f'y="{axis + 32}" text-anchor="{"start" if sx < YEAR_W * 0.7 else "end"}">'
            f"sworn in {esc(sworn)}</text>",
        ]
        height += 10
    parts.append(figure_stamp(meta, YEAR_L, YEAR_W - YEAR_R, height - 5))
    label = (
        f"This officeholder's {ERA['year']} record on one line of time. " + "; ".join(said) + "."
    )
    caption = (
        "The transaction reports and the annual report attributed here, and any document whose "
        "header the register could not read, on one line of time, as the reports print their dates "
        "and the Clerk's index dates the reports"
        + (
            "; a trade dated before the year is an arrow at the edge, and each square opens its "
            "report's rows below"
            if reports
            else ""
        )
        + ". Extension requests and amendments are listed below, not drawn. "
        + ("The law asks for the reports and does not prohibit the trades. " if reports else "")
        # Never "whether any trade was allowed": the Act asks for reports and prohibits none of
        # these trades, and under a person's trades the words raised a question the law does not
        # (the Council's reading of the year figure, Seats B and D).
        + "It shows dates. It does not show whether an extension was granted, or anything the "
        f"House Committee on Ethics has determined. {FRAME}"
    )
    return (
        '<figure class="year">\n<div class="yscroll">'
        f'<svg viewBox="0 0 {YEAR_W} {height}" direction="ltr" role="img" '
        f'aria-label="{esc(label)}" aria-describedby="year-cap">'
        + "".join(parts)
        + f"</svg></div>\n{year_key(ptr_on, annual_on)}"
        + f'<figcaption id="year-cap">{esc(caption)}</figcaption>\n</figure>'
    )


YEAR_KEY = (
    (
        "ptr",
        '<circle class="ytrade" cx="6" cy="6" r="2.4"/>',
        "one or more trades on a date, as the report prints it",
    ),
    (
        "ptr",
        '<rect class="sq s-after" x="2" y="2" width="8" height="8"/>',
        "a report the index dates after the STOCK Act deadline for a trade compared",
    ),
    (
        "ptr",
        '<line class="yspan" x1="0" y1="6" x2="12" y2="6"/>',
        "a report's trades to its own date: dates only",
    ),
    (
        "both",
        '<rect class="yafter" x="0" y="4" width="12" height="4"/>',
        "the days past a deadline, from the earliest the report's date passed; each tick is one "
        "deadline",
    ),
    (
        "ptr",
        '<rect class="sq s-checked" x="2" y="2" width="8" height="8"/>',
        "compared, none after",
    ),
    (
        "ptr",
        '<rect class="sq s-unchecked" x="2" y="2" width="8" height="8"/>',
        "no row on it compared",
    ),
    (
        "annual",
        '<circle class="amark after" cx="6" cy="6" r="4"/>',
        "annual report after the latest date an extension could reach",
    ),
    ("annual", '<circle class="amark compared" cx="6" cy="6" r="4"/>', "on or before 15 May"),
    (
        "annual",
        '<circle class="amark read" cx="6" cy="6" r="4"/>',
        "in between, which the register does not decide",
    ),
    (
        "annual",
        '<circle class="amark void" cx="6" cy="6" r="4"/>',
        "not evaluated, for the reason the sentence above gives",
    ),
    (
        "annual",
        '<circle class="amark unread" cx="6" cy="6" r="3.4"/>',
        "a document whose header the register could not read",
    ),
    (
        "both",
        '<rect class="yvoid" x="1" y="3" width="10" height="6"/>',
        "what the register did not read or found nothing in, said in the outline",
    ),
)


def year_key(ptr_on: bool, annual_on: bool) -> str:
    """The year figure's marks, each drawn as it is drawn there, with its words. Every mark a lane
    can draw is named, whether or not this page draws it, so every key reads the same."""
    lines = []
    for lane, mark, words in YEAR_KEY:
        if (lane == "ptr" and not ptr_on) or (lane == "annual" and not annual_on):
            continue
        lines.append(
            '<li><svg class="key" viewBox="0 0 12 12" aria-hidden="true" focusable="false">'
            f"{mark}</svg> {esc(words)}</li>"
        )
    return f'<ul class="squarekey yearkey">{"".join(lines)}</ul>\n'


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
    held_notices: list[dict] | None = None,
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
    # Every row set aside at this seat under this surname, whatever its code, for the annual
    # report's sentence where none is attributed: the index's code is not read to choose them.
    held_all = (
        sum(n for kind, n in held_here.items() if kind != "elsewhere")
        if isinstance(held_here, dict)
        else int(held_here or 0)
    )
    check_line = signal_check_line(signals, findings, outcomes, held_reports, sworn)
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
        held_notices,
    )
    head = (
        '<header class="frame">\n'
        f'<p class="frame">{esc(FRAME)}</p>\n'
        '<div class="masthead">\n<div>\n'
        '<p class="kicker">Oath · the register</p>\n'
        f'<h1 translate="no">{esc(holder["legal_name"])}</h1>\n'
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
    # The order a reader who arrives with a question meets it: the answer, what the register can
    # check, what the signal found, then the record it read, then the standards and the terms,
    # every one still whole (docs/design/pages-a-reader-can-use.md §2.2). The same order on every
    # page, whether a signal fired or not.
    fired = {f["producing_filings"][0] for f in fired_now(findings)}
    answer = answer_section(
        signals, findings, outcomes, meta, held_reports, sworn, filings, held_all, transactions
    )
    body = (
        f'{head}\n<main id="main">\n'
        f"{answer}\n"
        f"{checks_section(holder, filings, held_here, check_line, until, listings, changes)}\n"
        f"{section}\n"
        f"{filings_section(filings, held_here, changes, until, moved_away, holder['id'], sworn)}\n"
        f"{transactions_section(filings, transactions or [], held_reports, changes, fired)}\n"
        f"{REQUIRES}\n"
        f"{disputes_section(True)}\n"
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
            f'<a class="{cls}" href="{SEATS_PAGE}#state-{esc(code)}" '
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
        '<p class="quiet">Every square is the same size on purpose; the number is its House '
        "seats. Dashed: seats with no floor vote. Not sure of your district? "
        f'<a href="{HOUSE_FINDER}">The House\'s own finder</a> takes a ZIP code.</p>\n'
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


def headers_clause(header: int) -> str:
    """The documents read for what their own header prints they are, apart from the unread."""
    if not header:
        return ""
    return (
        f"; {header:,} more fetched and hashed, and read for what "
        f"{plural(header, 'its', 'their')} own header {plural(header, 'prints', 'print')} "
        f"{plural(header, 'it is', 'they are')}: an annual report, an amendment or an extension "
        "form, with its dates"
    )


def unreadable_clause(scanned: int) -> str:
    """The landing's aside for documents fetched but not read, or nothing."""
    if not scanned:
        return ""
    return (
        f"; {scanned} more fetched and hashed, not read: no Filing ID line in the text the "
        "register extracted, or a form it does not yet read"
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
    outcomes_all: dict[str, list[dict]] | None = None,
    findings: list[dict] | None = None,
) -> str:
    """Numbers about the register and the chamber as a whole: each counts rows the register
    holds or seats of the chamber, and none is sorted by anything the register computes about a
    person. A Member the roster stopped listing is named in a list, never counted in a line
    that reads as about the chamber (the Council's third reading of S.1b, Seats B and F)."""
    transactions = transactions or []
    signal_lines = ""
    for signal, summary in signal_runs or []:
        if voice(signal) == ANNUAL_VOICE:
            signal_lines += annual_record_line(
                signal, summary, (outcomes_all or {}).get(signal["id"], []), findings or []
            )
            continue
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
    header = headers_read(filings)
    scanned -= header
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
    year = year_of(run)
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
            "the maintainer merged it, when the maintainer merged a Signal's first definition, "
            "or when the maintainer published a correction, dated "
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
        "<details>\n<summary>Every count this build holds, what the register reads, and what it "
        "cannot see</summary>\n"
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
        f"checked against the seat and filing ID printed inside it{headers_clause(header)}"
        f"{unreadable_clause(scanned)}; "
        f"the links open the Clerk's copies{bar(read, matched)}</dd>\n"
        f"<dt>{len(transactions):,}</dt><dd>rows the read reports list, as filed{marked_note}, "
        "each on its officeholder's page grouped by report; no page sums the amounts, averages "
        "them, or compares them with anyone else's</dd>\n"
        f"<dt>{held:,}</dt><dd>index rows set aside for the maintainer to decide by hand, "
        f"because the register does not guess; {at_seat_total:,} of them sit at an "
        "officeholder's own seat under their surname"
        + (
            f"; {shut:,} more {plural(shut, 'is', 'are')} not attributed, because the register "
            "cannot show an officeholder of that seat in office on the date the index gives "
            f"{plural(shut, 'it', 'them')} "
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
            f'published, <a href="{SEATS_PAGE}#not-listed">listed with the seats</a>, with '
            "the reads that "
            "last listed them and first did not.</p>\n"
            if gone
            else ""
        )
        + f'<p class="quiet">{fresh}The seal fixes exactly this reading.</p>\n'
        f"{chart}</details>\n</section>"
    )


# ---- the strip: how a stock trade becomes a public record ------------------------------------
#
# The comic energy is the institution's and the process's, never a person's: no member is drawn,
# named or caricatured. The four panels teach the four marks the Findings' figures use, so a
# reader who has read the strip can read the figure (the maintainer's direction of 2026-09-27:
# immersion, curb appeal, "someone really thought about this").

PANELS = (
    (
        "A trade is made",
        "In a member's own account, or a spouse's or dependent child's. On every figure, the "
        "trade is a dot.",
        "trade",
        '<path class="ht" d="M10 72 L40 58 L60 64 L85 38 L110 48 L140 22 L150 22 L150 92 L10 92Z"/>'
        '<path class="ln" d="M10 72 L40 58 L60 64 L85 38 L110 48 L140 22"/>'
        '<circle class="ink" cx="85" cy="38" r="6"/>'
        '<path class="ln thin" d="M10 92 H150"/>',
    ),
    (
        "Notice arrives",
        "The report prints the date the member was notified of the trade. It is the filer's own "
        "entry, and it can move the deadline by at most 15 days. Wherever a figure draws it, the "
        "notice is a diamond.",
        "notice",
        '<rect class="ht" x="36" y="30" width="100" height="58" rx="3"/>'
        '<rect class="paper ln" x="28" y="22" width="100" height="58" rx="3"/>'
        '<path class="ln" d="M28 24 L78 56 L128 24"/>'
        '<path class="paper ln" d="M78 45 L89 56 L78 67 L67 56Z"/>',
    ),
    (
        "The clock runs",
        "The report is due 30 days after the notice or 45 days after the trade, whichever comes "
        "first. Wherever a figure draws it, the deadline is a tick.",
        "deadline",
        '<rect class="ht" x="40" y="22" width="100" height="70" rx="3"/>'
        '<rect class="paper ln" x="32" y="14" width="100" height="70" rx="3"/>'
        '<rect class="ink" x="32" y="14" width="100" height="14"/>'
        '<path class="ln thin" d="M32 46 H132 M32 65 H132 M57 28 V84 M82 28 V84 M107 28 V84"/>'
        '<circle class="ln thin" cx="44.5" cy="37.5" r="10"/>'
        '<circle class="ln thin" cx="119.5" cy="74.5" r="10"/>'
        '<text x="44.5" y="41.5" text-anchor="middle">30</text>'
        '<text x="119.5" y="78.5" text-anchor="middle">45</text>',
    ),
    (
        "The report goes public",
        "The Clerk publishes it, dated. Where that date falls after the deadline, the days "
        "between are a bar.",
        "after",
        '<rect class="ht" x="58" y="10" width="54" height="56"/>'
        '<path class="paper ln" d="M50 4 H94 L104 14 V58 H50Z"/>'
        '<path class="ln thin" d="M58 20 H86 M58 29 H96 M58 38 H96 M58 47 H80"/>'
        '<path class="ln thin" d="M14 82 H112"/><circle class="ink" cx="16" cy="82" r="4"/>'
        '<path class="paper ln thin" d="M30 77 L35 82 L30 87 L25 82Z"/>'
        '<path class="ln" d="M92 74 V90"/><rect class="bar" x="92" y="79" width="40" height="6"/>'
        '<path class="ln" d="M132 70 V94"/>',
    ),
)


def strip_panels() -> str:
    """The four panels of the rule, each teaching one mark every figure here uses."""
    panels = []
    for n, (head, words, mark, art) in enumerate(PANELS, 1):
        panels.append(
            f'<li class="panel"><p class="cap"><span class="no">{n}</span> {esc(head)}</p>'
            f'<svg viewBox="0 0 160 100" aria-hidden="true" focusable="false">{art}</svg>'
            f"<p>{key_mark(mark)} {esc(words)}</p></li>"
        )
    return f'<ol class="strip">{"".join(panels)}</ol>'


def strip_section(unread: int, total: int, year: int) -> str:
    """How a stock trade becomes a public record, in four panels, each teaching one mark of the
    figures the Findings carry; then the one wry fact the record itself supplies, about the
    machinery and not about anyone: on how many of the chamber's reports the register found no
    Filing ID line, and so read nothing.

    Never "arrived as scanned paper". The register records that it found no Filing ID line and
    no State/District line in the text it extracted (src/adapters/house-fd/ptr.py, verify);
    that a document is a picture of its pages is a cause consistent with that, and no row and
    no run record holds it (the fifth reading of S.1b, Seat G)."""
    paper = (
        f" On {unread:,} of them the register found no Filing ID line, so it read nothing from "
        "them: a limit of the register, not a fact about what was filed."
        if unread
        else ""
    )
    return (
        '<section class="howto" id="how">\n<h2><span class="tag">How a stock trade becomes a '
        "public record</span></h2>\n"
        f"{strip_panels()}\n"
        '<p class="punch">That is the rule, in four steps, for each trade over $1,000. '
        "The law asks for the report; it does not ask "
        f"anyone to stop trading. The Clerk's {year} index lists {total:,} of these reports."
        f"{paper}</p>\n</section>"
    )


# ---- where the record ends ------------------------------------------------------------------

# The Committee on Ethics's own published rule for what follows a report dated after the deadline:
# past thirty more days its memorandum of 30 January 2023 sets a minimum fee of $200 a report, and
# its filing-deadlines page says the fee may be waived in exceptional circumstances (STANDARDS.md
# S.2, both read at the source 2026-09-21 and 2026-09-23). The register places its own rows against
# that published line and computes no fee for anyone: a fee is assessed, or waived, by the
# Committee, and the register sees none of its decisions.
GRACE_DAYS = 30


def report_lateness(findings: list[dict], signal_id: str) -> list[int]:
    """Each current Finding of this signal as one number: the days between the report's own due
    date and the date the Clerk's index gives it.

    A report is due by the earliest deadline among the rows on it, so the row with the earliest
    deadline is the row furthest past it, and its `days_after` is the report's. The arithmetic is
    the Signal's, sealed with the Finding; this reads it back."""
    out = []
    for finding in fired_now(findings, signal_id):
        days = [
            row["days_after"]
            for row in finding["evidence"]["rows"]
            if isinstance(row.get("days_after"), int)
        ]
        if days:
            out.append(max(days))
    return sorted(out)


def ends_chart(late: list[int], meta: dict | None = None) -> str:
    """Two rows, one span: the days after a report's own due date.

    Above, every report the Clerk's index dates after the deadline, one square each, stacked where
    two fall on the same day, with the upright line at the thirtieth day the Committee's memorandum
    names. Below, at the same width, what the register holds about what followed, which is nothing,
    so the row is empty.

    A draft drew the lower row as the upper row's shadow: the same 27 squares in the same places,
    hollow. It was the more clever figure and the less legible one — twenty-seven empty boxes read
    as twenty-seven things, and the eye counts them instead of noticing there is nothing to count.
    An empty band is what emptiness looks like. Nothing is drawn in the lower row at all, so the
    figure asserts no fact about the Committee; it draws this register's own silence at the size of
    the question."""
    if not late:
        return ""
    pad, w = 10, 360
    sq, step = 6.0, 7.5
    floor_y, axis_y = 70.0, 78.0
    band_top, band_h = 124.0, 46.0
    span = max(max(late), GRACE_DAYS + 1)
    inner = w - 2 * pad

    def x(day: int) -> float:
        return pad + inner * day / span

    stacked: dict[int, int] = {}
    squares = []
    for day in late:
        k = stacked.get(day, 0)
        stacked[day] = k + 1
        squares.append(
            f'<rect class="esq" x="{x(day) - sq / 2:.2f}" y="{floor_y - k * step:.1f}" '
            f'width="{sq}" height="{sq}"/>'
        )
    xg = x(GRACE_DAYS)
    parts = [
        f'<text x="{pad}" y="10" text-anchor="start">what the Clerk\'s index shows</text>',
        f'<line class="eline" x1="{xg:.1f}" y1="25" x2="{xg:.1f}" y2="{axis_y}"/>',
        # The 30th day is where the Committee's memorandum sets a fee, so it is named in the
        # strip's caption box; the register draws the line and computes no fee.
        law_tag(xg, 14, f"day {GRACE_DAYS}", 40),
        *squares,
        f'<line class="eaxis" x1="{pad}" y1="{axis_y}" x2="{w - pad}" y2="{axis_y}"/>',
        f'<text x="{pad}" y="{axis_y + 12}" text-anchor="start">0</text>',
        f'<text x="{w - pad}" y="{axis_y + 12}" text-anchor="end">{span}</text>',
        f'<text x="{w - pad}" y="{axis_y + 24}" text-anchor="end">'
        "days after the report was due</text>",
        f'<text x="{pad}" y="{band_top - 6}" text-anchor="start">what followed</text>',
        f'<rect class="evoid" x="{pad}" y="{band_top}" width="{inner}" height="{band_h}"/>',
        f'<text class="eq" x="{w / 2:.1f}" y="{band_top + band_h / 2 + 8:.1f}" '
        'text-anchor="middle">?</text>',
    ]
    stamp = figure_stamp(meta, pad, w - pad, band_top + band_h + 18)
    return (
        f'<svg class="ends" viewBox="0 0 {w} {band_top + band_h + (24 if stamp else 8):.0f}" '
        'direction="ltr" aria-hidden="true" focusable="false">' + "".join(parts) + stamp + "</svg>"
    )


def ends_section(
    signal_runs: list[tuple[dict, dict]], findings: list[dict], meta: dict | None = None
) -> str:
    """Where this register's chain stops, drawn at the width of the part it can see.

    Every other figure on this page is about what the register found or could not read inside the
    filings. This one is about what happens to a filing after the register has read it, which is
    the question a reader asks next and the one the pages had no answer for. The honest answer has
    three parts and the section gives all three: the rule the Committee publishes, where these
    reports fall against it, and the number of rows here about what the Committee then did, which
    is nothing.

    Three things it must not do. It must not compute a fee for anyone: a fee is assessed, or
    waived, by the Committee (STANDARDS.md S.2). It must not read its own silence as the
    Committee's: the register reads the Clerk's filing index, a Committee decision is not among
    its sources, and whether one is published to read is a question it has not answered. And it
    must not lump the two populations the record plainly holds, because eighteen of these reports
    are days past their due date, seven of them by one, and nine are three to six months past;
    a figure that drew them as one number would be false about every report in it."""
    for signal, _summary in signal_runs:
        late = report_lateness(findings, signal["id"])
        if not late:
            continue
        inside = [d for d in late if d <= GRACE_DAYS]
        past = [d for d in late if d > GRACE_DAYS]
        one_day = sum(1 for d in late if d == 1)
        # The emptiness between the two groups is worth a sentence when it is wider than the
        # whole window the Committee's line marks: that is a threshold the record supplies rather
        # than one chosen here, and it keeps a one-day gap, which is noise, out of the page.
        gap = ""
        if inside and past and min(past) - max(inside) > GRACE_DAYS:
            gap = f" No report in this build falls between {max(inside):,} days and {min(past):,}."
        filed = sorted(f["evidence"]["filed_at"] for f in fired_now(findings, signal["id"]))
        swatch = (
            '<svg class="key" viewBox="0 0 12 12" aria-hidden="true" focusable="false">'
            '<rect class="{0}" x="1" y="1" width="10" height="10"/></svg>'
        )
        n = len(late)
        return (
            '<section class="ends" id="ends">\n'
            '<h2><span class="tag">Where the record ends</span></h2>\n'
            f'<p class="glance">A report the Clerk\'s index dates after the deadline is where this '
            "register stops being able to follow anything. What the rule does next is the "
            f"Committee on Ethics's: past {GRACE_DAYS} more days its "
            f'<a href="{PTR_DUE_MEMO}">memorandum of 30 January 2023</a> sets a minimum fee of '
            f'$200 a report, and <a href="{ETHICS_FD}">its filing-deadlines page</a> says the fee '
            "may be waived in exceptional circumstances. The register computes no fee for anyone "
            "and holds no row about what the Committee did.</p>\n"
            '<figure class="ends">\n'
            + ends_chart(late, meta)
            + f"\n<figcaption>Above: the {n:,} {plural(n, 'report', 'reports')} the Clerk's "
            f"{ERA['year']} index dates after the deadline, one square each, placed by the days "
            "between the report's own due date and the date the index gives it, and stacked where "
            f"two fall on the same day. The upright line is the {GRACE_DAYS}th day. Below, on the "
            "same span and at the same width: every row this register holds about what followed, "
            "whether a fee was assessed, waived, or neither. There are none, which is why it is "
            "empty. That emptiness is a fact about this register's sources and not about the "
            "Committee: the register reads the Clerk's filing index, a Committee decision is not "
            "among the sources it reads, and whether one is published to read is a question it "
            "has not answered. It counts reports, not trades or people.</figcaption>\n</figure>\n"
            '<ul class="squarekey">'
            f"<li>{swatch.format('esq')} <b>{len(inside):,}</b> "
            f"{plural(len(inside), 'report', 'reports')} at or inside the {GRACE_DAYS}th day past "
            f"their own due date"
            + (f", {one_day:,} of them by one day" if one_day else "")
            + "</li>"
            f"<li>{swatch.format('esq')} <b>{len(past):,}</b> "
            f"{plural(len(past), 'report', 'reports')} past it, at {min(past):,} to "
            f"{max(past):,} days.{gap}</li>"
            f"<li>{swatch.format('evoid')} <b>0</b> rows here about what followed, for any of the "
            f"{n:,}</li></ul>\n"
            f"<p>The Clerk's index dates these reports between {esc(filed[0])} and "
            f"{esc(filed[-1])}. What followed each is the Committee's to say, on "
            f'<a href="{ETHICS_FD}">its own page</a>. Every piece of official information that '
            f"would let the register carry on past this point is listed, one row each, in "
            f'<a href="{WANTED_PAGE}">what would close the loop</a>.</p>\n'
            f'<p class="quiet">{esc(FRAME)}</p>\n'
            "</section>"
        )
    return ""


# ---- the notice clock: the one date the filer writes ----------------------------------------


# The key's swatch, drawn from the same two fills the figure uses, so a reader matches the block
# in the key to the block in the bar without being told which is which.
DEADLINE_SWATCH = (
    '<svg class="key" viewBox="0 0 12 12" aria-hidden="true" focusable="false">'
    '<rect class="dl {0}" x="1" y="1" width="10" height="10"/></svg>'
)


# ---- the deadline: by it, or after it -------------------------------------------------------


def days_after_rows(findings: list[dict], signal_id: str) -> list[int]:
    """Every row a current Finding of this signal rests on, as the days the Signal computed between
    the deadline and the date the Clerk's index gives the report. The arithmetic is the Signal's and
    is sealed with the Finding; this reads it back and never recomputes it."""
    return sorted(
        row["days_after"]
        for finding in fired_now(findings, signal_id)
        for row in finding["evidence"]["rows"]
        if isinstance(row.get("days_after"), int)
    )


def law_tag(x: float, y: float, words: str, width: float) -> str:
    """The strip's caption box, in the spot colour, naming a line the law or the Committee draws
    on a figure. Only such a line gets one: the box says *this line is the rule*, never *this is
    what the register found*."""
    return (
        f'<rect class="stag" x="{x - width / 2:.1f}" y="{y}" width="{width}" height="11"/>'
        f'<text class="stagt" x="{x:.1f}" y="{y + 8.2:.1f}" text-anchor="middle">{words}</text>'
    )


def figure_stamp(meta: dict | None, left: float, right: float, y: float, size: float = 6.0) -> str:
    """The build a figure was drawn from, inside the drawing, so a crop of it still says which
    sealed record it shows and a reader can find that build in ANCHORS.md and check it.

    One line at the figure's foot, in the build's one written form, and after it a short engraved
    band struck from the digest the way the mark is: fine interlaced waves whose counts and phases
    are the digest's own bytes, so each build draws its own, and a band that does not match the
    digest printed beside it shows it was drawn for another build. It borrows the mark's craft and
    never the mark (feedback-the-mark-is-his.md), and it is set in the quietest ink the figure has,
    because it is provenance and not a subject."""
    if not meta or not meta.get("digest"):
        return ""
    raw = bytes.fromhex(str(meta["digest"])[:64].ljust(64, "0"))
    label = f"oath · {build_label(meta)}"
    # The words take their width from the type, roughly; the band takes what is left, and is left
    # out entirely on a figure too narrow to hold it quietly.
    text_w = len(label) * size * 0.62
    x0, x1 = left + text_w + 8, right
    parts = [
        # The size rides on the element, because each figure draws on its own canvas and its own
        # text rule would otherwise set the stamp in the figure's type.
        f'<text class="stamp" x="{left}" y="{y + size * 0.4:.1f}" style="font-size:{size}px" '
        f'text-anchor="start">{esc(label)}</text>'
    ]
    if x1 - x0 > 40:
        for i in range(3):
            cycles = 4 + raw[i] % 5
            phase = raw[i + 3] / 255 * 2 * math.pi
            amp = (1.0 + (raw[i + 6] % 3) * 0.35) * size / 6
            pts = []
            for k in range(81):
                t = k / 80
                pts.append(
                    f"{x0 + (x1 - x0) * t:.1f},"
                    f"{y + amp * math.sin(2 * math.pi * cycles * t + phase):.2f}"
                )
            parts.append(f'<polyline class="stampwave" points="{" ".join(pts)}"/>')
    return "".join(parts)


def deadline_chart(on_time: int, late: list[int], meta: dict | None = None) -> str:
    """One drawing, two registers.

    Above: every trade the Signal compared, as a single bar split where the deadline falls, so the
    proportion is the first thing a reader takes in and not a number they have to divide. Below:
    the far side of that split enlarged, spread by the days past the deadline, one bar a day. A
    bracket joins the two, because the lower register is the upper one's dark segment magnified and
    a reader should not have to be told that in words.

    The page taught four marks in its four panels; the tick is the deadline and the bar is how late.
    This is where it draws them at the scale of the whole chamber."""
    # Room above the bar for its one label, and room between the two registers for the bracket to
    # read as a bracket: the whole drawing is the one line at the split, twice, joined.
    pad, w = 8, 360
    bar_y, bar_h, gap = 20, 16, 3
    head, base = 78, 168
    # A day carrying any trade at all is drawn at least this high. Without a floor the long tail,
    # where a day holds one or two trades against a busiest day of hundreds, falls below a pixel
    # and the figure shows four spikes and an empty plain; with one, the caption says so.
    FLOOR = 2.5
    inner = w - 2 * pad
    total = on_time + len(late)
    if not total:
        return ""
    split = pad + inner * on_time / total
    per_day: dict[int, int] = {}
    for d in late:
        per_day[d] = per_day.get(d, 0) + 1
    furthest = max(per_day, default=1)
    step = inner / max(furthest, 1)
    top = max(per_day.values(), default=1)
    on_w = len(f"{on_time:,}") * 6.2 + 8
    parts = [
        # The strip's own ink: a panel's hard shadow under the whole bar, and paper beneath the
        # screened block so the shadow does not show through its dots.
        f'<rect class="dshadow" x="{pad + 3}" y="{bar_y + 3}" width="{inner}" height="{bar_h}"/>',
        f'<rect class="dpaper" x="{pad}" y="{bar_y}" width="{inner}" height="{bar_h}"/>',
        # the whole, and the part of it past the deadline
        f'<rect class="dl by" x="{pad}" y="{bar_y}" width="{split - pad:.1f}" height="{bar_h}"/>',
        f'<rect class="dl after" x="{split:.1f}" y="{bar_y}" width="{w - pad - split:.1f}" '
        f'height="{bar_h}"/>',
        # the deadline itself, the one line the rest of the drawing hangs on
        f'<line class="dline" x1="{split:.1f}" y1="{bar_y - 4}" x2="{split:.1f}" '
        f'y2="{bar_y + bar_h + 4}"/>',
        # The deadline named the way the strip names things: a caption box in the spot colour.
        f'<rect class="dtag" x="{split - 34:.1f}" y="3" width="68" height="12"/>',
        f'<text class="dtagt" x="{split:.1f}" y="12" text-anchor="middle">the deadline</text>',
        # Both counts on the blocks they belong to, so the picture says what it is without the
        # key: a reader should be able to take the whole of it in before reading a word below.
        # The screened block's count sits on paper, in a box, so the dots never cross the digits.
        f'<rect class="dlabel" x="{(pad + split) / 2 - on_w / 2:.1f}" y="{bar_y + 2}" '
        f'width="{on_w:.1f}" height="{bar_h - 4}"/>',
        f'<text class="don" x="{(pad + split) / 2:.1f}" y="{bar_y + bar_h - 4.5}" '
        f'text-anchor="middle">{on_time:,}</text>',
        f'<text class="doff" x="{(split + w - pad) / 2:.1f}" y="{bar_y + bar_h - 4.5}" '
        f'text-anchor="middle">{len(late):,}</text>',
        # the bracket: the dark segment, opened out into the register below it
        f'<path class="dfan" d="M{split:.1f} {bar_y + bar_h + gap} L{pad} {head - 6} '
        f'L{w - pad} {head - 6} L{w - pad} {bar_y + bar_h + gap} Z"/>',
    ]
    for day, n in sorted(per_day.items()):
        h = max(round(n / top * (base - head), 1), FLOOR)
        x = pad + (day - 1) * step
        parts.append(
            f'<rect class="dl after" x="{x:.2f}" y="{base - h:.1f}" '
            f'width="{min(step - 0.25, 3):.2f}" height="{h:.1f}"/>'
        )
    parts.append(f'<line class="dline" x1="{pad}" y1="{head - 6}" x2="{pad}" y2="{base}"/>')
    parts.append(f'<line class="daxis" x1="{pad}" y1="{base}" x2="{w - pad}" y2="{base}"/>')
    for day in (30, 90, furthest):
        if day > furthest:
            continue
        x = pad + (day - 1) * step
        parts.append(f'<line class="dtick" x1="{x:.1f}" y1="{base}" x2="{x:.1f}" y2="{base + 3}"/>')
        parts.append(f'<text x="{x:.1f}" y="{base + 12}" text-anchor="middle">{day}</text>')
    parts.append(f'<text x="{pad}" y="{base + 12}" text-anchor="start">1</text>')
    parts.append(
        f'<text x="{w - pad}" y="{base + 24}" text-anchor="end">days after the deadline</text>'
    )
    stamp = figure_stamp(meta, pad, w - pad, base + 40)
    return (
        f'<svg class="deadline" viewBox="0 0 {w} {base + (46 if stamp else 28)}" direction="ltr" '
        'aria-hidden="true" focusable="false">' + "".join(parts) + stamp + "</svg>"
    )


def deadline_section(
    signal_runs: list[tuple[dict, dict]],
    findings: list[dict],
    meta: dict | None = None,
    all_runs: list[tuple[dict, dict]] | None = None,
) -> str:
    """The one figure the page is for: the deadline, and how many trades fell on each side of it.

    Every other figure here says which reports the register could read, or where a filer's own
    notice date fell. None said the thing the register was built to show: that of the trades it
    compared, most were reported inside the limit the law sets, and that where a report came after
    it the distance is usually days and occasionally months. Both halves are the record, and a
    figure that drew only the second would be an indictment rather than a register.

    The counts come from the run record; the distribution comes from the rows the Findings carry,
    which is the Signal's own arithmetic, sealed. Where the two disagree about how many rows are
    past the deadline the section says so and draws nothing, because a picture drawn from one and
    labelled from the other is the defect this project exists to prevent."""
    parts = []
    for signal, summary in signal_runs:
        compared = summary.get("rows_evaluated") or 0
        after = summary.get("rows_after") or 0
        if not compared:
            continue
        late = days_after_rows(findings, signal["id"])
        if len(late) != after:
            parts.append(
                f'<p class="quiet">This build\'s run record counts {after:,} '
                f"{plural(after, 'trade', 'trades')} past the deadline and its Findings carry "
                f"{len(late):,}, so the register draws neither: "
                f'<a href="{signal_page_path(signal)}">the signal\'s own page</a> has what it '
                "did.</p>\n"
            )
            continue
        on_time = compared - len(late)
        reports = summary.get("reports_with_a_finding") or 0
        named = len({f["officeholder_id"] for f in fired_now(findings, signal["id"])})
        middle = late[len(late) // 2] if late else 0
        words = ANSWER_WORDS.get((signal["slug"], signal["version"]))
        against = words["against"] if words else "the deadline the rule sets"
        parts.append(
            '<figure class="deadline">\n'
            + deadline_chart(on_time, late, meta)
            + "\n<figcaption>Every trade the signal compared, as one bar split where the deadline "
            "falls, and below it the part after, spread one bar a day by the days between the "
            "deadline and the date the Clerk's index gives the report, on a plain scale where a "
            "day carrying any trade at all is drawn at least a tick high so the far days show. It "
            "counts trades and not reports or people: a tall bar can be a single report."
            "</figcaption>\n</figure>\n"
            '<ul class="squarekey">'
            f"<li>{DEADLINE_SWATCH.format('by')} <b>{on_time:,}</b> trades whose report the "
            f"Clerk's index dates on or before {against}</li>"
            f"<li>{DEADLINE_SWATCH.format('after')} <b>{len(late):,}</b> trades whose report it "
            f"dates after the deadline, on {reports:,} {plural(reports, 'report', 'reports')}: "
            f"half of them by {middle:,} {plural(middle, 'day', 'days')} or fewer, the "
            f"furthest by {max(late):,}</li></ul>\n"
            + (
                f"<p>The {reports:,} {plural(reports, 'report is', 'reports are')} by {named:,} "
                f"{plural(named, 'member', 'members')}. Each is on that member's page, with the "
                f'dates it rests on drawn: <a href="{signal_page_path(signal)}">the {named:,} '
                f"{plural(named, 'member', 'members')}, in seat order</a>.</p>\n"
                if reports and named
                else ""
            )
        )
    # What a signal is, said here because this is where a reader first meets one at work. It
    # carries the only link from the landing to each Signal's own page, and in a build with no
    # signal it is the sentence that says which silence the landing is.
    what = (
        "<details>\n<summary>What a signal is, and what it does not say</summary>\n"
        + signals_lede(signal_runs if all_runs is None else all_runs).replace(
            '<p class="lede">', "<p>", 1
        )
        + "</details>\n"
    )
    if not parts:
        return f'<section class="deadline" id="deadline">\n{what}</section>'
    # The thirty words about who decides are said in full once, here, where a result is first
    # drawn. Every later figure carries the nine-word frame, which is the sentence Seat D's
    # finding says must never travel without the result; the rest said four times on one page
    # made it sound as if it were apologising, which is a change of tone nobody chose (P.6).
    return (
        '<section class="deadline" id="deadline">\n'
        '<h2><span class="tag">By the deadline, or after it</span></h2>\n'
        f'<p class="quiet">{esc(HOW_TO_READ)}</p>\n' + "".join(parts) + f'<p class="quiet">'
        f"{esc(EITHER_WAY)}</p>\n{what}</section>"
    )


def notice_bands(transactions: list[dict], filings: list[dict]) -> dict:
    """Every trade the register has read, by the days from the trade to the notice date its report
    prints, and for each band the trades, the reports and the members it holds: one report can
    list hundreds of trades, so a count of trades alone would let one report look like many."""
    filed = {f["id"]: f.get("filed_at") for f in filings}
    days: dict[object, int] = {}
    bands: dict[str, dict] = {
        k: {"trades": 0, "reports": set(), "members": set()}
        for k in ("before", "same", "within", "past")
    }
    spouse = same_day = 0
    for t in transactions:
        if not (t.get("transaction_date") and t.get("notified_date")):
            continue
        gap = (
            date.fromisoformat(t["notified_date"]) - date.fromisoformat(t["transaction_date"])
        ).days
        key = "<0" if gap < 0 else gap if gap <= 60 else "61+"
        days[key] = days.get(key, 0) + 1
        band = "before" if gap < 0 else "same" if gap == 0 else "within" if gap <= 45 else "past"
        b = bands[band]
        b["trades"] += 1
        b["reports"].add(t["filing_id"])
        b["members"].add(t["officeholder_id"])
        if band == "past":
            spouse += t.get("owner") == "spouse"
            same_day += filed.get(t["filing_id"]) == t["notified_date"]
    out = {
        k: {"trades": v["trades"], "reports": len(v["reports"]), "members": len(v["members"])}
        for k, v in bands.items()
    }
    return {"days": days, "bands": out, "spouse": spouse, "same_day": same_day}


def notice_chart(days: dict, meta: dict | None = None) -> str:
    """One bar a day, from the day of the trade to 60 days after it, a bar for notices printed
    before the trade at the left and one for 61 days or more at the right, drawn to one linear
    scale; upright lines at 30 and 45 days. Dates and counts only; its words are in the caption,
    and the stamp at its foot names the build it was drawn from."""
    keys = ["<0"] + list(range(61)) + ["61+"]
    top = max(days.values(), default=1) or 1
    base, height, step = 128, 110, 5.0

    def x(k) -> float:
        if k == "<0":
            return 4
        if k == "61+":
            return 16 + 61 * step + 8
        return 16 + k * step

    parts = []
    for k in keys:
        n = days.get(k, 0)
        h = round(n / top * height, 1)
        band = "before" if k == "<0" else "past" if (k == "61+" or k > 45) else "within"
        if n:
            parts.append(
                f'<rect class="nb {band}" x="{x(k):.1f}" y="{base - max(h, 0.8):.1f}" width="4" '
                f'height="{max(h, 0.8):.1f}"/>'
            )
    for mark, cls in ((30, "thirty"), (45, "fortyfive")):
        xm = x(mark) + 2 + step / 2
        parts.append(f'<line class="nl {cls}" x1="{xm:.1f}" y1="14" x2="{xm:.1f}" y2="{base}"/>')
        # 45 days is the line the statute draws, so it is named in the strip's caption box; 30 is
        # counted from the notice, which moves, so it keeps a plain label.
        parts.append(
            law_tag(xm, 1, "45", 22)
            if mark == 45
            else f'<text x="{xm:.1f}" y="10" text-anchor="middle">{mark}</text>'
        )
    parts.append(f'<line class="na" x1="2" y1="{base}" x2="358" y2="{base}"/>')
    for k, label in (("<0", "&lt;0"), (0, "0"), (30, ""), ("61+", "61+")):
        if label:
            parts.append(
                f'<text x="{x(k) + 2:.1f}" y="{base + 13}" text-anchor="middle">{label}</text>'
            )
    stamp = figure_stamp(meta, 4, 356, base + 30)
    return (
        f'<svg class="noticeclock" viewBox="0 0 360 {base + (36 if stamp else 18)}" '
        'direction="ltr" aria-hidden="true" focusable="false">' + "".join(parts) + stamp + "</svg>"
    )


def notice_section(transactions: list[dict], filings: list[dict], meta: dict | None = None) -> str:
    """The one date the filer writes: the notice date, which alone can move a deadline, and by no
    more than 15 days. Every trade the register has read, drawn by the days from the trade to its
    printed notice; the key says trades, reports and members for each band. It names no one, and
    it says what the register cannot see: why a notice came when it did."""
    facts = notice_bands(transactions, filings)
    b = facts["bands"]
    total = sum(v["trades"] for v in b.values())
    if not total:
        return ""

    def trio(v: dict) -> str:
        return (
            f"{v['trades']:,} {plural(v['trades'], 'trade', 'trades')} on {v['reports']:,} "
            f"{plural(v['reports'], 'report', 'reports')} by {v['members']:,} "
            f"{plural(v['members'], 'member', 'members')}"
        )

    swatch = (
        '<svg class="key" viewBox="0 0 12 12" aria-hidden="true" focusable="false">'
        '<rect class="nb {0}" x="1" y="1" width="10" height="10"/></svg>'
    )
    past = b["past"]
    spouse = ""
    if past["trades"]:
        spouse = (
            f" For {facts['spouse']:,} of these trades the filer marked the asset as a spouse's"
        )
        if facts["same_day"]:
            n = facts["same_day"]
            spouse += (
                f", and {n:,} {plural(n, 'is on a report', 'are on reports')} dated the same day "
                f"as the notice {plural(n, 'it prints', 'they print')}"
            )
        spouse += "."
    return (
        '<section class="noticeclock" id="notice">\n<h2><span class="tag">The one date the filer '
        "writes</span></h2>\n"
        f'<p class="glance">On {past["trades"]:,} of these trades the notice date the report '
        "prints falls more than 45 days after the trade itself, so, as the dates are printed, the "
        "deadline had passed before the member says they learned of it. The notice date is the "
        "filer's own entry and the only date that can move a deadline, by at most 15 days; past "
        "45 days after the trade it no longer waits for one.</p>\n"
        '<figure class="noticeclock">\n'
        + notice_chart(facts["days"], meta)
        + f"\n<figcaption>All {total:,} trades on the transaction reports the register has read, "
        "by the days from the trade to the notice date the report prints, one bar a day, with "
        "every trade 61 days or more after in the last bar, notices printed before the trade in "
        "one at the left, and upright lines at 30 and 45 days. It counts trades, not reports or "
        "people, and draws each date as the report prints it, so a date typed wrong on a form is "
        "drawn where it was typed.</figcaption>\n</figure>\n"
        '<ul class="squarekey">'
        f"<li>{swatch.format('within')} <b>{b['same']['trades'] + b['within']['trades']:,}</b> "
        "notices printed the same day as the trade or up to 45 days after it "
        f"({b['same']['trades']:,} the same day)</li>"
        f"<li>{swatch.format('past')} <b>{past['trades']:,}</b> printed more than 45 days after "
        f"the trade, the ones this section opens with: {trio(past)}."
        f"{spouse}</li>"
        f"<li>{swatch.format('before')} <b>{b['before']['trades']:,}</b> printed before the "
        f"trade itself, dates that cannot both be right: {trio(b['before'])}.</li></ul>\n"
        "<p>The register cannot see why a notice came when it did, and the report does not say. "
        "It can show where the dates fall against the rule; every member's page lists each trade "
        f'with both of its dates, as filed. <span class="either">{esc(FRAME)}</span></p>\n'
        "</section>"
    )


# What the Signal's run record says about a row it did not evaluate, grouped as a reader needs and
# attributed where it belongs. The register's own limits on one side; the rule's own scope on the
# other, which on the 2025 record is one row of 1,156. Saying "the rule does not reach" of the rest
# is the falsehood that flatters, and it is the same defect as the one that condemns (COUNCIL §5).
NARROWS_GROUPS = (
    ("asset coded", "a kind of asset the register does not evaluate", "register"),
    (
        "coded as a stock, named as an ETF",
        "an asset whose printed code and printed name disagree",
        "register",
    ),
    (
        "dated before this Congress's swearing-in",
        "dated before the swearing-in the roster records",
        "register",
    ),
    ("marked Amended", "the report itself marks amended or deleted", "report"),
    ("marked Deleted", "the report itself marks amended or deleted", "report"),
    ("transaction dated after the report", "dated after the report that lists them", "report"),
    ("$1,000 or less", "at or under the $1,000 the rule sets", "rule"),
)


def narrows_group(reason: str) -> tuple[str, str]:
    """One recorded reason, as (words, whose). A reason this version has no words for is given as
    the run record writes it and attributed to the register, never to the rule."""
    for prefix, words, whose in NARROWS_GROUPS:
        if reason.startswith(prefix):
            return words, whose
    return f"set aside, recorded as {reason}", "register"


def narrows_figure(
    outcomes: list[dict], findings: list[dict], signal: dict, words: dict, meta: dict | None = None
) -> str:
    """Where the record narrows, and why, from the Clerk's index to a signal firing: four steps,
    each with the number of reports that survive it and a plain sentence naming what did not.

    Every other surface here says what the register found. This one says what it could reach, which
    is the harder half and the half nobody else publishes. The landing already gives 463 in the
    strip and 294 in the paragraph above; what it never gave is the 115 between them, the reports
    the register read and compared no row on, and that is the one number a reader needs before
    trusting any other. Each step is a fact about the register, not about anyone; no step names a
    person and nothing is sorted by anything about one (INVARIANTS §7, §13).

    Bars in the page's own ink, at one opacity per step so the narrowing reads without colour
    carrying the meaning; inline SVG, no script, legible at 360px and through the caption alone.
    Drawn from the same run record the sentence above it counts, so it regenerates with it.
    """
    one, many = words["reports"]
    total = len(outcomes)
    if not total:
        return ""
    read = [o for o in outcomes if o["state"] == "evaluated"]
    compared = [o for o in read if o.get("evaluated")]
    fired = len({f["producing_filings"][0] for f in fired_now(findings, signal["id"])})
    rows = sum(o.get("rows") or 0 for o in read)
    set_aside: dict[tuple[str, str], int] = {}
    codes: dict[str, int] = {}
    for o in read:
        for reason, n in (o.get("not_evaluated") or {}).items():
            key = narrows_group(reason)
            set_aside[key] = set_aside.get(key, 0) + n
            if reason.startswith("asset coded "):
                code = reason.removeprefix("asset coded ")
                codes[code] = codes.get(code, 0) + n
    biggest = max(codes.items(), key=lambda i: (i[1], i[0]), default=None)
    by_whose = {"register": 0, "report": 0, "rule": 0}
    for (_w, whose_), n in set_aside.items():
        by_whose[whose_] += n
    said = "; ".join(
        f"{n:,} {w}"
        + (
            f", {biggest[1]:,} of them coded {biggest[0]}"
            if biggest and w == NARROWS_GROUPS[0][1]
            else ""
        )
        for (w, _whose), n in sorted(set_aside.items(), key=lambda i: (-i[1], i[0]))
    )
    ours = by_whose["register"] + by_whose["report"]
    whose = (
        " Of those, the rule's own scope accounts for "
        + (f"{by_whose['rule']:,}" if by_whose["rule"] else "none")
        + f"; the other {ours:,} {plural(ours, 'is a limit', 'are limits')} of the register, "
        "or what the report says about itself."
        if said
        else ""
    )
    steps = (
        (
            total,
            f"the Clerk's {ERA['year']} index lists",
            f"Every {one} the index attributes to a member of the chamber.",
            "",
        ),
        (
            len(read),
            "the register read",
            f"{total - len(read):,} it fetched and could not read: it looks in the text it "
            "extracts for the Filing ID line and the State/District line the Clerk's system "
            "prints on a filed report, and did not find both. That is a limit of the register, "
            "not a fact about what was filed.",
            "",
        ),
        (
            len(compared),
            "it compared a trade on",
            f"On {len(read) - len(compared):,} more it compared no trade at all. Of the "
            f"{rows - sum(o.get('evaluated') or 0 for o in read):,} trades it set aside across "
            f"every report it read: {said}.{whose} Each reason is one this Signal ",
            f'<a href="{signal_page_path(signal)}">wrote down before it ran</a>.',
        ),
        (
            fired,
            "the index dates after the deadline",
            "For at least one trade compared.",
            "",
        ),
    )
    w, bar, gap = 640, 26, 16
    height = len(steps) * (bar + gap)
    drawn = []
    # One mark, one meaning, on every figure of the landing: the squares' own three states. The
    # reports the index lists and the register read are outlined and lightly screened, the ones it
    # compared carry the 50% screen the squares give "checked", and the ones the index dates after
    # the deadline are solid ink, as every figure draws after. Each bar sits on a panel's shadow.
    fills = ("nr listed", "nr read", "nr compared", "nr after")
    for i, (n, _label, _why, _tail) in enumerate(steps):
        y = i * (bar + gap)
        width = max(round(w * n / total, 1), 2.0)
        drawn.append(
            f'<rect class="nrshadow" x="4" y="{y + 4}" width="{width}" height="{bar}"/>'
            f'<rect class="nrpaper" x="0" y="{y}" width="{width}" height="{bar}"/>'
            f'<rect class="{fills[i]}" x="0" y="{y}" width="{width}" height="{bar}"/>'
            f'<text class="out" x="{width + 12:.1f}" y="{y + bar - 8}" text-anchor="start">'
            f"{n:,}</text>"
        )
    spoken = "; ".join(f"{n:,} {label}" for n, label, _why, _tail in steps)
    stamp = figure_stamp(meta, 0, w + 50, height + 8, 11)
    svg = (
        f'<svg viewBox="-1 0 {w + 60} {height + (20 if stamp else 0)}" role="img" '
        f'aria-label="{esc(spoken)}." xmlns="http://www.w3.org/2000/svg">{"".join(drawn)}'
        f"{stamp}</svg>"
    )
    listed = "\n".join(
        f"<dt>{n:,}</dt><dd><b>{esc(label)}.</b> {esc(why)}{tail}</dd>"
        for n, label, why, tail in steps
    )
    return (
        '<figure class="narrows">\n'
        f"{svg}\n"
        f"<figcaption>Where the record narrows, and why. Each bar counts {many}, not trades, as a "
        f"share of the {total:,} the index lists; a report counts as compared where the register "
        "compared at least one trade on it, and one report can list hundreds. The figure shows the "
        "register's own reach. It does not show what any report says, or anything the House "
        "Committee on Ethics has determined.</figcaption>\n"
        "</figure>\n"
        f'<dl class="narrows">\n{listed}\n</dl>\n'
    )


def narrows_section(
    signal_runs: list[tuple[dict, dict]],
    outcomes_all: dict[str, list[dict]],
    findings: list[dict],
    meta: dict | None = None,
) -> str:
    """What the register could not reach, in one place.

    These four numbers and their reasons used to sit inside the glance, which already said the
    funnel in a sentence and again in its key: three tellings of one narrowing in the first screens
    a reader meets. Limits read better as their own movement, in the order a careful reader raises
    them, than as a caveat hung on every number, and that is the shape the README is written in.
    The figure and its list stay together, because the list is what the figure means.
    """
    parts = []
    for signal, _summary in signal_runs:
        words = ANSWER_WORDS.get((signal["slug"], signal["version"]))
        outcomes = outcomes_all.get(signal["id"], [])
        if words is None or not outcomes:
            continue
        parts.append(narrows_figure(outcomes, findings, signal, words, meta))
    if not parts:
        return ""
    return (
        '<section class="narrows" id="narrows">\n'
        "<h2>What the register could not reach</h2>\n"
        '<p class="lede">Every other part of this page says what the register found. This one says '
        "what it could not get to, which is the harder half and the half that decides whether any "
        "of the rest is worth trusting.</p>\n" + "".join(parts) + "</section>"
    )


def glance_section(
    signal_runs: list[tuple[dict, dict]],
    outcomes_all: dict[str, list[dict]],
    findings: list[dict],
    home: str = "",
) -> str:
    """The House at a glance: one square for every report a Signal read or tried to read, across
    the whole chamber, in the order filed, and the same three states a person's page draws. No
    square names anyone and no square links to anyone; the members a Finding rests on are one
    click away, in seat order, on the Signal's own page (Invariant §13).

    It lives on the record page, not the landing (NEXT.md P.6). The deadline figure answers the
    landing's question, whether the chamber's trades were reported by the deadline, better than
    463 squares in filing order do, and its counts are the narrowing figure's and the ends
    figure's; report-by-report detail is apparatus. What only the glance carried moved with the
    reader: the link to the members in seat order, the statute, and what a signal is. `home` is
    the path back to the landing, for the link to the map."""
    parts = []
    for signal, _summary in signal_runs:
        words = ANSWER_WORDS.get((signal["slug"], signal["version"]))
        outcomes = outcomes_all.get(signal["id"], [])
        if words is None or not outcomes:
            continue
        one, many = words["reports"]
        states = report_states(outcomes, findings, signal["id"])
        counts = {k: sum(1 for st in states if st[2] == k) for k in SQUARE_WORDS}
        members = len({o["officeholder_id"] for o in outcomes})
        named = len({f["officeholder_id"] for f in fired_now(findings, signal["id"])})
        checked = counts["after"] + counts["checked"]
        n = len(states)
        first, last = states[0][0], states[-1][0]
        parts.append(
            f'<p class="glance">One square for each of the {n:,} '
            f"{plural(n, one, many)} "
            f"the Clerk's {ERA['year']} index attributes to {members:,} "
            f"{plural(members, 'member', 'members')}. The register compared {checked:,} of them "
            f"against {words['against']}, and the Clerk's index dates {counts['after']:,} of "
            "those after it, for at least one trade compared.</p>\n"
            f'<figure class="glance">\n'
            + squares(states, square_label(states, words["reports"]))
            + f"\n<figcaption>One square per report, in the order the Clerk's index dates them, "
            f"{esc(first)} to {esc(last)}. No square names anyone, and nothing here is sorted by "
            "anything about a person.</figcaption>\n</figure>\n"
            + square_key(counts)
            + f"<p>The {counts['after']:,} dark squares are {counts['after']:,} reports by "
            f"{named:,} "
            f"{plural(named, 'member', 'members')}. Each is on that member's page, with the dates "
            f'it rests on drawn: <a href="{signal_page_path(signal)}">the {named:,} '
            f"{plural(named, 'member', 'members')}, in seat order</a>. Or find your own "
            f'representative <a href="{home}#find">on the map</a>.</p>\n'
            f'<p class="quiet">{esc(EITHER_WAY)}</p>\n'
        )
    if not parts:
        return ""
    return (
        '<section class="glance" id="glance">\n<h2><span class="tag">The House at a glance</span>'
        "</h2>\n" + "".join(parts) + "</section>"
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
        "unread_only": sum(1 for s in states.values() if s == {"not read"}),
        "some_unread": sum(1 for s in states.values() if "not read" in s and s != {"not read"}),
        "not_fetched": unfetched,
        "before_swearing_in": len(before),
        "set_aside_held": held,
        "set_aside_shut": shut,
        "set_aside_other": len(ptr) - held - shut,
    }


def coverage_sentence(c: dict[str, int]) -> str:
    """Who cannot appear among those on which a signal fired, and why, in counts."""
    unread, partly, before = c["unread_only"], c["some_unread"], c["before_swearing_in"]
    held, other = c["set_aside_held"], c["set_aside_other"]
    shut, unfetched = c.get("set_aside_shut", 0), c.get("not_fetched", 0)
    aside = held + other + shut
    return (
        f"It cannot reach {unread:,} {plural(unread, 'officeholder', 'officeholders')} none of "
        "whose transaction reports it could read, or some of the reports of "
        f"{partly:,} more"
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
    filings: list[dict] | None = None,
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
        "Who cannot appear here, and why, is counted above: "
        + (
            "an officeholder whose annual report prints no header the register could read "
            "cannot, whatever the report shows. "
            if voice(signal) == ANNUAL_VOICE
            else "an officeholder none of whose transaction reports the register could read "
            "cannot, whatever the reports show. "
        )
        + "What the register "
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
        f"<dt>{c['unread_only']:,}</dt><dd>officeholders none of whose transaction reports "
        "the register could read, so they cannot appear below whatever the reports show: in "
        "each it looked for the Filing ID line the Clerk's system prints and found none; "
        f"{c['some_unread']:,} more have some</dd>\n"
        f"<dt>{c['before_swearing_in']:,}</dt><dd>officeholders with rows dated before the "
        f"swearing-in the roster records for {congress_words()}, which it does not evaluate: "
        "the roster records that date, not the start of anyone's service, and the register "
        "holds no earlier index</dd>\n"
        f"<dt>{c['set_aside_held'] + c['set_aside_other'] + c.get('set_aside_shut', 0):,}</dt>"
        "<dd>transaction reports the index sets aside, not attributed to an officeholder, which "
        f"it does not see: {c['set_aside_held']:,} under the surname of an officeholder the "
        "register holds, for the maintainer to decide by hand, "
        + (
            f"{c['set_aside_shut']:,} under such a surname and dated outside the days the "
            "register can show an officeholder of that seat in office, which no decision "
            "attributes, "
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
        f"<dt>{by_state.get('not read', 0) - c.get('not_fetched', 0):,}</dt><dd>reports "
        "fetched, hashed and not read: the register looked in the text it extracted for the "
        "Filing ID line and the State/District line the Clerk's system prints on a filed "
        "report, and did not find both, so it read no transaction from them. A picture of "
        "the pages, or a form that prints neither line, would both read this way, and the "
        "register does not record which</dd>\n"
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
    if voice(signal) == ANNUAL_VOICE:
        record = annual_signal_record(summary, outcomes, findings, signal, filings or [], holders)
    body = (
        f'{head}\n<main id="main">\n'
        f"{rule_drawn(signal)}"
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


def rule_drawn(signal: dict) -> str:
    """The rule a Signal reads, drawn before it is written out: the landing's four panels for the
    transaction report, and for the annual report its two dates and the three places a report's
    date can fall. The definition below is the Signal's own words, frozen with its version; this
    drawing restates no criterion it does not state."""
    if voice(signal) == PTR_VOICE:
        return (
            '<section class="howto">\n<h2><span class="tag">The rule, in four panels</span></h2>\n'
            f"{strip_panels()}\n"
            '<p class="punch">That is the rule, for each trade over $1,000. The law asks for the '
            "report; it does not ask anyone to stop trading.</p>\n</section>\n"
        )
    if voice(signal) == ANNUAL_VOICE:
        return (
            '<section class="howto">\n<h2><span class="tag">The rule, drawn</span></h2>\n'
            f"{annual_rule_figure()}\n</section>\n"
        )
    return ""


def annual_rule_figure() -> str:
    """The annual report's two dates and the three places its date can fall, with a sample mark in
    each, drawn as every figure here draws it. No report is drawn: this is the rule, not the
    record."""
    w, left, right = 520, 14, 14
    due_x, latest_x = 150, 380
    axis = 64

    def mark(cx: float, state: str) -> str:
        return f'<circle class="amark {state}" cx="{cx}" cy="{axis - 14}" r="5.5"/>'

    parts = [
        BENDAY,
        law_tag(due_x, 2, "15 May", 32),
        law_tag(latest_x, 2, "+90", 22),
        f'<path class="abracket" d="M{due_x} {axis - 6} V{axis - 34} H{latest_x} V{axis - 6}"/>',
        f'<line class="aline" x1="{due_x}" y1="13" x2="{due_x}" y2="{axis + 4}"/>',
        f'<line class="aline" x1="{latest_x}" y1="13" x2="{latest_x}" y2="{axis + 4}"/>',
        f'<line class="aaxis" x1="{left}" y1="{axis}" x2="{w - right}" y2="{axis}"/>',
        mark(82, "compared"),
        mark(265, "read"),
        mark(455, "after"),
        # The day after the latest date, which the Signal does not evaluate: an outline, the mark
        # for nothing decided there.
        f'<rect class="yvoid" x="{latest_x + 3}" y="{axis - 19}" width="10" height="10"/>',
    ]
    labels = (
        (82, "on or before it:", "compared"),
        (265, "in between: an extension may", "cover it; not decided"),
        (455, "after it, from the", "second day: it fires"),
    )
    for cx, one, two in labels:
        parts.append(
            f'<text class="alaw" x="{cx}" y="{axis + 15}" text-anchor="middle">{esc(one)}</text>'
            f'<text class="alaw" x="{cx}" y="{axis + 26}" text-anchor="middle">{esc(two)}</text>'
        )
    height = axis + 32
    caption = (
        "The annual report is due by 15 May of the year after the one it covers, or the next "
        "business day, and outside a combat zone extensions may add at most 90 days (5 U.S.C. "
        "§ 13103(d), (g)(1)). A report dated on or before its original due date is compared and "
        "is not after it; one dated in between may be covered by an extension, which the register "
        "does not decide; one dated after the latest date an extension could reach is where the "
        "Signal fires, except on the day after it, the outlined square, which it does not "
        "evaluate. The drawing shows the rule, not any report."
    )
    return (
        '<figure class="annual rule">\n'
        f'<svg viewBox="0 0 {w} {height}" direction="ltr" role="img" '
        'aria-describedby="rule-cap">'
        + "".join(parts)
        + f'</svg>\n<figcaption id="rule-cap">{esc(caption)}</figcaption>\n</figure>'
    )


# ---- the annual report: one date per report, against the latest date the law allows ---------

# Which of the page's voices speaks for a Signal. Every sentence, count and figure above this
# section was written for the Signal that compares rows on transaction reports: it says trades
# and rows, and spoken for a Signal about an annual report it would say them of reports that list
# none. So a Signal is spoken for only by the voice written for it; the transaction sections are
# handed that Signal's runs alone, and a Signal no voice speaks for stops the render, as one with
# no answer words always has (answer_section).
PTR_VOICE = ("stock-act-ptr-after-deadline", 1)
ANNUAL_VOICE = ("annual-report-after-extension-limit", 1)
VOICES = (PTR_VOICE, ANNUAL_VOICE)
USC_13103 = (
    "https://uscode.house.gov/view.xhtml?req=granuleid:USC-prelim-title5-section13103"
    "&num=0&edition=prelim"
)
ETHICS_GUIDE_2025 = "https://ethics.house.gov/wp-content/uploads/2026/07/7-8-2026-2025-Published-Instruction-Guide.pdf"
STANDARD_LINKS["S.1"] = (
    ("5 U.S.C. § 13103(d), (g)", USC_13103),
    ("the Committee on Ethics' 2025 Instruction Guide", ETHICS_GUIDE_2025),
    ("STANDARDS.md S.1", STANDARDS_S1),
)
ANSWER_WORDS[ANNUAL_VOICE] = {
    "reports": ("annual report", "annual reports"),
    "against": (
        "the latest date any extension the statute allows outside a combat zone could reach "
        f'(<a href="{USC_13103}">5 U.S.C. § 13103(d), (g)(1)</a>)'
    ),
    # "A Member, Delegate or Resident Commissioner": the reader this reaches in a territory is on
    # a Delegate's page, and § 13101 counts them (the Council's second reading, Seat F).
    "rule": (
        "The rule: a Member, Delegate or Resident Commissioner (5 U.S.C. § 13101) who serves "
        "more than 60 days in a year files an annual financial disclosure report for it by 15 "
        "May of the next year, or the next business day, and outside a combat zone extensions "
        "may add at most 90 days in total. This Signal reads only the report's date, not what "
        "the report lists."
    ),
}
# The Signal's own reasons, as its implementation writes them into the run record.
ANNUAL_WITHIN = "after the original due date, within the time an extension may cover"
ANNUAL_DAY_AFTER = (
    "the day after the latest date, and the register has not established the time zone of the "
    "printed date"
)
ANNUAL_DATES_DISAGREE = "the index date, the printed filing date and the signature date disagree"
ANNUAL_NO_DATE = "a date the register cannot read"
# Why the register did not compare a report, in its own voice: what it did not do, never what
# the rule does not reach (the Council's second reading of the built answer, Seat B). "The
# original due date" is the Committee's own term: "its due date" came back from every language
# the Council tried as a deadline already missed (the second reading, Seats A, B, D and F).
ANNUAL_REASON_WORDS = {
    ANNUAL_WITHIN: (
        "it is dated after its original due date and on or before the latest date an extension "
        "could reach, so an extension may cover it, and the register does not decide whether one "
        "does"
    ),
    ANNUAL_DAY_AFTER: (
        "it is dated the day after the latest date an extension could reach, which the register "
        "does not evaluate, because it has not established the time zone of the printed date"
    ),
    "prints no filing year": "its header prints no filing year the register could read",
    "a filing year whose instructions the register has not read": (
        "it is for a filing year whose instructions the register has not read"
    ),
    ANNUAL_NO_DATE: (
        "one of its dates could not be read: the date the Clerk's index gives it, the Filing "
        "Date it prints, or the date its signature line gives"
    ),
    ANNUAL_DATES_DISAGREE: (
        "the date the Clerk's index gives it, the Filing Date it prints and the date its "
        "signature line gives are not the same day"
    ),
    "the roster records no swearing-in": (
        "the Clerk's roster records no swearing-in for this officeholder"
    ),
    "60 days or fewer of service in the filing year, by the swearing-in recorded": (
        "by the swearing-in the roster records, this officeholder served 60 days or fewer of "
        "the year, so the register does not compare the report"
    ),
    "a later annual report for a filing year for which the register reads an earlier one": (
        "the index lists an earlier annual report of this officeholder for the same filing year, "
        "and the register compares the earliest"
    ),
}
# When the Council read each Signal before it was first defined, and where the reading is
# recorded, for the Signal's own page (the Council's second reading, Seats D and G).
COUNCIL_READ = {
    ANNUAL_VOICE: (
        "2026-09-27",
        REPO + "docs/council/2026-09-27-the-annual-report-signal-built.md",
    ),
}


def voice(signal: dict) -> tuple[str, int]:
    return (signal["slug"], signal["version"])


def runs_in(signal_runs: list[tuple[dict, dict]], key: tuple[str, int]) -> list[tuple[dict, dict]]:
    """The runs of the Signals one voice speaks for, in the order given."""
    return [(s, r) for s, r in signal_runs if voice(s) == key]


def unvoiced(signals: list[dict]) -> list[str]:
    """Signals no voice on these pages speaks for; the render refuses them."""
    return [f"{s['slug']} version {s['version']}" for s in signals if voice(s) not in VOICES]


def annual_reason(reason: str) -> str:
    return ANNUAL_REASON_WORDS.get(
        reason, f"the register did not evaluate it, recorded as {reason}"
    )


def annual_state(outcome: dict, fired: set[str]) -> str:
    """One annual report in the drawing language of every figure here: `after` where a current
    Finding rests on it (ink), `compared` where its date was compared and is not after (dense
    dots), and `read` where the register read it and did not decide (pale dots)."""
    if outcome["filing_id"] in fired:
        return "after"
    return "compared" if outcome["evaluated"] else "read"


def one_day(outcome: dict) -> bool:
    """Whether the report has one date to draw: its three dates were read and agree."""
    return not {ANNUAL_DATES_DISAGREE, ANNUAL_NO_DATE} & set(outcome["not_evaluated"])


def served_briefly(sworn: str | None, year: int) -> bool:
    """Whether the swearing-in the roster records leaves 60 days or fewer of the filing year:
    for such an officeholder the Signal compares no report of that year, and a page that said it
    could not tell whether they filed one would imply a report owed that the rule does not ask
    for (the Council's second reading, Seats A, B, D, E and F)."""
    try:
        day = date.fromisoformat(sworn or "")
    except ValueError:
        return False
    served = (date(year, 12, 31) - max(day, date(year, 1, 1))).days + 1
    return served <= 60


def annual_sentence(
    outcome: dict, finding: dict | None, subject: str, filing: dict | None = None
) -> str:
    """What the register did with one annual report, from the run record and the Finding alone:
    the dates are the Signal's, sealed, and never recomputed here."""
    d, due, latest = (esc(outcome.get(k) or "") for k in ("filed_at", "original_due", "latest"))
    if finding:
        ev = finding["evidence"]
        return (
            f"The Clerk's index dates {subject} {d}, {ev['days_after_latest']:,} days after "
            f"{esc(ev['latest'])}, the latest date any extension the statute allows outside a "
            "combat zone could reach."
        )
    if outcome["evaluated"]:
        return f"The Clerk's index dates {subject} {d}, on or before its original due date, {due}."
    reason = next(iter(outcome["not_evaluated"]), "")
    if reason == ANNUAL_WITHIN:
        return (
            f"The Clerk's index dates {subject} {d}, after its original due date, {due}, and on "
            f"or before {latest}, the latest date any extension could reach, so an extension may "
            "cover it; the register does not decide whether one does."
        )
    if reason == ANNUAL_DAY_AFTER:
        return (
            f"The Clerk's index dates {subject} {d}, the day after {latest}, the latest date any "
            "extension could reach; the register does not evaluate that day, because it has not "
            "established the time zone of the printed date."
        )
    if reason == ANNUAL_DATES_DISAGREE and filing:
        # Every date the record gives, and none chosen as the report's own: the figure that
        # drew one gave the report a date it does not print (Seats A, E and F).
        p = filing.get("printed") or {}
        return (
            f"The Clerk's index dates {subject} {d}; the report prints "
            f"{esc(p.get('filing_date') or 'no date')} as its Filing Date and "
            f"{esc(p.get('signed_on') or 'no date')} on its signature line. These are not all "
            "the same day, so the register does not compare the report."
        )
    return (
        f"The Clerk's index dates {subject} {d}; the register did not compare it: "
        f"{annual_reason(reason)}."
    )


def headless(filings: list[dict]) -> int:
    """Documents attributed here that the register fetched and whose header printed nothing it
    could read. The Signal cannot tell whether any of them is an annual report, because it reads
    which reports are annual from each report's own header and never from the index's code."""
    return sum(
        1
        for f in filings
        if f.get("source_form_code") != "P"
        and (f.get("source") or {}).get("content_hash")
        and not f.get("printed")
    )


def annual_answer(
    signal: dict,
    outcomes: list[dict],
    findings: list[dict],
    filings: list[dict],
    held_all: int = 0,
    sworn: str | None = None,
    meta: dict | None = None,
) -> list[str]:
    """The answer's paragraphs for the annual report, in a shape that is the same for everyone:
    what the register read, then each report's date against the two dates the law sets, then the
    same two sentences as every result. A page with no annual report attributed says exactly that,
    and never that none was filed (the Council's reading, B-3, D-2, E-2, C-6, F-5)."""
    words = ANSWER_WORDS[ANNUAL_VOICE]
    year = ERA["year"]
    fired = {f["producing_filings"][0]: f for f in fired_now(findings, signal["id"])}
    by_id = {f["id"]: f for f in filings}
    unread = headless(filings)
    read_on = esc(((meta or {}).get("built_at") or "")[:10])
    if not outcomes and served_briefly(sworn, year):
        text = (
            f"By the swearing-in the Clerk's roster records, {esc(sworn)}, this officeholder "
            f"served 60 days or fewer of {year}, and the rule asks for an annual report only for "
            "a year of more than 60 days' service, so this Signal compares no annual report of "
            f"theirs for {year} against {words['against']}."
        )
    elif not outcomes:
        text = (
            "The register found no annual report to compare here, which is a fact about its own "
            "reading and matching and not about what was filed: it attributes to this "
            f"officeholder no document in the Clerk's {year} index whose own header prints it as "
            f"a member's annual report, so it compared none against {words['against']}."
            + (
                f" {unread:,} {plural(unread, 'document', 'documents')} attributed here "
                f"{plural(unread, 'prints', 'print')} no header it could read, so it cannot tell "
                f"whether {plural(unread, 'it is', 'any is')} one."
                if unread
                else ""
            )
            + (
                f" {held_all:,} {plural(held_all, 'row', 'rows')} of the index at this seat under "
                f"this surname {plural(held_all, 'is', 'are')} set aside, not attributed to this "
                "officeholder."
                if held_all
                else ""
            )
            # Dated, and with the reason a later search may find nothing: the Clerk keeps a
            # Member's reports only until six years after they leave (Seat G).
            + f' On {read_on}, <a href="{CLERK_SITE}">the Clerk\'s own search</a> listed the '
            "reports the Clerk then held. The Clerk keeps a Member's reports until six years "
            "after the Member leaves (5 U.S.C. § 13107(d)), so a later search may find none, "
            "whatever was filed."
        )
    else:
        n = len(outcomes)
        ordered = sorted(outcomes, key=lambda o: (o["filed_at"], o["filing_id"]))
        text = (
            f"The register read {n:,} {plural(n, 'annual report', 'annual reports')} in the "
            f"Clerk's {year} index that it attributes to this officeholder, "
            f"{'by its' if n == 1 else 'each by its'} own header, and read "
            f"{'its dates' if n == 1 else 'the dates of each'} against its original due date "
            f"and {words['against']}. "
            + " ".join(
                annual_sentence(
                    o,
                    fired.get(o["filing_id"]),
                    "it" if n == 1 else "one",
                    by_id.get(o["filing_id"]),
                )
                for o in ordered
            )
        )
        # The check a reader can take without a terminal (the second reading, Seat E).
        url = ((by_id.get(ordered[0]["filing_id"]) or {}).get("source") or {}).get("url")
        if n == 1 and url:
            text += (
                f' To check it, open <a href="{esc(url)}">the Clerk\'s copy</a> and read its '
                "Filing Date and the date on its signature line."
            )
    # Who decides is said once for the whole answer, and the report's dates are drawn once, in
    # the page's year figure beside every other report (answer_section); a Finding's own block
    # below carries its figure in full.
    return [
        f'<p>{text} <span class="either">{esc(FRAME)}</span></p>',
        f'<p class="rule">{words["rule"]}</p>',
    ]


def annual_quiet(outcomes: list[dict], findings: list[dict], signal_id: str) -> str:
    """Which silence, for the Signal's block on a person's page, in a few words."""
    if not outcomes:
        return (
            "No annual report is attributed to this officeholder in the register by its own "
            "header, so there was nothing to compare. That is a fact about the register's reading "
            "and matching."
        )
    fired = {f["producing_filings"][0] for f in fired_now(findings, signal_id)}

    def what(o: dict) -> str:
        state = annual_state(o, fired)
        if state == "after":
            return "a Finding rests on it, shown below"
        if state == "compared":
            return "it is dated on or before its original due date"
        return annual_reason(next(iter(o["not_evaluated"]), ""))

    if len(outcomes) == 1:
        return (
            f"It read the one annual report attributed to this officeholder: {what(outcomes[0])}."
        )
    counts: dict[str, int] = {}
    for o in outcomes:
        counts[what(o)] = counts.get(what(o), 0) + 1
    return f"It read {len(outcomes):,} annual reports attributed to this officeholder. " + " ".join(
        f"Of {c:,}, {key}." for key, c in sorted(counts.items(), key=lambda i: (-i[1], i[0]))
    )


def annual_silence(outcomes: list[dict], sworn: str | None = None) -> str:
    """The checklist's few words for the annual Signal where it did not fire."""
    if not outcomes and served_briefly(sworn, ERA["year"]):
        return (
            f"60 days or fewer of {ERA['year']} by the swearing-in recorded, so no report compared"
        )
    if not outcomes:
        return "no annual report is attributed by its own header, which says nothing about filing"
    if all(o["evaluated"] for o in outcomes):
        return (
            "the report is dated on or before its original due date"
            if len(outcomes) == 1
            else "every report is dated on or before its original due date"
        )
    if any(ANNUAL_WITHIN in o["not_evaluated"] for o in outcomes):
        return (
            "within the time an extension may cover; the register does not decide whether one does"
        )
    return "not compared, for the reason below"


EXTENSION_CODE = "X"


def held_rows_by_holder(
    rejected: list[dict], holders: list[dict], code: str = EXTENSION_CODE
) -> dict[str, list[dict]]:
    """Set-aside rows of one index code at a holder's seat under the holder's surname, by
    officeholder, split by given name as the filings line is: the rows a page lists as set aside,
    beside the ones it attributes, so what a page shows does not turn on how a name was spelled
    (the Council's second reading of the annual Signal, Seats A, B and D)."""
    at = holders_by_seat(holders)
    out: dict[str, list[dict]] = {}
    for row in rejected:
        source = row.get("source_row", {})
        if source.get("filing_type") != code:
            continue
        for holder in theirs(at.get(source.get("state_dst", "").strip(), []), source):
            out.setdefault(holder["id"], []).append(row)
    return out


def annual_notices(filings: list[dict], held: list[dict] | None = None) -> str:
    """Every row the Clerk's index lists at this seat under this surname with the code its
    extension forms carry, attributed or set aside, read or not, in the same words on every page:
    shown beside the report and deciding nothing. A list of only the notices the register could
    attribute and read made two pages with the same dates read differently according to how a
    name was spelled and whether a form was on paper (the Council's second reading, Seats A, B and
    D); a sentence resting on the join would rest on what the register failed to hold (its first
    reading)."""
    mine = sorted(
        (f for f in filings if f.get("source_form_code") == EXTENSION_CODE),
        key=lambda f: (f["filed_at"], f["id"]),
    )
    aside = sorted(
        held or [],
        key=lambda r: (iso_of(r["source_row"].get("filing_date", "")), r["source_row"]["doc_id"]),
    )
    items = []
    for f in mine:
        p = f.get("printed") or {}
        if p.get("extension_length_days") or p.get("new_due_date"):
            said = [
                f"a length of {p['extension_length_days']:,} days"
                if p.get("extension_length_days")
                else "",
                f"a new due date of {p['new_due_date']}" if p.get("new_due_date") else "",
                f"for the {p['report_type_due']}" if p.get("report_type_due") else "",
            ]
            what = "its header prints " + ", ".join(w for w in said if w)
        else:
            what = "its header could not be read, so what it grants is not listed here"
        items.append(
            "<li>Attributed to this officeholder; the Clerk's index dates it "
            f"{esc(f['filed_at'])}; {esc(what)} · "
            f'<a href="{esc(f["source"]["url"])}">the Clerk\'s copy</a></li>'
        )
    for r in aside:
        src = r["source_row"]
        url = f"{CLERK_BASE}public_disc/financial-pdfs/{src.get('year', '')}/{src['doc_id']}.pdf"
        items.append(
            "<li>Set aside under this surname, not attributed to this officeholder, and the "
            "register does not say whose it is; the Clerk's index dates it "
            f"{esc(iso_of(src.get('filing_date', '')) or src.get('filing_date', ''))} · "
            f'<a href="{esc(url)}">the Clerk\'s copy</a></li>'
        )
    n, k = len(mine), len(aside)
    lead = (
        f'<p class="quiet">The Clerk\'s index lists its extension forms under the code '
        f"{EXTENSION_CODE}; every document so coded that the register has read is one. It lists "
        f"{n:,} attributed to this officeholder, and at this seat under this surname {k:,} set "
        "aside. The register lists them as the index does; no sentence on this page rests on any "
        "of them, and nothing here says whether an extension covers a report.</p>\n"
    )
    return lead + (f'<ul class="notices">{"".join(items)}</ul>\n' if items else "")


ANNUAL_W, ANNUAL_L, ANNUAL_R = 360, 10, 10


def annual_figure(outcome: dict, state: str) -> str:
    """One annual report on a line of days, beside the two dates the law sets for it: its due
    date and the latest date any extension could reach, with the span between them screened as the
    time an extension may cover. Drawn from the run record alone, the same shape on every page
    whatever the Signal found; the mark carries the page's one drawing language (ink after, the
    half screen compared, the light screen read and not decided)."""
    filed = date.fromisoformat(outcome["filed_at"])
    due = date.fromisoformat(outcome["original_due"])
    latest = date.fromisoformat(outcome["latest"])
    start = min(filed, due) - timedelta(days=14)
    end = max(filed, latest) + timedelta(days=14)
    span = max((end - start).days, 1)
    inner = ANNUAL_W - ANNUAL_L - ANNUAL_R

    def x(day: date) -> float:
        return ANNUAL_L + (day - start).days / span * inner

    def f(v: float) -> str:
        return f"{v:.1f}".rstrip("0").rstrip(".")

    band_y, band_h, axis_y = 16, 14, 34
    parts = [
        BENDAY,
        # The time an extension may cover, bracketed and never filled: the report's own mark is
        # drawn in the light screen when the register did not decide, and a screened ground
        # would swallow it.
        f'<path class="abracket" d="M{f(x(due))} {band_y + 2} V{band_y - 2} H{f(x(latest))} '
        f'V{band_y + 2}"/>',
        f'<line class="aline" x1="{f(x(due))}" y1="{band_y - 3}" x2="{f(x(due))}" '
        f'y2="{axis_y + 3}"/>',
        f'<line class="aline" x1="{f(x(latest))}" y1="{band_y - 3}" x2="{f(x(latest))}" '
        f'y2="{axis_y + 3}"/>',
        law_tag(x(latest), 1, "90", 20),
        f'<line class="aaxis" x1="{ANNUAL_L}" y1="{axis_y}" x2="{ANNUAL_W - ANNUAL_R}" '
        f'y2="{axis_y}"/>',
    ]
    month = date(start.year, start.month, 1)
    while month <= end:
        if month > start:
            parts.append(
                f'<line class="atick" x1="{f(x(month))}" y1="{axis_y}" x2="{f(x(month))}" '
                f'y2="{axis_y + 4}"/>'
            )
        month = date(month.year + month.month // 12, month.month % 12 + 1, 1)
    parts.append(
        f'<circle class="amark {state}" cx="{f(x(filed))}" cy="{band_y + band_h / 2}" r="5"/>'
    )
    # The law's two dates under the axis, the report's own under them, so no label sits on
    # another whatever the report's date (a report two days after the latest date included).
    for day, y, cls in ((due, axis_y + 13, "alaw"), (latest, axis_y + 13, "alaw")):
        parts.append(
            f'<text class="{cls}" x="{f(x(day))}" y="{y}" text-anchor="middle">'
            f"{esc(day.isoformat())}</text>"
        )
    anchor = (
        "start" if x(filed) < ANNUAL_W * 0.2 else "end" if x(filed) > ANNUAL_W * 0.8 else "middle"
    )
    # The report's own date, unless it is one of the law's two, which are printed already.
    if filed not in (due, latest):
        parts.append(
            f'<text class="afiled" x="{f(x(filed))}" y="{axis_y + 26}" text-anchor="{anchor}">'
            f"{esc(filed.isoformat())}</text>"
        )
    height = axis_y + 31
    words = {
        "after": "after the latest date",
        "compared": "on or before its original due date",
        "read": "read, and the register does not decide whether an extension covers it",
    }[state]
    label = (
        f"The date the Clerk's index gives the report, {filed.isoformat()}, {words}; original due "
        f"date {due.isoformat()}; the latest date any extension could reach, {latest.isoformat()}."
    )
    cap = "annual-" + re.sub(r"[^a-z0-9]+", "-", outcome["filing_id"].lower()).strip("-")
    # The marks are named by how they look, not as "screened", which came back from translation
    # as "examined" (the Council's second reading, Seat F).
    caption = (
        "The date the Clerk's index gives the report (the dot, with its date below) and the two "
        f"dates the law sets for it: its original due date, {esc(due.isoformat())}, and, marked "
        f"90, the latest date any extension could reach, {esc(latest.isoformat())}. The bracket "
        "between them is the time an extension may cover. The dot is solid ink where the report "
        "is dated after the latest date, densely dotted where it is dated on or before its "
        "original due date, and pale dotted where the register read it and does not decide "
        "whether an extension covers it. A tick marks the first of each month. The figure shows "
        "dates. It does not show whether an extension was granted, or anything the House "
        "Committee on Ethics has determined."
    )
    return (
        f'<figure class="annual">\n<svg viewBox="0 0 {ANNUAL_W} {height}" direction="ltr" '
        f'role="img" aria-label="{esc(label)}" aria-describedby="{cap}">'
        + "".join(parts)
        + f'</svg>\n<figcaption id="{cap}">{caption}</figcaption>\n</figure>'
    )


def annual_finding_block(
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
    evidence = finding.get("evidence", {})
    drawn = (
        annual_figure(
            {
                "filing_id": finding["producing_filings"][0],
                "filed_at": evidence["filed_at"],
                "original_due": evidence["original_due"],
                "latest": evidence["latest"],
            },
            "after",
        )
        if evidence.get("filed_at") and evidence.get("original_due") and evidence.get("latest")
        else ""
    )
    return (
        f'<article class="finding" id="finding-{esc(doc_id)}">\n'
        f"<h4>Annual report the Clerk's index dates {esc(finding['evidence']['filed_at'])}"
        f"{copy}</h4>\n"
        f"<p>{esc(finding['description'])}</p>\n"
        f"{drawn}\n"
        f"{finding_changes(finding, changes)}"
        f"{correction_line(finding, findings or [])}"
        f'<p class="quiet">Finding <code>{esc(finding["id"])}</code>, first produced from the '
        f"record as retrieved {esc(finding['fired_at'])}, from rows whose digest is "
        f"<code>{esc(finding['build_hash'][:12])}</code>. Regenerate it from the rows it names: "
        f"<code>python tools/rebuild.py {esc(finding['id'])}</code></p>\n"
        "</article>"
    )


def annual_counts(outcomes: list[dict], findings: list[dict], signal_id: str) -> dict[str, int]:
    """The chamber's annual reports by what the Signal did with each, from its run record."""
    fired = {f["producing_filings"][0] for f in fired_now(findings, signal_id)}
    counts = {"after": 0, "compared": 0, "within": 0, "day after": 0, "other": 0}
    for o in outcomes:
        state = annual_state(o, fired)
        if state != "read":
            counts[state] += 1
        elif ANNUAL_WITHIN in o["not_evaluated"]:
            counts["within"] += 1
        elif ANNUAL_DAY_AFTER in o["not_evaluated"]:
            counts["day after"] += 1
        else:
            counts["other"] += 1
    return counts


ANNUAL_KEY = (
    ("compared", "compared", "dated on or before the original due date"),
    (
        "within",
        "read",
        "dated after the original due date and within the time an extension may cover; the "
        "register does not decide whether one does",
    ),
    (
        "day after",
        "read",
        "dated the day after the latest date, which the register does not evaluate, because it "
        "has not established the time zone of the printed date",
    ),
    ("other", "read", "not compared, each for a reason its officeholder's page gives"),
    (
        "after",
        "after",
        "dated after the latest date any extension the statute allows outside a combat zone "
        "could reach",
    ),
)


def annual_bins(due: date, latest: date, first: date, last: date) -> list[tuple[date, date]]:
    """Weeks of days, as (first day, last day), whose edges fall on the two dates the law sets:
    seven-day weeks ending on the due date before it, seven-day weeks from the day after it to
    the latest date (the last one shorter where ninety days do not divide by seven), and weeks
    from the day after the latest date on. So no column holds a report on both sides of a line
    the law draws, and a column is wide enough for its screen to read."""
    bins = []
    end = due
    while end >= first:
        bins.insert(0, (end - timedelta(days=6), end))
        end -= timedelta(days=7)
    day = due + timedelta(days=1)
    while day <= latest:
        bins.append((day, min(day + timedelta(days=6), latest)))
        day += timedelta(days=7)
    day = latest + timedelta(days=1)
    while day <= last:
        bins.append((day, day + timedelta(days=6)))
        day += timedelta(days=7)
    return bins


def annual_drawn(outcomes: list[dict]) -> list[dict]:
    """The reports one chamber figure can draw: those of the earliest filing year whose two dates
    the Signal wrote, all of which share them."""
    dated = [o for o in outcomes if o.get("original_due") and o.get("latest") and one_day(o)]
    if not dated:
        return []
    due = min(o["original_due"] for o in dated)
    return [o for o in dated if o["original_due"] == due]


def annual_chart(
    outcomes: list[dict], findings: list[dict], signal_id: str, meta: dict | None
) -> str:
    """Every annual report the Signal read, one column a week by the date the Clerk's index gives
    it, each column stacked by what the Signal did with its reports, between the two lines the
    law draws: the due date and the latest date any extension could reach. The weeks break on
    those two dates. The span between them is bracketed and never filled, because the reports in
    it are drawn in the light screen and a screened ground would swallow them."""
    fired = {f["producing_filings"][0] for f in fired_now(findings, signal_id)}
    drawn = annual_drawn(outcomes)
    if not drawn:
        return ""
    due = date.fromisoformat(drawn[0]["original_due"])
    latest = date.fromisoformat(drawn[0]["latest"])
    days = sorted(date.fromisoformat(o["filed_at"]) for o in drawn)
    bins = annual_bins(
        due,
        latest,
        min(days[0], due - timedelta(days=27)),
        max(days[-1], latest + timedelta(days=14)),
    )
    start, end = bins[0][0], bins[-1][1]
    span = (end - start).days + 1
    w, left, right, top, base = 360, 8, 8, 30, 132
    step = (w - left - right) / span
    counts_in: list[dict[str, int]] = [{} for _ in bins]
    for o in drawn:
        day = date.fromisoformat(o["filed_at"])
        i = next(k for k, (a, b) in enumerate(bins) if a <= day <= b)
        state = annual_state(o, fired)
        counts_in[i][state] = counts_in[i].get(state, 0) + 1
    tallest = max((sum(c.values()) for c in counts_in), default=1)
    unit = (base - top - 4) / max(tallest, 1)

    def x(day: date) -> float:
        return left + (day - start).days * step

    def f(v: float) -> str:
        return f"{v:.1f}".rstrip("0").rstrip(".")

    parts = []
    for (a, b), states in zip(bins, counts_in, strict=True):
        x0, x1 = x(a) + 0.6, x(b + timedelta(days=1)) - 0.6
        # Stacked from just above the axis's own ink, and never under four units tall, so a
        # column of one report is a mark and not a thickening of the axis (Seat E).
        y = base - 1.6
        for state in ("compared", "read", "after"):
            n = states.get(state, 0)
            if not n:
                continue
            h = max(n * unit, 4)
            parts.append(
                f'<rect class="acol {state}" x="{f(x0)}" y="{f(y - h)}" width="{f(x1 - x0)}" '
                f'height="{f(h)}"/>'
            )
            y -= h
    # The two lines the law draws, at the end of the due date and of the latest date, and the
    # bracket between them for the time an extension may cover.
    xd, xl = x(due + timedelta(days=1)), x(latest + timedelta(days=1))
    for cx in (xd, xl):
        parts.append(
            f'<line class="aline" x1="{f(cx)}" y1="{top - 12}" x2="{f(cx)}" y2="{base + 3}"/>'
        )
    parts.append(f'<path class="abracket" d="M{f(xd)} {top - 2} V{top - 6} H{f(xl)} V{top - 2}"/>')
    parts.append(law_tag(xd, 2, f"{due.day} {due.strftime('%b')}", 34))
    parts.append(law_tag(xl, 2, "+90", 22))
    parts.append(f'<line class="aaxis" x1="{left}" y1="{base}" x2="{w - right}" y2="{base}"/>')
    month = date(start.year, start.month, 1)
    while month <= end:
        if month > start:
            mx = x(month)
            parts.append(
                f'<line class="atick" x1="{f(mx)}" y1="{base}" x2="{f(mx)}" y2="{base + 4}"/>'
            )
            parts.append(
                f'<text class="amonth" x="{f(mx + 2)}" y="{base + 12}">'
                f"{esc(month.strftime('%b'))}</text>"
            )
        month = date(month.year + month.month // 12, month.month % 12 + 1, 1)
    height = base + 30
    stamp = figure_stamp(meta, left, w - right, base + 23)
    counts = annual_counts(drawn, findings, signal_id)
    label = (
        f"{len(drawn):,} annual reports, one column a week from {start.isoformat()} to "
        f"{end.isoformat()}: "
        + "; ".join(f"{counts[k]:,} {words}" for k, _cls, words in ANNUAL_KEY)
        + "."
    )
    return (
        f'<svg class="annualchart" viewBox="0 0 {w} {height}" role="img" '
        f'aria-label="{esc(label)}" direction="ltr">' + "".join(parts) + stamp + "</svg>"
    )


def annual_key(counts: dict[str, int]) -> str:
    lines = []
    for key, cls, words in ANNUAL_KEY:
        swatch = (
            '<svg class="key" viewBox="0 0 12 12" aria-hidden="true" focusable="false">'
            f'<rect class="acol {cls}" x="1" y="1" width="10" height="10"/></svg>'
        )
        lines.append(f"<li>{swatch} <b>{counts.get(key, 0):,}</b> {esc(words)}</li>")
    return '<ul class="squarekey">' + "".join(lines) + "</ul>\n"


def annual_reach(outcomes: list[dict], filings: list[dict], holders: list[dict]) -> dict:
    """Whom the annual Signal cannot reach, counted apart so no quiet is told as another: the
    officeholders with no annual report attributed who served the year and those the roster's
    swearing-in leaves 60 days or fewer of it (the Council's second reading, Seats A, B, D, E and
    F), and the documents with no readable header, split by whether the index gives them the code
    every annual report read so far carries."""
    year = ERA["year"]
    attributed = {o["officeholder_id"] for o in outcomes}
    quiet = [h for h in holders if h["id"] not in attributed]
    brief = sum(1 for h in quiet if served_briefly(h.get("sworn_at"), year))
    blind = [
        f
        for f in filings
        if f.get("source_form_code") != "P"
        and (f.get("source") or {}).get("content_hash")
        and not f.get("printed")
    ]
    coded = sum(1 for f in blind if f.get("source_form_code") == "O")
    unfetched = sum(
        1
        for f in filings
        if f.get("source_form_code") != "P" and not (f.get("source") or {}).get("content_hash")
    )
    return {
        "without": len(quiet) - brief,
        "brief": brief,
        "headless": len(blind),
        "headless_o": coded,
        "unfetched": unfetched,
    }


NAME_MATCH_WORDS = (
    "It cannot see a report the index sets aside under a sitting member's surname because the "
    "given names differ or the index prints another seat: such a row waits for the maintainer to "
    "decide by hand, citing the evidence, and a report among them is on no page's result until "
    "then."
)


def annual_section(
    signal_runs: list[tuple[dict, dict]],
    outcomes_all: dict[str, list[dict]],
    findings: list[dict],
    filings: list[dict],
    holders: list[dict],
    meta: dict | None = None,
) -> str:
    """The annual report, for the chamber: the one figure that says where every annual report the
    register read falls against the two dates the law sets, and what the register did not decide.
    The window is drawn as read and not decided, never as compared, because an extension the
    register cannot see may cover every report in it; drawing them as checked would be the
    falsehood that flatters, and drawing them as after would be the one that condemns."""
    parts = []
    year = ERA["year"]
    for signal, _summary in signal_runs:
        outcomes = outcomes_all.get(signal["id"], [])
        chart = annual_chart(outcomes, findings, signal["id"], meta)
        if not chart:
            continue
        drawn = annual_drawn(outcomes)
        counts = annual_counts(drawn, findings, signal["id"])
        undrawn = len(outcomes) - len(drawn)
        named = len({f["officeholder_id"] for f in fired_now(findings, signal["id"])})
        r = annual_reach(outcomes, filings, holders)
        parts.append(
            '<figure class="annualchart">\n'
            + chart
            + "\n<figcaption>Every annual report the register read by its own header, one column "
            "a week by the date the Clerk's index gives it, stacked by what the Signal did with "
            "its reports; the weeks break on the two lines the law draws. The line marked 15 May "
            "is the original due date, and the line marked +90 the latest date any extension the "
            "statute allows could reach; the bracket between them is the time an extension may "
            "cover. It counts reports and not people, and nothing in it is ordered by anything "
            "about a person.</figcaption>\n</figure>\n"
            + annual_key(counts)
            + (
                f'<p class="quiet">{undrawn:,} more {plural(undrawn, "report", "reports")}, of '
                "another filing year, or whose dates disagree or could not be read, "
                f"{plural(undrawn, 'is', 'are')} not drawn; each is on its officeholder's "
                "page.</p>\n"
                if undrawn
                else ""
            )
            + (
                f"<p>The {counts['after']:,} {plural(counts['after'], 'report', 'reports')} "
                f"after the latest date {plural(counts['after'], 'is', 'are')} by {named:,} "
                f"{plural(named, 'member', 'members')}. Each is on that member's page, with its "
                f'dates drawn: <a href="{signal_page_path(signal)}">the {named:,} '
                f"{plural(named, 'member', 'members')}, in seat order</a>.</p>\n"
                if counts["after"] and named
                else ""
            )
            + f'<p class="quiet">For {r["without"] + r["brief"]:,} of the {len(holders):,} '
            "officeholders the register holds, it attributes no annual report by the report's own "
            "header, and each of their pages says which quiet it is: for "
            f"{r['brief']:,} of them, the swearing-in the roster records leaves 60 days or fewer "
            f"of {year}, for which the rule asks no annual report; for the other "
            f"{r['without']:,}, the page gives the rows set aside at the seat and a link to the "
            "Clerk's own search, and this Signal says nothing about whether they filed one."
            + (
                f" {r['headless']:,} more {plural(r['headless'], 'document', 'documents')} "
                f"attributed to members {plural(r['headless'], 'prints', 'print')} no header the "
                f"register could read, among them any report filed on paper; {r['headless_o']:,} "
                f"of them carry the index code O, which every annual report whose header it read "
                "carries. This Signal cannot reach them."
                if r["headless"]
                else ""
            )
            + f" {esc(FRAME)}</p>\n"
        )
    if not parts:
        return ""
    return (
        '<section class="annual" id="annual">\n'
        '<h2><span class="tag">The annual report, against the latest date an extension could '
        "reach</span></h2>\n" + "".join(parts) + "</section>"
    )


def annual_record_line(
    signal: dict, summary: dict, outcomes: list[dict], findings: list[dict]
) -> str:
    """The annual Signal's line in the landing's numbers about the register."""
    counts = annual_counts(outcomes, findings, signal["id"])
    read = summary.get("reports", 0)
    fired = summary["reports_with_a_finding"]
    waiting = counts["within"] + counts["day after"]
    return (
        f"<dt>{fired:,}</dt><dd>of the {read:,} annual reports read by their own header, on which "
        f'the signal <a href="{signal_page_path(signal)}">{esc(signal["name"])}</a>, version '
        f"{signal['version']}, fired: dated after the latest date any extension the statute allows "
        f"could reach, on reports attributed to {summary['officeholders_with_a_finding']:,} "
        f"officeholders. {counts['compared']:,} {plural(counts['compared'], 'is', 'are')} dated "
        f"on or before the original due date; {waiting:,} {plural(waiting, 'is', 'are')} within "
        "the time an extension may cover, or the day after it, and the register does not decide "
        f"whether an extension covers {plural(waiting, 'it', 'them')}; {counts['other']:,} "
        f"{plural(counts['other'], 'was', 'were')} not compared, "
        f"{plural(counts['other'], 'with its reason', 'each with a reason')}. A count about the "
        f"register; no page ranks anyone by it{bar(fired, read)}</dd>\n"
    )


def annual_signal_record(
    summary: dict,
    outcomes: list[dict],
    findings: list[dict],
    signal: dict,
    filings: list[dict],
    holders: list[dict],
) -> str:
    """What the annual Signal did in this build, and whom it cannot reach, for its own page."""
    counts = annual_counts(outcomes, findings, signal["id"])
    reasons: dict[str, int] = {}
    for o in outcomes:
        for reason, n in o["not_evaluated"].items():
            if reason not in (ANNUAL_WITHIN, ANNUAL_DAY_AFTER):
                reasons[reason] = reasons.get(reason, 0) + n
    other = "; ".join(
        f"{n:,} where {annual_reason(r)}"
        for r, n in sorted(reasons.items(), key=lambda i: (-i[1], i[0]))
    )
    r = annual_reach(outcomes, filings, holders)
    year = ERA["year"]
    withdrawn = len(withdrawn_now(findings, signal["id"]))
    read = COUNCIL_READ.get(voice(signal))
    return (
        '<section class="record">\n<h2>What it did in this build</h2>\n<dl>\n'
        + (
            f"<dt>{esc(read[0])}</dt><dd>the day the Council's seven seats closed their reading of "
            f'this version, built, before it was first defined: <a href="{esc(read[1])}">the '
            "record</a>. It publishes in the first sealed build after that reading, on the "
            "register's regular Monday cadence, whatever the calendar</dd>\n"
            if read
            else ""
        )
        + f"<dt>{summary.get('reports', 0):,}</dt><dd>annual reports read by their own header, "
        f"and fired on {summary['reports_with_a_finding']:,} of them"
        f"{bar(summary['reports_with_a_finding'], summary.get('reports', 0))}</dd>\n"
        f"<dt>{counts['compared']:,}</dt><dd>dated on or before the original due date</dd>\n"
        f"<dt>{counts['within']:,}</dt><dd>dated after the original due date and within the time "
        "an extension may cover; the register does not decide whether one does</dd>\n"
        f"<dt>{counts['day after']:,}</dt><dd>dated the day after the latest date, which it does "
        "not evaluate, because it has not established the time zone of the printed date</dd>\n"
        f"<dt>{counts['other']:,}</dt><dd>not compared: {esc(other) or 'none'}</dd>\n"
        f"<dt>{r['headless']:,}</dt><dd>documents attributed to members that the register "
        "fetched and whose header printed nothing it could read, among them any report filed on "
        f"paper ({r['headless_o']:,} carry the index code O, which every annual report whose "
        "header it read carries): the Signal reads which reports are annual from each report's "
        "own header, so it cannot reach these</dd>\n"
        f"<dt>{r['unfetched']:,}</dt><dd>documents attributed to members that the register has "
        "not fetched: it fetches those the index lists under the codes P, O and X, which is a "
        "choice of what to fetch, and reads which of them are annual reports from each one's own "
        "header</dd>\n"
        f"<dt>{r['without']:,}</dt><dd>officeholders who served more than 60 days of {year} by "
        "the roster's swearing-in, to whom the register attributes no annual report by the "
        "report's own header; each of their pages says so, with the rows set aside at the seat "
        "and a link to the Clerk's own search, and this Signal says nothing about whether they "
        "filed one</dd>\n"
        f"<dt>{r['brief']:,}</dt><dd>officeholders whose swearing-in the roster records leaves "
        f"60 days or fewer of {year}, for which the rule asks no annual report; each of their "
        "pages says so</dd>\n"
        f"<dt>{summary['officeholders_with_a_finding']:,}</dt><dd>officeholders the reports it "
        "fired on are attributed to. A count about the register; no page ranks anyone by it</dd>\n"
        + (
            f"<dt>{withdrawn:,}</dt><dd>Findings it once produced and a correction withdrew; each "
            "stays in the ledger with its reason, and on its officeholder's page</dd>\n"
            if withdrawn
            else ""
        )
        + f'</dl>\n<p class="quiet">{esc(NAME_MATCH_WORDS)}</p>\n</section>'
    )


# ---- the directory and the apparatus: each its own page ---------------------------------


def inner_head(kicker: str, title: str, lede: str = "") -> str:
    """The header every page but the landing opens with: the frame first, then the page's own
    name. The frame is in the header on every surface (INVARIANTS.md §7)."""
    return (
        '<header class="frame">\n'
        f'<p class="frame">{esc(FRAME)}</p>\n'
        '<div class="masthead">\n<div>\n'
        f'<p class="kicker">{esc(kicker)}</p>\n'
        f"<h1>{esc(title)}</h1>\n"
        f"{lede}"
        "</div>\n</div>\n</header>"
    )


def roster_reading(
    holders: list[dict], offices: list[dict], changes: dict[str, list[dict]] | None
) -> tuple[dict[str, dict], dict[str, dict], list[str], list[str]]:
    """The roster as the register holds it, and the directory's rows: (the holders a later
    roster stopped listing, keyed by id; the holder at each seat; every seat; the table rows).

    One reading, three callers. The landing counts what this reads, the apparatus page states
    it, and the directory lists it, so none of the three can say a different thing about who
    the register holds at a seat."""
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
            '<span class="note">Last listed here on the roster read the register built from, '
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
                "any filing by a Member of this seat who left before the register first read the "
                "roster is among the "
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
    return off_roster, holder_by_seat, seats, rows


def seats_sections(
    holders: list[dict], off_roster: dict[str, dict], seats: list[str], rows: list[str]
) -> str:
    """Every seat in the register, and the seats a later roster stopped listing.

    The directory. It is 439 names, and it belongs on the page a reader opens to find a name,
    not in the middle of the story the landing tells: the landing showed a map and then, six
    screens down, the same chamber again as a list. One of the two was the reader's, and the
    list was not."""
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
            "<th>Last listed, roster read the register built from</th>"
            "<th>Not listed, roster read</th></tr></thead>\n"
            f"<tbody>\n{kept_rows}\n</tbody>\n</table>\n</section>"
        )
    return table


def render_seats(
    holders: list[dict],
    offices: list[dict],
    run: dict,
    meta: dict,
    changes: dict[str, list[dict]] | None = None,
) -> str:
    """The directory: every seat of this Congress, with the name the Clerk's roster gave it."""
    ERA.update(era_of(run, holders))
    off_roster, _at_seat, seats, rows = roster_reading(holders, offices, changes)
    lede = (
        f'<p class="lede">{len(seats)} seats. Choose a name to read that Member\'s page: every '
        "transaction report the register attributes to them, every trade on it, and what it "
        "could not read. Seat order is an order of offices; it says nothing about anyone.</p>\n"
    )
    body = (
        f'{inner_head("Oath · the directory", SEATS_TITLE, lede)}\n<main id="main">\n'
        f"{seats_sections(holders, off_roster, seats, rows)}\n"
        f"</main>\n{footer(meta, home=False, to_root='')}"
    )
    return page(SEATS_TITLE, body)


def render_record(
    meta: dict,
    run: dict,
    holders: list[dict],
    filings: list[dict],
    offices: list[dict],
    held_rows: int | dict = 0,
    rejected_url: str = REPO + "data/rejected/house-fd/",
    transactions: list[dict] | None = None,
    signal_runs: list[tuple[dict, dict]] | None = None,
    reach: dict[str, dict[str, int]] | None = None,
    changes: dict[str, list[dict]] | None = None,
    outcomes_all: dict[str, list[dict]] | None = None,
    findings: list[dict] | None = None,
) -> str:
    """The apparatus: what this build holds, how a fact here gets corrected, and what every
    term on the pages means.

    This is the register describing itself, and it used to be two thirds of the landing's
    words. A reader who wants it should be able to open it; a reader who came to find their
    representative should not have to walk through it. Nothing is cut: every sentence that was
    on the landing is here, under a heading, on a page linked from the landing's foot. So is the
    House at a glance, one square per report, which left the landing when the deadline figure
    came to answer its question better (NEXT.md P.6)."""
    ERA.update(era_of(run, holders))
    _off_roster, at_seat, _seats, _rows = roster_reading(holders, offices, changes)
    lede = (
        '<p class="lede">What this build holds, how each number was arrived at, what the '
        "register could not read, how to get a fact here corrected, and what every term on "
        "these pages means. Nothing here is about a person.</p>\n"
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
        len(at_seat),
        outcomes_all,
        findings,
    )
    glance = glance_section(
        runs_in(signal_runs or [], PTR_VOICE), outcomes_all or {}, findings or [], "index.html"
    )
    body = (
        f'{inner_head("Oath · the apparatus", RECORD_TITLE, lede)}\n<main id="main">\n'
        f"{record}\n{glance}\n{disputes_section(False)}\n{how_to_read(False)}\n"
        f"</main>\n{footer(meta, home=False, to_root='')}"
    )
    return page(RECORD_TITLE, body)


# ---- closing the loop: what the register would need ------------------------------------------

WANTED_ROWS = "docs/wanted/wanted.ndjson"
WANTED_PAGE = "closing-the-loop.html"
WANTED_TITLE = "What would close the loop"
# The chain, left to right, and which of its links this register can read. The first four are
# dates in the Clerk's index; the last three are what follows a report, and the register holds
# no row about any of them. The break between them is the figure.
# One word a link: at seven links across 360 units a label has 44 units, and "the deadline"
# needs 46. The article goes, not the link.
LOOP = (
    ("trade", True, None),
    ("notice", True, None),
    ("report", True, None),
    ("deadline", True, "the-date"),
    ("fee", False, "the-fee"),
    ("review", False, "the-review"),
    ("court", False, "the-courts"),
)
# Each part of the loop, in the order a reader meets it, and the heading it is published under.
# tools/check-wanted.py writes the same keys on its own and refuses a row whose key is not here.
WANTED_GROUPS = (
    ("the-date", "The date every sentence here rests on"),
    ("the-fee", "The fee the rule itself sets"),
    ("the-review", "Whether anyone looked"),
    ("the-courts", "What happens outside the chamber"),
    ("the-shut-door", "The door that may not open"),
)
PUBLICNESS = {
    "published": "published",
    "obtainable": "obtainable",
    "not public": "not public",
    "unknown": "nobody here has looked yet",
}


def load_wanted(root: Path) -> list[dict]:
    """The wanted register, or nothing. It is not sealed with the build, so a checkout may not
    carry it and the page it feeds is simply not written."""
    path = root / WANTED_ROWS
    return read_ndjson(path) if path.is_file() else []


def loop_chain(rows: list[dict]) -> str:
    """The loop as a chain of seven links, broken where this register stops.

    The first four links are dates the Clerk's index carries and the register reads. The last
    three are what follows a report, and the register holds no row about any of them, so they are
    drawn open, in the same outline this page uses everywhere for *nothing here*. The break is the
    figure: a chain is the one picture where a missing link needs no caption."""
    w, link_w, link_h, overlap = 360, 52.0, 24.0, 8.0
    gap, top = 16.0, 30.0
    counts: dict[str, int] = {}
    for r in rows:
        counts[r["closes"]] = counts.get(r["closes"], 0) + 1
    span = len(LOOP) * link_w - (len(LOOP) - 1) * overlap + gap
    x = (w - span) / 2
    parts = []
    for i, (label, held, key) in enumerate(LOOP):
        if i and LOOP[i - 1][1] is not held:
            x += gap
        parts.append(
            f'<rect class="link {"held" if held else "open"}" x="{x:.1f}" y="{top}" '
            f'width="{link_w}" height="{link_h}" rx="{link_h / 2:.1f}"/>'
        )
        mid = x + link_w / 2
        parts.append(
            f'<text x="{mid:.1f}" y="{top + link_h + 12}" text-anchor="middle">{label}</text>'
        )
        if key and not held:
            n = counts.get(key, 0)
            parts.append(
                f'<text class="lct" x="{mid:.1f}" y="{top + link_h + 24}" text-anchor="middle">'
                f"{n} wanted</text>"
            )
        x += link_w - overlap
    held_to = (w - span) / 2 + 4 * link_w - 3 * overlap
    parts.append(
        f'<line class="lbrace" x1="{(w - span) / 2:.1f}" y1="{top - 8}" x2="{held_to:.1f}" '
        f'y2="{top - 8}"/>'
    )
    parts.append(
        f'<text x="{((w - span) / 2 + held_to) / 2:.1f}" y="{top - 12}" text-anchor="middle">'
        "what this register reads</text>"
    )
    parts.append(f'<text x="{w - 6}" y="{top - 12}" text-anchor="end">what follows a report</text>')
    return (
        f'<svg class="loop" viewBox="0 0 {w} {top + link_h + 32:.0f}" direction="ltr" '
        'aria-hidden="true" focusable="false">' + "".join(parts) + "</svg>"
    )


def wanted_row(row: dict) -> str:
    """One wanted piece, in the shape a reader reads it: the question, what the register can say
    without it, what it could say with it, and then the apparatus."""
    lines = [
        ("Today", row["today"]),
        ("With it", row["with_it"]),
        ("Who holds it", row["holder"]),
        ("How it would be got", row["route"]),
    ]
    if row.get("joins_on"):
        lines.append(
            (
                "What it would join on",
                f"{row['joins_on']}, which every report here carries.",
            )
        )
    else:
        lines.append(
            (
                "What it would join on",
                "Nothing known. A record naming a member and a period does not name a report, "
                "and joining one to the other would be an inference published against a named "
                "person, which this register does not do.",
            )
        )
    if not row["verified"]:
        lines.append(("What to read to settle it", row["check"]))
    body = "\n".join(f"<dt>{esc(term)}</dt><dd>{esc(text)}</dd>" for term, text in lines)
    seen = "read at its source" if row["verified"] else "not read at any source by this project"
    links = "".join(
        f' <a href="{esc(c["url"])}">{esc(c["what"])}</a>;'
        if c.get("url")
        else f" {esc(c['what'])};"
        for c in row.get("candidates") or []
    ).rstrip(";")
    where = (
        f'<p class="quiet">Where it might be: {links}. {esc(seen.capitalize())}.</p>\n'
        if links
        else f'<p class="quiet">{esc(seen.capitalize())}.</p>\n'
    )
    return (
        f'<div class="want" id="{esc(row["id"])}">\n'
        f"<h3>{esc(row['question'])}</h3>\n"
        f'<p class="tags"><span class="tag2">{esc(PUBLICNESS[row["publicness"]])}</span>'
        f'<span class="tag2">one row per {esc(row["unit"].replace("-", " "))}</span>'
        f"<code>{esc(row['id'])}</code></p>\n"
        f"<dl>\n{body}\n</dl>\n{where}</div>"
    )


def render_closing(rows: list[dict], run: dict, holders: list[dict], meta: dict) -> str:
    """The register of what this register does not have.

    Every other page here says what the record holds. This one says, piece by piece, what would
    have to exist and be readable before the register could follow a report past its deadline to
    whatever followed it. It is a register and not an essay because the difference matters: a row
    has an id, a row says what to read to settle it, a row can close, and a row is never deleted.

    It asks for nothing. Naming what is missing is not the same as claiming it is being kept back,
    and twelve of these rows say plainly that nobody here has looked yet."""
    ERA.update(era_of(run, holders))
    open_rows = [r for r in rows if not r.get("closed")]
    verified = sum(1 for r in rows if r["verified"])
    lede = (
        '<p class="lede">The register can follow a trade to the day the Clerk\'s index dates the '
        "report that carries it, and read that against the deadline. Then it stops. This is every "
        "piece of official information it would need to carry on, one row each, with what it "
        "could say if it had it and what to read to find out whether it exists.</p>\n"
    )
    groups, nav = [], []
    for key, heading in WANTED_GROUPS:
        here = [r for r in rows if r.get("closes") == key]
        if here:
            nav.append(f'<li><a href="#{esc(key)}">{esc(heading)}</a> ({len(here)})</li>')
    for key, heading in WANTED_GROUPS:
        here = [r for r in rows if r.get("closes") == key]
        if not here:
            continue
        groups.append(
            f'<section class="wants" id="{esc(key)}">\n<h2>{esc(heading)}</h2>\n'
            + "\n".join(wanted_row(r) for r in here)
            + "\n</section>"
        )
    figure = (
        '<section class="loop">\n<h2><span class="tag">The loop, and where it breaks</span></h2>\n'
        '<figure class="loop">\n'
        + loop_chain(rows)
        + "\n<figcaption>The seven stages of a reported trade. The register reads the first four, "
        "because the Clerk publishes them: the trade, the notice the filer prints, the report, and "
        "the deadline the rule sets. It holds no row about any of the last three. They are drawn "
        "open because on these pages an outline means the register has nothing, and the count "
        "under each is the number of pieces below that would fill it; "
        f"{sum(1 for r in rows if r.get('closes') == 'the-shut-door')} more are about why the "
        "break is there at all. The break is not a claim that anything is being kept back; it is "
        "where this project's own reading stops.</figcaption>\n</figure>\n</section>"
    )
    counted = (
        f"<section>\n<h2>How to read this list</h2>\n"
        f"<p>{len(rows):,} {plural(len(rows), 'piece', 'pieces')}, {len(open_rows):,} still open. "
        f"{verified:,} of them {plural(verified, 'has', 'have')} been read at a source by this "
        f"project; the rest say <em>nobody here has looked yet</em>, which is the honest state and "
        "not a finding about anyone. A row saying a thing is published, obtainable or not public "
        "when nobody here has read it is refused by "
        f'<a href="{REPO}tools/check-wanted.py">the gate that keeps this file</a>, because '
        "believing a thing is public is not knowing it.</p>\n"
        f'<p>The rows are data: <a href="{REPO}{WANTED_ROWS}">{esc(WANTED_ROWS)}</a>, one JSON '
        f'object a line, under <a href="{REPO}schemas/wanted.schema.json">a schema</a>. A piece '
        "that stops being wanted is marked closed and stays; nothing here is deleted. If you know "
        "the answer to one of these, or where to read it, "
        f'<a href="{CORRECTION_FORM}">the same route that corrects a fact</a> opens a row.</p>\n'
        "</section>"
    )
    body = (
        f'{inner_head("Oath · what is missing", WANTED_TITLE, lede)}\n<main id="main">\n'
        f"{figure}\n"
        + (f'<nav class="parts"><ul>{"".join(nav)}</ul></nav>\n' if nav else "")
        + "\n".join(groups)
        + f"\n{counted}\n"
        f"</main>\n{footer(meta, home=False, to_root='')}"
    )
    return page(WANTED_TITLE, body)


def render_index(
    holders: list[dict],
    offices: list[dict],
    filings: list[dict],
    run: dict,
    meta: dict,
    striker,
    transactions: list[dict] | None = None,
    signal_runs: list[tuple[dict, dict]] | None = None,
    changes: dict[str, list[dict]] | None = None,
    outcomes_all: dict[str, list[dict]] | None = None,
    findings: list[dict] | None = None,
) -> str:
    """The landing: the record, told in pictures.

    It used to carry the directory of 439 names and the register's whole account of itself, and
    those were two thirds of its words. Both have their own page now, linked from the foot. What
    is left is one story a reader can follow without being taught anything first: a map to their
    own representative, the rule in four panels, the deadline and the trades on each side of it,
    the one date the filer writes, what the register could not reach, and where the record ends.
    Every figure carries its caption; the captions are where the words went. The chamber's
    reports as squares, one per report, are on the record page (NEXT.md P.6).
    """
    ERA.update(era_of(run, holders))
    off_roster, _at_seat, _seats, _rows = roster_reading(holders, offices, changes)
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
        '<h1 class="comic" data-text="Oath">Oath</h1>\n'
        f"{ended}"
        + (
            # Both deadlines once the annual report is read against its own, in the same words
            # and the same place: the lede said one, and 399 rows of the page were read against
            # the other (the second reading of the annual Signal, Seat E). The mark is unchanged.
            '<p class="lede">Every member of the U.S. House swore an oath. The law adds '
            "deadlines: report a stock trade within 45 days, sooner if you learned of it sooner, "
            "and file each year's financial disclosure report by 15 May of the next.</p>\n"
            f'<p class="quiet">This page sets the second beside the first for '
            f"{esc(congress_words(terms=True))}: each row of the Clerk's {ERA['year']} filing "
            "index the register could match to a name on the Clerk's roster, read against the "
            "deadline the law sets for it and linked to the Clerk's own copy. It draws no "
            "conclusion about anyone.</p>\n"
            if runs_in(signal_runs or [], ANNUAL_VOICE)
            else '<p class="lede">Every member of the U.S. House swore an oath. The law adds a '
            "deadline: report a stock trade within 45 days, sooner if you learned of it "
            "sooner.</p>\n"
            f'<p class="quiet">This page sets the second beside the first for '
            f"{esc(congress_words(terms=True))}: each row of the Clerk's {ERA['year']} filing "
            "index the register could match to a name on the Clerk's roster, read against that "
            "deadline and linked to the Clerk's own copy. It draws no conclusion about "
            "anyone.</p>\n"
        )
        + "</div>\n"
        + seal_figure(
            mark,
            "Struck from this build's own digest, so the mark changes when the record changes. "
            "Every officeholder page carries its own.",
        )
        + "\n</div>\n</header>"
    )
    # The doors out, at the foot, where a reader who has read the page is ready for them. They
    # used to sit in the second screen, ahead of any reason to want them.
    door = (
        '<section class="door" id="more">\n<h2>Where to go next</h2>\n'
        f'<div><p><a href="{SEATS_PAGE}">Every seat in the register</a></p><p>All '
        f"{len(offices)} seats, in seat order; each name is a Member's page.</p></div>\n"
        # The name goes in the card's body and never in its heading. A member's name set as a
        # headline on the front door invites the question the frame exists to answer, and seat
        # order is a reason a reader should read before they read the name, not after.
        f"<div><p>Read one page in full</p><p>{example}, first in seat order: every report the "
        "register attributes to them, every trade, every date.</p></div>\n"
        f'<div><p><a href="{RECORD_PAGE}">How this register was built</a></p><p>What this build '
        "holds, what it could not read, and how to get a fact here corrected.</p></div>\n"
        f'<div><p><a href="{CHARTER}">The Charter</a></p><p>Five vows, short on purpose.</p>'
        "</div>\n"
        + (
            f'<div><p><a href="{SEATS_PAGE}#not-listed">A seat that changed hands</a></p><p>'
            f"Members the Clerk's roster stopped listing during {esc(congress_words())} keep "
            "their pages, with every row the register published.</p></div>\n"
            if off_roster
            else ""
        )
        + "</section>"
    )
    oath = (
        '<section class="sworn">\n<h2>What every member swore</h2>\n'
        f'<blockquote class="oath"><p>{esc(OATH)}</p><footer>{OATH_CITE} Every member took it. '
        "The register sets the record beside it.</footer></blockquote>\n</section>"
    )
    # The transaction sections are handed the transaction Signal's runs alone, and the annual
    # report its own, so no sentence written for one is said of the other (VOICES).
    ptr_runs = runs_in(signal_runs or [], PTR_VOICE)
    deadline = deadline_section(ptr_runs, findings or [], meta, signal_runs or [])
    ends = ends_section(ptr_runs, findings or [], meta)
    narrows = narrows_section(ptr_runs, outcomes_all or {}, findings or [], meta)
    notice = notice_section(transactions or [], filings, meta)
    annual = annual_section(
        runs_in(signal_runs or [], ANNUAL_VOICE),
        outcomes_all or {},
        findings or [],
        filings,
        [h for h in holders if h["id"] not in off_roster],
        meta,
    )
    everything = [o for s, _ in ptr_runs for o in (outcomes_all or {}).get(s["id"], [])]
    by_id = {f["id"]: f for f in filings}
    how = (
        strip_section(
            sum(
                1
                for o in everything
                if o["state"] != "evaluated"
                and (by_id.get(o["filing_id"], {}).get("source") or {}).get("content_hash")
            ),
            len(everything),
            ERA["year"],
        )
        if everything
        else ""
    )
    # The order is the editorial decision this page turns on. The reader who arrived from a
    # friend wants their own representative, so the map is first. Then the rule, in four panels,
    # because nobody reads a rule they have no reason to care about yet. Then what the chamber
    # filed against it, then the one date the filer writes, then what the register could not
    # reach, then where the record ends, then the oath the whole page is set beside. The doors out
    # are last.
    # The halftone every drawing here fills from is defined once for the page, not inside one of
    # its figures. It used to live in the glance's squares, and when the glance moved to the record
    # page the notice clock's reassuring band and the strip's screens drew empty, so the figure's
    # weight ran one way with nobody having chosen it. A zero-size drawing, not display:none, which
    # some browsers decline to paint patterns from.
    screens = (
        '<svg width="0" height="0" style="position:absolute" aria-hidden="true" '
        f'focusable="false">{BENDAY}</svg>'
    )
    body = (
        f'{head}\n<main id="main">\n{screens}\n{tile_map(offices)}\n{how}\n{deadline}\n'
        f"{notice}\n{annual + chr(10) if annual else ''}{narrows}\n{ends}\n{oath}\n"
        f"{disputes_section(False, brief=True)}\n{door}\n"
        f"</main>\n{footer(meta, home=True)}"
    )
    return page(HOME_TITLE, body)


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


def answer_rests_on_these_rows(
    outcomes_by: dict[str, dict[str, list[dict]]],
    filings: list[dict],
    transactions: list[dict],
    reads_transactions: set[str] | None = None,
) -> list[str]:
    """Where a Signal's run record and the register's rows disagree about a report.

    `load_signals` keys each Signal's outcomes by the officeholder the RUN RECORD names, and every
    page's answer is drawn from those outcomes while the page's own rows come from
    data/filings.ndjson. The maintainer's correction of an attribution (tools/correct.py --field
    officeholder_id, the documented route) moves the row and not the run record, because the Signal
    has not been re-run since. Both pages then say something the rows contradict, and one of them
    says it adversely. Shown against this renderer: the page the report moved away from reads "The
    register read 1 of 1 transaction report it attributes to this officeholder ... The Clerk's index
    dates 1 report it compared after the deadline: 1 trade on it, 37 days past its own deadline",
    with no such report among its rows, while the page the rows now attribute it to reads "The
    register found nothing to compare here". An adverse sentence about a named person, resting on a
    report the register's own rows give to somebody else, is the worst defect this project has.

    A correction of a report's row count is the same class: the answer's trade counts, and the
    landing's narrowing figure, would be the counts the Signal saw and not the ones the rows hold.

    So the register asserts rather than picks, as it does where reports read and reports compared
    cannot both be true. A refusal is recoverable by a maintainer in minutes (the Council's second
    reading of the built answer, Seat G).
    """
    holder_of = {f["id"]: f["officeholder_id"] for f in filings}
    filed_of = {f["id"]: f.get("filed_at") for f in filings}
    rows_of: dict[str, int] = {}
    for t in transactions:
        rows_of[t["filing_id"]] = rows_of.get(t["filing_id"], 0) + 1
    problems = []
    for signal_id, by_oh in sorted(outcomes_by.items()):
        for outcome in sorted(
            (o for group in by_oh.values() for o in group), key=lambda o: o["filing_id"]
        ):
            report, said = outcome["filing_id"], outcome["officeholder_id"]
            if report not in holder_of:
                problems.append(
                    f"{signal_id} read {report}, which no row of data/filings.ndjson holds"
                )
                continue
            if holder_of[report] != said:
                problems.append(
                    f"{signal_id} attributes {report} to {said} and data/filings.ndjson attributes "
                    f"it to {holder_of[report]}"
                )
            # A Signal that reads only a report's header counts its one date as the row it read,
            # and holds no transaction row to disagree with (signal-outcome.schema.json, rows);
            # that one row is held to the register's instead, so a correction of the date moves
            # the answer or stops the render (the second reading of the annual Signal, Seat C).
            if reads_transactions is not None and signal_id not in reads_transactions:
                if outcome.get("filed_at") != filed_of.get(report):
                    problems.append(
                        f"{signal_id} read {report} as dated {outcome.get('filed_at')} and "
                        f"data/filings.ndjson dates it {filed_of.get(report)}"
                    )
                continue
            counted, held = outcome.get("rows") or 0, rows_of.get(report, 0)
            if counted != held:
                problems.append(
                    f"{signal_id} read {counted} "
                    f"{plural(counted, 'row', 'rows')} on {report} and data/transactions.ndjson "
                    f"holds {held}"
                )
    return problems


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
    held_notices = held_rows_by_holder(rejected, holders)
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
    # One line of time for every person's year figure in this build: to the latest date any
    # annual report could reach, and the last day the one index the register reads lists a
    # transaction report, beyond which a page's lane says it is not read.
    latest = [
        o["latest"]
        for by_oh in outcomes_by.values()
        for rows in by_oh.values()
        for o in rows
        if o.get("latest")
    ]
    ERA["drawn_to"] = max(latest) if latest else ""
    ptr_dates = [f["filed_at"] for f in filings if f.get("source_form_code") == "P"]
    ERA["index_last"] = max(ptr_dates) if ptr_dates else ""
    silent = unvoiced(signals)
    if silent:
        raise SystemExit(
            "refusing to render: no voice on these pages speaks for "
            f"{', '.join(silent)}, and the sentences written for another Signal would say its "
            "results in words that are not true of it. Add its voice in src/surfaces/render.py "
            "(VOICES), with its own answer, silence and figure."
        )
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
    adrift = answer_rests_on_these_rows(
        outcomes_by,
        filings,
        transactions,
        {s["id"] for s in signals if "transaction" in s.get("inputs", [])},
    )
    if adrift:
        raise SystemExit(
            "refusing to render: a Signal's run record and the register's rows disagree about "
            f"{len(adrift)} {plural(len(adrift), 'report', 'reports')}, and every page's answer is "
            "drawn from the record while its rows are drawn from the register. One of the two "
            "pages would carry a sentence the rows contradict, and where a Finding rests on the "
            "report it would be an adverse sentence about a person the rows no longer attribute it "
            "to:\n  "
            + "\n  ".join(adrift[:10])
            + (f"\n  and {len(adrift) - 10} more" if len(adrift) > 10 else "")
            + "\nRe-run the Signal (python src/signals/run.py) so its record covers the rows as "
            "they now stand, or supersede the Findings the moved reports produce "
            "(python src/signals/run.py --correct), citing the evidence."
        )
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
                held_notices.get(h["id"], []),
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
            transactions,
            signal_runs,
            changes,
            {
                sid: [o for group in by_oh.values() for o in group]
                for sid, by_oh in outcomes_by.items()
            },
            findings,
        ),
        encoding="utf-8",
        newline="\n",
    )
    (out / SEATS_PAGE).write_text(
        render_seats(holders, offices, run, meta, changes), encoding="utf-8", newline="\n"
    )
    wanted = load_wanted(root)
    if wanted:
        (out / WANTED_PAGE).write_text(
            render_closing(wanted, run, holders, meta), encoding="utf-8", newline="\n"
        )
    (out / RECORD_PAGE).write_text(
        render_record(
            meta,
            run,
            holders,
            filings,
            offices,
            set_aside_counts(rejected, holders, until),
            rejected_url,
            transactions,
            signal_runs,
            reach,
            changes,
            {
                sid: [o for group in by_oh.values() for o in group]
                for sid, by_oh in outcomes_by.items()
            },
            findings,
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
                filings,
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
        f"rendered {len(holders)} pages, the index, {SEATS_PAGE}, {RECORD_PAGE}, "
        f"{WANTED_PAGE + ', ' if wanted else ''}"
        f"{len(signal_runs)} signal "
        f"{plural(len(signal_runs), 'page', 'pages')} and mark.svg to {shown}"
    )
    print(f"{quiet} pages have no matched row; each says so, with the count set aside at its seat")
    print("Now run: python tools/lint-frame-presence.py && python tools/lint-no-ranking.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
