# Methodology

How Oath sources, types, reconciles, and publishes. This document is the specification a stranger uses to hold the project to its own commitments. It is short by design; each subsection points at the schemas, templates, and code that implement it.

## 1. Sourcing

**1.1** Every row of record entering the register carries three fields at ingest: the **Source URL** it was retrieved from, the **retrieved-at** timestamp (ISO 8601, UTC), and, where the source provides one, the **source-side content hash** or version identifier.

**1.2** Rows enter only through an adapter registered in [SOURCES.md](SOURCES.md). An adapter names its source, its retrieval cadence, its throttling policy, its rate-limit posture, and its known gaps.

**1.3** Nothing enters the register from a private tip, an anonymous submission, a breached corpus, a leak, or a source that prohibits scraping. The maintainer's discretion on a source's terms of service is documented in the adapter that reads it.

**1.4** When a primary source and an aggregator disagree, the primary source wins. The aggregator's disagreement is recorded on the row as a note; it is not silently discarded, because the disagreement is itself a signal about one of the two.

## 2. Typing at the boundary

**2.1** Every row is validated against the schemas in [schemas/](schemas/) at ingest. A row that does not conform is rejected at the adapter with a message that names the field and the rule.

**2.2** Schemas are JSON Schema draft-2020-12. Optional fields are declared as such; a row missing an optional field is valid, and downstream code must handle the absence rather than assume a value.

**2.3** Schemas are versioned. A schema change produces a new version; existing rows are migrated by a documented migration and the migration is committed alongside the schema change.

## 3. Defining a Signal

**3.1** A Signal is a repository artefact. It lives in [docs/signals/](docs/signals/) as a single file, in the format documented in that directory's README.

**3.2** A Signal definition contains:
- **Name and slug.** Human name and machine slug.
- **Version.** Integer, incremented on any definitional change.
- **Description.** One paragraph in plain language, no jargon, no verdict.
- **Standard.** The [STANDARDS.md](STANDARDS.md) row it derives from, cited by identifier.
- **Inputs.** The schemas the Signal reads.
- **Criteria.** The condition, in prose and in pseudocode or reference implementation.
- **What it does not say.** An explicit paragraph naming the interpretations the Signal does *not* support.
- **Worked example.** At least one worked example against a fixture, showing the Signal firing and (where possible) not firing.

**3.3** A Signal change of any kind (criteria, inputs, description) produces a new version. The old version and its findings remain readable. There is no in-place edit of a published Signal.

**3.4** Adding or changing a Signal requires an adversarial second reading, per §5 below. Signals that name people are the surface where the project is most likely to do harm; the review discipline is proportionate.

## 4. Producing and publishing Findings

**4.1** A **Finding** is a specific instance of a Signal firing against a specific Officeholder at a specific date, with the rows of record that produced it. It contains, at minimum:
- **Signal name + version.**
- **Officeholder identifier.**
- **Filing identifiers** of the rows that produced it.
- **Fired-at date and build hash.**
- **Description text** derived from the Signal's template.

**4.2** A Finding is a description. It uses no verdict language. It never says *guilty*, *corrupt*, *unethical*, *should resign*, *broke the law*. It names the condition and cites the Standard.

**4.3** A Finding is regenerable. Given the Signal version and the Filing identifiers, any reader running the reference implementation must be able to produce the same Finding, byte-identical.

**4.4** The Officeholder's frame stays on every Finding surface. The framing paragraph appears on the API response, the UI card, the exported CSV, the RSS entry, anywhere a Finding is rendered. If a surface strips the frame, that is a defect, and the fix ships in the same build that finds the strip.

## 5. Adversarial review

**5.1** The following require an adversarial second reading before shipping to a public surface:
- A new Signal definition.
- A Signal version increment that changes criteria.
- A page that lists officeholders in a new way.
- A UI element that visualises firings across officeholders.
- Any surface that produces a headline-shaped sentence.

