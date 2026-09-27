# Council reading: the seats amendment

*Held 2026-09-27. Prompt blob `11f058c0fde5b2bd26bdd7e562b5ba94e1e7808c`, which defines seats A, B
and C. Read by A, B and C.*

## Why these three seats and not seven

COUNCIL.md §8 makes an amendment to the Council's own instrument Council-reviewed on purpose,
because a prompt that softens a seat quietly softens every review after it. The amendment under
reading is the one that creates seats D to G. So it is read by the seats that exist before it: the
three the prompt defines at the blob SHA above. Reading it with the seats it creates would be the
circularity §8 exists to prevent, and `tools/highlight-charter-change.py` enforces the same thing
from the other side: it refuses an amendment row whose recorded reading names a seat the prompt at
that reading's SHA does not define.

## What was read

COUNCIL.md §3 (seven seats, the floor sentence, and why these seven), §4 (seven new finding
categories), §5 (three new failure modes, ten in all), §8 (what holds the prompt and §3 together);
`.claude/prompts/council.md` (the same seven seats in the prompt's register); and
`scripts/oath-doctor.py`'s check that the two agree word for word.

## Findings

**B-1. Blocking. Seat D's findings could name a person, and the Council record is sealed.**
Seat D is instructed to find "the sentence you would lift without its frame to wound the other
side." Its carve-out reached party figures only: a computed figure goes to the maintainer and never
into the Council record. Nothing stopped a Seat D finding from naming the officeholder whose
sentence is most liftable. The Council record is committed and sealed with the build, so the
amendment as drafted permitted a durable document collecting the most damaging quotable line about
named people, assembled by a reviewer instructed to think like their opponent. That is the register
becoming the weapon [INVARIANTS](../../INVARIANTS.md) §7 and §13 exist to prevent, by way of its own
review notes.

*Fixed in this amendment.* Seat D's carve-out now reaches persons as well as party figures, in
COUNCIL.md and in the prompt alike: findings cite the surface and the pattern, and where one page is
the instance, its template and the condition; a name the maintainer needs in order to act goes in
the report to the maintainer and never into the Council record.

**C-1. Advisory, taken. "Word for word" is checked on words, not on link targets.**
§3 said the prompt carries each seat's text word for word and the doctor turns red when the two
differ. The doctor compares with link targets stripped and whitespace collapsed, so the claim is
true of words and not of markup. §3 now says "link targets and spacing aside".

**A-1. Advisory, left open with its defence recorded.** Seat D is the only seat named for a group of
people rather than a standpoint: the others are The Reader Who Wants to Be Fair, The Subject in a
Room, The Reviewer's Reviewer, The Constituent the Averages Leave Out, The Person Beyond the Border,
The Reader Who Comes Later. A reader who is themselves partisan may read "The Partisans" as the
project's label for them, which is the opposite of what the seat is for. Against that: the seat's
own first sentence explains the plural, because the seat is sat once for each side. Left as drafted;
recorded so a later reader knows it was weighed rather than missed.

## Two findings that dissolved when they were checked

Both are recorded because the check is the finding, and because a reading that reports only what
survived hides how much of it was guesswork.

**A-2, withdrawn.** Seat D is told to read party only from the register's own rows. I read that as
unexecutable, on the belief that no row carries party. False: `data/officeholders.ndjson` carries
`party` on all 439 rows and `schemas/officeholder.schema.json` defines the field. Party is in the
sealed data and on no surface, which is what [INVARIANTS](../../INVARIANTS.md) §13 and
`tools/lint-no-ranking.py` require, and the instruction is executable exactly as written.

**C-2, withdrawn.** The doctor's floor is the literal `SEAT_FLOOR = "ABCDEFG"`, which I read as a
coupling a future Seat H would silently break. It would not: the check is
`letters.startswith(SEAT_FLOOR)`, so an eighth seat passes, and the agreement loop iterates every
seat COUNCIL.md defines rather than the floor, so Seat H is still compared with the prompt. The
constant's job is to stop A to G being removed, which is what §3's floor sentence says.

## What the reading did not cover

The three seats reading this are the three whose watch the amendment does not change. Seat B's
widened watch, and seats D to G, are read for the first time by the pass that follows this one:
their first real exercise is the next Council session held under the amended prompt. A seat cannot
review its own creation, and this record says so rather than implying seven seats read it.
