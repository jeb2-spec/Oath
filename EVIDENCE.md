# Evidence

*How the register captures a source's bytes so that the citation survives the source itself, the platform under it, the internet's decay, and the rising tide of fabricated content.*

Every claim in Oath rests on a filing at a URL. Every URL is a bet on the future, that a host, a domain, a CDN, a filesystem, and an organisation will all still be exactly where they were when we captured the row. That bet is losing more often every year. Studies of legal and academic citations show that half of URLs die within a decade. Government sites migrate platforms and drop legacy URL schemes. Content is edited silently. Content is removed at the source with no notice. And in front of all of that, a rising fog of AI-generated documents makes independently verifying what a source *actually said* harder every quarter.

The register cannot survive that fog unless the evidence it cites survives independently of the fog. This document is how.

The design principle is simple to state and requires the whole rest of the document to make real: **a row does not rely on any single witness. Every row of record is captured against the source in a way that at least three independent parties can verify years later, without contacting us and without the source having to still exist.**

---

## 1. The threat model, named

We name each failure the design has to survive so the design's decisions are readable against them.

**Link rot.** The URL that cited the filing returns 404, redirects to unrelated content, or resolves to a paywall. The captured *bytes* are still real; only the *address* has decayed.

**Silent editing.** The URL still resolves, but the content behind it has been altered since we captured it. Without a captured copy and a hash, we cannot show what the source said at the time we cited it.

**Deplatforming and migration.** The source moves from one URL scheme to another (a common government pattern, the House migrated its financial disclosure portal at least twice in the last decade). The old URLs die; the new URLs are unknown to old citations.

**Aggressive edge caching and geo-blocking.** A CDN serves different bytes to different regions, at different times, based on user agent. The reader today might not see what we captured yesterday, and both captures might be "correct" from the source's perspective.

**Deliberate takedown.** A source removes content at a subject's request, under legal pressure, or as a matter of policy change. In some cases this is legitimate; in every case the register's citation to it must not evaporate with the source.

**Adversarial submission.** An actor submits a fabricated filing to a source that gets published (temporarily) before being caught. If we cited it during that window and the source silently reverses, both directions of the record disappear.

**AI-generated content in the wild.** Not on our side (we disclose our AI collaborator); on the sources'. A political operative generates a plausible-looking filing image and hosts it at a look-alike URL. A reader who trusts a URL that looks right, without a hash they can check, has been sold a fake.

**CDN spoofing and TLS interception.** Even the direct source URL can be intercepted upstream. A hash captured at retrieval time is the only defence against a MITM the reader cannot see.

**Institutional decay.** Wayback Machine, IPFS pinning services, archive.today, or the register's own domain could disappear on any timescale from *tomorrow* to *fifty years*. The design has to survive any one of them going dark.

**Long-tail correctness.** A citation from a paper written this year might be checked in the year 2100. The evidence has to make that reader's job possible.

## 2. The three-witness principle

