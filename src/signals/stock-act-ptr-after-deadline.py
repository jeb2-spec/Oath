#!/usr/bin/env python3
"""A Periodic Transaction Report dated after the STOCK Act deadline.

sg:stock-act-ptr-after-deadline:v1.

The definition is docs/signals/stock-act-ptr-after-deadline.md, and this file does what it
says. It is the implementation that writes the register's Findings, in the same language
as the adapter and the seal, so one writer serialises every sealed row. The reference
implementation the course named, src/signals/stock-act-ptr-after-deadline.ts, shares no
code with this one and must agree with it on every known-answer case under
fixtures/stock-act-ptr-after-deadline/ and on every row of the register; a Vitest test
holds the two together, so neither can drift without CI going red.

Pure: it reads the rows it is handed and returns rows. No file, no network, no clock.
Standard library.

The rule (5 U.S.C. § 13105(l); STANDARDS.md S.2): a transaction is reported "not later
than 30 days after receiving notification" of it, "but in no case later than 45 days
after such transaction". The House Committee on Ethics' instructions for these reports
state that a due date on a weekend or holiday does not move. So, for each row a report
lists, in scope:

    deadline = the earlier of  notified + 30 days  and  transaction + 45 days
               (the 30-day limit only where the report prints a notification date
               that reads, falls on or after the transaction, and on or before the
               report's own date; otherwise transaction + 45 days alone)
    after    = the Clerk's index date for the report, minus the deadline, in days

and the Signal fires for a report when any row it evaluates is after by a day or more.

In scope means the rule plainly reaches the row: a transaction marked New, in an asset the
report codes as a stock, a corporate bond or note, an option or a cryptocurrency, over the
rule's $1,000 threshold, dated on or after the swearing-in the roster records for this
Congress, with a deadline in the years whose instructions the register has read. What it
declines to evaluate, it counts and names, because silence is a result and the page must
say which silence it is.
"""

from __future__ import annotations

import re
from datetime import date, timedelta

SLUG = "stock-act-ptr-after-deadline"
VERSION = 1
SIGNAL_ID = f"sg:{SLUG}:v{VERSION}"
FORM_TYPE = "House-PTR"
NOTIFICATION_DAYS = 30
TRANSACTION_DAYS = 45
THRESHOLD = 1000
CITATION = "5 U.S.C. § 13105(l)"
FRAME = "Presence in the register is not evidence of wrongdoing."

# The asset codes evaluated. The Clerk's legend defines them and the register has not read it
# at its source; the rows the reports code so name stocks, corporate bonds and notes, options
# and cryptocurrencies. Every other code, and a row with none, is counted and not evaluated.
EVALUATED_CODES = ("CS", "CT", "OP", "ST")
ETF = re.compile(r"\bETF\b")
# The instructions the register has read for the deadline (the Committee's CY 2025 form,
# read 2026-09-21) govern reports in 2025 on. Earlier instructions have not always said the
# same thing about a weekend, so a deadline before this date is not evaluated.
RULE_FROM = date(2025, 1, 1)

# The words an outcome is written in. The reference implementation, the fixtures and
# the pages use the same ones; change one and every one of them has to change with it.
AFTER, ON_TIME, NOT_EVALUATED = "after", "on time", "not evaluated"
EVALUATED, NOT_READ = "evaluated", "not read"
BY_NOTIFICATION, BY_TRANSACTION = "notification", "transaction"
APPLIED = "applied"
BEFORE_SWEARING_IN = "dated before this Congress's swearing-in"

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


# ---- the federal calendar, 5 U.S.C. § 6103 -------------------------------------------------


def nth_weekday(year: int, month: int, weekday: int, n: int) -> date:
    first = date(year, month, 1)
    return first + timedelta(days=(weekday - first.weekday()) % 7 + 7 * (n - 1))


