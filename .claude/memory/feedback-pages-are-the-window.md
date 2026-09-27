---
name: feedback-pages-are-the-window
description: "Jared, 2026-09-27, stopping a full local CI run for a landing edit: pages are the window into the record, not the record, and they should be treated like it. The record carries the ceremony; the window carries a light touch."
metadata:
  node_type: memory
  type: feedback
---

# Pages are the window, not the record

*2026-09-27, in the session that slimmed the landing (NEXT.md P.6).* The page change was done and
its render tests were green. I had then added two measured guards and a new test to pin the
wording choice I had just made, and was installing the pinned toolchain to run the whole CI
locally. Jared stopped it: *"Lots of CI for pages... Lots.. keep in mind it's the window into the
record.. not the record.. that's what pages needs to be treated like as well."*

He was right, and it is the same lesson the landing itself had just been taught. The landing was
slimmed because it had been describing itself instead of the record. The tooling around the pages
had grown the same way: at that moment 34 of the 67 measured guards sat on `render.py`, and I was
adding two more, both about how often a sentence appears on one page.

**Why.** The record is what a reader trusts: the rows, the seal, the anchor, the Signal's
arithmetic, a sentence about a named person. A defect there is a false fact about a human being,
and that is where ceremony pays. A page is how the record is shown. When a page is wrong, the fix
is a re-render, and the record under it has not moved. Rigour spent pinning a window's wording is
rigour not spent where it counts, and it makes every page change slower, which is what the
maintainer is actually asking for more of.

**How to apply.**

- **One question sorts every check on a page: does it keep a sentence about a person true, or does
  it keep the window arranged?** The first kind stays, whatever surface it is on: the frame,
  no names in figures, no ranking, no verdict words, an answer resting on the rows its page shows.
  The second kind (caption phrasing, section order, how often a line repeats, a fold) is taste,
  and taste is changed by looking at the page, not by a guard.
- **For a page change, the evidence is the render, the page gates, the render tests, and a
  screenshot.** Seconds. CI runs the rest on the push; do not run it again by hand first.
- **Do not add a guard or a test to hold a design choice in place.** If the next session wants the
  page different, it should be able to make it different.
- **Look at the page.** The screenshot is the instrument for a window. It caught what the HTML
  assertions did not, twice on the same day.

Related: [[story-the-product-was-fine]] (rigour has a derivative), [[feedback-usage-stewardship]]
(one hand, cheap evidence), [[feedback-signal-to-noise]].
