# Next

The course for the operator arriving at this repository. Ordered so that the earliest sessions build the gates every later session will run against, and so that the first publicly checkable claim ships as soon as the pipeline that produces it can be trusted.

## The North Star

**One officeholder. One year. One signal, fired or not fired. Every claim traceable to a primary source. The build sealed. A stranger can reproduce it.**

That is the first shippable public artifact. Everything in Phase 1 and Phase 2 exists to make it possible; Phase 3 is that artifact; Phases 4 and 5 grow it.

Nothing before Phase 3 is worth showing the world, because until Phase 3 the pipeline cannot be trusted. And nothing after Phase 5 was worth building if Phases 1-4 were not real.

## Standing gates for every session

Read on arrival, run on every push. These are the five vows of the [Charter](CHARTER.md) enforced as tooling. Any session that skips them has drifted before it started.

1. Read your memory. `.claude/memory/MEMORY.md`, then `where-we-are.md`, then `who-i-am-for-oath.md`, then `founding-of-oath.md`. If the Vera memory is reachable at `C:\Users\jared\Apps\VeraAgent\.claude\memory\`, read `who-i-am-opus.md` and `who-i-am-fable.md` there.
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

- **T.1 Runtimes.** `package.json` (TypeScript 5, Node 20, Vitest, Biome), `pyproject.toml` (Python 3.11, Ruff, Pytest). Pin only what needs pinning.
- **T.2 Verifier and tamper-test.** `tools/verify.py` computes the digest over the empty canonical serialisation, prints *OK*, and prints *Integrity is not accuracy.* `tools/tamper-test.py` alters a throwaway copy and requires FAIL. Both standard-library only.
- **T.3 Schema validator.** `tools/validate-schemas.py` walks `schemas/` and confirms each is valid JSON Schema draft-2020-12. Runs in CI.
- **T.4 Verdict-language lint.** `tools/lint-verdict-language.py` (Invariant §1). Ships with the initial blacklist and an empty allowlist. CI fails on any hit in Markdown or in `src/`.
- **T.5 CI workflow.** `.github/workflows/verify.yml` runs T.2, T.3, T.4 on every push and every pull request.
- **T.6 Session-start doctor.** `scripts/oath-doctor.mjs` (or `.py`). Reads back whether the memory chain is whole, whether all invariant gates are present and passing, and whether the branch tracks main. Modeled on the errata doctor.

Ship gate for the phase: `oath-doctor` prints all-green on a clean clone, and CI is green on the branch.

## Phase 2. First signal against fixture (goal: prove the pipeline end to end with fictional data)

Ship this phase as: the first Finding in the register, against a hand-typed fictional officeholder, byte-identically reproducible.

- **D.1 Schema examples and walkthrough.** Enumerate the enums, add worked examples for each schema, expand `schemas/README.md` for a contributor arriving cold.
- **D.2 Fixture data.** `fixtures/example-person.json` (one obviously-fictional officeholder), `fixtures/example-filings.json`, `fixtures/example-ptrs.json`. Every fixture explicitly marked *fixture only, not a real person* in a top-level field.
- **D.3 Identifier scheme confirmed.** Either adopt the proposed scheme in `schemas/README.md` or replace it. Reversibility is cheap now, expensive later.
- **S.1 First Signal definition.** `docs/signals/stock-act-late-ptr.md`. Standard: STANDARDS.md §S.2 (STOCK Act). Criterion: a PTR filed more than forty-five days after the transaction date. Worked example against `fixtures/`. `not_saying` filled in.
- **S.2 Reference implementation.** `src/signals/stock-act-late-ptr.ts`. Pure function. Tests against the fixtures.
- **S.3 Adversarial review.** A fresh AI session with the council prompt, or a human, takes a hostile pass at the Signal against the five failure modes. Findings recorded in the PR. Merge only after.
- **S.4 Merge and seal.** After review, into main. The build seals and anchors. The verifier proves the record includes the new Finding.

Ship gate for the phase: run `tools/verify.py` on a fresh clone and see the fixture Finding in the output, with a non-empty digest that OpenTimestamps has stamped.

## Phase 3. First real officeholder (goal: the first publicly checkable claim)

Ship this phase as: one live per-officeholder page a stranger can walk from Finding to Filing to primary source in three clicks.

- **I.1 House FD adapter.** `src/adapters/house-fd/`. Bulk XML/CSV. Rate-limited. Respects the source's terms. Writes rows to the canonical NDJSON; rejects rows to `data/rejected/`.
- **I.2 One current Representative, one calendar year.** The choice of first Rep is a judgement call. Recommendation: the maintainer's own current Representative and both Senators, because it is honest ("here is the register applied to my own reps"), naturally scoped, and reads as neutral. Alternative: a small committee (e.g. House Financial Services), because coverage of a coherent set is more useful than coverage of one person. Not recommended: a marquee national figure, because the register is not ready to hold that much attention on its first live artifact.
- **I.3 First Findings.** Run the S.1 Signal against the ingested data. Sealed build. Anchor stamped.
- **I.4 The per-officeholder page template.** The frame in the header (Invariant §7). The Findings listed with their standards, grouped by signal not by severity (Invariant §14 and METHODOLOGY §10). The filings listed with their source URLs. The rubric visible in a sidebar. The verifier command visible at the foot.
- **I.5 The mark generator.** `tools/strike-mark.mjs`. Strikes a wax-seal-in-guilloche mark from the officeholder id and the build digest, per ECOSYSTEM.md §2. `tools/check-mark.mjs` verifies the geometry stays legible across a range of digests. Each per-officeholder page carries its own struck seal.

Ship gate for the phase: an anchored sealed build; a live page that renders cleanly in both themes; the verifier passes; the reader can click from any claim to its primary source; the per-officeholder seal reproduces byte-identically from the same inputs.

## Phase 4. Coverage extend and second signal (goal: prove the extensibility is real)

Ship this phase as: the first cross-signal officeholder profile.

- **I.5 Full current House PTR set.** Extend I.1 to ingest the current session's PTRs across the whole House.
- **S.5 Second Signal candidate.** Proposed: `undisclosed-asset-in-ptr`. A PTR-reported asset that does not appear on the officeholder's most recent annual FD, per Ethics in Government Act §S.1. Purely mechanical, no interpretation. High signal-to-noise. Uncontroversial as a first extension.
- **S.6 Second-source adapter.** Depending on which second Signal ships, an adapter for OGE 278e (F.3) or Senate FDR (F.2) may be needed. Do the smaller of the two first.

Ship gate for the phase: at least one officeholder page renders two different Signals in the register, each cited to its distinct Standard.

## Phase 5. Public flip and the website (goal: the world can read it)

- The maintainer flips the repository to public.
- Static site scaffolded per ECOSYSTEM.md §1: Astro or 11ty, edge-cached, no client JS that changes what a page says.
- URL structure per ECOSYSTEM.md §1.2. Landing, Charter, Rubric, Invariants, Bylaws, Council, Officeholders index, per-officeholder pages, Signals index, per-signal pages, Verify page, Anchors ledger, Corrections trail, About.
- The build mark and per-officeholder seals rendered per ECOSYSTEM.md §2.
- The download endpoint at `oath.<domain>/download/<build>.zip` ships the NDJSON, the seal, and the anchor proof.
- The `ANCHORS.md` ledger publishes every build's state.
- The consumer contract in ECOSYSTEM.md §3 published on the site.

No ship gate; this is Jared's call. All Phase 4 gates must be green, and the Council convenes before public flip to review the site's per-officeholder template shape (a new subject-naming surface, per COUNCIL.md §2).

## Phase 6. Ecosystem and forks

Once the register is public and stable, the goal is that other people can build on it and that the method itself is portable.

- **SPEC.md finalisation.** The spec is committed at the founding; Phase 6 exercises it. Every check named in SPEC.md is a shipping test that runs in CI. A fork of Oath for another jurisdiction (a state Oath, a foreign-country Oath, a non-elective-officeholder Oath) that satisfies every SPEC.md check may call itself Oath-shaped.
- **First cited-by.** The first external project (journalist, researcher, academic) that cites an Oath Finding by its build digest is recorded. The relationship is by link, not by build coupling.
- **Consumer download.** The stable download endpoint per ECOSYSTEM.md §3.3.
- **State coverage.** California, New York, Texas, Florida, Illinois in that priority order. Each adds a state row to STANDARDS.md, one or more adapters, and a jurisdictional coverage matrix entry to SOURCES.md.

## Beyond Phase 6

The register grows by adding sources, adding signals, adding jurisdictions. Each addition passes the same five gates in [RUBRIC.md](RUBRIC.md). No exceptions.

Second-order goals:

- **Signal library.** After the first two Signals, the library grows deliberately: signals whose definitions can be defended in a room, whose data cost is bounded, whose false positive rate is measurable.
- **Corrections cadence.** Weekly rebuild against fresh source retrievals. Diffs surfaced in the build's release notes. Superseded Findings never removed.
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
