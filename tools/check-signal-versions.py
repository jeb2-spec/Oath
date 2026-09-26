#!/usr/bin/env python3
"""Silent redefinition of a Signal is prohibited. INVARIANTS.md §11; METHODOLOGY.md §3.3.

Compares `data/signals.ndjson` in the tree with the published file, the same path on
`origin/main` (or the ref in OATH_PUBLISHED_REF; on a push to main CI sets it to main as it
stood before the push), and fails when:

  1. a published Signal row is missing, or differs in any byte, from the tree's: a change
     to a published definition, its wording included, is a new version, never an edit, and
     so is a change to either implementation or the known-answer cases, whose SHA-256 the
     row carries (`implementation`), because the code is part of the criteria
     (METHODOLOGY.md §3.2);
  2. a version above 1 does not name, in `supersedes`, the version below it, or that
     version's row is not in the ledger;
  3. a superseded version's definition file, `docs/signals/<slug>.v<n>.md`, is gone, so the
     old version could no longer be read in full;
  4. the current definition, `docs/signals/<slug>.md`, is not the latest version of its slug.

The comparison is stricter than the tuple INVARIANTS.md §11 names, because METHODOLOGY.md
§3.3 says a change of any kind is a new version, and a stricter gate cannot soften the
invariant. It fails rather than passes when it cannot read the published file at all.
Standard library.

    python tools/check-signal-versions.py

Example of a failing input: one word of a published Signal's not_saying changed in
docs/signals/, and the runner's regenerated row committed without a version bump.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

SIGNALS = "data/signals.ndjson"
DEFINITIONS = "docs/signals"


def canonical(row: dict) -> str:
    return json.dumps(row, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def git(root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-C", str(root), *args], capture_output=True, text=True, encoding="utf-8"
    )


def published(root: Path, ref: str, rel: str) -> list[dict] | None:
    if git(root, "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}").returncode != 0:
        return None
    shown = git(root, "show", f"{ref}:{rel}")
    if shown.returncode != 0:
        return []
    return [json.loads(line) for line in shown.stdout.splitlines() if line.strip()]


def problems(root: Path, tree: list[dict], before: list[dict]) -> list[str]:
    out = []
    here = {row["id"]: row for row in tree}
    for old in before:
        new = here.get(old["id"])
        if new is None:
            out.append(f"{old['id']}: published, and gone from data/signals.ndjson")
        elif canonical(new) != canonical(old):
            changed = sorted(k for k in set(old) | set(new) if old.get(k) != new.get(k))
            out.append(
                f"{old['id']}: published, and redefined in place ({', '.join(changed)}); "
                "a change is a new version"
            )
    latest: dict[str, int] = {}
    for row in tree:
        latest[row["slug"]] = max(latest.get(row["slug"], 0), row["version"])
        if row["version"] > 1:
            below = f"sg:{row['slug']}:v{row['version'] - 1}"
            if row.get("supersedes") != below:
                out.append(f"{row['id']}: supersedes {row.get('supersedes')}, not {below}")
            elif below not in here:
                out.append(f"{row['id']}: the version it supersedes, {below}, is not in the ledger")
    for row in tree:
        if row["version"] < latest[row["slug"]]:
            kept = root / DEFINITIONS / f"{row['slug']}.v{row['version']}.md"
            if not kept.is_file():
                out.append(
                    f"{row['id']}: superseded, and its definition "
                    f"{kept.relative_to(root).as_posix()} is gone"
                )
    for slug, version in sorted(latest.items()):
        current = root / DEFINITIONS / f"{slug}.md"
        if not current.is_file():
            out.append(f"{slug}: no current definition at {current.relative_to(root).as_posix()}")
        elif f"version: {version}\n" not in current.read_text("utf-8"):
            out.append(f"{slug}: {current.relative_to(root).as_posix()} is not version {version}")
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("root", nargs="?", default=".", help="repository root (default: .)")
    args = parser.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    root = Path(args.root).resolve()
    ref = os.environ.get("OATH_PUBLISHED_REF", "origin/main")
    path = root / SIGNALS
    tree = (
        [json.loads(line) for line in path.read_text("utf-8").splitlines() if line.strip()]
        if path.is_file()
        else []
    )
    before = published(root, ref, SIGNALS)
    if before is None:
        print(
            f"FAIL  cannot read the published Signals at {ref}; fetch it "
            "(git fetch origin main) and run again. Nothing was checked."
        )
        return 1
    found = problems(root, tree, before)
    if found:
        print(f"FAIL  {len(found)} Signal definitions changed without a new version:")
        for line in found:
            print(f"      {line}")
        return 1
    print(
        f"OK    {len(tree)} Signal {'version' if len(tree) == 1 else 'versions'}; "
        f"{len(before)} published at {ref}, each unchanged; "
        "every later version names the one it supersedes, and every earlier one stays readable."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
