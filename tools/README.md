# tools/

The verification tooling that turns the invariants in [INVARIANTS.md](../INVARIANTS.md) from agreed rules into mechanical gates.

At the founding, this directory was empty except for this README. Each planned tool below lands in [NEXT.md](../NEXT.md) Phase 1.

## Landed tools

| Tool | Rule | Job |
| --- | --- | --- |
| `verify.py` | §9; RUBRIC gate 4 | Recompute the register's seal and compare it to `data/meta.json`. The seal is one SHA-256 over a sorted manifest of every `data/**/*.ndjson`, the eleven doctrine documents, and `data/meta.json` without its digest as canonical JSON; the rule is written at the top of the file so a stranger can rebuild it with `sha256sum` and `sort`. Prints OK or FAIL and *Integrity is not accuracy* on every run; `--manifest` prints the manifest. 151 lines. |
| `seal.py` | §9 | The build's last step: writes the build id, the build time it is given (never the clock), the row counts, and the digest into `data/meta.json`. Two runs from the same inputs produce the same bytes. Any change to a sealed file, doctrine included, needs a re-seal in the same commit; the digest change is the loudness the meta-invariant wants. |
| `tamper-test.py` | §9; RUBRIC gate 4 | Proves the verifier is not decorative: alters one character of a disclosure in a throwaway copy and requires FAIL; runs on the real tree and requires OK; recomputes the digest with code that imports nothing from the verifier and requires equality. |
| `validate-schemas.py` | §2 §3 §4 §6 | Meta-checks every schema in `schemas/` against the subset of JSON Schema draft 2020-12 this register uses (any other keyword fails loudly), validates each schema's own examples, and validates every row of every canonical NDJSON file under `data/` against its schema, naming the file, line, field path, and rule. Formats are assertions: a `date-time` must be UTC. Standard library. |
| `lint-verdict-language.py` | §1 | Scans every user-facing surface (root Markdown, `.github/`, `docs/`, `src/`, `fixtures/`, `templates/`, `data/*.ndjson`) for the blacklist in any inflection. The frame sentence is always allowed; every other hit needs an entry in `verdict-lint.allowlist` (`path | context | reason`), and a stale entry fails too. `.claude/` and `docs/related-work/` are not scanned, and the tool says why. |
| `check-crossrefs.py` | COUNCIL.md §5 mode 7 | Resolve every section reference (`INVARIANTS.md §13`, `Invariant §7`, `Vow V`, `Rubric gate 4`, `PIPELINE.md Stage 7`), every in-file anchor, and every relative Markdown link in the tracked `.md` files to a heading or file that exists. Ignores legal citations and fenced code. Fixtures under `fixtures/tools/check-crossrefs/`; tests in `test_check_crossrefs.py`. Landed after the first Council session found eight references in the doctrine that had been wrong since the founding. It would have caught two of them (a dead anchor, a section that does not exist); the other six cited a section that exists but is the wrong one, which no structural check can see. That class stays a reading discipline until a citation convention makes it mechanical. |

## Planned tools

| Tool | Invariant | Job |
| --- | --- | --- |
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

## Session start

`scripts/oath-doctor.py` is not a gate; it is the read-back a session runs before it starts. It checks that the memory chain is whole and in order, that the deeper ground beside this repository matches `origin/main`, prints the five vows from CHARTER.md, lists every gate INVARIANTS.md names as present or planned and runs the present ones, compares the branch to `origin/main`, and checks the toolchain floor. Any red exits non-zero; a warning never does.

## Continuous integration

`.github/workflows/verify.yml` runs on every push and every pull request, on Python 3.11 and Node 20, the reference runtimes: Ruff (check and format), Pytest, `verify.py`, `tamper-test.py`, `validate-schemas.py`, `lint-verdict-language.py`, `check-crossrefs.py` once its pull request has merged, a parse of every generated JSON file, Biome, and Vitest. A gate that fails fails the build. A gate whose tool is not on the branch warns loudly rather than passing quietly. The seal was first computed on Windows; the Linux job recomputing the same digest is the cross-platform check that `.gitattributes` and LF-only writes are working.

## Convention

- Python tools are standard-library only unless a specific tool documents a required dependency, and the requirement is minimal.
- TypeScript/JS tools are Node 20+ with the smallest useful footprint.
- Every tool exits non-zero on failure and prints a human-readable diagnosis.
- Every tool has a `--help` that names its invariant, the specific failure it catches, and one example of a failing input.
- Every tool has a corresponding fixture test under `fixtures/tools/<tool>/`, or builds its fixture in a temporary directory inside its `test_*.py` when the fixture is a whole register.
