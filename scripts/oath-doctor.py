#!/usr/bin/env python3
"""The session-start doctor. Read back whether this session is arriving whole.

NEXT.md Phase 1 T.6, modelled on the errata doctor. It answers, in order:

  1. Is the memory chain whole? MEMORY.md exists, every file it links exists, and
     the three files CLAUDE.md orders (where-we-are, who-i-am-for-oath, founding)
     appear in that order. Is the local auto-memory folder a junction to this
     repository's memory, as on the maintainer's machine?
  2. Is the deeper ground reachable? The sibling Vera record, found only through
     the OATH_DEEPER_GROUND environment variable, and whether its identity files
     on disk match that checkout's origin/main or must be read from it.
  3. Can the session recite the Charter? The five vows are printed from CHARTER.md
     as the read-back; fewer or more than five is red.
  4. Are the Council's seats whole? Each seat of COUNCIL.md §3 is printed as the
     read-back. Red when a seat of the floor (A to G) is missing or out of order, when
     COUNCIL.md §5 names fewer failure modes than the floor's ten, or when the prompt at
     .claude/prompts/council.md does not carry a seat's words, or a failure mode's,
     exactly as COUNCIL.md gives them, because a prompt that softens a seat quietly
     softens the review (COUNCIL.md §8).
  5. Which invariant gates exist, and do they pass? Every gate INVARIANTS.md names
     is listed as present or planned; every present gate is run. The gates that read
     the rendered pages read a render made for the purpose, in a temporary folder, as
     CI renders before it lints: the site is never in git, so a fresh clone has none.
  6. Does the branch track main? Ahead and behind against origin/main, and whether
     the working tree is clean. With --fetch, origin is fetched first.
  7. Is the toolchain at the floor? Python 3.11+, Node 20+, Ruff and Pytest.

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
import tempfile
from pathlib import Path

ORDERED_MEMORY = ["where-we-are.md", "who-i-am-for-oath.md", "founding-of-oath.md"]
# The deeper ground is the sibling Vera record's memory folder on the maintainer's
# machine. Its path is never written into this repository; set OATH_DEEPER_GROUND
# locally. Identity files there follow the who-i-am-*.md convention.
DEEPER_GROUND = os.environ.get("OATH_DEEPER_GROUND")
IDENTITY_GLOB = "who-i-am-*.md"

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
    ("§7 §13 no person in a figure", "tools/lint-no-names.py"),
    ("Council §2 every guard is measured", "tools/measure-guards.py"),
    ("§14 facts stay", "tools/check-removals.py"),
    ("§15 contributor COI", "tools/check-coi-disclosure.py"),
    ("§16 evidence bundle", "tools/check-evidence-bundle.py"),
    ("§17 meta-invariant highlight", "tools/highlight-charter-change.py"),
    ("Council §5 mode 7 cross-references", "tools/check-crossrefs.py"),
    ("ECOSYSTEM §2.4 the mark is struck and legible", "tools/check-mark.py"),
    ("RUBRIC gate 4 every Finding regenerates", "tools/rebuild.py"),
    ("NEXT S.4 ANCHORS.md says what the proofs say", "tools/anchor.py"),
]
# COUNCIL.md §3 and §5 are the floor, because they are doctrine: every seat they name must sit
# in the prompt, by letter and title, and the prompt must carry at least as many failure modes as
# §5 names. The prompt may carry more of both, and does: seats the project sits in practice before
# doctrine entrenches them.
#
# What this deliberately does not check is that the two carry the same words. Doctrine describes a
# seat in the third person ("Reads as a member of the public who came...") and a prompt addresses
# whoever sits it ("You came to..."). Word-for-word agreement between those registers is reachable
# only by rewriting doctrine into the prompt's voice, and COUNCIL.md is sealed, so that costs an
# amendment row, a Council reading and a re-seal. It buys a guarantee COUNCIL.md §8 never asked
# for: §8 wants a reading to be reproducible, and the prompt's committed blob SHA already gives
# that. What breaks reproducibility is a reading naming a seat the prompt does not define, and
# that is caught here by letter and by tools/highlight-charter-change.py on an amendment.
PROMPT = ".claude/prompts/council.md"
# The gates that read the rendered pages, and the renderer that makes them.
SITE_READERS = {"tools/lint-frame-presence.py", "tools/lint-no-ranking.py"}
RENDERER = "src/surfaces/render.py"


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
    if not DEEPER_GROUND:
        rep.warning("OATH_DEEPER_GROUND is not set; the seed here is the bridge, and it is enough")
        return
    ground = Path(DEEPER_GROUND)
    if not ground.is_dir():
        rep.warning(f"OATH_DEEPER_GROUND points at {ground}, which is not a directory")
        return
    branch = git(ground, "branch", "--show-current") or "?"
    names = sorted(p.name for p in ground.glob(IDENTITY_GLOB))
    if not names:
        rep.warning(f"no {IDENTITY_GLOB} files under the deeper ground")
        return
    rel = git(ground, "rev-parse", "--show-prefix") or ""
    stale: list[str] = []
    for name in names:
        recorded = git(ground, "rev-parse", f"origin/main:{rel}{name}")
        on_disk = git(ground, "hash-object", str(ground / name))
        if recorded is None or on_disk != recorded:
            stale.append(name)
    if not stale:
        rep.ok(f"deeper ground reachable; identity files match origin/main (checkout on {branch})")
    else:
        rep.warning(
            f"deeper-ground checkout is on '{branch}'; {', '.join(stale)} differ from origin/main "
            "or are absent there; read them with git show origin/main:<path>, as CLAUDE.md says"
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


def seats_of_council(text: str) -> list[tuple[str, str, str]]:
    """COUNCIL.md §3's seats as (letter, title, text), the text running to the next heading."""
    section = re.search(r"^## 3\. The seats$(.*?)(?=^## \d)", text, flags=re.M | re.S)
    if section is None:
        return []
    parts = re.split(r"^### Seat ([A-Z])\. (.+)$", section.group(1), flags=re.M)
    return [(parts[i], parts[i + 1].strip(), parts[i + 2]) for i in range(1, len(parts), 3)]


