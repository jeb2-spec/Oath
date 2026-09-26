---
id: sg:stock-act-late-ptr:v1
slug: stock-act-late-ptr
version: 1
name: Periodic Transaction Report filed after the STOCK Act deadline
standard: S.2
standard_citation: 5 U.S.C. § 13105(l), added by the STOCK Act of 2012 (Pub. L. 112-105)
inputs: transaction, filing, officeholder
supersedes: null
fixture: fixtures/stock-act-late-ptr/cases.json
---

# Periodic Transaction Report filed after the STOCK Act deadline

## Description

A Member of the House reports each purchase, sale or exchange of a stock, bond, commodity future or other security over $1,000 on a Periodic Transaction Report, due within 30 days of being notified of the transaction and in no case later than 45 days after it. This Signal sets the date the Clerk's index gives each House report the register has read beside the dates the report prints for each transaction on it. It fires for a report when, for at least one of those transactions, the Clerk's date is later than the deadline, and it records by how many days and for which transactions.

## Standard

[STANDARDS.md S.2](../../STANDARDS.md#s2-stop-trading-on-congressional-knowledge-stock-act-of-2012). The deadline is [5 U.S.C. § 13105(l)](https://uscode.house.gov/view.xhtml?req=granuleid:USC-prelim-title5-section13105&num=0&edition=prelim), added to the Ethics in Government Act by the STOCK Act of 2012 ([Pub. L. 112-105](https://www.govinfo.gov/app/details/PLAW-112publ105)): a report of a transaction is due "not later than 30 days after receiving notification of any transaction required to be reported under section 13104(a)(5)(B), but in no case later than 45 days after such transaction." The House Committee on Ethics states the same deadline as the earlier of 30 days from being made aware of the transaction or 45 days from it ([Financial Disclosure](https://ethics.house.gov/financial-disclosure)), and in its [memorandum of 30 January 2023](https://ethics.house.gov/wp-content/uploads/2023/01/FINAL-PTR-Due-Date-Pink-Sheet.pdf) that the date does not move to the next business day when it falls on a weekend or holiday, and that no extension is available for these reports. Its [form and instructions](https://ethics.house.gov/wp-content/uploads/2026/02/Final-CY-2025-PTR-Form-1.pdf) define the transaction date and the notification date the report prints.

## Inputs

- **transaction.** `transaction_date`, `notified_date` and `filing_status` as the report prints them; `filing_id`.
- **filing.** `filed_at`, the date the Clerk's index gives the report; `form_type`; `extraction_confidence`, which reads `structured` only where the register read the report and its printed Filing ID agreed with the index.
- **officeholder.** `sworn_at`, the date the Clerk's roster records the officeholder as sworn in.

## Criteria

The Signal reads every report of form type `House-PTR` in the register. A report the register did not read, which is a scanned paper filing, is not evaluated: the Committee judges a paper report by its postmark, and the register does not see the postmark. A report whose date in the Clerk's index cannot be read is not evaluated.

For every other report it takes each transaction row in turn. A row is not evaluated when the report marks it with a filing status other than New, or with none (an amendment is filed after the report it amends, and the rule measures the original); when its transaction date is not a real calendar date written as the report writes dates; when the roster records no swearing-in date for the officeholder, or the transaction is dated before that date (the requirement applies to a Member's transactions, and the roster does not say whether the person held the office before the date it records); or when the transaction is dated after the report.

For a row it evaluates, the deadline is the earlier of 30 days after the notification date the report prints and 45 days after the transaction date. Where the report prints no notification date, or one that cannot be read, or one before the transaction date or after the report's own date, the 30-day limit is not applied and the deadline is 45 days after the transaction, which does not depend on it. Days are calendar days: 30 days after 13 January is 12 February. The deadline does not move when it falls on a weekend or holiday. Where the two limits fall on the same day, the 45-day limit is named as setting it.

A row is after the deadline when the Clerk's index dates the report later than the deadline, by the difference in days. The Signal fires for a report when at least one row it evaluated is after the deadline. The Finding names the report and the officeholder the register attributes it to, and for every row after the deadline gives its dates as printed, the deadline, the limit that set it, whether the deadline fell on a weekend, whether the report prints a notification date later than 45 days after the transaction, and the days after. It also counts the rows on the report it evaluated and the rows it did not, by reason.

    deadline(row) = min(notified + 30, traded + 45)   when traded <= notified <= report date
                  = traded + 45                       otherwise
    after(row)    = report date - deadline(row)       the row is after when this is 1 or more

The implementation that writes the Findings is [`src/signals/stock-act-late-ptr.py`](../../src/signals/stock-act-late-ptr.py). The reference implementation, [`src/signals/stock-act-late-ptr.ts`](../../src/signals/stock-act-late-ptr.ts), shares no code with it and must agree with it on every known-answer case and every row of the register; `python tools/rebuild.py <finding-id>` regenerates any Finding from the rows it names.

## What this Signal does not say

It does not say the House Committee on Ethics found a report late, assessed a fee, waived one, or took any other action: the register sees none of the Committee's decisions. It does not say the officeholder meant to delay a report, knew of a transaction earlier than the report says, or gained anything from its timing. It says nothing about the transactions themselves, which the Act requires reported and does not prohibit, and nothing about who holds an asset: many rows are a spouse's, a dependent child's or held jointly, whether or not the filer marked them.

It does not evaluate reports the register has not read, rows marked Amended or Deleted or marked with no status, or transactions dated before the swearing-in the roster records, so a page on which this Signal did not fire may still hold such a report or row, and the page says how many. A transaction reported on more than one report is evaluated on each. The Signal relies on the date the Clerk's index gives a report and the dates the report prints; where either is wrong, a Finding repeats the error, and the correction follows the record by supersession, never by removal. It does not rank, total or compare officeholders, and a report with many rows after the deadline is one report.

## Worked example

Against [`fixtures/stock-act-late-ptr/cases.json`](../../fixtures/stock-act-late-ptr/cases.json), twenty-six cases with no person in them, each answer worked by hand. A transaction on 2 January 2025, notified on 20 January, has a deadline of 16 February, 45 days after the transaction and earlier than 30 days after the notification: a report dated 16 February is on time and one dated 17 February is after the deadline by 1 day. A report dated 10 April 2025 listing a transaction of 3 March notified the same day (deadline 2 April), one of 20 March notified the same day (deadline 19 April) and one marked Amended fires for the first row only, with this text: "The Clerk's index dates this report 2025-04-10, which is later than the deadline the rule sets for 1 of the 2 transactions on it that this Signal evaluated, by 8 days. The deadline is the earlier of 30 days after the notification date the report prints and 45 days after the transaction date (5 U.S.C. § 13105(l))." A notification date printed before the transaction date is not applied, so a report of 5 May for a transaction of 10 April with a printed notification of 1 April does not fire, where applying that date would have put it 4 days after 1 May.
