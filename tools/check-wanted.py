#!/usr/bin/env python3
"""The wanted register says what it does not know, and never more. INVARIANTS.md §1 and §4.

`docs/wanted/wanted.ndjson` lists every piece of official information the register would need
to follow a report past the deadline to whatever followed it. A list like that is the easiest
document in this project to lie in, because every row is about something nobody here has seen,
and a confident sentence about an absent record costs nothing to write and cannot be checked by
a reader. So the rules are stricter here than on a row of evidence, not looser:

  1. Every row validates against `schemas/wanted.schema.json`, ids are unique, and a row is
     never deleted: a piece that stops being wanted carries a `closed` date and stays.
  2. **A row may say something is published, obtainable or not public only when somebody here
     has read a candidate at its source** (`verified: true`). Every other row says `unknown`.
     Believing a thing is public is not knowing it, and the difference is the whole file.
  3. A row that is not verified carries a `check`: exactly what to read, and where, to settle
     it. A row that says the project does not know must say how to find out, or it is a
     complaint rather than a work item.
  4. A verified row carries at least one candidate, because verified means somebody read one.
  5. No row names an officeholder the register holds, or writes a seat, an officeholder id
     or a DocID, which stand in for one. The wanted list is about institutions and records; a
     person's name in it would read as a claim that something is withheld about them.
  6. Every `closes` key is one the renderer has a heading for, so a new group cannot appear on
     the page unlabelled, and every group the renderer knows has at least one row.

It is not sealed with the build. The seal vouches for evidence; this file is a work list, and a
list that re-seals on every addition would cost a new build and a new anchor to admit that the
project does not know something. NEXT.md carries the question of folding it in.

    python tools/check-wanted.py
    python tools/check-wanted.py --rows docs/wanted/wanted.ndjson
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROWS = "docs/wanted/wanted.ndjson"
SCHEMA = "schemas/wanted.schema.json"
HOLDERS = "data/officeholders.ndjson"
# The renderer's headings, written here on its own: a gate that imports the thing it checks
# agrees with it by construction and proves nothing.
GROUPS = ("the-date", "the-fee", "the-review", "the-courts", "the-shut-door")
KNOWN = ("published", "obtainable", "not public", "unknown")
UNIT = ("report", "officeholder", "matter", "chamber-year")
ID = re.compile(r"^wt:[a-z0-9]+(-[a-z0-9]+)*$")
# What stands in for a person: the seat they hold and their row's id, both of which have a shape
# no sentence writes by accident. A DocID does not: tools/lint-no-names.py reads any run of five
# or more digits as one, which is right for a sealed figure and wrong here, where the rows carry
# statute sections. "5 U.S.C. 13106" is not a filing. So a DocID is matched against the DocIDs
# this register actually holds, which is both narrower and stronger than a shape.
PLACES_SOMEONE = (
    (re.compile(r"\b[A-Z]{2}\d{2}\b"), "a seat"),
    (re.compile(r"\boh:us:[a-z0-9:-]+"), "an officeholder's id"),
)
FILINGS = "data/filings.ndjson"
DATE = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")
REQUIRED = (
    "id",
    "closes",
    "question",
    "today",
    "with_it",
    "unit",
    "joins_on",
    "holder",
    "publicness",
    "route",
    "candidates",
    "verified",
    "added",
)


def read_rows(path: Path) -> list[dict]:
    rows = []
    for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise SystemExit(f"FAIL  {path}:{n} is not JSON: {exc}") from exc
    return rows


def names(root: Path) -> list[str]:
    """Every name the register publishes for an officeholder it holds, longest first.

    Whole published names, and never a surname token on its own. A first draft matched any
    four-letter word that is also a surname in the chamber and reported three rows: *fields*,
    the plural noun, and *case* twice, once in "a named case" and once in "the case file".
    Fields and Case are both real surnames and both ordinary English words, and a gate that
    cries wolf on ordinary English is a gate somebody switches off. tools/lint-no-names.py
    settled this convention before this file existed: match what the register publishes as a
    person's name. A second draft matched those names as bare substrings and reported "a named
    case where one exists" for containing a two-word name across a word it does not begin, so
    the match is on word boundaries."""
    path = root / HOLDERS
    if not path.is_file():
        return []
    found: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        for key in ("common_name", "legal_name"):
            if row.get(key):
                found.add(row[key])
    return sorted(found, key=len, reverse=True)


def doc_ids(root: Path) -> set[str]:
    """Every DocID the register holds, as the Clerk's index writes it: the digits at the end of
    a filing's id. Matching these, rather than any long run of digits, lets a row cite a statute
    section and still refuses a row that points at one person's filing."""
    path = root / FILINGS
    if not path.is_file():
        return set()
    out: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        tail = str(json.loads(line).get("id") or "").rsplit(":", 1)[-1]
        if tail.isdigit():
            out.add(tail)
    return out


