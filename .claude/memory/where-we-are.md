---
name: where-we-are
description: "The current state of Oath. Read first. Updated in the same commit that changes it, or deleted."
metadata:
  node_type: memory
  type: state
---

# Where we are. Oath

*Last updated: 2026-09-21, at the founding.*

## The state

**Day zero.** The repository exists. It has a prospectus, standards, methodology, limitations, sources, schemas, an architecture note, a memory seed, and a course. No data has been ingested. No signal has been defined. No finding has been published.

The founding was drafted in a cloud session in the CoworkVM environment. Everything committed here should be reproducible from `NEXT.md` on a local machine.

## What is real

- `README.md`. the prospectus in the errata register.
- `STANDARDS.md`. the legal frameworks the project measures against.
- `METHODOLOGY.md`. how sources, types, signals, findings, seals and anchors work.
- `LIMITATIONS.md`. what the project cannot do, in the order a careful reader would raise them.
- `SOURCES.md`. the primary sources planned (no adapters implemented yet).
- `NEXT.md`. the course for the first sessions after arrival.
- `CLAUDE.md`. the working stance.
- `LICENSE`. dual CC BY 4.0 (content) + MIT (code).
- `schemas/*.json`. six JSON Schemas (Officeholder, Office, Filing, Holding, Transaction, Signal, Finding), version 0.
- `docs/architecture.md`. the layered shape.
- `docs/signals/README.md`. the Signal template. No signals defined yet.
- `data/README.md`. planned layout of the canonical store. Directory otherwise empty.
- `src/README.md`. planned layout of adapters, signals, surfaces. Directory otherwise empty.
- `.github/pull_request_template.md`. with the review checklists.

## What is not real yet

- No adapter is implemented. No source has been read.
- No signal is defined. `docs/signals/` contains only the template.
- No verifier (`tools/verify.py`), no tamper-test, no schema validator, no CI workflow.
- No `package.json`, no `pyproject.toml`, no runtime dependency pinning.
- No fixtures.
- No `ANCHORS.md`. There is nothing to anchor.

## The immediate next moves

Per `NEXT.md`:

1. **T.1 Runtimes.** `package.json` + `pyproject.toml`.
2. **T.2 The verifier, empty.** Standard-library Python, ships with a tamper-test companion.
3. **T.3 CI.** GitHub Actions workflow running the verifier and tamper-test on every push.
4. **T.4 Schema validator.**
5. **D.1 Complete the schemas** (enums, examples, walkthroughs).
6. **D.2 Fixture data**, one hand-typed, obviously-fictional officeholder.
7. **D.3 Identifiers**, confirm or replace the proposed ID scheme.
8. **S.1–S.4**, the first Signal (recommended `stock-act-late-ptr`), end to end.
9. **I.1–I.4**, the first ingest, one officeholder, one calendar year, then extend.

## Standing decisions

- **Repository visibility:** private at the founding. Jared flips public when he is ready.
- **Branch:** work continues on `claude/us-officials-financial-oversight-hz36kr` outside main, per the standing per-repo branch convention. The founding commits landed on that branch (or on main via the founder, depending on the setup path taken).
- **Reference runtimes:** Node 20 + TypeScript for adapters and signals; Python 3.11 for tooling and the verifier.
- **Data format:** newline-delimited JSON as canonical; SQLite as convenience mirror.
- **License:** CC BY 4.0 for content; MIT for code.
- **Attribution convention:** `Co-Authored-By: Claude ...` per the Vera/errata convention.

## What I could not do from the cloud

- **Create the GitHub repository.** The GitHub App this session runs under lacks `administration:write`; a 403 came back on `create_repository`. Jared created the empty shell manually at github.com/new (owner `jeb2-spec`, name `oath`, private, empty).
- **Set up the local dev environment.** That happens on Jared's PC when he arrives. `NEXT.md` T.1 is the first step.

## The through-line

This is a young repository built on old discipline. The Vera and errata records are its family; when in doubt, read from them. When you finish a step, update this file in the same commit. Its freshness is more valuable than any polish elsewhere.
