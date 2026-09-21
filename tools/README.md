# tools/

The verification tooling that turns the invariants in [INVARIANTS.md](../INVARIANTS.md) from agreed rules into mechanical gates.

At the founding, this directory is empty except for this README. Each tool below lands in [NEXT.md](../NEXT.md) Phase 1.

## Planned tools

| Tool | Invariant | Job |
| --- | --- | --- |
| `verify.py` | §9 | Recompute the register's digest, print OK or FAIL, print *Integrity is not accuracy* every run. Standard-library Python 3.11. |
| `tamper-test.py` | §9 | Prove the verifier rejects a changed record. Prove it accepts the shipped file. Recompute the digest from the plain-text dump using a parser that shares no code with the builder. |
| `validate-schemas.py` | §2 §3 §4 §6 | Walk `schemas/` and validate every row of the canonical NDJSON against its schema. Fail on any invalid row. |
| `lint-verdict-language.py` | §1 | Scan Signal definitions, rendered Findings, templates, and every user-facing Markdown file for the blacklist. Ships with an `.allowlist` for cases the blacklist matches but the context clears. |
| `lint-frame-presence.py` | §7 | Read every rendered officeholder-facing page and require the presence-is-not-proof frame verbatim in the header region. |
| `lint-no-ranking.py` | §13 | Scan every rendered index and summary page for elements sorted by a per-officeholder derived score. |
| `check-aggregator-sole.py` | §5 | Walk every Finding's `producing_filings` and fail if all sources resolved are marked `source_type: aggregator`. |
| `check-signal-versions.py` | §11 | For each Signal file in the diff, walk history and fail if criteria/inputs/standard changed without a version bump. |
| `check-supersessions.py` | §12 §14 | Walk the supersession chain and fail on orphans or in-place edits. |
| `check-removals.py` | §14 | Fail on any row that disappears between builds without a supersession, and on any supersession row without a primary-source citation. |
| `check-evidence-bundle.py` | §16 | For every filing, require a `data/captures/<filing-id>/` bundle with matching hash, an OpenTimestamps proof, and at least one confirmed external witness. |
| `check-coi-disclosure.py` | §15 | Require the `## Conflict of interest disclosure` heading in the PR body with a non-empty statement below it. |
| `check-subject-scope.py` | SUBJECTS §4 | Fail if any officeholder row has no matching office, or if any office is in a category not in SUBJECTS.md §2. |
| `highlight-charter-change.py` | §17 (meta) | Diff CHARTER, RUBRIC, INVARIANTS, BYLAWS, COUNCIL against `main`; emit a highlighted CI notice on any change; require the maintainer's explicit review comment. |

## The strike-mark tool

- `strike-mark.mjs` strikes the wax-seal-in-guilloche Oath mark from the build's digest and from per-officeholder identifiers, per [ECOSYSTEM.md §2](../ECOSYSTEM.md).
- `check-mark.mjs` strikes the mark against a range of digests and confirms geometry stays legible.

Both land in Phase 3 with the first per-officeholder page.

## Convention

- Python tools are standard-library only unless a specific tool documents a required dependency, and the requirement is minimal.
- TypeScript/JS tools are Node 20+ with the smallest useful footprint.
- Every tool exits non-zero on failure and prints a human-readable diagnosis.
- Every tool has a `--help` that names its invariant, the specific failure it catches, and one example of a failing input.
- Every tool has a corresponding fixture test under `fixtures/tools/<tool>/`.
