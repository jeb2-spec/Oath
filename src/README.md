# src/

Reference implementations. TypeScript for adapters and Signals; Python for the verifier and CLI tooling under `scripts/` and `tools/`.

At the founding, this directory is empty except for this README.

## Layout (planned)

```
src/
├── adapters/            # one per primary source
│   ├── house-fd/
│   ├── senate-fdr/
│   ├── oge-278e/
│   ├── fec/
│   └── lda/
├── signals/             # one per Signal, pure functions
│   └── stock-act-late-ptr.ts
├── shared/              # schemas types (generated), validation helpers
└── surfaces/            # readers of the store (page renderers, CSV export)
```

## Conventions

- **Adapters are cron-friendly.** Each exports a single `run()` entrypoint that reads env vars for credentials, retrieves rows, validates at the boundary, and writes to the canonical NDJSON.
- **Signals are pure.** They read the schemas the definition names and return Finding rows. No network. No I/O. Tests against fixtures under `fixtures/`.
- **Surfaces are read-only.** They read the canonical NDJSON (or the SQLite mirror) and render. They never write.

## Generated types

TypeScript types are generated from the JSON Schemas by `scripts/generate-types.ts`. Regenerate on any schema change:

```bash
npm run generate-types
```

The generated files live under `src/shared/generated/` and are gitignored, because they are derivable.

## Testing

- **Vitest** for TypeScript unit tests.
- **Pytest** for Python.
- **Schema validation** runs as part of every test; a test that produces an invalid row fails.
- **Signal tests** are always against fixtures under `fixtures/`. Never against live data.
