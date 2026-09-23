# The Pipeline

*How a public filing becomes a written, verified, checkable record, and how a reader without training walks the whole chain, from a Reddit thread to a Bitcoin block, without having to trust anyone.*

This is the operational document for Oath. The Charter names what we will not do; the Rubric names the gates every Signal passes; the Invariants name the mechanical rules. This file names *how the arrow flies*. It is written at three altitudes on purpose: the story a reader arrives with, the vocabulary a researcher or a PhD would want, and the schemas and contracts an engineer would build against. Every reader can stop at their level. Nothing above stops being true when you keep reading; the deeper layers just show the working.

---

## The walk

A person reads on Reddit that their Senator bought defense-contractor stock two weeks before a committee vote. Somebody in the thread says *citation needed.* Nobody has one. The thread devolves into the usual shape. The person closes the browser and doesn't think about it for three days.

Then they see Oath in a footer link somewhere, click, search the Senator's name. There is a Finding on the page: *Periodic Transaction Report filed forty-three days after the transaction date. The STOCK Act (2 U.S.C. § 30104) requires filing within thirty days of notification or forty-five days of the transaction, whichever is earlier.* Under it: the filing's PDF URL at senate.gov. Under that: a command a person can run to prove the record has not been quietly rewritten.

They click the PDF. It opens on senate.gov. The form is there. The transaction date is there. The filing date is there. The math is right.

They copy the verify command. They paste it into a terminal. It prints *OK*, a build digest, and a Bitcoin block number. A friend who knows a little more tells them what that last bit means: the digest of every row on that page was written into a Bitcoin block on a date the register cannot rewrite, witnessed by a network the register's authors have no reach into.

The person now knows three things they did not know three days ago. The Senator's filing was late by three days. The register that said so did not invent the number. The register did not quietly change the number after publishing it. None of the three required them to trust anyone.

The Reddit thread is still where it was. The person adds the link to the Oath Finding and closes the tab.

*That is the arrow. This document is how it flies.*

---

## The seven stages, in order

Every claim on Oath moves through the same seven stages. Each stage has an input, an output, a guarantee it makes to the next stage, and a receipt a stranger can inspect after the fact. Nothing skips a stage. Nothing enters the register another way.

### Stage 1. Discovery

A primary source is identified and registered. A primary source is an official body publishing filings the officeholder is required by law to make: the U.S. House Clerk's Financial Disclosure Portal, the Senate's Electronic Financial Disclosure Search, the Office of Government Ethics for Form 278e, the FEC for campaign finance, the Senate LDA database for lobbying, and their state-level analogues.

**What happens.** A maintainer or contributor reads the source's terms of service, understands its format, documents its cadence and its known gaps, and opens a pull request that adds a row to [SOURCES.md](SOURCES.md).

**What must be true.** The source publishes public filings; the source's terms permit programmatic reading of them (or a manual path exists that does); the source has a stable enough URL scheme that a citation to it will resolve for years.

**Where it lands.** [SOURCES.md](SOURCES.md), one row per source, with URL, publisher, form types accepted, formats emitted, retention policy, terms notes, and known gaps.

**How it can fail.** A source's terms prohibit programmatic reading and the manual path is prohibitively expensive (documented as inaccessible in SOURCES.md with the reason). A source disappears (its row stays; the row is annotated with the outage date; the register's citations to it continue to display).

### Stage 2. Retrieval and multi-witness capture

An adapter fetches from one registered source on a cadence, produces schema-typed rows, and produces the durable evidence bundle that lets the citation survive the source itself.

**What happens.** The adapter (in `src/adapters/<source>/`) reads the source on schedule, respects rate limits and any documented politeness rules, writes the exact response bytes to `data/captures/<filing-id>/response.<ext>`, records the response headers, computes the SHA-256 hash, submits to the Wayback Machine and (where permitted) archive.today, pins the bytes to IPFS through at least two pinning services, and commits the hash to OpenTimestamps. Full architecture in [EVIDENCE.md](EVIDENCE.md).

