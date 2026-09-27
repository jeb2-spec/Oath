# Council reading: the annual-report Signal, first draft

*Held 2026-09-27, on `docs/design/the-annual-report-signal.md` as merged in PR #67 (main `6d0146f`).
Prompt blob `18ddca5a8f05b484d2a74ca1ba49a41d0299c549`. Read by all seven seats, A to G, each sitting
alone and cold. Every seat re-derived the draft's counts from the rows and the documents and printed
its derivation; the counts held. Names and document ids stayed with the maintainer, as the prompt
requires; this record carries neither.*

## The finding five seats made independently

**Blocking (A-1, B-1, C-1, D-1, E-1; G-1 on the same rows). The extension join sees only what the
adapter attributes, and the draft's promise that every doubt resolves to not firing did not hold.**
Of 422 annual-coded rows in the build of 2026-09-22, 260 are dated after 15 May 2026. 12 of those have
no extension row tied to their Member. For 8 of the 12, an extension row sits at the Member's own seat
under the Member's surname, set aside by the name match because the given names differ. Seven of the
eight are dated 81 to 90 days after 15 May, three on the last day of a 90-day extension. Seats B and
C each read one of those rows by eye: the Committee's own paper form, for that Member's annual report,
with the Committee's *Days granted* box filled in (30 on one, 90 on the other). The draft would have
said *after the deadline* about them, two thirds of its first Findings, and whether it did would have
turned on how a given name was spelled (failure modes 6 and 10).

**What changed.** The Signal no longer depends on the join. It fires only where a report is dated
after the latest date any extension the statute allows could reach, which no posting, name or chain
of notices can move. The join survives as display, labelled as the register's.

## The other blocking findings

- **Extensions are posted late (A-2, G-1).** Extension notices are indexed weeks after the due date
  (the index dates dozens in June and July). A build in that window would have fired on extensions not
  yet posted. Dissolved by the change above.
- **A chain of notices (F-3, B-2).** One filer holds a 60-day notice and then a 30-day notice; the
  printed *Extension Length* is an increment, and each form prints its own *New Due Date*. Holding one
  of the two, the draft fired on a report inside the other. Dissolved by the change above; the display
  shows the printed New Due Date, never a sum.
- **The weekend rule (C-3; A-3, B-2, E-5, G-5).** The Guide exempts only 90-day extension ends from the
  weekend roll; the draft applied that to every length. Dissolved: only the latest date matters now,
  and where the rules admit two readings of it the later one is taken.
- **Unreadable extensions (C-2).** For a document with no text only its code says it is an extension,
  and the draft refused to read codes. Dissolved: no extension decides a sentence.
- **A timing rule (D-4, advisory but taken as blocking).** A new sentence about nearly every Member,
  first published in October 2026, 37 days before a general election, with no rule saying why then.
  The draft now says: first publication on the regular cadence after the Council closes, whatever
  the calendar.
- **Translation (F-1, F-2).** *Beside that deadline* came back from Chinese as *outside this deadline*,
  a claim about every Member; *it does not say anything about what the report discloses* came back
  from Arabic as *he did not mention anything*, a Member hiding something. Rewritten: *compares the
  date … with the latest date*, and each sentence opens *This Signal does not say*, with *Oath reads
  none of the House Committee on Ethics' decisions, which is not to say none exist*.
- **A fourth silence (B-3, D-2, E-2, C-6, F-5).** 9 Members who served all of 2025 have no annual-coded
  row attributed; for 5, one is set aside under their surname. The draft named three kinds of quiet and
  not this one. Every page now says it exactly, with the count set aside and the Clerk's search, and
  never *did not file*.
- **The second year of a Congress (E-3).** The 2026 reports are due in May 2027, after the 119th
  Congress's terms end, and the adapter attributes no row of a closed Congress by name. The Signal
  reaches each Congress's first year only, and now says so in *does not say*.
- **Reproducibility (G-2, G-3, C-7).** A Finding resting on an absence could not be rebuilt once the
  live index moved, and 5 U.S.C. § 13107(d) destroys a Member's reports six years after they leave.
  The change above removes the absence; the adapter keeps the SHA-256 of every document whose header
  it reads, beside each field.

## Advisory findings taken

Delegates and the Resident Commissioner are in scope and said to be (F-4, § 13101). Every Standard is
linked (A-5, C-8, E-7, F-7). *On time* is not a page's phrase (D-3). The sample is replaced by the
build reading every header (G-4, D-6). *Filing year* and the other terms are explained where a page
uses them (E-6). The one-day edge: the time zone of the printed date is not established, so a report
dated the day after the latest date is not evaluated (B-6). Seats who left, and candidates, are named
as outside the Signal's reach (D-5, E-4). NEXT.md's stale lines and its one use of *late* are fixed
(B-5, B-6, C-9).

## Advisory findings not taken, with why

- **Recording the extension ids inside each Finding (G-2, C-7).** A Finding no longer rests on an
  extension, so nothing in it would be those ids' to support. The page lists them.

## The reading's own weakest point

No seat could read the paper extension forms except by eye, four of them in all, so that the eight
set-aside rows are those Members' own is shown for two and inferred for six. The change above does not
depend on it: under the new rule none of the eight is evaluated, whoever's they are.
