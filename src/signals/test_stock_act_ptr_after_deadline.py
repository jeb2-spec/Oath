"""The first Signal against its known-answer cases. RUBRIC.md gate 4; NEXT.md D.2 and S.2.

Every expected answer in fixtures/stock-act-ptr-after-deadline/cases.json was worked by hand
from the calendar, not by this implementation. The reference implementation in TypeScript is
held to the same file by src/signals/stock-act-ptr-after-deadline.test.ts.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CASES = json.loads(
    (ROOT / "fixtures" / "stock-act-ptr-after-deadline" / "cases.json").read_text("utf-8")
)
DEFAULTS = CASES["row_defaults"]


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


signal = load(ROOT / "src" / "signals" / "stock-act-ptr-after-deadline.py", "stock_act_ptr")
validator = load(ROOT / "tools" / "validate-schemas.py", "validate_schemas")


def rows_of(case: dict) -> tuple[list[dict], list[dict], list[dict]]:
    """A case as the register's own row shapes, placeholders only."""
    holder = {"id": case["officeholder"]["id"], "sworn_at": case["officeholder"]["sworn_at"]}
    report = case["report"]
    filing = {
        "id": report["id"],
        "officeholder_id": holder["id"],
        "form_type": "House-PTR",
        "source_form_code": "P",
        "filed_at": report["filed_at"],
        "extraction_confidence": "structured" if report["read"] else None,
    }
    transactions = [
        {
            **DEFAULTS,
            **{k: v for k, v in row.items() if k != "expect"},
            "filing_id": report["id"],
            "officeholder_id": holder["id"],
        }
        for row in case.get("rows", [])
    ]
    return [holder], [filing], transactions


def test_every_row_meets_its_worked_answer():
    for case in CASES["cases"]:
        holders, filings, transactions = rows_of(case)
        sworn = signal.read_date(holders[0]["sworn_at"])
        outcome = signal.evaluate_report(filings[0], transactions, sworn)
        for row in case.get("rows", []):
            assert outcome["results"].get(row["id"]) == row["expect"], (case["name"], row["id"])


def test_every_report_meets_its_worked_answer():
    for case in CASES["cases"]:
        holders, filings, transactions = rows_of(case)
        findings, outcomes = signal.evaluate(holders, filings, transactions)
        want = case["expect"]
        (outcome,) = outcomes
        assert bool(findings) is want["fires"], case["name"]
        assert outcome["evaluated"] == want["evaluated"], case["name"]
        if "state" in want:
            assert outcome["state"] == want["state"], case["name"]
        if "not_evaluated" in want:
            assert outcome["not_evaluated"] == want["not_evaluated"], case["name"]
        if want["fires"]:
            (found,) = findings
            assert [r["id"] for r in found["producing_rows"]] == want["after"], case["name"]
            assert found["producing_filings"] == [case["report"]["id"]]
            assert outcome["finding_id"] == found["id"]
            if "description" in want:
                assert found["description"] == want["description"], case["name"]
        else:
            assert outcome["finding_id"] is None


def test_every_finding_is_a_valid_row():
    schemas = validator.load_schemas(ROOT)
    for case in CASES["cases"]:
        findings, _ = signal.evaluate(*rows_of(case))
        for found in findings:
            row = dict(found, fired_at="2026-01-01T00:00:00Z", build_hash="0" * 64)
            schema = schemas["finding.schema.json"]
            errors = validator.validate(row, schema, schemas, "finding.schema.json")
            assert errors == [], (case["name"], errors)


def test_the_evaluation_is_deterministic():
    everything = [rows_of(case) for case in CASES["cases"]]
    holders = everything[0][0]
    filings = [filing for _, fs, _ in everything for filing in fs]
    transactions = [row for _, _, ts in everything for row in ts]
    first = signal.evaluate(holders, filings, transactions)
    second = signal.evaluate(holders, list(reversed(filings)), list(reversed(transactions)))
    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)


def test_the_boundaries_the_rule_turns_on():
    """The two days the answer changes, and the limit that binds first, stated directly."""
    new = {
        **DEFAULTS,
        "filing_status": "New",
        "transaction_date": "2025-01-02",
        "notified_date": "2025-01-20",
    }
    sworn = signal.read_date("2023-01-03")
    on_45 = signal.evaluate_row(new, signal.read_date("2025-02-16"), sworn)
    on_46 = signal.evaluate_row(new, signal.read_date("2025-02-17"), sworn)
    assert on_45["state"] == signal.ON_TIME and on_46["state"] == signal.AFTER
    assert on_46["days_after"] == 1 and on_46["set_by"] == signal.BY_TRANSACTION


def test_only_real_iso_dates_are_read():
    assert signal.read_date("2024-02-29") is not None
    unreadable = (
        "2025-02-29",
        "2025-02-30",
        "05/15/2025",
        "20250515",
        "2025-W07-4",
        "",
        None,
        20250515,
    )
    for value in unreadable:
        assert signal.read_date(value) is None, value


def test_no_fixture_reaches_the_register():
    findings = ROOT / "data" / "findings.ndjson"
    if findings.is_file():
        text = findings.read_text("utf-8")
        assert ":example:" not in text and "oh:us:example" not in text


def test_the_signal_touches_nothing_outside_its_arguments():
    source = (ROOT / "src" / "signals" / "stock-act-ptr-after-deadline.py").read_text("utf-8")
    banned = ("open(", "urllib", "socket", "subprocess", "datetime.now", "date.today", "time.time")
    for word in banned:
        assert word not in source, word


def test_the_federal_calendar_is_the_statutes():
    """5 U.S.C. § 6103(a), on the days observed, for the years the register's rows reach."""
    got = {d.isoformat(): n for d, n in signal.federal_holidays(2025).items()}
    assert got == {
        "2025-01-01": "New Year's Day",
        "2025-01-20": "Birthday of Martin Luther King, Jr.",
        "2025-02-17": "Washington's Birthday",
        "2025-05-26": "Memorial Day",
        "2025-06-19": "Juneteenth National Independence Day",
        "2025-07-04": "Independence Day",
        "2025-09-01": "Labor Day",
        "2025-10-13": "Columbus Day",
        "2025-11-11": "Veterans Day",
        "2025-11-27": "Thanksgiving Day",
        "2025-12-25": "Christmas Day",
    }
    # 2027-12-31 is a Friday and the observed New Year's Day of 2028, a Saturday.
    assert signal.holiday(signal.read_date("2027-12-31")) == "New Year's Day (observed)"
    assert signal.not_a_business_day(signal.read_date("2025-09-01")) == "Labor Day"
    assert signal.first_business_day_after(signal.read_date("2025-08-30")).isoformat() == (
        "2025-09-02"
    )


def test_every_finding_carries_the_frame():
    for case in CASES["cases"]:
        findings, _ = signal.evaluate(*rows_of(case))
        for found in findings:
            assert found["frame"] == "Presence in the register is not evidence of wrongdoing."
