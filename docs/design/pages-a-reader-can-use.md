# The pages a reader can use

*Design note, 2026-09-27, after the seven-seat Council's four readings of S.1b (PR #40) and the
merge. It proposes no change to what the register holds, and no change to a Signal. It proposes
where a page puts what it already says, and one figure it does not yet draw. Nothing here ships
before the Council reads it: the sentence at the top of a person's page is the most sensitive
sentence this project can write.*

## 1. Abstract

Four Council readings asked whether every sentence on a page is true. None asked whether a person
who arrives with a question and thirty seconds gets an answer. Those are different tests, and the
second has never been run.

Measured on the pages this repository publishes at build `0005-house-2025`:

| What a reader meets | Measured |
| --- | --- |
| Officeholder pages where no Signal fired | 418, a median of **2,146 words** |
| Officeholder pages where one fired | 21, a median of **5,394 words** |
| The longest officeholder page | **35,616 words**, printing 1,429 transaction rows |
| Officeholders whose page prints more than 100 rows | 15 |
| The landing page | **5,553 words** |
| Words before the reader meets what the Signal found | 472 |
| Words before "Verify it", on a page of 19,825 | **9,196** |

The register's own discipline says *the practical thing at the end*. On a page of nineteen
thousand words there is no end a reader reaches. The paper's shape, which the README sets and the
pages inherit, puts method before result: correct for a paper a reader has chosen to study, wrong
for a door a reader arrives at.

## 2. What this proposes

Five changes, in the order a reader meets them.

### 2.1 The answer first, in one sentence, identical in shape for everyone

Every officeholder page opens, above the standards and below the frame, with what the register
read and what it found, in one sentence of fixed shape:

> The register read **20** of the **20** transaction reports the Clerk's 2025 index attributes to
> this officeholder. On **3** of them, the index dates the report after the deadline the STOCK Act
> rule sets from the dates the report prints.

And, unchanged in shape, where nothing fired:

> The register read **4** of the **4** transaction reports the Clerk's 2025 index attributes to
> this officeholder. On **none** of them does the index date the report after the deadline the
> STOCK Act rule sets from the dates the report prints.

And where it could not read:

> The register read **0** of the **2** transaction reports the Clerk's 2025 index attributes to
> this officeholder: both are scanned paper, whose dates are printed in a document the register
> does not read. It evaluated nothing here, which is a fact about the register, not about what was
> filed.

**The constraints this sentence must meet, which the Council will test:**

- **One shape, both ways.** The same clauses, in the same order, whether a Signal fired or not. A
  sentence that appears only on a page where something fired is a verdict by placement (COUNCIL
  §5, mode 6).
- **It names a condition and cites a standard.** It never uses *late*, *failed*, *violated*, or
  any word the lint forbids; the deadline is the rule's, and the dates are the report's own.
- **It counts the register's reading, not the person.** "Read 20 of 20" is a fact about coverage.
  It is the one number a reader needs before any other, and it is the number the register is
  answerable for.
- **It says nothing a later build could make false.** No present tense that floats: the index is
  named by the year, the read by its date in the line below.
- **It is followed, immediately, by the existing not-a-determination sentence.** The frame does
  not move: it stays in the header, above this, on every page (INVARIANTS §7).

A reader who stops after this sentence has not been misled. That is the test.

### 2.2 A quiet page is a short page

418 of 439 pages spend a median of 2,146 words, most of it the standards block that is identical
on every page, to say that nothing fired. The honest page should also be the brief one.

- The summary sentence, the record, and where to read it come first.
- *What this office requires* moves below the record, unchanged, still complete, still citing and
  linking every rule. It is reference, and reference belongs where a reader who wants it can find
  it, not in front of a reader who came for one fact.
- Nothing is removed from any page. The lints that count the frame, the citations and the absence
  of ranking must pass unchanged, and a test asserts each one on a quiet page and a fired page.

### 2.3 One figure per Finding: the dates on a line

A Finding is arithmetic on four dates: the transaction, the notice, the deadline the rule sets,
and the date the Clerk's index gives the report. The page states them in prose. For a reader who
thinks in pictures, and for one skimming on a phone, that arithmetic is currently invisible.

Draw it: a single horizontal rule, four marks, the span between the deadline and the filing date
shaded, inline SVG, no client JavaScript, legible at 360px, and legible in a screen reader through
its caption.

The caption carries what the figure shows **and what it does not**, as every figure here must:

> The four dates this Finding rests on, as the report prints them and the Clerk's index dates it.
> The figure shows a span of days. It does not show why the span is what it is, whether notice
> reached the filer when the report says, or anything the Committee on Ethics has determined.

This is the same move as the seals: the thing that means something and cannot be faked, rather
than the thing that is merely pretty. The figure is derived from the Finding's own rows, so it
regenerates byte for byte with them (RUBRIC gate 4).

