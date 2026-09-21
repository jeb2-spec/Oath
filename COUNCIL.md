# The Council

The Council is Oath's adversarial-review body. It convenes on the events listed in §2 below and it applies the review discipline in §3. Its findings are posted to the pull request. The Maintainer either acts on each finding or overrides it in writing.

The Council pattern is inherited from the sibling *errata* project, where the first Council session on the errata README returned sixteen findings, the first four of which were reader-catchable defects that the author of the document had missed. The lesson from that session is the argument for this file: **a document a single hand wrote and a single mind approved will ship with the specific class of error that hand and that mind cannot see.**

The Council is the mechanism that reads for that class.

## 1. What the Council is

The Council is a rotating set of adversarial reviewers. It has:

- **No standing members by name.** A Council session convenes for a specific pull request, does its work, posts its findings, and dissolves.
- **Standing seat definitions.** The seats are roles the session fills. Each seat carries a specific viewpoint that the session must actively hold.
- **A public prompt.** The Council prompt is committed at `.claude/prompts/council.md` and versioned; a session at prompt version *N* posts its version in the PR alongside its findings.
- **No unilateral merge or veto authority.** The Council reports; the Maintainer decides.

## 2. When the Council convenes

A Council session is required (INVARIANTS.md §8) before merging any of:

- A new Signal definition (v1).
- A Signal version bump that changes criteria, inputs, or the cited Standard.
- A change to METHODOLOGY.md, LIMITATIONS.md, or the Rubric's five gates.
- A change to CHARTER.md, INVARIANTS.md, or BYLAWS.md (both Council review and Maintainer approval; both required).
- A new user-facing template or page shape that names Officeholders in a way an existing template did not.

A Council session is *encouraged* but not required for:

- Adapter changes that could plausibly alter the visible distribution of Findings.
- Standards or Sources additions that materially expand coverage.
- Corrections to shipped Findings when the correction touches more than one Officeholder.

## 3. The seats

Three seats convene on every session. A single fresh AI session may hold multiple seats sequentially (writing each seat's findings before moving to the next), or the seats may be split across multiple reviewers. The prompt at `.claude/prompts/council.md` names the required perspective for each seat.

### Seat A. The Reader Who Wants to Be Fair

Reads as a member of the public who came to the register wanting to know if a specific Officeholder deserves their vote and wanting to be fair to everyone in the register. Watches specifically for:

- Sentences that read as verdicts even where the verdict-language lint passed.
- Framing that would produce a different reader takeaway for an ally vs. an opponent given structurally identical facts.
- Coverage gaps that make the visible distribution look partisan when the underlying data does not.

### Seat B. The Subject in a Room

Reads as the Officeholder the PR most affects. Watches specifically for:

- Sentences the subject would read back to the author uncomfortably.
- Claims that would prompt a lawyer's letter under a fair-minded reading.
- Descriptions that name conditions in language the Standard itself does not use.
- Omissions of context that the Standard requires the reader to hold.

### Seat C. The Reviewer's Reviewer

Reads as a hostile technical reviewer looking for methodological defects. Watches specifically for:

- Signal criteria that permit false positives or false negatives the definition does not disclose.
- Standard citations that do not actually govern the fact pattern the Signal fires on.
- Reproducibility gaps (a Finding the reference implementation does not produce byte-identically from the cited Filings).
- Coverage gaps that shape the visible distribution.
- Any of the failure modes named in METHODOLOGY.md §5.2.

## 4. What a Council finding looks like

A Council finding is posted as a review comment on the PR. Each finding contains:

- **Seat.** A, B, or C.
- **Category.** One of: verdict-language, framing-asymmetry, coverage-gap, standard-mismatch, reproducibility, subject-discomfort, other.
- **Severity.** `blocking` or `advisory`.
- **What.** The specific sentence, code path, or omission at issue.
- **Why.** The reason it fails the seat's read.
- **Fix.** The change the finding proposes, or a note that the finding is a discovery rather than a fix request.

The session posts one aggregate reply that lists all findings with their categories and severities. This is the row a future maintainer reads when they want to know what the Council saw.

## 5. Findings a Council session must always try to catch

The following failure modes are named up front, and every session is directed to check for each of them. A Council session that returns zero findings under any category below without a written *checked and clear* note is a Council session that did not run the seat.

1. **A tie called a lead.** A summary claim that the underlying table contradicts.
2. **Every self-catch was mechanical.** A claim of a property the schema does not measure.
3. **Seven that were fourteen.** A count in prose that the derived table does not produce.
4. **A transcript the command does not produce.** A code block that the tool does not actually emit.
5. **The-frame-was-stripped.** A user-facing surface that renders an Officeholder without the presence-is-not-proof frame.
6. **A signal that would fire on ally-A but not on ally-B for structurally identical inputs.**
7. **A standard cited but not linked.**

The names of the first four are the errata precedent; they are kept here so the family recognises them across projects.

## 6. Acting on findings

The pull request author addresses each finding by:

- **Accepting.** Applying the fix and pushing.
- **Rejecting.** Posting a reply that names the reason. A rejection stands only for `advisory` findings. A `blocking` finding cannot be rejected; it can only be resolved.
- **Escalating.** Requesting the Maintainer's ruling. The Maintainer's ruling is written in the PR.

A Council session does not close its own findings. The finding is closed by the reviewer who wrote it (or by the Maintainer, in writing, with the override reason).

## 7. Overriding a Council finding

The Maintainer may override a `blocking` Council finding only by:

- Posting a written justification in the PR that names the finding, states the reason for override, and identifies the risk being accepted.
- Marking the PR with the `council-override` label.
- Adding a row to `data/council-overrides.ndjson` at the same commit as the merge, with the finding text, the reason, and the merge commit hash.

The row in `council-overrides.ndjson` is sealed with the build. Every override is publicly visible for every future reader.

## 8. The Council prompt

The prompt lives at `.claude/prompts/council.md`. It is committed. Its version is the git blob SHA at the time of a session. A session posts its prompt version alongside its findings so a later reader can reproduce the seat's read.

The prompt is amended by pull request. Amendments to the prompt are Council-reviewed (recursive on purpose: the Council reviews changes to its own instrument), because a prompt that softens the seat quietly softens the review.

## 9. On AI vs. human reviewers

Both may sit. The seat definitions do not care which. What the seat cares about is that its perspective was actively held.

An AI session convened as Council is instructed (via the prompt) to:

- Start with no context beyond the PR diff, the prompt, and the linked files.
- Not read the PR author's own arguments before making its findings; read them after and note where they change the finding.
- Post findings in a format a future reader can walk.

A human reviewer sitting a Council seat is asked to hold the seat's perspective consciously. It is easier for a human to slide into general helpfulness; the seat definition is a discipline for the reviewer, not just a rubric for the review.

## 10. What the Council does not do

- The Council does not decide policy. It reports.
- The Council does not approve or veto. It reports.
- The Council does not evaluate Officeholders. It evaluates the *project's* handling of Officeholders.
- The Council does not read the PR author's replies to prior findings as ground truth. It reads the diff.
- The Council does not exist to make the PR merge faster. It exists to make the PR merge honestly.
