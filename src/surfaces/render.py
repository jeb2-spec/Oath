#!/usr/bin/env python3
"""Render the register as static pages. NEXT.md Phase 3 I.4, I.5 and I.5b.

Reads the sealed store and writes `docs/build/`: one index of every officeholder
the register holds and one page per officeholder, shaped by ECOSYSTEM.md §1.3,
each carrying its own struck seal from `tools/strike-mark.py`. Standard library.
No template engine, no client-side script, no font request, no image request. A
page is one self-contained file that says what the row says and nothing more, and
will render the same way in a browser twenty years from now.

The register speaks to a reader who is not an expert and should not have to be.
So every page ends with the few words it uses, each explained once in one line,
and every table and every seal carries a caption saying what it shows and what
it does not.

Two invariants live at render time, stated here and checked by their own gates:

  §7   every officeholder page opens with the frame, inside its first header;
  §13  the index is in seat order, an order of offices and not of persons, and
       carries no number beside anyone.

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
import sys
from pathlib import Path

FRAME = "Presence in the register is not evidence of wrongdoing."
CLERK_SEARCH = "https://disclosures-clerk.house.gov/FinancialDisclosure"
CHARTER = "https://github.com/jeb2-spec/Oath/blob/main/CHARTER.md"

# The oath every member takes, verbatim. STANDARDS.md C.1; 5 U.S.C. § 3331; U.S. Const.
# Art. VI § 3. It is the standard the register exists to set the record beside, and
# it is the same words for everyone, which is why it is printed on every page.
OATH = (
    "I, ___, do solemnly swear (or affirm) that I will support and defend the Constitution "
    "of the United States against all enemies, foreign and domestic; that I will bear true "
    "faith and allegiance to the same; that I take this obligation freely, without any "
    "mental reservation or purpose of evasion; and that I will well and faithfully "
    "discharge the duties of the office on which I am about to enter. So help me God."
)
OATH_CITE = "The oath of office. U.S. Const. Art. VI § 3; 5 U.S.C. § 3331. STANDARDS.md C.1."

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
.kicker, h2, th, .how dt, .door div p:first-child {
  font-variant-caps: all-small-caps; letter-spacing: .06em; color: var(--ink-2);
  font-weight: normal; }
.kicker { margin: 0 0 .25rem; font-size: .95rem; }
h1 { font-size: 2.1rem; line-height: 1.15; margin: 0 0 .35rem; font-weight: normal; }
p.office { margin: 0; color: var(--ink-2); }
p.lede { margin: .75rem 0 0; max-width: 34rem; }
figure.seal { margin: 0; width: 104px; }
figure.seal svg { width: 104px; height: 104px; display: block; margin: 0 auto .35rem; }
blockquote.oath { margin: .25rem 0 1rem; padding: .6rem 1rem; border-left: 3px solid var(--rule); }
blockquote.oath p { margin: 0; font-style: italic; }
blockquote.oath footer { border: 0; margin: .4rem 0 0; padding: 0; font-size: .8rem; }
.requires dl { display: grid; grid-template-columns: max-content 1fr; gap: .35rem 1rem; margin: 0; }
.requires dt, .requires dd { margin: 0; }
.requires dt { color: var(--ink); }
.requires dd { color: var(--ink-2); }
figcaption { font-size: .78rem; line-height: 1.35; color: var(--ink-2); }
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
p.quiet { color: var(--ink-2); max-width: 36rem; }
.how dl { display: grid; grid-template-columns: max-content 1fr; gap: .35rem 1rem; margin: 0; }
.how dt, .how dd { margin: 0; }
.how dd { color: var(--ink-2); }
footer { margin-top: 2.5rem; padding-top: .9rem; border-top: 2px solid var(--ink);
         font-size: .85rem; color: var(--ink-2); }
footer p { margin: .25rem 0; }
code { font-family: var(--mono); font-size: .88em; }
/* the door: a tile map of states; equal squares on purpose */
.finder { display: grid; grid-template-columns: 1fr; gap: .75rem; }
.tiles { display: grid; grid-template-columns: repeat(11, minmax(0, 1fr)); gap: 4px;
         max-width: 34rem; }
.tile { aspect-ratio: 1; display: flex; flex-direction: column; align-items: center;
        justify-content: center; border: 1px solid var(--rule); text-decoration: none;
        color: var(--ink); font-family: var(--mono); font-size: .72rem; line-height: 1.1; }
.tile small { color: var(--ink-2); font-size: .6rem; }
.tile:hover, .tile:focus-visible { border-color: var(--ink); outline: none; }
.tile.t { border-style: dashed; }
/* the state of the record: bars and a rhythm, numbers about the register, never about a person */
.record dl { display: grid; grid-template-columns: max-content 1fr; gap: .5rem 1rem;
             margin: 0 0 1rem; }
.record dt { font-family: var(--mono); font-variant-numeric: tabular-nums; text-align: right;
             color: var(--ink); }
.record dd { margin: 0; color: var(--ink-2); }
.bar { height: 6px; background: var(--rule); margin-top: .3rem; max-width: 24rem; }
.bar i { display: block; height: 100%; background: var(--ink); opacity: .55; }
.rhythm svg { width: 100%; max-width: 40rem; height: auto; display: block; color: var(--ink); }
figure.rhythm { margin: .5rem 0 0; }
/* the roll: state header rows inside the one table */
tr.state th { padding-top: 1.1rem; font-variant-caps: all-small-caps; letter-spacing: .06em;
              color: var(--ink); border-bottom: 1px solid var(--ink); }
tr.vacant td { color: var(--ink-2); font-style: italic; }
/* what the register can check here */
.checks dl { display: grid; grid-template-columns: max-content 1fr; gap: .35rem 1rem; margin: 0; }
.checks dt, .checks dd { margin: 0; }
.checks dt { color: var(--ink); }
.checks dd { color: var(--ink-2); }
.checks dd b { font-weight: normal; color: var(--ink); font-variant-caps: all-small-caps;
               letter-spacing: .05em; }
@media (max-width: 40rem) {
  .record dl, .checks dl { grid-template-columns: 1fr; }
  .record dt { text-align: left; }
  .masthead { grid-template-columns: 1fr; }
  figure.seal { width: 110px; } figure.seal svg { width: 110px; height: 110px; }
  .how dl, .requires dl { grid-template-columns: 1fr; }
}
@media print {
  html { font-size: 11pt; background: #fff; color: #000; }
  .skip { display: none; } a { color: inherit; }
  figure.seal { width: 28mm; } figure.seal svg { width: 28mm; height: 28mm; }
  table, figure { break-inside: avoid; }
}
"""


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


