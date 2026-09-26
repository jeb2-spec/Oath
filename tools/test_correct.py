"""The correction a person makes, proven end to end. INVARIANTS.md §14; BYLAWS.md §5, §6.

A correction is a row a reader can see, citing a primary source whose bytes the register
keeps; the fact moves, what it was stays in the row, and the §14 gate lets exactly that move
through. Found necessary by the Council's reading of S.1b: once the gate refused every fact
moved in place, nothing a person could do would correct a filing's date or attribution.
"""

from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


correct = load("correct", ROOT / "tools" / "correct.py")
gate = load("check_removals", ROOT / "tools" / "check-removals.py")
schemas = load("validate_schemas", ROOT / "tools" / "validate-schemas.py")

ROW = {
    "id": "fl:house-clerk:P:1",
    "officeholder_id": "oh:us:house:x000001",
    "filed_at": "2025-02-25",
    "source": {"url": "u", "retrieved_at": "2026-01-01T00:00:00Z", "content_hash": None},
}
URL = "https://disclosures-clerk.house.gov/public_disc/financial-pdfs/2025FD.zip"
EVIDENCE = b"the index, as the Clerk now serves it"


@pytest.fixture
def register(tmp_path, monkeypatch):
    """A throwaway repository whose branch `published` holds one filing."""
    (tmp_path / "data").mkdir()
    (tmp_path / "tools").mkdir()
    shutil.copy(ROOT / "SOURCES.md", tmp_path / "SOURCES.md")
    shutil.copy(ROOT / "tools" / "check-aggregator-sole.py", tmp_path / "tools")
    (tmp_path / "data" / "filings.ndjson").write_text(correct.canonical(ROW), encoding="utf-8")
    for args in (
        ["init", "-q", "-b", "published"],
        ["add", "-A"],
        ["-c", "user.email=t@example.com", "-c", "user.name=t", "commit", "-q", "-m", "p"],
    ):
        subprocess.run(["git", "-C", str(tmp_path), *args], check=True, capture_output=True)
    (tmp_path / "evidence.zip").write_bytes(EVIDENCE)
    monkeypatch.setenv("OATH_PUBLISHED_REF", "published")
    return tmp_path


def run(root: Path, *extra: str) -> int:
    return correct.main(
        [
            str(root),
            "--row",
            "fl:house-clerk:P:1",
            "--field",
            "filed_at",
            "--kind",
            "source",
            "--because",
            "The Clerk's index read 2026-10-05 dates the report 2025-02-26.",
            "--evidence-url",
            URL,
            "--evidence-file",
            str(root / "evidence.zip"),
            "--decided-by",
            "the maintainer",
            "--decided-at",
            "2026-10-06T12:00:00Z",
            *extra,
        ]
    )


def changes(root: Path) -> list[dict]:
    path = root / "data" / "changes.ndjson"
    return [json.loads(line) for line in path.read_text("utf-8").splitlines()]


def test_a_correction_moves_the_fact_keeps_what_it_was_and_passes_the_gate(register):
    assert gate.main([str(register)]) == 0
    assert run(register, "--now", "2025-02-26") == 0
    row = json.loads((register / "data" / "filings.ndjson").read_text("utf-8"))
    assert row == dict(ROW, filed_at="2025-02-26")
    (change,) = changes(register)
    assert (change["change"], change["field"], change["was"], change["now"], change["kind"]) == (
        "corrected",
        "filed_at",
        "2025-02-25",
        "2025-02-26",
        "source",
    )
    kept = register / "data" / "captures" / "sha256" / f"{change['capture']['content_hash']}.zip"
    assert kept.read_bytes() == EVIDENCE, "the evidence's bytes are kept, named by their hash"
    assert gate.main([str(register)]) == 0, "the gate lets exactly this move through"
    loaded = schemas.load_schemas(ROOT)
    assert (
        schemas.validate(change, loaded["change.schema.json"], loaded, "change.schema.json") == []
    )


def test_the_same_move_without_its_row_is_refused_by_the_gate(register):
    moved = dict(ROW, filed_at="2025-02-26")
    (register / "data" / "filings.ndjson").write_text(correct.canonical(moved), encoding="utf-8")
    assert gate.main([str(register)]) == 1


def test_a_value_that_stands_is_recorded_and_nothing_moves(register):
    before = (register / "data" / "filings.ndjson").read_bytes()
    assert run(register, "--stands") == 0
    assert (register / "data" / "filings.ndjson").read_bytes() == before
    (change,) = changes(register)
    assert change["was"] == change["now"] == "2025-02-25"
    assert gate.main([str(register)]) == 0


@pytest.mark.parametrize(
    "extra, says",
    [
        (["--now", "2025-02-25"], "nothing to move"),
        (["--stands", "--now", "2025-02-26"], "give no --now"),
        ([], "give --now"),
        (["--now", "x", "--field", "no_such_fact"], "carries no no_such_fact"),
    ],
)
def test_a_correction_that_says_nothing_or_too_much_is_refused(register, capsys, extra, says):
    assert run(register, *extra) == 1
    assert says in capsys.readouterr().out
    assert not (register / "data" / "changes.ndjson").exists()


def test_the_evidence_must_be_a_primary_source_and_kept(register, capsys):
    args = [str(register), "--row", "fl:house-clerk:P:1", "--field", "filed_at"]
    tail = ["--kind", "source", "--because", "why", "--decided-by", "the maintainer"]
    for url, evidence in (
        ("https://www.opensecrets.org/x", register / "evidence.zip"),
        ("http://disclosures-clerk.house.gov/x", register / "evidence.zip"),
        (URL, register / "missing.zip"),
    ):
        code = correct.main(
            [*args, "--now", "2025-02-26", "--evidence-url", url, "--evidence-file", str(evidence)]
            + tail
        )
        assert code == 1
    out = capsys.readouterr().out
    assert "primary source" in out and "keeps the bytes" in out
    assert not (register / "data" / "changes.ndjson").exists()


def test_a_row_the_register_does_not_hold_is_refused(register, capsys):
    code = correct.main(
        [
            str(register),
            "--row",
            "fl:house-clerk:P:2",
            "--field",
            "filed_at",
            "--now",
            "x",
            "--kind",
            "register",
            "--because",
            "why",
            "--evidence-url",
            URL,
            "--evidence-file",
            str(register / "evidence.zip"),
            "--decided-by",
            "the maintainer",
        ]
    )
    assert code == 1 and "not in data/filings.ndjson" in capsys.readouterr().out
