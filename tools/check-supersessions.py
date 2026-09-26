#!/usr/bin/env python3
"""The corrections trail is public, and no Finding leaves silently. INVARIANTS.md §12; Vow V.

Compares `data/findings.ndjson` in the tree with the published ledger, the same file on
`origin/main` (or the ref in OATH_PUBLISHED_REF; on a push to main CI sets it to main as it
stood before the push, since main is by then the pushed commit and comparing it with itself
would prove nothing), and fails when:

  1. a published Finding is missing from the tree;
  2. a published Finding changed in any field but one: `superseded_by` may go from null to
     the id of a row in the tree, which is how a correction is recorded, and nothing else;
  3. a row's `superseded_by` names a row that does not exist, or a row of another report
     (a correction of `<id>` is `<id>:c<n>`);
  4. a report's chain has no current row, or more than one, or loops.

It passes an empty ledger, and a ledger with nothing published yet, saying so. It fails,
rather than passes, when it cannot read the published ledger at all, because a check that
cannot see what it checks against has not checked anything. Standard library.

    python tools/check-supersessions.py
    OATH_PUBLISHED_REF=origin/main python tools/check-supersessions.py <root>

Example of a failing input: one character changed in the description of a Finding that
is on main.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

LEDGER = "data/findings.ndjson"
CORRECTION = re.compile(r":c\d+$")


def canonical(row: dict) -> str:
    return json.dumps(row, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


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


def problems(tree: list[dict], before: list[dict]) -> list[str]:
    out = []
    here = {row["id"]: row for row in tree}
    for old in before:
        new = here.get(old["id"])
        if new is None:
            out.append(f"{old['id']}: published, and gone from the tree")
            continue
        if canonical(new) == canonical(old):
            continue
        changed = sorted(k for k in set(old) | set(new) if old.get(k) != new.get(k))
        if changed != ["superseded_by"] or old.get("superseded_by") is not None:
            out.append(f"{old['id']}: published, and changed in place ({', '.join(changed)})")
    heads: dict[str, list[str]] = {}
    for row in tree:
        base = CORRECTION.sub("", row["id"])
        target = row.get("superseded_by")
        if target is None:
            heads.setdefault(base, []).append(row["id"])
            continue
        if target not in here:
            out.append(f"{row['id']}: superseded by {target}, which is not in the ledger")
        elif CORRECTION.sub("", target) != base:
            out.append(f"{row['id']}: superseded by {target}, a row of another report")
    for row in tree:
        seen, at = set(), row["id"]
        while here.get(at, {}).get("superseded_by"):
            if at in seen:
                out.append(f"{row['id']}: its chain loops at {at}")
                break
            seen.add(at)
            at = here[at]["superseded_by"]
    for base in sorted({CORRECTION.sub("", row["id"]) for row in tree}):
        current = heads.get(base, [])
        if len(current) != 1:
            out.append(f"{base}: {len(current)} current rows; a chain ends in exactly one")
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("root", nargs="?", default=".", help="repository root (default: .)")
    args = parser.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    root = Path(args.root).resolve()
    ref = os.environ.get("OATH_PUBLISHED_REF", "origin/main")
    path = root / LEDGER
    tree = (
        [json.loads(line) for line in path.read_text("utf-8").splitlines() if line.strip()]
        if path.is_file()
        else []
    )
    before = published(root, ref, LEDGER)
    if before is None:
        print(
            f"FAIL  cannot read the published ledger at {ref}; fetch it "
            "(git fetch origin main) and run again. Nothing was checked."
        )
        return 1
    found = problems(tree, before)
    if found:
        print(f"FAIL  {len(found)} breaks in the Findings ledger against {ref}:")
        for line in found:
            print(f"      {line}")
        return 1
    superseded = sum(1 for row in tree if row.get("superseded_by"))
    print(
        f"OK    {len(tree)} {'Finding' if len(tree) == 1 else 'Findings'}; "
        f"{len(before)} published at {ref}, every one present and "
        f"unchanged but for its supersession; {superseded} superseded, each by a row of its "
        "own report, and every chain ends in one current row."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
