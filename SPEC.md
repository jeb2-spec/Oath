# Spec

*What any register in Oath's shape has to do to be checkable by a stranger.*

This document exists so that a fork of Oath for another jurisdiction, another subject population, or another purpose can hold itself to the same discipline. It states the properties a valid Oath-shaped register must satisfy. It says nothing about the specific subject matter of *this* register (U.S. elected officials, financial disclosures); it says what any register that would call itself Oath-shaped must be.

A register that satisfies every clause below is Oath-shaped. A register that does not may still be worth building; it should not use the family name.

The clauses below are the ones a stranger with a terminal and a browser can verify. Every clause carries the check that proves it.

---

## S1. Subject scope is defined and testable

A register names its subjects. A subject is either in scope or out of scope. The rule that decides membership is stated in prose and testable in code.

**Check:** the register publishes a `subjects.ndjson` with one row per subject in scope, and a `SUBJECTS.md` document with the membership rule (for Oath, [SUBJECTS.md](SUBJECTS.md); for a fork, the equivalent). A tool `check-subject-scope` reads a candidate subject and returns `in`, `out`, or `undetermined`; `undetermined` is not more than a documented fraction of applied cases.

## S2. Every claim traces to a primary source

Every row in the register carries a `source.url` and a `source.retrieved_at`. Every derived claim (a Finding, a summary count) names the row ids it was derived from.

**Check:** the register ships a `verify-source-trail` tool that walks every derived claim, resolves it to source rows, and fails if any derived claim reaches a row without a source URL or retrieval timestamp.

## S3. The record is sealed

The register produces a single SHA-256 digest over a canonical serialisation of its contents at each build. The canonical form is documented; two builds from the same content on any machine produce byte-identical output.

**Check:** the register ships a `verify` tool that recomputes the digest and compares it against the recorded digest. On match, prints `OK`. On mismatch, prints `FAIL` and returns non-zero.

## S4. The seal covers its own disclosures

The register's `meta`, disclosures, license, and any embedded self-description are inside the sealed serialisation. A change to any of them changes the digest.

**Check:** a `tamper-test` tool alters one row of the disclosures on a throwaway copy and requires `verify` to reject it.

## S5. The record is anchored

Every published build's digest is committed to an external, timestamped, third-party witness that the register's authors cannot rewrite. OpenTimestamps against a public blockchain is the reference witness; equivalents that meet the same property (third-party, timestamped, non-rewritable) qualify.

**Check:** each published build has an anchor file in `data/anchors/<build-hash>.<ext>` with the third-party witness's proof. `verify --anchor` reads the anchor file and confirms it commits to the same digest.

A build made where the anchor cannot be reached ships with its anchor state marked *owed* and says so publicly. It does not ship a proof of a different file.

## S6. The record is portable

The register produces both a database file (SQLite by reference) and a plain-text dump. Both contain the same content in canonical order. A stranger without the database can read the dump; a stranger without either can read the schemas.

**Check:** the register ships a `verify-portable` tool that recomputes the digest from the plain-text dump using a parser that shares no code with the builder, and requires it to match the digest computed from the database.

## S7. Corrections are visible

The register never silently removes a row. A corrected row is superseded by a new row; both remain readable. The chain is walkable: a Finding's `superseded_by` points at its replacement; a replacement's `supersedes` points at what it replaced.

**Check:** a `check-supersessions` tool walks the chain and fails if any superseded row is missing its replacement, or if any Finding has been silently removed from the register between builds.

## S8. The frame appears on every user-facing surface

A register concerned with subjects (as most Oath-shaped registers are) carries a frame sentence that names what the register is and is not. That sentence appears on every surface that names a subject.

For Oath itself the frame is *"Presence in the register is not evidence of wrongdoing."* A fork chooses its own frame in accordance with its subject matter, but the frame is present.

**Check:** a `lint-frame-presence` tool reads every rendered subject-facing template output and requires the frame sentence to appear verbatim in the page's header region.

## S9. Definitions are versioned and their changes are visible

Any classifier, signal, criterion, or rule the register applies to its subjects is versioned. A definitional change produces a new version; the old version and its outputs remain readable.

**Check:** a `check-definition-versions` tool walks the register's definitions and their history and fails if any current definition's criteria differ from a predecessor's without a version bump.

## S10. Adversarial review before shipping subject-naming surfaces

Any change that names a subject in a new way (a new definition, a new template, a page that lists names) requires an adversarial second reading before merge. The review's findings are recorded publicly.

**Check:** the pull request template requires the review checkbox and a linked review comment; CI rejects the merge without both.

## S11. The doctrine is in the record

The register's Charter (or equivalent name), its Rubric (or equivalent), its Invariants (or equivalent), and its Bylaws (if it has them) are committed inside the sealed record. A stranger who verifies the record verifies the doctrine too.

**Check:** the sealed serialisation includes these documents. A tamper of any of them changes the digest.

## S12. Contributor obligations are stated

The register states what a contributor commits to when they open a pull request. At minimum: license terms, conflict-of-interest disclosure, and adherence to the register's Charter.

**Check:** a `CONTRIBUTING.md` (or equivalent) is present and referenced from the pull request template.

## S13. Removal policy is stated and universal

The register states, publicly, what its policy on subject-side removal requests is. The policy applies uniformly; a request from one subject is treated identically to a request from another. No shadow removals.

**Check:** the removal policy is in the Bylaws (or equivalent) and is referenced from the landing page.

---

## What this Spec does not require

- **A specific technology.** SQLite, JSON, TypeScript, Python are the reference stack. Any equivalent works, provided the checks above run.
- **A specific subject.** U.S. elected officials are Oath's subjects. A fork may address any subject population that satisfies S1.
- **A specific jurisdiction.** State forks, city forks, foreign-country forks, and non-governmental forks all fit.
- **A specific set of Signals or classifiers.** What conditions the register defines is the fork's editorial work.
- **A relationship with the parent project.** A fork owes nothing to Oath except honesty about its lineage where applicable.

## Why publish a Spec at day zero

Publishing the Spec before any real data has landed commits the project to the shape *the checks can enforce*, before the temptation to bend a check exists. The Spec that a young project can hold is the Spec its future self can be held to.

If the register ever fails a clause above, the failure is documented as a correction, and the failure and its remedy are the material for the next Council session.
