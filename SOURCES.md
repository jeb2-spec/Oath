# Sources

Every row of record in Oath enters through an adapter registered here. An adapter names its primary source, its retrieval cadence, its throttling policy, its rate-limit posture, its terms-of-service constraints, and its known gaps.

This file grows as coverage extends. At the founding, no adapter is implemented; every entry below is a planned source with the information a maintainer or contributor needs to build the adapter honestly.

## Federal — primary

### F.1 — U.S. House Financial Disclosures
- **URL.** <https://disclosures-clerk.house.gov/FinancialDisclosure>
- **Publisher.** Office of the Clerk of the U.S. House of Representatives.
- **Forms.** Financial Disclosure (annual), Periodic Transaction Report (PTR).
- **Formats.** PDF (individual filings), XML/CSV bulk (annual index).
- **Retention.** Six years post-filing.
- **Terms.** Public documents. Bulk downloads are permitted.
- **Known gaps.** Older filings are scanned images; extraction is bounded by OCR quality. PTRs are often incomplete descriptions of underlying transactions.
- **Adapter status.** Planned.

### F.2 — U.S. Senate Financial Disclosures
- **URL.** <https://efdsearch.senate.gov>
- **Publisher.** Office of Public Records, Secretary of the Senate.
- **Forms.** Financial Disclosure Report (annual), Periodic Transaction Report (PTR).
- **Formats.** HTML web forms with paginated results; no bulk download; captcha on the search interface.
- **Retention.** Six years post-filing.
- **Terms.** Public documents; the interface asks users to agree to a use policy before searching. The adapter honours the policy.
- **Known gaps.** Absence of bulk download imposes a per-filing retrieval cost; adapter throttling must be conservative.
- **Adapter status.** Planned.

### F.3 — U.S. Office of Government Ethics — Executive Branch Form 278e
- **URL.** <https://extapps2.oge.gov/Web/278eFiling.nsf>
- **Publisher.** Office of Government Ethics (OGE).
- **Forms.** OGE Form 278e (public financial disclosure for senior Executive Branch officials).
- **Formats.** PDF via a search interface.
- **Retention.** Six years post-filing.
- **Terms.** Public documents.
- **Known gaps.** Coverage is limited to senior officials as defined by 5 U.S.C. app. 4 § 101; a large population of federal employees files the confidential OGE-450, which is not public.
- **Adapter status.** Planned.

### F.4 — Federal Election Commission (FEC)
- **URL.** <https://www.fec.gov/data/>
- **API.** <https://api.open.fec.gov/developer/>
- **Publisher.** Federal Election Commission.
- **Forms.** Form 3 (candidate committees), Form 3X (other political committees), Form 3P (presidential), Form 5 (independent expenditures), Form 24 (48-hour reports), and others.
- **Formats.** Well-documented JSON API with rate limits; bulk CSV downloads.
- **Retention.** Permanent.
- **Terms.** API requires a free registered key. Terms are permissive for civic use.
- **Known gaps.** Committee-to-candidate linking is not always clean; small in-kind contributions may go unreported below thresholds.
- **Adapter status.** Planned.

### F.5 — U.S. Senate Lobbying Disclosure Act database
- **URL.** <https://lda.senate.gov/system/public/>
- **Publisher.** Secretary of the Senate.
- **Forms.** LD-1 (registration), LD-2 (quarterly activity), LD-203 (semiannual contribution report by registered lobbyists).
- **Formats.** XML bulk downloads.
- **Retention.** Permanent.
- **Terms.** Public documents.
- **Adapter status.** Planned.

### F.6 — U.S. House Lobbying Disclosure
- **URL.** <https://disclosurespreview.house.gov/>
- **Publisher.** Clerk of the U.S. House.
- **Formats.** XML.
- **Adapter status.** Planned (mirror of F.5 for House-side filings).

### F.7 — Congress.gov (legislative activity)
- **URL.** <https://www.congress.gov>
- **API.** <https://api.congress.gov>
- **Publisher.** Library of Congress.
- **Data.** Bills, votes, committee memberships, member biographies.
- **Formats.** REST API with API key; bulk XML from GPO's govinfo.
- **Terms.** Public. Rate limits documented.
- **Adapter status.** Planned. Needed to reconcile filings against legislative activity.

## Federal — corroborating (aggregators, cited never sole)

- **OpenSecrets** — <https://www.opensecrets.org> — Center for Responsive Politics; comprehensive campaign finance and lobbying, with lobbying-issue coding and reconciliation not in the primaries.
- **ProPublica Represent** — <https://projects.propublica.org/represent/> — congressional votes, statements, and financial disclosures with a well-designed API.
- **Ballotpedia** — <https://ballotpedia.org> — encyclopedic coverage of federal, state, and local officeholders; useful for identity resolution.
- **LegiStorm** — <https://www.legistorm.com> — congressional staff, salaries, foreign travel gifts.
- **Follow the Money** — <https://www.followthemoney.org> — National Institute on Money in Politics; deep state-level campaign finance.
- **MapLight** — <https://maplight.org> — money-and-influence analysis, with issue-level joins.
- **GovTrack** — <https://www.govtrack.us> — legislative tracking; long-lived.
- **Capitol Trades** — <https://www.capitoltrades.com> and **Unusual Whales congressional trading** — <https://unusualwhales.com/politics> — STOCK Act trade tracking with UX suited to lay readers.
- **CREW** — <https://www.citizensforethics.org> — Citizens for Responsibility and Ethics in Washington; enforcement filings and investigative work.

**Rule.** An aggregator is cited alongside the primary source it drew from. Where the two disagree, the primary source is authoritative and the disagreement is recorded on the row.

## State coverage

States are added per coverage. Each state entry follows the shape:

### [STATE] — [Ethics Commission or equivalent]
- **URL.**
- **Publisher.**
- **Forms.**
- **Formats.**
- **Retention.**
- **Terms.**
- **Known gaps.**
- **Adapter status.**

Priority states (populous, machine-readable, high officeholder density) will be documented first: California, New York, Texas, Florida, Illinois. The state coverage matrix — which states have adapters, which are pending, which are known infeasible without paper retrieval — will be maintained as a table in this file as adapters land.

## Local coverage

Most county, municipal, and school-board offices have no financial disclosure requirement. Where a locality does maintain a disclosure regime (New York City, Los Angeles, Cook County, San Francisco), an adapter is added under a `LOCAL.` prefix following the state shape.

## How to add a Source

Sources are added by pull request. The template requires:

1. The primary source URL.
2. The publisher (the official body that maintains it).
3. The forms and formats.
4. The retention policy.
5. The terms of service, verbatim where restrictive.
6. Known gaps or extraction constraints.
7. The adapter, or a note that the adapter is deferred and why.

A source is not a permission to ingest. A source is a description of a public record and the honest constraints on retrieving it.