def last_weekday(year: int, month: int, weekday: int) -> date:
    last = date(year + month // 12, month % 12 + 1, 1) - timedelta(days=1)
    return last - timedelta(days=(last.weekday() - weekday) % 7)


def observed(day: date) -> date:
    """A holiday on a Saturday is observed the Friday before, on a Sunday the Monday after."""
    return day + timedelta(days={5: -1, 6: 1}.get(day.weekday(), 0))


def federal_holidays(year: int) -> dict[date, str]:
    """The legal public holidays of 5 U.S.C. § 6103(a) in one year, on the days observed."""
    fixed = [
        ("New Year's Day", date(year, 1, 1)),
        ("Independence Day", date(year, 7, 4)),
        ("Veterans Day", date(year, 11, 11)),
        ("Christmas Day", date(year, 12, 25)),
    ]
    if year >= 2021:
        fixed.append(("Juneteenth National Independence Day", date(year, 6, 19)))
    moving = [
        ("Birthday of Martin Luther King, Jr.", nth_weekday(year, 1, 0, 3)),
        ("Washington's Birthday", nth_weekday(year, 2, 0, 3)),
        ("Memorial Day", last_weekday(year, 5, 0)),
        ("Labor Day", nth_weekday(year, 9, 0, 1)),
        ("Columbus Day", nth_weekday(year, 10, 0, 2)),
        ("Thanksgiving Day", nth_weekday(year, 11, 3, 4)),
    ]
    shifted = {
        observed(day): name if observed(day) == day else f"{name} (observed)" for name, day in fixed
    }
    return shifted | {day: name for name, day in moving}


def holiday(day: date) -> str | None:
    for year in (day.year, day.year + 1):  # New Year's Day can be observed on 31 December
        name = federal_holidays(year).get(day)
        if name:
            return name
    return None


def not_a_business_day(day: date) -> str | None:
    """Saturday, Sunday or the holiday's name; None on a business day."""
    return {5: "Saturday", 6: "Sunday"}.get(day.weekday()) or holiday(day)


def first_business_day_after(day: date) -> date:
    day += timedelta(days=1)
    while not_a_business_day(day):
        day += timedelta(days=1)
    return day


def holidays_between(start: date, end: date) -> list[tuple[str, str]]:
    """The holidays on the weekdays strictly after start and before end, as (date, name)."""
    out, day = [], start + timedelta(days=1)
    while day < end:
        name = holiday(day)
        if name and day.weekday() < 5:
            out.append((day.isoformat(), name))
        day += timedelta(days=1)
    return out


# ---- one row, one report --------------------------------------------------------------------


def out_of_scope(row: dict) -> str | None:
    """Why the rule does not plainly reach this row, or None when it does."""
    code = row.get("asset_code")
    if not code:
        return "no asset code printed"
    if code not in EVALUATED_CODES:
        return f"asset coded {code}"
    if code == "ST" and ETF.search(row.get("asset") or ""):
        return "coded as a stock, named as an ETF"
    top = (row.get("amount_range") or {}).get("max")
    if top is not None and top <= THRESHOLD:
        return "$1,000 or less"
    return None


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
    scope = out_of_scope(row)
    if scope:
        return {"state": NOT_EVALUATED, "reason": scope}
    if sworn_at is None:
        return {"state": NOT_EVALUATED, "reason": "no swearing-in date recorded"}
    if traded < sworn_at:
        return {"state": NOT_EVALUATED, "reason": BEFORE_SWEARING_IN}
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
    if deadline < RULE_FROM:
        return {"state": NOT_EVALUATED, "reason": "deadline before 2025"}

    out = {
        "state": ON_TIME,
        "deadline": deadline.isoformat(),
        "set_by": set_by,
        "notification": notification,
    }
    days = (filed_at - deadline).days
    if days > 0:
        falls_on = not_a_business_day(deadline)
        out.update(
            state=AFTER,
            days_after=days,
            deadline_falls_on=falls_on,
            first_business_day_after=(
                first_business_day_after(deadline).isoformat() if falls_on else None
            ),
            notified_after_limit=notification == APPLIED and notified > deadline,
            days_after_notice=(filed_at - notified).days if notification == APPLIED else None,
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
    which limit set it, the days, and what kind of day the deadline fell on."""
    return {
        "id": row["id"],
        "transaction_date": row.get("transaction_date"),
        "notified_date": row.get("notified_date"),
        "notification": result["notification"],
        "deadline": result["deadline"],
        "set_by": result["set_by"],
        "days_after": result["days_after"],
        "deadline_falls_on": result["deadline_falls_on"],
        "first_business_day_after": result["first_business_day_after"],
        "notified_after_limit": result["notified_after_limit"],
        "days_after_notice": result["days_after_notice"],
    }


# ---- the words -------------------------------------------------------------------------------


def thousands(n: int) -> str:
    return f"{n:,}"


def those(part: int, whole: int) -> str:
    """How a sentence names the rows a clause is about."""
    if part == whole == 1:
        return "that transaction"
    if part == whole:
        return "each of them"
    return f"{thousands(part)} of them"


def days_phrase(low: int, high: int) -> str:
    if low == high:
        return f"{thousands(low)} {'day' if low == 1 else 'days'}"
    return f"{thousands(low)} to {thousands(high)} days"


def describe(filed_at: str, evaluated: int, after: list[dict]) -> str:
    """The Finding's sentence. Its fixed words are the ones the Council read; its blanks
    come from the rows. It names the report, not the person, and draws no conclusion."""
    k = len(after)
    days = [r["days_after"] for r in after]
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
        f"rule sets for {which}, by {days_phrase(min(days), max(days))}. The deadline is the "
        "earlier of 30 days after the notification date the report prints and 45 days after "
        f"the transaction date ({CITATION})."
    )
    unusable = sum(1 for r in after if r["notification"] != APPLIED)
    if unusable:
        text += (
            f" For {those(unusable, k)} the report prints no usable notification date, so the "
            "deadline is 45 days after the transaction."
        )
    late = [r for r in after if r["notified_after_limit"]]
    if late:
        gap = [r["days_after_notice"] for r in late]
        when = (
            "the same day as that notification"
            if max(gap) == 0
            else f"{days_phrase(min(gap), max(gap))} after it"
        )
        text += (
            f" For {those(len(late), k)} the report prints a notification date later than 45 "
            "days after the transaction, so the deadline had passed before that notification; "
            f"the Clerk's index dates the report {when}."
        )
    decided = [
        r for r in after if r["deadline_falls_on"] and filed_at <= r["first_business_day_after"]
    ]
    if decided:
        kinds = {r["deadline_falls_on"] for r in decided}
        (only,) = kinds if len(kinds) == 1 else (None,)
        if only in ("Saturday", "Sunday"):
            kind = f"a {only}"
        elif only:
            kind = f"{only}, a federal holiday"
        else:
            kind = "a weekend or a federal holiday"
        days_after = {r["first_business_day_after"] for r in decided}
        (next_day,) = days_after if len(days_after) == 1 else (None,)
        between = sorted(
            {
                pair
                for r in decided
                for pair in holidays_between(
                    read_date(r["deadline"]), read_date(r["first_business_day_after"])
                )
            }
        )
        held = "; ".join(f"{name}, {day}, was a federal holiday" for day, name in between)
        text += (
            f" For {those(len(decided), k)} the deadline fell on {kind}, and the Clerk's index "
            "dates the report on or before the first business day after it"
            + (f", {next_day}" if next_day else "")
            + (f" ({held})" if held else "")
            + "; the Committee's instructions for these reports state that a due date on a "
            "weekend or holiday does not move."
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
        "frame": FRAME,
        "superseded_by": None,
        "notes": None,
    }


def withdrawal(head: dict, outcome: dict | None) -> dict:
    """The row a correction writes when this Signal does not fire, on the register's rows as
    they now stand, on a report it once fired on: what the rows now show, in the Signal's
    words, with no row after the deadline. Written once, by `run.py --correct`, never
    regenerated; the person correcting supplies the reason, which the notes carry."""
    report_id = head["producing_filings"][0]
    if outcome is None:
        filed_at, rows, evaluated, not_evaluated = None, 0, 0, {}
        now = (
            "The register's rows no longer include this report, so this Signal evaluates none "
            "of its rows."
        )
    else:
        filed_at, rows = outcome["filed_at"], outcome["rows"]
        evaluated, not_evaluated = outcome["evaluated"], outcome["not_evaluated"]
        if outcome["state"] == NOT_READ:
            now = (
                f"The register does not read this report, which the Clerk's index dates "
                f"{filed_at}, so this Signal evaluates none of its rows."
            )
        elif evaluated == 0:
            now = (
                f"The Clerk's index dates this report {filed_at}, and on the register's rows as "
                "they now stand this Signal evaluates none of the transactions on it; each is "
                "counted, with its reason, in this row's evidence."
            )
        else:
            n = (
                "the one transaction"
                if evaluated == 1
                else f"any of the {thousands(evaluated)} transactions"
            )
            now = (
                f"The Clerk's index dates this report {filed_at}, and on the register's rows as "
                f"they now stand it is not later than the deadline the rule sets for {n} on it "
                f"that this Signal evaluated ({CITATION})."
            )
    return {
        "id": f"fn:{SIGNAL_ID}:{report_id}",
        "signal_id": SIGNAL_ID,
        "officeholder_id": head["officeholder_id"],
        "producing_filings": [report_id],
        "producing_rows": [],
        "description": (
            f"{now} So this Signal does not fire on it. The Finding this row corrects stays in "
            "the ledger, and this row's notes say why, and cite the source."
        ),
        "evidence": {
            "filed_at": filed_at,
            "rows_on_report": rows,
            "evaluated": evaluated,
            "after": 0,
            "not_evaluated": not_evaluated,
            "rows": [],
        },
        "frame": FRAME,
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
