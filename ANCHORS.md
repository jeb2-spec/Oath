# Anchors

The public ledger of every published Oath build, its integrity digest, and its third-party anchor state. This file is the reader's answer to *"how do I know this record was not quietly rewritten after publication?"*

Every build sealed with the verifier is anchored by committing its digest to an external, timestamped, third-party witness that the project's authors cannot rewrite. The reference anchor is OpenTimestamps against the Bitcoin blockchain; the practice is inherited from the sibling *errata* project.

A build made where the OpenTimestamps calendar servers cannot be reached ships with its anchor state marked **owed**, and this file says so. It does not ship a proof of a different file.

---

## Table

*No published builds yet. The founding is a private-repo prospectus; the first anchored build lands with the first Signal fired against real data (per NEXT.md Phase 3).*

Once builds are published, the table below fills in this shape:

```
| Build id       | Digest (SHA-256, prefix) | Built at (UTC)        | Anchor state | Bitcoin block | Note |
| -------------- | ------------------------ | --------------------- | ------------ | ------------- | ---- |
| oath-2026-XX   | abcdef01…                | 2026-XX-XX T HH:MM:SS | confirmed    | 869XXX        |      |
| oath-2026-YY   | 12345678…                | ...                   | pending      | -             | awaiting aggregation |
| oath-2026-ZZ   | fedcba98…                | ...                   | owed         | -             | calendars unreachable at build; retry recorded in build log |
```

## Fields

- **Build id.** The maintainer-assigned identifier for the build. Convention: `oath-YYYY-MM-DD-N` where N is the day's build sequence (typically 1).
- **Digest.** The SHA-256 of the canonical serialisation, prefix printed for display (full digest is inside the sealed record).
- **Built at.** ISO 8601 UTC timestamp of the build.
- **Anchor state.** One of:
  - **confirmed.** The anchor's Bitcoin block header has been observed and the proof verifies against it.
  - **pending.** The OpenTimestamps calendars received the digest; the proof exists but the Bitcoin block containing the merkle root has not yet been confirmed.
  - **owed.** The calendars could not be reached at build time. A retry is scheduled and recorded in the build log.
- **Bitcoin block.** The block height that confirms the anchor, when confirmed.
- **Note.** Human-readable annotation. Standing conventions: `calendars unreachable at build`, `retried at YYYY-MM-DD and confirmed`, `stamp owed`, `superseded by build X`.

## How a reader verifies an anchor

The reader does not need to trust this ledger. They walk it themselves. From the checked-out repository:

```bash
# Read the anchor proof (no Bitcoin node required)
pip install opentimestamps-client
ots info data/anchors/<build-hash>.ots

# The value on the line above each `BitcoinBlockHeaderAttestation`
# is the merkle root of that block, byte-reversed. Reverse it,
# look it up on any block explorer, and confirm the two match.

# The one-command version (requires a local Bitcoin node)
ots verify data/anchors/<build-hash>.ots
```

Nothing in that path goes through the project.

## What the anchor proves

- **Integrity.** The register at that build was byte-identical to what the digest names. Nobody has silently altered it since.
- **Timestamp.** The digest existed no later than the Bitcoin block that confirms it. A rewrite dated earlier is impossible.

## What the anchor does not prove

- **Accuracy.** The register at that build may have contained mistakes. The anchor witnesses that they were the mistakes as published, not that they were true.
- **Continuity.** A gap between builds is not covered by any anchor. The reader learns about a gap only by seeing the row.

## When a stamp is owed and later confirmed

The maintainer retries owed stamps on a schedule (recommended: daily). When the retry succeeds, the row is updated in place, its state moves from **owed** to **pending** to **confirmed**, and the update is committed with a note like `retried at 2026-XX-XX and confirmed`. The build's `meta` includes the retry history.

An owed stamp that goes six months without a successful retry is escalated in the build's release notes and in the next Council session as a governance question, per BYLAWS.md §2.

---

*The first row of this table will be a small moment. It is the register saying, to any stranger who wants to check, that the first published Finding is exactly what the digest names. That is the whole promise of the project, made in one row.*
