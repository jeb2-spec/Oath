# An outside witness for the documents the Findings rest on

*Design note, 2026-09-27. This is a measurement and a question, not a change to the record. Nothing
here enters `data/`, no page says anything new, and no Finding moves. The tool is
[tools/witness.py](../../tools/witness.py); the job that runs it is
[.github/workflows/witness.yml](../../.github/workflows/witness.yml).*

## Abstract

Every Finding here rests on one document the House Clerk serves, and the register keeps that
document's SHA-256, sealed with the build, and not its bytes. That was decided at the Council's third
reading of S.1b, by Seat B: a kept copy would outlast the Clerk's withdrawal or redaction of a private
person's name written into a report, and the §14 gate would then refuse the copy's removal
([the seats note §3](the-councils-seven-seats.md#3-the-extension-to-seat-b)). The decision is right,
and it leaves a gap. A hash proves which bytes were read only while somebody still holds bytes to
hash. If the Clerk later serves a document in other bytes, or stops serving it, a reader holding the
hash has nothing to check it against, and the Finding's evidence has outlived its source only as a
number.

The Internet Archive crawls the Clerk's site on its own account. `tools/witness.py` asks it, for each
document a published Finding rests on, which captures it lists; fetches one capture of each distinct
payload, byte for byte; and hashes what arrived. A document is **held** only where a capture's bytes
hash to the sealed hash. It observes and never submits.

## What it says, and what it does not

| Outcome | What it means | What it does not mean |
| --- | --- | --- |
| held | A capture's bytes hash to the sealed hash. Someone other than the register holds what the register read, and has since the capture's date. | That the document is accurate. Integrity is not accuracy. |
| differs | The Archive lists captures of the address, and none of those read is the bytes the register read. | That the Clerk changed the document, or that either copy is wrong. A person reads the captures before anything is said. |
| none | The Archive lists no capture of the address. | Anything about the document or its filer. |
| unchecked | The Archive could not be asked, or no capture could be read. | That no copy exists. |

Three rules hold it to that, each tested in `tools/test_witness.py` and the first two measured by
`tools/measure-guards.py`: a capture of other bytes is never a witness; an archive that could not be
asked is never reported as holding nothing; and the tool asks only `web.archive.org`. It prints counts
and document ids, never a name, and it fails when a document could not be checked or a copy differs,
because either is for a person to read.

**Why only the documents a Finding rests on.** A Finding is the one sentence here that says something
about a named person, so it is the sentence whose evidence most needs to outlive its source. INVARIANTS
§16 asks for a witness for every filing, and the same tool reaches every filing by widening one
function, once the questions below are settled.

**Why it runs on GitHub's runners.** The sessions that build this register reach the Clerk and not
`web.archive.org`, which resets the connection (2026-09-27; the Archive's availability endpoint on
`archive.org` answers, and it lists captures without serving their bytes). The job runs by hand, keeps
its report as the job summary and an artifact, and writes nothing to the repository.

## The question for the Council

Three decisions follow from the measurement, and none is the tool's to make. Seat B decided the
kept-copy question, and each of these is that question in a new shape.

1. **Should the register ask the Archive to capture a document it does not hold?** The Archive's
   *save* service would make a copy because of the register. Seat B's harm was a copy the register
   holds and the §14 gate will not let go; a copy the Archive holds is under the Archive's own removal
   policy, and the register cannot promise anything about that policy. The capture would still exist
   because this project asked for it.
2. **Should the witness enter the sealed record, and should a page link to the copy?** A row per
   document and check (held since, by whom, the hash) is a fact about the Archive at a time, and it stays
   true after the copy is gone. A link on a Finding's page is different: it sends every reader to a copy
   that may outlast a redaction the Clerk makes for a private person's sake. The row without the link
   keeps the proof and does not point at the copy.
3. **INVARIANTS §16 as written promises a bundle of kept bytes and at least one outside witness for
   every filing,** and Seat B's decision rules out the first half. Reconciling §16 is an amendment of
   a watched file (INVARIANTS §17), for the maintainer, and belongs with the doctrine catch-up in
   [NEXT.md D.4](../../NEXT.md#d4-doctrine-catch-up). The outside witness is the half of §16 that the
   decision leaves standing.

## Measured

Asked from this session on 2026-09-27, the Archive's availability endpoint listed a capture for three
of the first six documents a Finding rests on. That is the Archive's index, not a reading of bytes, and
it is not the answer. The first run of the job is.
