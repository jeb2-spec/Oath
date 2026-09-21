# Architecture

Oath is designed as three layers over one canonical store, so that four groups of contributors — data-source authors, signal authors, jurisdictional authors, tooling authors — can extend the project without stepping on each other. This file documents the shape at the founding. It will evolve as real data lands and constraints become concrete.

## The layers

```
    ┌──────────────────────────────────────────────┐
    │  Surfaces                                    │
    │  README, per-officeholder pages, API, CSV    │
    │  Signal definitions rendered as docs         │
    │  Findings rendered as descriptions           │
    └──────────────────────────────────────────────┘
                       ▲
    ┌──────────────────┴───────────────────────────┐
    │  Signals & Findings                          │
    │  Signal = definition + reference impl        │
    │  Finding = signal firing against a record    │
    └──────────────────────────────────────────────┘
                       ▲
    ┌──────────────────┴───────────────────────────┐
    │  Canonical store                             │
    │  Officeholder / Office / Filing / Holding /  │
    │  Transaction — schema-typed, sealed          │
    └──────────────────────────────────────────────┘
                       ▲
    ┌──────────────────┴───────────────────────────┐
    │  Adapters                                    │
    │  One per primary source (House FD, Senate    │
    │  FDR, OGE 278e, FEC, LDA, state ethics ...)  │
    │  Type at the boundary. Retry, throttle,      │
    │  cache raw responses locally (gitignored).   │
    └──────────────────────────────────────────────┘
                       ▲
    ┌──────────────────┴───────────────────────────┐
    │  Primary sources                             │
    │  (public, cited, rate-respected)             │
    └──────────────────────────────────────────────┘
```

Each layer knows only about the layer directly below it. Surfaces do not know about adapters. Signals do not know about primary sources. This is what makes the project extensible without a coordination cost.

## The canonical store

**Format.** The store's canonical form is a set of newline-delimited JSON files, one per entity type, plus a `meta.json` with the build's provenance. This gives:

- **Trivial diffing.** A pull request is readable.
- **Byte-stable serialisation.** The Seal is a SHA-256 over the concatenated files in a defined byte-order (documented in `tools/verify.py`).
- **No database required to read.** A stranger with `cat` and `jq` can read the record.

**Database backing.** For query performance the store is loaded into SQLite (`data/oath.db`), rebuildable from the canonical NDJSON. The SQLite file may be committed for convenience, but the source of truth is the NDJSON.

## Adapters

An adapter is a script (or module) that:

1. Retrieves rows from one primary source.
2. Normalises them to the schemas in `schemas/`.
3. Validates each row at the boundary.
4. Writes accepted rows to the canonical NDJSON.
5. Writes rejected rows to `data/rejected/<source>/<date>.ndjson` with the validation error.
6. Logs its run to `data/adapter-runs/` with timestamps, counts, and any HTTP status errors encountered.

An adapter is registered in `SOURCES.md`. Its ingest cadence is documented; its throttling and rate-limit posture are respected; its known gaps are stated.

## Signals

A Signal has two files:

- **Definition** — `docs/signals/<slug>.md` in the template documented at `docs/signals/README.md`. Human-readable. The definition is the artefact a reader argues with.
- **Reference implementation** — `src/signals/<slug>.ts` (or `.py`). A pure function that reads the schemas the definition names and returns Finding rows. Tests against fixtures under `fixtures/`.

A Signal is *pure*: it does not fetch, it does not write side-effects, it does not touch the network. This is what makes findings regenerable.

## Findings

Findings are produced by running Signals against the current store. They are:

- Serialised to `data/findings.ndjson`.
- Regenerable byte-identically given the same store and the same Signal version.
- Rendered in surfaces (README, per-officeholder pages, API) with the frame from `METHODOLOGY.md` §4.

A Finding never edits a prior Finding; a corrected Finding supersedes the old one, both rows remain in the file.

## Sealing and anchoring

The Seal is a SHA-256 digest computed over the canonical NDJSON files plus `meta.json`, in a defined byte-order documented in `tools/verify.py`. It is emitted by the build and printed by the verifier.

The Anchor is an OpenTimestamps proof against the Bitcoin blockchain, stored in `data/anchors/<build-hash>.ots`, in the manner of the sibling *errata* project. Anchor state (confirmed, pending, owed) is tracked in `ANCHORS.md` (planned).

## Reference language choice

The reference implementation is TypeScript + Node 20 for adapters and Signals, Python 3.11 for the verifier and CLI tools. These choices reflect the surrounding *Vera* and *ellebee* ecosystems and Python's suitability for short standard-library tooling. They are conveniences, not constraints; ports of Signals to other languages are welcome provided they produce byte-identical Findings on the same fixtures.

## Extensibility points

- **Add a source** → add an adapter, register in `SOURCES.md`.
- **Add a signal** → add a definition and a reference implementation, cite the Standard.
- **Add a jurisdiction** → add the state or locality's Standards, its sources, its officeholders.
- **Add a surface** → read the canonical store or the findings file. Never modify either.

## What this architecture does not include

- No user database. There are no accounts.
- No moderation surface. There is no comment system on findings.
- No feedback endpoint from findings back into the store. A correction is a pull request.
- No API rate-limiting middleware, because there is no API-as-service yet. If one lands, it lives in a separate surface layer that reads the store; the store itself remains file-based.

The absence of these is a feature at day zero. When any of them becomes needed, the addition is documented here in the same commit.
