# Invariants

The rules that make the [Charter](CHARTER.md) enforceable when nobody is watching. Each rule below is a mechanical gate: a schema check, a lint, a test, or a CI step. Each names the gate that enforces it. A rule without a gate is a hope; every rule in this file has a gate.

Where a gate is marked *(planned)*, the invariant is agreed at the founding and the gate lands as part of the tooling foundation in [NEXT.md](NEXT.md) §T. Until the gate exists, the rule holds by discipline; the moment it exists, the rule holds by design.

---

## §1. Verdict language is forbidden on any user-facing surface.

**Blacklist (v0):** *guilty, corrupt, unethical, criminal, crook, disgrace, disgraceful, shameful, should resign, broke the law, broke laws, dishonest, dishonesty, sleazy, sleaze, dirty, tainted, illegal conduct, illegal act, wrongdoing, malfeasance, misconduct.*

**Gate:** `tools/lint-verdict-language.py` *(planned)*. Runs on every Signal definition, every rendered Finding, and every user-facing template (README examples included). CI fails on any hit. False positives are added to a `verdict-lint.allowlist` file with the surrounding context and a one-line reason.

**Change process:** adding a word requires one approver on the pull request. Removing a word requires two approvers and a written justification, and the PR is highlighted by [§13](#13-the-meta-invariant) below.

## §2. Every Signal cites a Standard.

**Gate:** JSON Schema validation of `schemas/signal.schema.json` requires `standard.id` (must reference an id in STANDARDS.md) and `standard.citation` (the display string). `tools/validate-schemas.py` *(planned)* runs on every push.

## §3. Every Finding names its producing filings.

**Gate:** JSON Schema validation of `schemas/finding.schema.json` requires `producing_filings` with `minItems: 1`. Enforced at ingest and in CI.

## §4. Every Filing carries a Source URL and a retrieval timestamp.

**Gate:** JSON Schema validation of `schemas/filing.schema.json` requires `source.url` (must be a URL) and `source.retrieved_at` (must be ISO-8601 UTC). Rejected rows go to `data/rejected/` with the validation error; they are never silently dropped.

## §5. No aggregator is the sole source for a Finding.

**Gate:** `tools/check-aggregator-sole.py` *(planned)*. Walks every Finding's `producing_filings`, resolves each filing's source registration in SOURCES.md, and fails if every source resolved is registered with `source_type: aggregator`. Aggregators must be cited beside a primary; they are never in place of one.

## §6. Every Signal declares what it does not say.

**Gate:** `schemas/signal.schema.json` requires a non-empty `not_saying` string. A blank or one-word field fails schema validation.

The point of this invariant is that a Signal author has to actively name the interpretations the Signal does not support before the Signal can publish. It forces the author to stand between the reader and the wrong conclusion.

## §7. The frame appears on every officeholder page.

**Gate:** `tools/lint-frame-presence.py` *(planned)*. Reads every rendered officeholder template output and requires the sentence *"Presence in the register is not evidence of wrongdoing"* to appear verbatim (case-insensitive, punctuation-insensitive) in the page's header region.

## §8. Signal version bumps require adversarial review.

**Gate:** the pull request template's *Adversarial second reading requested and recorded* checkbox is required for any PR that touches `docs/signals/*.md` or `src/signals/*`. A GitHub Actions workflow rejects the merge if the checkbox is not marked and a review comment is not linked.

## §9. The Seal covers the disclosures.

**Gate:** `tools/verify.py` *(planned)* recomputes the digest including `meta.json` and the `documents` section of the canonical store. The tamper-test companion proves the verifier rejects a `meta.json` alteration on a throwaway copy. This is the specific failure mode that once bit errata; the gate exists so it does not bite Oath.

## §10. No secret ever lands in git.

**Gate:** `tools/scan-secrets.py` *(planned)*. Runs as a pre-commit hook and in CI. Scans for the common secret patterns (API keys, AWS credentials, private keys, tokens). Ships a `.secrets.baseline` for known false positives. A hit blocks the commit or the merge.

## §11. Silent redefinition of a Signal is prohibited.

**Gate:** `tools/check-signal-versions.py` *(planned)*. For every Signal file in the diff, walks git history for the previous state of the same `slug` and fails if the current file's `(criteria, inputs, standard.id)` tuple differs from the previous file's without a bump to `version`. If a Signal author wants to change a criterion, they must produce a new version; the old version stays readable.

## §12. The corrections trail is public.

**Gate:** any correction to a shipped Finding produces a new Finding row with `superseded_by` set on the old row. Neither row is deleted. `tools/check-supersessions.py` *(planned)* walks the chain and fails if any superseded row is missing its replacement, or if any Finding has been silently removed from the register between builds.

The corrections themselves live in the sibling [errata](https://github.com/jeb2-spec/errata) project, which is the family's canonical corrections record.

## §13. The meta-invariant.

**No invariant above may be removed, softened, or weakened without a pull request that:**

1. **Names** which gate is being removed or weakened.
2. **Explains** the reason, including what problem the current gate is causing and what the change is expected to fix.
3. **Is approved** by the repository maintainer.

**Gate:** `tools/highlight-charter-change.py` *(planned)*. On every push, diff `CHARTER.md`, `RUBRIC.md`, and `INVARIANTS.md` against `main`. If any of the three files has changed, emit a highlighted CI notice and require the maintainer's explicit review comment before the PR can merge.

Silent softening of the antidrift core is not possible under this rule. Loud softening is possible, and is sometimes the honest thing; the point of the rule is that the loudness cannot be avoided.

---

## Why these are twelve and not more

Every rule above is one a stranger can verify by running one command against this repository. Each catches a specific failure that this project's family has already suffered, or that its neighbours have suffered publicly. This is not a wish list. It is a list of things gates make impossible to do accidentally.

More rules will land as more failures land. They land here, with their gates. A rule without a gate is not added to this file; it is added to [METHODOLOGY.md](METHODOLOGY.md) as a discipline instead.

## The order of precedence

When two rules could conflict, the order is:

1. The **Charter**'s four vows.
2. The **twelve invariants** above.
3. The **rubric**'s five gates.
4. The methodology, the standards, the sources.
5. Everything else.

A future session that reads a lower-precedence sentence disagreeing with a higher-precedence one holds the higher-precedence one.