def page(title: str, body: str) -> str:
    return (
        '<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f"<title>{esc(title)} · Oath</title>\n<style>{CSS}</style>\n</head>\n<body>\n"
        '<a class="skip" href="#main">Skip to the record</a>\n'
        f"{body}\n</body>\n</html>\n"
    )


def how_to_read(person: bool) -> str:
    seal_line = (
        "Struck from this officeholder's identifier and the build's digest. It changes when the "
        "record changes. It says nothing about the person."
        if person
        else "Every page carries one, struck from that officeholder's identifier and the build's "
        "digest. It changes when the record changes. It says nothing about the person."
    )
    return (
        '<section class="how">\n<h2>How to read this page</h2>\n<dl>\n'
        "<dt>The oath</dt><dd>The words every member speaks on taking the seat, printed as the "
        "statute gives them and cited to it. It is the standard the register sets the record "
        "beside.</dd>\n"
        "<dt>A filing</dt><dd>A document the officeholder was required to file with the Clerk of "
        "the House, listed here as the Clerk lists it.</dd>\n"
        "<dt>The document</dt><dd>The Clerk's own copy. The register links to it and does not "
        "host it.</dd>\n"
        "<dt>Fetched</dt><dd>The day the register last read the Clerk's index.</dd>\n"
        "<dt>A signal</dt><dd>A condition written down in advance, citing the rule it comes "
        "from. None is defined in this build, so none can fire.</dd>\n"
        f"<dt>The seal</dt><dd>{seal_line}</dd>\n"
        "<dt>The build</dt><dd>One sealed reading of the record, with a digest anyone can "
        "recompute. Cite the build, not the page.</dd>\n"
        "</dl>\n</section>"
    )


