# data/

The canonical store of the register, and the caches around it.

At the founding, this directory was empty except for this README. Since Phase 1 T.2 it holds `meta.json`, the sealed record of the build: the digest `tools/verify.py` recomputes, the row counts, the disclosures the seal covers, and the anchor state.

The register stopped being empty on 2026-09-22, when the House index layer landed: 441 seats, 439 officeholders and 1,097 filings, each citing the Clerk document it came from, and no transactions, because a filing index carries no transaction dates. On 2026-09-23 the document layer followed: the transaction reports behind the index, read and written to `transactions.ndjson`. The current counts live in `meta.json`, the one place they are kept, and the seal covers them. No Signal is defined, so nothing here can fire one, and that is the register working as designed.

`data/rejected/` is part of the record, not a scratch directory. It is sealed with everything else, because what the adapter refused and why is as much a fact about the build as what it accepted. Its files are named for the captures they came from, so an unchanged source rebuilds an unchanged tree; earlier captures' rejections live in git history.

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
├── cache/                       # gitignored: raw retrieved documents
└── raw/                         # gitignored: adapter working directory
```

## Provenance

- **Every row carries a `source`** with a URL and a retrieval timestamp.
- **The Seal covers the canonical NDJSON and `meta.json`.** It does not cover `cache/` or `raw/` (transient).
- **The Anchor witnesses the Seal.** OpenTimestamps against the Bitcoin blockchain.

## Rules

- **Never edit the NDJSON files by hand.** All writes go through adapters or through Signal producers. A hand-edit that survives is a break in reproducibility.
- **Never commit `cache/` or `raw/`.** They are working directories; their contents can be arbitrarily large and are rebuildable from the primary sources.
- **The SQLite file `oath.db` is a convenience.** The canonical store is the NDJSON. If the two disagree, the NDJSON wins and the SQLite is regenerated.