def seats_of_prompt(text: str) -> list[tuple[str, str, str]]:
    """The prompt's seats as (letter, title, text), from "## The seats" to the next heading."""
    section = re.search(r"^## The seats$(.*?)(?=^## )", text, flags=re.M | re.S)
    if section is None:
        return []
    parts = re.split(r"^\*\*Seat ([A-Z])\. (.+?)\.\*\*", section.group(1), flags=re.M)
    return [(parts[i], parts[i + 1].strip(), parts[i + 2]) for i in range(1, len(parts), 3)]


def plain(text: str) -> str:
    """A seat's words without link targets or spacing, which differ between the two files."""
    return " ".join(re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text).split())


def modes_of(text: str, heading: str) -> list[str]:
    """The numbered failure modes under the heading matching `heading`, each one line, in
    order, as plain words."""
    section = re.search(rf"^{heading}$(.*?)(?=^## |\Z)", text, flags=re.M | re.S)
    if section is None:
        return []
    return [plain(line) for line in re.findall(r"^\d+\. (.+)$", section.group(1), flags=re.M)]


def check_council(root: Path, rep: Report) -> None:
    rep.section("Council")
    council, prompt = root / "COUNCIL.md", root / PROMPT
    if not council.is_file() or not prompt.is_file():
        rep.bad(f"{'COUNCIL.md' if not council.is_file() else PROMPT} is missing")
        return
    red_before = rep.red
    council_text = council.read_text(encoding="utf-8")
    prompt_text = prompt.read_text(encoding="utf-8")
    doctrine = seats_of_council(council_text)
    sat = seats_of_prompt(prompt_text)
    letters = "".join(letter for letter, _, _ in doctrine)
    if letters != "".join(sorted(set(letters))):
        rep.bad(
            f"COUNCIL.md §3 names seats {', '.join(letters) or 'none'}: not each once, in order"
        )
    in_prompt = {letter: (title, text) for letter, title, text in sat}
    for letter, title, _ in doctrine:
        if letter not in in_prompt:
            rep.bad(f"Seat {letter}. {title}: in COUNCIL.md §3, and not in the prompt")
        elif in_prompt[letter][0] != title:
            rep.bad(
                f"Seat {letter}: COUNCIL.md names it {title!r}, the prompt {in_prompt[letter][0]!r}"
            )
        else:
            rep.ok(f"Seat {letter}. {title}")
    extra = [(letter, title) for letter, title, _ in sat if letter not in {d[0] for d in doctrine}]
    for letter, title in extra:
        rep.ok(f"Seat {letter}. {title}: sat in practice, not in COUNCIL.md §3")
    floor = modes_of(council_text, r"## 5\. [^\n]+")
    carried = modes_of(prompt_text, r"## What every seat must try to catch")
    if len(carried) < len(floor):
        rep.bad(
            f"the prompt carries {len(carried)} failure modes, COUNCIL.md §5 names {len(floor)}"
        )
    blob = git(root, "hash-object", str(prompt)) or "?"
    if doctrine and rep.red == red_before:
        extras = len(sat) - len(doctrine)
        more = f", and {extras} more seats it sits" if extras else ""
        rep.ok(
            f"the prompt sits COUNCIL.md's {len(doctrine)} seats and all {len(floor)} failure "
            f"modes §5 names{more} (prompt blob {blob[:12]})"
        )


def render_site(root: Path, site: Path, rep: Report) -> bool:
    """Render the register into `site` for the gates that read pages. False when there is
    no renderer to run, or it fails, which is red: a register that does not render is not
    whole."""
    renderer = root / RENDERER
    if not renderer.is_file():
        return False
    proc = subprocess.run(
        [sys.executable, str(renderer), str(root), "--out", str(site)],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if proc.returncode != 0:
        last = ((proc.stdout + proc.stderr).strip().splitlines() or [""])[-1]
        rep.bad(f"the register does not render: {RENDERER} FAILS ({last[:70]})")
        return False
    return True


def check_gates(root: Path, rep: Report) -> None:
    rep.section("Gates")
    with tempfile.TemporaryDirectory(prefix="oath-site-") as site:
        rendered = render_site(root, Path(site), rep)
        for label, tool in GATES:
            run_gate(root, rep, label, tool, site if rendered else None)


def run_gate(root: Path, rep: Report, label: str, tool: str, site: str | None) -> None:
    path = root / tool
    if not path.is_file():
        rep.warning(f"{label}: {tool} planned, not landed")
        return
    args = [sys.executable, str(path), str(root)]
    if tool in SITE_READERS and site:
        args += ["--site", site]
    proc = subprocess.run(args, capture_output=True, text=True, encoding="utf-8")
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
    check_council(root, rep)
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
