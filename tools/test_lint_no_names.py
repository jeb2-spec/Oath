"""The §7/§13 gate over the sealed state and the run records: no figure names a person.

Every input here is the register's own published build with one thing changed, so the gate is
measured against the shape the defect actually took and not against a fixture invented for it
(the Council's fifth reading of S.1b, Seats A, C, D, E and F).
"""

from __future__ import annotations

import importlib.util
import json
import shutil
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def load():
    spec = importlib.util.spec_from_file_location("lint_no_names", HERE / "lint-no-names.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def register(tmp_path):
    """The published build, without the caches and the kept captures."""
    shutil.copytree(
        ROOT / "data",
        tmp_path / "data",
        ignore=shutil.ignore_patterns("cache", "anchors", "captures"),
    )
    return tmp_path


def state_of(root: Path) -> str:
    return json.loads((root / "data" / "meta.json").read_text("utf-8"))["state"]


def reseal(root: Path, state: str) -> None:
    meta = json.loads((root / "data" / "meta.json").read_text("utf-8"))
    meta["state"] = state
    (root / "data" / "meta.json").write_text(json.dumps(meta), encoding="utf-8")


def test_the_published_build_names_nobody(register):
    assert load().problems(register) == []


def test_a_sealed_sentence_that_names_an_officeholder_fails(register):
    """The defect itself: one line of the adapter put the roster name and seat of every sitting
    member whose surname a set-aside row shares into the one sentence the register seals about
    itself, ordered by how many rows each had. The clause below is that sentence's own shape."""
    who = json.loads((register / "data" / "officeholders.ndjson").read_text("utf-8").split("\n")[0])
    reseal(
        register,
        state_of(register) + f" 14 because surname matches a sitting member ({who['common_name']}, "
        f"{who['offices'][0]['seat']}) but the given names differ; a human decides this one.",
    )
    found = load().problems(register)
    assert any(who["common_name"] in line for line in found), found
    assert any("a seat" in line for line in found), found


def test_a_sealed_sentence_that_places_a_row_fails(register):
    """A DocID or an officeholder's id stands in for a name. Both fail; a filing year, a
    comma-grouped figure and a fingerprint are facts about the build, and pass."""
    lint = load()
    sealed = state_of(register)
    for placed in ("DocID 20030699", "the row oh:us:house:a000055"):
        reseal(register, sealed + f" Set aside: {placed}.")
        assert lint.problems(register), placed
    reseal(register, sealed + " Read from the 2025 index, 7,346 transactions.")
    assert lint.problems(register) == []


def test_a_run_records_group_key_that_names_an_officeholder_fails(register):
    """The run record is sealed too, and `README.md` sends a reader to it for what was set aside
    and why. The gate reads its group keys, not only the sentence derived from them."""
    path = next((register / "data" / "adapter-runs").glob("*.ndjson"))
    lines = path.read_text("utf-8").splitlines()
    run = json.loads(lines[0])
    who = json.loads((register / "data" / "officeholders.ndjson").read_text("utf-8").split("\n")[0])
    seat = who["offices"][0]["seat"]
    run["rejected_by_reason"][
        f"surname matches a sitting member ({who['common_name']}, {seat})"
    ] = 1
    path.write_text("\n".join([json.dumps(run), *lines[1:]]) + "\n", encoding="utf-8")
    assert load().problems(register)


def test_the_sources_a_run_record_read_are_not_about_a_person(register):
    """A run record names the Clerk's own files and the captures the build was made from. Those
    are facts about bytes, and the gate does not read them as names."""
    path = next((register / "data" / "adapter-runs").glob("*.ndjson"))
    run = json.loads(path.read_text("utf-8").splitlines()[0])
    assert run.get("sources"), "the fixture's run record must carry its sources"
    assert load().problems(register) == []


def test_a_build_with_no_sealed_state_or_no_run_record_fails(register, tmp_path):
    lint = load()
    (register / "data" / "meta.json").unlink()
    assert lint.problems(register), "a gate that reads nothing proves nothing"
    empty = tmp_path / "bare"
    (empty / "data").mkdir(parents=True)
    (empty / "data" / "meta.json").write_text('{"state": ""}', encoding="utf-8")
    (empty / "data" / "officeholders.ndjson").write_text("", encoding="utf-8")
    assert lint.problems(empty), "a state sentence that says nothing is not a state"
