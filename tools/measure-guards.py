#!/usr/bin/env python3
"""Every guard in the list has a failing input, measured by removing it.

Reads `tools/guards.ndjson`, and for each guard removes it from the working tree, runs the tests
it names, restores the file, and reports whether the removal failed a test. A guard no test
catches is printed, and the tool fails.

Why this exists as a command. Three Council readings in a row found the same shape: the third
found that "each guard has a test" had never been measured; the fourth found eleven guards no
test caught, nine of them the third pass's own; the fifth found twelve more, one of them a guard
the repository had measured before and silently stopped measuring when another rule started
catching its input first. Each time the answer was a sweep run by hand and a number written into
a commit message, and each time the number decayed, because a claim nobody can re-run is a claim
about the past. The list and this runner are the claim in a form a reader can check, and the next
pass can re-run. When a guard is added, its row goes in the list in the same commit.

A guard names the tests that should catch it, so a run is seconds rather than the whole suite.
Naming them is part of the record: it says which test measures which guard, which the older
sweeps never wrote down. `--all` runs the whole suite for each guard instead, which is slower and
is how a guard whose named tests are wrong gets found.

    python tools/measure-guards.py
    python tools/measure-guards.py --only reason-group-names-nobody
    python tools/measure-guards.py --all
"""

from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
import sys
import time
from pathlib import Path

LIST = "tools/guards.ndjson"


def guards(root: Path, only: str = "") -> list[dict]:
    path = root / LIST
    rows = [
        json.loads(line)
        for line in path.read_text("utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("//")
    ]
    ids = [g["id"] for g in rows]
    if len(set(ids)) != len(ids):
        raise SystemExit(f"{LIST}: two guards share an id")
    return [g for g in rows if not only or g["id"] == only]


def forget(path: Path) -> None:
    """Drop any compiled bytecode for one source file.

    A .pyc header records the source's mtime to the SECOND, so two versions of the same file
    written inside one second are indistinguishable to the import machinery and the first one's
    bytecode is reused for the second. Measuring 37 guards takes eleven seconds, so several
    removals land in the same second as the restore before them, and the tests then ran against
    code that was no longer on disk. That made a measurement depend on the order of the run: one
    guard reported caught alone and uncaught in the sweep, which is the worst kind of failure here,
    because both runs printed a number and neither said which to believe.
    """
    cache = path.parent / "__pycache__"
    for stale in cache.glob(f"{path.stem}.*.pyc") if cache.is_dir() else ():
        stale.unlink(missing_ok=True)


def remove(root: Path, guard: dict) -> str:
    """The file's contents before the guard was removed from it, or a refusal saying why it
    could not be. A guard whose `old` text is no longer in the file is stale, and stale is a
    failure: the code moved and the list did not."""
    path = root / guard["file"]
    if not path.is_file():
        return ""
    before = path.read_text("utf-8")
    if before.count(guard["old"]) != 1:
        return ""
    path.write_text(before.replace(guard["old"], guard["new"]), encoding="utf-8")
    forget(path)
    return before


# What pytest's exit code means, and which of them is a measurement. 1 is the only one: tests ran
# and one failed. 5 collected nothing, 4 is a usage error, 2 and 3 are an interrupted or broken run,
# and each of those is a run that measured nothing while exiting non-zero, which this tool used to
# read as the guard being caught. A measurement that passes because the measurement broke is worse
# than no measurement, so a run that did not run is its own outcome.
ALL_PASSED = 0
RAN_AND_FAILED = 1
DID_NOT_RUN = {2: "interrupted", 3: "an internal error", 4: "a usage error", 5: "no test collected"}


def caught(root: Path, guard: dict, whole: bool) -> tuple[bool, str]:
    """Whether the tests refuse the tree with the guard removed, and the first line that says so.
    A run that could not run returns (False, "did not run: ...") rather than a verdict."""
    args = [sys.executable, "-m", "pytest", "-x", "-q"]
    # shlex, not split: a guard whose named tests are a -k expression writes it quoted, and a
    # plain split turned `-k "a or b"` into three arguments and pytest into "file not found:
    # or", which the runner then reported as the guard being caught. A measurement that passes
    # because the measurement broke is worse than no measurement.
    args += [] if whole else shlex.split(guard["tests"])
    # And no new bytecode is written during the run, so nothing this measurement leaves behind
    # can shadow the next one.
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    done = subprocess.run(args, cwd=root, capture_output=True, text=True, encoding="utf-8", env=env)
    ran = done.returncode in (ALL_PASSED, RAN_AND_FAILED)
    if not ran:
        said = [
            line
            for line in (done.stdout + done.stderr).splitlines()
            if line.startswith("ERROR") or "not found" in line or "no tests ran" in line
        ]
        why = DID_NOT_RUN.get(done.returncode, f"pytest exited {done.returncode}")
        return False, f"did not run ({why}): {said[0] if said else guard['tests']}"
    if done.returncode == ALL_PASSED:
        return False, ""
    failed = [
        line
        for line in (done.stdout + done.stderr).splitlines()
        if line.startswith("FAILED") or line.startswith("ERROR")
    ]
    return True, (failed[0] if failed else "refused")


def measure(root: Path, only: str = "", whole: bool = False) -> int:
    rows = guards(root, only)
    if not rows:
        print(f"FAIL {LIST}: no guard to measure{f' named {only!r}' if only else ''}")
        return 1
    print(f"Measuring {len(rows)} guards by removing each one, against the tests it names.\n")
    missed, stale, started = [], [], time.monotonic()
    for guard in rows:
        before = remove(root, guard)
        if not before:
            stale.append(guard)
            print(f"STALE {guard['id']}: {guard['file']} no longer carries this guard, once")
            continue
        try:
            found, why = caught(root, guard, whole)
        finally:
            (root / guard["file"]).write_text(before, encoding="utf-8")
            forget(root / guard["file"])
        if found:
            print(f"ok    {guard['id']}: {why}")
        elif why:
            missed.append(guard)
            print(f"FAIL  {guard['id']}: {why}")
        else:
            missed.append(guard)
            print(f"FAIL  {guard['id']}: removed, and every test it names still passes")
    took = time.monotonic() - started
    print()
    for guard in missed:
        print(f"unmeasured: {guard['id']} — {guard['why']}")
    for guard in stale:
        print(f"stale: {guard['id']} — {guard['why']}")
    if missed or stale:
        print(
            f"\n{len(missed)} of {len(rows)} guards no named test catches"
            + (f", and {len(stale)} the code no longer carries" if stale else "")
            + f". A guard without a failing input is a comment. ({took:.0f}s)"
        )
        return 1
    print(
        f"OK    {len(rows)} guards removed one at a time; each fails a test it names. ({took:.0f}s)"
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", default=".", help="repository root (default: .)")
    parser.add_argument("--only", default="", help="measure one guard by its id")
    parser.add_argument(
        "--all", action="store_true", help="run the whole suite for each guard, not its named tests"
    )
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    dirty = subprocess.run(
        ["git", "-C", str(root), "status", "--porcelain", "--", LIST],
        capture_output=True,
        text=True,
    )
    if dirty.returncode == 0 and dirty.stdout.strip():
        print(f"note  {LIST} is uncommitted; measuring the working tree's list.\n")
    return measure(root, args.only, args.all)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
