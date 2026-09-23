# Sources

Every row of record in Oath enters through an adapter registered here. An adapter names its primary source, its retrieval cadence, its throttling policy, its rate-limit posture, its terms-of-service constraints, and its known gaps.

This file grows as coverage extends. At the founding, no adapter is implemented; every entry below is a planned source with the information a maintainer or contributor needs to build the adapter honestly.

## Federal. primary

### F.1. U.S. House Financial Disclosures
- **URL.** <https://disclosures-clerk.house.gov/FinancialDisclosure>
- **Publisher.** Office of the Clerk of the U.S. House of Representatives.
- **Forms.** Financial Disclosure (annual), Periodic Transaction Report (PTR).
- **Formats.** PDF (individual filings), XML/CSV bulk (annual index).
- **Retention.** Six years post-filing.
- **Terms.** Public documents. Bulk downloads are permitted.
- **Known gaps.** Older filings are scanned images; extraction is bounded by OCR quality. PTRs are often incomplete descriptions of underlying transactions. The index carries no person identifier, so the join to an officeholder runs on a name; measured consequences are below. Twelve filing-type codes appear in the 2025 index and no Clerk page read on 2026-09-22 defines them.
- **Retrieval, confirmed 2026-09-22.** The index is at `public_disc/financial-pdfs/<year>FD.zip`, holding a tab-separated and an XML index of the same rows. Documents are served per filing at `public_disc/financial-pdfs/<year>/<DocID>.pdf`, except rows coded `P`, which the Clerk serves from `public_disc/ptr-pdfs/<year>/<DocID>.pdf`. That split is the publisher's own, and is the only reason any code here is interpreted. `robots.txt` returns 404, so no crawl directive is published. The archive is live, not annual: the 2025 file was last modified 2026-09-22, partway through the following year, so it grows as filings arrive and a build states one retrieval rather than one year.
- **The roster, added 2026-09-22.** `https://clerk.house.gov/xml/lists/MemberData.xml`, published by the same Clerk, carries every seat of the current Congress with a `bioguideID`, party, sworn date and committee assignments. It is the primary source for House identity, so officeholder rows need no aggregator and satisfy Invariant §5 directly. On the 2026-09-02 publication it holds 441 seats, 439 filled and 2 vacant; a vacant seat carries no name and no identifier, which is the record's own distinction between an Office and an Officeholder.
- **Measured join quality of the name alone, 2025 index against the 2026-09-02 roster, before the document's header is read.** Of 2,939 index rows, 1,718 sit at a real seat under a surname that is not the sitting member's: the file is mostly candidates, who are out of scope per SUBJECTS.md §3. Matching on name rather than seat attributes 1,097 filings to 393 of the 439 sitting members. The remainder is held, not guessed: 255 rows carry a surname matching exactly one sitting member whose given names differ, which is usually a common name against a legal name and is also the shape of a relative running for the same seat. Forty-six sitting members end with nothing attributed. Those were the name join's numbers on its own; the header step in the next bullet settles most of the rows at a member's own seat, and the current totals, still the adapter's stated incompleteness, are the ones in `data/meta.json`.
- **The documents, read 2026-09-23.** Of the 463 transaction reports (code `P`) the register attributes to sitting members, 409 were produced by the Clerk's e-filing system and read as text; 54 are scanned paper filings (DocIDs beginning 82 and 91), which the register captures and hashes and does not read. Each e-filed report is a table, and the adapter reads it as one, by the position of every text fragment on the page: the owner code, the asset, the type, the two dates and the amount band sit in the form's columns; beneath each transaction the form prints up to five labelled lines (filing status, subholding of, location, description, comments), which the register carries in the row's notes as filed. The header names the filer, the status, the seat as `State/District`, and the `Filing ID`; the adapter requires the Filing ID to equal the DocID of the index row and the seat to equal the roster seat. A document that disagrees on the Filing ID, or on the seat without its printed name confirming the officeholder, refuses the row. 3 reports by one member print the seat held in the previous Congress while naming the member exactly; those rows stand and carry the discrepancy in `notes`. Where a filer entered an exact figure instead of a band (10 rows), the band is the whole dollars on either side of it and the notes carry the figure as printed. Dates are carried as printed, including rows whose notification date precedes the transaction date (35 in build 0003-house-2025). The asset codes are defined by the Clerk at <https://fd.house.gov/reference/asset-type-codes.aspx>, verified reachable 2026-09-23; the register carries the code and cites the legend rather than restating it. The header also settles the rows the name join holds: where the index places a row at a member's own seat under the member's surname with a different given name, the row is attributed only when its document prints Status `Member`, that seat, that DocID and a filer name carrying the roster surname, and the index dates it no earlier than the swearing-in the roster records; a document that prints another filer status (the form prints `Congressional Candidate` for a candidate) holds the row with that status quoted, for a person to decide; 101 rows were attributed this way, 28 wait on documents with no Filing ID line, 6 on a filer status other than Member, 1 on the date. The member a surname points at is the one whose every surname word the row carries, or, among several, the one at the row's seat. Annual reports (codes other than `P`) are not yet read beyond their headers.
- **Adapter status.** Index layer and transaction-report documents landed, `src/adapters/house-fd/`. Annual reports planned.

