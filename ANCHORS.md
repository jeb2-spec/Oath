# Anchors

The public ledger of every published Oath build, its integrity digest, and its third-party anchor state. This file is the reader's answer to *"how do I know this record was not quietly rewritten after publication?"*

Every build sealed with the verifier is anchored by committing its digest to an external, timestamped, third-party witness that the project's authors cannot rewrite. The reference anchor is OpenTimestamps against the Bitcoin blockchain; the practice is inherited from the sibling *errata* project.

A build made where the OpenTimestamps calendar servers cannot be reached ships with its anchor state marked **owed**, and this file says so. It does not ship a proof of a different file.

---

## Table

Written by `python tools/anchor.py --ledger` from the files under [`data/anchors/`](data/anchors/), never by hand. `python tools/anchor.py` fails CI when this table and the proofs disagree, or when a proof does not commit to the manifest beside it.

<!-- anchors:table:start (written by tools/anchor.py --ledger; do not edit by hand) -->
| Build id | Digest (SHA-256, prefix) | Built at (UTC) | Anchor state | Bitcoin block | Note |
| --- | --- | --- | --- | --- | --- |
| `0005-house-2025` | `6a28c538b177ca4a…` | 2026-09-23T14:13:28Z | confirmed | 968733 |  |
<!-- anchors:table:end -->

The rendered register has been public on GitHub Pages since 2026-09-23 and the repository since 2026-09-26. Builds before `0005-house-2025` were sealed and never stamped, and are not stamped now: a stamp made today proves only that a digest existed today, which says nothing about the day those builds were published.

## Fields

- **Build id.** The build's identifier as `data/meta.json` gives it: its sequence number, the adapter, and the filing year.
- **Digest.** The build's seal, printed by its first sixteen characters. It is the SHA-256 of the build's manifest, `data/anchors/<build>.manifest`, which lists every sealed file with its own SHA-256.
- **Built at.** The build's `built_at`: the retrieval time of the latest capture it read, never the clock.
- **Anchor state.** Read from the proof, never typed:
  - **owed.** The manifest is written and no proof exists yet: the calendars could not be reached, or the scheduled job has not yet run. The job retries daily.
  - **pending.** The OpenTimestamps calendars hold the digest; the proof names no Bitcoin block yet.
  - **confirmed.** The proof names a Bitcoin block header, at the height shown. Checking that header against the block is the reader's walk, below.
- **Bitcoin block.** The height the proof names, when it names one; the lowest, when it names several.
- **Note.** A standing phrase for the state.

## How a reader verifies an anchor

The reader does not need to trust this ledger. They walk it themselves, from the checked-out repository:

```bash
# The manifest is the seal: its SHA-256 is the digest in that build's data/meta.json.
sha256sum data/anchors/<build>.manifest
python tools/verify.py --manifest | sha256sum    # the current build's, recomputed from the tree

# The proof commits to that same hash, and names the blocks that hold it.
pip install opentimestamps-client
ots info data/anchors/<build>.manifest.ots

# With a local Bitcoin node, the one-command check. Each proof sits beside the exact file it
# proves, so this works for every build, not only the latest.
ots verify data/anchors/<build>.manifest.ots
```

Without a node, `ots -v info` prints every intermediate value, and the one on the line above each `BitcoinBlockHeaderAttestation` is that block's merkle root, byte-reversed. Reverse it, look the block up on any block explorer, and confirm the two match. Nothing in that path goes through the project.

## What the anchor proves

- **Integrity.** The register at that build was byte-identical to what the digest names. Nobody has silently altered it since.
- **Timestamp.** The digest existed no later than the Bitcoin block that confirms it. A rewrite dated earlier is impossible.

## What the anchor does not prove

- **Accuracy.** The register at that build may have contained mistakes. The anchor witnesses that they were the mistakes as published, not that they were true.
- **Continuity.** A gap between builds is not covered by any anchor. The reader learns about a gap only by seeing the row.

## When a stamp is owed and later confirmed

The weekly refresh (`.github/workflows/refresh.yml`) stamps each new build as soon as it seals it, so the pull request that proposes the build carries its manifest and its pending proof. The anchor workflow (`.github/workflows/anchor.yml`) runs on every push to `main` that seals a build and once a day. It stamps the current build if it has no proof, retries every owed stamp, and completes every pending proof once Bitcoin holds it, then opens a pull request with the proofs and this table. A proof is only ever added to or completed; a manifest is never rewritten; the history of both is the git history of `data/anchors/` and of this file. A stamp the calendars cannot take is recorded as owed in that pull request, and the run then fails and says so in an issue, rather than pass quietly.

An owed stamp that goes six months without a successful retry is escalated in the build's release notes and in the next Council session as a governance question, per BYLAWS.md §2.

---

*The first row of this table will be a small moment. It is the register saying, to any stranger who wants to check, that the first published Finding is exactly what the digest names. That is the whole promise of the project, made in one row.*
