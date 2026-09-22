# Ecosystem

How this repository becomes a public artifact people can use, how it feeds a broader ecosystem beyond itself, and the symbolic design that makes it unmistakable.

The register is a repository. That is where the ground truth lives, cryptographically sealed and reproducible. The ecosystem is what lets that truth reach a reader, a journalist, a researcher, a fellow citizen, or a downstream project without any of them having to trust the register's maintainer to have done the right thing.

Everything in this file is a plan, not a shipped surface. It is committed at the founding so a future contributor arriving at any part of the ecosystem work knows what shape it is meant to take.

---

## 1. The website

A simple, static, symbolic surface at `oath.<domain>` (domain choice deferred). Its job is to make the register readable by a person without a subscription, without a law degree, and without a database client.

### 1.1 Principles

- **Static, prerendered, edge-cached.** No user accounts, no comment forms, no interactive analytics beyond a privacy-respecting counter, no client-side JavaScript that changes what the page says.
- **The frame appears on every officeholder page.** Presence in the register is not evidence of wrongdoing. Enforced by INVARIANTS.md §7.
- **The cite-the-build line appears on every page.** Every page prints the digest of the build it was generated from, and a `verify this` link.
- **No cross-officeholder ranking.** Enforced by INVARIANTS.md §13. The index sorts by office and jurisdiction, or alphabetically, never by signal count.
- **Renders in light and dark themes.** No brand-loud color. The document typography from the errata project (rule-weight hierarchy, hung mono indices, small-caps section labels) carries here.
- **Works with JavaScript disabled.** JavaScript enhances; the page reads without it.

### 1.2 URL structure

```
/                        landing (prospectus + charter + one worked example)
/charter                 the CHARTER
/rubric                  the RUBRIC
/invariants              the INVARIANTS
/bylaws                  the BYLAWS
/council                 the COUNCIL doc
/methodology             the METHODOLOGY
/limitations             the LIMITATIONS
/standards               the STANDARDS
/sources                 the SOURCES (with adapter status per source)
/verify                  the reproduction page (verifier + tamper-test + walk-through)
/officeholders           the index (sortable by name, office, jurisdiction)
/officeholders/{id}      per-officeholder page
/signals                 the library of defined Signals
/signals/{slug}/{ver}    per-Signal page (definition, standard cited, criteria, findings)
/anchors                 the ANCHORS ledger (every build, its seal, its stamp state)
/corrections             the corrections trail (Oath-specific rows + link to errata)
/about                   history, governance, disclosures
/mark/{id}.svg           per-officeholder struck seal (see §2)
/mark/build.svg          the build's Oath mark
```

### 1.3 Per-officeholder page (the anatomy)

The page a reader arrives at when they look up their Representative or Senator. Every element on it is a specific piece of the register, cited to its source.

```
─────────────────────────────────────────────────────────────
[frame line, presence is not proof]
Name (legal, as filed)                                  [mark]
Office · Jurisdiction · Term
─────────────────────────────────────────────────────────────

FILINGS
  Year · Form type · Filed · Source URL · Retrieved
  ...

SIGNALS FIRED (grouped by signal, not by severity)
  Signal name (version)                     STANDARD ref
    Finding date · Producing filings
    Description text
    Why: standard citation and criterion
    Reproduce: `tools/rebuild <finding-id>`
  ...

SIGNALS THAT DID NOT FIRE (defined signals, no finding)
  Signal name (version) · reason: no criterion met

─────────────────────────────────────────────────────────────
BUILD: <digest>  ANCHOR: <state>  CITE THIS BUILD: <cmd>
```

The page is a static file. It is regenerated on every build. The mark in the top-right is struck from the officeholder's identifier and the build digest, per §2.

### 1.4 The landing page

Two paragraphs, one call to action, one worked example.

```
OATH

A public register reconciling what U.S. elected officials swore
to uphold with what the record shows.

Look up an officeholder:
  [ search or index link ]

Read one example in full:
  [ link to the first published worked example ]

Understand the discipline:
  [ Charter (five vows) ]
```

The landing is the door. The Charter is one click behind it. The example is one click behind it. The index is one click behind it. Nothing else on the landing.

### 1.5 Technology

Deferred until Phase 5. Recommended: Astro (static-first, minimal JS, MDX support) or 11ty. Hosted on Cloudflare Pages or GitHub Pages. The site build is triggered by every merge to `main`; the build reads the sealed NDJSON in the repo and produces static HTML.

## 2. The Oath mark

The symbolic move that makes the project recognisable.

### 2.1 The concept

A **wax seal rendered as guilloche**, struck from the build's SHA-256 digest. Wax seals have carried an oath's authority for centuries: a person's word made physical, witnessed by an impression that could not be counterfeited by anyone without the die. The digital seal is the modern die. The guilloche is the two-hundred-year-old anti-forgery craft the errata project already uses. Guilloche + wax seal = an oath, verified.