### 2.4 The long pages become navigable

Fifteen officeholders' pages print more than a hundred rows; one prints 1,429. A page nobody can
traverse keeps its promise to nobody.

- Each report's rows sit inside a `<details>` element, summarised by the report's date, its row
  count and whether a Finding rests on it. HTML alone, no JavaScript, open to a screen reader,
  and every row still in the page's source and in the download.
- A report a Finding rests on is open by default. Nothing a reader needs to see is behind a click
  they must know to make.
- A short jump list at the top of the transactions section, by report date.

### 2.5 The practical thing where a reader reaches it

*Verify it* at word 9,196 is a rule we wrote and then broke with length. The verify line, the
build's mark and the citation a reader should use move into the page's head matter, beside the
seal that already sits there, and stay at the foot as well.

## 3. What this does not propose

- **No new claim about anyone.** Every number in the summary sentence is already on the page.
- **No change to a Signal**, its definition, its version, or any Finding. Findings stay byte for
  byte (INVARIANTS §11, §12).
- **No client JavaScript that changes what a page says** (ECOSYSTEM §1).
- **No ranking, no sorting by anything the register computes about a person** (INVARIANTS §13).
- **No page shorter by omission.** Everything now published stays published, on the same page.

## 4. Threats to validity, in the order a careful reader would raise them

1. **A summary sentence is a verdict with extra steps.** This is the real risk and the reason the
   Council must read it before it ships. The mitigations are the fixed shape, the coverage number
   first, the absence of any word the lint forbids, and the frame above it. The test that decides
   it: read the sentence as the officeholder it describes, then as their opponent. If the two
   readings differ in what the sentence asserts, it is wrong.
2. **A number at the top invites comparison between people.** No page will carry another person's
   number, no page will sort, and the index will not print these counts. The existing no-ranking
   lint covers the index and the Signal page; it should cover the officeholder pages too, and
   that is a gate to add with this work.
3. **`<details>` hides evidence.** A collapsed section is still in the source, the download and
   the seal. A Finding's own rows are never collapsed.
4. **Moving the standards down reads as demoting the standards.** They are the reason the register
   exists. The summary sentence cites the rule by name and links to it, so a reader meets the
   standard in the first sentence, in the only form a first sentence can carry.
5. **A figure can mislead by scale.** A span of nine days and a span of three hundred must not
   look alike, and a very long span must not dwarf the marks. The axis is days, stated in the
   caption, with the scale named.
6. **This adds surface to maintain.** Each of the five changes needs a test that fails without it,
   and the guard sweep must cover them, as the fourth reading's eleven unmeasured guards taught.

## 4a. A second reading of the built answer

*Added 2026-09-27. Two sessions built this note's proposals in parallel, without knowing of each
other: the one recorded in §7 below, which shipped on PR #42, and one that reached §2.2 to §2.5
separately and drafted §2.1 three times. PR #42's is the implementation, and it is better: the
answer's numbers come from the Signal's own run record rather than from a filing's extraction
field, it says the days and what decides them, and it carries the frame inside its own paragraph.
The parallel draft was dropped. What it contributes instead is a second seven-seat reading, of the
merged sentence and not of a proposal, convened on the pages as published, and the page fixes the
Council's fifth reading of S.1b found that PR #42 did not carry: the swearing-in named as the
officeholder's own rather than the Congress's, a row said to carry a given name rather than a
person said to have used one, a replaced file distinguished by whether its rows read otherwise, the
build named for the first correction of a line rather than the latest, and what a fingerprint does
and does not do.*

*The duplication is worth recording because it cost a working session. The lesson is the one the
memory already carries about the junction: two halves both working perfectly is exactly when nobody
notices. A session that is about to build something already on the course should read `origin/main`
first, not the branch it cut.*

## 5. The reading this needs before it ships

COUNCIL §2 requires an adversarial reading for any surface that names an officeholder in a new
way. A sentence that summarises a person at the top of their page is exactly that, and it is the
sharpest such surface the project has proposed. All seven seats read it, with these questions in
front:

- **Seat A**, the reader who wants to be fair: does the summary read the same for an ally and an
  opponent, on structurally identical records?
- **Seat B**, the subject and the private persons beside them: read the sentence back as the
  officeholder. Does it assert anything the record does not hold?
- **Seat C**, the reviewer's reviewer: does the summary's every number derive from the rows, and
  does the figure regenerate with them?
- **Seat D**, the partisans: is the sentence one you would screenshot as proof of bias, in either
  direction, and is the shape identical across the divide?
- **Seat E**, the constituent the averages leave out: can a person on a phone, in thirty seconds,
  get the answer they came for, and is the quiet page as clear as the fired one?
