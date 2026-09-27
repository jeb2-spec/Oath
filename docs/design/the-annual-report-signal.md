# The annual report against the latest date the law allows it: a draft Signal

*Draft, second version, 2026-09-27, after the Council's reading of the first
([docs/council/2026-09-27-the-annual-report-draft.md](../council/2026-09-27-the-annual-report-draft.md)).
This is not a Signal. Nothing here is in `data/signals.ndjson`, no code implements it, and no
Finding rests on it. The built Signal goes to the Council again before it publishes.*

## Abstract

Every Member of the U.S. House of Representatives who serves more than 60 days in a year is
required to file a financial disclosure report for it by 15 May of the next year, and the Committee
on Ethics may grant extensions of up to 90 days in total. This draft proposes a Signal that fires
only where a Member's annual report is dated after the latest date any extension the statute allows
could reach. Before that date the register does not decide whether a report was covered; it shows the
report's date and the extension notices the Clerk lists, and says it does not evaluate them. The
first draft tried to decide the window by joining each report to its extension, and the Council
showed, from the documents, that the join would have been false about most of the Members it fired
on.

## What the Council found, and why this draft is different

The first draft set a report beside 15 May plus any extension the register had tied to the same
Member. Five of the seven seats found, independently, the same hole: the join sees only the rows the
adapter attributes. In the build of 2026-09-22, 12 annual-coded reports dated after 15 May have no
extension row tied to their Member; for 8 of them an extension row sits at the Member's own seat
under the Member's surname, set aside by the name match for a person to decide. Two seats read one of
those forms by eye: it is the Committee's own paper form, for that Member's annual report, with the
Committee's box *Days granted* filled in. The first draft would have published *after the deadline*
about Members whose extensions the Clerk lists. Extensions are also posted weeks after they are
granted, and a filer can hold two notices whose printed lengths are increments, not totals. **A rule
that depends on the register holding every extension is a rule that fires on what the register
failed to hold.**

So the Signal no longer depends on the join at all. It fires only where no extension the statute
allows could cover the report, which is a fact about the report's own date and the statute, and is
true whatever the register holds.

## What the record holds, read at the source on 2026-09-27

- **Which reports are annual.** The Clerk publishes no legend for the index's one-letter codes, and
  the register interprets none (`wt:the-form-codes`). Each document prints *Filing Type*, *Status*,
  *Filing Year* and *Filing Date* in its header. The Signal reads those lines, never the code.
- **Which date.** On all 38 annual reports read that day, the Filing Date the document prints, the
  date its last line says it was digitally signed and the date the Clerk's index gives it are the
  same day.
- **Where the dates fall.** Of the 422 rows the index codes `O` in the build of 2026-09-22 (a sizing
  count; the Signal reads headers, not codes): 162 are dated on or before 15 May 2026, 252 in the 90
  days after it, 3 on 14 August, and 5 later than that.