For evidence to survive scrutiny across decades, no single party can be the sole witness to the capture. We aim for **at least three independent witnesses** on every row that enters the register, plus a fourth (the register's own retained copy) that a reader can verify against any of the others.

The four witnesses:

1. **Our own capture.** The adapter fetched the URL, recorded the response bytes, and stored them locally in the repository. The bytes are cryptographically hashed at retrieval time.
2. **A public web archive.** The Internet Archive's Wayback Machine (`https://web.archive.org/save/<url>`) is submitted at retrieval time. Archive.today (`https://archive.ph`) is submitted as a second archive where the source permits it.
3. **Content-addressable storage.** The captured bytes are pinned to IPFS with a stable CID (content identifier). A pin exists at at least two pinning services (initial: `pinata` and `web3.storage` or their successors). Optionally, for critical filings, an Arweave upload provides pay-once-store-forever durability.
4. **Third-party timestamp.** The hash of the captured bytes is committed to OpenTimestamps and, through it, to the Bitcoin blockchain. This proves *when* we captured what we captured, independent of any file store.

No two of the four witnesses are subject to the same failure mode:

| Failure | Our capture | Wayback | IPFS | OpenTimestamps |
| --- | --- | --- | --- | --- |
| Source URL rot | intact | intact | intact | intact |
| Source silent edit | intact + provable | intact + provable | intact + provable | proves when we saw the earlier state |
| Our organisation compromised | corrupt | intact | intact | intact |
| Internet Archive dark | intact | dark | intact | intact |
| IPFS pinning services dark | intact | intact | dark | intact |
| Bitcoin dead as a witness | intact | intact | intact | dark |
| Adversarial replay | our hash rules | different hash | different CID | can't backdate |

A row cited from Oath at any point in the future can be verified by any single one of witnesses 1–3, with witness 4 confirming the capture predates any adversary's post-hoc fabrication.

## 3. What we capture, per row

For every filing that enters the register, the adapter records:

- **The URL** the response was fetched from, including its final URL after redirect chain.
- **The response bytes**, in the format the source served (PDF, HTML, XML, JSON, whichever), stored at `data/captures/<filing-id>/response.<ext>`.
- **The response headers** (Server, Content-Type, Content-Length, Last-Modified, ETag, Cache-Control, and any Content-Digest header the source emits), stored at `data/captures/<filing-id>/headers.json`. Headers are hashed alongside the bytes to preserve the source's own metadata about what it served.
- **The retrieval timestamp** (ISO-8601 UTC) at which the response was received.
- **The adapter identity**: `<adapter-name>@<adapter-version>`, so the code path that fetched the bytes is traceable.
- **The SHA-256 hash** of the response bytes (`content_hash`).
- **The Wayback submission**: the Wayback Machine URL of the capture at retrieval time (`wayback_url`, filled once the archive confirms).
- **The archive.today submission** (`archive_today_url`), where the source permits.
- **The IPFS CID** for the captured bytes (`ipfs_cid`).
- **The OpenTimestamps proof** for the SHA-256, stored at `data/captures/<filing-id>/hash.ots`.
- **Extraction confidence** (per `schemas/filing.schema.json`): whether the row's structured fields were extracted from a structured source (JSON, XML, CSV), OCR of a scanned PDF, or manual entry. OCR-derived fields are flagged in downstream Findings.

## 4. The evidence bundle

Every filing has an evidence bundle: a directory `data/captures/<filing-id>/` with a fixed shape.

```
data/captures/<filing-id>/
├── response.<ext>        the exact bytes the source served
├── headers.json          the response headers, sorted by key
├── metadata.json         URL, retrieval timestamp, adapter, hashes,
│                         witness URLs and CIDs
├── hash.ots              OpenTimestamps proof of SHA-256(response.<ext>)
├── wayback.url           the Wayback capture URL (one line)
├── archive_today.url     optional; the archive.today capture URL
└── ipfs.cid              the IPFS CID (one line)
```

The bundle is byte-identical to a reader who clones the repo. The bundle's `metadata.json` is what the schema's `source.*` fields point at.

**Bundle stability rule.** A bundle is written once, at the retrieval that created the filing row, and never modified. Later retrievals of the same filing (say the source amends it) create a *new* bundle at a new filing id (`fl-…-r2`, `fl-…-r3`), with a supersession row per Vow V. The old bundle stays intact; the new bundle records what changed.

## 5. The verification path a reader walks

The reader who wants to check a Finding from any year, without contacting the register's authors:

1. Reads the Finding on the page or in the exported record. It names the `filing_id` and the `content_hash`.
2. Opens `data/captures/<filing-id>/response.<ext>`, the captured bytes. Locally on disk after a clone.
3. Computes SHA-256 of the file and compares to `content_hash`. Match.
4. Runs `ots info data/captures/<filing-id>/hash.ots`. The proof commits the hash to a specific Bitcoin block, at a date the register cannot rewrite.
5. **Independent verification path A.** Opens `data/captures/<filing-id>/wayback.url` and visits the Wayback capture. It should render the same content the reader has on disk; the reader can view the source's response as archived by an unrelated party.
6. **Independent verification path B.** Runs `ipfs cat $(cat data/captures/<filing-id>/ipfs.cid) | sha256sum` (or uses a public IPFS gateway). The bytes returned hash to the same `content_hash`.
7. **Independent verification path C.** If the source URL still resolves, the reader fetches it and hashes the result. A match confirms the source has not changed. A mismatch is not the register's failure, it is a signal that the source changed after we captured it, and the register's row shows what the source said *at retrieval time*.

Any one of the three independent paths (Wayback, IPFS, or a live source URL) confirms the register's capture. Two agreeing rules out most adversarial scenarios. Three agreeing is overwhelming.

## 6. Failure modes and what still holds

Enumerated so the design's guarantees can be read alongside its concessions.

**One witness goes dark.** Any single one of witnesses 1–4 can disappear and the row still verifies through the other three. The row's page annotates the dark witness so the reader knows which paths still work.

**Two witnesses go dark.** Two independent verification paths remain. Practically, this covers the scenario where our organisation is compromised *and* the source URL rots. Wayback and IPFS both still hold the bytes; OpenTimestamps still proves when we captured them.

**Three witnesses go dark.** One path remains. This is the survival floor. The design does not promise more than one path in the worst case; it promises that no single failure eliminates the evidence.

**All four go dark.** The evidence is unrecoverable. This is possible in principle; the design chooses witnesses precisely to make it improbable. Bitcoin, the Internet Archive, IPFS as an ecosystem, and the register itself would all have to fail together. If that has happened, checking Oath is not the reader's biggest problem.

**Adversary claims we forged a capture.** OpenTimestamps proves the hash existed no later than the Bitcoin block it commits to. The Wayback capture at the same retrieval timestamp is a wholly independent witness. Forgery would require rewriting Bitcoin history and Wayback simultaneously.

**Source content contains AI-generated forgery.** Not the register's failure to detect. The register records *what the source served*. If the source later retracts, a supersession row (Vow V) records the retraction and cites the source's own correction. The historical row stays, marked with the retraction.

**Source silently edits a filing in place.** The register's capture proves what the source said at the time we read it. A future rehydration of the URL will show a mismatch to `content_hash`, at which point a new filing id and a supersession row are created for the current state, and both are preserved.

## 7. Legal posture on retained bytes

**Federal government works are public domain** (17 U.S.C. § 105). Every filing published by the House Clerk, the Secretary of the Senate, the Office of Government Ethics, the FEC, and their siblings is uncopyrighted. The register may retain and redistribute the bytes.

**State-published filings** vary. Most state ethics disclosures are records of the state, published to the public under state open-records laws. Retention is generally permitted; redistribution is generally permitted; the register documents state-by-state exceptions in [SOURCES.md](SOURCES.md) as coverage extends.

**Fair use for verification and citation** is a strong defence in any close case. The register's use is verificatory: the bytes are retained so a reader can confirm a citation is accurate. This is one of the paradigmatic fair uses.

**Personal identifiers on filings.** Some filings include SSNs, home addresses, phone numbers, or dependent names. Adapters are required to scrub these before the bytes enter the canonical capture, per the `redaction-manifest` recorded alongside `metadata.json`. Redaction is deterministic and versioned; if a redaction rule changes, prior captures are re-scrubbed, both bundles retained in the supersession chain.

**Judicial takedown order.** Per BYLAWS.md §6, compliance is documented publicly with the docket number and the order, redacted only to the extent the order requires. The evidence bundle is annotated with the removal reason; witnesses (Wayback, IPFS) survive independently of any local removal.

## 8. Forward-looking: what is coming and how the design absorbs it

**Content Credentials (C2PA).** The emerging standard for signing media with cryptographic provenance from camera through editor through publication. As government sources begin signing their PDFs (the U.S. Government Publishing Office has announced pilots), the register records the signature alongside the bytes. A signed source strengthens verification; an unsigned source is business as usual.

**WACZ (Web ARChive Zipped).** The modern successor to WARC for dynamic web content. The register's default capture is the response bytes; where the source requires JavaScript to render (increasingly common), the adapter uses a headless browser and stores the WACZ file alongside `response.html`. WACZ preserves the network trace and the rendered DOM.

**PDF/A** for archival PDFs where the source serves normal PDFs. Optional. Not converted automatically; a converted archival copy would not have the same hash as the source's bytes and would need its own witness chain.

**Software Heritage** for adapter code. Every adapter's source is archived to Software Heritage as part of the release process; a reader can retrieve the exact adapter that captured a specific filing years later, even if this repository is gone.

**Post-quantum signatures.** SHA-256 is not vulnerable to quantum attack in the way RSA and ECDSA are. Bitcoin's block-header signatures use ECDSA and will migrate; OpenTimestamps rides that migration. The register does not need to act; it inherits the ecosystem's answer.

**Decentralised backup.** As the ecosystem matures, additional durability layers (Storj, Filecoin, Sia) can be added as additional witnesses. Every new witness is additive; no witness is subtractive from the guarantee.

## 9. What this changes in the pipeline

The [Pipeline](PIPELINE.md) Stage 2 (Retrieval) is where the evidence bundle is produced. Making it explicit:

Stage 2 now emits, per fetched filing:
- One canonical NDJSON row (as before).
- One evidence bundle at `data/captures/<filing-id>/` (new).
- One Wayback submission and one IPFS pin (new; asynchronous, retried by a follower job if the primary submission failed).
- One OpenTimestamps stamp of the response hash (new).

A row is not considered complete until its bundle exists on disk *and* at least one external witness (Wayback, archive.today, or IPFS) has confirmed. The gate for this is Invariant §16 (added by this commit). A row with only our own witness ships as *pending-external-witness* and is retried; a row with no external witness after seven days is escalated to the maintainer and, if still failing, moved to the rejected pool so the register never claims a witness it does not have.

## 10. What this design is not

- **Not a replacement for the source.** The register never claims to be the authoritative filing. The source is the authority. The register is the reader's independent verification path when the source is unavailable, unreachable, or has changed.
- **Not a general web archive.** We capture only the filings the register cites, not the surrounding pages, not the source's home page, not the source's terms of service. Those are outside the scope of a Finding.
- **Not perfect against every future adversary.** Sufficiently patient nation-state actors, sufficient computational advances, or sufficient collapses of the underlying infrastructure can eventually defeat any current design. What we can promise is: no *single* failure defeats the evidence, and every witness path is independent of every other.
- **Not free.** IPFS pinning costs. Wayback submission is subject to their rate limits. Storage of the captured bytes grows monotonically. The bylaws' financial posture (no funding, no advertising) means the operational cost is the maintainer's, backed by durable-storage services chosen for their independence rather than their sponsorship. Costs are documented in the build's release notes.

## 11. What a reader in the year 2100 does

Set the frame at the far end of the design.

A researcher in 2100 who wants to cite an Oath Finding from 2027 opens the archived repository (which is itself in Software Heritage, in the Internet Archive, and in whichever future archive succeeds them). They walk to the evidence bundle. The response bytes are there. The hash matches. They compute SHA-256 themselves, an algorithm that still runs, on whatever computer they use, because SHA-256 is a specification a page-long implementation can reproduce from scratch. They check the OpenTimestamps proof, the Bitcoin block it commits to is still visible in whichever archive of the chain has survived.

They do not need us. They do not need the source. They do not need any specific third party. They need:

- One archive of the register.
- One implementation of SHA-256.
- One archive of the Bitcoin block header at the anchor's block height.

That is the shape of a citation that lasts.

The design that makes it possible is what this file specifies.

---

*Read next: [PIPELINE.md](PIPELINE.md) for how the seven stages of the register produce evidence bundles at Stage 2, and [INVARIANTS.md](INVARIANTS.md) §16 for the mechanical gate that keeps every row honest to its witnesses.*
