# Security

Oath's threat model is broader than a typical project's because the register itself is a security surface: the reader's trust depends on the machinery. This file names what to report, how, and what happens next.

## What counts as a security issue

Three categories. Each has its own reporting path.

### 1. Traditional software vulnerabilities

Secrets committed to git, dependency vulnerabilities, injection paths, supply-chain compromise of an adapter, a verifier that returns OK on a tampered file, a hash collision path, a URL parser that misroutes to a look-alike host.

**How to report.** Open a private security advisory via GitHub's *Security → Advisories → New draft security advisory* on this repository. Include what you observed, how to reproduce, and where you tested. If you cannot use GitHub advisories, email the Maintainer with subject `[Oath security] <one-line summary>`; the Maintainer's public email is on their commits.

**What we commit to.** Acknowledgement within seven days. A written assessment within thirty days. A public write-up in the build's release notes once the fix is out, with credit to the reporter (or anonymity, at the reporter's request).

### 2. Evidence-chain issues

An evidence bundle that fails verification against its recorded hash. A Wayback capture that does not match our stored bytes. A supersession that leaves the chain unwalkable. A row that appears to have been silently edited between builds. An OpenTimestamps proof that does not commit to what the row claims.

**How to report.** These are integrity issues, and integrity is the whole product. Report as *Traditional software vulnerabilities* above, and include the specific `filing_id`, the `content_hash`, and the discrepancy you observed. The response cadence is the same, but the fix will produce a supersession row per Charter Vow V, so the reader who checks later sees exactly what changed and when.

### 3. Editorial and register-integrity issues

Verdict language that made it past the lint. A Signal that fires against structurally similar cases unevenly by party. A page that renders an officeholder without the frame. A correction request handled off-the-record. A source cited as primary that is actually an aggregator.

**How to report.** Open a normal issue or pull request naming the specific row and the specific rule you believe is being broken. These are not private matters; they are exactly the things the register exists to make checkable in public. The Council may be convened per [COUNCIL.md](COUNCIL.md).

## What we ask you not to do

- **Do not test on production data in ways that pollute the register.** If you need to probe a fictional case, use the fixtures under `fixtures/`. If you need to test against a real filing, do so read-only through the source itself.
- **Do not scrape the sources on the register's behalf.** Every source's terms of service govern its own access; contributors do not fetch on Oath's behalf outside the adapters and their documented cadences.
- **Do not publish a vulnerability that could be used to fabricate a Finding before the fix is out.** A demonstration that "here is how one would fake a filing citation" is a legitimate research finding; a live fake filing linked from a public thread is not.

## What we will not do

- **Not sue you for reporting in good faith.** This is a good-faith safe harbor for security research consistent with the DMCA §1201(j) research exception and the CFAA's authorized-access defense as those apply to public data. We do not authorize testing that goes beyond public data (do not attempt to access private state), but we will not pursue action against a reporter who tests within that boundary and reports what they find.
- **Not silently patch.** Every fix ships with a public note in the build's release notes and, where the finding affected published Findings, a supersession chain the reader can walk.

## The reader's independent verification

The register's design assumes that the reader may not trust us. Every published Finding can be verified independently through the paths in [PIPELINE.md §7](PIPELINE.md) and [EVIDENCE.md §5](EVIDENCE.md): the sealed record, the OpenTimestamps anchor against Bitcoin, the Wayback capture, and the IPFS pin. If any of those paths returns a different answer than the register's own, that is itself a security report of the most valuable kind.

Report what you find. The register is stronger for it.
