# Contributing

Thank you for wanting to make this real.

Before you open a pull request, read three files, in this order, and know that opening a PR is a written commitment to them:

1. [CHARTER.md](CHARTER.md). Five vows, short on purpose. When everything else is negotiable, they are not.
2. [BYLAWS.md](BYLAWS.md). Governance, roles, corrections and supersessions, contributor agreement (§7 is what you are agreeing to when you open a PR), and the removal policy.
3. [RUBRIC.md](RUBRIC.md), if your PR touches a Signal or a Finding. Five pass/fail gates; the PR sits at review until each is answered.

Beyond that, the shape of a good contribution:

- **Small, named commits.** One purpose per commit. A PR with three orthogonal purposes should be three PRs.
- **Cheap evidence first.** Run whatever gates exist locally before you push (`tools/validate-schemas.py`, `tools/verify.py`, `npm test`, `pytest`) once they land. If a gate does not exist yet, run the closest thing that does and note what you could not run.
- **No verdict language.** Every user-facing sentence passes the "would the subject read this back to you comfortably in a room?" test. See [INVARIANTS.md §1](INVARIANTS.md).
- **Corrections and supersessions preserve the past.** Nothing is deleted; everything is superseded. See Charter Vow V and [BYLAWS.md §6](BYLAWS.md).
- **Conflict of interest disclosure is required.** Every PR body carries a `## Conflict of interest disclosure` heading. `None.` is a valid answer when true. See [BYLAWS.md §7](BYLAWS.md).
- **Council review before publishing anything that names an officeholder in a new way.** New Signal, Signal version bump, new naming template. See [COUNCIL.md](COUNCIL.md).
- **Attribution follows the `Co-Authored-By` convention.** If an AI collaborator helped, disclose it in the trailer.

## What kind of contribution the project needs most

At the founding, work concentrates in the phases of [NEXT.md](NEXT.md). Priority order:

- **Phase 1 tooling.** The verifier, the tamper-test, the schema validator, the verdict-language lint, the CI workflow, and the session-start doctor. Standard-library Python where possible; TypeScript for adapters and Signals.
- **Phase 2 first Signal.** `stock-act-late-ptr`, end-to-end, against fixtures.
- **Adapter for the U.S. House Financial Disclosure Portal.** The reference primary source.

## What to do if you find a problem in a published Finding

Two paths, both documented in [BYLAWS.md §6](BYLAWS.md):

- **Fact correction** (wrong person, wrong filing, wrong amount): open a PR that adds a supersession row citing the primary source that reveals the correction. Both rows stay in the register.
- **Demonstrated change** (a later primary-source filing shows the subject's conduct has changed such that the Finding's condition no longer applies): open a PR that adds a supersession row citing the primary source that shows the change. Both rows stay.

Off-the-record requests are not honored. Every change is a row in the register a reader can see.

## Reporting a security or trust issue

See [SECURITY.md](SECURITY.md).

## The larger question you probably have

Yes, this repository is unusually dense for its state. That is because the discipline it enforces is what makes the register worth reading; adding it after the fact is much harder than adding it now. If a rule seems overkill, read the [Charter](CHARTER.md) again, and then the section of the [Invariants](INVARIANTS.md) that names the specific failure the rule catches. If it still seems overkill, open a PR that names why. That kind of pushback is welcome.