**What must be true.** Every candidate row carries a `source.url`, a `source.retrieved_at` timestamp in ISO-8601 UTC, the SHA-256 `content_hash` of the response, and the pointer to its evidence bundle at `data/captures/<filing-id>/`. Every filing has at least one external witness confirmed before it is considered complete (Invariant §16). Nothing enters without those fields. This is Invariants §4 and §16.

**Where it lands.** The adapter's output is inputs to Stage 3 (schema validation) *and* a self-contained evidence bundle a stranger can verify years later without contacting the register.

**How it can fail.** Source down (adapter fails closed, logs to `data/adapter-runs/`, next scheduled retry). Source shape changed (schema mismatch caught at Stage 3; adapter version bump follows). Rate limit hit (adapter backs off; retries with the source's stated retry-after). External witness unavailable (row ships as *pending-external-witness*, a follower job retries; after seven days, escalation per Invariant §16).

### Stage 3. Typing at the boundary

Every candidate row is validated against a JSON Schema. Invalid rows are rejected loudly, not silently swallowed.

**What happens.** Each row from Stage 2 is validated against the appropriate schema in [`schemas/`](schemas/): `officeholder.schema.json`, `office.schema.json`, `filing.schema.json`, `holding.schema.json`, `transaction.schema.json`. Rows that pass are written to the canonical newline-delimited JSON files under `data/`. Rows that fail are written to `data/rejected/<source>/<date>.ndjson` with the field name and rule that failed.

**What must be true.** No row enters the register that does not conform to a published schema. This is the property that lets every downstream step trust its inputs. It is not a checkbox; it is the machinery that prevents the register from ever containing a shape it did not agree to.

**Where it lands.** `data/*.ndjson` (canonical) and `data/oath.db` (SQLite convenience mirror, rebuilt from the NDJSON).

**How it can fail.** A row is systematically rejected because the schema needs an additive field (schema version bump). A row is rejected because the source publishes garbage occasionally (row remains in `data/rejected/`, visible; the count is a signal about source quality).

### Stage 4. Signal application

Defined Signals read the typed rows and produce Findings.

**What happens.** Each Signal defined in [`docs/signals/`](docs/signals/) has a definition file (name, version, description, cited Standard, inputs, criteria, `not_saying`, worked example) and a pure reference implementation in [`src/signals/`](src/signals/). The reference implementation is called on the current register and emits Finding rows. It reads what its definition names and nothing else. It writes no side effects. It touches no network.

**What must be true.** Every Finding cites a Signal (with version), an Officeholder, and one or more producing Filings. Every Signal traces to a Standard in [STANDARDS.md](STANDARDS.md). Every Finding is regenerable byte-identically from its named inputs by any machine running the reference implementation. These are Invariants §2 and §3 and Rubric gate 4.

**Where it lands.** `data/findings.ndjson`, one row per Finding.

**How it can fail.** A Signal fires against a case that fits the letter but not the spirit of the Standard (bug; a version bump adjusts the criterion; the pre-existing Findings stay in the record with `superseded_by` per Vow V). A Signal does not fire against a case the Standard clearly covers (bug; version bump; missing coverage documented as a Correction). Both cases route through the Council per [COUNCIL.md](COUNCIL.md) at the version bump.

### Stage 5. Rendering

The typed rows and the produced Findings become a written record a reader can read.

**What happens.** The build reads the canonical NDJSON and produces:

- **Per-officeholder pages** (`officeholders/<id>.html`), showing filings in chronological order, Findings grouped by Signal name, sources cited, verifier command visible at the foot. The frame *presence in the register is not evidence of wrongdoing* appears in the header of every one. This is Invariant §7.
- **Per-signal pages** (`signals/<slug>/<version>.html`), showing the definition, the cited Standard, the criterion, and every Finding this Signal has produced in the current build.
- **Doctrine pages** (Charter, Rubric, Invariants, Bylaws, Council, Methodology, Standards, Sources, Limitations, Spec, Ecosystem, Anchors) served as static HTML.
- **The build's Oath mark**, struck as guilloche from the build's SHA-256 digest per [ECOSYSTEM.md §2](ECOSYSTEM.md).
- **Per-officeholder seals**, each parameterised by the officeholder's identifier and the build digest. Change the officeholder's record, the seal changes.

**What must be true.** Every rendered sentence about an officeholder passes the verdict-language lint (Invariant §1). No cross-officeholder ranking appears on any surface (Invariant §13). Every user-facing page carries the frame (Invariant §7). Every rendered Finding descends from a Finding row (no free-standing prose about a person that isn't a rendered row).

**Where it lands.** The static site, deployable to a static host, buildable offline.

**How it can fail.** The verdict-language lint hits (build blocks; sentence rewritten). A template renders a person without the frame (build blocks; template fixed). A page sorts officeholders by a per-person score (build blocks; sort order changed to non-scoring).

### Stage 6. Sealing and Anchoring

The build's contents are cryptographically sealed and third-party-witnessed.

**What happens.** The build computes a SHA-256 digest over the canonical NDJSON plus `meta.json` plus the doctrine documents (Charter, Rubric, Invariants, Bylaws, Council, Methodology, Standards, Sources, Limitations, Spec, Ecosystem included in the sealed serialisation). The digest is emitted, printed by the verifier, and committed to OpenTimestamps against the Bitcoin blockchain via public calendar servers. The proof is stored at `data/anchors/<build-hash>.ots`.

**What must be true.** The Seal covers its own disclosures (Invariant §9). The Anchor is a third-party witness the register's authors cannot rewrite (Bitcoin's blockchain, via OpenTimestamps calendars). A build made where the calendars cannot be reached ships with its anchor state marked **owed** and says so in [ANCHORS.md](ANCHORS.md); it does not ship a proof of a different file.

**Where it lands.** `data/anchors/<build-hash>.ots` (the proof file); [ANCHORS.md](ANCHORS.md) (the public ledger row).

**How it can fail.** Calendars unreachable (state: **owed**, retry queue, escalation after six months per BYLAWS §2). Anchor stays *pending* longer than expected (state stays pending until block confirmation is observed; the row updates in place with the retry history).

### Stage 7. Reader verification

A stranger, on their own machine, confirms the record independently of the register's authors.

**What happens.** The reader:

1. Clones the repository (or downloads the build bundle).
2. Runs `python3 tools/verify.py`, recomputes the digest, compares to the recorded digest, prints *OK* on match, prints *FAIL* on mismatch. Prints *Integrity is not accuracy* on every run so that promise is never quietly dropped.
3. Optionally runs `python3 tools/tamper-test.py`, proves the verifier rejects a changed record.
4. Optionally runs `ots info data/anchors/<build-hash>.ots`, reads the OpenTimestamps proof and prints the Bitcoin block height that confirms it. The reader can look up the block on any public block explorer and see that the register's digest is in it.

Nothing in that path goes through the register's authors.

**What must be true.** The verifier is standard-library-only in its reference language (Python 3.11). The verifier is short enough to read in one sitting. The digest recomputation from a plain-text dump shares no code with the builder (Rubric gate 4; the errata precedent).

**Where it lands.** In the reader's own trust, earned by checking. The register produces no side effect here; the reader has become independent of it.

**How it can fail.** The verifier is confusing (documentation is improved; the errata verifier already ships a plain-language explainer). The reader lacks a terminal (the site provides a Signal Message channel where a friend who has a terminal can send them the same output). The reader still doesn't trust it (the register does not require them to; the primary source URL is in the same row).

---

## The register register

The seven stages are the plumbing. The **register register** is the way the register speaks about what it found. It sits between Stage 4 (a Finding row) and Stage 5 (a rendered sentence). It is the pipeline stage that has no schema, because language does not schema-fit, so it is a discipline instead.

The discipline has four parts.

**Structure and precision, not vocabulary.** A Finding is rendered from a template. The template is a fill-in-the-blank pattern: `{Officeholder.legal_name}'s {Filing.form_type} was filed {N} days after the {Transaction.transaction_date} named on the report. {Standard.short_form} requires filing within {threshold} days of {trigger}, whichever is earlier.` The template's blanks are drawn from the schema-typed rows. The template's fixed words are approved once by Council review and then reused. Every rendered Finding has the same shape; no rendered Finding is a bespoke sentence.

**No verdict language.** The rendered sentence names conditions, cites Standards, and stops. It does not use *guilty, corrupt, unethical, criminal, crook, disgrace, dishonest, sleazy, dirty, tainted, wrongdoing, malfeasance,* or *misconduct.* This is the verdict-language blacklist enforced by Invariant §1. Adding a word takes one approver; removing a word takes two.

**Would the subject read this in a room comfortably?** Every template is drafted, then read aloud by the author sitting in the chair of the officeholder it describes. If any sentence in the template would cause them to protest, the sentence is not correct; it is a claim in disguise. Rewrite.

**The frame stays.** Every rendered surface that names an officeholder shows *presence in the register is not evidence of wrongdoing* in a place the reader will see before the Finding. This is Vow II and Invariant §7. It is not a footer, and it is not an "About" link. It is the first thing on the page above the Officeholder's name.

## Serving four audiences at once

The register is written for four kinds of reader at once, and each reader can stop at their level.

**The person from Reddit.** They arrive from a comment thread. They want to know if the anecdote is true. They read the Finding, they click the source URL, they see the filing, they decide. The **walk** above is what they get. The plain-language sentence carries the whole load: *N days after the date on the report; the STOCK Act requires within X days.* No jargon. No party name. No claim about who the officeholder is.

**The engineer.** They opened the repo. They want to know how it works. They read PIPELINE.md's seven stages, they descend into `schemas/`, they read the adapter contract, they run the verifier. The **stages** are what they get. Every stage names an invariant, a schema, a receipt, and a failure mode.

**The researcher or PhD.** They want to know whether the method is defensible under academic scrutiny. They read METHODOLOGY.md, they read STANDARDS.md, they read LIMITATIONS.md, they check the Signal definitions against the Standards they cite. They may read SPEC.md to see whether the shape of the register is fork-able. The **vocabulary** and the **citations** are what they get. Every term is defined once; every claim traces to a statute clause or a CFR section; every Signal names what it does not say.

**The subject.** The Officeholder or their staff. They want to know what the register says about them and how to correct or supersede it. They read their own page, they read the frame at the top, they read the Bylaws' correction path in §5 and the supersession path in §6. If a Finding is wrong on a fact, they can send a primary-source citation and the correction is entered. If a Finding named a condition they have since demonstrated a change of, they can send the later filing that shows it. The **corrections and supersessions** are what they get. Facts stay. Change is shown.

The pipeline is one pipeline serving all four. The altitude of a sentence depends on where the sentence sits.

## Terms, reconciled

Terms defined once, used consistently, drawn together for a reader who wants them in one place. Full definitions in [README §3](README.md).

| Term | One-line definition |
| --- | --- |
| Oath | The sworn statement, taken on assumption of an elective office, that binds the officeholder to defined duties. |
| Office | A specific elective position, with a jurisdiction, a term, and a set of duties. |
| Officeholder | A natural person occupying an Office for a defined term. |
| Standard | A statute, regulation, constitutional clause, or codified ethics rule that defines a duty applicable to an Office. |
| Filing | A single dated instance of a required Disclosure, identified by its filer, its form type, and its retrieval URL. |
| Holding | A reported asset attributed to an Officeholder or a covered relative in a Filing. |
| Transaction | A reported purchase, sale, or exchange affecting a Holding. |
| Signal | A named, versioned, defined condition observable in the record. |
| Finding | A specific instance of a Signal firing against a specific Officeholder. |
| Source | The primary document or database entry from which a row was retrieved. |
| Seal | The SHA-256 digest of the register at a build. |
| Anchor | A third-party witness to the Seal. OpenTimestamps against Bitcoin is the reference. |
| Correction | A row that supersedes an earlier row on the ground that the earlier row named a fact incorrectly. |
| Supersession | A row that supersedes an earlier row on the ground that a later primary-source filing demonstrates a change of conduct addressing the condition the earlier row named. |

## The engineering appendix

For the engineer descending to the level where a fork could be built or a check could be extended.

### Adapter contract

The founding wrote this contract as a guess. The first adapter (`src/adapters/house-fd/`, landed 2026-09-22 and 23) grew into the shape below, and the shape is now the contract; the founding's version stays in git history. This is the union the next adapter must fit, whatever its source.

Every adapter lives at `src/adapters/<source>/` and is three stages, each a script one maintainer can run by hand:

- **Capture** (`fetch.py`; and `documents.py` where the source keeps documents behind an index). Retrieves the exact bytes and records, for each retrieval, the URL, the time, the SHA-256 and the response headers the source sent, into `data/cache/<source>/` (ignored by git) with a manifest. It touches the network and touches nothing under `data/` that is sealed. It is polite: one request at a time, a pause between them, a user agent naming the project and the operator's address. It decides what to capture from the source's own index and the build's join, never from the register's rows, so the capture stage is pure with respect to the register and a build is never a cycle behind its source.
- **Build** (`build.py`). Reads the captures and nothing else; touches no network. Writes the canonical rows under `data/` that validate against `schemas/`. Writes every row it did not accept to `data/rejected/<source>/<year>-<capture key>.ndjson` with the reason, in the source's own words where the source spoke. Writes one run record to `data/adapter-runs/<source>-<year>-<capture key>.ndjson` naming the captures (URL, time, hash, last-modified), the counts, the rejections by reason, the documents read and not read, and the hash of any adjudication file that shaped the build. The capture key is the hash of the captures' hashes, so the same bytes rebuild the same tree byte for byte and the seal holds; the tree carries one run record and one set-aside file per adapter and year, and the record of an earlier capture lives in git history with the build it sealed.
- **Seal** (`tools/seal.py`, shared by every adapter). Re-run in the same commit as any change to a sealed file. `built_at` is a time from the record, the latest retrieval or the tip the build came from, never the clock. The seal refuses a state text that does not carry the build's own figures and a run record with no set-aside file beside it.

What every adapter must do, learnt from the first:

- Attribute a row to a person only on the source's own evidence (the roster's name; the document's own header), never on a likelihood. Hold what it cannot settle for a person, with the reason and the evidence cited on the row. Refuse nothing on an inference about who a filer is not.
- Carry the source's codes, marks and words as printed, and cite the source's own legend rather than restate it. Where the source's form makes a mark optional, a blank is unmarked, not a fact.
- Say on the row what it could not do (a document captured and not read; a column not read; a source that lists a row twice), and count it in the run record, so that absence is said rather than guessed.
- Keep every fact it learnt about the source's shape in [SOURCES.md](SOURCES.md) with the date it was measured, and every shape in a test with no real person in it.
- Need nothing but the standard library to build; declare any extraction dependency under an optional group in `pyproject.toml`, and never import it in the verifier.
- Run under the refresh loop: capture, compare the capture key with the last run record, build, seal, every gate, and a pull request only when the source served different bytes.

Grafting the next adapter, the checklist: a [SOURCES.md](SOURCES.md) entry naming the door and its terms, and whether a human step stands in it; the [STANDARDS.md](STANDARDS.md) entry for what the source's office requires; the three scripts and their tests; a README beside them saying what one retrieval produced and what it refused; the run record's counts on the landing; and a Council reading before any page names a person through it.

An adapter is *pure with respect to the register*: it does not read from the canonical NDJSON, only write. If a downstream process needs adapter A's output as adapter B's input, that is a build orchestration matter, not an adapter concern.

### Signal contract

Every Signal lives at:

- `docs/signals/<slug>.md`. the definition, in the template documented at [docs/signals/README.md](docs/signals/README.md).
- `src/signals/<slug>.ts`. the reference implementation. A pure function of typed inputs to Finding rows. No network. No file I/O.
- `fixtures/<slug>/`. one or more fixture pairs (inputs, expected outputs) that are the Signal's tests.

A Signal is versioned. A change to a Signal's criteria, inputs, or Standard produces a new version file at `docs/signals/<slug>.v<n>.md`; the current file is always the latest. Findings produced against the old version stay in the record with their old version id.

### Verifier contract

`tools/verify.py`:

- Standard-library-only Python 3.11.
- Short enough to read in one sitting (target: under 200 lines).
- Recomputes the digest over the canonical NDJSON in a defined byte-order documented at the top of the file.
- Prints `OK` on match, `FAIL` on mismatch, `Integrity is not accuracy` on every run.
- Exits with the appropriate return code (0 on OK, non-zero on FAIL).
- Has a companion `tools/tamper-test.py` that:
  - Alters one row in a throwaway copy and requires `FAIL`.
  - Runs against the shipped file and requires `OK`.
  - Recomputes the digest from the plain-text dump using a parser that shares no code with the builder (per RUBRIC gate 4 and the errata precedent).

### The gate list (planned tools, one per invariant)

Every gate lives at `tools/<name>.py` or `tools/<name>.mjs` and runs in CI. Every invariant in [INVARIANTS.md](INVARIANTS.md) names its gate. Summarised here for the engineer building them:

| Invariant | Gate |
| --- | --- |
| §1 verdict language | `tools/lint-verdict-language.py` |
| §2 signal cites standard | `tools/validate-schemas.py` (schema check) |
| §3 finding names filings | `tools/validate-schemas.py` |
| §4 filing carries source | `tools/validate-schemas.py` |
| §5 no aggregator sole | `tools/check-aggregator-sole.py` |
| §6 signal declares not-saying | `tools/validate-schemas.py` |
| §7 frame on every surface | `tools/lint-frame-presence.py` |
| §8 signal version bump reviewed | GitHub Actions workflow reads PR checkbox + council link |
| §9 seal covers disclosures | `tools/verify.py` + `tools/tamper-test.py` |
| §10 no secrets | `tools/scan-secrets.py` |
| §11 no silent redefinition | `tools/check-signal-versions.py` |
| §12 supersessions chained | `tools/check-supersessions.py` |
| §13 no cross-officeholder ranking | `tools/lint-no-ranking.py` |
| §14 facts stay | `tools/check-removals.py` |
| §15 contributor COI | `tools/check-coi-disclosure.py` |
| §16 evidence bundle per filing | `tools/check-evidence-bundle.py` |
| §17 meta-invariant highlight | `tools/highlight-charter-change.py` |

Every one is *(planned)* at the founding. They land in NEXT.md Phase 1.

### The build output

A build emits, atomically:

- `data/*.ndjson` (canonical rows).
- `data/findings.ndjson` (produced Findings).
- `data/oath.db` (SQLite mirror; rebuildable).
- `meta.json` (build id, timestamp, digest, gate results, adapter run summary).
- `data/anchors/<build-hash>.ots` (once stamped).
- `docs/build/` (rendered HTML for the site, once Phase 5).
- One row appended to [ANCHORS.md](ANCHORS.md).
- One release note in the build's changelog.

The build is deterministic: two builds from the same inputs on the same machine produce byte-identical output. Non-determinism (a timestamp, a random id) is a build failure.

## The arrow

The pipeline exists so that a reader who came here from a Reddit thread can walk to a Bitcoin block and back, and take with them three things they did not have before:

1. **What the record shows.** Named clearly, cited to the primary source, without a verdict wrapped around it.
2. **The Standard that governs it.** So the reader knows whether the condition matters under U.S. law, not whether we say it matters.
3. **A way to prove the register did not fabricate the number or edit it afterwards.** Cryptographic, third-party-witnessed, independent of us.

None of the three asks the reader to trust the register. All three ask them to look. The register earns whatever trust it earns by handing over the means to check every one of its claims, before it makes any of its claims.

This is why the pipeline is what it is. Every stage exists so that the reader who chooses to check can. The register's job is not to be believed. The register's job is to be checkable, in a form a person without a subscription and without a law degree can walk. When the reader gets to the end of the walk and the numbers still match, the trust they have is trust they made themselves.

*Prepare. Craft. Aim. Shoot.*

The preparation is the Charter, the Rubric, the Invariants, the Bylaws, the Council.

The craft is the schemas, the adapters, the verifier, the gates.

The aim is the first Signal, chosen because it is small, sourceable, mechanical, and cannot be gamed by editorial choice.

The shot is the first live Finding, on a real officeholder, with the seal against a Bitcoin block a reader can look up themselves.

The arrow does not need to be spectacular. It needs to fly straight.

---

*Kept by the Maintainer, with an AI collaborator disclosed. Read next: [NEXT.md](NEXT.md) for the phases that take this pipeline from prospectus to shipped.*
