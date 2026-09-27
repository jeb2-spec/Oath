#!/usr/bin/env python3
"""An annual financial disclosure report dated after the latest date an extension could reach.

sg:annual-report-after-extension-limit:v1.

The definition is docs/signals/annual-report-after-extension-limit.md, and this file does
what it says. The reference implementation, src/signals/annual-report-after-extension-limit.ts,
shares no code with this one and must agree with it on every known-answer case under
fixtures/annual-report-after-extension-limit/ and on every row of the register.

Pure: it reads the rows it is handed and returns rows. No file, no network, no clock.
Standard library. It carries its own copy of the federal calendar, because a Signal's version
is frozen by the hashes of its own files, and a calendar shared with another Signal could
change this one's criteria without changing its version (INVARIANTS §11).

The rule (5 U.S.C. § 13103(d), (g)(1)): a Member who performs the duties of the office for
more than 60 days in a calendar year files an annual report on or before 15 May of the next
year, and extensions may add at most 90 days in total. The House Committee on Ethics' 2025
Instruction Guide moves an annual report's due date that falls on a weekend or a federal
holiday to the next business day, and does not move the end of a 90-day extension. So, for
each Member's annual report, read by its own header:

    due     = 15 May of the next year, or the next business day after it
    latest  = the later of 15 May + 90 days and due + 90 days, moved to the next business
              day where it falls on a weekend or holiday (the later reading, always)
    fires   where the report is dated two days or more after latest

A report dated after its due date and on or before the day after `latest` is not evaluated:
an extension may cover it, and the register does not decide whether one did. The day after
`latest` is not evaluated either, because the clock behind the printed date is not
established (docs/wanted/wanted.ndjson, wt:the-filing-systems-clock). No extension notice,
joined or not, decides anything here (docs/council/2026-09-27-the-annual-report-draft.md).
"""

from __future__ import annotations

import re
from datetime import date, timedelta

SLUG = "annual-report-after-extension-limit"
VERSION = 1
SIGNAL_ID = f"sg:{SLUG}:v{VERSION}"
FILING_TYPE = "Annual Report"
STATUS = "Member"
EXTENSION_DAYS = 90
SERVICE_DAYS = 60
CITATION = "5 U.S.C. § 13103(d), (g)(1)"
FRAME = "Presence in the register is not evidence of wrongdoing."
# The filing years whose instructions the register has read at their source: the Committee's
# Instruction Guide for calendar year 2025.
FIRST_YEAR = 2025

EVALUATED = "evaluated"
NOT_EVALUATED = "not evaluated"

NO_YEAR = "prints no filing year"
YEAR_UNREAD = "a filing year whose instructions the register has not read"
NO_DATE = "a date the register cannot read"
DATES_DISAGREE = "the index date, the printed filing date and the signature date disagree"
NO_SWEARING_IN = "the roster records no swearing-in"
SHORT_SERVICE = "60 days or fewer of service in the filing year, by the swearing-in recorded"
WITHIN = "after its due date, within the time an extension may cover"
DAY_AFTER = "the day after the latest date, whose clock the register has not established"

ISO_DATE = re.compile(r"\d{4}-\d{2}-\d{2}")


def read_date(value: object) -> date | None:
    """A real calendar date written YYYY-MM-DD, or None."""
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
        ("Juneteenth National Independence Day", date(year, 6, 19)),
        ("Independence Day", date(year, 7, 4)),
        ("Veterans Day", date(year, 11, 11)),
        ("Christmas Day", date(year, 12, 25)),
    ]
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


def not_a_business_day(day: date) -> str | None:
    """Saturday, Sunday or the holiday's name; None on a business day."""
    weekend = {5: "Saturday", 6: "Sunday"}.get(day.weekday())
    if weekend:
        return weekend
    for year in (day.year, day.year + 1):  # New Year's Day can be observed on 31 December
        name = federal_holidays(year).get(day)
        if name:
            return name
    return None


def on_or_after_business_day(day: date) -> tuple[date, str | None]:
    """The day itself if it is a business day, or the first after it, with the reason moved."""
    why = not_a_business_day(day)
    moved = day
    while not_a_business_day(moved):
        moved += timedelta(days=1)
    return moved, why


