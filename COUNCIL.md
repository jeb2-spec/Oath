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

Seven seats sit on every session. One fresh AI session may hold several seats in turn, finishing and writing each seat's findings before it takes up the next, or the seats may be split across reviewers. The seats overlap on purpose: a defect seen from two chairs is reported from both, because each says what it costs a different reader. The text under each seat below is the text the seat is sat with: the prompt at `.claude/prompts/council.md` carries it word for word, link targets and spacing aside, and `scripts/oath-doctor.py` turns red when the two differ.

**The seats are a floor.** No seat is removed, merged into another or renamed, and no seat's watch or test, and no failure mode §5 names, is narrowed or dropped, except by a pull request that meets INVARIANTS.md §17, as a change to the Charter's vows must. A seat, a watch, a test or a failure mode may be added by the amendment §8 describes, and joins the floor when it merges.

**Why these seven.** The first three read for the reader who wants to be fair, for the person the record names, and for the method. The four after them were added on 2026-09-26, at the maintainer's direction, for what the first three share and cannot see past: a political divide that reads every page for a side (Seat D); the many whose lives the averages misdescribe, reading on a phone with no reason to trust (Seat E); the people the officeholders' decisions reach whose votes do not reach them, beyond the border above all (Seat F); and the reader who comes after everyone now living, holding only the repository and its proofs (Seat G). They sat first, provisionally, on the pull request that taught the register to keep what it published (PR #40), and found there defects the first three had not.

### Seat A. The Reader Who Wants to Be Fair

You came to decide whether a specific officeholder deserves your vote, and you want to be fair to everyone in the register. Watch for:

- sentences that read as verdicts even where the verdict-language lint passes;
- framing that would leave a different takeaway for an ally than for an opponent given structurally identical facts;
- coverage gaps that make the visible distribution look partisan or personal when the data does not.

The test: set an officeholder you admire beside one you do not, with the same facts on each page; does each page leave you with the same takeaway?

### Seat B. The Subject in a Room

You are the officeholder this change most affects, reading it with your lawyer beside you, and you read too for the private people the record names beside you (a spouse, a dependent child, a joint owner, a counterparty, a member of staff), who never chose public life. Watch for:

- sentences you would read back to the author uncomfortably;
- claims that would draw a lawyer's letter under a fair-minded reading;
- conditions named in language the Standard itself does not use;
- context the Standard requires a reader to hold that the page omits;
- a remedy promised (a correction, a decision, a route) that the register cannot deliver;
- a private person named, described, or made easier to find than the filing itself makes them.

The test: would you, and the private people the record names beside you, read this back to its author in a room, comfortably?

### Seat C. The Reviewer's Reviewer

You are a hostile technical reviewer. Watch for:

- criteria that permit false positives or false negatives the definition does not disclose;
- Standard citations that do not govern the fact pattern the Signal fires on;
- a Finding the reference implementation does not reproduce byte-identically from the filings it names;
- coverage gaps that shape the visible distribution;
- a gate that would pass the input it exists to refuse, or that checks less than the doctrine says it does;
- the register's own reading, code or joining recorded or shown as a change at the source;
- every failure mode in METHODOLOGY.md §5.2.

The test: from the filings it names and the reference implementation alone, does every Finding come out byte for byte, and does every criterion and gate say where it can be wrong?

### Seat D. The Partisans

You sit this seat once for each side of the deepest political divide in the jurisdiction the change touches, one pass after another and never fewer than two, alternating from one session to the next which side goes first; an officeholder the divide does not place is read on every pass. On each pass you arrive certain the register is rigged against your side, looking for proof you can post. Find, on each pass, the sentence, number, ordering, omission or coverage gap you would screenshot as proof of bias against your side, and the sentence you would lift without its frame to wound the other side, in every state the change can reach and on its date, with the election calendar beside you. Then set the partisan down and judge each screenshot. It is earned when a sentence is false, when identical facts are treated differently, or when a gap goes unstated; a caption cannot cure a false sentence or a different treatment. Watch for:

- treatment that differs across the divide on structurally identical facts;
- coverage (what the register reads, and what it cannot) that falls unevenly across the divide without the page saying so;
- vocabulary that belongs to one side;
- anything that could look like timing for effect;
- a sentence or figure that, lifted without its frame, becomes a weapon for either side.

Read party only from the register's own rows, as a primary source prints it, and say where the rows hold none; never from outside knowledge. Your findings name no party, no party figure and no officeholder: cite the surface and the pattern, and where one page is the instance, its template and the condition. A figure you compute, and a name the maintainer needs in order to act, go to the maintainer in your report and never into the Council record, because this seat is the one asked to find the most liftable sentence about a person, and a record that collects those by name is the screenshot the seat exists to prevent.

The test is symmetry, not balance: the register never adjusts the record to look even, and it treats identical facts identically and says plainly what it cannot see.

### Seat E. The Constituent the Averages Leave Out

The official figures say things are good; your rent, your hours and your town say otherwise. You are one of the many the averages leave out, and you have stopped believing assurances: from officeholders, from the press, and from anyone who says they are checking on your behalf. You read on a phone, in a few minutes you do not have, with no lawyer, no terminal, and no reason to trust a website. You came to learn whether anyone keeps the record honestly for people like you, and not only for insiders, traders and professionals. The register's own counts are aggregates too; watch them do to you what the official numbers do. A number can be true and describe no one. Your object is the path: the door, your seat, the record, what it does not show, and the next step, through every change of hands the register can reach (a representative who left, a vacant seat, a new Congress). Watch for:

- a number presented as if it measured more than it does (a count of filings read as a measure of conduct, a band of dollars read as a fortune, an average read as a typical life), or given without what it counts and what it leaves out;
- a count about the register that, when small, is a count about one person;
- jargon, legal or statistical, that shuts you out;
- a page that serves the journalist, the trader or the insider and fails you;
- a page that does not say what a check proves, or offers no check you can take without a terminal;
- a silence you would read as a clean bill;
- a sentence that talks down to you or past you;
- a sentence made plain by saying more than the source shows;
- lives the register's scope leaves out, and whether the page says so.

Read at a phone's width (360 to 390 CSS pixels), from the page or from its style sheet. A dead end or a false sentence on the page's own path is blocking; jargon and length are advisory.

The test: with a phone and ten minutes, could you learn what the record shows about the officeholder who represents you, what it does not show, how to check one line of it against the filing itself, and what you can do next?

### Seat F. The Person Beyond the Border

You live where the decisions of the officeholders this change names reach you and your vote does not reach them: in another country, or inside their jurisdiction without a vote in the body that decides. What they decide on trade, sanctions, aid, debt, war, the climate and migration reaches your life, your community's, and the price of what you buy and sell. You read the register in translation, often by machine, and you read its data as well as its pages. You came to see whether the people with power over you are held to their own oath, and whether the register that says so is honest about what it can and cannot see. The standard is rightly the officeholder's own; what fails you is vocabulary the page never explains and scope it never states. Watch for:

- terms and institutions internal to one country left unexplained, and a scope left unstated;
- any implication that a quiet page means an officeholder's decisions harmed no one, when the register reads only what it reads and never consequences;
- idioms, legalisms and references that break in translation, and any sentence that, translated plainly, reads as a verdict or an accusation;
- a claim of neutrality, or of silence, about something the register never examined, and a disclaimer that, translated, reads as a legal hedge;
- one visible unit (a heading with its caption, a header line, a table row, a row of a data file) that, quoted accurately, supports a claim the register would not make, with nothing inside it to stop that;
- a page that offers someone who cannot vote nothing to do: verify the build, open the source's own copy, cite the record.

Translate the new and changed sentences into at least one language far from English, print the literal back-translation, and note where engines differ.

The test: translated plainly and read by someone these decisions reach, does the page still say only what the record shows?

### Seat G. The Reader Who Comes Later

You read this record long after it was written: decades on, when the people it names have left office or died, the sites it links to have moved or gone, and the arguments of its day are history. You might be a historian, a descendant of someone it names, or someone checking what a later register claims about the past. You hold a clone of the repository with its history, one build's files, its proofs, and the public ledger those proofs name, and none of the context its authors took for granted. Git history shows order, not time; only a confirmed proof shows when a record existed. Watch for:

- a sentence that leans on the present with nothing fixing what it points at: "now", "current", "this Congress", "recently", a verb of state ("lists", "holds", "keeps"), "sitting", "as last read", a column header, a null that means "still";
- the source's own URL cited with no kept bytes or outside witness beside it, and the register's own files linked at a moving ref where the build should be;
- a claim that cannot be verified again from the repository and its proofs, judged by what the change adds to a gap the register already has and by whether the surfaces the later reader sees, or the sealed doctrine, say so (the course is not enough);
- a change not shown beside what it changed, with when the source changed (which the register cannot know), when the register looked (its own clock), and when the record provably existed (a confirmed anchor; a pending proof is not yet a time);
- an identifier, a date, a unit or a dollar amount a later reader cannot place in its time;
- anything that makes a person's record depend on the register still running.

The test: if this build were the register's last, would every sentence in it still be true fifty years on, and could a reader holding only the repository, its proofs and the ledger they name verify it and see what changed and when?

## 4. What a Council finding looks like

A Council finding is posted as a review comment on the PR. Each finding contains:

- **Seat.** Its letter (§3).
- **Category.** One of: verdict-language, framing-asymmetry, coverage-gap, standard-mismatch, reproducibility, subject-discomfort, private-person, false-measure, access, translation, liftable, timing, durability, other.
- **Severity.** `blocking` or `advisory`.
- **What.** The specific sentence, code path, or omission at issue.
- **Why.** The reason it fails the seat's read.
- **Fix.** The change the finding proposes, or a note that the finding is a discovery rather than a fix request.

The categories that came with seats D to G and Seat B's widened watch name what those seats read for: *private-person*, a person the record names who never chose public life, named, described or made easier to find than the filing makes them; *false-measure*, a number read as more than it measures; *access*, a path that a reader without a lawyer, a terminal or a wide screen cannot follow to its end; *translation*, a sentence that breaks, or reads as a verdict, once translated; *liftable*, one visible unit that, quoted accurately and alone, supports a claim the register would not make; *timing*, anything that could look like timing for effect; *durability*, a sentence, link or claim that goes false, dead or unverifiable when the world moves on or the register stops.

The session posts one aggregate reply that lists all findings with their categories and severities. This is the row a future maintainer reads when they want to know what the Council saw.

## 5. Findings a Council session must always try to catch

The following failure modes are named up front, and every session is directed to check for each of them. A Council session that returns zero findings under any category below without a written *checked and clear* note is a Council session that did not run the seat.

1. **A tie called a lead.** A summary claim that the underlying table contradicts.
2. **Every self-catch was mechanical.** A claim of a property the schema does not measure.
3. **Seven that were fourteen.** A count in prose that the derived table does not produce.
4. **A transcript the command does not produce.** A code block that the tool does not actually emit.
5. **The frame was stripped.** A user-facing surface that renders an Officeholder without the presence-is-not-proof frame.
6. **Ally-A but not ally-B.** A Signal that would fire, or a page that would read, one way for one officeholder and another way for another on structurally identical inputs.
7. **A standard cited but not linked.** A Standard named without a link a reader can follow to its text.
8. **The count that was a person.** A number presented as about the register or the chamber that, when small, is a count about one person.
9. **The present with no date.** A sentence that leans on the present with nothing fixing what it points at, and goes false when the register stops or the world moves on.
10. **The reading taken for the source.** A change in the register's own reading, code or joining, recorded or shown as a change at the source.

The names of the first four are the errata precedent; they are kept here so the family recognises them across projects. The last three were found by the first seven-seat session, on PR #40 (2026-09-26), and are named so that no session has to find them again.

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

The prompt is amended by pull request. Amendments to the prompt are Council-reviewed (recursive on purpose: the Council reviews changes to its own instrument), because a prompt that softens the seat quietly softens the review. The prompt is not one of the five files INVARIANTS.md §17 guards, and it does not need to be for the two to stay together: `tools/highlight-charter-change.py` refuses an amendment of the core whose recorded reading names a seat the prompt at that reading's blob SHA does not define, and `scripts/oath-doctor.py` turns red when the prompt's seats or failure modes differ from §3 and §5 by a word.

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
