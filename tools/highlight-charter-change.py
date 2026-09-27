#!/usr/bin/env python3
"""Silent softening of the antidrift core is not possible. INVARIANTS.md §17, the meta-invariant.

Five files hold the rules that hold every other rule: CHARTER.md, RUBRIC.md, INVARIANTS.md,
BYLAWS.md, COUNCIL.md. §17 says none of the invariants may be removed, softened or weakened
without a pull request that names the gate, explains the reason, and is approved by the
maintainer, and it names this gate: diff the five against `main`, and where any has changed,
emit a highlighted notice and require both the Council's review and the maintainer's written
justification before it can merge.

So this gate compares the five with the published record, the same paths on `origin/main` (or
the ref in OATH_PUBLISHED_REF; on a push to main CI sets it to main as it stood before the
push), and:

  1. where none has changed, prints each file's SHA-256 and the sections it holds, so the claim
     "the antidrift core is unchanged" is a thing a reader sees rather than infers from silence;
  2. where one has changed, prints the diff under a highlighted CI notice, and **requires a row
     in `data/doctrine-amendments.ndjson`** naming that file, the sections it touches, whether
     the change adds or narrows, the reason, the Council reading that read it, and the
     maintainer's approval. A change with no such row fails, and says what is missing;
  3. where a row names a file that did not change, fails too. A justification for an amendment
     nobody made is the same rot as a guard nobody measures: it stands in the record claiming a
     decision was weighed, and the next reader believes it.

Why a row in the register rather than a PR body. A PR body is not in the record: it cannot be
fetched with the build, a later reader holding only the repository cannot read it, and nothing
re-reads it. COUNCIL.md §7 already puts an override in `data/council-overrides.ndjson`, sealed
with the build, for exactly that reason. An amendment to the core is at least as consequential as
an override of one finding, so it is recorded the same way: a row, under `data/`, inside the
seal, where every future reader meets it.

The gate never decides whether an amendment is right. It decides whether it was made in the open.

    python3 tools/highlight-charter-change.py
    python3 tools/highlight-charter-change.py <root>
"""

from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

# The antidrift core, in the order INVARIANTS §17 names it.
CORE = ("CHARTER.md", "RUBRIC.md", "INVARIANTS.md", "BYLAWS.md", "COUNCIL.md")
LEDGER = "data/doctrine-amendments.ndjson"
# What a row must carry for the amendment to be in the open. Each is a thing a later reader needs
# and cannot recover from the diff: the diff shows what changed, never who weighed it or why.
REQUIRED = ("file", "sections", "direction", "because", "council", "approved_by", "decided_at")
DIRECTIONS = ("adds", "narrows", "widens", "clarifies")
# §17's own words: a change that removes, softens or weakens carries the heaviest burden, so the
# row says which of those it is and the gate prints it in the notice.
SOFTENING = ("widens",)


def git(root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-C", str(root), *args], capture_output=True, text=True, encoding="utf-8"
    )


def readable(root: Path, ref: str) -> bool:
    return git(root, "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}").returncode == 0


def published_text(root: Path, ref: str, rel: str) -> str:
    """The file's text as published at `ref`; empty when the ref has no such file."""
    shown = git(root, "show", f"{ref}:{rel}")
    return shown.stdout if shown.returncode == 0 else ""


def digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sections(text: str) -> list[str]:
    """The headings a doctrine file holds, as a reader cites them: "§17", "Vow III", "gate 4"."""
    found = []
    for line in text.splitlines():
        if not line.startswith("#"):
            continue
        head = line.lstrip("#").strip()
        marked = re.match(r"(§\s?\d+|Vow [IVX]+|[Gg]ate \d+|\d+\.\d*)", head)
        found.append(marked.group(1).replace("§ ", "§") if marked else head)
    return found