# ---- one report -----------------------------------------------------------------------------


def dates_for(year: int) -> dict:
    """The due date and the latest date for a filing year, with why each moved, if it did."""
    may15 = date(year + 1, 5, 15)
    due, due_moved_for = on_or_after_business_day(may15)
    cap = max(may15 + timedelta(days=EXTENSION_DAYS), due + timedelta(days=EXTENSION_DAYS))
    latest, latest_moved_for = on_or_after_business_day(cap)
    return {
        "cap": cap,
        "due": due,
        "due_moved_for": due_moved_for,
        "latest": latest,
        "latest_moved_for": latest_moved_for,
    }


def is_annual(filing: dict) -> bool:
    printed = filing.get("printed") or {}
    return printed.get("filing_type") == FILING_TYPE and printed.get("status") == STATUS


def evaluate_report(report: dict, sworn_at: date | None) -> dict:
    """One annual report: its state, the reason where it is not evaluated, and the dates."""
    printed = report.get("printed") or {}
    year = printed.get("filing_year")

    def not_evaluated(reason: str, **facts) -> dict:
        return {"state": NOT_EVALUATED, "reason": reason, "after": False, **facts}

    if isinstance(year, bool) or not isinstance(year, int):
        return not_evaluated(NO_YEAR)
    if year < FIRST_YEAR:
        return not_evaluated(YEAR_UNREAD, filing_year=year)
    d = dates_for(year)
    known = {"filing_year": year, **d}
    dated = [read_date(report.get("filed_at")), read_date(printed.get("filing_date"))]
    dated.append(read_date(printed.get("signed_on")))
    if any(x is None for x in dated):
        return not_evaluated(NO_DATE, **known)
    if len(set(dated)) != 1:
        return not_evaluated(DATES_DISAGREE, **known)
    if sworn_at is None:
        return not_evaluated(NO_SWEARING_IN, **known)
    served = (date(year, 12, 31) - max(sworn_at, date(year, 1, 1))).days + 1
    if served <= SERVICE_DAYS:
        return not_evaluated(SHORT_SERVICE, **known)
    dated_on = dated[0]
    facts = {"dated": dated_on, **known}
    if dated_on <= d["due"]:
        return {"state": EVALUATED, "reason": None, "after": False, **facts}
    if dated_on <= d["latest"]:
        return not_evaluated(WITHIN, **facts)
    if dated_on == d["latest"] + timedelta(days=1):
        return not_evaluated(DAY_AFTER, **facts)
    return {"state": EVALUATED, "reason": None, "after": True, **facts}


def moved_from(why: str | None, day: date) -> str:
    """Where a date was moved off a day that is not a business day, which day and why."""
    if not why:
        return ""
    which = f"a {why}" if why in ("Saturday", "Sunday") else why
    return f", the first business day after {day.isoformat()}, {which}"


def describe(result: dict) -> str:
    """The Finding's sentences: what the report is, its dates, the rule, the days, and nothing
    about why. Short sentences, each one fact, because they are read in translation."""
    d, due, latest = result["dated"], result["due"], result["latest"]
    year = result["filing_year"]
    return (
        f"This is an annual financial disclosure report for calendar year {year}. The Clerk's "
        f"index dates it {d.isoformat()}, the same date the report prints as its filing date and "
        f"its signature line gives. It was due {due.isoformat()}"
        f"{moved_from(result['due_moved_for'], date(year + 1, 5, 15))}. The statute lets "
        f"extensions add at most {EXTENSION_DAYS} days ({CITATION}), so the latest date any "
        f"extension could reach was {latest.isoformat()}"
        f"{moved_from(result['latest_moved_for'], result['cap'])}. The report is dated "
        f"{(d - latest).days} days after that date and {(d - due).days} days after its due date. "
        "The register cannot see an extension for service in a combat zone, which 5 U.S.C. "
        "§ 13103(g)(2) allows beyond 90 days."
    )


