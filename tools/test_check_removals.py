"""The §14 gate, proven red before green. INVARIANTS.md §14; CHARTER Vow V.

Each test makes the change the gate exists to refuse and requires the refusal, and each
lets through what a refresh legitimately does: read the source again, fill a null, add a
field, add a term. The published side of the end-to-end cases is a real git ref in a
throwaway repository, because that is what the gate reads in CI.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "check_removals", ROOT / "tools" / "check-removals.py"
)
gate = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(gate)

FILINGS = "data/filings.ndjson"


def filing(**extra) -> dict:
    row = {
        "id": "fl:house-clerk:P:1",
        "officeholder_id": "oh:us:house:x000001",
        "office_id": "of:us:house-xx01:2025",
        "extraction_confidence": None,
        "notes": None,
        "source": {"url": "u", "retrieved_at": "2026-01-01T00:00:00Z", "content_hash": None},
    }
    row.update(extra)
    return row


def test_a_published_row_that_disappears_is_refused():
    fails, _ = gate.problems(FILINGS, [], [filing()])
    assert fails and "gone from the tree" in fails[0]


def test_a_fact_changed_in_place_is_refused():
    moved = filing(officeholder_id="oh:us:house:x000002")
    fails, _ = gate.problems(FILINGS, [moved], [filing()])
    assert fails and "officeholder_id" in fails[0]


def test_a_removed_key_is_refused():
    row = filing()
    del row["office_id"]
    fails, _ = gate.problems(FILINGS, [row], [filing()])
    assert fails and "office_id: " in fails[0] and "gone" in fails[0]


def test_facts_accrue_a_null_filled_a_key_added_a_term_added():
    now = filing(extraction_confidence="structured", asset_code="ST")
    assert gate.problems(FILINGS, [now], [filing()]) == ([], [])
    holder = {"id": "oh:1", "offices": [{"id": "of:1", "term_end": None}]}
    grown = {"id": "oh:1", "offices": [{"id": "of:1", "term_end": "2027-01-03"}, {"id": "of:2"}]}
    assert gate.problems("data/officeholders.ndjson", [grown], [holder]) == ([], [])
    shrunk = {"id": "oh:1", "offices": []}
    assert gate.problems("data/officeholders.ndjson", [shrunk], [holder])[0]


def test_a_filled_fact_cannot_be_emptied_again():
    fails, _ = gate.problems(FILINGS, [filing()], [filing(extraction_confidence="structured")])
    assert fails and "extraction_confidence" in fails[0]


def test_reading_again_moves_silently_and_new_bytes_or_prose_are_shown_not_refused():
    before = filing(source={"url": "u", "retrieved_at": "t1", "content_hash": "a"}, notes="n")
    now = filing(source={"url": "u", "retrieved_at": "t2", "content_hash": "b"}, notes="m")
    fails, warns = gate.problems(FILINGS, [now], [before])
    assert fails == [] and len(warns) == 2
    assert any("source.content_hash" in w for w in warns) and any("notes" in w for w in warns)
    elsewhere = filing(source={"url": "v", "retrieved_at": "t1", "content_hash": "a"})
    assert gate.problems(FILINGS, [elsewhere], [before])[0], "the source's URL is a fact"


def test_a_change_row_never_changes():
    change = {"id": "ch:1", "row_id": "oh:1", "change": "not listed", "capture": {"url": "u"}}
    edited = dict(change, change="listed again")
    assert gate.problems("data/changes.ndjson", [edited], [change])[0]
    assert gate.problems("data/changes.ndjson", [change], [change]) == ([], [])


def repo_with(tmp_path: Path, files: dict[str, str]) -> Path:
    """A throwaway repository whose branch `published` holds `files`."""
    for rel, text in files.items():
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / rel).write_text(text, encoding="utf-8")
    for args in (
        ["init", "-q", "-b", "published"],
        ["add", "-A"],
        ["-c", "user.email=t@example.com", "-c", "user.name=t", "commit", "-q", "-m", "p"],
    ):
        subprocess.run(["git", "-C", str(tmp_path), *args], check=True, capture_output=True)
    return tmp_path


def lines(*rows: dict) -> str:
    return "".join(json.dumps(r, sort_keys=True) + "\n" for r in rows)


def test_the_gate_reads_the_published_ref(tmp_path, monkeypatch, capsys):
    root = repo_with(tmp_path, {FILINGS: lines(filing(), filing(id="fl:house-clerk:P:2"))})
    monkeypatch.setenv("OATH_PUBLISHED_REF", "published")
    assert gate.main([str(root)]) == 0
    (root / FILINGS).write_text(lines(filing()), encoding="utf-8")
    assert gate.main([str(root)]) == 1
    assert "fl:house-clerk:P:2 is published, and gone" in capsys.readouterr().out


def test_an_unreadable_ref_fails_rather_than_passes(tmp_path, monkeypatch):
    root = repo_with(tmp_path, {FILINGS: lines(filing())})
    monkeypatch.setenv("OATH_PUBLISHED_REF", "no-such-ref")
    assert gate.main([str(root)]) == 1


def test_the_repository_keeps_every_published_row():
    assert gate.main([str(ROOT)]) == 0
