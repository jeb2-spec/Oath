"""Every test runs in the same environment, whoever is running it.

Four tools in this repository read a variable from the environment, and each one changes what the
tool measures: `OATH_PUBLISHED_REF` is the published record the comparing gates read (Invariants
11, 12, 14 and 17), `OATH_PAGES_COMMIT` is the commit the rendered pages name as their build,
`OATH_DEEPER_GROUND` is the deeper record the session-start doctor reads and is set on the
maintainer's machine, and `GITHUB_ACTIONS` turns a notice into the runner's own highlight. A test
that leaves one of them to the ambient environment measures a different thing on the maintainer's
machine, in a cloud session, and on a runner, and the three disagree without saying so.

That happened. CI sets `OATH_PUBLISHED_REF` on a push to main, to main as it stood before the
push, because by then main is the pushed commit and a gate comparing it with itself would prove
nothing. The pytest step inherits the variable; `tools/test_highlight_charter_change.py` builds a
repository in a temporary directory that has never heard of that commit; the gate refuses to read
it, which is exactly what the gate is for. So the assertion that the gate passes on a well-formed
tree failed on every push to main and passed everywhere else, and `verify` was red on main at
3d4c1b9 and at 9663388 while the identical commit was green on the branch push and on the pull
request. Two merges carried it.

So these are cleared before every test, and a test that wants one sets it itself with
`monkeypatch.setenv`, as `tools/test_check_removals.py`, `tools/test_signal_gates.py` and
`tools/test_correct.py` already do. Autouse fixtures of a scope are instantiated before the
fixtures a test asks for by name, so a fixture that sets one of these still wins.

This clears nothing else, and the list is checked against the code rather than trusted:
`tools/test_conftest.py` reads every variable the tools actually reach for and fails if this list
and that set have drifted apart in either direction. A test that depends on anything else about
the machine it runs on is a test to rewrite, not a variable to add here.
"""

from __future__ import annotations

import pytest

# Every variable a tool under test reads from the environment. Each one changes what that tool
# measures, so none of them is left to the machine the tests happen to run on.
AMBIENT = (
    "GITHUB_ACTIONS",
    "OATH_DEEPER_GROUND",
    "OATH_PAGES_COMMIT",
    "OATH_PUBLISHED_REF",
)

# A variable a tool reads that a test must not clear, and why. Nothing is here yet, and the entry
# exists so that the next variable a tool reaches for is a decision and not an omission: clearing
# HOME or PATH would break the machine rather than isolate it, and tools/test_conftest.py refuses a
# variable that is in neither list.
LEFT_ALONE: tuple[str, ...] = ()


@pytest.fixture(autouse=True)
def one_environment(monkeypatch):
    """Clear the ambient environment, so a test's answer is the code's answer, not the machine's."""
    for name in AMBIENT:
        monkeypatch.delenv(name, raising=False)
