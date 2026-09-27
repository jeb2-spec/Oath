# data/

The canonical store of the register, and the caches around it.

At the founding, this directory was empty except for this README. Since Phase 1 T.2 it holds `meta.json`, the sealed record of the build: the digest `tools/verify.py` recomputes, the row counts, the disclosures the seal covers, and the anchor state.

The register stopped being empty on 2026-09-22, when the House index layer landed: 441 seats, 439 officeholders and 1,097 filings, each citing the Clerk document it came from, and no transactions, because a filing index carries no transaction dates. On 2026-09-23 the document layer followed: the transaction reports behind the index, read and written to `transactions.ndjson`. The current counts live in `meta.json`, the one place they are kept, and the seal covers them. No Signal is defined, so nothing here can fire one, and that is the register working as designed.

`data/rejected/` is part of the record, not a scratch directory. It is sealed with everything else, because what the adapter refused and why is as much a fact about the build as what it accepted. Its files are named for the captures they came from, so an unchanged source rebuilds an unchanged tree; earlier captures' rejections live in git history.

`data/changes.ndjson` holds what a later capture showed about a row the register had already published, and what a person corrected, one change per line, each citing the capture that shows it. The published row stays as published beside it (INVARIANTS §14). The file only grows at its end, byte for byte, and `tools/check-removals.py` holds it to that.

`data/captures/sha256/` keeps the bytes of the two captures the adapter fetches every week, the Clerk's roster and a filing year's index, wherever a change row or a closed year cites one, each named by its SHA-256 and never changed, so a change about a person can be checked from the repository alone once the source serves something else. Every other evidence a correction cites is cited by its SHA-256 alone, which a reader checks against a copy they hold. It keeps no filed document. A document can carry the names of private people (a spouse, a dependent child, a joint owner), and a copy kept here would outlast the Clerk's withdrawal or redaction of it, with the §14 gate refusing its removal (the Council's third reading of S.1b (Seat B), whose scope the fifth reading corrected; EVIDENCE.md §7 and INVARIANTS.md §16 still say the register may keep a filing's bytes, and NEXT.md D.4 carries the amendment). So a document a later read finds the Clerk serving as a different file is named by both files' SHA-256 on its change row, with which rows read otherwise and in which facts, never what they say; a correction citing a document cites it by URL, time and SHA-256; and a correction of a filer's own text keeps the SHA-256 of what it said, not the text. The gate fails a kept PDF. It is the one part of the retrieved bytes the register commits: the roster the Clerk serves today is not the roster it served when a Member was last listed.

`data/adapter-runs/` holds the current build's one-line run record per adapter: which captures it read, their hashes and retrieval times, the hash of any adjudication file that shaped it, and the counts. It is named for the same capture key as the set-aside file, so the two can never be told apart wrongly, and the record of an earlier capture lives in git history with the build it sealed. Sealed too. The provenance of a build lives inside the build.

## Layout (planned)

```
data/
├── officeholders.ndjson         # canonical: one Officeholder per line
├── offices.ndjson               # canonical: one Office per line
├── filings.ndjson               # canonical: one Filing per line
├── holdings.ndjson              # canonical: one Holding per line
├── transactions.ndjson          # canonical: one Transaction per line
├── findings.ndjson              # produced: one Finding per line
├── meta.json                    # build provenance and digest
├── oath.db                      # SQLite mirror (rebuildable from NDJSON)
├── anchors/
│   └── <build-hash>.ots         # OpenTimestamps proof per sealed build
├── adapter-runs/
│   └── <adapter>-<date>.log     # per-run telemetry
├── rejected/
│   └── <adapter>/<date>.ndjson  # rows the adapter's validation rejected
├── changes.ndjson               # what later captures showed, and corrections, one per line
├── captures/
│   ├── sha256/<sha256>.<ext>    # the bytes a change row cites, kept, never changed
│   └── <filing-id>/             # the evidence bundle, INVARIANTS §16 (planned)
├── cache/                       # gitignored: raw retrieved documents
└── raw/                         # gitignored: adapter working directory
```

## Provenance

- **Every row carries a `source`** with a URL and a retrieval timestamp.
- **The Seal covers the canonical NDJSON and `meta.json`.** It does not cover `cache/` or `raw/` (transient).
- **The Anchor witnesses the Seal.** OpenTimestamps against the Bitcoin blockchain.

## Rules

- **Never edit the NDJSON files by hand.** All writes go through adapters or through Signal producers. A hand-edit that survives is a break in reproducibility.
- **Never commit `cache/` or `raw/`.** They are working directories; their contents can be arbitrarily large. They are not rebuildable in general: the Clerk serves today's roster and a growing index, not the bytes of an earlier retrieval, which is why the captures a change row cites are kept in `captures/sha256/`. The rest of the retrieved bytes are named by their hash on the rows that came from them, and are not kept (INVARIANTS §16, the evidence bundle, is not yet built).
- **The SQLite file `oath.db` is a convenience.** The canonical store is the NDJSON. If the two disagree, the NDJSON wins and the SQLite is regenerated.
