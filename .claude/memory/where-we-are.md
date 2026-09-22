---
name: where-we-are
description: "The current state of Oath. Read first. Updated in the same commit that changes it, or deleted."
metadata:
  node_type: memory
  type: state
---

# Where we are

*Last updated: 2026-09-22, second local session (Fable 5.1). Five pull requests are open and Jared reviews; nothing new is on `main` since PR #2.*

## The state

**Day zero of the register, day two of the discipline: the neighbourhood is read and the empty register is sealed.** The foundation is on `main`. Five branches wait on Jared:

- **PR #3, `claude/phase-1-runtimes`.** Phase 1 T.1: `package.json`, `pyproject.toml`, `biome.json`. Toolchain on this machine: TypeScript 5.9.3, Vitest 5.0.1, Biome 2.5.14, Ruff 0.16.8, Pytest 9.1.1 (Ruff and Pytest were installed with `python -m pip install` this session; they are not on the PATH from Git Bash, so run them as `python -m ruff` and `python -m pytest`).
- **PR #4, `claude/doc-crossrefs`, base `main`.** Eight section cross-references and two counts wrong since the founding commit, in seven files including INVARIANTS.md, BYLAWS.md, RUBRIC.md, and METHODOLOGY.md. The first Council session read it (nine advisory findings, eight acted on, one discovery: `.claude/prompts/council.md` does not exist yet). The meta-invariant applies, so Jared's written approval is requested in the PR.
- **PR #5, `claude/gate-crossrefs`, stacked on #4.** `tools/check-crossrefs.py`, the first landed gate: every section reference, anchor, and relative Markdown link must resolve. Fixtures and five tests. It catches dead references and cannot catch a live reference to the wrong section; the docstring says so. Not yet in CI, because no workflow exists (T.5).
- **PR #6, `claude/related-work`, stacked on #3.** `RELATED.md` (the related-work section: the neighbourhood on its own terms, what Oath is against it, what the field teaches the build), `docs/related-work/` (the verified records, JSON plus rendered Markdown, four clusters), SOURCES.md corrections, README pointers, the colophon on the course (NEXT.md Phase 3 I.6), and this memory. A three-seat Council read the draft; the findings and dispositions are in the PR. The trading-tracker cluster (§2.6) landed with both readings after the Council, spliced by hand. The journalism cluster (§2.7) had one reading; its second hit Jared's usage limit and was not re-run, so its six entries are named in §2.7 and held per §6. The first reading is not in the repo; it is in the workflow journal under the session's `subagents/workflows/` directory (`journal.jsonl`, the `sweep:journalism` result) and, durably, in `C:/Users/jared/.claude/projects/C--Users-jared-Apps-Oath/carry-2026-09-21/` (the survey JSON for every cluster, the drafted §2.7, the held media entry, both Council records, and the record-building scripts), copied there at the end of the session because the scratchpad is temporary. A skeptic agent was launched for the second reading and died silently on the usage limit, so on 2026-09-22 the second reading was started by hand: seven pages checked, three corrections to carry (The Washington Sun launched as NOTUS in 2024 and rebranded the same year, not 2026; ProPublica's May 2025 piece names executive-branch officials and congressional aides, not members; Trump Town was last updated October 15, 2019 and its page does not name the form it was built from). Three pages remain, all needing the built-in browser: Insider's *Conflicted Congress* methodology page (the scoring bands), the Pulitzer listing for *Capital Assets*, and the Times article. Jared chose to stop for the night before those. Finishing is three browser reads, the splice, the gates, and a push; no agent.

- **PR #7, `claude/phase-1-verifier`, stacked on #6.** Phase 1 T.2: `tools/verify.py` (151 lines, standard library), `tools/seal.py`, `tools/tamper-test.py`, eleven tests, and `data/meta.json`, the sealed record of build `0000-empty`. The seal covers every `data/**/*.ndjson`, the eleven doctrine documents, and meta's own disclosures; the manifest rule is written at the top of the verifier. The empty build verifies OK and the tamper-test passes its three checks. Rule that follows: any change to a sealed file, doctrine included, needs `python tools/seal.py --build <id> --built-at <time>` in the same commit, or the verifier fails loudly, which is the point. After #4 and #6 merge into `main`, one re-seal commit on `main` is due; either of us can make it. tools/README.md will conflict trivially with #5 (both add a Landed tools section); resolve by keeping both rows.

**The next session's first move** is [NEXT.md](../../NEXT.md) Phase 1 T.3 (the schema validator), after Jared merges what he merges.

## What this session decided or learned

