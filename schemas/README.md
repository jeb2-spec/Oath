# Schemas

The data model of Oath. Every row that enters the register is validated against one of these schemas at ingest. A row that does not conform is rejected at the adapter with a message that names the field and the rule.

## Files

- `officeholder.schema.json`. a natural person occupying an elective Office.
- `office.schema.json`. a specific elective position with a jurisdiction and a term.
- `filing.schema.json`. a single dated instance of a required Disclosure.
- `holding.schema.json`. a reported asset attributed to an Officeholder or a covered relative.
- `transaction.schema.json`. a reported purchase, sale, or exchange affecting a Holding.
- `signal.schema.json`. a versioned, defined condition observable in the record.
- `finding.schema.json`. a specific instance of a Signal firing against a specific Officeholder.

## Conventions

- **Draft.** JSON Schema draft-2020-12.
- **`$id`.** Every schema declares an `$id` under `https://oath.jeb2-spec.dev/schemas/<name>/v<n>.json`. Version bumps produce a new `$id`.
- **Optional fields.** Declared with `type: [T, "null"]` and no entry in `required`. Consumers must handle the absence rather than assume a value.
- **Enums.** Use enums for form types, jurisdictions, and party identifiers. The enum values are the source-side spellings, not project synonyms.
- **IDs.** Every entity carries an `id` in the schema-defined format. IDs are stable across builds; a change of ID is a break and produces a supersession row.

## Identifier scheme (decided 2026-09-22, NEXT.md D.3)

- **Officeholder.** `oh:<country>:<chamber>:<stable-person-key>`. e.g. `oh:us:house:a000055`.
- **Office.** `of:<country>:<seat-slug>:<term-year>`. e.g. `of:us:house-al04:2025`.
- **Filing.** `fl:<source>:<source-form-code>:<source-id>`. e.g. `fl:house-clerk:P:20032062`.
- **Signal.** `sg:<slug>:v<n>`. e.g. `sg:stock-act-late-ptr:v1`.
- **Finding.** `fn:<signal-id>:<filing-id>`, e.g. `fn:sg:stock-act-late-ptr:v1:fl:house-clerk:P:20032062`; a correction appends `:c<n>` (docs/signals/README.md, Corrections). The founding convention was `fn:<signal-id>:<officeholder-id>:<yyyy-mm-dd>`, and it was replaced before any Finding existed, on 2026-09-26: a Finding describes one report, and in the 2025 index four officeholders filed two reports on the same day, so a person and a date do not name one report. The report's own identifier does, and the row still names the officeholder.

**Two fields added on 2026-09-26, both optional, with the rows migrated in the same commit.** `officeholder.sworn_at`, the day the primary source records the person as sworn into the first Office listed, as data rather than the prose note it was, because a Signal that asks whether a rule applied on a date must not parse prose; the House rows were migrated from the adapter's own note, which the adapter wrote from the same roster field, and the adapter now writes both. `finding.evidence`, what the record shows and what the Signal computed from it, in the Signal's own terms, so a reader holding one row can check the Finding against the filing without running code. No `$id` changed: both are additive, and no Finding existed before them.

**The person key never carries the office.** The founding draft put the district in the officeholder identifier. Real data killed it inside an hour: two sitting members hold each other's former districts across the Clerk's own two files, and a district-bearing identifier would have made each of them two different people, or forced a supersession for an event that changed nothing about who they are. The key is the Biographical Directory identifier, lowercased, which is the identifier the field already agrees on and which the Clerk publishes for every member.

**The seat does carry the office**, because an Office *is* a seat and a term. A member who changes district gets a second office row and keeps one officeholder identifier, which is the correct shape.

The founding examples here named a sitting Senator and a real district. They are replaced with rows the register actually holds.

## How to add or change a schema

By pull request. The template requires:

1. The reason for the change (a use case a Signal or an adapter needs).
2. The migration path for existing rows (or a note that no rows exist yet).
3. A worked example in the schema's `examples` field.
4. Updates to `schemas/README.md` and any adapter or Signal that reads the schema.

A schema change is not a small thing. Prefer additive change (new optional fields) over breaking change; when a breaking change is required, bump the schema `$id` version and migrate deliberately.
