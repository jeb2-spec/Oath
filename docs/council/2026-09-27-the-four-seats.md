# Council reading: the four seats, before they were sat

*Held 2026-09-27. Prompt blob `11f058c0fde5b2bd26bdd7e562b5ba94e1e7808c`, which defines seats A, B
and C. Read by A, B and C.*

## Why this is not an amendment

It began as one. Seats D to G had read every pass since the fourth reading and were written down
nowhere a later reader could find, which COUNCIL.md §8 makes a real problem: the prompt's blob SHA is
the reproducibility guarantee, and a reading naming a seat the prompt does not define cannot be
repeated. The obvious fix was to write the four seats into COUNCIL.md §3.

COUNCIL.md is sealed doctrine and one of the five files INVARIANTS.md §17 watches, so that fix cost
an amendment row, a Council reading of the amendment, a re-seal under a new build id, and a fresh
OpenTimestamps proof. Four ceremonies, for a change that makes no claim about any person and that no
reader of the register will ever see.

The cheaper fix does the same work. The seats go in the prompt, which is not sealed. Their reasoning
is already public in
[docs/design/the-councils-seven-seats.md](../design/the-councils-seven-seats.md). COUNCIL.md §3 says
three seats convene on every session, and seven convening is more than three, not a contradiction.
`scripts/oath-doctor.py` reads every seat back and turns red if a seat doctrine names is missing from
the prompt, which is the failure §8 actually cares about. Nothing else was ever needed.

**What was dropped to get here, and it is worth naming.** The draft also required the prompt to carry
each seat's text *word for word* as COUNCIL.md gives it. That requirement was what forced the
amendment: doctrine describes a seat in the third person and a prompt addresses whoever sits it, so
the two can only agree word for word if doctrine is rewritten into the prompt's voice. The check is
gone. The letters and titles are still compared, because a seat named two ways, or named in a reading
and absent from the prompt, is the thing that actually breaks a reproducible read.

## What was read

The four seats as the prompt now sits them, Seat B's widened watch, the seven finding categories and
three failure modes that came with them, and the doctor's check that every seat doctrine names is
sat.

## Findings

**B-1. Blocking. A Seat D finding could name a person, and the Council record is committed.**
Seat D is instructed to find "the sentence you would lift without its frame to wound the other
side." Its carve-out reached party figures only: a computed figure goes to the maintainer and never
into the Council record. Nothing stopped a finding from naming the officeholder whose sentence is
most liftable. That record is committed to a public repository, so the seat as drafted permitted a
durable document collecting the most damaging quotable line about named people, assembled by a
reviewer instructed to think like their opponent. It is the register becoming the weapon
[INVARIANTS](../../INVARIANTS.md) §7 and §13 exist to prevent, by way of its own review notes.

*Fixed.* The carve-out now reaches persons: findings cite the surface and the pattern, and where one
page is the instance, its template and the condition. A name the maintainer needs in order to act
goes in the report to the maintainer and never into the Council record.

**A-1. Advisory, left open with its defence recorded.** Seat D is the only seat named for a group of
people rather than a standpoint; the others name a relation. A reader who is themselves partisan may
read "The Partisans" as the project's label for them, which is the opposite of what the seat is for.
Against that: the seat's own first sentence explains the plural, because the seat is sat once for each
side. Left as drafted, recorded so a later reader knows it was weighed rather than missed.

## Two findings that dissolved when they were checked

Recorded because the check is the finding, and because a reading that reports only what survived
hides how much of it was guesswork.

**A-2, withdrawn.** Seat D is told to read party only from the register's own rows. I read that as
unexecutable, believing no row carries party. False: `data/officeholders.ndjson` carries `party` on
all 439 rows and `schemas/officeholder.schema.json` defines the field. Party is in the sealed data and
on no surface, which is what §13 and `tools/lint-no-ranking.py` require.

**C-2, withdrawn.** The doctor held a literal `SEAT_FLOOR = "ABCDEFG"`, which I read as a coupling a
future Seat H would silently break. It would not have: the test was `startswith`. The constant is
gone anyway, because doctrine is the floor by being doctrine, and a second copy of a rule can
disagree with the first.

## The reading's own weakest point

The seats that read this were held by the same session that drafted it. The reading found one blocking
defect in its author's own text and withdrew two findings that did not survive a check, which is
better than a reading that found nothing and is not the independence §8 asks for. An author is the
worst available reviewer of their own intent, because the defects they cannot see are the ones they
wrote deliberately. What would fix it is a session that did not write the text holding the seats.

Seats D to G are read for the first time by the pass that follows this one. A seat cannot review its
own creation, and this record says so rather than implying seven seats read it.