### F.2. U.S. Senate Financial Disclosures
- **URL.** <https://efdsearch.senate.gov>
- **Publisher.** Office of Public Records, Secretary of the Senate.
- **Forms.** Financial Disclosure Report (annual), Periodic Transaction Report (PTR).
- **Formats.** HTML web forms with paginated results; no bulk download; captcha on the search interface.
- **Retention.** Six years post-filing.
- **Terms.** Public documents; the interface asks users to agree to a use policy before searching. The policy, citing 5 U.S.C. app. § 105(c), forbids use for commercial purposes (news media excepted), for credit rating, and for solicitation. The adapter honours the policy, and the consumer contract in ECOSYSTEM.md §3 carries it downstream.
- **Known gaps.** Absence of bulk download imposes a per-filing retrieval cost; adapter throttling must be conservative. The report-identifier scheme has not yet been observed, because the search sits behind the agreement gate; the first adapter session that passes it records the scheme before anything else.
- **The roster.** <https://www.senate.gov/general/contact_information/senators_cfm.xml>, the Senate's own member list, verified reachable as XML on 2026-09-22. It is the identity source for the Senate the way the Clerk's `MemberData.xml` is for the House; its fields are recorded when the adapter is written.
- **The human step.** The agreement gate and the captcha are not passed by software. A person accepts the agreement and exports the search; the adapter takes the export from there, and the run record names the person and the session. This is the register's first recorded human step in retrieval, and it is a Limit, not a workaround.
- **Adapter status.** Planned.

### F.3. U.S. Office of Government Ethics. Executive Branch Form 278e
- **URL.** <https://extapps2.oge.gov/Web/278eFiling.nsf>
- **Publisher.** Office of Government Ethics (OGE).
- **Forms.** OGE Form 278e (public financial disclosure for senior Executive Branch officials).
- **Formats.** PDF via a search interface.
- **Retention.** Six years post-filing.
- **Terms.** Public documents.
- **Known gaps.** Coverage is limited to senior officials as defined by 5 U.S.C. app. 4 § 101; a large population of federal employees files the confidential OGE-450, which is not public.
- **Adapter status.** Planned.

### F.4. Federal Election Commission (FEC)
- **URL.** <https://www.fec.gov/data/>
- **API.** <https://api.open.fec.gov/developer/>
- **Publisher.** Federal Election Commission.
- **Forms.** Form 3 (candidate committees), Form 3X (other political committees), Form 3P (presidential), Form 5 (independent expenditures), Form 24 (48-hour reports), and others.
- **Formats.** Well-documented JSON API with rate limits; bulk CSV downloads.
- **Retention.** Permanent.
- **Terms.** API requires a free registered key. Terms are permissive for civic use.
- **Known gaps.** Committee-to-candidate linking is not always clean; small in-kind contributions may go unreported below thresholds.
- **Adapter status.** Planned.

### F.5. U.S. Senate Lobbying Disclosure Act database
- **URL.** <https://lda.senate.gov/system/public/>
- **Publisher.** Secretary of the Senate.
- **Forms.** LD-1 (registration), LD-2 (quarterly activity), LD-203 (semiannual contribution report by registered lobbyists).
- **Formats.** XML bulk downloads.
- **Retention.** Permanent.
- **Terms.** Public documents.
- **Adapter status.** Planned.

### F.6. U.S. House Lobbying Disclosure
- **URL.** <https://disclosurespreview.house.gov/>
- **Publisher.** Clerk of the U.S. House.
- **Formats.** XML.
- **Adapter status.** Planned (mirror of F.5 for House-side filings).

### F.7. Congress.gov (legislative activity)
- **URL.** <https://www.congress.gov>
- **API.** <https://api.congress.gov>
- **Publisher.** Library of Congress.
- **Data.** Bills, votes, committee memberships, member biographies.
- **Formats.** REST API with API key; bulk XML from GPO's govinfo.
- **Terms.** Public. Rate limits documented.
- **Adapter status.** Planned. Needed to reconcile filings against legislative activity.

