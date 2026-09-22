#!/usr/bin/env python3
"""The session-start doctor. Read back whether this session is arriving whole.

NEXT.md Phase 1 T.6, modelled on the errata doctor. It answers, in order:

  1. Is the memory chain whole? MEMORY.md exists, every file it links exists, and
     the three files CLAUDE.md orders (where-we-are, who-i-am-for-oath, founding)
     appear in that order. Is the local auto-memory folder a junction to this
     repository's memory, as on the maintainer's machine?
  2. Is the deeper ground reachable? The Vera memory beside this repository, and
     whether its identity files are in that checkout's working tree or must be
     read from origin/main, as CLAUDE.md says.
  3. Can the session recite the Charter? The five vows are printed from CHARTER.md
     as the read-back; fewer or more than five is red.
  4. Which invariant gates exist, and do they pass? Every gate INVARIANTS.md names
     is listed as present or planned; every present gate is run.
  5. Does the branch track main? Ahead and behind against origin/main, and whether
     the working tree is clean. With --fetch, origin is fetched first.
  6. Is the toolchain at the floor? Python 3.11+, Node 20+, Ruff and Pytest.

Prints one line per check, [ok], [warn], or [red], and exits non-zero on any red.
A warning never fails the doctor; a red always does. Standard-library Python 3.11+.

    python3 scripts/oath-doctor.py
    python3 scripts/oath-doctor.py --fetch
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

ORDERED_MEMORY = ["where-we-are.md", "who-i-am-for-oath.md", "founding-of-oath.md"]
VERA_MEMORY = Path(r"C:\Users\jared\Apps\VeraAgent\.claude\memory")
VERA_IDENTITY = ["who-i-am-opus.md", "who-i-am-fable.md"]

# Every gate INVARIANTS.md names, by section, with the tool that enforces it.
GATES = [
    ("§1 verdict language", "tools/lint-verdict-language.py"),
    ("§2 §3 §4 §6 schemas", "tools/validate-schemas.py"),
    ("§5 no aggregator sole", "tools/check-aggregator-sole.py"),
    ("§7 frame on every surface", "tools/lint-frame-presence.py"),
    ("§9 seal covers disclosures", "tools/verify.py"),
    ("§9 seal is not decorative", "tools/tamper-test.py"),
    ("§10 no secrets", "tools/scan-secrets.py"),
    ("§11 no silent redefinition", "tools/check-signal-versions.py"),
    ("§12 supersessions chained", "tools/check-supersessions.py"),
    ("§13 no ranking", "tools/lint-no-ranking.py"),
    ("§14 facts stay", "tools/check-removals.py"),
    ("§15 contributor COI", "tools/check-coi-disclosure.py"),
    ("§16 evidence bundle", "tools/check-evidence-bundle.py"),
    ("§17 meta-invariant highlight", "tools/highlight-charter-change.py"),
    ("Council §5 mode 7 cross-references", "tools/check-crossrefs.py"),
    ("ECOSYSTEM §2.4 the mark is struck and legible", "tools/check-mark.py"),
]


class Report:
    def __init__(self) -> None:
        self.lines: list[str] = []
        self.red = 0
        self.warn = 0

    def ok(self, text: str) -> None:
        self.lines.append(f"[ok]   {text}")

    def warning(self, text: str) -> None:
        self.warn += 1
        self.lines.append(f"[warn] {text}")

    def bad(self, text: str) -> None:
        self.red += 1
        self.lines.append(f"[red]  {text}")

    def section(self, title: str) -> None:
        self.lines.append(f"\n{title}")


def git(root: Path, *args: str) -> str | None:
    try:
        return subprocess.run(
            ["git", "-C", str(root), *args], capture_output=True, text=True, check=True
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def check_memory(root: Path, rep: Report) -> None:
    rep.section("Memory")
    index = root / ".claude" / "memory" / "MEMORY.md"
    if not index.is_file():
        rep.bad(".claude/memory/MEMORY.md is missing; the session cannot arrive")
        return
    text = index.read_text(encoding="utf-8")
    links = re.findall(r"\]\(([a-z0-9-]+\.md)\)", text)
    for link in dict.fromkeys(links):
        if (index.parent / link).is_file():
            rep.ok(f"memory index links {link}, present")
        else:
            rep.bad(f"memory index links {link}, which is missing")
    positions = [text.find(f"({name})") for name in ORDERED_MEMORY]
    if all(p >= 0 for p in positions) and positions == sorted(positions):
        rep.ok("the three arrival files are indexed in the order CLAUDE.md gives")
    else:
        rep.bad("the arrival files are not indexed in the order CLAUDE.md gives")
    arrival = index.parent / "where-we-are.md"
    if arrival.is_file():
        stamp = re.search(r"\*Last updated: ([^*]+)\*", arrival.read_text(encoding="utf-8"))
        rep.ok(f"where-we-are: {stamp.group(1).strip() if stamp else 'no last-updated line'}")
    slug = re.sub(r"[:\\/]", "-", str(root)).strip("-")  # C:\a\b becomes C--a-b
    local = Path.home() / ".claude" / "projects" / slug / "memory"
    if local.exists() and Path(os.path.realpath(local)) == Path(os.path.realpath(index.parent)):
        rep.ok("local auto-memory is a junction to this repository's memory")
    elif local.exists():
        rep.warning(f"local auto-memory at {local} is not a junction to this repository's memory")
    else:
        rep.warning(f"no local auto-memory folder at {local} (fine in a cloud session)")


def check_deeper_ground(rep: Report) -> None:
    rep.section("Deeper ground")
    if not VERA_MEMORY.is_dir():
        rep.warning(
            "the Vera memory is not reachable; the seed here is the bridge, and it is enough"
        )
        return
    branch = git(VERA_MEMORY, "branch", "--show-current") or "?"
    stale: list[str] = []
    for name in VERA_IDENTITY:
        path = VERA_MEMORY / name
        recorded = git(VERA_MEMORY, "rev-parse", f"origin/main:.claude/memory/{name}")
        on_disk = git(VERA_MEMORY, "hash-object", str(path)) if path.is_file() else None
        if recorded is None or on_disk != recorded:
            stale.append(name)
    if not stale:
        rep.ok(f"Vera memory reachable; identity files match origin/main (checkout on {branch})")
    else:
        rep.warning(
            f"Vera checkout is on '{branch}'; {', '.join(stale)} on disk differ from origin/main "
            "or are absent; read them with git show origin/main:.claude/memory/<file>, as "
            "CLAUDE.md says"
        )


def check_charter(root: Path, rep: Report) -> None:
    rep.section("Charter")
    charter = root / "CHARTER.md"
    if not charter.is_file():
        rep.bad("CHARTER.md is missing")
        return
    vows = re.findall(r"^## ([IVX]+)\. (.+)$", charter.read_text(encoding="utf-8"), flags=re.M)
    if len(vows) == 5:
        for numeral, title in vows:
            rep.ok(f"Vow {numeral}. {title}")
    else:
        rep.bad(f"CHARTER.md has {len(vows)} vows, not five")


def check_gates(root: Path, rep: Report) -> None:
    rep.section("Gates")
    for label, tool in GATES:
        path = root / tool
        if not path.is_file():
            rep.warning(f"{label}: {tool} planned, not landed")
            continue
        proc = subprocess.run(
            [sys.executable, str(path), str(root)], capture_output=True, text=True, encoding="utf-8"
        )
        first = (proc.stdout.strip().splitlines() or [""])[0]
        if proc.returncode == 0:
            rep.ok(f"{label}: {tool} passes ({first[:70]})")
        else:
            rep.bad(f"{label}: {tool} FAILS ({first[:70]})")


def check_branch(root: Path, rep: Report, fetch: bool) -> None:
    rep.section("Branch")
    branch = git(root, "branch", "--show-current")
    if branch is None:
        rep.bad("not a git repository, or git is not available")
        return
    branch = branch or "a detached HEAD"  # CI checks out the commit, not the branch
    if fetch and git(root, "fetch", "origin", "--quiet") is None:
        rep.warning("could not fetch origin; comparing against the last known origin/main")
    counts = git(root, "rev-list", "--left-right", "--count", "origin/main...HEAD")
    if counts:
        behind, ahead = counts.split()
        rep.ok(f"on {branch}: {ahead} ahead of origin/main, {behind} behind")
        if int(behind) > 0:
            rep.warning(
                "origin/main has moved since this branch was cut; reconcile before you push"
            )
    else:
        rep.warning(f"on {branch}: origin/main is not known here")
    dirty = git(root, "status", "--porcelain")
    if dirty:
        rep.warning(f"working tree has {len(dirty.splitlines())} uncommitted paths")
    else:
        rep.ok("working tree clean")


def check_toolchain(rep: Report) -> None:
    rep.section("Toolchain")
    floor = (3, 11)
    if sys.version_info[:2] >= floor:
        rep.ok(f"Python {sys.version.split()[0]}")
    else:
        rep.bad(f"Python {sys.version.split()[0]} is below the 3.11 floor")
    for module in ("ruff", "pytest"):
        proc = subprocess.run(
            [sys.executable, "-m", module, "--version"], capture_output=True, text=True
        )
        if proc.returncode == 0:
            rep.ok(f"{module} {proc.stdout.strip().split()[-1]}")
        else:
            rep.warning(
                f"{module} is not installed for this Python (python -m pip install {module})"
            )
    try:
        node = subprocess.run(["node", "--version"], capture_output=True, text=True, check=True)
        version = node.stdout.strip()
        major = int(version.lstrip("v").split(".")[0])
        (rep.ok if major >= 20 else rep.bad)(f"Node {version}")
    except (OSError, subprocess.CalledProcessError, ValueError):
        rep.warning("Node is not on the PATH")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Read back whether this session is arriving whole."
    )
    parser.add_argument("root", nargs="?", default=".", help="repository root (default: .)")
    parser.add_argument("--fetch", action="store_true", help="fetch origin before comparing")
    args = parser.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    root = Path(args.root).resolve()
    rep = Report()
    check_memory(root, rep)
    check_deeper_ground(rep)
    check_charter(root, rep)
    check_gates(root, rep)
    check_branch(root, rep, args.fetch)
    check_toolchain(rep)
    print("\n".join(rep.lines))
    print()
    if rep.red:
        print(
            f"RED   {rep.red} red, {rep.warn} warnings. Do not start until the red is understood."
        )
        return 1
    print(f"GREEN {rep.warn} warnings, no red. Read the Charter, then go be useful.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
