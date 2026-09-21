# Signals

A **Signal** is a named, versioned, defined condition observable in the record. This directory holds one Markdown file per Signal, plus this README describing the template and the review requirements.

At the founding, no Signal is defined. The first Signal (recommended: `stock-act-late-ptr`, per `NEXT.md`) lands with the first end-to-end demonstration.

## Template

Every Signal file follows this structure:

```markdown
---
id: sg:<slug>:v<n>
slug: <slug>
version: <n>
name: <Human-readable name>
standard: <id from STANDARDS.md>
supersedes: <previous version id, or null>
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

## Versioning

- **v1** is the first published version of a Signal.
- Any change to the Criteria, Inputs, or Standard is a version bump.
- The Signal file for the old version is renamed `<slug>.v<n>.md` and remains readable. The new version lives at `<slug>.md`.
- Findings produced against the old version carry the old version's ID and stay readable.
- The new version's `supersedes` frontmatter names the old ID.

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