def footer(meta: dict, home: bool) -> str:
    anchor = meta.get("anchor", {}).get("state", "none")
    back = "" if home else '<p><a href="../index.html">Every officeholder in the register</a></p>\n'
    return (
        "<footer>\n"
        f"{back}"
        f"<p>Build <code>{esc(meta.get('build'))}</code>, sealed "
        f"<code>{esc(meta.get('built_at'))}</code>. Digest <code>{esc(meta.get('digest'))}</code>. "
        f"Anchor: {esc(anchor)}.</p>\n"
        "<p>Cite the build, not the page. Verify it: <code>python tools/verify.py</code>. "
        "Integrity is not accuracy.</p>\n"
        "</footer>"
    )


def seal_figure(svg: str, caption: str) -> str:
    return f'<figure class="seal">\n{svg}<figcaption>{esc(caption)}</figcaption>\n</figure>'


def filings_section(filings: list[dict], build: str) -> str:
    if not filings:
        return (
            "<section>\n<h2>What this officeholder filed</h2>\n"
            f'<p class="quiet">Nothing is attributed to this officeholder in build '
            f"<code>{esc(build)}</code>. The register attributes a filing only when the name "
            "matches the Clerk's roster beyond doubt, and holds the rest for a person to decide. "
            "The held rows are counted in the build record. "
            f'<a href="{CLERK_SEARCH}">Search the Clerk\'s disclosure site directly.</a></p>\n'
            "</section>"
        )
    rows = []
    for f in sorted(filings, key=lambda f: (f["filed_at"], f["id"])):
        code = f.get("source_form_code") or ""
        form = f.get("form_type", "")
        label = f"{code} ({form})" if code else form
        rows.append(
            "<tr>"
            f'<td class="idx">{esc(f["filed_at"])}</td>'
            f"<td>{esc(label)}</td>"
            f'<td><a href="{esc(f["source"]["url"])}">Open the Clerk\'s copy</a></td>'
            f'<td class="idx">{esc(f["source"]["retrieved_at"][:10])}</td>'
            "</tr>"
        )
    n = len(rows)
    return (
        "<section>\n<h2>What this officeholder filed</h2>\n<table>\n"
        f"<caption>{n} filing{'s' if n != 1 else ''} attributed in build {esc(build)}, "
        "oldest first. The code is the Clerk's own and is not interpreted here.</caption>\n"
        "<thead><tr><th>Date filed</th><th>What the Clerk calls it</th>"
        "<th>The document</th><th>Fetched</th></tr></thead>\n<tbody>\n"
        + "\n".join(rows)
        + "\n</tbody>\n</table>\n</section>"
    )


REQUIRES = (
    '<section class="requires">\n<h2>What this office requires</h2>\n'
    '<p class="quiet">The same for every member of the House. Each line cites the rule it '
    "comes from.</p>\n"
    f'<blockquote class="oath"><p>{esc(OATH)}</p><footer>{esc(OATH_CITE)}</footer></blockquote>\n'
    "<dl>\n"
    "<dt>An annual financial disclosure</dt><dd>Filed with the Clerk of the House for each year "
    "the office is held. Ethics in Government Act of 1978. STANDARDS.md S.1.</dd>\n"
    "<dt>A report of each covered transaction</dt><dd>A purchase, sale or exchange of a "
    "security over $1,000, reported within 30 days of notice of it and no later than 45 days "
    "after it. STOCK Act of 2012, Pub. L. 112-105. STANDARDS.md S.2.</dd>\n"
    "</dl>\n</section>"
)

