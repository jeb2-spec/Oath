#!/usr/bin/env python3
"""No cross-officeholder ranking on any surface. INVARIANTS.md §13.

Reads the rendered index at `docs/build/index.html` and requires two things of the
officeholders table:

  1. Its rows are in a declared, permitted order. The table announces its order in
     a `data-order` attribute and each row carries the key it was ordered by. The
     permitted orders are the ones §13 names: an order of offices (`seat`) or of
     names (`name`). Any other declared order fails, an undeclared order fails, and
     a declared order the rows do not actually follow fails.
  2. No cell in the table is a bare number. A count beside a person on an index is
     a score whether or not the table is sorted by it, and METHODOLOGY.md §10 says
     the register does not curate persons.

Standard library, and no code shared with the renderer.

    python tools/lint-no-ranking.py
    python tools/lint-no-ranking.py --site docs/build
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

PERMITTED = {"seat", "name"}
TABLE = re.compile(r"<table\b([^>]*)>(.*?)</table>", re.S | re.I)
ROW = re.compile(r"<tr\b([^>]*)>(.*?)</tr>", re.S | re.I)
CELL = re.compile(r"<td\b[^>]*>(.*?)</td>", re.S | re.I)
ATTR = re.compile(r"""\b([a-z-]+)="([^"]*)\"""", re.I)
TAGS = re.compile(r"<[^>]+>")
NUMBER = re.compile(r"^\s*[\d,.]+\s*$")


def attrs(fragment: str) -> dict[str, str]:
    return {k.lower(): v for k, v in ATTR.findall(fragment)}


def check_index(text: str) -> list[str]:
    failures = []
    tables = [(attrs(a), body) for a, body in TABLE.findall(text)]
    index = [(a, body) for a, body in tables if a.get("id") == "officeholders"]
    if not index:
        return ['no table with id="officeholders"; the index cannot be checked']
    table_attrs, body = index[0]
    order = table_attrs.get("data-order")
    if order is None:
        failures.append("the officeholders table declares no data-order")
    elif order not in PERMITTED:
        failures.append(
            f"the officeholders table is ordered by '{order}', which §13 does not permit"
        )

    keys, rows_seen = [], 0
    for row_attrs_raw, row_body in ROW.findall(body):
        cells = CELL.findall(row_body)
        if not cells:
            continue  # a header row
        rows_seen += 1
        row_attrs = attrs(row_attrs_raw)
        key = row_attrs.get(f"data-{order}") if order else None
        if order in PERMITTED and key is None:
            failures.append(f"row {rows_seen} carries no data-{order} key")
        keys.append(key or "")
        for cell in cells:
            plain = TAGS.sub("", cell)
            if NUMBER.match(plain) and plain.strip():
                failures.append(
                    f"row {rows_seen} carries a bare number ({plain.strip()}) beside a person"
                )
    if order in PERMITTED and keys and keys != sorted(keys):
        failures.append(f"rows are not in the declared {order} order")
    if rows_seen == 0:
        failures.append("the officeholders table has no rows")
    return failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("root", nargs="?", default=".", help="repository root (default: .)")
    parser.add_argument("--site", default="docs/build", help="rendered site (default: docs/build)")
    args = parser.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    index = Path(args.root).resolve() / args.site / "index.html"
    if not index.is_file():
        print(f"OK    no index at {args.site}/index.html; nothing rendered, so nothing is ranked.")
        print("      Render first: python src/surfaces/render.py")
        return 0
    failures = check_index(index.read_text(encoding="utf-8"))
    for line in failures:
        print(f"FAIL  {line}")
    if failures:
        print(f"\n{len(failures)} problems on the index; the register does not rank persons.")
        return 1
    print(
        "OK    the officeholders index is in a permitted order and carries no number about anyone."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
