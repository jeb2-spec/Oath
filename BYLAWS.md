# Bylaws

The governance of Oath. Roles, decision authority, correction process, contributor obligations, removal policy, legal posture, and how the project changes hands.

The bylaws exist because trust and genuinely good people are hard to find. Every rule below is written for a world in which the next contributor is a stranger, the next AI session has no memory of this one, and the maintainer is not always awake. When the project depends on any of the three being good, the project has already failed. What we can build instead is a set of gates and a governance shape that makes bad actions visible and reversible.

The bylaws bind alongside the [Charter](CHARTER.md) and the [Invariants](INVARIANTS.md), with the order of precedence set in INVARIANTS.md §The order of precedence.

---

## 1. Roles

### 1.1 Maintainer

There is one Maintainer at a time. The Maintainer holds merge authority on `main`, holds authority to flip repository visibility, and holds veto authority over Signal admission and correction merges.

The founding Maintainer is Jared Bownds (GitHub: `jeb2-spec`).

The Maintainer may not:

- Silently edit a published Finding.
- Silently edit CHARTER, RUBRIC, INVARIANTS, or BYLAWS (the meta-invariant highlights any change).
- Merge a Signal that fails any of the five gates in RUBRIC.md.
- Override a Council finding without a written PR comment naming the override and its reason.
- Grant a contributor the ability to bypass the gates. The gates are contributor-agnostic by design.

### 1.2 Contributors

A Contributor is anyone who opens a pull request. Contributor status is per-PR; it is not granted, it is not revoked, it is not persistent. Every contribution passes the same gates.

Contributors submit under the Contributor Agreement in §7 below.

### 1.3 Council

The Council is the adversarial-review body defined in [COUNCIL.md](COUNCIL.md). It convenes on demand for the events listed in COUNCIL.md §2. Its findings are recorded in the pull request; the Maintainer may accept a Council finding by acting on it or override it in writing.

Council seats are roles, not humans. A seat may be filled by a fresh AI session with the Council prompt, or by a named human reviewer. The Maintainer may not sit as a Council reviewer on any PR the Maintainer also merges.

### 1.4 Successor Maintainer

If the Maintainer becomes unavailable (unresponsive for ninety days, or by written declaration), a Successor Maintainer is designated by the Maintainer's most recent written designation. In the absence of one, the project enters a Read-Only state (§4) until the sibling *Vera Project* maintainer designates one in writing.

The Maintainer is asked to keep a current designation in `docs/succession.md` (this file is created when the first designation is made).

## 2. Decision authority

Every decision that changes the register or its governance passes through a pull request. The following matrix names who can merge what.

| Change type | Author | Reviewer | Merge authority |
| --- | --- | --- | --- |
| Data-adapter change | Any Contributor | Automated gates + Maintainer | Maintainer |
| New Signal (v1) | Any Contributor | Council + Maintainer | Maintainer |
| Signal version bump | Any Contributor | Council + Maintainer | Maintainer |
| Correction to a Finding | Any Contributor (with cited source) | Automated gates + Maintainer | Maintainer |
| New Standard row in STANDARDS.md | Any Contributor | Maintainer | Maintainer |
| New Source in SOURCES.md | Any Contributor | Maintainer | Maintainer |
| Change to METHODOLOGY.md, LIMITATIONS.md | Any Contributor | Council + Maintainer | Maintainer |
| Change to CHARTER, RUBRIC, INVARIANTS, BYLAWS | Any Contributor | Council + Maintainer (both required) | Maintainer, with written justification in the PR |
| Change to gate tooling (`tools/*`) | Any Contributor | Automated gates + Maintainer | Maintainer |
| Change to schemas (`schemas/*`) | Any Contributor | Automated gates + Maintainer | Maintainer |
| Repository visibility flip | Maintainer only | N/A | Maintainer |

Any table row that says "Council" requires a Council session to have run and to have posted its findings to the PR, per COUNCIL.md.

## 3. Signal admission process

A new Signal moves from proposal to shipped by the following path.

1. **Proposal.** A Contributor opens a pull request that adds a definition file at `docs/signals/<slug>.md` and a reference implementation at `src/signals/<slug>.<ext>`, with tests against fixtures under `fixtures/`.
2. **Automated gates.** Schema validation, verdict-language lint, verifier, tamper-test, tests. All must pass.
3. **Rubric.** The Contributor states in the PR body which of the five RUBRIC gates the Signal passes. Any `advisory` gate is called out with a reason.
4. **Council.** A Council session convenes. Its findings are posted to the PR. The Contributor addresses each finding or explains, per COUNCIL.md.
5. **Merge.** The Maintainer merges when the automated gates are green, the RUBRIC gates are addressed, and the Council findings are either resolved or overridden in writing.

## 4. Read-Only state

The project enters Read-Only state if:

- The Maintainer becomes unavailable and no Successor is designated.
- A judicial order requires it.
- The Maintainer declares it in writing.

In Read-Only state:

- No merges to `main`.
- The existing sealed builds remain served.
- The verifier and the reproduction path continue to work.
- The Charter, Rubric, and Invariants continue to bind whoever comes next.

Read-Only is a survival state, not an end state.

## 5. Corrections

Every correction to a shipped Finding produces a new Finding row with `superseded_by` set on the old one. Neither row is deleted. The corrections chain is enforced by INVARIANTS.md §12.

A correction pull request must:

- Cite the primary source that reveals the correction.
- Explain the direction the error ran (in whose favour) and who paid the cost.
- Name the class of the error with a slug (e.g. `stock-act-day-count-off-by-one`), following the errata precedent.
- Link the superseded Finding by id.

Corrections that would apply to a whole class of Findings (a Signal-level bug) require a Signal version bump per §3.

## 6. Corrections and supersessions (facts stay, change is shown)

Charter Vow V is the rule: what was disclosed is a fact and does not change; what has changed since can be shown, with primary-source evidence, in public. Removal by request is not the register's mechanism. Supersession is.

**A subject may request a correction.** If a specific Finding cites a fact incorrectly (wrong person, wrong filing, wrong asset, wrong date, wrong amount), the correction path in §5 applies. The correction PR is opened by the subject or by any Contributor on their behalf; the primary-source citation requirement stands. The corrected row supersedes the original; both stay in the register.

**A subject may request a supersession on demonstrated change.** If a subject can point to a later primary-source filing that demonstrates a change of conduct addressing the condition a Finding named, a supersession may be entered. The supersession row cites the primary source that demonstrates the change and states, in one sentence, what changed. The original Finding stays; the supersession stays; the reader sees both. The signal itself is not altered; the officeholder's status against the signal is what has changed, and the record shows it.

**What supersession does not do.** It does not erase the original Finding. It does not remove the historical facts. It does not hide the condition that fired at the time it fired. Facts stay.

**No shadow removal.** The Maintainer does not honor an off-the-record request from any party. Every change is a row in the register that a reader can see.

**Public-record source removal.** If the primary source itself removes the underlying filing, the register annotates the row with the removal date and reason. The row is not deleted from the register (a stranger reading a citation to it should still find the citation). The row's source URL is marked *withdrawn from source on YYYY-MM-DD* and continues to display.

**Removal by judicial order.** A court of competent jurisdiction may compel removal or redaction. Compliance is documented in the build's release notes with the docket number and the order, redacted only to the extent the order itself requires. The reader sees that the removal happened and why.

## 7. Contributor Agreement

By opening a pull request against this repository, a Contributor:

1. Certifies that the contribution is their own work (or is authorized by its owner) and is submitted under the licenses in LICENSE.
2. Discloses any conflict of interest, including:
   - Being themselves an Officeholder in the current or planned scope of the register.
   - Being an employee, contractor, or paid representative of an Officeholder in scope, or of an entity likely to be named in a Signal that fires against an Officeholder.
   - Being an employee, contractor, or paid representative of an aggregator or source registered in SOURCES.md.
   - Being an employee, contractor, or paid representative of a political party, campaign, PAC, or lobbying entity.
3. Understands that undisclosed conflicts of interest, discovered later, are grounds for the PR to be reverted (per §5, superseded not deleted).
4. Agrees to the Charter, the Rubric, the Invariants, and these Bylaws.

The disclosure lives in the PR body under the heading `## Conflict of interest disclosure`. `None` is a valid answer when true.

## 8. Legal posture

The project publishes information from public records, cites the primary source of every claim, describes conditions rather than adjudicating them, and applies the verdict-language lint to every user-facing sentence. These are the project's shields.

The Maintainer engages legal counsel when:

- A demand letter, cease-and-desist, or subpoena is received.
- A Signal is proposed that would fire against a category of Officeholder for the first time.
- A jurisdictional expansion is proposed to a state whose ethics law meaningfully differs from the federal framework.

Legal counsel's role is to advise on posture; it does not overrule the Charter. A finding that a specific published sentence carries actionable defamation risk is treated as a correction (§5) and produces a new build.

## 9. Financial

The project is not incorporated. It receives no funding, no donations, no advertising, no sponsorship. It carries no financial relationship to any officeholder, party, or source.

If the Maintainer proposes to change any of these at any future date, the proposal enters through the change-of-Bylaws process (§2), is highlighted by the meta-invariant, and requires Council review.

## 10. Amendments to these Bylaws

Amendments to this file are governed by the meta-invariant in INVARIANTS.md §13. A PR that touches BYLAWS.md is highlighted, requires Council review, and requires the Maintainer's written justification. Silent softening is not possible under this rule.

---

## The bylaws behind the bylaws

The project's discipline is what makes it useful. Its usefulness is what makes it worth protecting. Every rule in this file exists so that the discipline can survive the loss of any single person, including the founder, including the collaborator that helped draft it, and including the reader of this sentence.

If a future contributor asks *"why so many rules for a small project?"*, the answer is that the project is small on purpose, and the rules are what let it stay honest as it grows.
