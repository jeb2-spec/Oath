"""The Signal runner keeps facts (CHARTER Vow V; INVARIANTS §12, §14) and derives, never types.

Each refusal is proven by making the change it refuses and requiring the refusal.
"""

from __future__ import annotations

import importlib.util
import json
import shutil
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


run = load(ROOT / "src" / "signals" / "run.py", "signals_run")
validator = load(ROOT / "tools" / "validate-schemas.py", "validate_schemas")

SID = "sg:stock-act-late-ptr:v1"


def finding(base: str, after: int = 1, description: str = "text", **extra) -> dict:
    row = {
        "id": base,
        "signal_id": SID,
        "officeholder_id": "oh:us:example:example",
        "producing_filings": ["fl:example:P:0001"],
        "producing_rows": [{"schema": "transaction", "id": "tx:example:0001:001"}],
        "description": description,
        "evidence": {"after": after},
        "superseded_by": None,
        "notes": None,
    }
    row.update(extra)
    return row


def published(row: dict) -> dict:
    return dict(row, fired_at="2026-01-01T00:00:00Z", build_hash="a" * 64)


def test_a_new_finding_is_added_with_the_builds_provenance():
    out = run.merge([], [finding("fn:1")], SID, "2026-02-02T00:00:00Z", "b" * 64)
    assert out == [dict(finding("fn:1"), fired_at="2026-02-02T00:00:00Z", build_hash="b" * 64)]


def test_a_published_finding_stays_byte_identical_on_a_later_run():
    ledger = [published(finding("fn:1"))]
    out = run.merge(ledger, [finding("fn:1")], SID, "2027-01-01T00:00:00Z", "c" * 64)
    assert out == ledger


def test_a_published_finding_is_never_rewritten_in_place():
    ledger = [published(finding("fn:1", description="as published"))]
    with pytest.raises(run.Refusal, match="differently"):
        run.merge(ledger, [finding("fn:1", description="changed")], SID, "t", "d")


def test_a_published_finding_is_never_dropped():
    ledger = [published(finding("fn:1"))]
    with pytest.raises(run.Refusal, match="no longer produces it"):
        run.merge(ledger, [], SID, "t", "d")


def test_a_correction_chain_is_followed_to_its_head():
    old = published(finding("fn:1", description="as published", superseded_by="fn:1:c1"))
    head = published(finding("fn:1:c1", description="corrected", notes="the Clerk re-dated it"))
    out = run.merge([old, head], [finding("fn:1", description="corrected")], SID, "t", "d")
    assert out == [old, head]


def test_a_correction_that_records_no_firing_accepts_silence_and_refuses_a_return():
    old = published(finding("fn:1", superseded_by="fn:1:c1"))
    withdrawn = published(finding("fn:1:c1", after=0, description="no longer fires"))
    assert run.merge([old, withdrawn], [], SID, "t", "d") == [old, withdrawn]
    with pytest.raises(run.Refusal):
        run.merge([old, withdrawn], [finding("fn:1")], SID, "t", "d")


def test_a_chain_with_no_head_is_refused():
    old = published(finding("fn:1", superseded_by="fn:1:c1"))
    with pytest.raises(run.Refusal, match="no current row"):
        run.merge([old], [finding("fn:1")], SID, "t", "d")


def test_another_versions_findings_are_carried_untouched():
    other = published(dict(finding("fn:v0"), signal_id="sg:stock-act-late-ptr:v0"))
    out = run.merge([other], [finding("fn:1")], SID, "t", "d")
    assert other in out and len(out) == 2


def test_the_definition_file_becomes_a_valid_signal_row():
    row = run.parse_definition(ROOT / "docs" / "signals" / "stock-act-late-ptr.md")
    schemas = validator.load_schemas(ROOT)
    schema = schemas["signal.schema.json"]
    assert validator.validate(row, schema, schemas, "signal.schema.json") == []
    assert row["id"] == SID and row["standard"]["id"] == "S.2"
    assert row["inputs"] == ["transaction", "filing", "officeholder"]


def test_a_definition_missing_its_not_saying_section_is_refused(tmp_path):
    text = (ROOT / "docs" / "signals" / "stock-act-late-ptr.md").read_text("utf-8")
    cut = text.split("## What this Signal does not say")[0] + "## Worked example\n\nx\n"
    path = tmp_path / "stock-act-late-ptr.md"
    path.write_text(cut, encoding="utf-8")
    with pytest.raises(run.Refusal, match="What this Signal does not say"):
        run.parse_definition(path)


def test_the_register_regenerates_byte_identically():
    """The sealed Signal files are exactly what the definitions and the rows produce."""
    assert run.main([str(ROOT), "--check"]) == 0


def test_check_mode_sees_a_hand_edit(tmp_path):
    for rel in ("data", "docs/signals", "src/signals", "fixtures/stock-act-late-ptr"):
        shutil.copytree(ROOT / rel, tmp_path / rel)
    ledger = tmp_path / "data" / "findings.ndjson"
    rows = [json.loads(line) for line in ledger.read_text("utf-8").splitlines() if line]
    rows[0]["description"] += " An edit by hand."
    ledger.write_text("".join(run.canonical(r) for r in rows), encoding="utf-8")
    assert run.main([str(tmp_path), "--check"]) == 1


