#!/usr/bin/env python3
"""Periodic Transaction Report filed after the STOCK Act deadline. sg:stock-act-late-ptr:v1.

The definition is docs/signals/stock-act-late-ptr.md, and this file does what it says.
It is the implementation that writes the register's Findings, in the same language as
the adapter and the seal, so one writer serialises every sealed row. The reference
implementation the course named, src/signals/stock-act-late-ptr.ts, shares no code
with this one and must agree with it on every known-answer case under
fixtures/stock-act-late-ptr/ and on every row of the register; a Vitest test holds
the two together, so neither can drift without CI going red.

Pure: it reads the rows it is handed and returns rows. No file, no network, no clock.
Standard library.

The rule (5 U.S.C. § 13105(l); STANDARDS.md S.2): a transaction is reported "not later
than 30 days after receiving notification" of it, "but in no case later than 45 days
after such transaction". The House Committee on Ethics states that the date does not
move to the next business day when it falls on a weekend or holiday, and that no
extension is available for these reports. So, for each row of a report:

    deadline = the earlier of  notified + 30 days  and  transaction + 45 days
               (the 30-day limit only where the report prints a notification date
               that reads, falls on or after the transaction, and on or before the
               report's own date; otherwise transaction + 45 days alone)
    after    = the Clerk's index date for the report, minus the deadline, in days

and the Signal fires for a report when any row it evaluates is after by a day or more.

What it declines to evaluate, it counts and names, because silence is a result and
the page must say which silence it is: a report the register did not read; a row the
filer marked Amended or Deleted, or marked nothing; a transaction dated before the
swearing-in the roster records; dates that do not read, or contradict each other.
"""

from __future__ import annotations

import re
from datetime import date, timedelta

SLUG = "stock-act-late-ptr"
VERSION = 1
SIGNAL_ID = f"sg:{SLUG}:v{VERSION}"
FORM_TYPE = "House-PTR"
NOTIFICATION_DAYS = 30
TRANSACTION_DAYS = 45
CITATION = "5 U.S.C. § 13105(l)"

# The words an outcome is written in. The reference implementation, the fixtures and
# the pages use the same ones; change one and every one of them has to change with it.
AFTER, ON_TIME, NOT_EVALUATED = "after", "on time", "not evaluated"
EVALUATED, NOT_READ = "evaluated", "not read"
BY_NOTIFICATION, BY_TRANSACTION = "notification", "transaction"
APPLIED = "applied"

ISO_DATE = re.compile(r"\d{4}-\d{2}-\d{2}")


def read_date(value: object) -> date | None:
    """A real calendar date written YYYY-MM-DD, or None. Nothing else is read as a date:
    not 05/15/2025, not 20250515, not 2025-02-30."""
    if not isinstance(value, str) or not ISO_DATE.fullmatch(value):
        return None
    try:
        return date(int(value[0:4]), int(value[5:7]), int(value[8:10]))
    except ValueError:
        return None


def weekend(day: date) -> str | None:
    return {5: "Saturday", 6: "Sunday"}.get(day.weekday())


def evaluate_row(row: dict, filed_at: date | None, sworn_at: date | None) -> dict:
    """One transaction row against the rule. The first reason not to evaluate wins."""
    status = (row.get("filing_status") or "").strip()
    if not status:
        return {"state": NOT_EVALUATED, "reason": "no filing status printed"}
    if status.lower() != "new":
        return {"state": NOT_EVALUATED, "reason": f"marked {status}"}
    if filed_at is None:
        return {"state": NOT_EVALUATED, "reason": "report date not read"}
    traded = read_date(row.get("transaction_date"))
    if traded is None:
        return {"state": NOT_EVALUATED, "reason": "transaction date not read"}
    if sworn_at is None:
        return {"state": NOT_EVALUATED, "reason": "no swearing-in date recorded"}
    if traded < sworn_at:
        return {"state": NOT_EVALUATED, "reason": "dated before the swearing-in"}
    if traded > filed_at:
        return {"state": NOT_EVALUATED, "reason": "transaction dated after the report"}

    printed = row.get("notified_date")
    notified = read_date(printed)
    if printed is None or printed == "":
        notification = "not printed"
    elif notified is None:
        notification = "not read"
    elif notified < traded:
        notification = "before the transaction"
    elif notified > filed_at:
        notification = "after the report"
    else:
        notification = APPLIED

    limit_45 = traded + timedelta(days=TRANSACTION_DAYS)
    deadline, set_by = limit_45, BY_TRANSACTION
    if notification == APPLIED:
        limit_30 = notified + timedelta(days=NOTIFICATION_DAYS)
        if limit_30 < limit_45:
            deadline, set_by = limit_30, BY_NOTIFICATION

    out = {
        "state": ON_TIME,
        "deadline": deadline.isoformat(),
        "set_by": set_by,
        "notification": notification,
    }
    days = (filed_at - deadline).days
    if days > 0:
        out.update(
            state=AFTER,
            days_after=days,
            weekend=weekend(deadline),
            notified_after_limit=notification == APPLIED and notified > deadline,
        )
    return out


