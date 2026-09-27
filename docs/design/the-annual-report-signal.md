# The annual report against its deadline: a draft Signal

*Draft, 2026-09-27. This is not a Signal. Nothing here is in `data/signals.ndjson`, no code
implements it, and no Finding rests on it. It goes to the Council's adversarial reading before
anything is built, because it would publish a new kind of sentence about every Member of the
House. NEXT.md S.2 is the course it belongs to.*

## Abstract

Every Member who serves more than 60 days in a year files a financial disclosure report for it by
15 May of the next year, with extensions of up to 90 days in total. The register's one Signal today
reads the transaction report, which reaches only the Members who trade; the annual report reaches
nearly every seat. This draft proposes a Signal that sets each Member's annual report beside its
deadline, and shows, from the documents themselves, that a version which ignored extensions would
be false about most of the House.

## What the record holds, read at the source on 2026-09-27

- **Which reports are annual.** The Clerk publishes no legend for the index's one-letter codes, and
  the register interprets none (`wt:the-form-codes`). The documents say what they are: each prints
  *Filing Type*, *Filing Year* and *Filing Date* in its header. In a sample, 38 of 40 `O` documents
  say *Filing Type: Annual Report*, by a Member, and 2 carry no text; every `A` document that
  carries text says *Amendment Report*. The Signal reads the document's own line and never the code.
- **Which date.** On all 38 sampled annual reports the *Filing Date* the document prints, the date
  its last line says it was digitally signed, and the date the Clerk's index gives it are the same
  day. For transaction reports the index date is the signature date on all 409 whose text the
  register can read (`tools/check-signed-dates.py`).
- **How many are after 15 May.** 25 of those 38 are dated after 15 May 2026. That is the fact this
  whole draft is organised around.
- **Extensions are public.** The Committee's 2025 Instruction Guide: the Committee grants
  extensions, a single filing's may not exceed 90 days, and *pursuant to the STOCK Act, the Clerk is
  required to post notice of all FD extensions granted for Members and Candidates*. The index's `X`
  documents are extension forms: in a sample of 20, 14 name an *Original Report* as the report due,
  1 a *New Filer Report*, and each prints its *Extension Length*; 5 carry no text.

## The standard

- 5 U.S.C. § 13103(d): an individual described in subsection (f) who performs the duties of the
  office for more than 60 days in a calendar year *shall file on or before May 15 of the succeeding
  year*. Members of Congress are among those subsection (f) lists.
- 5 U.S.C. § 13103(g)(1): extensions *may be granted under procedures prescribed by the supervising
  ethics office*, *but the total of such extensions shall not exceed 90 days*.
- 5 U.S.C. § 13106(d)(1): a report filed *more than 30 days after the later of* the due date or,
  where an extension was granted, *the last day of the filing extension period* carries a $200 fee;
  (d)(2): the fee may be waived in extraordinary circumstances. The register computes no fee.
- The Committee's 2025 Instruction Guide: an annual report whose deadline falls on a weekend or a
  federal holiday is due the next business day; an extension deadline 90 days from the original
  due date is not moved for a weekend or holiday; a report filed electronically is timely when it
  is submitted on or before the due date.

All four read at uscode.house.gov and ethics.house.gov on 2026-09-27. They enter STANDARDS.md with
the next sealed build, which is the only way sealed doctrine changes.

## The proposed definition

**Description.** A Member of the House files an annual financial disclosure report for each
calendar year of more than 60 days' service, due 15 May of the next year and later where an
extension was granted. This Signal sets the date on each Member's annual report beside that
deadline, counting any extension the Clerk has posted for it, and fires where the report is dated
after the deadline, recording by how many days.

**Criteria, in prose.** The Signal reads documents whose own header says *Filing Type: Annual
Report* and *Status: Member*, for one filing year. It evaluates nothing else, whatever the code.
For each such report:

1. The due date is 15 May of the year after the filing year, moved to the next business day where
   15 May falls on a weekend or a federal holiday.
2. Where the Clerk has posted an extension for that Member, that year and the original report, the
   deadline is the due date plus the extension's printed length, not moved for a weekend. More than
   one extension is summed, and never past 90 days.
