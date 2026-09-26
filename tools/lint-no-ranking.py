#!/usr/bin/env python3
"""No cross-officeholder ranking on any surface. INVARIANTS.md §13.

Reads the rendered index at `docs/build/index.html` and every summary page under
`docs/build/signals/`, and finds every list of officeholders on them: the index's
`officeholders` table, any table or `<ol>`/`<ul>` that declares
`data-lists="officeholders"`, and any table or list whose rows link to two or more
officeholders' pages, declared or not, because a list of persons is one whatever its author
called it. On a summary page every link to an officeholder's page must sit inside such a
declared list. Of each list it requires two things:

  1. Its rows are in a declared, permitted order. The list announces its order in a
     `data-order` attribute and each row (`<tr>` or `<li>`) carries the key it was ordered
     by. The permitted orders are the ones §13 names: an order of offices (`seat`) or of
     names (`name`). Any other declared order fails, an undeclared order fails, and a
     declared order the rows do not actually follow fails.
  2. No row carries a number beside a person: once seat codes (`CA12`) and dates
     (`2025-03-01`) are set aside, no digit may remain. A count beside a person is a score
     whether or not the list is sorted by it ("3 reports" as much as "3"), and
     METHODOLOGY.md §10 says the register does not curate persons.

A site with no index fails too: a gate that reads nothing proves nothing, and CI renders
before it runs this. Standard library, and no code shared with the renderer.

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
LIST = re.compile(r"<(ol|ul)\b([^>]*)>(.*?)</\1>", re.S | re.I)
ROW = re.compile(r"<tr\b([^>]*)>(.*?)</tr>", re.S | re.I)
ITEM = re.compile(r"<li\b([^>]*)>(.*?)</li>", re.S | re.I)
CELL = re.compile(r"<td\b[^>]*>(.*?)</td>", re.S | re.I)
ATTR = re.compile(r"""\b([a-z-]+)="([^"]*)\"""", re.I)
TAGS = re.compile(r"<[^>]+>")
SEAT_OR_DATE = re.compile(r"\b[A-Z]{2}\d{2}\b|\b\d{4}-\d{2}-\d{2}\b")
OFFICEHOLDER_LINK = re.compile(r"""href="[^"]*\bofficeholders/[^"/]+\.html""", re.I)


def attrs(fragment: str) -> dict[str, str]:
    return {k.lower(): v for k, v in ATTR.findall(fragment)}


def a_number_in(text: str) -> str | None:
    """The text, when a digit is left once seat codes and dates are set aside."""
    plain = " ".join(TAGS.sub(" ", text).split())
    return plain if re.search(r"\d", SEAT_OR_DATE.sub(" ", plain)) else None


def lists_officeholders(list_attrs: dict[str, str], body: str) -> bool:
    """A list of officeholders: it says so, or its rows link to two or more of their pages."""
    return (
        list_attrs.get("id") == "officeholders"
        or list_attrs.get("data-lists") == "officeholders"
        or len(OFFICEHOLDER_LINK.findall(body)) >= 2
    )


def check_list(list_attrs: dict[str, str], rows: list[tuple[str, str]], name: str) -> list[str]:
    """The two requirements, for one list of officeholders given as (row attributes, row)."""
    failures = []
    order = list_attrs.get("data-order")
    if order is None:
        failures.append(f"the {name} list declares no data-order")
    elif order not in PERMITTED:
        failures.append(f"the {name} list is ordered by '{order}', which §13 does not permit")
    keys = []
    for n, (row_attrs_raw, row_body) in enumerate(rows, 1):
        key = attrs(row_attrs_raw).get(f"data-{order}") if order else None
        if order in PERMITTED and key is None:
            failures.append(f"row {n} carries no data-{order} key")
        keys.append(key or "")
        number = a_number_in(row_body)
        if number:
            failures.append(f"row {n} carries a number beside a person ({number[:60]})")
    if order in PERMITTED and keys and keys != sorted(keys):
        failures.append(f"rows are not in the declared {order} order")
    if not rows:
        failures.append(f"the {name} list has no rows")
    return failures


def table_rows(body: str) -> list[tuple[str, str]]:
    """The rows of a table that hold cells (a header row holds none), as (attributes, cells)."""
    return [
        (row_attrs, " ".join(CELL.findall(row_body)))
        for row_attrs, row_body in ROW.findall(body)
        if CELL.findall(row_body)
    ]


def list_name(list_attrs: dict[str, str]) -> str:
    return list_attrs.get("id") or list_attrs.get("data-lists") or "unnamed"


def lists_on(text: str) -> list[tuple[dict[str, str], list[tuple[str, str]], str]]:
    """Every table and list on a page that lists officeholders, with its rows."""
    found = []
    for raw, body in TABLE.findall(text):
        table_attrs = attrs(raw)
        if lists_officeholders(table_attrs, body):
            found.append((table_attrs, table_rows(body), body))
    for _tag, raw, body in LIST.findall(text):
        list_attrs = attrs(raw)
        if lists_officeholders(list_attrs, body):
            found.append((list_attrs, ITEM.findall(body), body))
    return found


def check_index(text: str) -> list[str]:
    tables = [(attrs(a), body) for a, body in TABLE.findall(text)]
    if not any(a.get("id") == "officeholders" for a, _ in tables):
        return ['no table with id="officeholders"; the index cannot be checked']
    failures = []
    for list_attrs, rows, _body in lists_on(text):
        failures += check_list(list_attrs, rows, list_name(list_attrs))
    return failures


def check_summary(text: str) -> list[str]:
    """A summary page may list no one; every list on it that lists officeholders is checked,
    and no link to an officeholder's page may stand outside a declared list."""
    failures, inside = [], 0
    for list_attrs, rows, body in lists_on(text):
        failures += check_list(list_attrs, rows, list_name(list_attrs))
        if list_attrs.get("data-lists") == "officeholders":
            inside += len(OFFICEHOLDER_LINK.findall(body))
    total = len(OFFICEHOLDER_LINK.findall(text))
    if total > inside:
        failures.append(
            f"{total - inside} links to officeholders' pages stand outside a declared list"
        )
    return failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("root", nargs="?", default=".", help="repository root (default: .)")
    parser.add_argument("--site", default="docs/build", help="rendered site (default: docs/build)")
    args = parser.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    site = Path(args.root).resolve() / args.site
    index = site / "index.html"
    if not index.is_file():
        print(
            f"FAIL  no index at {args.site}/index.html; a gate that reads nothing proves nothing."
        )
        print("      Render first: python src/surfaces/render.py")
        return 1
    failures = [f"index.html: {line}" for line in check_index(index.read_text(encoding="utf-8"))]
    summaries = sorted((site / "signals").glob("**/*.html"))
    for path in summaries:
        where = path.relative_to(site).as_posix()
        failures += [f"{where}: {line}" for line in check_summary(path.read_text("utf-8"))]
    for line in failures:
        print(f"FAIL  {line}")
    if failures:
        print(f"\n{len(failures)} problems; the register does not rank persons.")
        return 1
    pages = f"{len(summaries)} signal page{'' if len(summaries) == 1 else 's'}"
    print(
        f"OK    the officeholders index and {pages} list persons only in a permitted order, "
        "and carry no number about anyone."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
