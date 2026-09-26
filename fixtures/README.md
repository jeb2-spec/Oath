# fixtures/

Test inputs whose correct answer is known in advance. Nothing here is a person, and nothing here ever enters the register.

At the founding, this directory contained only this README. Since Phase 1 it also holds the cross-reference gate's cases, and since 2026-09-26 the first Signal's: [`stock-act-late-ptr/cases.json`](stock-act-late-ptr/cases.json), twenty-six cases, each a report, its rows and its officeholder's swearing-in as placeholders, with every row's expected result and the reason written beside it. Both implementations of the Signal are tested against the file, and neither wrote it. On its first run it caught its own author: two cases had forgotten the Signal's own swearing-in rule, and the implementation declined to evaluate them, correctly.

## Rules

- **No invented person, and no real one.** Earlier drafts of the course planned a hand-typed fictional officeholder. That is cut, set by the maintainer on 2026-09-22. Where a schema requires an identifier, use a reserved placeholder (`oh:us:example:example`, `example.com`, per RFC 2606), which is visibly not a person and makes no claim about one.
- **Fixtures never enter the canonical NDJSON.** They live only under `fixtures/` and are read only by tests. A test that leaks a fixture into `data/` is a test that fails.
- **Every fixture carries its expected answer.** A case without a written expectation is not a fixture; it is a sample.
- **Fixtures are versioned.** A schema change that would invalidate a fixture requires an updated fixture in the same commit.

## Layout

```
fixtures/
├── stock-act-late-ptr/
│   └── cases.json              each case: placeholder rows, and for every row and the
│                               report, the expected answer and why (landed 2026-09-26)
├── tools/
│   ├── check-crossrefs/        landed in Phase 1: good/ and bad/ trees
│   └── verify/
│       ├── clean-db.sql        a known-good tiny record
│       ├── clean-db.digest     the expected digest
│       └── tampered-db.sql     a record with one row altered
```

## Why not test against real filings

A test needs an input whose correct answer is known before the tool runs. Real filings do not come with an answer key; producing one is the reason the tool is being built. Run a Signal against real data and it returns something plausible whether the logic is right or wrong, and there is nothing to compare it to.

The cases that matter are the ones at the edges of the rule, and the record almost never hands you a clean one. The STOCK Act sets two prongs, thirty days from notification and forty-five days from the transaction, whichever falls earlier. The day the answer changes, the prong that binds first, a notification date that is absent, a date that does not parse: those are arithmetic, and arithmetic can be stated exactly. Getting the boundary wrong against a real filing means publishing a false claim about a real person, and no amount of care at ingest catches a logic error that ingest cannot see.

So the fixtures here are dates and amounts, and the register holds only what a primary source published.
