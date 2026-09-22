#!/usr/bin/env python3
"""Render the register as static pages. NEXT.md Phase 3 I.4 and I.5b.

Reads the sealed store and writes `docs/build/`: one index of every officeholder
in the register and one page per officeholder, shaped by ECOSYSTEM.md §1.3.
Standard library only; no template engine, no client-side script. A page says
what the row says and nothing more.

Two invariants are rendering-time, and this file is where they are either kept or
broken, so they are stated here and checked by their own gates afterwards:

  §7   Every officeholder page opens with the frame sentence, before the name.
       `tools/lint-frame-presence.py` reads the output and requires it.
  §13  The index is in seat order, which is an order of offices and not of
       persons, and carries no number about anyone. `tools/lint-no-ranking.py`
       reads the output and requires both.

What the page does not show: party. ECOSYSTEM.md §1.3 lists name, office,
jurisdiction and term, and CLAUDE.md asks that the reader-facing register carry
no party label. The row holds it; this surface does not print it.

    python src/surfaces/render.py
    python src/surfaces/render.py --out docs/build
"""

from __future__ import annotations

import argparse
import html
import json
import sys
from pathlib import Path

FRAME = "Presence in the register is not evidence of wrongdoing."
CLERK_SEARCH = "https://disclosures-clerk.house.gov/FinancialDisclosure"