### F.8. GovInfo bulk data
- **URL.** <https://www.govinfo.gov> (Bill Status bulk data and the govinfo API).
- **Publisher.** U.S. Government Publishing Office, jointly with the Library of Congress, the Clerk of the House, and the Secretary of the Senate.
- **Data.** Bill status XML, bill text, and status documents; the upstream that GovTrack, the unitedstates scrapers, and Congress.gov's own developer guidance name.
- **Formats.** Bulk XML; REST API with a key.
- **Terms.** Public. The licence statement is recorded when the adapter is written.
- **Adapter status.** Planned, alongside F.7 where bulk history is wanted.

### F.9. Office of Congressional Conduct
- **URL.** <https://conduct.house.gov>. Renamed from the Office of Congressional Ethics by H.Res. 5 (119th Congress) on January 3, 2025; oce.house.gov redirects here.
- **Publisher.** U.S. House of Representatives.
- **Data.** Referrals to the Committee on Ethics with exhibits, an investigations table, quarterly statistics, rules and guides.
- **Formats.** HTML tables and PDF; quarterly statistics are published as images and PDF. No bulk download or API observed.
- **Terms.** Public documents.
- **Known gaps.** A referral is a primary record of a process step. The office states that a referral "is not a finding that a violation occurred"; any row citing one carries that frame.
- **Adapter status.** Planned, after Phase 3.

## Federal. corroborating (aggregators, cited never sole)

- **OpenSecrets**. <https://www.opensecrets.org>, the 501(c)(3) formed in 2021 when the Center for Responsive Politics and the National Institute on Money in Politics combined; comprehensive campaign finance and lobbying, with industry coding and household attribution not in the primaries. Its API was discontinued on April 15, 2025; bulk CSV is offered under CC BY-NC-SA 3.0 after account approval, so nothing derived from it can be relicensed.
- **ProPublica**. The FEC Itemizer, <https://projects.propublica.org/itemizer/>, and its Campaign Finance API (CC BY-NC-ND 3.0). The *Represent* congressional database and the Congress API closed in July 2024; the page remains as an archival snapshot.
- **Ballotpedia**. <https://ballotpedia.org>, encyclopedic coverage of federal, state, and local officeholders; useful for identity resolution.
- **LegiStorm**. <https://www.legistorm.com>, congressional staff, salaries, foreign travel gifts.
- **Follow the Money**. <https://www.followthemoney.org>, the state campaign-finance surface of OpenSecrets since the 2021 combination; state data shown through the 2024 election, federal data moved to opensecrets.org. CC BY-NC-SA 3.0.
- **MapLight**. <https://maplight.org>. Its money-and-votes research data covers 2007 to 2021 and is no longer updated. Its current products are the campaign-finance, lobbying, and ethics e-filing systems some state and local agencies use to collect disclosures, which makes it the vendor behind certain state primary records rather than an aggregator to cite beside them.
- **GovTrack**. <https://www.govtrack.us>, legislative tracking; long-lived.
- **Capitol Trades**. <https://www.capitoltrades.com> and **Unusual Whales congressional trading**, <https://unusualwhales.com/politics>, STOCK Act trade tracking with UX suited to lay readers.
- **CREW**. <https://www.citizensforethics.org>, Citizens for Responsibility and Ethics in Washington; enforcement filings and investigative work.
- **Campaign Legal Center**. <https://campaignlegal.org>, STOCK Act complaints with posted PDFs and a per-Congress ownership fact sheet.
- **Sludge**. <https://readsludge.com>, per-member reporting on late filings, committee-jurisdiction holdings, and trade timing, read from Clerk filings and Capitol Trades.

**Rule.** An aggregator is cited alongside the primary source it drew from. Where the two disagree, the primary source is authoritative and the disagreement is recorded on the row.

## State coverage

States are added per coverage. Each state entry follows the shape:

### [STATE]. [Ethics Commission or equivalent]
- **URL.**
- **Publisher.**
- **Forms.**
- **Formats.**
- **Retention.**
- **Terms.**
- **Known gaps.**
- **Adapter status.**

Priority states (populous, machine-readable, high officeholder density) will be documented first: California, New York, Texas, Florida, Illinois. The state coverage matrix, which states have adapters, which are pending, which are known infeasible without paper retrieval, will be maintained as a table in this file as adapters land.

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
