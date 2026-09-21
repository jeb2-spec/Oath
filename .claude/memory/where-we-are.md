---
name: where-we-are
description: "The current state of Oath. Read first. Updated in the same commit that changes it, or deleted."
metadata:
  node_type: memory
  type: state
---

# Where we are

*Last updated: 2026-09-21, after the antidrift foundation landed on the working branch.*

## The state

**Day zero, plus the antidrift core.** The repository exists on `main` with the founding doctrine. A pull request on the working branch adds the Charter, the Rubric, the Invariants, and the sharpened critical path in NEXT.md. No data has been ingested. No signal has been defined. No finding has been published. The verifier does not exist yet. The gates named in INVARIANTS.md are agreed but not yet wired.

The founding and the antidrift additions were both drafted in a cloud session on Opus 4.7. Everything committed here should be reproducible from `NEXT.md` on a local machine.

## What is real

**On `main`:**
- `README.md`: the prospectus in the errata register.
- `STANDARDS.md`: the legal frameworks the project measures against.
- `METHODOLOGY.md`: how sources, types, signals, findings, seals and anchors work.
- `LIMITATIONS.md`: what the project cannot do, in the order a careful reader would raise them.
- `SOURCES.md`: the primary sources planned. No adapters implemented yet.
- `NEXT.md`: the course for the first sessions after arrival.
- `CLAUDE.md`: the working stance.
- `LICENSE`: dual CC BY 4.0 (content) plus MIT (code).
- `schemas/*.json`: six JSON Schemas (Officeholder, Office, Filing, Holding, Transaction, Signal, Finding), version 0.
- `docs/architecture.md`: the layered shape.
- `docs/signals/README.md`: the Signal template. No signals defined yet.
- `data/README.md`: planned layout of the canonical store. Directory otherwise empty.
- `src/README.md`: planned layout of adapters, signals, surfaces. Directory otherwise empty.
- `.github/pull_request_template.md`: with the review checklists.
- `.claude/memory/`: the bridge, four files.

**On the working branch (`claude/us-officials-financial-oversight-hz36kr`), pending merge:**
- Em-dash strip across every markdown file (voice-print discipline).
- `CHARTER.md`: four vows. The antidrift core in 400 words.
- `RUBRIC.md`: the five gates every Signal passes before it publishes a Finding.
- `INVARIANTS.md`: twelve mechanical rules with their gates, plus the meta-invariant.
- `NEXT.md`: rewritten with the sharpened five-phase critical path.
- This file updated.

## What is not real yet

- No adapter is implemented. No source has been read.
- No signal is defined. `docs/signals/` contains only the template.
- No verifier (`tools/verify.py`), no tamper-test, no schema validator, no CI workflow.
- No verdict-language lint. No frame-presence lint. No aggregator-sole check. No supersession check. None of the twelve invariant gates in INVARIANTS.md exist yet as tools; they land in NEXT.md Phase 1.
- No `package.json`, no `pyproject.toml`, no runtime dependency pinning.
- No fixtures.
- No `ANCHORS.md`. There is nothing to anchor.

## The immediate next moves

Per the sharpened `NEXT.md`:

**Phase 1. Plumbing green.** Ship as: a green CI badge on the working branch and a sealed empty build.

1. T.1 Runtimes. `package.json` (TypeScript 5, Node 20, Vitest, Biome) and `pyproject.toml` (Python 3.11, Ruff, Pytest).
2. T.2 Verifier and tamper-test.
3. T.3 Schema validator.
4. T.4 Verdict-language lint (INVARIANTS §1).
5. T.5 CI workflow running T.2 through T.4.
6. T.6 Session-start doctor.

Every step is small enough to finish in one session.

Then Phase 2 (first Signal against fixture), Phase 3 (first real officeholder, live checkable page), Phase 4 (coverage extend and second Signal), Phase 5 (public flip).

## Standing decisions

- **Repository visibility.** Private at the founding. Jared flips public when he is ready.
- **Branch.** Work continues on `claude/us-officials-financial-oversight-hz36kr`, per the per-repo branch convention. The founding commits landed on `main` directly (no reviewers at that point); everything since is on the working branch and lands via pull request.
- **Reference runtimes.** Node 20 with TypeScript 5 for adapters and Signals; Python 3.11 for tooling and the verifier.
- **Data format.** Newline-delimited JSON as canonical; SQLite as convenience mirror.
- **License.** CC BY 4.0 for content; MIT for code.
- **Attribution convention.** `Co-Authored-By: Claude ...` per the Vera and errata convention.
- **Voice-print.** No em dashes in any authored markdown. Stripped 2026-09-21 across all fourteen files. New writing follows the same rule.

## What I could not do from the cloud

- **Create the GitHub repository.** The GitHub App this session runs under lacks `administration:write`; a 403 came back on `create_repository`. Jared created the empty shell manually at github.com/new (owner `jeb2-spec`, name `oath`, private, empty).
- **Set up the local dev environment.** That happens on Jared's PC when he arrives. `NEXT.md` Phase 1 T.1 is the first step.
- **Wire the twelve invariant gates.** They are agreed and named in INVARIANTS.md; the tools that enforce them are Phase 1 work.

## The through-line

This is a young repository built on old discipline. The Vera and errata records are its family; when in doubt, read from them. When you finish a step, update this file in the same commit. Its freshness is more valuable than any polish elsewhere.

Read the [Charter](../../CHARTER.md) before you start. If you cannot recall the four vows, come back.