def check_row(row: dict, seen: set[str]) -> list[str]:
    where = row.get("id", "(no id)")
    bad = []
    for field in REQUIRED:
        if field not in row:
            bad.append(f"{where}: has no {field}")
    if bad:
        return bad
    if not ID.match(row["id"]):
        bad.append(f"{where}: its id is not wt: followed by lowercase words")
    if row["id"] in seen:
        bad.append(f"{where}: two rows carry this id")
    if row["closes"] not in GROUPS:
        bad.append(f"{where}: closes {row['closes']!r}, which the page has no heading for")
    if row["unit"] not in UNIT:
        bad.append(f"{where}: unit {row['unit']!r} is not one this register counts by")
    if row["publicness"] not in KNOWN:
        bad.append(f"{where}: publicness {row['publicness']!r} is not one of {KNOWN}")
    if not DATE.match(str(row["added"])):
        bad.append(f"{where}: added is not a date")
    for field in ("question", "today", "with_it", "route", "holder"):
        if not str(row.get(field) or "").strip():
            bad.append(f"{where}: {field} is empty, and every field here is load-bearing")
    # The rule the file exists for.
    if not row["verified"] and row["publicness"] != "unknown":
        bad.append(
            f"{where}: says publicness {row['publicness']!r} and nobody here has read a "
            "candidate at its source. Believing a thing is public is not knowing it; say "
            "unknown until somebody has looked"
        )
    if not row["verified"] and not str(row.get("check") or "").strip():
        bad.append(
            f"{where}: is not verified and carries no check. A row that says the project does "
            "not know must say what to read, and where, to find out"
        )
    if row["verified"] and not row["candidates"]:
        bad.append(f"{where}: is verified and names no candidate, so there is nothing it read")
    return bad


def names_a_person(row: dict, published: list[str], docs: set[str]) -> list[str]:
    """Where a row names an officeholder, or writes something that stands in for one."""
    text = " ".join(
        str(v) for k, v in row.items() if k != "candidates" and isinstance(v, (str, int))
    )
    for candidate in row.get("candidates") or []:
        text += " " + str(candidate.get("what") or "")
    out = []
    for name in published:
        if re.search(rf"\b{re.escape(name)}\b", text, re.IGNORECASE):
            out.append(
                f"{row.get('id')}: names {name!r}. This list is about records, and a person's "
                "name in it reads as a claim that something is being withheld about them"
            )
            break
    for pattern, what in PLACES_SOMEONE:
        if pattern.search(text):
            out.append(f"{row.get('id')}: carries {what}, which stands in for a person")
    for number in re.findall(r"(?<![\w,:-])\d{4,}(?![\w,-])", text):
        if number in docs:
            out.append(f"{row.get('id')}: carries DocID {number}, which stands in for a person")
            break
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("root", nargs="?", default=".", help="repository root (default: .)")
    parser.add_argument("--rows", default=ROWS, help=f"the wanted rows (default: {ROWS})")
    args = parser.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    root = Path(args.root).resolve()
    path = root / args.rows
    if not path.is_file():
        print(f"FAIL  no wanted register at {args.rows}; a gate that reads nothing proves nothing.")
        return 1
    rows = read_rows(path)
    if not rows:
        print(f"FAIL  {args.rows} holds no row, and the loop is not closed.")
        return 1

    failures: list[str] = []
    seen: set[str] = set()
    published, docs = names(root), doc_ids(root)
    for row in rows:
        failures += check_row(row, seen)
        failures += names_a_person(row, published, docs)
        if isinstance(row.get("id"), str):
            seen.add(row["id"])
    for group in GROUPS:
        if not any(r.get("closes") == group for r in rows):
            failures.append(f"the page has a heading for {group!r} and no row closes it")

    for line in failures:
        print(f"FAIL  {line}")
    if failures:
        print(f"\n{len(failures)} problems; the wanted register says what it does not know.")
        return 1

    open_rows = [r for r in rows if not r.get("closed")]
    verified = sum(1 for r in rows if r["verified"])
    unknown = sum(1 for r in rows if r["publicness"] == "unknown")
    print(
        f"OK    {len(rows)} wanted rows across {len(GROUPS)} parts of the loop, "
        f"{len(open_rows)} still open; {verified} verified at a source and {unknown} saying "
        "unknown, each with what to read to settle it."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