- **Seat F**, the reader beyond the border: does the sentence survive translation without becoming
  an accusation, and does the figure need words a translation will break?
- **Seat G**, the reader who comes later: can the summary and the figure be rebuilt from the
  sealed rows alone, years from now?

## 6. Sources

- The measurements in §1 were taken on the site this repository renders at build
  `0005-house-2025`, by counting the words a reader meets with style and markup removed. The
  script is in the session record; the counts reproduce from `python3 src/surfaces/render.py` at
  `29a17ed`, the commit before this design was built.
- [ECOSYSTEM.md](../../ECOSYSTEM.md) §1 for what a surface may do, §2 for the marks.
- [INVARIANTS.md](../../INVARIANTS.md) §7 the frame, §11 and §12 Findings unchanged, §13 no
  ranking.
- [COUNCIL.md](../../COUNCIL.md) §2 for when the Council must read, §5 for the failure modes.
- [RUBRIC.md](../../RUBRIC.md) gate 4, every Finding regenerates.

## 7. What was built, and what the Council changed

*Built on 2026-09-27, PR #42, at the maintainer's direction: pages are the canvas, the record is
what they rest on; show the record, simply, and do not trip over the process to get there.*

**On every officeholder's page**, in the order a reader meets it:

- **The answer**, under the frame: how many transaction reports the register read and checked
  against the STOCK Act deadline, then what the Clerk's index shows, by how many days, and, from
  the Findings' own rows, the two facts that decide them where they apply: a weekend or holiday
  deadline met by the next business day, and a notice date printed after the 45-day limit. Where
  nothing could be checked it says which silence it is. The result and the sentence that frames
  it are one paragraph, ending with *Presence in the register is not evidence of wrongdoing*, so
  no crop carries one without the other.
- **The reports as squares**: one per report in the order filed, dark where a Finding rests on
  it, light where it was checked and none is after the deadline, an outline where it was not
  checked; each links to its report.
- **The rule in one line**: 30 days from notice, 45 from the trade; the law requires trades
  reported and does not prohibit them.
- Then what the register can check, the signal and its Findings, each with **its dates on a
  line** (a ring marks the first business day after a weekend or holiday deadline, drawn on top,
  inside the scale), the filings, the transactions (a report of more than 25 rows folds unless a
  Finding rests on it), and the oath and the standards, whole.

**On the landing**, the same squares for the whole chamber, **the House at a glance**: 463
reports, 294 checked, 27 dated after the deadline, by 21 members, a click from the members in seat
order. No square names anyone. The full count of the record is one tap in, whole.

**What the Council changed.** Seven seats read the built pages (A to C as COUNCIL.md §3 defines
them; D to G provisionally, with §5's questions). The findings that changed the answer:

- *A count of reports ranked records backwards* (Seats A and B, blocking): three one-day Findings,
  two of them weekend deadlines met the next business day, read as more than one Finding of 197
  days. The answer now says the days and what decides them.
- *A number with no noun reads as days* (Seats A, B, D, E and F): "dates 3 after the deadline"
  now reads "dates 3 of the 14 reports checked after the deadline".
- *The frame could be cropped away* (Seat D, blocking): the result and its framing sentence are
  now one paragraph, with the frame inside it; "on time" left the page.
- *"Read 6 of 6", then blaming what it could read* (Seat E, blocking): the silence is now named
  where it is.
- *The ring hidden under the upright line, or past it* (Seats B and C, blocking): the scale now
  includes the next business day, and the ring is drawn on top.
- Advisories taken: the swearing-in date in the answer; set-aside reports on every branch; a
  withdrawn Finding said in the answer; one short spoken name for the figure; left-to-right under a
  right-to-left page; larger figure text; neutral jump labels, hidden in print; the seal's caption
  off a phone's first screen; the no-ranking gate reading every form a link to a person can take.

**What the sealed doctrine should say, at the next sealed build.** ECOSYSTEM.md §1.3 still draws
the page with the standards first, and §1.4 draws the landing without the glance. A build whose
proof exists does not move, and a page is not a reason to cut a build: the record's own next build
carries the amendment. Its text: the diagram and paragraph in PR #42's commit `02bdff4` (reverted
there, kept in the history for this purpose), with the answer's sentence shapes quoted so a change
to the wording moves the digest (Seat G), and §1.4 gaining *The House at a glance*. INVARIANTS §13's
gate line should say the gate reads every officeholder's page (Seat C); that is §17's to approve.

## 8. The second reading, of the pages as published

*2026-09-27, all seven seats, on `adc06f5` and the 439 pages it renders. The first reading read the
pages as they were built; this one read them as a stranger meets them. Every finding below was
reachable on a published page, and each seat verified its own numbers against the sealed rows. The
reports are in the session record.*

**What made the answer a claim it could not stand behind, and is fixed:**

