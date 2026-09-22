#!/usr/bin/env python3
"""Check that every section cross-reference in the repository's Markdown resolves.

Gate for COUNCIL.md §5, failure mode 7 (a standard cited but not linked), turned on
the project's own documents. It catches a sentence that cites `INVARIANTS.md §14` when
the ranking rule is §13, an in-file anchor such as `[§13](#13-the-meta-invariant)`
whose heading does not exist, a `README §3` in a file that has no section 3, and a
relative link to a Markdown file that is not in the repository.

Example of a failing input, as one line in any tracked .md file:

    Enforced by INVARIANTS.md §99.

What it cannot catch, stated so nobody reads a green run as more than it is: a live
reference to the wrong section. `INVARIANTS.md §14` resolves whenever §14 exists, even
when the writer meant §13. Of the eight references corrected in the founding's first
Council session, this gate would have caught two. The other six stay a reading
discipline (COUNCIL.md §5 mode 7) until a citation convention makes them mechanical.

Standard-library Python 3.11+. Exits 0 when every reference resolves, 1 otherwise.
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

HEADING = re.compile(r"^#{1,6}\s+(.*?)\s*#*\s*$")
BOLD_NUMBERED = re.compile(r"^\*\*(\d+(?:\.\d+)+)\b")  # **5.2** and **5.2 Title.** alike
KEY = re.compile(
    r"^(?:§\s*)?(Stage\s+\d+|[A-Z]{1,2}\.?\d+(?:\.\d+)*|\d+(?:\.\d+)*|[IVX]+)\.?(?=\s|$)"
)

SECTION_REF = re.compile(r"§\s*(?P<key>[A-Z]{0,2}\.?\d+(?:\.\d+)*)")
FILE_BEFORE = re.compile(r"\[?(?P<file>[A-Z][A-Z_-]{2,})(?:\.md)?\]?(?:\([^)]*\))?\s*$")
INVARIANT_BEFORE = re.compile(r"\bInvariants?\s*$")
LEGAL_BEFORE = re.compile(
    r"(U\.S\.C\.|C\.F\.R\.|CFR|Art\.\s+[IVX]+|Pub\.\s*L\.|Ch\.)\s*(app\.\s*\d+\s*)?$"
)
STAGE_REF = re.compile(r"\b(?P<file>[A-Z][A-Z_-]{2,})(?:\.md)?\s+Stage\s+(?P<key>\d+)\b")
VOW_REF = re.compile(r"\bVow\s+(?P<key>[IVX]+)\b")
GATE_REF = re.compile(r"\bRubric gate\s+(?P<key>\d)\b")
LINK = re.compile(r"\]\((?P<target>[^)\s]+)\)")


def tracked_markdown(root: Path, scan_only: bool = True) -> list[Path]:
    """Every tracked .md file under root, via git when available, else a walk.

    Files under `fixtures/` are inputs to tools, not documents, and are left out of a
    repository scan; a fixture directory passed as the root is scanned in full. Pass
    `scan_only=False` to get them back, which is how a link *to* a fixture document
    resolves: the file exists and may be linked, it is simply never read for sections.
    """
    files: list[Path] = []
    try:
        out = subprocess.run(
            ["git", "-C", str(root), "ls-files", "-z", "--", "*.md"],
            capture_output=True,
            check=True,
            text=True,
        ).stdout
        files = [root / p for p in out.split("\0") if p]
    except (OSError, subprocess.CalledProcessError):
        pass
    if not files:
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d not in {".git", "node_modules"}]
            files.extend(Path(dirpath) / f for f in filenames if f.endswith(".md"))
    if not scan_only:
        return sorted(files)
    return sorted(p for p in files if p.relative_to(root).parts[:1] != ("fixtures",))


def slug(heading: str) -> str:
    """GitHub's anchor rule: lowercase, drop punctuation, spaces to hyphens."""
    text = re.sub(r"[^\w\s-]", "", heading.lower())
    return re.sub(r"\s", "-", text.strip())


def sections(text: str) -> tuple[set[str], set[str]]:
    """The section keys and anchor slugs a file defines."""
    keys, slugs = set(), set()
    in_fence = False
    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        m = HEADING.match(line)
        if m:
            heading = re.sub(r"[*_`]", "", m.group(1))
            slugs.add(slug(m.group(1)))
            k = KEY.match(heading)
            if k:
                keys.add(re.sub(r"\s+", " ", k.group(1)))
            continue
        b = BOLD_NUMBERED.match(line)
        if b:
            keys.add(b.group(1))
    return keys, slugs


