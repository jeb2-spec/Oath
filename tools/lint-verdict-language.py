#!/usr/bin/env python3
"""Lint every user-facing surface for the verdict-language blacklist.

INVARIANTS.md §1: verdict language is forbidden on any user-facing surface. The
blacklist (v0) is the one printed there, matched as whole words in any inflection
(corrupt, corruption, corrupted; criminal, criminally; and so on), case-insensitive.

What is scanned: the Markdown at the repository root (doctrine, prospectus,
guides), .github/, docs/ (Signal definitions and rendered pages included), src/,
fixtures/, templates/, and every data/*.ndjson row. Two places are not scanned, and
the reason is stated here so the exclusion is loud: .claude/ (the working memory,
not a surface), and docs/related-work/ (records of what neighbouring projects say
in their own names and words; they name no officeholder and are appendix, not
surface). Everything that names or describes an officeholder is scanned.

One phrase is always allowed: the register's own frame, "not evidence of
wrongdoing", which is Vow II in its own words.

Every other hit fails unless verdict-lint.allowlist at the repository root allows
it. An entry is one line, `path | context | reason`: the hit's file, a substring
the hit's line must contain, and one line saying why the word is not a verdict
there (the doctrine defines the list; a statute's own category; a neighbour's own
name). An allowlist entry that no longer matches any line is reported as stale and
fails too, so the file cannot drift. Adding a word to the blacklist takes one
approver; removing one takes two and a written justification (INVARIANTS.md §1).

Example of a failing input, as one line in any scanned file:

    The senator's late filing was dishonest.

Standard-library Python 3.11+.
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

BLACKLIST_V0 = [
    r"guilty",
    r"corrupt\w*",
    r"unethical",
    r"criminal\w*",
    r"crook\w*",
    r"disgrace\w*",
    r"shameful",
    r"should resign",
    r"broke the law",
    r"broke laws",
    r"dishonest\w*",
    r"sleaz\w*",
    r"dirty",
    r"tainted",
    r"illegal conduct",
    r"illegal act\w*",
    r"wrongdoing",
    r"malfeasance",
    r"misconduct",
]
PATTERN = re.compile(r"\b(" + "|".join(BLACKLIST_V0) + r")\b", re.IGNORECASE)
FRAME = re.compile(r"not evidence of wrongdoing", re.IGNORECASE)
ALLOWLIST = "verdict-lint.allowlist"
SCANNED_PREFIXES = (".github/", "docs/", "src/", "fixtures/", "templates/")
EXCLUDED_PREFIXES = (".claude/", "docs/related-work/", "node_modules/")


def scanned_files(root: Path) -> list[Path]:
    """Tracked files in scope, via git when available, else a walk."""
    try:
        out = subprocess.run(
            ["git", "-C", str(root), "ls-files", "-z"], capture_output=True, check=True, text=True
        ).stdout
        rels = [p for p in out.split("\0") if p]
    except (OSError, subprocess.CalledProcessError):
        rels = []
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d not in {".git", "node_modules"}]
            for f in filenames:
                rels.append((Path(dirpath) / f).relative_to(root).as_posix())
    keep: list[Path] = []
    for rel in sorted(rels):
        if rel.startswith(EXCLUDED_PREFIXES):
            continue
        root_md = "/" not in rel and rel.endswith(".md")
        in_scope = rel.startswith(SCANNED_PREFIXES) and rel.endswith(
            (".md", ".ts", ".js", ".mjs", ".py", ".json", ".html", ".txt", ".yaml", ".yml")
        )
        data_row = rel.startswith("data/") and rel.endswith(".ndjson")
        if root_md or in_scope or data_row:
            keep.append(root / rel)
    return keep


def load_allowlist(root: Path) -> list[tuple[str, str, str, int]]:
    """Entries as (path, context, reason, line number in the allowlist)."""
    path = root / ALLOWLIST
    entries: list[tuple[str, str, str, int]] = []
    if not path.is_file():
        return entries
    for lineno, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = [p.strip() for p in line.split("|", 2)]
        if len(parts) != 3 or not all(parts):
            raise ValueError(f"{ALLOWLIST}:{lineno}: expected 'path | context | reason'")
        entries.append((parts[0], parts[1], parts[2], lineno))
    return entries


def lint(root: Path) -> tuple[list[str], int, int]:
    """Return (failures, files scanned, hits allowed)."""
    entries = load_allowlist(root)
    used = [False] * len(entries)
    failures: list[str] = []
    allowed = 0
    files = scanned_files(root)
    for path in files:
        rel = path.relative_to(root).as_posix()
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for lineno, line in enumerate(text.splitlines(), 1):
            for match in PATTERN.finditer(line):
                word = match.group(0)
                if FRAME.search(line) and word.lower() == "wrongdoing":
                    continue
                hit_allowed = False
                for i, (e_path, context, _reason, _n) in enumerate(entries):
                    if e_path == rel and context in line:
                        used[i] = True
                        hit_allowed = True
                if hit_allowed:
                    allowed += 1
                    continue
                excerpt = line.strip()
                if len(excerpt) > 110:
                    start = max(0, match.start() - 50)
                    excerpt = "..." + line[start : start + 110].strip() + "..."
                failures.append(f'{rel}:{lineno}: "{word}" in: {excerpt}')
    for (e_path, context, _reason, n), was_used in zip(entries, used, strict=True):
        if not was_used:
            failures.append(
                f"{ALLOWLIST}:{n}: stale entry, no line in {e_path} contains '{context}'"
            )
    return failures, len(files), allowed


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Lint user-facing surfaces for the blacklist of INVARIANTS.md §1.",
        epilog=(
            "Gate: INVARIANTS.md §1. Catches: any blacklisted word, in any inflection, on a "
            "user-facing surface, outside the frame sentence and the reasoned allowlist; and "
            "any allowlist entry that no longer matches a line. Example failing input: "
            "'The senator's late filing was dishonest.' in a Signal definition."
        ),
    )
    parser.add_argument("root", nargs="?", default=".", help="repository root (default: .)")
    args = parser.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    root = Path(args.root).resolve()
    try:
        failures, scanned, allowed = lint(root)
    except ValueError as exc:
        print(f"FAIL  {exc}")
        return 1
    for f in failures:
        print(f"FAIL  {f}")
    if failures:
        print(f"\n{len(failures)} problems across {scanned} files ({allowed} hits allowlisted).")
        return 1
    print(f"OK    {scanned} files scanned; {allowed} hits allowlisted with a reason;")
    print("      no verdict language.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
