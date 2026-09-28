# The FEC domain: the second source, and a second kind of row

*Written 2026-09-28, at the maintainer's direction: the register should be more than a record of
stock trading, and it should move faster. Both are answered by the same change, and it is not the
one this note set out to propose.*

## Abstract

The register holds one source (the Clerk's financial-disclosure index) and one Signal (a transaction
report dated after the STOCK Act deadline). Extending it by adding a second Signal over a second
source would double the machinery and roughly double the caution each new claim requires, because a
Signal is a computed condition about a named person and every one of them has to be defined,
versioned, fixture-tested, read adversarially and defended.

This note proposes something cheaper and, for a reader, worth more: **a second kind of row.** The
Federal Election Commission publishes, as a primary source under a public-domain licence with a real
API, what every federal campaign raised and spent. Almost none of it needs a condition computed over
it. Set beside what a member disclosed owning and what they swore, it is a picture; and a picture
assembled from sourced facts, with no line drawn between them, is the thing this project can publish
that a watchdog with a thesis cannot.

So: the FEC enters mostly as **reference**, with **one** narrow Signal.

## 1. Why the FEC, and not an aggregator

Everything in this section is from this repository's own catalogue
([docs/related-work/aggregators.md](../related-work/aggregators.md)), read at its source on
2026-09-21, and not re-read since; where a claim in this section matters, it carries that date and
not today's. What *was* read at the source on 2026-09-28 is the API's own published description of
itself, and §6 records exactly what it said.

**The FEC is a primary publisher, not an aggregator.** It publishes the filings themselves: a browse
site, the OpenFEC 1.0 REST API, and bulk data files. Summary data and report images post within 48
hours of receipt. API data updates nightly; bulk files run through the 2026 cycle.

**Every record traces to its filing image.** The developers page states that rows are tied to the
underlying form by file ID and image ID. That is the property the register needs and the one most
sources lack: a row here can cite the document it came from, not a summary of it.

**The licence is public domain.** Code and government works are CC0 / public domain. Compare
OpenSecrets, the obvious alternative: its API was **discontinued on 15 April 2025**, its bulk data is
CC BY-NC-SA 3.0 US behind account registration and approval, and it computes per-person ranks
(*"Rank: 6th in the House"*, *"Richest Members of Congress"*) that [INVARIANTS.md
§13](../../INVARIANTS.md) forbids this register from publishing. It is a fine project and it is not a
source this register can build on. Cite it; do not depend on it
([CLAUDE.md](../../CLAUDE.md), the humility clause).

**Access is ordinary.** An API key from api.data.gov; a registered key allows 1,000 calls an hour.
The solo-operator test ([METHODOLOGY.md §9](../../METHODOLOGY.md)) passes without a human in the
retrieval loop, unlike the Senate's disclosure search, which needs a person to click an agreement,
and unlike the Clerk's PTR documents, which need PDF text extraction.

## 2. The constraint that shapes everything, and why it is welcome

The catalogue records a data-use restriction under **52 U.S.C. § 30111(a)(4)** and **11 CFR §
104.15**: information about individual contributors (names, addresses) copied from reports is
restricted in how it may be used.

That restriction points the same way this register's own doctrine already points.
[SUBJECTS.md §3](../../SUBJECTS.md) puts private citizens out of scope.
[LIMITATIONS.md §9](../../LIMITATIONS.md) says the same. A contributor is a private person who gave
money to a campaign; they are not an officeholder and they did not swear anything.

**So the register does not read Schedule A at the contributor level, and publishes no contributor's
name, ever.** Not because the statute forbids this use, which it likely does not, but because the
register would not publish it either way, and a rule that is obeyed for two independent reasons is
one nobody has to remember.

What the register reads instead is the filing's own metadata and the committee's own totals: who
filed, for what period, when it was due, when it arrived, and what the committee reported in
aggregate. None of that names a private person.

## 3. The reference rows

A **reference row** is a new shape for this register: a sourced, dated fact joined to an
officeholder, with **no condition computed over it**. It never fires. It is never a Finding. It
carries no adverse sentence, because it carries no sentence at all: a page renders it, and the
reader reads it.

Proposed for the first pass, all of it committee-level and none of it about a private person:

| row | what it holds |
| --- | --- |
| `committee` | an authorized campaign committee: its FEC committee ID, its name, the candidate ID it is authorized by, and the cycle |
| `committee-period` | one reporting period for one committee: total receipts, total disbursements, cash on hand at close, the report's coverage dates, its due date, its receipt date, and the filing's file ID and image ID |

Two rows. That is the whole adapter's output for the first pass.

**Why this is the velocity answer.** A reference row makes no claim about a person's conduct, so it
needs no Signal definition, no version freeze, no known-answer fixtures, and no adversarial reading
before it ships. It needs what every row here needs: a schema, a primary source, an identifier that
joins without inference, and a gate. Nothing more. §7 says what that means for how we work.

## 4. The one Signal

**`committee-report-after-due-date`.** A periodic report the FEC's own calendar gives a due date for,
whose receipt date is after that date.

It is the drop-in analogue of the Signal already running: two dates, one comparison, no judgement,
and the arithmetic is the whole of it. It reuses the runner, the ledger, the supersession chain, the
seal and every gate unchanged.

What it must say, in the register's existing voice:

> The FEC's reporting calendar gives this report a due date of *«date»*. The FEC's own record gives
> its receipt date as *«date»*, which is *«n»* days after it. The register computes no penalty and
> sees none of the Commission's decisions.

What it must never say: that a committee was penalised, that anyone acted knowingly, that a late
report means anything beyond the two dates, or that the committee **filed** late. That last one is
not a style note. The field is the Commission's received date, by the FEC's own definition (§6.3), so
the register says *recorded* and never *filed*, in the Signal's sentence and in every figure caption
that renders it. The id proposed above, `committee-report-after-due-date`, already avoids both words,
and should keep avoiding them. Whether a report was late in the legal sense, and what
follows from it, is the Commission's; the register publishes the dates it read.

**Expect it to be quiet.** Campaign committees are professionally administered and mostly file on
time. A Signal that fires on almost nothing is [CHARTER](../../CHARTER.md) Vow V working, not a
failure: *the register is silent by default, and empty is a legitimate result*. It is included
because it costs almost nothing once the reference rows exist, and because a domain the register only
describes, never checks, would be a domain where nobody could tell whether the checking worked.

## 5. What this register will not do with it

Stated here so it cannot be adopted later by drift.

- **No contributor names or addresses.** §2.
- **No computed correlation between money and a vote.** The register may one day hold both a
  committee's receipts and a member's votes, and a reader may set them side by side. The register
  will not do that arithmetic for them. "Received money from an industry and voted for its bill" is
  an argument, and the moment this project computes it, it becomes a participant rather than a
  record. State both facts, cite both sources, draw no line.
- **No totals ranked across people.** INVARIANTS §13 already forbids it; it is repeated because a
  campaign-finance dataset invites a leaderboard more strongly than anything the register holds
  today, and because the nearest comparable project publishes exactly that.
- **No per-person "score", index or grade**, assembled from any combination of these rows.

## 6. What has been verified, and what has not

Read at the source on 2026-09-28, mostly from the document the API publishes about itself
(`https://api.open.fec.gov/swagger/`); where an item rests on something else, it says so. Each belongs
in
[docs/wanted/wanted.ndjson](../wanted/wanted.ndjson) before the adapter is written, under the rule
that file already enforces: **a row may not say what a source holds until somebody here has read it
at its source.** Three of the five are settled; two are not.

1. **The reporting calendar as data. Settled, yes.** `/v1/reporting-dates/` is a dataset, not a page
   for humans. It takes `report_type`, `report_year` and `min_due_date`/`max_due_date`; each record
   carries `due_date`, `report_type`, `report_type_full`, `report_year`, `create_date` and
   `update_date`. The Signal in §4 is definable. This was the load-bearing unknown and it fell the
   right way.

2. **A transaction-level identifier. Settled, with a caveat.** The `Filings` resource carries
   `sub_id`, a string. Its published description is **blank**, so what it identifies, and how stable
   it is across reads, is undocumented. An id whose meaning nobody has written down is a weaker
   foundation than one with a definition, so nothing in [INVARIANTS.md §14](../../INVARIANTS.md)
   rests on it until the adapter has watched it hold still across builds.