# ---- corrections, written by the runner so a person supplies only the reason -----------

signal = load(ROOT / "src" / "signals" / "stock-act-late-ptr.py", "stock_act_late_ptr_for_run")
BECAUSE = "The Clerk's index re-dated the report; https://disclosures-clerk.house.gov/"


def test_a_correction_carries_what_the_signal_now_produces_and_the_run_accepts_it():
    ledger = [published(finding("fn:1", description="as published"))]
    now = [finding("fn:1", description="as the record now reads")]
    out = run.correct(ledger, now, [], "fn:1", BECAUSE, "2026-10-01T00:00:00Z", "e" * 64, signal)
    old, new = out
    assert old == dict(ledger[0], superseded_by="fn:1:c1"), "the only change a published row takes"
    assert new == dict(
        now[0],
        id="fn:1:c1",
        notes=BECAUSE,
        fired_at="2026-10-01T00:00:00Z",
        build_hash="e" * 64,
    )
    assert run.merge(out, now, SID, "t", "d") == out


def test_a_withdrawal_takes_the_signals_own_words_and_is_a_valid_row():
    ledger = [published(finding("fn:1"))]
    outcome = {
        "filing_id": "fl:example:P:0001",
        "officeholder_id": "oh:us:example:example",
        "filed_at": "2025-03-01",
        "state": "evaluated",
        "rows": 2,
        "evaluated": 2,
        "after": 0,
        "not_evaluated": {},
        "finding_id": None,
    }
    out = run.correct(
        ledger, [], [outcome], "fn:1", BECAUSE, "2026-10-01T00:00:00Z", "e" * 64, signal
    )
    withdrawn = out[1]
    assert withdrawn["id"] == "fn:1:c1" and withdrawn["producing_rows"] == []
    assert withdrawn["evidence"]["after"] == 0 and withdrawn["evidence"]["filed_at"] == "2025-03-01"
    assert "not later than the deadline the rule sets for any of the 2" in withdrawn["description"]
    assert withdrawn["notes"] == BECAUSE
    assert run.merge(out, [], SID, "t", "d") == out, "silence is accepted after a withdrawal"
    schemas = validator.load_schemas(ROOT)
    schema = schemas["finding.schema.json"]
    assert validator.validate(withdrawn, schema, schemas, "finding.schema.json") == []


def test_a_correction_without_a_cited_source_is_refused():
    ledger = [published(finding("fn:1"))]
    with pytest.raises(run.Refusal, match="URL"):
        run.correct(ledger, [], [], "fn:1", "the Clerk re-dated it", "t", "d", signal)


def test_a_correction_the_record_does_not_call_for_is_refused():
    ledger = [published(finding("fn:1"))]
    with pytest.raises(run.Refusal, match="still produces it as published"):
        run.correct(ledger, [finding("fn:1")], [], "fn:1", BECAUSE, "t", "d", signal)
    with pytest.raises(run.Refusal, match="not in the ledger"):
        run.correct(ledger, [], [], "fn:2", BECAUSE, "t", "d", signal)


def test_the_next_correction_takes_the_next_number_and_only_the_head_changes():
    first = published(finding("fn:1", description="first", superseded_by="fn:1:c1"))
    head = published(finding("fn:1:c1", description="second", notes="an earlier correction"))
    now = [finding("fn:1", description="third")]
    out = run.correct([first, head], now, [], "fn:1:c1", BECAUSE, "t", "d", signal)
    assert [r["id"] for r in out] == ["fn:1", "fn:1:c1", "fn:1:c2"]
    assert out[0] == first and out[1] == dict(head, superseded_by="fn:1:c2")


def test_a_refused_run_is_answered_by_one_correction_and_every_gate_holds(tmp_path):
    for rel in ("data", "docs/signals", "src/signals", "fixtures/stock-act-late-ptr"):
        shutil.copytree(ROOT / rel, tmp_path / rel)
    ledger_path = tmp_path / "data" / "findings.ndjson"
    before = [json.loads(line) for line in ledger_path.read_text("utf-8").splitlines() if line]
    target = before[0]
    report = target["producing_filings"][0]
    filings_path = tmp_path / "data" / "filings.ndjson"
    filings = [json.loads(line) for line in filings_path.read_text("utf-8").splitlines() if line]
    for row in filings:
        if row["id"] == report:
            row["filed_at"] = target["evidence"]["rows"][0]["transaction_date"]
    filings_path.write_text("".join(run.canonical(r) for r in filings), encoding="utf-8")
    at = "2026-10-19T09:20:00Z"
    assert run.main([str(tmp_path), "--at", at]) == 1, "the run refuses to drop it"
    code = run.main([str(tmp_path), "--at", at, "--correct", target["id"], "--because", BECAUSE])
    assert code == 0
    assert run.main([str(tmp_path), "--check"]) == 0
    after = [json.loads(line) for line in ledger_path.read_text("utf-8").splitlines() if line]
    assert len(after) == len(before) + 1
    assert next(r for r in after if r["id"] == target["id"]) == dict(
        target, superseded_by=target["id"] + ":c1"
    )
