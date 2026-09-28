# Next

The course for the operator arriving at this repository. Ordered so that the earliest sessions build the gates every later session will run against, and so that the first publicly checkable claim ships as soon as the pipeline that produces it can be trusted.

## The North Star

**One officeholder. One year. One signal, fired or not fired. Every claim traceable to a primary source. The build sealed. A stranger can reproduce it.**

That is the first shippable public artifact. Everything in Phase 1 and Phase 2 exists to make it possible; Phase 3 is that artifact; Phases 4 and 5 grow it.

Nothing before Phase 3 is worth showing the world, because until Phase 3 the pipeline cannot be trusted. And nothing after Phase 5 was worth building if Phases 1-4 were not real.

The register around that artifact holds the whole chamber from the start, per Phase 3 I.2. One page is the thing a stranger checks; it is not the thing the register covers.

## The shape of full coverage

Full coverage is a finite, small population. This is the most important strategic fact about Oath and it is worth stating before any phase. Counted from [SUBJECTS.md](SUBJECTS.md) §2:

| Group | People | Source family |
| --- | --- | --- |
| U.S. House, voting members and delegates | 441 | House Clerk (SOURCES F.1) |
| U.S. Senate | 100 | Senate eFD (F.2) |
| Federal executive, §2.2 plus President and Vice President | 37 | OGE 278e (F.3) |
| Governors | 50 | fifty state regimes |
| Lieutenant Governors, where separately elected | varies by state | fifty state regimes |
| **Total** | **about 650** | |

Three adapters reach nearly nine in ten of them. The House, the Senate, and OGE cover 578 people between them; the remaining fifty-odd cost one adapter per state. That ratio, and not editorial interest, is why coverage runs federal first and state last. Cost per officeholder covered is the ordering principle.

The second axis is depth, and it has a cliff in it:

- **The index layer.** Offices, officeholders, and the list of filings. Machine-readable at the source. No document parsing. Produces no Findings at all, because a filing index carries no transaction dates.
- **The document layer.** Transactions and holdings, which live inside the filings themselves. Bounded by extraction quality; older filings are scanned images (F.1). This is where the expense is, and where every Signal that needs a date lives.

Ship the index layer for a group before the document layer for that group. A register that lists every member of a chamber and fires nothing is complete, honest, and cheap, and it is the state the project should be comfortable sitting in.

## Obtaining the record

Coverage is a ladder of doors, and each door has a shape. The shape sets the order, because the cost of a source is the cost of its door, not the number of people behind it. Verified reachable on 2026-09-22 unless marked.

| Source | People | The door | Index layer | Document layer |
| --- | --- | --- | --- | --- |
| House Clerk, filing index (F.1) | 441 | bulk ZIP, no key | landed | PDF text; e-filed reports are text, older ones scanned |
| House Clerk, roster | 441 | XML, no key | landed | none needed |
| Senate roster (F.2) | 100 | XML, no key | one session | none needed |
| Senate eFD, filings (F.2) | 100 | search behind a use agreement and a captcha; no bulk | a human step, then two or three sessions | e-filed reports are HTML tables |
| FEC (F.4) | 541 | JSON API with a free key; bulk CSV | two or three sessions | structured; no extraction |
| OGE 278e (F.3) | 37 | search interface, PDF | two to four sessions, plus requests that take weeks | PDF |
| Governors and Lieutenant Governors | about 68 | fifty regimes | one to three sessions each; the best five first | varies by state |

Three rules for walking the ladder:

- **A door software cannot pass lawfully and mechanically is a human step, recorded.** The Senate's agreement gate and captcha are the first. A person accepts the agreement and exports the search; the adapter takes it from there, and the run record names the person and the session. Nothing here passes a captcha by machine, ever.
- **The document layer takes one dependency, deliberately.** The standard library reads no PDF. The document adapter declares one pure-Python reader (the candidate is `pypdf`, BSD licence, no compiled parts); the verifier stays standard library, because the reader touches the cache and never the sealed rows. It is the first dependency the project takes on and it is recorded as such.
- **Capture before extraction.** Every document the adapter reads is captured first, bytes and hash and headers, into an evidence bundle per [INVARIANTS.md §16](INVARIANTS.md) and [EVIDENCE.md](EVIDENCE.md), before anything is read out of it. Extraction confidence is recorded on the row.

Two doors that stand open and are deliberately not walked through:

- **Roll-call votes and bills.** The House (`clerk.house.gov/evs`) and the Senate (LIS `roll_call_votes`) publish every vote as XML, and GovInfo publishes bill status in bulk (F.8). They are the most machine-readable primary records in the federal government. They are not ingested, because no Standard in [STANDARDS.md](STANDARDS.md) makes a vote a condition, and a filing set beside a vote is the arrangement of facts that invites the reader to infer what the register will not state ([RELATED.md](RELATED.md) §5.4). Whether they enter is a Council question, not an adapter question.
- **Lobbying disclosure (F.5, F.6).** Filed by lobbyists and naming counterparties, whom [SUBJECTS.md](SUBJECTS.md) §3 excludes as subjects.

When, counted in sessions rather than dates, because a session is the unit this project is actually built in: House documents and the first Signal, three to five; the Senate roster, one, and the Senate filings, a human step and then two or three; the FEC, two or three; OGE, two to four plus the requests. The federal picture, which is nearly nine in ten of the population, is ten to sixteen sessions of work from the night this section was written. The states follow, five at a time.

The Signal library grows on its own axis and is not tied to coverage. Every Signal cites a Standard ([INVARIANTS.md](INVARIANTS.md) §2), so the library can only grow as far as [STANDARDS.md](STANDARDS.md) reaches. A condition with no standard behind it is not a Signal, whatever the arrangement of facts around it suggests.

## Standing gates for every session

Read on arrival, run on every push. These are the five vows of the [Charter](CHARTER.md) enforced as tooling. Any session that skips them has drifted before it started.

1. Read your memory. `.claude/memory/MEMORY.md`, then `where-we-are.md`, then `who-i-am-for-oath.md`, then `founding-of-oath.md`. If the deeper ground is configured (`OATH_DEEPER_GROUND`, which the doctor reads), read the identity files there from that repository's `origin/main`.
2. Read the [Charter](CHARTER.md). Five vows, short on purpose. If you cannot recall them, come back.
3. Read the [Rubric](RUBRIC.md) if the session touches Signals or Findings.
4. Read the [Invariants](INVARIANTS.md) if the session touches gates, or wants to (any change to CHARTER, RUBRIC, or INVARIANTS is highlighted by the meta-gate and requires the maintainer).

## Phase 0. Foundation (done, at the founding)

- Prospectus, standards, methodology, limitations, sources, schemas, architecture.
- Working stance and memory seed.
- Charter, Rubric, Invariants.
- License, PR template, gitignore.

Nothing to do in Phase 0. It is the state you arrive to.

## Phase 1. Plumbing green (goal: an empty build seals, verifies, and CI enforces the gates)

Ship this phase as: a green CI badge on the working branch, and a sealed empty build with the verifier passing.