def check(root: Path) -> tuple[list[str], int]:
    """Return (failures, references_checked)."""
    files = tracked_markdown(root)
    linkable = set(tracked_markdown(root, scan_only=False))
    by_name = {p.name.upper(): p for p in files if p.parent == root}
    defined = {p: sections(p.read_text(encoding="utf-8", errors="replace")) for p in files}
    failures: list[str] = []
    checked = 0

    def resolve(where: Path, lineno: int, target: Path | None, key: str, shown: str) -> None:
        nonlocal checked
        checked += 1
        if target is None or target not in defined:
            failures.append(
                f"{where.relative_to(root)}:{lineno}: {shown} names a file that is not tracked"
            )
            return
        if key not in defined[target][0]:
            failures.append(
                f"{where.relative_to(root)}:{lineno}: {shown} does not resolve "
                f"({target.name} has no section {key})"
            )

    for path in files:
        text = path.read_text(encoding="utf-8", errors="replace")
        in_fence = False
        for lineno, line in enumerate(text.splitlines(), 1):
            if line.lstrip().startswith("```"):
                in_fence = not in_fence
                continue
            if in_fence:
                continue  # code blocks hold templates and transcripts, not references
            last_file: Path | None = None
            for m in SECTION_REF.finditer(line):
                prefix = line[: m.start()]
                key = m.group("key")
                fb = FILE_BEFORE.search(prefix)
                if INVARIANT_BEFORE.search(prefix):
                    target = by_name.get("INVARIANTS.MD")
                    last_file = target
                    resolve(path, lineno, target, key, f"Invariant §{key}")
                elif fb and fb.group("file") + ".MD" in by_name:
                    target = by_name[fb.group("file") + ".MD"]
                    last_file = target
                    resolve(path, lineno, target, key, f"{fb.group('file')}.md §{key}")
                elif last_file is not None and key.isdigit() and not LEGAL_BEFORE.search(prefix):
                    resolve(
                        path,
                        lineno,
                        last_file,
                        key,
                        f"{last_file.name} §{key} (continued)",
                    )
                # a bare § with no project file named earlier on the line is a legal citation
            for m in STAGE_REF.finditer(line):
                name = m.group("file") + ".MD"
                if name in by_name:
                    resolve(
                        path,
                        lineno,
                        by_name[name],
                        f"Stage {m.group('key')}",
                        m.group(0),
                    )
            for m in VOW_REF.finditer(line):
                resolve(path, lineno, by_name.get("CHARTER.MD"), m.group("key"), m.group(0))
            for m in GATE_REF.finditer(line):
                resolve(path, lineno, by_name.get("RUBRIC.MD"), m.group("key"), m.group(0))
            for m in LINK.finditer(line):
                target = m.group("target")
                if target.startswith(("http://", "https://", "mailto:")):
                    continue
                file_part, _, anchor = target.partition("#")
                dest = path if not file_part else (path.parent / file_part).resolve()
                if file_part and not file_part.endswith(".md"):
                    continue
                checked += 1
                if file_part and dest not in defined:
                    if dest in linkable:
                        continue  # tracked but never scanned, so its anchors are unknown
                    failures.append(
                        f"{path.relative_to(root)}:{lineno}: link to {file_part} "
                        "names a file that is not tracked"
                    )
                    continue
                if anchor and anchor not in defined[dest][1]:
                    failures.append(
                        f"{path.relative_to(root)}:{lineno}: anchor #{anchor} "
                        f"has no heading in {dest.name}"
                    )
    return failures, checked


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__.split("\n\n")[0],
        epilog=(
            "Gate: COUNCIL.md §5 mode 7, a standard cited but not linked, applied to the "
            "repository's own section references, anchors, and relative Markdown links.\n"
            "Catches: `INVARIANTS.md §99`, `[§13](#13-the-meta-invariant)` with no such "
            "heading, `README §3` where README has no section 3, `](docs/missing.md)`.\n"
            "Ignores: legal citations (`5 CFR § 2635`, `18 U.S.C. § 201`) and non-numeric "
            "section names."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("root", nargs="?", default=".", help="repository root (default: .)")
    args = parser.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")  # the section sign survives a Windows console
    root = Path(args.root).resolve()
    failures, checked = check(root)
    for f in failures:
        print(f"FAIL  {f}")
    if failures:
        print(f"\n{len(failures)} of {checked} cross-references do not resolve.")
        return 1
    print(
        f"OK    {checked} cross-references resolve "
        f"across {len(tracked_markdown(root))} Markdown files."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