def evaluate_report(report: dict, rows: list[dict], sworn_at: date | None) -> dict:
    """One report: its state, how many rows were evaluated, and each row's result."""
    results = {}
    if report.get("extraction_confidence") != "structured":
        state = NOT_READ
    else:
        filed_at = read_date(report.get("filed_at"))
        state = EVALUATED if filed_at is not None else NOT_EVALUATED
        for row in rows:
            results[row["id"]] = evaluate_row(row, filed_at, sworn_at)
    not_evaluated: dict[str, int] = {}
    for result in results.values():
        if result["state"] == NOT_EVALUATED:
            not_evaluated[result["reason"]] = not_evaluated.get(result["reason"], 0) + 1
    after = [row for row in rows if results.get(row["id"], {}).get("state") == AFTER]
    return {
        "state": state,
        "rows": len(rows),
        "evaluated": sum(1 for r in results.values() if r["state"] != NOT_EVALUATED),
        "after": len(after),
        "not_evaluated": not_evaluated,
        "results": results,
        "after_rows": [evidence_row(row, results[row["id"]]) for row in after],
    }


def evidence_row(row: dict, result: dict) -> dict:
    """What a reader needs to check one row by hand: the dates as printed, the deadline,
    which limit set it, and the days."""
    return {
        "id": row["id"],
        "transaction_date": row.get("transaction_date"),
        "notified_date": row.get("notified_date"),
        "notification": result["notification"],
        "deadline": result["deadline"],
        "set_by": result["set_by"],
        "days_after": result["days_after"],
        "weekend": result["weekend"],
        "notified_after_limit": result["notified_after_limit"],
    }


def thousands(n: int) -> str:
    return f"{n:,}"


def those(part: int, whole: int) -> str:
    """How a sentence names the rows a clause is about."""
    if part == whole == 1:
        return "that transaction"
    if part == whole:
        return "each of them"
    return f"{thousands(part)} of them"


def describe(filed_at: str, evaluated: int, after: list[dict]) -> str:
    """The Finding's sentence. Its fixed words are the ones the Council read; its blanks
    come from the rows. It names the report, not the person, and draws no conclusion."""
    k = len(after)
    days = [r["days_after"] for r in after]
    low, high = min(days), max(days)
    if low == high:
        span = f"{thousands(low)} {'day' if low == 1 else 'days'}"
    else:
        span = f"{thousands(low)} to {thousands(high)} days"
    if evaluated == 1:
        which = "the one transaction on it that this Signal evaluated"
    elif k == evaluated:
        which = f"each of the {thousands(evaluated)} transactions on it that this Signal evaluated"
    else:
        which = (
            f"{thousands(k)} of the {thousands(evaluated)} transactions on it "
            "that this Signal evaluated"
        )
    text = (
        f"The Clerk's index dates this report {filed_at}, which is later than the deadline the "
        f"rule sets for {which}, by {span}. The deadline is the earlier of 30 days after the "
        "notification date the report prints and 45 days after the transaction date "
        f"({CITATION})."
    )
    unusable = sum(1 for r in after if r["notification"] != APPLIED)
    if unusable:
        text += (
            f" For {those(unusable, k)} the report prints no usable notification date, so the "
            "deadline is 45 days after the transaction."
        )
    late_notice = sum(1 for r in after if r["notified_after_limit"])
    if late_notice:
        text += (
            f" For {those(late_notice, k)} the report prints a notification date later than 45 "
            "days after the transaction, so the deadline had passed before that notification."
        )
    weekends = sum(1 for r in after if r["weekend"])
    if weekends:
        text += (
            f" For {those(weekends, k)} the deadline fell on a weekend; the House Committee on "
            "Ethics states that the date does not move to the next business day."
        )
    return text


