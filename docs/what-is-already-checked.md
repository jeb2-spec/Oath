# What is already checked

*Written 2026-09-27, after a session that went looking for defects in seven places and found the
project already sound in all seven. That is a good result and an expensive way to learn it. This page
exists so the next session spends its time on what is not covered instead of rediscovering what is.*

Every line below was confirmed by reading the tool or running it in this session, not by reading a
document's claim about itself. Where a claim here and the code ever disagree, the code is right and
this page is stale; `scripts/oath-doctor.py` prints the live inventory of gates and should be trusted
over this list.

## The register's rows

| Guaranteed | By |
| --- | --- |
| Every row validates against its schema | `tools/validate-schemas.py` |
| An id is unique within its file | same, `check_rows`: *"an id is a key"* |
| A filing names an officeholder the register holds, at an office that officeholder holds | same, `joins()` |
| A transaction names a filing the register holds, and agrees with it about whose it is | same, `joins()` |
| A change row is about a row the register holds | same, `joins()` |
| A Signal run's summary is the sum of its own outcome rows | same, `run_agrees_with_itself()` |
| One outcome per report in a run record | same |
| A published row never disappears, and only gains facts it lacked | `tools/check-removals.py` |
| A published Finding never changes or vanishes; supersessions chain | `tools/check-supersessions.py` |
| A published Signal version never changes in any byte | `tools/check-signal-versions.py` |
| No Finding rests on an aggregator alone | `tools/check-aggregator-sole.py` |
| Every Finding regenerates byte-identically from the rows it names | `tools/rebuild.py` |
| Nothing sealed changed since the build | `tools/verify.py`, and `tools/tamper-test.py` proves the verifier is not decorative |

**Checked by hand in this session and found clean, with no gate behind them:** no two officeholders on
one seat; no amount range whose floor exceeds its ceiling; no trade dated in the future. Worth a gate
only if one of them ever appears.

## The Signal

| Guaranteed | By |
| --- | --- |
| Every worked case in `fixtures/stock-act-ptr-after-deadline/cases.json` comes out as hand-computed | `src/signals/test_stock_act_ptr_after_deadline.py` |
| The Python and TypeScript implementations agree on every case | the Vitest suite, 42 tests |
| The deadline is the earlier of 30 days from notification and 45 from the trade | guard `the-deadline-is-the-earlier-of-the-two-limits` |
| A notification date earlier than the trade it notifies never sets the deadline | guard `a-notification-before-its-trade-never-sets-the-deadline` |
| A notification date later than the report never sets the deadline | guard `a-notification-after-its-own-report-never-sets-the-deadline` |
| A trade dated after its own report is not evaluated | guard `a-trade-dated-after-its-own-report-is-not-evaluated` |
| A deadline before the rule's first year is not evaluated | guard `a-deadline-before-the-rules-first-year-is-not-evaluated` |

The five guards were added on 2026-09-27 because the branches were tested and nothing proved a test
would catch their removal, which is what `tools/measure-guards.py` exists for and what 56 guards did
for everything except the one file that decides whether a named person is said to have missed a legal
deadline.

**Live proof the first of them matters.** 35 transaction rows on the 2025 record carry a
`notified_date` earlier than the trade it notifies, one of them by 32,858 days: a report filed
2025-04-11 whose 18 rows print 1935-03-28. Applying that date sets a deadline in April 1935, after
which every filing on earth is late. The branch holds, the report records `after: 0`, and no Finding
rests on it.

## The surfaces

| Guaranteed | By |
| --- | --- |
| Every page naming an officeholder opens with the frame | `tools/lint-frame-presence.py` |
| No list ranks officeholders, and no number sits beside a person | `tools/lint-no-ranking.py` |
| The register of what is missing never says a record is public, obtainable or withheld until somebody here has read it at its source, and every row that does not know says what to read | `tools/check-wanted.py` |
| The sealed state and every run record name no person | `tools/lint-no-names.py` |
| No verdict language on any user-facing surface | `tools/lint-verdict-language.py` |
| Every page tells a person how to dispute a fact about themselves | guards in `tools/guards.ndjson`, measured |
| An answer never rests on rows the page does not show, and never on another person's report | guards `an-answer-rests-on-the-rows-its-page-shows`, `a-reports-row-count-is-the-one-the-rows-hold` |
| The mark is struck legibly at every digest | `tools/check-mark.py` |
| Every Markdown cross-reference resolves | `tools/check-crossrefs.py` |
| No secret, personal path or personal e-mail address in any tracked text file | `tools/scan-secrets.py` |

## The doctrine and the record

| Guaranteed | By |
| --- | --- |
| The five antidrift files cannot change without a row naming the change, its reason, its Council reading and its approver | `tools/highlight-charter-change.py` (INVARIANTS §17) |
| A recorded reading cannot name a seat the prompt at that blob SHA does not define | same |
| Every seat COUNCIL.md §3 names is sat in the Council prompt | `scripts/oath-doctor.py` |
| Every guard in the list has a failing input | `tools/measure-guards.py` |
| A build's digest is committed to Bitcoin | `tools/anchor.py`, build `0005-house-2025` confirmed at block 968733 |
| Every test's answer is the code's answer, not the machine's | `conftest.py`, and `tools/test_conftest.py` checks its list against the code both ways |

## What is not checked, and is known

- **The Clerk's obsolete code for American Samoa.** `clerk.house.gov/xml/lists/MemberData.xml`
  publishes `AQ`, not `AS`. The register carries it faithfully and the landing names it at its
  destination heading. **Do not "fix" it to `AS`:** the source says `AQ`, and rewriting it would make
  the register disagree with the record it cites.
- **The chamber's seat count.** The register holds 439 offices, 433 Representatives, 5 Delegates and 1
  Resident Commissioner. It does not hold how many seats the chamber has, so it cannot say whether any
  seat was vacant when the roster was read. Nothing on any surface claims otherwise.
- **The TypeScript implementation's branches are not measured.** `tools/measure-guards.py` drives
  pytest only, so a guard cannot name a Vitest selector. The hand-worked fixtures do cover the
  TypeScript side, so a mutation there fails its own suite; what is missing is the proof that it would.
- **INVARIANTS §15 and §16 have no gate**, and §16's text still requires a bundle containing each
  filing's bytes, which the register deliberately does not keep. INVARIANTS.md also still marks ten
  landed gates *(planned)*.
- **One chamber, one filing year, one Signal.** The Senate, the executive branch and the states are not
  read. The index's one-letter form codes are not interpreted, which is what the second Signal waits on.