Change one row of the register and the mark changes. Cannot be counterfeited without the die (the build's digest). Beauty and verification are the same move.

### 2.2 Per-officeholder seal

Each Officeholder's page carries their own struck seal, parameterised by:

- The Officeholder's identifier (`oh:us:...`) hashed to seed the guilloche rosette.
- The build's digest, so the seal changes when their record changes.
- A ring around the seal's edge with one tick per Signal defined against them, and one bar per Signal that fired.

The reader who sees the same seal twice knows the record has not changed. The reader who sees a different seal on the same URL knows it has.

### 2.3 The build mark

Every build produces a single Oath mark, seeded from the build's digest. This mark:

- Appears at the top of the landing page.
- Is embedded in the OpenTimestamps proof file's directory.
- Is the image the project uses in cross-references from Vera, errata, and ellebee.

### 2.4 Craft rules

- **Struck, not drawn.** The mark is emitted by a script (recommended path: `tools/strike-mark.mjs`, following errata's pattern) that computes guilloche from the seed. A hand-drawn version of the mark is a picture of proof, not proof itself.
- **Type as outlines.** Any lettering (the word *oath*, the digest prefix) is embedded as outlines, not as font requests, so a browser without the font renders identically.
- **A gate strikes and verifies.** Following the errata `check-mark.mjs` precedent, a CI gate strikes the mark against a range of digests and confirms the geometry stays legible (the ring is not clipped, the ticks land on the ring, the wordmark scales correctly). CI fails on any violation.

*Landed 2026-09-22* as `tools/strike-mark.py` and `tools/check-mark.py`, standard-library Python rather than the `.mjs` path recommended above, for the reason recorded in `src/README.md`: one language writes and seals the record. On that date errata's `tools/` held no mark generator, so the precedent named here did not yet exist and Oath's is the first; the pattern is errata's guilloche, not errata's code.

## 3. The consumer contract

Third-party consumers (journalists, researchers, downstream registers, aggregators) may build on Oath. The contract they hold us to and we hold them to is short.

### 3.1 What consumers may do

- Read the sealed NDJSON and derived Findings.
- Cite Findings by their id and the build's digest.
- Republish Findings in accordance with the CC BY 4.0 license, with attribution and the frame preserved.
- Fork the schema, the tooling, and the SPEC to build a register for another jurisdiction or subject.

### 3.2 What consumers must do

- Cite the build. `oath@<digest>` identifies a specific record. Citing `oath.<domain>` without a digest identifies the moving current.
- Preserve the frame. Any surface that shows an Officeholder's Finding must show the *presence is not proof* frame nearby.
- Preserve the source trail. A republished Finding cites the primary source the Finding cites.
- Not use the register for verdicts. Findings are descriptions. A republisher who prints *"Officeholder X is corrupt"* citing an Oath Finding is misusing the citation; nothing in the CC BY license permits misrepresentation.

### 3.3 What Oath commits to consumers

- No breaking schema changes without a version bump and a migration.
- Every build sealed and anchored. Deleted or altered rows appear in `corrections` with `superseded_by`.
- A stable read-only download endpoint at `oath.<domain>/download/<build>.zip` (once Phase 5 ships), containing the NDJSON, the seal, and the anchor proof.
- No advertising, no tracking, no dark patterns on the public site.

## 4. The fork-friendly design

Oath's method is not proprietary. Any subject with a public record can be held to a similar register, and the intent is that the shape of this repository lets that be true.

- **SPEC.md** (planned, in progress) documents what any register in Oath's shape must satisfy. A fork of this project for a different jurisdiction or a different subject population that meets SPEC.md is a valid Oath-shaped register.
- **The schemas are portable.** JSON Schema draft-2020-12. Any language can produce and consume rows.
- **The verifier is standard-library only.** A fork can rewrite it in any language without importing this project's code.
- **The Council prompt is CC BY 4.0.** Forks may use it verbatim or adapt.
- **The Charter and Rubric are CC BY 4.0.** Forks may reproduce them as the founding of their own project.

## 5. Relationships to sibling projects

Oath does not exist alone. It is part of a family whose spine is *proof over reputation*, and each sibling holds part of that spine.

- **Vera** (`jeb2-spec/Vera`). A record beats a reputation. Vera is the origin repo and the environment in which this discipline was formed. Oath extends the discipline to public officeholders.
- **errata** (`jeb2-spec/errata`). The corrections record for the family. Oath's own corrections trail is a subset of errata's when a correction concerns Oath's published Findings.
- **ellebee** (`jeb2-spec/ellebee`). The sibling assistant. Its stance on trust ("silence is the failure mode") applies to Oath's operational monitoring once the register is public: a build that fails to publish is a signal to a human, not a quiet day.

Cross-linkage is by human hyperlink, not by build coupling. Each sibling remains independent.

## 6. What ecosystem work happens when

- **Phase 3.** The per-officeholder page template and the mark generator land as part of the first live per-officeholder page. Static site scaffold minimal (single page rendered by hand or by a small script).
- **Phase 4.** The `/signals` index and the per-signal pages land as part of the second Signal.
- **Phase 5.** Full static site build, edge deployment, domain, download endpoint, ANCHORS.md ledger public.
- **Phase 6.** SPEC.md finalised; first external fork encouraged (a state-level Oath, or a subject-population Oath).

The ecosystem is not the point of the project. The register is the point. The ecosystem exists so the register reaches the reader.