3. **The receipt date. Settled, and it is the opposite of the Clerk's.** The API documents
   `receipt_date` as *"Date the FEC received the electronic or paper record."* It is the Commission's
   received date. It is not the committee's filing act, and no amount of reading documents will make
   it one, because the FEC says plainly that it is not.

   This tightens §4 rather than loosening it. A Signal built on this field may say *the Commission
   recorded this report after its due date*. It may never say *the committee filed late*; that is a
   different claim about a named committee, and this field does not support it. The Clerk's
   `FilingDate` turned out to be the filing act (`wt:the-clerks-filing-date`, read on every report
   the register can read); the FEC's turns out not to be. The two must never be described in the
   same words.

   **The trap, named now while it is cheap:** the `EFilings` resource carries a field called
   `filed_date`, described as *"Timestamp of electronic or paper record that FEC received."* A field
   whose name says *filed* and whose definition says *received* is this project's characteristic
   defect sitting in the open, waiting to be picked up by whoever reads the name and not the line
   under it. The adapter reads the definition.

4. **The candidate-to-member join. Settled, and the answer is better than a crosswalk.** The FEC's
   candidate record carries no identifier this register already holds: no Bioguide id, no Clerk id.
   What it carries is `office` (`H`, `S`, `P`), `state`, `district`, `district_number` and
   `election_years`. That is a seat, and this register's offices are keyed the same way:
   `data/offices.ndjson` holds `chamber`, `state`, `district` and `seat` (`AK00`). So the join is
   structural, on fields both sides publish, and never a match on a person's name, which is also
   how it avoids taking a dependency on an aggregator's crosswalk, per §1.

   What stays open is narrow and testable: whether the FEC's two-digit `district` encodes an at-large
   seat the way this register's `00` does, and what the join does with a seat that changed hands
   inside a cycle. Both are read from the data once, before any row publishes.

5. **The terms of service. Unread, and the catalogue's link is wrong.** `https://api.data.gov/terms/`
   returns 404 today; `https://api.data.gov/about/` resolves and states no terms. Whatever governs an
   api.data.gov key is not where the catalogue said it was, so this note claims nothing about it. It
   blocks nothing: §2 already holds the register to less than any licence would grant.

## 7. What this changes about how we work

The maintainer's direction alongside this note was to rely less on the Council for decisions, and to
move faster: *this is a mission, not a product.*

The reference row is what makes that safe rather than merely fast. The Council's readings have
earned their place: they caught a claim about scanned paper that no row supported, an adverse
sentence left on the wrong person's page, a frame that a crop would drop, a square at 1.64:1 against
its background. Every one of those was **a claim about a person**. None of them was a gate on
plumbing.

So the rule that should govern is the narrow one this project already wrote down in
[CLAUDE.md](../../CLAUDE.md): *any surface that names an officeholder in a new way goes through an
adversarial second reading before it ships.* A new Signal qualifies. Reference rows, pages, gates,
adapters, schemas and tooling do not.

[COUNCIL.md §3](../../COUNCIL.md) currently says three seats convene **on every session**. That is
the expensive rule and it is the stale one: it was written before the project had shipped anything,
and practice long ago settled on reading what names a person. It is sealed, so narrowing it costs an
amendment, a reading and a re-seal, and buying that ceremony to reduce ceremony would be the joke
this project has already caught itself telling once. It rides the next re-seal;
[NEXT.md D.4](../../NEXT.md) carries it.

Until then the working stance is the binding one, and it says what it says.

## 8. The order to build it

1. **Done, 2026-09-28.** §6.1 and §6.3 were reads, not code, and both are settled: the reporting
   calendar is a dataset, and the receipt date is the Commission's and not the committee's. §4
   survives both, with *recorded* where it would have been tempting to write *filed*. What is still
   to be read is §6.2's undocumented id, §6.4's two narrow encoding questions, and §6.5's terms.
2. `SOURCES.md` row for the FEC, with its retrieval, its throttle, its licence and its known gaps.
   Sealed; rides a re-seal.
3. Schemas for `committee` and `committee-period`, and the adapter that writes them. Gates as usual.
4. The reference rows on the pages: a member's committee, its totals by period, sourced and dated,
   beside what they disclosed. No condition, no colour, no ranking.
5. The Signal of §4. §6.1 settled yes, so it is on the table. Fixtures first, then the runner, then
   one adversarial reading before it publishes.

Steps 2 to 4 are the engineer's to decide and ship. Step 5 is the one that names people in a new way.