- **Two integers side by side are a rate, and the reader divides them** (Seat A, blocking). The
  denominator was the reports the register *could compare*, which shrinks for reasons that are not
  about timeliness at all. So the officeholder whose whole condition was two trades one day past a
  deadline that fell on a weekend showed **1 of 1** — the largest figure on the site — while the one
  with 463 trades up to 165 days past showed **1 of 4**. The landing publishes the chamber's own
  rate of 9%, so the comparator was already in the reader's hand. The numerator now carries the size
  the record holds, the trades, and no two counts sit adjacent.
- **"No trade the rule reaches" asserted the statute's reach** (Seat B, blocking). On 17 pages not
  one skipped row was skipped on a ground about the rule: they were dated before the swearing-in the
  roster records, or the report marks them amended, or the transaction is dated after the report.
  The Signal's own criteria say a returning Member's earlier trades "were under the same rule". A
  sentence that flatters a person falsely is the same defect as one that condemns them falsely, and
  it was never the register's to say. It names its own reasons now.
- **The Clerk's name stood behind the register's own undecided matching** (Seat B, blocking). "No
  report in the Clerk's index is attributed to this officeholder", on a page where the index lists
  twelve reports at that seat under that surname which the register has simply not decided. The
  register attributes; the index lists.
- **"Checked" is not what the register did** (Seat F, blocking). In three of five languages its
  fluent equivalent is *audited*, *investigated* or *inspected for compliance*, which makes a quiet
  page a clearance and a fired page an adverse finding by an authority the register is not. The act
  is a comparison of two printed dates against a span the statute defines, and the page says so.
- **The answer's numbers could contradict each other** (Seat C, blocking). A `min()` clamped a
  discrepancy where an assertion belongs: a Finding resting on a report this build's run record
  marks unread made one paragraph assert that the register read none, compared one, found that one
  after the deadline, and could not read it. It refuses now, naming the two routes that resolve it.
- **A Signal's words did not move with its version** (Seats C and G, blocking). The table was keyed
  by slug alone, so a v2 would publish v1's account of the rule: INVARIANTS §11's silent
  redefinition, relocated into the sentence a reader actually meets. And a Signal with no words
  printed a bare firing count with no coverage and no standard, in a shape that differed according
  to whether it fired.
- **The year came from a default argument** (Seat G, blocking). A build with no run record published
  1,644 sentences about the Clerk's 2025 index with nothing behind them. The year is the answer's
  only durable anchor; it fails closed.
- **The paragraph fitted no phone** (Seat E, blocking). Eighty to a hundred and fifty words, of
  which forty were a sentence the reader met at word four, and on no page of 439 did it fit a first
  screen: a reader saw the coverage clause cut mid-sentence and nothing else. The result and its
  framing are two paragraphs now, adjacent and inseparable.
- Smaller, and each a sentence a person reads about themselves: the day span belongs to the trades,
  each with its own deadline, not to a report that has one filing date; the tenure context prints
  wherever it is true, not only where the page is quiet; the innocence clause says "made any trade
  the rule requires reported", because "anything to report" renders in Arabic as "anything to be
  reported on"; the framing sentence is in full ink rather than the page's fine print; the square
  that carries the reassuring answer measured 1.76:1 against the paper while the adverse one sat at
  15.69:1; and the strip of squares carries what it does not show, which every figure here must.

**What the landing gained.** *Where the record narrows*: four bars from the Clerk's index to a
signal firing, each with the number that survives and a plain sentence naming what did not. Every
other surface says what the register found; this one says what it could reach, which is the harder
half and the half nobody else publishes. And the state map moved above the glance, because a visitor
who arrived for one person could not reach it until word 301.

**What the reading found that is not fixed here**, each a design question rather than a wording one:

- A recorded correction moves a report in the rows and the answer does not move with it, because
  the counts come from the Signal's run record and nothing reconciles the two; a re-captured
  document would inflate them (Seat G). The renderer already refuses a ledger naming an
  officeholder with no page; this wants the same guard, one set comparison, and it is the next
  pass's first item.
- `producing_filings` has no `maxItems` and nine readers take `[0]` (Seat C).
- There is no schema for the signal run record, and one of the answer's four numbers is
  recoverable from nothing else (Seat G).
- "Scanned paper" is a property no sealed row records (Seats C and G): the register should record
  why a document was not read, on the row.
- No surface tells a subject how to dispute a fact (Seat B). BYLAWS §6 promises the route and the
  pages never name it.
- The answer is still four numbers where this reader holds two, and "transaction report" has no
  glossary entry (Seat E).
- The committed Council prompt defines three seats; four of the seven that read this are defined
  only in §5 above (Seats E and G). COUNCIL §8 makes the prompt's blob SHA the reproducibility
  guarantee, and a later reader holding it cannot reproduce four of these readings.
