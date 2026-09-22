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
figure.seal { margin: 0; width: 132px; }
figure.seal svg { width: 132px; height: 132px; display: block; margin: 0 auto .35rem; }
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
@media (max-width: 40rem) {
  .masthead { grid-template-columns: 1fr; }
  figure.seal { width: 110px; } figure.seal svg { width: 110px; height: 110px; }
  .how dl { grid-template-columns: 1fr; }
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


SIGNALS = (
    "<section>\n<h2>Signals that fired</h2>\n"
    '<p class="quiet">None. No signal is defined in this build, so none has fired for anyone.</p>\n'
    "</section>\n<section>\n<h2>Signals that did not fire</h2>\n"
    '<p class="quiet">None to list. When signals exist, every one that did not fire is named here '
    "with its version, so silence is shown rather than assumed.</p>\n</section>"
)


def render_officeholder(holder: dict, filings: list[dict], meta: dict, striker) -> str:
    office = holder["offices"][0] if holder.get("offices") else {}
    term_end = office.get("term_end") or "current"
    build = meta.get("build", "")
    seal = striker.strike(holder["id"], meta.get("digest", ""), ticks=0, bars=0)
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
        f'{head}\n<main id="main">\n{filings_section(filings, build)}\n{SIGNALS}\n'
        f"{how_to_read(True)}\n</main>\n{footer(meta, home=False)}"
    )
    return page(holder["legal_name"], body)


def render_index(holders: list[dict], meta: dict, striker) -> str:
    ordered = sorted(holders, key=lambda h: (h["offices"][0]["seat"], h["id"]))
    rows = []
    for h in ordered:
        seat = h["offices"][0]["seat"]
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
        "</div>\n"
        + seal_figure(
            mark, f"The mark of build {build}, struck from its digest. Every page carries its own."
        )
        + "\n</div>\n</header>"
    )
    door = (
        '<section class="door">\n'
        "<div><p>Look up an officeholder</p>"
        "<p>Find them in the list below, in seat order.</p></div>\n"
        f"<div><p>Read one page in full</p><p>{example}, first in seat order.</p></div>\n"
        f'<div><p>Understand the discipline</p><p><a href="{CHARTER}">The Charter</a>: five vows, '
        "short on purpose.</p></div>\n</section>"
    )
    table = (
        "<section>\n<h2>Every officeholder in the register</h2>\n"
        '<table id="officeholders" data-order="seat">\n'
        f"<caption>{len(ordered)} officeholders in seat order. The order says nothing about "
        f"anyone. {esc(meta.get('state', ''))}</caption>\n"
        "<thead><tr><th>Seat</th><th>Name, as the Clerk lists it</th><th>Office</th></tr></thead>\n"
        "<tbody>\n" + "\n".join(rows) + "\n</tbody>\n</table>\n</section>"
    )
    body = (
        f'{head}\n<main id="main">\n{door}\n{table}\n{how_to_read(False)}\n</main>\n'
        f"{footer(meta, home=True)}"
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
    by_holder: dict[str, list[dict]] = {}
    for f in filings:
        by_holder.setdefault(f["officeholder_id"], []).append(f)

    (out / "officeholders").mkdir(parents=True, exist_ok=True)
    for h in holders:
        target = out / "officeholders" / f"{slug(h['id'])}.html"
        target.write_text(
            render_officeholder(h, by_holder.get(h["id"], []), meta, striker),
            encoding="utf-8",
            newline="\n",
        )
    (out / "index.html").write_text(
        render_index(holders, meta, striker), encoding="utf-8", newline="\n"
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