def rows(root: Path) -> list[dict]:
    path = root / LEDGER
    if not path.is_file():
        return []
    out = []
    for n, line in enumerate(path.read_text("utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError as bad:
            raise SystemExit(f"FAIL  {LEDGER}:{n} does not parse: {bad}") from bad
    return out


def incomplete(row: dict) -> list[str]:
    """What a justification row is missing, in the words the gate prints. A row that names a file
    and nothing else is a row that makes the amendment look weighed without weighing it."""
    missing = [field for field in REQUIRED if not row.get(field)]
    if row.get("direction") and row["direction"] not in DIRECTIONS:
        missing.append(f"direction (one of {', '.join(DIRECTIONS)}, not {row['direction']!r})")
    if row.get("sections") and not isinstance(row["sections"], list):
        missing.append("sections (a list of the sections the amendment touches)")
    because = row.get("because") or ""
    if because and len(because.split()) < 12:
        # §17 asks the reason to name what problem the current text causes and what the change is
        # expected to fix. Two of those do not fit in a clause.
        missing.append(
            "because (a reason, not a label: what the current text costs, and what this fixes)"
        )
    council = row.get("council") or {}
    if isinstance(council, dict):
        for field in ("prompt_sha", "read_at", "seats"):
            if not council.get(field):
                missing.append(f"council.{field}")
    elif council:
        missing.append("council (an object: prompt_sha, read_at, seats, findings)")
    return missing


def notice(kind: str, text: str) -> str:
    """A CI annotation where the runner reads them, and a plain line everywhere else. §17 asks for
    a highlighted notice, and highlighted means the runner's own highlight, not bold text."""
    if os.environ.get("GITHUB_ACTIONS") == "true":
        one = text.replace("\n", "%0A").replace("\r", "")
        return f"::{kind}::{one}"
    return text


def check(root: Path, ref: str) -> int:
    changed: dict[str, tuple[str, str]] = {}
    for rel in CORE:
        path = root / rel
        if not path.is_file():
            print(f"FAIL  {rel} is part of the antidrift core and is missing.")
            return 1
        now, before = path.read_text("utf-8"), published_text(root, ref, rel)
        if before and now != before:
            changed[rel] = (before, now)

    ledger = rows(root)
    bad = 0

    if not changed:
        print(f"OK    the antidrift core is unchanged from {ref}. INVARIANTS §17.")
        for rel in CORE:
            text = (root / rel).read_text("utf-8")
            marks = sections(text)
            print(f"      {digest(text)[:16]}…  {rel}  ({len(marks)} sections)")
        # A row for an amendment nobody made claims a decision was weighed. It is not a stale
        # comment; it is a false entry in the record, and the next reader believes it.
        for row in ledger:
            if row.get("file") in CORE:
                print(
                    notice(
                        "error",
                        f"{LEDGER} carries an amendment of {row['file']} and {row['file']} is "
                        f"unchanged from {ref}. Either the amendment is not in this tree, or the "
                        "row is a justification for a change nobody made. Remove the row or make "
                        "the change.",
                    )
                )
                bad += 1
        return 1 if bad else 0

    print(
        notice(
            "warning",
            "The antidrift core changed. "
            f"{', '.join(sorted(changed))} differ from {ref}. INVARIANTS §17 requires the "
            "Council's review and the maintainer's written justification, recorded in "
            f"{LEDGER}, before this can merge.",
        )
    )
    for rel, (before, now) in sorted(changed.items()):
        moved = [s for s in sections(now) if s not in sections(before)]
        gone = [s for s in sections(before) if s not in sections(now)]
        print(f"\n--- {rel} ---")
        print(f"      {digest(before)[:16]}…  as published at {ref}")
        print(f"      {digest(now)[:16]}…  in this tree")
        if moved:
            print(f"      sections added: {', '.join(moved)}")
        if gone:
            print(notice("error", f"{rel}: sections gone: {', '.join(gone)}"))
        diff = difflib.unified_diff(
            before.splitlines(), now.splitlines(), f"{ref}:{rel}", rel, lineterm="", n=2
        )
        for line in diff:
            print(f"      {line}")

        mine = [row for row in ledger if row.get("file") == rel]
        if not mine:
            print(
                notice(
                    "error",
                    f"{rel} changed and no row of {LEDGER} names it. Add one: the file, the "
                    "sections, the direction, the reason (what the current text costs and what "
                    "this fixes), the Council reading that read it (its prompt blob SHA, when, "
                    "which seats), who approved it and when. COUNCIL §8 makes the prompt's blob "
                    "SHA the reproducibility guarantee, so a reading with no SHA is a reading "
                    "nobody can repeat.",
                )
            )
            bad += 1
            continue
        for row in mine:
            gaps = incomplete(row)
            if gaps:
                print(
                    notice(
                        "error",
                        f"{rel}: its row in {LEDGER} is missing {', '.join(gaps)}. An amendment "
                        "recorded in part reads, to a later reader, as an amendment weighed in "
                        "part.",
                    )
                )
                bad += 1
                continue
            heavy = " (this SOFTENS the core)" if row["direction"] in SOFTENING else ""
            print(
                f"      justified{heavy}: {row['direction']} {', '.join(row['sections'])}; "
                f"read by seats {', '.join(row['council']['seats'])} at "
                f"{row['council']['read_at']} against prompt {row['council']['prompt_sha'][:12]}…; "
                f"approved by {row['approved_by']} on {row['decided_at']}"
            )

    for row in ledger:
        if row.get("file") in CORE and row["file"] not in changed:
            print(
                notice(
                    "error",
                    f"{LEDGER} carries an amendment of {row['file']} and {row['file']} is "
                    f"unchanged from {ref}.",
                )
            )
            bad += 1

    if bad:
        print(
            f"\nFAIL  {bad} amendment{'s' if bad != 1 else ''} to the antidrift core is not in "
            "the open. Silent softening is what §17 exists to prevent; loud softening is "
            "allowed, and this is how it is made loud."
        )
        return 1
    print(
        f"\nOK    {len(changed)} file{'s' if len(changed) != 1 else ''} of the antidrift core "
        f"changed, each with its justification in {LEDGER}: the Council's reading, the reason, "
        "and the maintainer's approval. The notice above is the highlight §17 asks for."
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", default=".", help="repository root (default: .)")
    args = parser.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    root = Path(args.root).resolve()
    ref = os.environ.get("OATH_PUBLISHED_REF", "origin/main")
    if not readable(root, ref):
        print(
            f"FAIL  cannot read the antidrift core as published at {ref}; fetch it "
            "(git fetch origin main) and run again. Nothing was checked, and a gate that cannot "
            "read the record fails rather than pass."
        )
        return 1
    return check(root, ref)


if __name__ == "__main__":
    sys.exit(main())