def finding(report: dict, outcome: dict) -> dict | None:
    """The Finding for a report, without the two fields only a build can give it
    (fired_at, build_hash), or None when no evaluated row is after the deadline."""
    after = outcome["after_rows"]
    if not after:
        return None
    return {
        "id": f"fn:{SIGNAL_ID}:{report['id']}",
        "signal_id": SIGNAL_ID,
        "officeholder_id": report["officeholder_id"],
        "producing_filings": [report["id"]],
        "producing_rows": [{"schema": "transaction", "id": r["id"]} for r in after],
        "description": describe(report["filed_at"], outcome["evaluated"], after),
        "evidence": {
            "filed_at": report["filed_at"],
            "rows_on_report": outcome["rows"],
            "evaluated": outcome["evaluated"],
            "after": outcome["after"],
            "not_evaluated": outcome["not_evaluated"],
            "rows": after,
        },
        "superseded_by": None,
        "notes": None,
    }


def withdrawal(head: dict, outcome: dict | None) -> dict:
    """The row a correction writes when this Signal no longer fires on a report it once
    fired on: what the record now shows, in the Signal's words, with no row after the
    deadline. Written once, by `run.py --correct`, and never regenerated; the person
    correcting supplies the notes, which say what changed and cite the source."""
    report_id = head["producing_filings"][0]
    if outcome is None:
        filed_at, rows, evaluated, not_evaluated = None, 0, 0, {}
        now = (
            "The Clerk's index no longer lists this report, so this Signal evaluates none of "
            "its rows."
        )
    else:
        filed_at, rows = outcome["filed_at"], outcome["rows"]
        evaluated, not_evaluated = outcome["evaluated"], outcome["not_evaluated"]
        if outcome["state"] == NOT_READ:
            now = (
                f"The register no longer reads this report, which the Clerk's index dates "
                f"{filed_at}, so this Signal evaluates none of its rows."
            )
        elif evaluated == 0:
            now = (
                f"The Clerk's index dates this report {filed_at}, and on the record as now read "
                "this Signal evaluates none of the transactions on it; each is counted, with its "
                "reason, in this row's evidence."
            )
        else:
            n = "the one transaction" if evaluated == 1 else f"any of the {thousands(evaluated)}"
            now = (
                f"The Clerk's index dates this report {filed_at}, and on the record as now read "
                f"it is not later than the deadline the rule sets for {n} on it that this Signal "
                f"evaluated ({CITATION})."
            )
    return {
        "id": f"fn:{SIGNAL_ID}:{report_id}",
        "signal_id": SIGNAL_ID,
        "officeholder_id": head["officeholder_id"],
        "producing_filings": [report_id],
        "producing_rows": [],
        "description": (
            f"{now} So this Signal does not fire on it. The row this one corrects stays in the "
            "ledger, and this row's notes say what changed and cite the source."
        ),
        "evidence": {
            "filed_at": filed_at,
            "rows_on_report": rows,
            "evaluated": evaluated,
            "after": 0,
            "not_evaluated": not_evaluated,
            "rows": [],
        },
        "superseded_by": None,
        "notes": None,
    }


def evaluate(
    officeholders: list[dict], filings: list[dict], transactions: list[dict]
) -> tuple[list[dict], list[dict]]:
    """Every House transaction report in the register, in id order. Returns the Findings
    (without fired_at and build_hash) and one outcome per report, fired or not."""
    sworn = {h["id"]: read_date(h.get("sworn_at")) for h in officeholders}
    by_report: dict[str, list[dict]] = {}
    for row in transactions:
        by_report.setdefault(row["filing_id"], []).append(row)
    findings, outcomes = [], []
    reports = sorted((f for f in filings if f.get("form_type") == FORM_TYPE), key=lambda f: f["id"])
    for report in reports:
        rows = sorted(by_report.get(report["id"], []), key=lambda r: r["id"])
        outcome = evaluate_report(report, rows, sworn.get(report["officeholder_id"]))
        found = finding(report, outcome)
        if found:
            findings.append(found)
        outcomes.append(
            {
                "filing_id": report["id"],
                "officeholder_id": report["officeholder_id"],
                "filed_at": report.get("filed_at"),
                "state": outcome["state"],
                "rows": outcome["rows"],
                "evaluated": outcome["evaluated"],
                "after": outcome["after"],
                "not_evaluated": outcome["not_evaluated"],
                "finding_id": found["id"] if found else None,
            }
        )
    return findings, outcomes
