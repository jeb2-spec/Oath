"""The environment every test runs in, measured. conftest.py.

`conftest.py` clears the variables the tools read so that a test's answer is the code's answer.
This file is the evidence that it does, and that its list cannot quietly fall behind the code.

Only the `tools` tree carries a test whose answer these variables change today, so the first test
below is the measured one and it runs against that tree. Under `src` the isolation is protection
for the next test rather than a guard with a failing input: `src/surfaces/render.py` reads
`OATH_PAGES_COMMIT`, and no test there asserts the build link it sets, so nothing under `src`
would notice today if the fixture stopped reaching it. That is stated rather than covered by an
assertion that would pass whether or not the isolation held.
"""

from __future__ import annotations

import importlib.util
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# A commit no repository built in a temporary directory has ever heard of. CI's own value is a real
# commit SHA, main as it stood before the push, and unreadable in such a repository for the same
# reason.
ABSENT = "refs/remotes/origin/a-ref-no-repository-has"

# `os.environ.get("NAME")` and `os.getenv("NAME")`, the two ways a tool here reads the environment.
# A write (`dict(os.environ, NAME="1")`, as tools/measure-guards.py does) is not a read and is not
# matched.
READS = re.compile(
    r"""environ\.get\(\s*["']([A-Z][A-Z0-9_]*)["']|getenv\(\s*["']([A-Z][A-Z0-9_]*)["']"""
)


def conftest():
    spec = importlib.util.spec_from_file_location("oath_conftest", ROOT / "conftest.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sources() -> list[Path]:
    """Every tool, adapter, surface and script: the code a test runs, and not the tests."""
    found = []
    for pattern in ("tools/*.py", "src/**/*.py", "scripts/*.py"):
        found += [p for p in ROOT.glob(pattern) if not p.name.startswith("test_")]
    return sorted(found)


def test_a_gate_test_keeps_its_answer_when_ci_sets_a_published_ref():
    """The failure this file exists for. CI sets OATH_PUBLISHED_REF on a push to main, the pytest
    step inherits it, and the gate is asked to compare a repository built in a temporary directory
    against a commit that repository has never heard of. The gate refuses, which is what it is for,
    and the assertion that a well-formed tree passes failed on main and nowhere else.

    Run with the variable set, as a runner would: the isolation makes it pass. Take the isolation
    away and this goes red, which is the guard's measured failing input in tools/guards.ndjson.

    The run below also selects this file's own clearing test, because with nothing set in the
    parent that test asserts something already true. Driven from here, with the variables set, it
    measures. The `-k` names both and nothing else, so this test does not select itself."""
    done = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "-p",
            "no:cacheprovider",
            "tools/test_highlight_charter_change.py",
            "tools/test_conftest.py",
            "-k",
            "cannot_read_the_published_core or variables_are_cleared",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        env=dict(os.environ, OATH_PUBLISHED_REF=ABSENT, GITHUB_ACTIONS="true"),
    )
    assert done.returncode == 0, done.stdout + done.stderr
    assert "2 passed" in done.stdout, done.stdout


def test_every_variable_the_code_reads_is_cleared_or_deliberately_left_alone():
    """A tool that starts reading a new variable is a new way for a test to measure the machine
    instead of the code. So the list is checked against the code, in both directions: a variable
    the code reads and neither list names is an omission, and a name in a list that no code reads
    any more is a list that has drifted."""
    module = conftest()
    named = set(module.AMBIENT) | set(module.LEFT_ALONE)
    read: dict[str, list[str]] = {}
    for path in sources():
        for first, second in READS.findall(path.read_text("utf-8")):
            read.setdefault(first or second, []).append(str(path.relative_to(ROOT)))

    unnamed = sorted(set(read) - named)
    assert not unnamed, (
        "these variables are read by the code and named in neither conftest.AMBIENT nor "
        "conftest.LEFT_ALONE, so a test inherits them from the machine: "
        + "; ".join(f"{name} ({', '.join(read[name])})" for name in unnamed)
    )
    stale = sorted(named - set(read))
    assert not stale, (
        "these names are in conftest.py and no code reads them any more, so the list has drifted "
        "from what it protects: " + ", ".join(stale)
    )


def test_the_variables_are_cleared_and_a_test_that_sets_one_still_wins(monkeypatch):
    """Two halves of the same contract. The fixture is autouse, so by the time a test body runs the
    environment is clear; and it is a fixture rather than a change to the tools, so a test that
    wants a variable sets it and is obeyed. Three test files depend on the second half, including
    two that set it from inside a fixture of their own.

    The first half only measures anything where something set the variables, so it is run that way
    on purpose: the subprocess in this file's first test sets them, and so does CI on a push to
    main. On a clean machine, run by itself, the first half asserts what is already true."""
    module = conftest()
    for name in module.AMBIENT:
        assert name not in os.environ, f"{name} reached a test body"
    monkeypatch.setenv("OATH_PUBLISHED_REF", ABSENT)
    assert os.environ["OATH_PUBLISHED_REF"] == ABSENT
