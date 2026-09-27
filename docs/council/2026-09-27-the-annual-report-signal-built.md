# Council reading: the annual-report Signal, built, with its pages

*Held 2026-09-27, on PR #70 at `57b8da4`: the Signal's definition (held in `docs/design/`), both
implementations, their known answers and the pages' voice for it. It was read over a scratch sealed
build made from the live Clerk index of that day, with every annual and extension header read.
Prompt blob `18ddca5a8f05b484d2a74ca1ba49a41d0299c549`. All seven seats, A to G, sat alone and cold;
Seat D sat twice, one pass for each side, and the side that went second at the first reading went
first. Every seat re-derived the counts from the rows, and they held on every surface: 399 annual
reports read by their headers, of which 151 were compared and on or before the original due date,
239 fell in the window, 3 on the day after the latest date, 1 had dates that disagree, and 5 were
after the latest date, by 5 members; the Signal attributes no annual report to 40 of the 439
officeholders. Five seats checked the five Findings against their documents: each document's SHA-256
matched its row, each header prints *Annual Report*, *Member* and filing year 2025, and the three dates
agree. No extension form the register read for a 2025 report prints a New Due Date after the latest
date. Names and document ids stayed with the maintainer; this record carries neither.*

## The findings several seats made

- **"Its due date" read as a deadline already missed (Seats A, B, D and F; blocking).** Seat F
  translated the pages into four languages of different families, and in every one *after its due
  date* came back as *overdue*. On 202 of the 239 pages in the window, the Clerk's own extension
  form listed below printed a New Due Date on or after the report's date. The Committee's own term
  is *original due date*. The Finding's *N days after its due date* overstated by the ninety days an
  extension may cover (Seat D). **Changed:** *the original due date* everywhere, in the Finding text,
  both implementations, the known answers, the pages and the key; the Finding no longer gives the
  days after the original due date, only the days after the latest date.
- **The extension list turned on spelling and on paper (Seats A, B and D; blocking).** Only notices
  both attributed and readable were listed, so of two pages with the same dates, one showed its
  extension and one did not, according to how the index spelled a given name or whether the form was
  on paper; the definition promised every notice at the seat. **Changed:** every row the index gives
  at the seat under the surname with the extension forms' code is listed, attributed or set aside,
  read or not, in the same words on every page, and the definition says what is shown.
- **Eight officeholders owed no report (Seats A, B, C, D, E and F).** The roster's swearing-in
  leaves them 60 days or fewer of 2025, for which § 13103(d) asks no annual report, and their pages
  said the Signal could not tell whether they filed one. **Changed:** their pages say so, from
  `sworn_at`, and the landing and the Signal page count them apart from the other 32.
- **One report's dates disagree, and the figure gave it a date (Seats A, E and F; blocking).** The
  index gives the report the day before the date it prints twice; the figure drew the index date as
  *the report's date* on the last day of the window. **Changed:** where the dates disagree, the page
  gives all three and draws no dot.
- **"Every … the same day" was false once (Seats A, B, C and D).** The dry run's SOURCES.md text,
  and the wanted register's clock row, said the three dates agree on every report read; one of 399
  does not. **Changed:** 398 of 399, and that report is recorded as the register's only evidence on
  the filing system's clock (`wt:the-filing-systems-clock`).

## The other blocking findings

- **A withdrawal would have given a false reason (Seat G).** After the outcomes took the house shape,
  the withdrawal's branch on the outcome's state never ran, so every withdrawal would have said a
  report was *not dated after the latest date*, whatever the reason. **Changed:** it reads the
  recorded reason; a test fails on the old code for each reason and passes on the new.
- **The seal's one sentence spoke of the annual Signal in the transaction Signal's words (Seat G).**
  It said *after the deadline the rule sets* and counted transaction reports as outside it.
  **Changed:** `tools/seal.py` has the annual Signal's own sentence.
- **An undated present tense (Seat G).** *The Clerk's own search lists what the Clerk holds* would
  mislead once 5 U.S.C. § 13107(d) has the reports destroyed. **Changed:** dated to the build, with
  the retention rule and the sentence that a later search may find none, whatever was filed.
- **The timing promise was not kept (Seats D and G).** The design promised the Signal's page would
  show the day its definition was merged; nothing did. **Changed:** the Signal's page names the day
  this reading closed, links this record and states the rule; the record page names a Signal's first
  definition among the reasons a build publishes; the design note says what is built.

## Advisory findings taken

The Finding and the pages qualify the latest date with *outside a combat zone* (C). The Signal
evaluates filing year 2025 only, whose instructions were read, and the known answers hold the
calendar for six filing years (G, C). For each officeholder and filing year it compares the earliest
annual report the index lists, and a later one is not evaluated (C). A header-only Signal's one row,
the report's date, is held to the register's row, and the render refuses where they differ (C). The
chart's columns stand clear of the axis, so the five after the latest date show on a phone (E). The
marks are named by how they look, not as *screened*, and *decide* has its object (F). The section
heading takes the Signal's own name (F). *The clock behind the printed date* is *the time zone*
(E, F). *Fired on it* is *a Finding rests on it* (F). The rule sentence names Delegates and the
Resident Commissioner (F). A report the index sets aside under a sitting member's surname is named
among what the Signal cannot see, on its page and in the definition's first paragraph of what it does
not say, where a fired page shows it (A, B). A document whose header was read is counted as read
(A). Documents never fetched are counted, and the fetch rule by code is stated (C). *1 were* (E, F),
the literal asterisks (C, E), `rebuild.py`'s *0 rows* (G, C), § 6103 read at the source and linked
(C, G), the chart's due-date tag taken from the data (C), a filing year explained (E), a link to the
report and the two lines a reader can check without a terminal (E), and the landing's opening lines
naming both deadlines (E).

## Advisory findings not taken, with why

- **A state token `read` for a header-only Signal (F).** An outcome's `state` means whether the
  register read the document, for both Signals; its schema says so, and a second token would split one
  meaning across two Signals. A row with `"evaluated": 0` is a read report whose one row was set aside
  with its reason, as a transaction report with every row set aside already is.
- **An outside witness for the five Finding documents and the Guide before publishing (G).** Owed for
  every Finding, not this Signal's alone: INVARIANTS §16's evidence bundle is the planned gate, and
  NEXT.md carries it. STANDARDS.md S.1 and SOURCES.md F.1 now say plainly that the register keeps
  each document's hash and not the document.
- **The timing rule in METHODOLOGY (D).** METHODOLOGY is sealed doctrine and changes with a sealed
  build; the rule rides the build that first carries the Signal, and until then the Signal's page and
  the design note state it.

## For the maintainer to decide

- **A report set aside by the name match (Seat A).** One e-filed document the index sets aside under
  a sitting member's surname prints *Annual Report*, *Member* and filing year 2025 and is dated 29
  days after the latest date; the index prints a seat that is not the roster's. It is on no page's
  result until the maintainer decides by hand, citing the evidence, whose it is. The Signal's page now
  says that such a row exists as a class.
- **A territory's seat coded two ways (Seat E).** The roster and the index give one Delegate's seat
  different codes, so a report the index lists there is set aside as a name no sitting member bears.
  An adapter alias is owed and is in NEXT.md; until then, that page says no annual report is
  attributed, which is true and incomplete.

## The reading's own weakest point

No seat could read the 71 documents without a text layer, 47 of them extension forms: whether any
grants more than 90 days is unknown, and under this Signal it decides nothing, because no extension
enters it. Translation was done by the seats themselves, not by an engine. The time zone of the
printed date is still not established; the one disagreeing report is evidence, not an answer.