- **What the index lists about extensions.** The `X` documents are the Committee's extension forms,
  posted by the Clerk (*pursuant to the STOCK Act, the Clerk is required to post notice of all FD
  extensions granted*, the Committee's 2025 Instruction Guide). Each form that carries text prints its
  *Extension Length*, *Original Due Date* and *New Due Date*; the paper form carries a *Days granted*
  box.

## The standard

- [5 U.S.C. § 13103(d)](https://uscode.house.gov/view.xhtml?req=granuleid:USC-prelim-title5-section13103&num=0&edition=prelim):
  an individual described in subsection (f) who performs the duties of the office for more than 60
  days in a calendar year *shall file on or before May 15 of the succeeding year*. Subsection (f)
  lists Members of Congress, and [§ 13101](https://uscode.house.gov/view.xhtml?req=granuleid:USC-prelim-title5-section13101&num=0&edition=prelim)
  defines a Member to include a Delegate and the Resident Commissioner.
- § 13103(g)(1): extensions *may be granted under procedures prescribed by the supervising ethics
  office*, *but the total of such extensions shall not exceed 90 days*. § 13103(g)(2) allows more for
  service in a combat zone, which the register cannot see.
- [5 U.S.C. § 13106(d)](https://uscode.house.gov/view.xhtml?req=granuleid:USC-prelim-title5-section13106&num=0&edition=prelim):
  a report filed more than 30 days after the later of its due date or the last day of a granted
  extension carries a $200 fee, which may be waived. The register computes no fee.
- The Committee's [2025 Instruction Guide](https://ethics.house.gov/wp-content/uploads/2026/07/7-8-2026-2025-Published-Instruction-Guide.pdf):
  an annual report whose deadline falls on a weekend or federal holiday is due the next business
  day; an extension deadline 90 days from the original due date is not moved for a weekend or
  holiday.

Read at uscode.house.gov (currency: through Pub. L. 119-103, as the pages say) and ethics.house.gov on
2026-09-27. They enter STANDARDS.md and SOURCES.md in the sealed build that first carries the Signal.

## The proposed definition

**Description.** A Member of the U.S. House of Representatives, including its Delegates and its
Resident Commissioner, is required to file an annual financial disclosure report for each calendar
year of more than 60 days' service, due 15 May of the next year, with extensions of up to 90 days in
total. This Signal compares the date on each Member's annual report with the latest date any
extension the statute allows could reach, and reports a result only where the report's date is
later, stating by how many days.

**Criteria.**

1. The Signal reads documents whose own header says *Filing Type: Annual Report* and *Status:
   Member*, for one filing year. It reads nothing by its index code.
2. A report is read only where the index date, the Filing Date it prints and the date its signature
   line gives are the same day. Otherwise it is not evaluated.
3. The due date is 15 May of the year after the filing year, moved to the next business day where 15
   May falls on a Saturday, a Sunday or a federal holiday.
4. **The latest date** is the due date plus 90 days; where the rules could be read to put it on either
   of two days (a due date moved for a weekend, a 90th day on a weekend), the later one. No extension
   the statute allows outside a combat zone can reach past it.
5. The Signal fires where the report is dated **two days or more** after the latest date. A report
   dated the day after is not evaluated, because the register has not established the time zone of
   the date the filing system prints (`wt:the-filing-systems-clock`), and a report submitted late in
   the evening could carry the next day's date.
6. The Finding gives the report's date, the due date, the latest date, and the days after each.

**Not evaluated, and counted by reason on every page.** A report dated after its due date and on or
before the day after the latest date: *within the time an extension may cover; the register does not
decide whether one did, and lists the extension notices the Clerk's index shows at this seat.* A
document with no text, or no *Filing Type* line. Dates that disagree. A Member the roster records as
serving 60 days or fewer in the year.

**What every page says, whether or not the Signal fires.** The date of the Member's annual report,
linked to the Clerk's copy; every extension row the index lists at the seat, whether the register
attributes it or set it aside, with its printed New Due Date where the form carries text, marked as
listed by the Clerk and joined by the register; and, where the index lists no annual report the
register attributes to the Member, that sentence exactly, with the count of rows set aside at the seat
and a link to the Clerk's own search, never *did not file*.

**What this Signal does not say.** This Signal does not say the House Committee on Ethics found a
report late, assessed a fee or waived one: Oath reads none of the Committee's decisions, which is not
to say none exist. This Signal does not say anything about what a report discloses, or why a report
carries the date it does. This Signal does not say that a report inside the time an extension may
cover was covered by one, or was not. This Signal does not reach a Member who left before the
roster the register read, a candidate for the seat, or a Congress's second year: the 2026 reports
are due after the 119th Congress's terms end, and the adapter attributes no row of a closed Congress
by name. It does not rank, total or compare Members.

## The display join, which never decides a sentence

The page lists extension rows at the Member's seat, attributed or set aside, because a reader who
opens a report dated 13 August should see beside it the notice the Clerk lists, and a quiet page next
to a fired one should not read as favour. The list is labelled as the register's join of the Clerk's
rows, by seat and surname. No Finding rests on it, and nothing on the page says a report was covered.

## Timing

The Signal first publishes on the register's regular Monday cadence after the Council's reading of the
built Signal closes and the maintainer merges it, whatever the calendar. The general election falls on
3 November 2026; the rule, not the date, decides, and the Signal's page shows the day its definition
was merged. Holding it back for the election would be a timing choice too.

## Known-answer cases to write before any code

1. Due 15 May (a Friday); latest date 13 August. A report dated 13 August: within the window, not
   evaluated. 14 August: the day after, not evaluated. 15 August: fires, 92 days after the due date
   and 2 after the latest date.
2. 15 May on a Saturday, as in 2027: due Monday 17 May. 15 May plus 90 days is Friday 13 August and
   17 May plus 90 is Sunday 15 August, so the latest date is the later reading moved off the weekend,
   Monday 16 August; a report dated 17 August is the day after and not evaluated, 18 August fires.
3. A 90th day on a weekend, whatever the year: the next business day, never the Friday before.
4. A report dated 16 May with a set-aside extension at the seat: not evaluated, and the page lists
   the extension.
5. A report dated 20 September with no extension row anywhere: fires.
6. A report whose printed Filing Date differs from its index date: not evaluated.
7. A document coded `O` whose header says anything but *Annual Report*: not read.
8. A document coded `A` whose header says *Amendment Report*: not read.
9. A paper report with no text, dated after the latest date: not evaluated, counted.
10. A Member sworn in with 60 days or fewer of the year left: not evaluated.
11. No annual report attributed, and one set aside at the seat under the surname: the page says so,
    with the count and the Clerk's search, and never *did not file*.

## Threats to validity, in the order a careful reader would raise them

1. **The clock of the printed date.** Settled by `wt:the-filing-systems-clock` or by the one-day
   margin in criterion 5, which costs silence on the day after the latest date.
2. **A combat-zone extension**, which § 13103(g)(2) allows past 90 days and the register cannot see. The
   Finding says so.
3. **Reports on paper** carry no text and are not evaluated, so a Member whose report is on paper
   cannot be among those on which it fires.
4. **The window is wide.** In the build of 2026-09-22, 252 of 422 annual-coded rows fall inside it,
   and the Signal says nothing about any of them. That is the price of never firing on an extension
   the register did not hold.
5. **The index is live.** The 2025 archive grows through the next year. A report added after a build
   is read by the next one; a Finding already published is superseded, never removed, if the source
   moves.
6. **The documents do not last.** 5 U.S.C. § 13107(d) has a Member's reports destroyed six years after
   the Member leaves, so the register keeps the SHA-256 of every document whose header it reads, and
   every field it records, beside the field.

## What it needs before it ships

1. The adapter reads the header of every annual-coded and extension-coded document it fetches,
   attributed or set aside at a Member's seat, and records what each prints (*Filing Type*, *Status*,
   *Filing Year*, *Filing Date*, the signature date; on an extension, *Extension Length*, *Original Due
   Date*, *New Due Date*, *Request Date*) with the document's SHA-256, on the filing row. A schema
   change and a new build.
2. The Signal file in `docs/signals/`, both implementations sharing no code, the known-answer cases
   above, and the pages.
3. The Council's reading of the built Signal.
4. STANDARDS.md and SOURCES.md rows for the sources above, in the sealed build that first carries it.