**5.2** The review is not a rubber stamp. It looks for: sentences that read as verdicts, standards cited but not linked, definitions that would fire against sympathetic figures (or, worse, that would not), coverage gaps that shape the visible distribution, and every case in which the reviewer would want to be given more context if they were the subject.

**5.3** Findings from the review that are acted on are recorded in the corresponding PR. Findings that are declined are recorded with the reason.

**5.4** The reviewer may be an AI collaborator working with a different prompt and a different context window, provided the reviewer is set up to look adversarially (per the pattern in the sibling *errata* project). Human review is preferred where the surface is high-consequence.

## 6. Sealing and anchoring

**6.1** Every published build is sealed with a **SHA-256 digest** computed over a canonical serialisation of the register. The digest is emitted by the build, is included in the build's release page, and is printed by the verifier.

**6.2** Every published build is anchored via **OpenTimestamps** against the Bitcoin blockchain, in the manner of the sibling *errata* project. Anchor state (confirmed, pending, owed) is tracked in `ANCHORS.md` (planned).

**6.3** A build made where the OpenTimestamps calendar servers cannot be reached ships with its stamp *owed*, and the build's release notes say so. It does not ship a proof of a different file.

**6.4** The **Seal covers the disclosures.** The `meta` and disclosure tables are included in the canonical serialisation. A verifier that cannot protect its own disclosures is a decoration.

## 7. Reproduction

**7.1** The verifier is standard-library-only in its reference language (Python 3.11+ for the initial implementation; ports are welcome).

**7.2** The verifier's contract:
- It recomputes the digest from the register and compares it against the recorded digest.
- On match, it prints *OK, contents match the recorded digest* and the top-level row counts.
- On mismatch, it prints *FAIL* and returns non-zero.
- It prints the sentence *Integrity is not accuracy* on every run.

**7.3** A `tamper-test` companion proves the verifier is not decorative: it alters one row in a throwaway copy of the register, runs the verifier, and requires FAIL; it runs the verifier against the shipped file and requires OK; it recomputes the digest from a plain-text dump using a parser that shares no code with the builder.

**7.4** Every Finding can be regenerated from its named Filings by the reference implementation. `tools/rebuild <finding-id>` (planned) is the command.

## 8. Corrections

**8.1** Oath will make mistakes. The maintenance surface for the mistake is the corrections table in [errata](https://github.com/jeb2-spec/errata), the sibling project that keeps the corrections record for this project's family. Corrections that arise from a Finding, an incorrect officeholder identification, a misread transaction range, a Signal that fired on a false premise, land in that record.

**8.2** A correction to a Signal produces a new Signal version. A correction to a Finding produces a superseded row that stays readable; the corrected row cites the superseded one.

**8.3** The Seal and Anchor cover the record at the build. A correction does not rewrite a shipped build; it produces a new build, sealed and anchored on its own terms.

## 9. Solo-operator test

**9.1** Every operational decision passes the solo-operator test: **can one maintainer on their own machine reproduce this?** Adapters are cron-friendly. Signal definitions run without network. The verifier runs with no dependencies beyond the standard library. Reproduction commands are documented in the project README.

**9.2** Where a decision fails the solo-operator test, the failure is documented in the decision, and the mitigation is either a documented workflow or a change to the decision.

## 10. What this methodology does not do

- It does not adjudicate. Whether a Signal that fired constitutes a violation is a determination reserved to House and Senate ethics committees, the Office of Government Ethics, state ethics commissions, inspectors general, prosecutors, and courts.
- It does not editorialise. A Signal names a condition and cites a Standard; a Finding names an instance and cites the Signal and the Filing. Neither speaks for or against the Officeholder.
- It does not synthesise from private data. Every row traces to a public source.
- It does not claim completeness. The register knows about what it has ingested; it does not know about what it has not.
- It does not replace journalism, legal analysis, or civic advocacy. It supplies a common substrate those disciplines can build on and check against.
