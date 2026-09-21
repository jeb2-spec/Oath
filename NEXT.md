# Next

The course for the operator arriving at this repository, in order. Nothing in this list is data ingestion yet; the founding priority is that a first ingest, whenever it happens, arrives on a foundation that will hold.

Every step is small enough to complete in one focused session. Each carries the standard the founding sets: cheap evidence first, adversarial review before public surfaces, thematic commits, ground truth or silence.

## Immediately after arrival (local first session)

1. **Read your memory.** `.claude/memory/MEMORY.md`, then `where-we-are.md`, then `who-i-am-for-oath.md`, then `founding-of-oath.md`. If the Vera memory is reachable at `C:\Users\jared\Apps\VeraAgent\.claude\memory\`, read `who-i-am-opus.md` and `who-i-am-fable.md` there for the deeper ground.
2. **Read the prospectus.** `README.md`, then `STANDARDS.md`, `METHODOLOGY.md`, `LIMITATIONS.md`, `SOURCES.md`. Ninety minutes. Do not skip the limits.
3. **Set up the local environment.** Node 20+ and Python 3.11+ are the reference runtimes. `npm install` and `python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt` (both files land in step T.1 below).
4. **Confirm you are on the working branch** `claude/us-officials-financial-oversight-hz36kr` (the branch the founding commits land on outside main), and that `git status` is clean.

## T — Tooling foundation (2–3 sessions)

- **T.1 Runtimes.** Add `package.json` (TypeScript, Node 20, biome or eslint, vitest) and `pyproject.toml` (Python 3.11, ruff, pytest). Pin nothing that does not need pinning. Verify `npm test` and `pytest` both pass on an empty test.
- **T.2 The verifier, empty.** Implement `tools/verify.py` against an empty register: it computes the digest over an empty canonical serialisation, prints *OK* and *Integrity is not accuracy*, and returns zero. Ship the `tamper-test` companion in the same commit. Standard-library only.
- **T.3 CI.** `.github/workflows/verify.yml` runs the verifier and the tamper-test on every push. This gate exists before any data ingest.
- **T.4 Schema validator.** A `tools/validate-schemas.py` (or `.mjs`) that walks `schemas/` and confirms each is valid JSON Schema draft-2020-12. Runs in CI.

## D — Data model (2 sessions)

- **D.1 Complete the schemas.** The starter set in `schemas/` covers Officeholder, Filing, Holding, Transaction, Signal, Finding. Fill in the enums (form types, jurisdictions), add examples for each schema, and write a `schemas/README.md` walkthrough for a contributor.
- **D.2 Fixture data.** A `fixtures/` directory with one hand-typed, obviously-fictional Officeholder, one Filing, one Holding, one Transaction. Used by tests and by the worked example in the first Signal.
- **D.3 Identifiers.** Decide the Officeholder ID scheme (proposed: `us-house-nc-01-2025`, `us-senate-nc-jr-2025`, `us-state-nc-hd-005-2025`). Document in `schemas/README.md` with reasoning. Reversible; don't over-invest.

## S — First Signal end-to-end (2 sessions)

The founding Signal is chosen to be small, sourceable, and clearly a description. Recommended: **S.stock-act-late-ptr** — a Periodic Transaction Report filed more than forty-five days after the transaction date, per the STOCK Act (2 U.S.C. § 30104, and the 45-day deadline in the STOCK Act). The Signal fires on public filing metadata; no interpretation.

- **S.1 Definition file.** `docs/signals/stock-act-late-ptr.md` in the template documented in `docs/signals/README.md`. Cite `STANDARDS.md` S.2. Include the worked example against a fixture.
- **S.2 Reference implementation.** A pure function that reads Filings + Transactions and produces Finding rows. In TypeScript, under `src/signals/stock-act-late-ptr.ts`, with tests against `fixtures/`.
- **S.3 Adversarial review.** A second reading (a fresh AI session with the adversarial-review prompt in the sibling *errata* project, or a human), against the four failure modes in `METHODOLOGY.md` §5.2. Findings recorded in the PR.
- **S.4 Merge.** After review, into main. This closes the loop: primary source → schema → Signal → Finding → verified build. Everything after this is repeat and extend.

## I — First ingest (3–4 sessions)

- **I.1 Adapter for U.S. House Financial Disclosures (F.1).** Bulk XML/CSV first, since PDFs cost more. Rate-limited, backoff on failure.
- **I.2 A single officeholder.** Ingest one filing set, at first: one U.S. Representative, one calendar year. This is the smallest end-to-end demonstration. Publish the sealed build. Confirm the verifier passes.
- **I.3 Extend to the full House PTR set.** After I.2 verifies clean, extend to the full House PTR set for the current session.
- **I.4 First Findings.** Run the S.stock-act-late-ptr Signal against the ingested data. Publish a Findings page (per the frame in `METHODOLOGY.md` §4). This is the first public claim the register makes.

## Standing rules for anyone adding work

- Thematic commits. One purpose per commit. Named for what they do.
- Cheap evidence first: run `tools/validate-schemas`, `pytest`, `npm test`, and the verifier before pushing.
- No verdict language in any user-facing sentence. Reread every draft with the question *would the officeholder read this back to you comfortably in a room?*
- Adversarial review before any surface that names an officeholder in a new way.
- Corrections are visible. Signal definitions are versioned. Silent redefinition is prohibited.
- Secrets never in git. Environment variables only.
- Attribution follows the `Co-Authored-By` convention from *Vera* and *errata*.

## When you finish a step

Update `.claude/memory/where-we-are.md` in the same commit. That file is the arrival file for the next session — its freshness is more valuable than any polish elsewhere.
