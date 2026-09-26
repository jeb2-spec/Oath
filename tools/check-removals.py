#!/usr/bin/env python3
"""Facts stay. Change is shown by supersession, not by removal. INVARIANTS.md §14; CHARTER Vow V.

Compares the register's rows in the tree with the published ones, the same paths on
`origin/main` (or the ref in OATH_PUBLISHED_REF; on a push to main CI sets it to main as it
stood before the push), and fails when:

  1. a published row is gone from the tree: an office, an officeholder, a filing, a
     holding, a transaction, or a change row;
  2. a fact a published row carries changed in place. Facts only accrue: a value stays as
     published; a null may be filled; a list may grow at its end; an object may gain keys.
     One thing may move without a word: when the row was last read
     (`source.retrieved_at`), because a refresh reads the source again;
  3. a published change row (data/changes.ndjson), which records what a capture showed,
     changed in any byte.

It warns, and passes, where a published row's `notes` (the adapter's prose about the
row) or its source's `content_hash` (the bytes it was read from) moved, because a reader
should see it and neither is by itself a fact about a person. Findings and Signal
definitions have their own gates (check-supersessions, check-signal-versions). It fails
rather than passes when it cannot read the published ref. Standard library.

Where it stops short of §14's text, said plainly: §14 makes any edit in place a build
failure, and this gate refuses every changed fact but lets the re-read time move, and
warns rather than fails on notes and on the source's content hash. The reason is the
adapter, which stamps a row it derives again with the time of this build's capture, so a
gate that refused every byte would refuse every refresh. A row kept byte-stable while its
facts hold would let the gate refuse every edit, as §14 says; that is on the course, a
choice for the maintainer (NEXT.md), and until then this gate is §14's floor, not all of it.

A published row stays even when a later capture no longer lists it: the adapter carries
it as published and records the change as a row of its own (src/adapters/house-fd/build.py,
`carry_forward`). So a Member who leaves office, a filing the Clerk's index stops listing,
and a filing year whose Congress has ended all keep their rows, and this gate is what
holds the adapter to that.

    python tools/check-removals.py

Example of a failing input: an officeholder the roster no longer lists, dropped from
data/officeholders.ndjson instead of carried, or a published filing's officeholder_id
moved to another person by a later join.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

FILES = (
    "data/offices.ndjson",
    "data/officeholders.ndjson",
    "data/filings.ndjson",
    "data/holdings.ndjson",
    "data/transactions.ndjson",
    "data/changes.ndjson",
)
IMMUTABLE = {"data/changes.ndjson"}
MOVES = {("source", "retrieved_at")}
WARNS = {("notes",), ("source", "content_hash")}
MISSING = object()


def git(root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-C", str(root), *args], capture_output=True, text=True, encoding="utf-8"
    )


def published(root: Path, ref: str, rel: str) -> list[dict] | None:
    """The file as published at `ref`: its rows, [] when the ref has no such file, and None
    when the ref itself cannot be read."""
    if git(root, "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}").returncode != 0:
        return None
    shown = git(root, "show", f"{ref}:{rel}")
    if shown.returncode != 0:
        return []
    return [json.loads(line) for line in shown.stdout.splitlines() if line.strip()]


def read(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text("utf-8").splitlines() if line.strip()]


def shown(value) -> str:
    if value is MISSING:
        return "gone"
    text = json.dumps(value, ensure_ascii=False, sort_keys=True)
    return text if len(text) <= 60 else text[:57] + "..."


def compare(old, new, path: tuple = ()):
    """Yield (kind, path, old, new) for every way `new` fails to keep what `old` carried;
    kind is "fail" or "warn"."""
    if path in MOVES:
        return
    if path in WARNS:
        if old is not None and old != new:
            yield "warn", path, old, new
        return
    if old is None:
        return
    if isinstance(old, dict):
        if not isinstance(new, dict):
            yield "fail", path, old, new
            return
        for key, value in old.items():
            if key not in new:
                yield "fail", (*path, key), value, MISSING
            else:
                yield from compare(value, new[key], (*path, key))
        return
    if isinstance(old, list):
        if not isinstance(new, list) or len(new) < len(old):
            yield "fail", path, old, new
            return
        for index, value in enumerate(old):
            yield from compare(value, new[index], (*path, index))
        return
    if old != new:
        yield "fail", path, old, new


def problems(rel: str, tree: list[dict], before: list[dict]) -> tuple[list[str], list[str]]:
    """(failures, warnings) for one file, the tree against its published rows."""
    fails, warns = [], []
    here = {row["id"]: row for row in tree}
    for old in before:
        new = here.get(old["id"])
        if new is None:
            fails.append(f"{rel}: {old['id']} is published, and gone from the tree")
            continue
        if rel in IMMUTABLE:
            if new != old:
                fails.append(f"{rel}: {old['id']} records what a capture showed; it never changes")
            continue
        for kind, path, was, now in compare(old, new):
            where = ".".join(str(p) for p in path) or "(the row)"
            line = f"{rel}: {old['id']} {where}: {shown(was)} -> {shown(now)}"
            (fails if kind == "fail" else warns).append(line)
    return fails, warns


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("root", nargs="?", default=".", help="repository root (default: .)")
    args = parser.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    root = Path(args.root).resolve()
    ref = os.environ.get("OATH_PUBLISHED_REF", "origin/main")
    fails, warns, rows, held = [], [], 0, 0
    for rel in FILES:
        before = published(root, ref, rel)
        if before is None:
            print(
                f"FAIL  cannot read the published rows at {ref}; fetch it "
                "(git fetch origin main) and run again. Nothing was checked."
            )
            return 1
        tree = read(root / rel)
        rows += len(tree)
        held += len(before)
        f, w = problems(rel, tree, before)
        fails += f
        warns += w
    for line in warns:
        print(f"WARN  {line}")
    if fails:
        print(f"FAIL  {len(fails)} published facts removed or changed against {ref}:")
        for line in fails:
            print(f"      {line}")
        print(
            "      A published row stays and its facts only accrue (INVARIANTS.md §14). A "
            "row a later capture no longer lists is carried as published, with the change "
            "recorded as a row of its own; a fact the source now states otherwise is a "
            "correction a person makes, with the evidence."
        )
        return 1
    print(
        f"OK    {rows:,} rows in the register; {held:,} published at {ref}, every one present, "
        "and every published fact still carried"
        + (f"; {len(warns)} notes or source hashes moved, shown above." if warns else ".")
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
