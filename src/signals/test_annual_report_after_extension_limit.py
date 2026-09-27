"""The annual-report Signal against its known-answer cases. RUBRIC.md gate 4.

Every expected answer in fixtures/annual-report-after-extension-limit/cases.json was worked by
hand and by a separate script from the calendar, not by this implementation. The reference
implementation in TypeScript is held to the same file by
src/signals/annual-report-after-extension-limit.test.ts.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
CASES = json.loads(
    (ROOT / "fixtures" / "annual-report-after-extension-limit" / "cases.json").read_text("utf-8")
)


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


signal = load(ROOT / "src" / "signals" / "annual-report-after-extension-limit.py", "annual_report")
validator = load(ROOT / "tools" / "validate-schemas.py", "validate_schemas")


@pytest.mark.parametrize("case", CASES["cases"], ids=lambda c: c["name"])
def test_each_known_answer(case):
    rows = [*case.get("also", []), case["report"]]
    findings, outcomes = signal.evaluate([case["officeholder"]], rows, [])
    findings = [f for f in findings if f["producing_filings"] == [case["report"]["id"]]]
    outcomes = [o for o in outcomes if o["filing_id"] == case["report"]["id"]]
    want = case["expect"]
    if not want["in_scope"]:
        assert outcomes == [] and findings == [], "not an annual report a Member filed"
        return
    (outcome,) = outcomes
    # Read, with one row, its date, compared or set aside with the reason: the house shape.
    assert (outcome["state"], outcome["rows"]) == ("evaluated", 1)
    assert outcome["evaluated"] == (1 if want["compared"] else 0)
    assert outcome["not_evaluated"] == ({want["reason"]: 1} if want["reason"] else {})
    assert bool(findings) is want["fires"]
    assert outcome["after"] == (1 if want["fires"] else 0)
    if want.get("description"):
        assert findings[0]["description"] == want["description"]
    if want["fires"]:
        (found,) = findings
        for key in ("original_due", "latest", "days_after_latest"):
            assert found["evidence"][key] == want[key], key
        assert found["frame"] == signal.FRAME
        assert "late" not in found["description"].lower().replace("latest", "")
        assert found["producing_filings"] == [case["report"]["id"]]


def test_a_finding_and_its_withdrawal_validate_against_the_finding_schema():
    """Every row the Signal can write has the shape the ledger accepts, with the two fields
    only a build gives it filled in as a build would."""
    firing = next(c for c in CASES["cases"] if c["expect"].get("fires"))
    (found,), (outcome,) = signal.evaluate([firing["officeholder"]], [firing["report"]], [])
    schemas = {p.name: json.loads(p.read_text("utf-8")) for p in (ROOT / "schemas").glob("*.json")}
    built = {"fired_at": "2026-09-28T09:17:00Z", "build_hash": "0" * 64}
    for row in (found, signal.withdrawal(found, outcome), signal.withdrawal(found, None)):
        errors = validator.validate(
            row | built, schemas["finding.schema.json"], schemas, "finding.schema.json"
        )
        assert errors == [], errors
    # The runner, the seal and the pages tell a firing from a withdrawal by evidence.after.
    run = load(ROOT / "src" / "signals" / "run.py", "signal_run")
    assert run.fires(found)
    assert not run.fires(signal.withdrawal(found, outcome))
    assert not run.fires(signal.withdrawal(found, None))


def test_no_extension_row_changes_whether_it_fires():
    """The Council's reading: no sentence rests on the join. The same report fires or not the
    same way whatever extension rows the register holds for its filer."""
    case = next(c for c in CASES["cases"] if c["name"] == "the day after the due date")
    extension = {
        "id": "fl:example:X:0002",
        "officeholder_id": case["report"]["officeholder_id"],
        "filed_at": "2026-06-04",
        "printed": {"status": "Member", "extension_length_days": 90, "new_due_date": "2026-08-13"},
    }
    alone = signal.evaluate([case["officeholder"]], [case["report"]], [])
    joined = signal.evaluate([case["officeholder"]], [case["report"], extension], [])
    assert alone == joined


def test_every_outcome_and_the_run_record_validate_against_their_schemas():
    """The run record is what every page's answer is counted from, and its schemas were written
    for a Signal that reads rows on a report. This Signal's outcomes take the same shape, a read
    report with one row, so every case's outcome and the summary over all of them must validate
    as they are, under an officeholder id of the roster's form."""
    run = load(ROOT / "src" / "signals" / "run.py", "signal_run")
    schemas = {p.name: json.loads(p.read_text("utf-8")) for p in (ROOT / "schemas").glob("*.json")}
    holder = "oh:us:ex:e000001"
    outcomes = []
    for case in CASES["cases"]:
        report = dict(case["report"], officeholder_id=holder)
        _, got = signal.evaluate([dict(case["officeholder"], id=holder)], [report], [])
        outcomes += got
    for outcome in outcomes:
        errors = validator.validate(
            outcome, schemas["signal-outcome.schema.json"], schemas, "signal-outcome.schema.json"
        )
        assert errors == [], errors
    summary = run.run_record(signal.SIGNAL_ID, "0" * 64, outcomes)[0]
    errors = validator.validate(
        summary, schemas["signal-run.schema.json"], schemas, "signal-run.schema.json"
    )
    assert errors == [], errors
    assert summary["reports_by_state"] == {"evaluated": len(outcomes)}


@pytest.mark.parametrize(
    "moved, reason",
    [
        ({"filed_at": "2026-08-14"}, signal.DAY_AFTER),
        ({"printed_filing_date": "2026-09-23"}, signal.DATES_DISAGREE),
        ({"filed_at": "2026-07-01"}, signal.WITHIN),
        ({"filed_at": "2026-05-01"}, None),
    ],
)
def test_a_withdrawal_says_why_on_the_rows_as_they_now_stand(moved, reason):
    """A withdrawal is written once, into a ledger that never removes a row, so its sentence
    must say the reason the rows now give: the Council's second reading, Seat G, found every
    withdrawal saying the report was not after the latest date, whatever the reason was."""
    firing = next(c for c in CASES["cases"] if c["expect"].get("fires"))
    (head,), _ = signal.evaluate([firing["officeholder"]], [firing["report"]], [])
    report = json.loads(json.dumps(firing["report"]))
    if "filed_at" in moved:
        for key in ("filing_date", "signed_on"):
            report["printed"][key] = moved["filed_at"]
        report["filed_at"] = moved["filed_at"]
    else:
        report["printed"]["filing_date"] = moved["printed_filing_date"]
    _, (outcome,) = signal.evaluate([firing["officeholder"]], [report], [])
    text = signal.withdrawal(head, outcome)["description"]
    if reason:
        assert f"does not evaluate it: {reason}." in text
        assert "not dated after the latest date" not in text
    else:
        assert "not dated after the latest date" in text


@pytest.mark.parametrize("year", CASES["calendar"]["years"], ids=lambda y: str(y["filing_year"]))
def test_the_calendar_for_each_filing_year(year):
    """The two dates the law sets, held for years this version does not read, so the weekend
    and holiday arithmetic is tested though filing year 2025 moves neither date."""
    d = signal.dates_for(year["filing_year"])
    got = {
        "original_due": d["due"].isoformat(),
        "original_due_moved_for": d["due_moved_for"],
        "latest": d["latest"].isoformat(),
        "latest_moved_for": d["latest_moved_for"],
    }
    assert got == {k: v for k, v in year.items() if k != "filing_year"}
