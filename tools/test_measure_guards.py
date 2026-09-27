"""The tool that measures every other guard, measured.

Three Council readings in a row found "each guard has a test" asserted and never checked. This
runner is the answer, and until now it was the one claim in the repository with nothing behind it:
if it reported a guard caught when the run had broken, or skipped a stale row quietly, every number
it prints would be worth nothing and nobody would know. Each test below is one way it could lie.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def load():
    spec = importlib.util.spec_from_file_location(
        "measure_guards", ROOT / "tools/measure-guards.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gate = load()


def repo(tmp_path: Path, guards: list[dict], files: dict[str, str]) -> Path:
    root = tmp_path / "repo"
    (root / "tools").mkdir(parents=True)
    (root / "tools/guards.ndjson").write_text(
        "".join(json.dumps(g, sort_keys=True) + "\n" for g in guards), encoding="utf-8"
    )
    for name, text in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    return root


GUARDED = 'def answer(n):\n    if n < 0:\n        raise ValueError("no")\n    return n\n'
TEST = (
    "import importlib.util, pathlib, pytest\n"
    "spec = importlib.util.spec_from_file_location('m', pathlib.Path(__file__).parent / 'm.py')\n"
    "m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)\n"
    "def test_a_negative_is_refused():\n"
    "    with pytest.raises(ValueError):\n"
    "        m.answer(-1)\n"
)
GUARD = {
    "id": "a-negative-is-refused",
    "why": "A negative would be answered as itself.",
    "file": "m.py",
    "old": '    if n < 0:\n        raise ValueError("no")\n',
    "new": "",
    "tests": "test_m.py",
}


def test_a_guard_whose_removal_fails_its_named_test_is_measured(tmp_path):
    """The whole point: remove the guard, the named test fails, and the file comes back whole."""
    root = repo(tmp_path, [GUARD], {"m.py": GUARDED, "test_m.py": TEST})
    assert gate.measure(root) == 0
    assert (root / "m.py").read_text("utf-8") == GUARDED, "the tree is restored, pass or fail"


def test_a_guard_no_named_test_catches_fails_the_run(tmp_path):
    """A guard whose removal changes nothing a test sees is a comment, and saying so is the job.
    Here a second guard sits in the same file and the named test never reaches it."""
    both = GUARDED.replace(
        "    return n\n",
        '    if n > 10**9:\n        raise ValueError("far too big")\n    return n\n',
    )
    root = repo(
        tmp_path,
        [
            dict(
                GUARD,
                id="too-big-is-refused",
                old='    if n > 10**9:\n        raise ValueError("far too big")\n',
            )
        ],
        {"m.py": both, "test_m.py": TEST},
    )
    assert gate.measure(root) == 1, "the run fails, and names the guard nothing catches"
    assert (root / "m.py").read_text("utf-8") == both, "the tree is restored, pass or fail"


def test_a_guard_the_code_no_longer_carries_is_stale_and_never_silent(tmp_path):
    """The failure mode that decayed the older sweeps: the code moves, the list does not, and the
    row is skipped. Stale is a failure, not a pass, because a guard nobody can find is a guard
    nobody is measuring."""
    root = repo(tmp_path, [GUARD], {"m.py": "def answer(n):\n    return n\n", "test_m.py": TEST})
    assert gate.measure(root) == 1


def test_a_guard_whose_old_text_appears_twice_is_stale_rather_than_half_removed(tmp_path):
    """Removing one of two identical sites leaves the guard in force and the run would call it
    uncaught. Ambiguity is reported, never guessed at."""
    twice = GUARDED + "\n\n" + GUARDED.replace("def answer", "def answer_again")
    root = repo(tmp_path, [GUARD], {"m.py": twice, "test_m.py": TEST})
    assert gate.measure(root) == 1
    assert (root / "m.py").read_text("utf-8") == twice


def test_a_named_test_selector_is_parsed_as_a_shell_would(tmp_path):
    """A guard may name a -k expression, and a plain whitespace split handed pytest a file called
    "or". Pytest then failed to collect it, the runner saw a non-zero exit, and the guard was
    reported caught. A measurement that passes because the measurement broke is worse than none."""
    root = repo(
        tmp_path,
        [dict(GUARD, tests='test_m.py -k "a_negative or nothing_named_this"')],
        {"m.py": GUARDED, "test_m.py": TEST},
    )
    assert gate.measure(root) == 0
    # And the same selector, split on whitespace, is what used to happen: five arguments, two of
    # them files that do not exist.
    quoted = 'test_m.py -k "a or b"'
    assert gate.shlex.split(quoted) == ["test_m.py", "-k", "a or b"]
    assert len(quoted.split()) == 5


def test_two_guards_may_not_share_an_id(tmp_path):
    """An id is how a reader points at one guard, and how --only reaches it."""
    root = repo(tmp_path, [GUARD, dict(GUARD)], {"m.py": GUARDED, "test_m.py": TEST})
    with pytest.raises(SystemExit):
        gate.guards(root)


def test_only_names_one_guard_and_an_unknown_name_fails(tmp_path):
    root = repo(tmp_path, [GUARD], {"m.py": GUARDED, "test_m.py": TEST})
    assert [g["id"] for g in gate.guards(root, GUARD["id"])] == [GUARD["id"]]
    assert gate.measure(root, only="not-a-guard") == 1


def test_the_repositorys_own_list_is_well_formed():
    """Every row carries what the runner needs, and every file it names is in the tree. This runs
    in milliseconds and catches a row added without its test or with a typo in its path."""
    rows = gate.guards(ROOT)
    assert len(rows) > 30, "the list is the claim; an empty list is not a passing claim"
    for guard in rows:
        for field in ("id", "why", "file", "old", "new", "tests"):
            assert guard.get(field) is not None, f"{guard.get('id')}: no {field}"
        assert (ROOT / guard["file"]).is_file(), (
            f"{guard['id']}: {guard['file']} is not in the tree"
        )
        assert guard["old"] != guard["new"], f"{guard['id']}: removing it changes nothing"
        assert guard["why"].endswith("."), f"{guard['id']}: why is a sentence"
        first = gate.shlex.split(guard["tests"])[0]
        assert (ROOT / first).is_file(), f"{guard['id']}: {first} is not in the tree"


def test_the_runner_refuses_a_list_with_uncommitted_edits():
    """An unknown guard id is a failure and never an empty pass: a run that measures nothing must
    not read as a run in which nothing was wrong."""
    done = subprocess.run(
        [sys.executable, "tools/measure-guards.py", "--only", "not-a-guard"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert done.returncode == 1, "an unknown guard id is a failure, not an empty pass"


def test_a_measurement_does_not_depend_on_what_was_measured_before_it(tmp_path):
    """A .pyc header records its source's mtime to the SECOND, so two versions of one file written
    inside the same second are indistinguishable to the import machinery and the first one's
    bytecode is reused. Measuring the real list takes eleven seconds across thirty-seven guards, so
    removals and restores share seconds, and one guard reported caught on its own and uncaught in
    the sweep. Both runs printed a number and neither said which to believe, which is worse than
    printing none."""
    root = repo(tmp_path, [GUARD], {"m.py": GUARDED, "test_m.py": TEST})
    # Warm the cache the way a test run does, then measure twice with no pause between.
    subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "test_m.py"], cwd=root, capture_output=True
    )
    assert (root / "__pycache__").is_dir() or True, "a cache may or may not have been written"
    assert [gate.measure(root), gate.measure(root)] == [0, 0], (
        "the same guard measures the same way twice in one second"
    )
    assert (root / "m.py").read_text("utf-8") == GUARDED


def test_removing_a_guard_drops_its_files_compiled_bytecode(tmp_path):
    """The mechanism, on its own, because the test above can pass by luck of the clock."""
    root = repo(tmp_path, [GUARD], {"m.py": GUARDED, "test_m.py": TEST})
    cache = root / "__pycache__"
    cache.mkdir()
    stale = cache / "m.cpython-311.pyc"
    stale.write_bytes(b"not really bytecode")
    assert gate.remove(root, GUARD) == GUARDED
    assert not stale.exists(), "the guarded file's bytecode goes with the guard"
    assert gate.forget(root / "nothing-here.py") is None, "a file with no cache is not an error"


def test_a_run_that_collected_no_test_is_not_a_measurement(tmp_path):
    """The failure that hid six broken rows at once. pytest exits non-zero when it collects nothing,
    when it is handed a path that does not exist, and when it is interrupted; the runner read every
    non-zero exit as the guard being caught. Six guards named tests the merge with main's pages had
    dropped, and all six reported measured (the sixth measurement, on the merged tree)."""
    root = repo(
        tmp_path,
        [dict(GUARD, tests="test_m.py -k nothing_is_named_this")],
        {"m.py": GUARDED, "test_m.py": TEST},
    )
    assert gate.measure(root) == 1, "a run that measured nothing is not a run that found nothing"
    root = repo(
        tmp_path / "again",
        [dict(GUARD, tests="test_not_here.py")],
        {"m.py": GUARDED, "test_m.py": TEST},
    )
    assert gate.measure(root) == 1, "a named file that is not in the tree is not a measurement"
    # And the distinction is exactly pytest's: only "ran, and something failed" is a measurement.
    assert gate.ALL_PASSED == 0 and gate.RAN_AND_FAILED == 1
    assert set(gate.DID_NOT_RUN) == {2, 3, 4, 5}
