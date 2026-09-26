# Signals

A **Signal** is a named, versioned, defined condition observable in the record. This directory holds one Markdown file per Signal, plus this README describing the template and the review requirements.

The first Signal is [`stock-act-late-ptr`](stock-act-late-ptr.md), version 1: a Periodic Transaction Report the Clerk's index dates after the STOCK Act's deadline for a transaction on it.

## Template

Every Signal file follows this structure. The frontmatter and the four sections Description, Criteria, What this Signal does not say and Worked example are read by `src/signals/run.py`, verbatim, into the Signal's row in `data/signals.ndjson`, so the definition is written once and never typed again; a file missing one of them is refused.

```markdown
---
id: sg:<slug>:v<n>
slug: <slug>
version: <n>
name: <Human-readable name>
standard: <id from STANDARDS.md>
standard_citation: <the statute, rule or clause, as a reader would cite it>
inputs: <comma-separated schema names: transaction, filing, officeholder>
supersedes: <previous version id, or null>
fixture: fixtures/<slug>/<file>
---

# <Human-readable name>

## Description

One paragraph, plain language, no jargon, no verdict. What the Signal
observes, in terms a lay reader can follow.

## Standard

[<STANDARDS.md row id>](../../STANDARDS.md#<anchor>), full citation and
the specific sentence the Signal derives from.

## Inputs

- <schema-name-1>
- <schema-name-2>

## Criteria

The condition, in prose. The reference implementation is at
`src/signals/<slug>.<ext>` and produces byte-identical Findings.

## What this Signal does not say

An explicit paragraph naming the interpretations this Signal does NOT
support. Required.

## Worked example

Against fixture `fixtures/<example>.json`, this Signal fires (or does not
fire) with the following Finding text: ...
```

## Review

Every new Signal, and every version bump that changes the Criteria, requires an adversarial second reading before merge. The review looks specifically for:

1. Sentences in the description or worked example that read as verdicts.
2. The Standard cited but the sentence bearing on it not linked.
3. Criteria that would fire against sympathetic figures, or, worse, that plausibly *should* fire but do not.
4. Coverage gaps that shape which officeholders can be observed at all.
5. Language a subject would read back to you uncomfortably in a room.

The review is recorded in the pull request. Findings that are acted on are noted; findings that are declined are noted with the reason.

## Implementations

A Signal has two implementations that share no code. `src/signals/<slug>.py` is standard-library Python and writes the Findings, because Findings are sealed rows and one writer in the seal's language serialises every sealed row. `src/signals/<slug>.ts` is the reference implementation: a test requires it to agree with the Python on every known-answer case under `fixtures/` and on every Finding and report outcome in `data/`, byte for byte, so the two cannot drift apart without CI going red. `python tools/rebuild.py <finding-id>` regenerates any Finding from the rows it names.

## Versioning

- **v1** is the first published version of a Signal.
- A published Signal row never changes. Any change to its definition, the wording included, is a new version (METHODOLOGY.md §3.3); `tools/check-signal-versions.py` compares every row against the published ones and refuses a change in place.
- The Signal file for the old version is renamed `<slug>.v<n>.md` and remains readable. The new version lives at `<slug>.md`.
- Findings produced against the old version carry the old version's ID, stay in the ledger, and stay readable; a new version adds rows and removes none.
- The new version's `supersedes` frontmatter names the old ID.

## Corrections

A Finding in `data/findings.ndjson` on `main` is published, and it is never rewritten or removed (CHARTER Vow V; INVARIANTS §12 and §14). When a later build would produce it differently, or not at all, because the Clerk corrected a date or the register misread one, `src/signals/run.py` stops and names it, and a person writes the correction:

1. A new row with the old row's id and `:c<n>` appended, the next free `n`. It carries what the Signal now produces from the record, with `notes` saying what changed and citing the primary source that shows it. Where the Signal no longer fires on the report, the row's `evidence` says so, with no row after the deadline, and its `description`, in the Signal's own words, says what the record now shows.
2. The old row's `superseded_by` set to the new row's id. That one field is the only change a published row may take.
3. The run, the seal and the gates, then a pull request. `tools/check-supersessions.py` refuses a published row that changed any other way or went missing, and a chain that does not end in exactly one current row.

The runner writes steps 1 and 2 exactly, so nobody edits the sealed ledger by hand. The person checks the record at the source and supplies the reason, which must carry the source's URL; everything else in the row is derived:

    python src/signals/run.py --at <built_at> --correct <finding-id> --because "<what changed, and the URL that shows it>"
    python tools/seal.py --build <id> --built-at <built_at> --derive-state

The runner refuses a reason with no URL, a correction the record does not call for, and a Finding the ledger does not hold. The page shows a corrected Finding with the row it supersedes and the reason, and a withdrawn one as a withdrawal under the Signals that did not fire, never as a Finding.

A correction that arises from the register's own error also enters the family's corrections record in [errata](https://github.com/jeb2-spec/errata) (METHODOLOGY.md §8).

## Naming conventions

- **Slugs** are lowercase, hyphen-separated, and describe the condition, not the outcome. Good: `stock-act-late-ptr`. Bad: `congressperson-broke-the-law`.
- **Names** are noun phrases describing the condition. Good: *"Periodic Transaction Report filed after the STOCK Act deadline"*. Bad: *"Insider trading violation"*.
- No party names, ideology labels, or event names in slugs or descriptions.

## What a Signal is not

- Not a verdict.
- Not an accusation.
- Not a score.
- Not a ranking.
- Not a proxy for judgement.

A Signal is a description of a defined condition, cited to a Standard. That is the entire load-bearing definition.