CSS = """
:root { color-scheme: light dark; --fg: #1a1a1a; --bg: #fdfdfb; --mute: #5a5a55;
        --rule: #d8d8d2; --link: #1d4ed8; }
@media (prefers-color-scheme: dark) {
  :root { --fg: #e8e8e2; --bg: #14141a; --mute: #a0a09a; --rule: #33333a; --link: #8ab4f8; } }
html { background: var(--bg); color: var(--fg); font: 16px/1.5 Georgia, 'Times New Roman', serif; }
body { max-width: 52rem; margin: 0 auto; padding: 1.5rem 1rem 4rem; }
header.frame { border-bottom: 1px solid var(--rule); padding-bottom: .75rem;
               margin-bottom: 1.5rem; }
header.frame p.frame { margin: 0 0 .75rem; color: var(--mute); font-style: italic; }
h1 { font-size: 1.75rem; margin: 0 0 .25rem; font-weight: normal; }
h2 { font-size: 1rem; letter-spacing: .08em; text-transform: uppercase; color: var(--mute);
     margin: 2rem 0 .5rem; font-weight: normal; }
p.office { margin: 0; color: var(--mute); }
table { border-collapse: collapse; width: 100%; font-size: .95rem; }
th, td { text-align: left; padding: .4rem .5rem; border-bottom: 1px solid var(--rule);
         vertical-align: top; }
th { font-weight: normal; color: var(--mute); }
a { color: var(--link); }
footer { margin-top: 3rem; padding-top: 1rem; border-top: 1px solid var(--rule);
         font-size: .85rem; color: var(--mute); }
code { font-family: ui-monospace, Menlo, Consolas, monospace; font-size: .9em; }
p.quiet { color: var(--mute); }
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


def page(title: str, body: str, depth: int = 0) -> str:
    return (
        '<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f"<title>{esc(title)}</title>\n<style>{CSS}</style>\n</head>\n<body>\n{body}\n</body>\n</html>\n"
    )


def footer(meta: dict) -> str:
    anchor = meta.get("anchor", {}).get("state", "none")
    return (
        "<footer>\n"
        f"<p>Build <code>{esc(meta.get('build'))}</code> sealed at "
        f"<code>{esc(meta.get('built_at'))}</code>. Digest <code>{esc(meta.get('digest'))}</code>. "
        f"Anchor: {esc(anchor)}.</p>\n"
        "<p>Cite this build, not this page. Verify it: <code>python tools/verify.py</code>. "
        "Integrity is not accuracy.</p>\n"
        "</footer>"
    )


def render_officeholder(holder: dict, filings: list[dict], meta: dict) -> str:
    office = holder["offices"][0] if holder.get("offices") else {}
    term = office.get("term_start", "")
    term_end = office.get("term_end") or "current"
    head = (
        '<header class="frame">\n'
        f'<p class="frame">{esc(FRAME)}</p>\n'
        f"<h1>{esc(holder['legal_name'])}</h1>\n"
        f'<p class="office">{esc(office.get("title", ""))} · '
        f"{esc(office.get('seat', ''))} · {esc(office.get('jurisdiction', ''))} · "
        f"term {esc(term)} to {esc(term_end)}</p>\n"
        "</header>"
    )

    if filings:
        rows = []
        for f in sorted(filings, key=lambda f: (f["filed_at"], f["id"])):
            code = f.get("source_form_code") or ""
            form = f.get("form_type", "")
            label = f"{code} ({form})" if code else form
            rows.append(
                "<tr>"
                f"<td>{esc(f['filed_at'])}</td>"
                f"<td>{esc(label)}</td>"
                f'<td><a href="{esc(f["source"]["url"])}">document</a></td>'
                f"<td>{esc(f['source']['retrieved_at'][:10])}</td>"
                "</tr>"
            )
        filings_html = (
            "<h2>Filings</h2>\n"
            "<table>\n<thead><tr><th>Filed</th><th>Form, as the source labels it</th>"
            "<th>Source</th><th>Retrieved</th></tr></thead>\n<tbody>\n"
            + "\n".join(rows)
            + "\n</tbody>\n</table>\n"
            '<p class="quiet">Form codes are the Clerk\'s own and are not interpreted here; '
            "see SOURCES.md F.1.</p>"
        )
    else:
        filings_html = (
            "<h2>Filings</h2>\n"
            f'<p class="quiet">No filings are attributed to this officeholder in build '
            f"<code>{esc(meta.get('build'))}</code>. The adapter attributes a filing only when the "
            "name matches the Clerk's roster without doubt, and holds the rest for a person to "
            "decide; the held rows are counted in the build record. "
            f'<a href="{CLERK_SEARCH}">Search the Clerk\'s disclosure site directly.</a></p>'
        )

    signals_html = (
        "<h2>Signals fired</h2>\n"
        '<p class="quiet">No Signal is defined in this build, so none has fired for anyone.</p>\n'
        "<h2>Signals that did not fire</h2>\n"
        '<p class="quiet">No Signal is defined in this build. When one is, every defined '
        "Signal that did not fire is listed here by name, with its version.</p>"
    )
    return page(holder["legal_name"], f"{head}\n{filings_html}\n{signals_html}\n{footer(meta)}")


def render_index(holders: list[dict], meta: dict) -> str:
    # Seat order: an order of offices, not of persons. INVARIANTS.md §13.
    ordered = sorted(holders, key=lambda h: (h["offices"][0]["seat"], h["id"]))
    rows = []
    for h in ordered:
        seat = h["offices"][0]["seat"]
        rows.append(
            f'<tr data-id="{esc(h["id"])}" data-seat="{esc(seat)}">'
            f"<td>{esc(seat)}</td>"
            f'<td><a href="officeholders/{esc(slug(h["id"]))}.html">{esc(h["legal_name"])}</a></td>'
            f"<td>{esc(h['offices'][0].get('title', ''))}</td>"
            "</tr>"
        )
    head = (
        '<header class="frame">\n'
        f'<p class="frame">{esc(FRAME)}</p>\n'
        "<h1>Oath</h1>\n"
        '<p class="office">A public register reconciling what U.S. elected officials swore '
        "to uphold with what the record shows. Every officeholder the register holds is listed "
        "here, in seat order. The order says nothing about anyone.</p>\n"
        "</header>"
    )
    body = (
        f"{head}\n<h2>Officeholders</h2>\n"
        '<table id="officeholders" data-order="seat">\n'
        "<thead><tr><th>Seat</th><th>Name, as the Clerk lists it</th><th>Office</th></tr></thead>\n"
        "<tbody>\n" + "\n".join(rows) + "\n</tbody>\n</table>\n"
        f'<p class="quiet">{esc(meta.get("state", ""))}</p>\n'
        f"{footer(meta)}"
    )
    return page("Oath", body)


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
            render_officeholder(h, by_holder.get(h["id"], []), meta), encoding="utf-8", newline="\n"
        )
    (out / "index.html").write_text(render_index(holders, meta), encoding="utf-8", newline="\n")

    quiet = sum(1 for h in holders if not by_holder.get(h["id"]))
    print(f"rendered {len(holders)} officeholder pages and the index to {out.relative_to(root)}")
    print(f"{quiet} pages carry no filing; each says so and points at the source")
    print("Now run: python tools/lint-frame-presence.py && python tools/lint-no-ranking.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