SIGNALS = (
    "<section>\n<h2>Signals that fired</h2>\n"
    '<p class="quiet">None. No signal is defined in this build, so none has fired for anyone.</p>\n'
    "</section>\n<section>\n<h2>Signals that did not fire</h2>\n"
    '<p class="quiet">None to list. When signals exist, every one that did not fire is named here '
    "with its version, so silence is shown rather than assumed.</p>\n</section>"
)


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
# size on purpose. (column, row). Territories take the last row.
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
HOUSE_FINDER = "https://www.house.gov/representatives/find-your-representative"
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def seats_by_state(offices: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for o in offices:
        counts[o["state"]] = counts.get(o["state"], 0) + 1
    return counts


def tile_map(offices: list[dict]) -> str:
    """The door. Every state in the data gets a tile; unknown codes join the territories row."""
    counts = seats_by_state(offices)
    tiles, extra_col = [], 0
    for code in sorted(counts):
        n = counts[code]
        if code in TILES:
            col, row = TILES[code]
            cls = "tile"
        else:
            col, row, extra_col = extra_col, 8, extra_col + 1
            cls = "tile t"
        name = STATE_NAMES.get(code, code)
        tiles.append(
            f'<a class="{cls}" href="#state-{esc(code)}" '
            f'style="grid-column:{col + 1};grid-row:{row + 1}" '
            f'title="{esc(name)}, {n} seat{"s" if n != 1 else ""}">'
            f"{esc(code)}<small>{n}</small></a>"
        )
    return (
        '<section class="finder" id="find">\n<h2>Find your representative</h2>\n'
        '<p class="quiet">Choose your state to go to its delegation. Each square is one state, '
        "placed "
        "roughly where it sits, and every square is the same size on purpose. The small number is "
        "how many House seats the state has, which is a fact about the office and not about anyone "
        f'in it. Not sure of your district? <a href="{HOUSE_FINDER}">The House\'s own finder</a> '
        "takes a ZIP code.</p>\n"
        f'<div class="tiles" role="navigation" aria-label="States">{"".join(tiles)}</div>\n'
        "</section>"
    )


def rhythm_chart(filings: list[dict], year: int) -> str:
    """Filings attributed by month across the whole chamber. A rhythm, not a measure of anyone."""
    counts = [0] * 12
    for f in filings:
        d = f.get("filed_at", "")
        if d[:4] == str(year) and d[5:7].isdigit():
            counts[int(d[5:7]) - 1] += 1
    top = max(counts) or 1
    w, h, pad = 600, 170, 28
    bw = (w - 2 * pad) / 12
    parts = [
        f'<line x1="{pad}" y1="{h - pad}" x2="{w - pad}" y2="{h - pad}" '
        'stroke="currentColor" stroke-width="0.8"/>'
    ]
    for i, c in enumerate(counts):
        bh = (h - 2 * pad) * c / top
        x = pad + i * bw + 4
        y = h - pad - bh
        mid = x + (bw - 8) / 2
        parts.append(
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{bw - 8:.1f}" height="{bh:.1f}" '
            'fill="currentColor" fill-opacity="0.35"/>'
        )
        parts.append(
            f'<text x="{mid:.1f}" y="{h - pad + 14}" text-anchor="middle" font-size="10" '
            f'fill="currentColor">{MONTHS[i]}</text>'
        )
        if c:
            parts.append(
                f'<text x="{mid:.1f}" y="{y - 4:.1f}" text-anchor="middle" font-size="10" '
                f'fill="currentColor">{c}</text>'
            )
    return (
        f'<svg viewBox="0 0 {w} {h}" role="img" aria-label="Filings attributed by month, {year}, '
        f'whole chamber">{"".join(parts)}</svg>'
    )


def bar(part: int, whole: int) -> str:
    pct = 0 if not whole else round(100 * part / whole)
    return f'<span class="bar"><i style="width:{pct}%"></i></span>'


def state_of_record(
    meta: dict, run: dict, holders: list[dict], filings: list[dict], offices: list[dict]
) -> str:
    """Numbers about the register and the chamber as a whole. None is about a person."""
    counts = run.get("counts", {})
    seats = counts.get("seats", len(offices))
    filled = counts.get("filled", len(holders))
    with_filing = counts.get(
        "officeholders_with_a_filing", len({f["officeholder_id"] for f in filings})
    )
    accepted = counts.get("accepted", len(filings))
    held = run.get("rejected_by_reason", {}).get("surname matches exactly one sitting member", 0)
    year = run.get("year", int(str(meta.get("build", "0000-x-2025")).split("-")[-1]))
    sources = {s["name"]: s for s in run.get("sources", [])}
    index_src = sources.get(f"{year}FD.zip", {})
    roster_src = sources.get("MemberData.xml", {})
    fresh = ""
    if index_src:
        fresh = (
            f"The Clerk's index was last modified {esc(index_src.get('last_modified', 'unknown'))} "
            f"and the register read it {esc(index_src.get('retrieved_at', '')[:10])}; "
            "the roster was "
            f"read {esc(roster_src.get('retrieved_at', '')[:10])}. "
        )
    return (
        '<section class="record" id="record">\n<h2>The state of the record</h2>\n'
        f'<p class="quiet">What the register holds at build '
        f"<code>{esc(meta.get('build', ''))}</code>. "
        "Every number here is about the register or the chamber as a whole. None is about a "
        "person, and nothing here is sorted by anything the register computes about one.</p>\n"
        "<dl>\n"
        f"<dt>{seats}</dt><dd>seats in the House; {filled} filled, {seats - filled} vacant"
        f"{bar(filled, seats)}</dd>\n"
        f"<dt>{with_filing}</dt><dd>of {filled} officeholders have at least one filing "
        f"attributed{bar(with_filing, filled)}</dd>\n"
        f"<dt>{accepted}</dt><dd>filings attributed, each linked to the Clerk's own document</dd>\n"
        f"<dt>0</dt><dd>of {accepted} documents read by the register so far; the links open "
        f"the Clerk's copies{bar(0, accepted)}</dd>\n"
        f"<dt>{held}</dt><dd>index rows held for a person to decide, because the register "
        "does not guess</dd>\n"
        "<dt>0</dt><dd>signals defined, so 0 fired; silence is a legitimate result</dd>\n"
        "</dl>\n"
        f'<p class="quiet">{fresh}The seal below fixes exactly this reading.</p>\n'
        f'<figure class="rhythm">{rhythm_chart(filings, year)}'
        f"<figcaption>Filings attributed by month in {year}, across every member. This is the "
        "rhythm of disclosure in the chamber; it is not a measure of anyone, and no person's "
        "count appears anywhere on this page.</figcaption></figure>\n"
        "</section>"
    )


def checks_section(holder: dict, filings: list[dict], run: dict, held: int) -> str:
    """What the register can and cannot check about this record. Identical in shape for everyone."""
    roster_read = holder.get("source", {}).get("retrieved_at", "")[:10]
    n = len(filings)
    if n:
        index_line = (
            f"<b>in the register</b> · {n} filing{'s' if n != 1 else ''} attributed from the "
            "Clerk's index."
        )
    else:
        index_line = (
            f"<b>nothing attributed</b> · the register attributes only beyond doubt; {held} rows "
            "across the chamber are held for a person to decide."
        )
    return (
        '<section class="checks">\n<h2>What the register can check here</h2>\n<dl>\n'
        f"<dt>Identity</dt><dd><b>in the register</b> · from the Clerk's roster, read "
        f"{esc(roster_read)}.</dd>\n"
        f"<dt>Filings index</dt><dd>{index_line}</dd>\n"
        "<dt>Documents</dt><dd><b>not yet</b> · the register has not read the documents; each link "
        "below opens the Clerk's own copy.</dd>\n"
        "<dt>Signals</dt><dd><b>none defined</b> · so none can fire, for anyone.</dd>\n"
        "</dl>\n</section>"
    )


def render_officeholder(
    holder: dict, filings: list[dict], meta: dict, striker, run: dict | None = None
) -> str:
    office = holder["offices"][0] if holder.get("offices") else {}
    term_end = office.get("term_end") or "current"
    build = meta.get("build", "")
    seal = striker.strike(holder["id"], meta.get("digest", ""), ticks=0, bars=0)
    run = run or {}
    held = run.get("rejected_by_reason", {}).get("surname matches exactly one sitting member", 0)
    checks = checks_section(holder, filings, run, held)
    head = (
        '<header class="frame">\n'
        f'<p class="frame">{esc(FRAME)}</p>\n'
        '<div class="masthead">\n<div>\n'
        '<p class="kicker">Oath · the register</p>\n'
        f"<h1>{esc(holder['legal_name'])}</h1>\n"
        f'<p class="office">{esc(office.get("title", ""))} · seat {esc(office.get("seat", ""))} · '
        f"term {esc(office.get('term_start', ''))} to {esc(term_end)}</p>\n"
        "</div>\n"
        + seal_figure(
            seal,
            f"Seal of this record at build {build}. It changes when the record changes. "
            "It says nothing about the person.",
        )
        + "\n</div>\n</header>"
    )
    body = (
        f'{head}\n<main id="main">\n{REQUIRES}\n{checks}\n'
        f"{filings_section(filings, build)}\n{SIGNALS}\n"
        f"{how_to_read(True)}\n</main>\n{footer(meta, home=False)}"
    )
    return page(holder["legal_name"], body)


def render_index(
    holders: list[dict], offices: list[dict], filings: list[dict], run: dict, meta: dict, striker
) -> str:
    holder_by_seat = {h["offices"][0]["seat"]: h for h in holders}
    seats = sorted(o["seat"] for o in offices)
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
                f"{n} seat{'s' if n != 1 else ''}"
                "</th></tr>"
            )
        h = holder_by_seat.get(seat)
        if h is None:
            rows.append(
                f'<tr class="vacant" data-id="of:us:house-{esc(seat.lower())}" '
                f'data-seat="{esc(seat)}"><td class="idx">{esc(seat)}</td><td>Vacant</td>'
                "<td>no officeholder in this build</td></tr>"
            )
            continue
        rows.append(
            f'<tr data-id="{esc(h["id"])}" data-seat="{esc(seat)}">'
            f'<td class="idx">{esc(seat)}</td>'
            f'<td><a href="officeholders/{esc(slug(h["id"]))}.html">{esc(h["legal_name"])}</a></td>'
            f"<td>{esc(h['offices'][0].get('title', ''))}</td>"
            "</tr>"
        )
    build = meta.get("build", "")
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
        '<p class="lede">Every member of the U.S. House is listed here with every financial '
        "disclosure they have filed, each linked to the Clerk's own copy. The register draws no "
        "conclusion about anyone. It shows what was filed, when, and where to read it "
        "yourself.</p>\n"
        '<p class="lede">This build holds no signals: no condition has been written against the '
        "record yet, so no page reports one. Most pages will stay quiet even when signals exist. "
        "Quiet means the record shows nothing a written rule catches.</p>\n"
        f'<blockquote class="oath"><p>{esc(OATH)}</p><footer>{esc(OATH_CITE)} Every member '
        "took it. The register sets the record beside it.</footer></blockquote>\n"
        "</div>\n"
        + seal_figure(
            mark, f"The mark of build {build}, struck from its digest. Every page carries its own."
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
        f"lists. The order says nothing about anyone. {esc(meta.get('state', ''))}</caption>\n"
        "<thead><tr><th>Seat</th><th>Name, as the Clerk lists it</th><th>Office</th></tr></thead>\n"
        "<tbody>\n" + "\n".join(rows) + "\n</tbody>\n</table>\n</section>"
    )
    body = (
        f'{head}\n<main id="main">\n{door}\n{tile_map(offices)}\n'
        f"{state_of_record(meta, run, holders, filings, offices)}\n{table}\n{how_to_read(False)}\n"
        f"</main>\n{footer(meta, home=True)}"
    )
    return page("Every officeholder in the register", body)


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
    out = root / args.out
    striker = load_striker(root)

    meta = json.loads((root / "data" / "meta.json").read_text(encoding="utf-8"))
    holders = read_ndjson(root / "data" / "officeholders.ndjson")
    filings = read_ndjson(root / "data" / "filings.ndjson")
    offices = read_ndjson(root / "data" / "offices.ndjson")
    runs = sorted((root / "data" / "adapter-runs").glob("house-fd-*.ndjson"))
    run = read_ndjson(runs[-1])[0] if runs else {}
    by_holder: dict[str, list[dict]] = {}
    for f in filings:
        by_holder.setdefault(f["officeholder_id"], []).append(f)

    (out / "officeholders").mkdir(parents=True, exist_ok=True)
    for h in holders:
        target = out / "officeholders" / f"{slug(h['id'])}.html"
        target.write_text(
            render_officeholder(h, by_holder.get(h["id"], []), meta, striker, run),
            encoding="utf-8",
            newline="\n",
        )
    (out / "index.html").write_text(
        render_index(holders, offices, filings, run, meta, striker),
        encoding="utf-8",
        newline="\n",
    )
    digest = meta.get("digest", "")
    (out / "mark.svg").write_text(
        striker.strike(digest, digest, with_wordmark=True), encoding="utf-8", newline="\n"
    )

    quiet = sum(1 for h in holders if not by_holder.get(h["id"]))
    print(f"rendered {len(holders)} pages, the index, and mark.svg to {out.relative_to(root)}")
    print(f"{quiet} pages carry no filing; each says so and points at the source")
    print("Now run: python tools/lint-frame-presence.py && python tools/lint-no-ranking.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
