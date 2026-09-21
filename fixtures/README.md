# fixtures/

Fictional data used to test the pipeline without touching real filings, real officeholders, or real sources.

At the founding, this directory contains only this README. Fixtures land in [NEXT.md](../NEXT.md) Phase 2 D.2, alongside the first Signal.

## Rules

- **Every fixture is obviously fictional.** Names are placeholder patterns (`Example Person`, `Test Officeholder A`), never a real person's name or a name that could plausibly be one.
- **Every fixture is marked.** Top-level `fixture_only: true` on every row. Any downstream tool that produces user-facing output from a fixture is required to display the fictional marker.
- **Fixtures never enter the canonical NDJSON.** They live only under `fixtures/` and are read only by tests. A test that leaks a fixture into `data/` is a test that fails.
- **Fixtures are versioned.** A schema change that would invalidate a fixture requires an updated fixture in the same commit.

## Planned layout

```
fixtures/
├── officeholders/
│   └── example-person.json
├── filings/
│   └── example-ptr-late.json
├── holdings/
│   └── example-holding.json
├── transactions/
│   └── example-transaction.json
├── signals/
│   └── stock-act-late-ptr/
│       ├── input.json          the fixture rows the Signal reads
│       └── expected.json       the Finding(s) the Signal must produce
└── tools/
    └── verify/
        ├── clean-db.sql        a known-good tiny record
        ├── clean-db.digest     the expected digest
        └── tampered-db.sql     a record with one row altered
```

## Why fictional

Signals should be tested against inputs that isolate the criterion the Signal exists to detect. Real filings carry adjacent conditions and confounders that are useful to encounter in ingest but not in a unit test. Fictional fixtures let the test suite say *this Signal fires on exactly this pattern* without accidentally also saying *this Signal fires on this officeholder*.

Every fixture pair is a small commitment to a specific interpretation of the criterion. When the interpretation changes, the fixture changes and the Signal version bumps.