- **Local memory is a junction.** `C:\Users\jared\.claude\projects\C--Users-jared-Apps-Oath\memory` is now a junction to this repo's `.claude/memory`, the same setup Vera uses, so auto-memory loads the repo's memory directly and anything written there is committed.
- **Keep usage in mind.** Jared's standing rule, given mid-session: fan out agents only for research or review one hand cannot do; say the cost before proposing it; do the rest by hand. See [feedback-usage-stewardship.md](feedback-usage-stewardship.md). The related-work survey ran about twenty agents before he said it. The critic-and-additions phase of the survey was cut; the skeptics' lists of projects they thought missing are in each record and are the seed for any later pass.
- **A named individual gets no weaker standard.** Jared and Lauren asked for one independent investigator's media platform to be read and differentiated from. It was read (home, About, and the Webb product page) and drafted, and the Council held it out because it had no first-reader record and no skeptic pass while every other entry did. The draft sits in the session scratchpad, not the repo. If Jared wants it in, the cost is one skeptic agent on a two-page record, and §2.8 goes back with the Council's fixes (no in-place comparison, no scorecard of absences, no characterisation of the owner's posts).
- **The colophon.** Jared's "made in America, but actually": every build emits a sealed record of how it was made, prints one line of it on every page, and the mark's ring counts it. On the course as Phase 3 I.6. It states what was done and never claims quality.
- **The first Signal's rule text.** The House PTR form and the Committee's January 2023 memorandum, and the Senate's Financial Disclosure page, state the rule: due the earlier of 30 days from notification or 45 from the transaction; more than 30 days late without the fee is "not properly filed." The notification date is a field on the form. Cite the chambers, not any summary.
- **Identifiers.** The field's convention is bioguide as primary key with a crosswalk of (scheme, id, from, to); `unitedstates/congress-legislators` is CC0 and vendorable; the Clerk's index has no person key, which is a Limit to state. Details in RELATED.md §5.1 for the D.3 decision.
- **What the verdict lint will hit.** RELATED.md carries four neighbours' own names and self-descriptions that contain blacklisted words (GovTrack's database, POGO's database, the site's own words for its investigations, OCCRP's name). When T.4 lands, those four contexts go in the allowlist with the reason.
- **What a cross-reference gate cannot see.** Six of the eight founding errors cited a section that exists but is the wrong one. That stays a Council discipline (COUNCIL.md §5 mode 7) until a citation convention makes it mechanical.

## What is on `main`

Unchanged since PR #2. Doctrine: CHARTER, SUBJECTS, PIPELINE, EVIDENCE, RUBRIC, INVARIANTS, BYLAWS, COUNCIL. Reference: METHODOLOGY, STANDARDS, SOURCES, LIMITATIONS, SPEC, ECOSYSTEM, ANCHORS. Community: CONTRIBUTING, CODE_OF_CONDUCT, SECURITY, LICENSE, PR template. Schemas: seven. Placeholders: data, src, tools, fixtures, docs/architecture, docs/signals. Memory: this folder.

## What is not real yet

- No adapter, no Signal, no Finding, no schema validator, no verdict-language lint, no frame lint, no ranking lint, no CI workflow, no session-start doctor, no fixtures for data, no mark generator, no struck seals, no `.claude/prompts/council.md`, no published or anchored builds. Two gates exist on branches: check-crossrefs (#5) and verify with its tamper-test (#7). The empty build is sealed but not anchored; anchoring begins with the first data build.
- No `tsconfig.json` and no TypeScript source; both land with the first Signal in Phase 2 S.2.

## The critical path

Per [NEXT.md](../../NEXT.md): Phase 1 plumbing (T.1 on a branch; T.2 next; then T.3 to T.6), Phase 2 first Signal against fixture, Phase 3 first real officeholder, Phase 4 coverage and second Signal, Phase 5 public flip, Phase 6 ecosystem and forks.

## Standing decisions

- **Repository visibility.** Private, still. Public flip is Phase 5 and is Jared's call.
- **Branch convention.** Per-purpose branches; stacked PRs when one depends on another (GitHub retargets when the base merges).
- **Commits.** Thematic, by name, never `git add -A` while agents share the tree (an agent saved a fetched page into the repo root this session and it was swept into a commit before being caught).
- **Reference runtimes.** Node 20 with TypeScript 5 for adapters and Signals; Python 3.11 for tooling and the verifier. Python files are written with `newline="\n"` on Windows; `.gitattributes` normalises the rest.
- **Data format.** Newline-delimited JSON canonical; SQLite mirror.
- **License.** CC BY 4.0 content; MIT code.
- **Attribution.** `Co-Authored-By: Claude ...` trailers.
- **Voice-print.** No em dashes in any authored markdown.
- **Order of precedence.** Charter > Invariants > Rubric > Bylaws > Methodology and companions > everything else.
- **Usage.** Jared's budget sets the scale of any fan-out, not the availability of the instrument.

## The through-line

This is a young repository built on old discipline. The Vera and errata records are its family; when in doubt, read from them. On this machine the Vera checkout can sit on a feature branch that lacks the identity files; read them from `origin/main` with `git show`, as CLAUDE.md says.

When you finish a step, update this file in the same commit. Read the [Charter](../../CHARTER.md) before you start. If you cannot recall the five vows, come back.