def finding(report: dict, result: dict) -> dict | None:
    """The Finding for a report, without fired_at and build_hash, or None where it does not
    fire."""
    if not result["after"]:
        return None
    return {
        "id": f"fn:{SIGNAL_ID}:{report['id']}",
        "signal_id": SIGNAL_ID,
        "officeholder_id": report["officeholder_id"],
        "producing_filings": [report["id"]],
        "description": describe(result),
        # `after` is the house count of rows after, here the report's one date, which the
        # runner, the seal and the pages read to tell a firing from a withdrawal.
        "evidence": {
            "after": 1,
            "filed_at": report["filed_at"],
            "filing_year": result["filing_year"],
            "due": result["due"].isoformat(),
            "due_moved_for": result["due_moved_for"],
            "latest": result["latest"].isoformat(),
            "latest_moved_for": result["latest_moved_for"],
            "days_after_latest": (result["dated"] - result["latest"]).days,
            "days_after_due": (result["dated"] - result["due"]).days,
        },
        "frame": FRAME,
        "superseded_by": None,
        "notes": None,
    }


def withdrawal(head: dict, outcome: dict | None) -> dict:
    """The row a correction writes when this Signal no longer fires, on the register's rows as
    they now stand, on a report it once fired on. Written once, by run.py --correct."""
    report_id = head["producing_filings"][0]
    if outcome is None:
        now = (
            "The register's rows no longer include this report as an annual report whose "
            "header the register read, so this Signal does not evaluate it."
        )
        filed_at, not_evaluated = None, {}
    else:
        filed_at, not_evaluated = outcome["filed_at"], outcome["not_evaluated"]
        if outcome["state"] == NOT_EVALUATED:
            reason = next(iter(not_evaluated), "not evaluated")
            now = (
                f"The Clerk's index dates this report {filed_at}, and on the register's rows as "
                f"they now stand this Signal does not evaluate it: {reason}."
            )
        else:
            now = (
                f"The Clerk's index dates this report {filed_at}, and on the register's rows as "
                "they now stand it is not dated after the latest date an extension could reach "
                f"({CITATION})."
            )
    return {
        "id": f"fn:{SIGNAL_ID}:{report_id}",
        "signal_id": SIGNAL_ID,
        "officeholder_id": head["officeholder_id"],
        "producing_filings": [report_id],
        "description": (
            f"{now} So this Signal does not fire on it. The Finding this row corrects stays in "
            "the ledger, and this row's notes say why, and cite the source."
        ),
        "evidence": {"after": 0, "filed_at": filed_at, "not_evaluated": not_evaluated},
        "frame": FRAME,
        "superseded_by": None,
        "notes": None,
    }


def evaluate(
    officeholders: list[dict], filings: list[dict], transactions: list[dict]
) -> tuple[list[dict], list[dict]]:
    """Every annual report a Member filed whose header the register read, in id order.
    Returns the Findings (without fired_at and build_hash) and one outcome per report: read,
    with one row, its date, compared or not evaluated with the reason."""
    sworn = {h["id"]: read_date(h.get("sworn_at")) for h in officeholders}
    findings, outcomes = [], []
    for report in sorted((f for f in filings if is_annual(f)), key=lambda f: f["id"]):
        result = evaluate_report(report, sworn.get(report["officeholder_id"]))
        found = finding(report, result)
        if found:
            findings.append(found)
        outcomes.append(
            {
                "filing_id": report["id"],
                "officeholder_id": report["officeholder_id"],
                "filed_at": report.get("filed_at"),
                # The house shape of an outcome: the report is read (its header), and the one
                # row this Signal reads on it, the report's own date, is compared or set aside
                # with its reason, as a transaction row is on a transaction report.
                "state": EVALUATED,
                "rows": 1,
                "evaluated": 1 if result["state"] == EVALUATED else 0,
                "after": 1 if result["after"] else 0,
                "not_evaluated": {result["reason"]: 1} if result["reason"] else {},
                "finding_id": found["id"] if found else None,
            }
            # The two dates the report is compared with, wherever its filing year gives them,
            # so a page states them from the sealed record and never recomputes the calendar.
            | (
                {"due": result["due"].isoformat(), "latest": result["latest"].isoformat()}
                if "due" in result
                else {}
            )
        )
    return findings, outcomes