- **T.1 Runtimes.** `package.json` (TypeScript 5, Node 20, Vitest, Biome), `pyproject.toml` (Python 3.11, Ruff, Pytest). Pin only what needs pinning. *Node 24 in CI since 2026-09-26: Vitest 5 needs Node 22.12 or later (`engines` in `package.json`), and Node 20 left support in April 2026.*
- **T.2 Verifier and tamper-test.** `tools/verify.py` computes the digest over the empty canonical serialisation, prints *OK*, and prints *Integrity is not accuracy.* `tools/tamper-test.py` alters a throwaway copy and requires FAIL. Both standard-library only.
- **T.3 Schema validator.** `tools/validate-schemas.py` walks `schemas/` and confirms each is valid JSON Schema draft-2020-12. Runs in CI.
- **T.4 Verdict-language lint.** `tools/lint-verdict-language.py` (Invariant §1). Ships with the initial blacklist and an empty allowlist. CI fails on any hit in Markdown or in `src/`.
- **T.5 CI workflow.** `.github/workflows/verify.yml` runs T.2, T.3, T.4 on every push and every pull request.
- **T.6 Session-start doctor.** `scripts/oath-doctor.mjs` (or `.py`). Reads back whether the memory chain is whole, whether all invariant gates are present and passing, and whether the branch tracks main. Modeled on the errata doctor.
- **T.7 Branch protection on main.** *Added 2026-09-26, with the first Signal.* Require verify.yml to pass and a review before a merge. The refresh and anchor pull requests already come through review; nothing yet stops a direct push. The maintainer's setting to change.
- **T.8 The actions' own runtime.** *Added 2026-09-26.* `actions/checkout@v4`, `setup-python@v5`, `setup-node@v4`, `upload-artifact@v4`, `configure-pages@v5`, `upload-pages-artifact@v3` and `deploy-pages@v4` run on Node 20, which the runners are retiring. Move each to the major that runs on Node 24 once its release notes are read at the source; GitHub's documentation is not reachable from the cloud sessions.
- **T.9 A published row kept byte for byte.** *Added and landed 2026-09-26, at the Council's reading of S.1b, which found that a register re-deriving its published rows let a change in its own reading pass as a change at the source, let the filer's own words in a row's notes change with only a warning, and gave a person no way to correct a row.* The adapter now writes every published row back byte for byte, a row only gains a fact it lacked, and `tools/check-removals.py` refuses every other edit but a person's correction that a change row names. A page shows when a row was first read; a later read that showed it otherwise is a note beside it. *Sharpened at the second reading the same day:* a change is recorded only where the source's own entry for the row changed, found in its bytes without the parser, so a change in the parsers can no longer pass as the Clerk's; and the gate honours a correction only where it names its kind, its reason, who decided and when, and primary-source evidence. *Sharpened again at the third reading:* an entry is weighed against the one the register last read for the row, not only the one it was first read from, so a change elsewhere in the entry cannot carry a later misreading through; rows a reader finds in the very bytes a report's rows were published from refuse until the maintainer's recorded decision says the report lists that many; and the register keeps no filed document.
### D.4 Doctrine catch-up

*Added 2026-09-26, widened the same day by the Council's reading of S.1b, and again by its fifth.* All of it is sealed doctrine or scope, so it changes through the process INVARIANTS §17 sets, with the maintainer's approval, in one sealed build:

- **§17's gate is landed and §17 still says *(planned)*.** `tools/highlight-charter-change.py` compares the five antidrift files with the published record, prints each file's digest where none changed, and where one did prints the diff under a highlighted notice and refuses the build unless a row of `data/doctrine-amendments.ndjson` names that file, the sections, the direction, the reason in the shape §17 asks for, the Council reading that read it (its prompt blob SHA, when, which seats) and the maintainer's approval. A row naming a file that did not change is refused too. The ledger has its own schema, is sealed with the build, and is under the §14 gate, so a recorded amendment never leaves the record. Marking §17 landed is itself an amendment of a watched file, so it is the gate's own first exercise and belongs in the sealed build that carries the Council amendment below.
- INVARIANTS.md still marks ten landed gates *(planned)*: those of §1, §2, §5, §7, §9, §10, §11, §12, §13 and §14; only §15, §16 and §17 are unbuilt, and §17's lands with the Council amendment. §14's gate text should say what the gate now does, the corrections it honours and why; §2's, that `validate-schemas.py` also checks the rows agree with one another; §16's scope should reach the captures a change row cites, which are not filings (the roster and index copies kept today under `data/captures/sha256/`, outside any rule).
- SUBJECTS.md is the rule a sealed build applies to who may appear, and the pages cite §1, yet it is not among the sealed doctrine (`tools/verify.py`), so a build does not fix the rule it was built under (the Council's second reading, Seat G). Seal it with the next re-seal; §1's own words about an office's term end need the same reconciliation as the office schema's.
- ECOSYSTEM §1.3 does not yet describe the page line, the seat note and the index section for a Member the roster no longer lists, or the change notes beside rows and Findings.
- ECOSYSTEM §1.4 describes a landing the code no longer renders. *Added 2026-09-27.* The landing is now the story in figures; the directory of seats is `seats.html` and the state of the record, the dispute route in full and the glossary are `record.html`, both one click from the foot. §1.4's own core ("two paragraphs, one call to action, one worked example"; the Charter, the example and the index each one click behind the door) is what the page finally is, and §1.2's URL plan already gave the index its own path, so the change moves toward the section and not away from it. Two sentences are now false: the tile map's tiles are "a door to that state's delegation in the roll below", and the roll is on another page; and "the state of the record" is listed as one of two things that "stand on the landing", and it does not. ECOSYSTEM.md is sealed, so this rides the next re-seal rather than superseding an anchored build for two sentences of description; the words to replace them with are *a door to that state's delegation in the directory* and *stand behind the landing*.
- BYLAWS §6 says a row the source removes is marked *withdrawn from source*. The register observes only that a later capture no longer lists a row, and does not know why, so the pages say that; the bylaw's words overclaim and should say what is observed.
- LIMITATIONS: the register reads no vote, decision or consequence, and a quiet page says nothing about them; no new filing enters for an officeholder after their term; the bytes of most captures are named by hash and not kept; a new build's time rests on its proof being completed. And from the second reading (Seat F): every way to check the record runs through services hosted in the United States (GitHub, the Clerk's site), which the register cannot promise are reachable from every country. The kept-copy question the second reading put to Seat B was answered at the third, and the code follows the answer: the register keeps no filed document, names a document the Clerk later serves as a different file by both files' hashes with the rows that read otherwise, and keeps only the hash of a filer's own text a correction replaces. §9 should say so, and say that a line a filer has the Clerk remove leaves the register's rows by a correction that keeps its hash alone, while the build that published the line still carries it, as every sealed build stays in the repository's history (the fourth reading, Seats B, E and G). That practice is the Council's decision and no sealed section states it, so the code and the pages cite the decision: **EVIDENCE §7 says the register *may* retain and redistribute a filing's bytes, its §3 to §5 and §11 promise the reader those bytes, and INVARIANTS §16 plans an evidence bundle "containing the captured bytes" for every filing.** Amending them names §16 under §17, which the Council's fourth reading (Seat G) asked be said plainly: the register holds no filing's bytes, and what rests on a document (a replaced file, a correction citing a report, a count of a report's rows) is checked by fingerprint against a copy the reader holds, not from the repository alone. Whether a filer's own text should also leave the history, which the seal, the anchors and the regeneration of a superseded Finding all rest on, is its own question beside the court-order route below (the fourth reading, Seat B).
- BYLAWS §6 promises a documented removal under a court order, and the removals gate (INVARIANTS §14) has no route for one: a row of its own naming the order, the docket and the path, which the gate honours, for a published row or a kept roster or index copy (the third reading, Seat B). Until it lands, a redaction of a filer's own text is the one removal the register can make, by correction.
- U.S. Const. amend. XX, section 1, which the closed year rests on, gets a row in STANDARDS or SOURCES with a link read at the source (congress.gov and archives.gov are not reachable from the cloud sessions). So does U.S. Const. Art. VI § 3, which the glossary's definition of the oath cites beside a linked statute and does not link (the fifth reading, Seat F).
- METHODOLOGY: the cadence (Mondays at 09:17 UTC) and the rule that a build publishes when a source changed, or when the maintainer publishes a correction, and the maintainer merges it, so no one can read timing into a publication (the fourth reading, Seat D: a correction publishes a build too, which the landing now says and the planned sentence denied); a written rule for when a new filing year enters the register; and whether the pages should carry the date a build was published beside the dates its sources were read (the second reading, Seat D).
- LIMITATIONS §9's last sentence says a filed line changes here only when the filer amends the report with the Clerk. `tools/correct.py --field asset` is a second way, and the page beside the link now says both, which is the honest state while §9 is sealed (the fifth reading, Seat F). §9 should name the correction route, say that it keeps a fingerprint of what the line carried and not the text, and say that the register cannot unpublish what it has sealed.
- SUBJECTS §1 enters no new filing for an officeholder after their term. A report that covers their time in office and is filed after it (the annual report for a final year, a termination report) is excluded by that text; the maintainer decides whether §1 means filed after, or covering a period after.
- **The Council's seats.** COUNCIL §3 says three seats convene on every session and names A, B and C; seven have read every pass since the fourth reading, and D, E, F and G are defined nowhere a later reader can find. COUNCIL §8 makes the committed prompt's blob SHA the reproducibility guarantee, so four of the seven readings that shaped this project cannot be reproduced. The seats earned their places by what they caught, which is the evidence the amendment should carry: D found the frame a crop leaves behind and the mark beside a Finding; E found the paragraph that fit no phone's first screen, the square at 1.64:1 and the seal speaking twice to a screen reader; F found *checked* translating as *audited*, the frame translating as a legal hedge, and a row's given name read as a person's; G found the scanned-paper claim, the year sourced from a default argument, and a Signal's words keyed without its version. COUNCIL.md is sealed doctrine and one of the five files the meta-invariant watches, so this lands as one sealed build with its amendment row, its own Council reading (§8 makes amendments to the Council's instrument Council-reviewed on purpose), and the maintainer's approval. The prompt and COUNCIL §3 move together or a session's recorded seats cannot be reproduced, and since the gate landed they cannot drift: it refuses an amendment whose recorded reading names a seat the prompt at that reading's blob SHA does not define. [docs/design/the-councils-seven-seats.md](docs/design/the-councils-seven-seats.md) sets the amendment out whole: the four seats in the shape §3 writes the three, each justified by the findings it actually made, the one extension Seat B's practice has already outgrown, the threats to validity, and the three things the amendment needs that are not an engineer's to supply (the maintainer's approval, its own Council reading, and a re-seal).
- The frame in translation (Seat F): engines render *not evidence of wrongdoing* as *not proof of offences*, which reads abroad as a legal hedge. A plain companion sentence, *Being listed here says nothing about whether this person did anything wrong*, is the maintainer's to weigh against Vow II's own words.

Ship gate for the phase: `oath-doctor` prints all-green on a clean clone, and CI is green on the branch.

### S.2 The next signal, and the one thing it waits on

*Added 2026-09-27.* The maintainer's recorded direction after P.1: pages as a large, well-sourced
anomaly detector for a citizen who needs help seeing the record, and the recommended next row is the
annual disclosure against its deadline (5 U.S.C. § 13103), which reaches every member and not only
those who trade. That direction is right and the register is closer to it than it looks, but it is
blocked on one specific, obtainable thing, and the block is worth writing down so the next session
does not build on an inference.

**What the register already holds.** 1,197 filing rows, every one with the date the Clerk's index
gives it. A deadline signal over an annual disclosure needs the filing date and the deadline, and not
the document's schedules, so the sealed rows would be enough.

**What it does not hold.** Which of those rows *are* annual disclosures. The index gives a one-letter
form code, and the register does not interpret it: `data/README.md` and the adapter's own README say
so, because the Clerk publishes the codes on the filing pages and not as a definition a reader can
cite. On the 2025 rows the codes come to 463 `P`, 422 `O`, 276 `X`, 24 `A`, 6 `C`, 3 `G` and 3 `H`,
and every non-`P` row is written `form_type: other`. Reading `A` as *annual report* is a plausible
inference and it is not in the primary record, so a signal resting on it would rest on a guess about
a form, published against named people. Twenty-four rows would also not be *every member*, which is
the whole reason the direction names this signal. *(Superseded 2026-09-27: `A` is the amendment, and
the annual reports are `O`, 422 rows against 441 seats; below.)*

**The one thing it waits on:** the Clerk's own definition of the form codes, read at its source and
entered in [SOURCES.md](SOURCES.md) with a row per code. Until then, a form-code signal is not
definable under Vow IV, and saying so is cheaper than discovering it after the Council reads it.
*(Settled 2026-09-27 without the legend, from the documents, as the next paragraph says.)*

**Read at the source, 2026-09-27, and the premise above was wrong in the way it feared.** The
Clerk publishes no legend for the codes, and the documents do not need one: each prints its own
*Filing Type*, *Filing Year* and *Filing Date* in its header. All 24 `A` documents that carry text
say *Amendment Report*; none is annual. 38 of 40 sampled `O` documents say *Annual Report* by a
Member, so the annual reports are under `O`, 422 rows against 441 seats, and **this Signal can
reach nearly every member**, which is the whole reason the direction named it. The Signal must
read each document's own *Filing Type* line and never the code (`wt:the-form-codes`).

**The standard, read at uscode.house.gov the same day.** 5 U.S.C. § 13103(d): a Member who
performs the duties of the office for more than 60 days in a calendar year files *on or before May
15 of the succeeding year*. § 13103(g)(1): extensions *shall not exceed 90 days* in total.
§ 13106(d)(1): the $200 fee falls on a report filed *more than 30 days after the later of* the due
date or *the last day of the filing extension period*. The Committee's 2025 Instruction Guide:
unlike a transaction report, an annual report whose deadline falls on a weekend or federal
holiday is due the next business day.

**What the Signal must do before it may say anything about a person, learnt from one header.**
A 2025 annual report sampled that day prints *Filing Date: 08/13/2026*, which is exactly 90 days
after 15 May 2026, and its posted extension prints a New Due Date of 13 August 2026. So
extension requests (the `X` documents, which print *Extension Length* and *Report Type Due*) are
joined to the report they extend before any row is evaluated, and a report whose extension the
register cannot read is not evaluated at all. The join is by officeholder, year and report type,
because an extension request carries no filing ID of the report it extends; that join is an
inference about a named person, and the Council reads it before the Signal ships.
*Superseded the same day by the Council's reading, below: the join could not see what the adapter
set aside, and no sentence now rests on it.*

**The Council read the draft the same day, all seven seats, and it changed shape**
([docs/council/2026-09-27-the-annual-report-draft.md](docs/council/2026-09-27-the-annual-report-draft.md)).
Five seats found independently that the extension join sees only what the adapter attributes: of 12
annual reports dated after 15 May with no extension tied to their Member, 8 have one at their own seat,
set aside by the name match, and two seats read those forms by eye and found the Committee's *Days
granted* box filled in. The first draft would have said *after the deadline* about them. The second
draft ([docs/design/the-annual-report-signal.md](docs/design/the-annual-report-signal.md)) fires only
where a report is dated after the latest date any extension the statute allows could reach, which is
true whatever the register holds; on the build of 2026-09-22 that is 5 of 422 annual-coded rows before
their headers are read, and 252 sit in the window it does not evaluate. The join is display only.

**Built, 2026-09-27, read by the Council, and held.** The adapter reads the headers (PR #69; from
the refresh of 2026-09-28). The Signal is built: [its definition](docs/design/annual-report-after-extension-limit.md),
held in `docs/design/` so the runner does not read it; both implementations, sharing no code and
agreeing on 17 known-answer cases and a calendar for six filing years; and the pages' own voice for
it. A second Signal was the first test of every shape written for the first, and each is met in the
house shape: a read report with one row, its date, compared or set aside with the reason. **The
Council read the built Signal and its pages the same day, all seven seats**
([record](docs/council/2026-09-27-the-annual-report-signal-built.md)), and every blocking finding is
folded in: *the original due date*, never *its due date*, which came back from translation as
overdue; every extension row at the seat listed alike, attributed or set aside, read or not; the eight
members sworn in with 60 days or fewer of 2025 told which quiet theirs is; no single date drawn where
the three disagree; a withdrawal that says its real reason; the seal's own sentence for the Signal;
the Clerk's search sentence dated. v1 evaluates filing year 2025 only, and the earliest annual report
per officeholder and year. On the dry run's build over the live index (399 annual reports read by
their headers): 151 on or before the original due date, 239 in the window, 3 the day after the latest
date, 1 whose dates disagree, and 5 after the latest date, by 5 members. **Next:** the definition moves
to `docs/signals/` with its sealed build and the rows STANDARDS.md S.1 and SOURCES.md F.1 carry for it
(written, read at the source 2026-09-27: § 13103(d), (f)(9), (g); § 13101; § 13106(d); § 13107(d),
which keeps a Member's reports until six years after they leave, not six years after filing; § 6103),
and it first publishes on the Monday after the Council closed. **The two items the Council left for the
maintainer were decided the same evening** on the maintainer's instruction, by recorded decisions
citing each document ([the record](docs/council/2026-09-27-the-annual-report-signal-built.md)): the
report set aside by the name match is the Member's and fires, which makes six Findings by six members
on the scratch build; the territory's report is the Delegate's and is compared on time. The decision
route now works where only the printed seat differs. An adapter alias for the territory's two seat
codes would let the document's own header settle such a row without a person; not built. *Read 2026-09-27:* the roster itself gives the alias. It codes the seat `AQ00` and gives the same member's state as `<state postal-code="AS">`, and it is the only one of the roster's seats whose code does not begin with its postal code; the 2025 index has one row at `AS00`, the report already decided. So the join can compare the index's seat with the roster's postal code and district, a rule the source states, and it waits until after the annual Signal lands so the landing publishes exactly what the Council read. An outside witness for every document a Finding rests on (INVARIANTS §16) is owed for
both Signals. *Measured from 2026-09-27, not yet recorded:* `tools/witness.py` asks the Internet Archive whether it holds each such document byte for byte, and observes without submitting; on its first run the Archive held 21 of the 27 byte for byte, none differed, and 6 could not be checked because the Archive's connections failed; whether the register should submit, record the witness in the sealed record, or link the copy is the Council's question, set out in [docs/design/an-outside-witness.md](docs/design/an-outside-witness.md).

**One sentence of the first Signal's own definition is now stale, and it stays until a version says
so.** `stock-act-ptr-after-deadline` v1 says *the register has not compared the index date with the
date signed on each report*. Since 2026-09-27 it has, on all 409 reports whose text it can read, and
they agree (`wt:the-clerks-filing-date`). The definition is frozen with the version by its hash, so
the sentence is not edited: v2 of that Signal says what was found, and v1 stays readable as it was.

**What can be done before that, and needs no network:** the signal's definition document and its
known-answer cases against the statute, if 5 U.S.C. § 13103 can be read at its source; the register's
own annual-report *header* read (24 rows carry `A` and their headers are captured), which would say
what the form itself calls itself and might settle the codes from the documents rather than from a
legend; and a decision about whether a signal that reaches 24 of 441 members should ship at all *(moot
2026-09-27: it reaches the annual reports, under `O`)*, since
a page that fires on a fifth of a chamber and is silent on the rest invites the reader to read the
silence as clearance, which is COUNCIL §5 mode 6 in a new shape.

### P.6 Slim the landing, at no cost to what it says

*Added 2026-09-27, from the maintainer reading the deployed pages: "I still think we need to slim it down, so it's less overwhelming, but not at the price of diluting the message or changing the tone."*

**Landed the same day, items 1 to 3.** The thirty words about who decides are said in full once, under the deadline figure, and every later result closes on the nine-word frame alone. *The House at a glance* is on `record.html`; the link to the members in seat order, the statute and *what a signal is* moved into the deadline section. The captions' shared caveats are one *how to read the figures* line before the first of them. Measured by one counter before and after (it counts the header and foot, so its totals run above the table below): visible words **2,320 → 2,046**, captions **489 → 389**, visual blocks **7 → 6**, page height on a phone **8,768px → 7,804px**. Less than the estimate below, for two reasons worth knowing: what only the glance carried moved with the reader rather than being cut, and **item 4 was not taken**. The narrows list is the landing's statement of its own limits, and the one place a reader sees that the rule's scope accounts for 1 set-aside trade and the register for the other 1,155; limits as their own section is CLAUDE.md's rule, so it stays on the front door. The figures below are the ones this was measured against.

The word count is no longer the problem. **2,197 words** is a third of what the page carried this morning. What is left is a different shape of heavy, and it measures:

| | |
| --- | --- |
| Visual blocks, back to back | **7** (the map, the strip, and five `<figure>`s) |
| Captions | **469 words, 21% of the page** |
| Four consecutive data sections | glance 335, notice 325, narrows 339, ends 360 = **1,359 words, 62% of the page** |

A reader meets four sections of about 330 words each, in a row, each with its own figure, caption and key. That run is the wall. None of them is bad and the fix is not to make any of them worse.

**The largest cut available costs nothing at all.** `EITHER_WAY` — forty words, *"This is not a ruling by anyone: what the deadline means for a filer is for the House Committee on Ethics to decide, and the register sees none of its decisions. Presence in the register is not evidence of wrongdoing."* — is printed **four times** on the landing, under the deadline figure, the glance, the notice clock and the ends figure. *"One report can list hundreds of trades"* appears twice.

Four repetitions do not make the point four times; they make the page sound like it is apologising, which is a change of tone nobody chose. But deleting them outright is not free either: the repetition exists because of Seat D's finding that a **crop** of one figure must not travel without the frame.

The second reading already settled the shape of that trade-off, in its own words: *the sentence that must never travel alone is the shortest one*. So the move is to keep the nine-word frame under each figure and say the thirty words about who decides **once**. Check the finding before acting on this paragraph rather than trusting it.

In order of value, and each to be weighed on its own:

1. **The frame, once in full.** Nine words under each figure, the thirty about who decides said once. ~120 words, and it removes three repetitions of a paragraph, which is worth more than the count.
2. **Move *The House at a glance* to `record.html`.** ~335 words and one figure. The deadline figure now answers *did they follow the rule* better than 463 squares do, and report-by-report detail is apparatus. **Check first:** the glance carries the only link to the Signal's own page and the *what a signal is, and what it does not say* panel; both must land somewhere a reader still meets.
3. **Captions to two sentences each**, with the standing caveats (it counts trades not people; a tall bar can be one report) said once in a short *how to read these figures* line rather than in every caption.
4. **The narrows list.** Four dense reasons under the figure; the figure plus a two-line caption on the landing, the reasons on `record.html`.

Taking 1 and 2 lands the page near **1,750 words and six visual blocks**; with 3, near **1,500 and six**. Those are checkable numbers, not a target to hit by cutting something load-bearing.

**What does not move, at any word count.** The two-population split of the 27 reports. The both-halves-or-neither bar and its guard. The empty second row of *Where the record ends* and the clause that says the emptiness is this register's and not the Committee's. Those three are the message; the slimming is everything around them.

### P.7 The record, drawn, not described

*Added and landed 2026-09-27, PR #73, from the maintainer: "we are still doing some describing of the record instead of illustrating the record and showing it back in powerful and meaningful ways."* Every officeholder page now opens its answer with **one drawing of the person's year**: each transaction report a row (its trades as dots on the dates it prints, its square on the date the index gives it, a line between), the days past a deadline a solid bar from the Finding's own evidence, the annual report beside its bracket, a document whose header the register could not read an outline where the index dates it, and what the register did not read outlined and said. One line of time for the whole build; the figure computes no deadline of its own. Who decides is said once, the links and the verify line sit under the sentences, long report tables and the glossary fold, and each Signal page opens with its rule drawn. Four seats read it ([record](docs/council/2026-09-27-the-year-figure.md)); four blocking findings, each fixed before merge, the first of them the lesson: a figure that draws a state from the run record must draw every state the run record holds, or it will say *in between* about a day the sentence above calls *the day after*.

### E.0 The wanted register, and the work of reading it

*Added 2026-09-27, at the maintainer's direction: keep a register of exactly what pieces of official information, public or not, would close the loop.*

[docs/wanted/wanted.ndjson](docs/wanted/wanted.ndjson) is that register: thirteen rows across the five parts of the loop, each with the question it answers, what the register can say without it, what it could say with it, who holds it, what it would join on, and what to read to settle it. [schemas/wanted.schema.json](schemas/wanted.schema.json) is its shape and [tools/check-wanted.py](tools/check-wanted.py) is its gate. It renders to `closing-the-loop.html`, linked from *Where the record ends*.

**The gate's central rule is the whole point.** A row may say a record is published, obtainable or not public **only when somebody here has read a candidate at its source**. Every other row says *unknown*, and twelve of thirteen do, because that is what is true from a session whose network policy reaches none of the relevant hosts. Believing a thing is public is not knowing it, and a list of absent records is the easiest document in this project to lie in: every row is about something nobody has seen, a confident sentence costs nothing to write, and no reader can check it. The *not public* claim is the one that would read as an accusation, and it needs a reading like any other. Two guards hold both rules.

**The work, then, is reading.** Every unverified row carries a `check` naming exactly what to read and where. None of it needs new code and all of it needs a session that can reach `ethics.house.gov`, `oce.house.gov`, `uscode.house.gov` and the federal dockets; from the cloud sessions all four return 000 through the agent proxy. In rough order of what it buys:

1. **`wt:the-clerks-filing-date`** first, and before any of the others, because it is the only row that could make a sentence already published here wrong about a person. The Clerk's index row carries eight fields and one date, and nothing says whether `FilingDate` is the day the member filed or the day the Clerk posted. All 27 Findings rest on it. *Read 2026-09-27, the first session whose network reached the hosts:* neither the Clerk's pages nor the Committee's 2025 Instruction Guide defines the field, and the reports answer it themselves. On all 409 of the 463 transaction reports whose text the register can read, the index date is the day the report's own last line says the filer digitally signed it, on the sealed bytes, and on none is it another day; every report a Finding rests on is among them. The 54 with no readable signature line carry no Finding, and the row stays open for them. `python tools/check-signed-dates.py` re-runs it. **No published sentence changes.**
2. **`wt:whether-foia-reaches-congress`**, because its answer decides whether the rest of the list is work or advocacy, and the page says which. *Read 2026-09-27:* 5 U.S.C. § 551(1) excludes "the Congress" from the definition § 552(f)(1) uses, so in the statute's own words a records request does not reach it; what the Committee releases of its own accord waits on a reading of the House's rules.
3. **`wt:the-fees-in-aggregate`** and **`wt:the-counts-by-stage`**, the two rows whose unit is `chamber-year`: they name nobody, so they are the cheapest things on the list to ask for and answer most of what a reader wants. *Read 2026-09-27:* the Office of Congressional Ethics is now the Office of Congressional Conduct, at conduct.house.gov, and publishes counts of its Board's actions every quarter, for all its matters, in a table the register has not yet read row by row; no count of fees has been found, and a text search of the Committee's 118th Congress summary found none, on an extraction too thin to call it silent.
4. **`wt:the-filers-own-amendment`**, which needs no source at all: 5 Amended and 2 Deleted rows are already in the sealed build and no page follows one back to the report it amends. LIMITATIONS 7 promises a superseded Finding where an amendment invalidates one, and no code does it yet.
5. The rest, in any order.

**Two open questions for the maintainer.** Whether `wanted.ndjson` should join the sealed set, so the list of what is missing becomes tamper-evident like every other row here — it is out today because a work list that re-seals on every addition costs a new build and a new anchor to admit the project does not know something, and that price would be paid in fewer admissions. And whether a row that has been read and found not to exist should close, or stay open marked *read, and there is none*, which is a different and more useful fact.

### E.1 The Committee's own record, the source the register does not read

*Added 2026-09-27, from the maintainer's reading of the landing: what happens after a report is dated late, and why does the trail go cold there?*

The register can follow a trade from the day it was made to the day the Clerk's index dates the report that carries it, and read that against the deadline. Then it stops. Everything after that point belongs to the House Committee on Ethics, and nothing the register reads says what the Committee did.

**What is sourced, and already in [STANDARDS.md](STANDARDS.md) S.2.** Past thirty days beyond the due date, the Committee's memorandum of 30 January 2023 sets a minimum fee of $200 a report; its filing-deadlines page says the fee may be waived in exceptional circumstances; and the Ethics in Government Act separately provides penalties for knowingly and willfully falsifying a report or failing to file one (5 U.S.C. § 13106). The register computes no fee for anyone.

**What this build can determine, and the landing now draws.** Of the 27 reports the Clerk's 2025 index dates after the deadline, 18 fall at or inside the thirtieth day past the report's own due date and 7 of those are one day past; 9 fall beyond it, at 91 to 197 days; and no report in this build falls between 28 days and 91. The two groups share no officeholder. That structure is arithmetic on sealed rows and needs no source the register does not have.

**What it cannot determine, and must not imply.** Whether a fee was assessed on any of these reports, whether one was waived, whether the Committee looked at all. The register holds zero rows about any of it, and *the register holds no row* is not *no record exists*. The difference between those two sentences is the whole discipline, and the landing's figure says which one it is.

**What an adapter would need before a row of it could enter the register.** In the order the questions arise:

1. **A primary source with a stable address.** The Committee publishes annual reports, and the Office of Congressional Ethics publishes referrals and reports the Committee did not extend review on. Neither was reachable from the cloud sessions (`ethics.house.gov` and `oce.house.gov` both return 000 through the agent proxy), so what either actually contains is unread here and must be read at the source before a word of it is written down.
2. **A row shape that can say nothing.** The common case will be *this report has no published outcome*, and that has to be a row the register can hold and a page can render, not an absence a reader fills in. The Signal's own `NOT_EVALUATED` states are the model.
3. **An identifier that joins.** A Committee document that names a Member and a period does not name a Filing ID. Joining an outcome to a report without one is an inference, and an inference published against a named person is the defect this project exists to prevent. If the join cannot be made from the documents, the register carries the outcome at the officeholder and never at the report.
4. **A rule for the asymmetry.** A published outcome is most likely to exist for the worst cases, so a register that carries outcomes where they exist and silence where they do not will show a pattern that is about publication and not about conduct. The page has to say that where it says anything, the same way the reach figure does today.
5. **SOURCES.md and STANDARDS.md rows,** each read at the source, before any of it ships.

**The honest interim, which is what shipped.** Draw the rule as the Committee publishes it, place the register's own rows against it, and draw the emptiness at the width of the part the register can see. Presence in that emptiness is not evidence of anything, and neither is absence from it.


## Phase 2. The decisions the adapter needs (goal: schema settled, identifier settled, empty register anchored)

Ship this phase as: schemas a stranger can read, an identifier convention that will survive contact with real data, and an anchored seal over a register that still holds nothing.

This phase used to hold the whole first Signal, because the Signal was going to be proven end to end against a hand-typed fictional officeholder before any real data arrived. The fiction is cut, set by the maintainer on 2026-09-22, and the reasoning sits in [fixtures/README.md](fixtures/README.md). Cutting it removed the reason for the Signal to come first: with no fictional rows flowing through anything, the Signal work proves one pure function correct, which is a unit test rather than a proof of the pipeline. What stays here is only what the adapter cannot start without.

- **D.1 Schema examples and walkthrough.** Enumerate the enums, add a worked example to each schema, expand `schemas/README.md` for a contributor arriving cold. Examples use reserved placeholders (`EXAMPLE`, `example.com`, per RFC 2606), which are visibly not a person. Replace the identifier examples in `schemas/README.md`, which currently name a sitting Senator and a real district.
- **D.3 Identifier scheme confirmed.** *Decided 2026-09-22 and written into `schemas/README.md`.* The founding draft put the district in the officeholder identifier; real data killed it within the hour, because two sitting members hold each other's former districts across the Clerk's own two files. The person key is the Biographical Directory identifier and carries no office; the office identifier carries the seat and the term.
- **S.4 Seal and anchor the empty register.** Into main. The build seals and anchors `data/` as it stands, which is empty. *On this date this register held nothing* is a true and checkable claim, and stamping it proves the anchoring chain works before one real row depends on it.

  *Overtaken 2026-09-22, when build `0001-house-2025` put the House into `data/` before this step ran. A stamp made now proves only that a digest existed by now, so the empty build can no longer be anchored in a way that says anything about the day it was empty. Proposed in its place, for the maintainer to decide: anchor the latest build when this step runs, and every build after it, so the chain is proven on a quiet build before a build carrying a Finding depends on it. One design question comes first. `data/meta.json` is sealed and carries the anchor state, so writing the state into it would move the digest the proof is over; errata keeps each proof beside its sealed file and the state in its ANCHORS ledger instead.*

  *Resolved 2026-09-26, the errata way. The anchor's state is never sealed: the seal records where a build's proof lives, the proof sits beside the build's manifest in `data/anchors/` (the manifest's SHA-256 is the digest, so the proof commits to the seal itself), and the table in [ANCHORS.md](ANCHORS.md) is generated from the proofs by `tools/anchor.py`, which CI runs as a gate. `0005-house-2025`, the first build carrying Findings, is the first stamped; its stamp was owed at the seal, because the calendars could not be reached from where it was sealed, and `anchor.yml` takes it on main. The refresh stamps every build after it as it seals it, whenever the refresh runs; [ANCHORS.md](ANCHORS.md) records what its schedule has actually done. Builds before `0005` are not stamped: a stamp made now would say nothing about the day they were published.*

Ship gate for the phase: every schema carries a worked example that validates against it; the identifier convention is decided and written down; `data/` is still empty, still verifies, and the empty build carries an OpenTimestamps proof. *(The last clause was overtaken with S.4; see the note there.)*

## Phase 3. The chamber, quiet, then the first Signal (goal: something a reader can use, then the first checkable claim)

Ship this phase as: every voting member of the House in the register, each filing they have made linked to the original document, and then the first Signal run against those real filings.

The phase has two movements and **the first one ships on its own**. A register that lists an entire chamber and links every disclosure to its primary document is useful to a reader before any Signal exists, because that record is already public without being reachable: it lives behind a search form that returns documents by an eight-digit identifier. Making it navigable, with a source URL and a retrieval timestamp on every row, is the first thing here that a citizen can use. The second movement adds the first checkable claim on top of it.

Most pages carry no Finding even after movement two. That is the phase working, not the phase unfinished.

### Movement one. The quiet chamber.

- **I.1a House FD adapter, index only.** *Landed 2026-09-22; see `src/adapters/house-fd/README.md`. From 2026-09-23 a held row at a member's own seat is settled by the document's own header, and only what the document cannot settle waits on a person.* `src/adapters/house-fd/`. The annual bulk ZIP: offices, officeholders, and the filings index. One fetch, one format, no document parsing. Rate-limited. Respects the source's terms. Writes rows to the canonical NDJSON; rejects rows to `data/rejected/`. This lands a register with every voting member in it and no Findings at all, because the index carries no transaction dates. Ship it in that state; the silent register is the cheapest honest proof the Charter's third vow is real.
- **I.2 The whole chamber, one calendar year.** Every voting member of the current House, from the pool defined in [SUBJECTS.md](SUBJECTS.md). No person is chosen to go first and no person is the focus. Set by the maintainer on 2026-09-22: everyone in scope is treated equally, and the weighting that decides who is in the register at all is the weighting already in SUBJECTS.md §7, which is the office's impact, its responsibilities, and the public sworn commitment that comes with it. The scope is weighted by office. The people inside it are not weighted against each other, ever; that is [INVARIANTS.md §13](INVARIANTS.md).

  Ingesting everyone is also the cheaper path and the more defensible one. One source, one file, no selection to justify. The earlier recommendation here was the maintainer's own Representative and both Senators; it is withdrawn, because two thirds of that cohort sit behind the Senate's agreement gate and captcha (SOURCES.md F.2) and because any three-person cohort invites the question of why those three.

  **The pressure this creates, named in advance.** With a whole chamber ingested, the first question anyone asks is who has the most of something. The register does not answer that. No index sorted by a per-person count, no league table, no "top" anything. Findings are grouped by Signal, never ranked by person, per INVARIANTS.md §13 and METHODOLOGY.md §10.
- **I.3b The two rendering gates.** *Landed 2026-09-22; CI renders and runs both.* `tools/lint-frame-presence.py` (§7) and `tools/lint-no-ranking.py` (§13). Both are rendering-time invariants, and both are unbuilt, so nothing currently stops a page without the frame or an index sorted by a per-person count from shipping. They land with the first template rather than after it, so that by the time a Finding exists every surface that could mishandle it is already gated.
- **I.4 The per-officeholder page template.** *Landed 2026-09-22 as `src/surfaces/render.py`, standard library, no client script; the mark (I.5) landed the same day. From 2026-09-23 the page lists what each transaction report the register read lists, as filed and grouped by report; a surface of that kind goes to the Council before it publishes, and this one did.* The frame in the header (Invariant §7). The Findings listed with their standards, grouped by signal not by severity (Invariant §13 and METHODOLOGY §10). The filings listed with their source URLs. The rubric visible in a sidebar. The verifier command visible at the foot.
- **I.5 The mark generator.** *Landed 2026-09-22 as `tools/strike-mark.py` and `tools/check-mark.py`; every rendered page carries its seal inline.* `tools/strike-mark.mjs` was the founding's recommended path. Strikes a wax-seal-in-guilloche mark from the officeholder id and the build digest, per ECOSYSTEM.md §2. `tools/check-mark.mjs` verifies the geometry stays legible across a range of digests. Each per-officeholder page carries its own struck seal.
- **I.5b The index of everyone, quiet.** *Landed 2026-09-22; 439 pages, 46 of them with no filing, each saying so and pointing at the source.* A page listing every officeholder the register holds, in a fixed order that is not a ranking (INVARIANTS §13), most of them with nothing to show. Built privately; the repository went public on 2026-09-26, the maintainer's call (Phase 5). This is the earliest point the project becomes a thing the maintainer can look at, and it exercises both rendering gates against real names before any Finding exists.

### Movement two. The first Signal, against real filings.

- **D.2 Known-answer cases.** *Landed 2026-09-26: thirty-six cases, ten of them added at the Council's reading.* `fixtures/stock-act-ptr-after-deadline/`. Dates and amounts with the correct answer written beside each, and no person in them: a transaction reported on day forty-five and one on day forty-six; the rule's two prongs (thirty days from notification, forty-five from the transaction, whichever falls earlier) crossing each other; a missing notification date; a date that does not parse. These are test inputs. They never enter `data/`.
- **S.1 First Signal definition.** *Landed 2026-09-26 as `sg:stock-act-ptr-after-deadline:v1`, drafted as `stock-act-late-ptr` and renamed at the Council's reading before anything was published, because whether a report was late is the Committee on Ethics' to decide. It evaluates only the rows the rule plainly reaches (marked New; stocks, corporate bonds, options and cryptocurrency by the Clerk's codes; over $1,000; on or after this Congress's swearing-in; a deadline from 2025), and counts every other row with its reason.* `docs/signals/stock-act-ptr-after-deadline.md`. Standard: STANDARDS.md §S.2 (STOCK Act). Criterion: a Periodic Transaction Report filed later than the rule allows, stated as both prongs rather than the forty-five-day prong alone. Worked example against the D.2 cases. `not_saying` filled in.
- **S.2 Reference implementation.** *Landed 2026-09-26. The Python writes the Findings, one writer in the seal's language; the TypeScript shares no code with it and agrees with it on every case and every row of the register, byte for byte. The Signal's row carries the SHA-256 of both, so the code is frozen with the version.* `src/signals/stock-act-ptr-after-deadline.ts`. A pure function over dates. Tests assert each boundary case, including the day the answer changes and the prong that binds first.
- **S.3 Adversarial review.** *Done 2026-09-26: three seats, one pass, recorded on PR #38, every blocking finding acted on before merge.* A fresh AI session with the council prompt, or a human, takes a hostile pass at the Signal against the five failure modes. Findings recorded in the PR. Merge only after.
- **I.1b House FD adapter, filing extraction.** *Transaction reports landed 2026-09-23: piloted on North Carolina, then run on the chamber; 409 of 463 read by the position of every fragment on the page, 54 scanned and not read, 7,346 transactions in the register and on each officeholder's page as filed (I.4), read by the Council before they published. Annual reports still to come.* Transaction rows from the Periodic Transaction Report documents, which is where the transaction date required by `transaction.schema.json` actually lives. Per [SOURCES.md](SOURCES.md) F.1, older filings are scanned images and extraction is bounded by their quality; a filing the adapter cannot read with confidence is rejected, never guessed. This is the hard half of the adapter and it is deliberately behind a shipped I.1a.
- **I.3 First Findings.** *Landed 2026-09-26 as build `0005-house-2025`: 27 Findings, on reports attributed to 21 officeholders; the stamp owed at the seal, for `anchor.yml` to take on main.* Run the S.1 Signal against the ingested data. Sealed build. Anchor stamped.

What the first Signal carries forward, in the order it bites:

- **S.1b The roster must not move a published Finding.** *Landed 2026-09-26, before the first scheduled refresh with the Signal in it, and reworked three times on the seven-seat Council's readings. The second found that the seal refused the very departure and closed year S.1b exists for, while 277 tests passed, because the seal's tests built run records the adapter does not write; that a change in the parsers could still be recorded as the Clerk's; and that moving an attribution left its trades behind. The seal now states the register's totals and a closed year's own figures and stamps a change only once sealed; the adapter records a change only where the source's own entry for the row changed; an attribution moves whole; and three tests run the adapter, the seal and the validator on one tree: a departure, a closed year after one, and a seal that refuses. The published register is an input to every build, and every published row is written back byte for byte. What a later capture shows otherwise is a row of its own in `data/changes.ndjson` (not listed, listed again, read otherwise, replaced), citing a capture whose bytes the register keeps; a fact moves only by a person's correction (`tools/correct.py`); the join never moves a published attribution; the bytes a row was read from reading otherwise refuse the build, because the source did not change. A filing year is built only against its own Congress's roster, and once the roster lists a later one the register closes the year: rows carried, set-aside reasons kept, offices given the day their terms ended. `tools/check-removals.py`, the §14 gate planned since the founding, holds every build to it. The pages name the Congress with its terms; a departed Member keeps a page that says the roster gives no reason and no date, a note at their seat, and a place below the seats; a change is a note beside the row and beside any Finding on its report. The third reading found the departed Member's page telling a false story about rows set aside while they sat, a correction invisible on the page it moved a row from, a reader's new rows publishable as filed, a kept copy of a filed document that would outlast the Clerk's redaction, and guards no test measured. Each is fixed. The fourth reading then removed the guards again and found eleven that no test caught, nine of them this change's own, so the earlier count stood for a measurement it had not made; each was given a failing input. *The fifth reading found twelve more that no test caught, three of them among the eleven the fourth had named, and one a guard this repository had measured before and stopped measuring when another rule began catching its input first: a sweep run by hand and a number written into a commit message is a claim about the past. So the claim is a command now. `tools/guards.ndjson` lists each guard, why it exists, how to remove it and which tests should catch it; `tools/measure-guards.py` removes each one and reports, in about four seconds, whether the tests it names refuse the tree; both run in CI and in the doctor. Thirty-nine guards are listed and every one is measured: removed on its own against a passing baseline, each failing a test it names. *(The claim as it stood on 2026-09-27 read "seventeen guards are listed", and the sixth measurement, run against the merged tree, found that eight of the thirty-one then listed were not measurements at all. pytest exits non-zero for a usage error, for an interrupted run and for a run that collected no test, and the runner read every non-zero exit as the guard being caught; six guards named tests that a merge had dropped and all six reported measured. A second defect made the result depend on the order of the run, because a .pyc header records its source's mtime to the second and the sweep rewrites one file several times a second. Both are fixed, both fixes are themselves guards, and `tools/test_measure_guards.py` now holds twelve cases, one for each way the runner could lie. Section 9.3 of [the pages design note](docs/design/pages-a-reader-can-use.md) records it. The count above is the count the command prints; run it rather than trusting this sentence.)* The fourth reading's own three blocking findings are fixed: a decision's own mark lost when its document was read, a correction that stopped every later build, and a page that told a private person the register keeps no copy of text its own history carries.* The adapter reads the roster of the sitting Congress, for attribution and for the swearing-in date the Signal bounds a transaction by. When a Member with a Finding leaves office, their reports stop being attributed; when a new Congress convenes, the roster's swearing-in date moves to its own, which puts every earlier transaction before it. Either way the next run refuses, by design, because a published Finding keeps its page (INVARIANTS §14): the refresh fails and opens an issue rather than drop the Finding. Before then the register must keep each Congress's rows, a departed Member's included, and hold each filing year's swearing-in dates fixed. It can happen any week a Member resigns; on 3 January 2027, when the 120th Congress convenes, it certainly happens.
- **S.1c The signed date.** Nine of the 27 Findings turn on one or two days. Read the date signed on each e-filed report and set it beside the date the Clerk's index gives it, and learn in which time zone the index keeps its date. The Signal page and each Finding's table already say where a Finding turns on a day or two.
- **S.1d Government securities, at the source.** 441 rows are coded `GS` and counted, not evaluated, because the register has not read, at the source, where the Committee's instructions put them. The Committee's site is not reachable from the cloud sessions; this is a read for the maintainer's machine.
- **S.1e Earlier indexes and service dates.** Read the Clerk's earlier indexes and the Biographical Directory's service dates, so a later version can evaluate a returning Member's transactions dated before this Congress's swearing-in (469 rows, on the reports of 28 officeholders), and judge a deadline before 2025 by the instructions of its own year.
- **S.1g A closed year's later filings.** *Added 2026-09-26 at the Council's reading of S.1b.* Once the roster lists the 120th Congress, a row new to the 2025 or 2026 index is set aside with the closed-year reason, and only a person's cited decision attributes it, within SUBJECTS §1. The Clerk's indexes keep growing after their year (the 2025 index lists reports it dates in 2026), so the register needs a way to attribute them against the year's own Congress: the last roster of that Congress it read, kept by its hash, or the officeholder rows it published from that roster. Before the first 2027 annual reports are filed.
- **S.1h When a Member left, from a primary source.** *Added 2026-09-26 at the Council's second reading (Seat A).* The register cannot show a Member in office after the last roster read the register built from that listed them, so a report dated between that read and the day they left cannot enter while the roster does not list them, and the gap is a week or more: a refresh that reads the same bytes, fails, or is not merged records no read, so the gap runs from the last build, not the last read, and falls differently for each departure (the third reading, Seats B, D, E, F and G). A cited primary source for the day a Member left (the Clerk's record of a vacancy, the House Journal) could extend the day, as a correction row the adapter honours. Until then the page names the day and says what cannot enter. With it: whether the Clerk's header prints a former Member's name in a short form ("Hon. Example"), which would let a successor of the same surname at the same seat take the report, is unchecked (Seat C, C-13), and needs the form read on the maintainer's machine.
- **S.1i Every roster read, kept.** *Added 2026-09-26 at the Council's second reading (Seat G).* The register keeps the roster that shows a change and the roster that closed a year, not the read before a change, so a later reader can check that a Member is absent but not, from the source's bytes, that the read before listed them; the page says so. Keeping every distinct roster read would close it; its size (the roster carries committee assignments and changes often) is to be measured on the maintainer's machine before deciding.
- **S.1j Each fact's own bytes.** *Added 2026-09-26 at the Council's third reading of S.1b (Seats C, F and G).* The guard weighs a row's whole entry against the one the register last read, so a change in the register's reading passes as the Clerk's only in the very build in which the row's own entry also changed, in a part the register does not read, and no row with an unchanged entry reads otherwise. Hashing each fact's own element (the official name, the name list, the party, the sworn date; the filing date, the filing type) would close that too, as a field a published row gains.
- **S.1k A change row the register wrote in error.** *Added at the third reading (Seat B, N9).* A change row never changes, and `tools/correct.py` corrects the register's own rows, not change rows; a read the register misrecorded despite every guard (a source served broken, then fixed) has no row that says so. A `corrected` row about a change row, which the page shows beside it, would give it one. More than ten rows recorded as no longer listed from one read now refuse until the maintainer confirms the count, which narrows it.
- **S.1l A superseded Finding, regenerated.** *Added at the third reading (Seat C, N-6).* `tools/rebuild.py <id>` regenerates a Finding from the rows it names as they now stand, so a Finding superseded because a correction moved its report no longer regenerates from today's rows; it does from the commit that sealed it. The tool should say so for a superseded row, and METHODOLOGY 7.4 should say which rows a superseded Finding regenerates from (D.4).
- **S.1f A Member's rows across Congresses.** A build of a filing year in the 120th Congress (2027 on) will need a returning Member's row to gain the new term without losing the old: an office row per term, and the swearing-in date belonging to the term, not the person. The Signal reads `sworn_at`, one date per officeholder, so a date per term is a new version of the Signal, with a Council reading. Until then the register is the 119th Congress's, and S.1b keeps it whole when the roster moves on.

- **I.6 The colophon.** Every build emits a sealed record of how it was made: the gates that ran and their results, the adapter and Signal versions, the Council sessions linked, the corrections and supersessions counted, the contributor roles (human, co-authored, assistant), the digest, and the anchor state. One line of it prints on every page beside the verifier command, and the build mark's ring counts it. It states what was done and never claims quality; a struck count is record, a badge is reputation. Set on the course by the maintainer on 2026-09-21 as the exhaust of the pipeline made into record. A design pass precedes the build.

Ship gate for movement one: every voting member in the register; the index page and one per-officeholder page render in both themes; both rendering gates pass; every filing row carries a source URL and a retrieval timestamp; the verifier passes on the sealed build.

Ship gate for the phase: an anchored sealed build carrying at least one Finding; the reader can click from any claim to its primary source; the per-officeholder seal reproduces byte-identically from the same inputs.

## Phase 4. Coverage extend and second signal (goal: prove the extensibility is real)

Ship this phase as: the first cross-signal officeholder profile.

- **I.5 Full current House PTR set.** Extend I.1 to ingest the current session's PTRs across the whole House. *Half unblocked 2026-09-26: the adapter scopes a build to its filing year by the index year the Clerk's own document URL names, so a build of the 2026 index leaves the 2025 rows untouched. It is not yet enough. `tools/seal.py` now seals a tree with a run record per year, and `src/surfaces/render.py` still reads one per adapter and stops at two (the Council's third reading of S.1b, Seat C, C-6), so it must read one per year first; until then the register covers the 2025 index. The 2026 index is the 119th Congress's too, so once they do, the refresh builds it as it builds 2025.*
- **S.5 Second Signal candidate.** Proposed: `undisclosed-asset-in-ptr`. A PTR-reported asset that does not appear on the officeholder's most recent annual FD, per Ethics in Government Act §S.1. Purely mechanical, no interpretation. High signal-to-noise. Uncontroversial as a first extension.
- **S.6 Second-source adapter.** Depending on which second Signal ships, an adapter for OGE 278e (F.3) or Senate FDR (F.2) may be needed. Do the smaller of the two first.

Ship gate for the phase: at least one officeholder page renders two different Signals in the register, each cited to its distinct Standard.

## Phase 5. Public flip and the website (goal: the world can read it)

- The maintainer flips the repository to public. *Done 2026-09-26, ahead of Phase 4, by the maintainer's call. The rendered site had been public since 2026-09-23, after the Council's first reading of the per-officeholder pages (PR #27).*
- Static site scaffolded per ECOSYSTEM.md §1: Astro or 11ty, edge-cached, no client JS that changes what a page says.
- URL structure per ECOSYSTEM.md §1.2. Landing, Charter, Rubric, Invariants, Bylaws, Council, Officeholders index, per-officeholder pages, Signals index, per-signal pages, Verify page, Anchors ledger, Corrections trail, About.
- The build mark and per-officeholder seals rendered per ECOSYSTEM.md §2.
- The download endpoint at `oath.<domain>/download/<build>.zip` ships the NDJSON, the seal, and the anchor proof.
- The `ANCHORS.md` ledger publishes every build's state.
- The consumer contract in ECOSYSTEM.md §3 published on the site.

- **P.1 The pages a reader can use.** *Added 2026-09-27, after the seven-seat Council's four readings of S.1b and its merge. Built the same day on PR #42, read by all seven seats, and published on build `0005-house-2025`; what was built, what the Council changed, and the ECOSYSTEM §1.3 and §1.4 amendment owed to the next sealed build are in the last section of [the design note](docs/design/pages-a-reader-can-use.md).* Four readings asked whether every sentence on a page is true; none asked whether a person who arrives with a question and thirty seconds gets an answer. Measured at build `0005-house-2025`: 418 pages spend a median of 2,146 words to say that no Signal fired; the 21 where one fired run to a median of 5,394 and a maximum of 35,616, one of them printing 1,429 transaction rows; the landing is 5,553; and *Verify it*, which this project's own discipline puts at the end of every entry, sits at word 9,196 on a page of 19,825. The design is in [docs/design/pages-a-reader-can-use.md](docs/design/pages-a-reader-can-use.md): the answer first in one sentence of fixed shape, identical whether a Signal fired or not; a quiet page that is short; one figure per Finding showing the four dates it rests on, with the caption saying what it does not show; the long pages navigable without JavaScript; and the practical thing where a reader reaches it. It proposes no new claim about anyone and no change to any Signal or Finding. A summary sentence at the top of a person's page is the sharpest subject-naming surface this project has proposed, so it ships only after all seven seats read it, on the questions §5 of that note sets. Two gates land with it: the no-ranking lint extended to the officeholder pages, and a test per change that fails without it. *All five landed on PR #42, and a second seven-seat reading of the published pages on 2026-09-27 found eight blocking defects in the answer, every one reachable on a real page; they are fixed, and the landing gained* Where the record narrows*, the one figure that says what the register could reach rather than what it found. Six findings the reading left open are design questions rather than wordings, and [the design note](docs/design/pages-a-reader-can-use.md) lists them in its last section; the first is that a recorded correction moves a report in the rows and the answer does not move with it, because its counts come from the Signal's run record and nothing reconciles the two. That first item is now fixed: `answer_rests_on_these_rows` compares every Signal's run record with the register's rows before a page is written and refuses where they disagree, because the defect was worse than the reading's summary of it (the page the correction moved a report away from carried the adverse sentence, with no such report among its rows). A third pass the same day merged the parallel session's comic layer, notice clock and impossible-dates rows, re-applied every page fix onto them, and found that the register asserted a physical fact about 54 filed documents that no row and no run record holds: nine surfaces called a document the register could not read "scanned paper", where what it records is that the text it extracted carried no Filing ID line and no State/District line. All nine now say what it looked for and did not find. Sections 9.1 to 9.3 of that note carry the figure, the three defects its own first draft shipped, and the measurement that was not one.*

No ship gate; this is Jared's call. All Phase 4 gates must be green, and the Council convenes before public flip to review the site's per-officeholder template shape (a new subject-naming surface, per COUNCIL.md §2).

## Phase 6. Ecosystem and forks

Once the register is public and stable, the goal is that other people can build on it and that the method itself is portable.

- **SPEC.md finalisation.** The spec is committed at the founding; Phase 6 exercises it. Every check named in SPEC.md is a shipping test that runs in CI. A fork of Oath for another jurisdiction (a state Oath, a foreign-country Oath, a non-elective-officeholder Oath) that satisfies every SPEC.md check may call itself Oath-shaped.
- **First cited-by.** The first external project (journalist, researcher, academic) that cites an Oath Finding by its build digest is recorded. The relationship is by link, not by build coupling.
- **Consumer download.** The stable download endpoint per ECOSYSTEM.md §3.3.
- **State coverage.** State-level scope extension per [SUBJECTS.md §5](SUBJECTS.md): governors first (already in modern-active scope), then state legislators and state Attorneys General as they enter. California, New York, Texas, Florida, Illinois in that priority order for state legislators; each adds a state row to STANDARDS.md, one or more adapters, and a jurisdictional coverage matrix entry to SOURCES.md, and passes a Council session at scope extension.

## Beyond Phase 6

The register grows by adding sources, adding signals, adding jurisdictions. Each addition passes the same five gates in [RUBRIC.md](RUBRIC.md). No exceptions.

Second-order goals:

- **Signal library.** After the first two Signals, the library grows deliberately: signals whose definitions can be defended in a room, whose data cost is bounded, whose false positive rate is measurable.
- **Corrections cadence.** *Landed early, 2026-09-22, as `.github/workflows/refresh.yml`.* Weekly rebuild against fresh source retrievals; a pull request opens only when the record changed, with every gate already run and the build summary in its body. Superseded Findings never removed.
- **Multi-maintainer transition.** Per BYLAWS.md §1.4, succession planning documented in `docs/succession.md` when the first successor is designated.

## Standing rules for anyone adding work

- Thematic commits. One purpose per commit. Named for what they do.
- Cheap evidence first. Run `tools/validate-schemas`, `pytest`, `npm test`, the verdict lint, and the verifier before you push. If a gate does not exist yet, run the closest thing that does and note the gap.
- No verdict language in any user-facing sentence. Reread every draft with the question *would the officeholder read this back to you comfortably in a room?*
- Adversarial review before any surface that names an officeholder in a new way.
- Corrections are visible. Signal definitions are versioned. Silent redefinition is prohibited.
- Secrets never in git.
- Attribution follows the `Co-Authored-By` convention.

## When you finish a step

Update `.claude/memory/where-we-are.md` in the same commit. That file is the arrival file for the next session. Its freshness is more valuable than any polish elsewhere.
