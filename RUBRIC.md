# Rubric

Every Signal that publishes a Finding in Oath answers five questions before it ships. They are gates, not axes. Any answer of *no* holds the Signal at pull request.

The rubric is errata-shaped: not a score, a discipline. A Signal that scores 4 of 5 is a Signal that ships nothing. There is no partial credit. This is the price of a register a stranger can trust.

---

## The five gates

### 1. Sourcing

Does every input row this Signal reads come from a primary source registered in [SOURCES.md](SOURCES.md)?

Aggregators (OpenSecrets, Capitol Trades, ProPublica *Represent*, LegiStorm, Ballotpedia, Follow the Money, MapLight, *Unusual Whales*, and their kin) are cited beside the primary they drew from. They are never the sole basis for a Finding. Where the aggregator disagrees with the primary, the primary wins and the disagreement is recorded.

**Gate:** the source-check tool walks every producing filing and confirms none is registered with `source_type: aggregator` alone. CI fails on any Finding that fails the check.

### 2. Standard grounding

Does the Signal's criterion cite a specific statute clause, CFR section, constitutional clause, or codified chamber rule from [STANDARDS.md](STANDARDS.md)?

A principle is not a citation. *"Trust in government"* is not a Standard. *"5 CFR § 2635.101(b)(14)"* is. If the paragraph in the Signal's definition cannot point at a specific numbered section, the Signal is asking the reader to take our word for it, and the register was built to stop doing that.

**Gate:** the Signal schema requires `standard.id` (an identifier from STANDARDS.md) and `standard.citation` (a display string). Schema validation runs on every push.

### 3. Frame preservation

Does every sentence the Signal produces (in its definition, in the template that renders its Findings, in the plain-language description on the officeholder page) avoid the verdict-language list at [INVARIANTS.md §1](INVARIANTS.md)?

The test that has never yet failed a session using it: **would a subject read this sentence back to you in a room, comfortably?** If the answer is no, the sentence carries a verdict the register does not have authority to render, and the sentence is rewritten.

**Gate:** the verdict-language lint scans every Signal definition and every rendered Finding for the blacklisted words. CI fails on any hit.

### 4. Reproducibility

Given the Signal's version and the Filing IDs it names, does the reference implementation regenerate byte-identical Findings?

A Finding a stranger cannot reproduce is a claim a stranger has to take on trust. The reference implementation is pure (no network, no side effects); its tests run against fixtures under `fixtures/`; the fixtures are committed; the same fixture must produce the same Finding on any machine that runs the tests.

**Gate:** the Signal's test file. Vitest or pytest running against fixtures. CI fails if any test fails.

### 5. Adversarial review

Has a second reader (a fresh AI session with the council prompt, or a human) taken a hostile pass at the Signal, looking for the five failure modes named in [METHODOLOGY.md §5.2](METHODOLOGY.md)?

The five failure modes are: sentences that read as verdicts, standards cited but not linked, criteria that would fire against sympathetic figures (or plausibly should fire but do not), coverage gaps that shape the visible distribution, and language a subject would read back to you uncomfortably in a room. The review is not a rubber stamp. It looks for one of the five and refuses to close until it is convinced none apply.

**Gate:** the pull request template requires a checkbox and a linked review comment. CI rejects the merge without both.

---

## Tuning

The five gates are pass/fail. Where projects like Oath want a scoring dial, they get one: the *weight* of a gate can be set to `required` or `advisory` per Signal. Every Signal in this repository starts with all five required. Downgrading any gate to `advisory` is a pull request that names the reason and the risk, is highlighted by the change-highlight tool, and is approved by the maintainer.

An advisory Signal still runs. Its Findings are still tracked. They just are not blocked by that gate. This is the honest version of *"we know this is not yet at the standard, and here is why we published it anyway."*

At the founding, no Signal is advisory. It is not likely any will be for a long time.

## Errata-style bookkeeping

Every Finding carries three fields the reader can hold us to:

- **What the record shows.** The specific filing rows and dates.
- **What the standard says.** The specific statute, CFR section, or clause.
- **What the two together produce.** The condition, in the words of the Signal definition. No verdict.

These are not opinions about the Officeholder. They are the fields a stranger uses to hold the Signal to what it says it is.

## The one measurement Oath runs on itself

Errata measures its own errors and publishes them. Oath does the same, one step upstream: it measures the Signals themselves, and it publishes what it finds.

- **Firings per Signal per build.** If a Signal fires against 40% of the ingested population, either the definition is broad, the population is broken, or the standard is systemically under-observed. Any of the three is worth naming.
- **Correction rate per Signal.** How many Findings has this Signal produced that were later superseded? A Signal with a high correction rate is a Signal whose definition needs a version bump.
- **Time from Filing publication to Finding surfaced.** The gap between the source and the register is a measure of how live the project is.

These are not scores of the Officeholders. They are scores of the Signals, published so the reader can see whether the register is calibrated honestly.

The method will be set down in METHODOLOGY.md, in its own section, and the values in `MEASUREMENT.md`, once the first Signal has fired against real data.

## The simplest version, if the rest is lost

If a Signal cannot answer *what does this cite, what does this not say, and how would we know it is wrong,* the Signal is not ready.
