---
name: where-we-are
description: "The current state of Oath. Read first. Updated in the same commit that changes it, or deleted."
metadata:
  node_type: memory
  type: state
---

# Where we are

*Last updated: 2026-09-21, after the second expansion of the working branch (Bylaws, Council, Ecosystem, SPEC, ANCHORS, curate/annotate).*

## The state

**Day zero, with the antidrift core, the governance shape, and the ecosystem plan committed.** The repository has doctrine, schemas, governance, adversarial-review protocol, and a planned website. What it does not have is a single row of real data, a single Signal fired, or a single line of tooling. Both are true and neither is a contradiction: the foundation is what makes the first row worth publishing.

The founding work continues on the working branch, one PR growing through six thematic commits.

## What is real

**On `main`:**
- Prospectus (README), standards (STANDARDS.md), methodology (METHODOLOGY.md), limitations (LIMITATIONS.md), sources (SOURCES.md), schemas (`schemas/*.json`), architecture (`docs/architecture.md`), signal template (`docs/signals/README.md`), placeholders (`data/README.md`, `src/README.md`), PR template, license, gitignore, the CLAUDE.md working stance, the four `.claude/memory/` bridge files, and NEXT.md.

**On the working branch (`claude/us-officials-financial-oversight-hz36kr`), pending PR review:**
- Em-dash strip (voice-print discipline).
- CHARTER.md (five vows + annotate/curate coda; Vow V, *facts stay, change is shown*, added on Jared's call).
- RUBRIC.md (five gates per Signal).
- INVARIANTS.md (sixteen mechanical rules + meta-invariant).
- BYLAWS.md (roles, decision authority, corrections, removal policy, contributor agreement).
- COUNCIL.md (adversarial review body, three seats, seven catch-list categories).
- ECOSYSTEM.md (website plan, mark, consumer contract, fork-friendly).
- SPEC.md (what any Oath-shaped register must satisfy; enables forks).
- ANCHORS.md (public build ledger, empty until first anchored build).
- METHODOLOGY.md §10 (annotate, do not curate).
- Updated PR template with Council checkbox and COI disclosure.
- Sharpened NEXT.md with six phases (added Phase 6: ecosystem and forks).
- README and CLAUDE.md wired to the new documents.
- This file, refreshed.

## What is not real yet

- No adapter. No source has been read.
- No signal is defined. `docs/signals/` contains only the template.
- No verifier, no tamper-test, no schema validator, no CI workflow, no verdict-language lint, no frame-presence lint, no aggregator-sole check, no supersession check, no ranking lint, no COI-disclosure check. Nothing in `tools/` yet.
- No `package.json`, no `pyproject.toml`.
- No fixtures.
- No mark generator; no struck seals.
- No `.claude/prompts/council.md`; the Council prompt is described in COUNCIL.md and lands in Phase 2 with the first Signal review.
- No published builds; ANCHORS.md ledger is empty by design.

## The immediate next moves

Per the sharpened `NEXT.md`:

**Phase 1. Plumbing green.** Ship as: a green CI badge on the working branch and a sealed empty build.

1. T.1 Runtimes (package.json, pyproject.toml).
2. T.2 Verifier and tamper-test (standard-library Python).
3. T.3 Schema validator.
4. T.4 Verdict-language lint (INVARIANTS §1) with initial blacklist.
5. T.5 CI workflow.
6. T.6 Session-start doctor.

Every step is small enough for one session.

Then Phase 2 (first Signal against fixture + Council session on it, prompt committed), Phase 3 (first real officeholder + per-officeholder page + mark generator), Phase 4 (coverage extend + second Signal), Phase 5 (public flip + static site), Phase 6 (ecosystem, forks, first cited-by).

## Standing decisions

- **Repository visibility.** Private at the founding. Jared flips public in Phase 5.
- **Branch.** Work continues on `claude/us-officials-financial-oversight-hz36kr`. Founding commits landed on `main` directly; everything since is on the working branch and lands via pull request.
- **Reference runtimes.** Node 20 with TypeScript 5 for adapters and Signals; Python 3.11 for tooling and the verifier.
- **Data format.** Newline-delimited JSON as canonical; SQLite as convenience mirror.
- **License.** CC BY 4.0 for content; MIT for code.
- **Attribution convention.** `Co-Authored-By: Claude ...`.
- **Voice-print.** No em dashes in any authored markdown.
- **Order of precedence.** Charter > Invariants > Rubric > Bylaws > Methodology/Standards/Sources/Council-prompt > everything else.

## The council seat rotation

Council seats (per COUNCIL.md §3) are: Seat A (the reader who wants to be fair), Seat B (the subject in a room), Seat C (the reviewer's reviewer). All three convene on every session; a single fresh AI session may hold multiple seats sequentially. The Council prompt is committed at `.claude/prompts/council.md` when Phase 2 lands the first Signal.

## What I could not do from the cloud

- Create the GitHub repository. Jared did it manually.
- Set up the local dev environment. Phase 1 T.1 on his machine.
- Wire the sixteen invariant gates. Phase 1 work.
- Convene the first Council session. It will happen for real on the first Signal (Phase 2 S.3).

## The through-line

This is a young repository built on old discipline. The Vera and errata records are its family; when in doubt, read from them. When you finish a step, update this file in the same commit. Its freshness is more valuable than any polish elsewhere.

Read the [Charter](../../CHARTER.md) before you start. If you cannot recall the five vows, come back.