3. The report is after the deadline when its date is later than the deadline, by the difference in
   days, and the Signal fires.

**Not evaluated, with the reason counted, never silently.** A document with no text or no *Filing
Type* line. A report whose date cannot be read. **A Member for whom an extension document exists
for that year that the register cannot read, or whose report type or length it cannot read:** the
report is not evaluated at all, because the error in the other direction is a false sentence about
a person. A Member the roster records as serving 60 days or fewer in the filing year. A report for
a year before the first year whose instructions the register has read.

**What this Signal does not say.** It does not say the Committee found the report late, assessed a
fee or waived one; the register sees none of its decisions. It does not say anything about what the
report discloses. It does not say an extension was needed or why one was asked for: an extension is
a lawful part of the rule, and a report filed under one inside its length is on time. It does not
rank, total or compare Members, and silence on a page is a report on time, a report not yet read,
or a report not evaluated, and the page says which.

## The join, which is where this can go wrong

An extension document carries no filing ID of the report it extends. Joining the two is done by
officeholder, filing year and report type, and that is an inference about a named person: the
first in this project that joins two documents by who filed them rather than by an identifier
either one prints. It has to be read as such.

The direction of every doubt is fixed in advance: **where the join is uncertain, the Signal does not
fire.** An extension that cannot be tied to one report makes the report not evaluated, not late.
That costs silence on some pages. Silence is a legitimate result; a sentence saying a Member filed
late when they filed on the last day of a granted extension is the defect this project exists to
prevent, and the sample says it would be the common case, not the rare one.

## Known-answer cases to write before any code

Each worked by hand, with no person in it:

1. A report dated 15 May of the next year: on time. Dated 16 May: after by 1 day.
2. 15 May on a Saturday: due Monday the 17th; a report that Monday is on time.
3. A 90-day extension: a report dated 13 August (15 May + 90) is on time; 14 August is after by 1.
4. An extension whose 90th day is a Sunday: not moved; the Monday is after by 1.
5. Two extensions of 60 and 60 days: summed and capped at 90.
6. An extension document with no readable length: the report is not evaluated.
7. An extension for a New Filer Report and none for the annual: the annual report's deadline is
   unextended.
8. A document whose code is `O` but whose header says anything but *Annual Report*: not read.
9. A document whose code is `A` whose header says *Amendment Report*: not read, since an amendment
   is measured by its own rule.
10. A Member the roster records as sworn in for 60 days or fewer of the filing year: not evaluated.

## Threats to validity, in the order a careful reader would raise them

1. **Whether a posted extension is a granted one.** The Guide says the Clerk posts notice of the
   extensions granted; the register has read the form's words and not a statement that every form
   it posts was granted. The Signal treats a posted extension as granted. If some were not, it
   under-fires, which is the safe direction, and it says so.
2. **Whether an extension's length is the one granted or the one requested.** The form prints
   *Extension Length*; the register reads that number and nothing else.
3. **The sample.** 40 of 422 annual-coded documents and 20 of 276 extension documents. The adapter
   reads every header at build time before the Signal runs; nothing here is a count of the House.
4. **Reports on paper.** Documents with no text cannot be read for their type or their date, and
   are not evaluated, so a Member whose report is on paper cannot be among those on which it fires.
5. **The 60-day service condition,** which the roster answers only through the swearing-in and
   departure dates it records.
6. **The index is live.** The 2025 archive grows through the next year; a build is a statement
   about one retrieval.

## What it needs before it ships

1. The adapter records, for every document it fetches, the *Filing Type*, *Filing Year*, *Filing
   Date*, *Extension Length* and *Report Type Due* its header prints, as fields of the filing row, so
   the Signal reads sealed rows and never a document at run time. That is a schema change and a new
   build.
2. The Signal file in `docs/signals/`, both implementations sharing no code, the known-answer cases
   above, and the pages that show it.
3. The Council's reading of this draft and of the built Signal, with the join as the first thing on
   the table.
4. STANDARDS.md and SOURCES.md rows for the four sources above, in the sealed build that first
   carries the Signal.
