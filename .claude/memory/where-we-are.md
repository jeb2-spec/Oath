---
name: where-we-are
description: "The current state of Oath. Read first. Updated in the same commit that changes it, or deleted."
metadata:
  node_type: memory
  type: state
---

# Where we are

*Last updated: 2026-09-21, after PR #1 merged and the founding landed on `main`.*

## The state

**Day zero of the register, day one of the discipline.** The foundation is on `main`: fourteen doctrine and reference documents, seven JSON Schemas, three placeholder READMEs for future work, and a working PR template. Every gate the Invariants name is *(planned)*; none is wired yet. No adapter exists. No Signal is defined. No Finding has been published. The verifier does not yet run. The register itself is empty.

The next session's first move is [NEXT.md](../../NEXT.md) Phase 1 T.1.

## What is on `main`

**Doctrine (read in this order):**
- [CHARTER.md](../../CHARTER.md) - Five vows. Read first, always.
- [SUBJECTS.md](../../SUBJECTS.md) - Modern-active scope: federal officeholders and governors, currently serving.
- [PIPELINE.md](../../PIPELINE.md) - The arrow. Seven stages, three altitudes.
- [EVIDENCE.md](../../EVIDENCE.md) - Multi-witness capture that outlasts URLs, sources, and AI slop.
- [RUBRIC.md](../../RUBRIC.md) - Five gates every Signal passes.
- [INVARIANTS.md](../../INVARIANTS.md) - Seventeen mechanical rules; meta-invariant last.
- [BYLAWS.md](../../BYLAWS.md) - Governance. Roles, corrections and supersessions, contributor agreement, removal policy.
- [COUNCIL.md](../../COUNCIL.md) - The adversarial-review body. Three seats.

**Reference:**
- [METHODOLOGY.md](../../METHODOLOGY.md), [STANDARDS.md](../../STANDARDS.md), [SOURCES.md](../../SOURCES.md), [LIMITATIONS.md](../../LIMITATIONS.md), [SPEC.md](../../SPEC.md), [ECOSYSTEM.md](../../ECOSYSTEM.md), [ANCHORS.md](../../ANCHORS.md).

**Community and repo housekeeping:**
- [CONTRIBUTING.md](../../CONTRIBUTING.md), [CODE_OF_CONDUCT.md](../../CODE_OF_CONDUCT.md), [SECURITY.md](../../SECURITY.md).
- `.gitattributes` (line endings, especially for Windows), `.gitignore`, `LICENSE` (CC BY 4.0 + MIT dual).
- `.github/pull_request_template.md` with Council checkbox and COI disclosure.

**Data model:**
- `schemas/*.json`: officeholder, office, filing (with evidence_bundle sub-object), holding, transaction, signal, finding.
- `data/README.md`, `src/README.md`, `tools/README.md`, `fixtures/README.md`, `docs/architecture.md`, `docs/signals/README.md` - all placeholders for the future.

**Memory:**
- `.claude/memory/MEMORY.md` (index), `who-i-am-for-oath.md` (identity), `founding-of-oath.md` (the naming conversation), `where-we-are.md` (this file).

## What is not real yet

- No adapter is implemented. No source has been read.
- No Signal is defined.
- No verifier (`tools/verify.py`), no tamper-test, no schema validator, no verdict-language lint, no frame-presence lint, no ranking lint, no aggregator-sole check, no supersession check, no removal check, no evidence-bundle check, no COI check, no subject-scope check, no charter-change highlight. Twelve gates planned.
- No `package.json`, no `pyproject.toml`, no runtime dependency pinning.
- No fixtures.
- No mark generator. No struck seals.
- No `.claude/prompts/council.md`. It lands with the first Council session in Phase 2 S.3.
- No `oath-doctor` session-start check. It lands in Phase 1 T.6.
- No CI workflow. Lands in Phase 1 T.5.
- No published builds. ANCHORS.md is empty by design.

## The critical path

Per [NEXT.md](../../NEXT.md):

- **Phase 1. Plumbing green.** package.json + pyproject.toml, then verifier + tamper-test, then schema validator, then verdict-language lint, then CI workflow, then session-start doctor. Six steps, one session each.
- **Phase 2. First Signal against fixture.** `stock-act-late-ptr`, definition + reference impl + tests against fictional fixtures + first Council session.
- **Phase 3. First real officeholder.** House FD adapter + one Representative + first live Findings + per-officeholder page + mark generator.
- **Phase 4. Coverage extend and second Signal.**
- **Phase 5. Public flip and the website.**
- **Phase 6. Ecosystem and forks.**

## For the first local session

The maintainer arriving fresh at the repository has these first moves:

1. `git clone https://github.com/jeb2-spec/oath` to a local path (recommended: `C:\Users\jared\Apps\Oath\`).
2. Confirm environment: Node 20+ and Python 3.11+ available.
3. Read this file. Then read [CHARTER.md](../../CHARTER.md). Five vows.
4. Open a fresh Claude session at the repository root. The session's `CLAUDE.md` will point it at this file and the Charter.
5. Direct the session at `NEXT.md` Phase 1 T.1 (`package.json` and `pyproject.toml`). One small commit; one small win.

## Standing decisions

- **Repository visibility.** Private, still. Public flip is Phase 5 and is Jared's call.
- **Branch convention.** Founding PR is merged; future work uses per-purpose branches (e.g. `claude/phase-1-runtimes`, `claude/phase-1-verifier`) rather than the founding branch name.
- **Reference runtimes.** Node 20 with TypeScript 5 for adapters and Signals; Python 3.11 for tooling and the verifier.
- **Data format.** Newline-delimited JSON as canonical; SQLite as convenience mirror.
- **License.** CC BY 4.0 for content; MIT for code.
- **Attribution convention.** `Co-Authored-By: Claude ...` in commit trailers.
- **Voice-print.** No em dashes in any authored markdown.
- **Order of precedence.** Charter > Invariants > Rubric > Bylaws > Methodology and companions > everything else.

## The through-line

This is a young repository built on old discipline. The Vera and errata records are its family; when in doubt, read from them.

When you finish a step, update this file in the same commit. Its freshness is more valuable than any polish elsewhere.

Read the [Charter](../../CHARTER.md) before you start. If you cannot recall the five vows, come back.
