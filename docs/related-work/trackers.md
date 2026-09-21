# Related-work record: Legislative trackers and identity resolution

*Read on 2026-09-21. A first reader wrote each entry from the project's own pages; a second reader, briefed to refute, re-fetched every cited page. Corrections are shown beside the claims they correct and both are kept. Presence in this record is not a claim about a project's quality, and absence is not either. Presence in the register is not evidence of wrongdoing: where a record below describes what a neighbour published about an officeholder, it describes the role and not the person, names no one outside a citation URL, and is not a Finding. Rendered from `data/trackers.json` by `render.py`; edit the JSON, not this file.*

## GovTrack.us

<https://www.govtrack.us>

- **Organisation.**
  Civic Impulse, LLC (registered in the District of Columbia)
- **Kind.**
  Independent legislative tracker and analysis site (LLC, not a nonprofit, not a government site)
- **Self-description, as read.**
  GovTrack says it tracks the activities of the United States Congress and, since 2025, the White House, publishing the status of federal legislation, voting records, information and statistics about representatives and senators, and news and commentary; it describes itself as one of the oldest open-government websites, launched in 2004, and states plainly that it is not a government website. Its posted charter gives its mission as helping Americans participate in their government, commits to reporting fairly and not taking sides on policies or politicians, and says it accepts no grants from partisan organisations.
- **Subject scope.**
  U.S. Congress: bills and resolutions (bill status back to 1799 in varying completeness), roll-call votes (1789 to present, historical votes from Rosenthal and Poole), current and former members with committee assignments, committees, caucuses, congressional district maps, a legislator misconduct database 1789 to present (514 entries at retrieval), and a White House tracker newsletter for presidential actions.
- **Sources it says it uses.**
  - Members: the congress-legislators community repository (which GovTrack originally developed and helps maintain); raw member XML from the House and Senate; photos from the GPO Guide to House and Senate Members
  - Bill status: GPO GovInfo.gov Bill Status XML bulk data, retrieved daily via the unitedstates/congress scrapers; historical (1989 to 2014) bill status from the former THOMAS.gov
  - Bill text: GPO GovInfo.gov (PDF, XML, plain text); Statutes at Large for older enacted bills; Library of Congress American Memory Century of Lawmaking for 1799 to 1873
  - Votes: Senate and House websites in XML, refreshed roughly hourly; Rosenthal and Poole roll-call records (Carnegie Mellon) for 1789 to 1990
  - Bill summaries: Congressional Research Service summaries obtained by the same channel as bill status, plus summaries GovTrack writes itself
  - Upcoming business and committee meetings: Senate website and Docs.House.Gov
  - Misconduct database: Senate Historical Office expulsion and censure cases, the House Committee on Standards historical summary of conduct cases 1798 to 2004, a Washington Post indictment list, a Wikipedia list of convictions as of Jan 23, 2018, and contemporary news reports
  - Row-level linking: the member page observed links out to the member's official website, OpenSecrets, Bioguide and C-SPAN; per-bill links to GovInfo text were not checked in this survey
- **Outputs.**
  - Bill pages with status, text, summaries, cosponsor tables and email alerts
  - Roll-call vote pages
  - Member pages with statistics, an ideology-leadership chart, and links to external profiles
  - Annual legislator report cards (per Congress)
  - Ideology and leadership scores (CSV downloads for House and Senate)
  - Bill prognosis (probability of enactment)
  - Text incorporation analysis (which bills were folded into enacted bills)
  - Legislator misconduct database (web page plus YAML/CSV on GitHub)
  - Pronunciation guide for member names
  - Congressional district maps
  - Twice-weekly newsletters on upcoming and completed legislative activity; White House tracker newsletter
  - Advocacy organisation ratings gathered onto member pages (since 2017) and FY24 earmark requests from Demand Progress Education Fund (since 2023)
- **Per-person derived score or rank, as observed.**
  Report cards rank every member within cohorts (all representatives, all senators, party, freshmen, sophomores, ten-plus years) from #1 downward on: bills cosponsored; bills introduced; bills out of committee; committee positions (a score of five points per full-committee leadership post and one per subcommittee post); cosponsors gathered; ideology score on a 0.00 to 1.00 scale from most politically left to most politically right; joining bipartisan bills (percent of cosponsored bills from the other party); laws enacted (primary sponsor of an enacted bill, or at least about one third of a bill's text incorporated into an enacted bill, by automated analysis); leadership score on a 0.00 to 1.00 scale from top leader to bottom/follower; missed votes (percent); powerful cosponsors; working with the other chamber (companion bills as identified by CRS); writing bipartisan bills. The 2024 report cards cover the 118th Congress as of Feb 13, 2025. Ideology score: principal components analysis (singular value decomposition) of a member-by-member cosponsorship matrix over the current and previous two Congresses, using the second dimension; not computed for members who introduced fewer than ten bills or who have a low leadership score. Leadership score: PageRank run on the same cosponsorship matrix. Bill prognosis: logistic regression per measure type, trained on the 117th Congress. Member pages also present third-party advocacy organisation ratings.
- **Identifiers exposed.**
  - GovTrack numeric person ID (in member page URLs, e.g. /congress/members/nancy_pelosi/400314; the govtrack key in congress-legislators; Wikidata property P12644)
  - Bioguide, OpenSecrets and C-SPAN profile links on member pages (the underlying IDs are held; the about-our-data page directs reusers to congress-legislators for the identifier crosswalk)
  - The unitedstates/congress scrapers emit GovTrack IDs for legislators when run with the --govtrack flag
- **Per-filing conditions it states or computes.**
  - No per-filing financial condition (STOCK Act timing, trade-vote proximity, committee-industry overlap, transaction-versus-annual asset checks) is computed on the pages read.
  - Misconduct database inclusion criteria, stated on the page: all letters of reproval, censures and expulsions since 1789; all investigations by the House Office of Congressional Ethics (2008 onward), the House Committee on Ethics (1975 onward) and the Senate Select Committee on Ethics (1962 onward), plus Senate exclusion votes tied to personal misconduct; some other congressional investigations and monetary settlements involving alleged personal misconduct that GovTrack is aware of; resignations GovTrack believes likely relevant to an allegation; felony convictions and other nationally significant misconduct before or after service. Each entry carries category tags (bribery and corruption, other crimes, ethics violation, sexual harassment and abuse, campaign and elections), consequence tags (expulsion, censure, reprimand, fined, resignation, exclusion, settlement, conviction, plea) and a resolved/unresolved flag.
  - Missed votes: the percentage of roll-call votes a member missed in the Congress, with stated exclusions for the Speaker and non-voting delegates.
  - Laws enacted: counted only where the member is primary sponsor of the enacted measure or of a bill at least about one third of whose text was incorporated, excluding bills whose text was wholly replaced.
- **Code.**
  Website front end is public at github.com/govtrack/govtrack.us-web (Django; GitHub's license API reports no license file; last push 2026-07-24). The misconduct database is at github.com/govtrack/misconduct under CC0-1.0 (LICENSE.md; last push 2026-08-21). The analysis methodology page says the ideology and leadership source code is on GitHub and gives the core numpy steps inline. Data collection uses the CC0 unitedstates/congress and congress-legislators repositories, which GovTrack co-maintains.
- **Data licence.**
  Terms of Service (last updated August 2023): readers are welcome and encouraged to copy and reuse site information, except that site text, images, data and metadata may not be used for developing any software program, including training a machine learning or AI system, nor for providing archived or cached datasets to another person or entity except for personal, non-commercial use. Ideology and leadership scores are offered as CSV downloads. The misconduct dataset is CC0. GovTrack's own bulk open data and API were retired in 2017 (site timeline).
- **API.**
  None. The site timeline records that its open data and API ended in 2017 because Congress began publishing structured data itself; the about-our-data page points reusers to congress-legislators, GovInfo bulk data, and House and Senate XML instead. Non-browser clients received HTTP 403 during this survey; pages loaded only with a browser user agent.
- **Funding or business model, as stated.**
  The About page states GovTrack is a project of Civic Impulse, LLC, wholly owned by its operator, with no outside funding, financers, sponsors, investors or partners, and no affiliation with any party, agency or outside group other than subscribers and advertisers. Operating costs are paid by advertising revenue, Substack subscribers, and crowdfunding (Patreon, Kickstarters in 2015 and 2025). It describes a few part-time staff.
- **How it frames what a listing means.**
  The report cards page states that a higher or lower number does not necessarily make a legislator better or worse or more or less effective, that the statistics are presented so readers can "make your own judgements" (GovTrack 2024 Report Cards page), and that much of legislating (constituent service, oversight) is not measured. The ideology methodology page says no margin of error is reported, scores fluctuate with limited data, the axis may measure partisan-ness rather than ideology, cosponsorship is a low-risk act, and scores can be gamed. The misconduct page says many entries are politically motivated, some allegations are never proven, and readers must judge for themselves whether the conduct is misconduct. Every page footer states the site is not a government website, and the contact widget states GovTrack has no affiliation with the member.
- **Status at retrieval.**
  active: the About Our Data page carries an analysis item dated Sept 21, 2026, the About page a recap dated Sept 18, 2026, and misconduct entries dated August 2026.
- **Not verified.**
  - License of the govtrack.us-web repository (no license file detected by GitHub)
  - Whether each bill page links to the GovInfo primary text (not fetched)
  - Location of the ideology/leadership CSV files (the linked download page was not fetched)
  - Pages returned HTTP 403 to WebFetch and to the browser pane; content was retrieved with a browser user agent
  - Whether each bill page links to GovInfo primary text (not fetched)
  - Location and contents of the ideology/leadership CSV download page (linked as 'over here' from the analysis page; not fetched)
  - 'Photos ... credited on individual legislator pages' beyond the data page's statement
  - Whether the 2013 charter wording or the 2017 advocacy-ratings item has changed since the survey (the timeline as read matches)
- **Confirmed by the second reader.** 14 claims, listed in the JSON.
- **Citations.**
  - <https://www.govtrack.us/about> (retrieved 2026-09-21): self-description, charter, organisation (Civic Impulse LLC), funding statement, timeline including 2017 end of open data and API, 2013 report cards, 2017 misconduct database, dated recap item
  - <https://www.govtrack.us/about-our-data> (retrieved 2026-09-21): data sources per collection and era, pointer to congress-legislators, GovInfo, House and Senate XML, misconduct data on GitHub, dated Sept 21, 2026 item
  - <https://www.govtrack.us/about/analysis> (retrieved 2026-09-21): ideology (PCA/SVD, second dimension), leadership (PageRank), prognosis (logistic regression trained on 117th), text incorporation; caveats; CSV downloads; source code on GitHub
  - <https://www.govtrack.us/congress/members/report-cards/2024> (retrieved 2026-09-21): report-card statistics, ranks, cohorts, committee-position scoring, ideology and leadership display scales, exclusions, framing language and quote, as-of date Feb 13, 2025
  - <https://www.govtrack.us/misconduct> (retrieved 2026-09-21): misconduct database count (514), inclusion criteria, category and consequence tags, sources, political-motivation caveat, dated 2026 entries
  - <https://www.govtrack.us/legal> (retrieved 2026-09-21): terms of service reuse permission and the AI-training and cached-dataset exclusions; last updated August 2023; Civic Impulse LLC
  - <https://www.govtrack.us/congress/members/nancy_pelosi/400314> (retrieved 2026-09-21): numeric GovTrack person ID in URL; outbound links to OpenSecrets, Bioguide, C-SPAN; ideology-leadership chart on member page; no-affiliation statement
  - <https://github.com/govtrack/govtrack.us-web> (retrieved 2026-09-21): public source repository; GitHub license API reports no license; last push 2026-07-24
  - <https://github.com/govtrack/misconduct> (retrieved 2026-09-21): misconduct dataset repository; CC0-1.0 LICENSE.md; last push 2026-08-21

## Congress.gov API

<https://api.congress.gov>

- **Organisation.**
  Library of Congress (Congress.gov)
- **Kind.**
  Official government API for legislative data
- **Self-description, as read.**
  The API root says Congress.gov shares its application programming interface with the public to ingest congressional data, with keys issued through api.data.gov and documentation in a GitHub repository. The repository README describes the API as a method for Congress and the public to "view, retrieve, and re-use machine-readable data" (LibraryOfCongress/api.congress.gov README) from collections on Congress.gov. The Congress.gov developer guidance page calls the API the preferred route for developers and describes bill status bulk data as a joint effort of GPO, the Library of Congress, the House Clerk and the Secretary of the Senate.
- **Subject scope.**
  Per the Congress.gov coverage-dates table: member profiles from 1971 (92nd Congress to present, including members from 1923 to 1970 still serving in 1971); bill actions and cosponsors from 1973 (93rd); amendment actions from 1981; bill and resolution text in XML from 2007 (older text in PDF/TXT back to 1799 with gaps); committee reports and hearing transcripts from 1995; committee prints from 1993; nominations from 1981; treaty status from 1975; daily Congressional Record from 1995 and bound edition 1873 to 1994; CRS products from 1997; House roll-call votes from 2017 (115th) with the ChangeLog noting 117th-Congress House votes being added in April 2026. Senate committee membership: current only. Votes section lists House roll-call votes only.
- **Sources it says it uses.**
  - This is itself the Library of Congress's publication; the developer-guidance page states bill status data is produced jointly by GPO, the Library of Congress, the Office of the Clerk of the House and the Office of the Secretary of the Senate, and is also available as GPO bulk data and via the govinfo API
  - Member endpoint documentation says the bioguideId originates in the Biographical Directory of the United States Congress, 1774 to present, and that member vacancy data is maintained separately on the House Clerk website
  - Bill text is made available by GPO (coverage-dates footnote)
- **Outputs.**
  - JSON or XML endpoints under /v3: bill (with actions, amendments, committees, cosponsors, related bills, subjects, summaries, text, titles), law, amendment, summaries, congress, member (list; by bioguideId; sponsored and cosponsored legislation; by congress, state and district), house-vote (list, by congress and session, vote detail and per-member positions, marked beta), committee (with bills, reports, nominations, communications), committee-report, committee-print, committee-meeting, hearing, congressional-record, daily-congressional-record, bound-congressional-record, house-communication, house-requirement, senate-communication, nomination, and (per the documentation folder) crsreport and treaty
  - OpenAPI specification (openapi.json and openapi.yaml)
  - Python and Java sample clients, a ChangeLog and an issue tracker on GitHub
  - Member records return name variants, party, state, district, terms with chamber and years, depiction with attribution, office contact, leadership positions, sponsored and cosponsored legislation counts, birth and death years, currentMember flag and updateDate
- **Per-person derived score or rank, as observed.**
  None observed. Member records carry counts of sponsored and cosponsored legislation but no score or rank.
- **Identifiers exposed.**
  - bioguideId as the member key (originates in the Biographical Directory of the United States Congress)
  - Committee system codes (committeeCode) and chamber
  - Bill identifiers as congress, billType, billNumber; law identifiers as congress, lawType, lawNumber
  - House roll-call vote identifiers as congress, session, voteNumber
- **Per-filing conditions it states or computes.**
  - None. The API publishes records and counts; no per-filing conditions are computed.
- **Code.**
  Documentation, sample clients, changelog and issue tracker at github.com/LibraryOfCongress/api.congress.gov (last push 2026-09-21). GitHub's license API reports no license file for the repository.
- **Data licence.**
  No license statement was found on the API root, the README, the developer-guidance page or the Library's legal page. The Library's legal page says users should determine for themselves whether an item is protected by copyright or in the public domain, and that the Library generally does not own rights to materials in its collections. The README says API keys and registration fall under data.gov's privacy policy and API content under the Library's.
- **API.**
  Public API; key required, obtained through api.data.gov; rate limit 5,000 requests per hour; default page size 20, adjustable up to 250; XML or JSON. The developer-guidance page warns that disregarding the disallow rules in Congress.gov's robots.txt leads to blocking. During this survey, congress.gov help pages returned HTTP 403 to non-browser clients.
- **Funding or business model, as stated.**
  Government service operated by the Library of Congress; no separate funding statement on the pages read.
- **How it frames what a listing means.**
  House vote detail and per-member vote endpoints are labelled beta. Coverage-dates footnotes state that historical action data before 1973 is less complete, that committee actions for 1973 to 1980 are limited to referral, reporting and discharge, that pre-1981 cosponsorship dates are unavailable, and that historical bill text may be missing, incomplete or inaccurate.
- **Status at retrieval.**
  active: ChangeLog entries dated May through August 2026; repository last pushed 2026-09-21; coverage-dates page describes next-morning updates.
- **Not verified.**
  - An explicit license or terms-of-use statement for API data
  - The full endpoint list beyond nomination (page text was truncated); crsreport and treaty endpoints inferred from documentation file names
  - api.data.gov terms page (HTTP 404 at /terms/)
  - An explicit license or terms-of-use statement for API data (none found on the pages read; same as the entry)
  - api.data.gov /terms/ HTTP 404 (not re-fetched)
  - The full endpoint list as rendered on the API root page (the root is JavaScript-rendered; only raw HTML strings were checked)
- **Confirmed by the second reader.** 9 claims, listed in the JSON.
- **Citations.**
  - <https://api.congress.gov/> (retrieved 2026-09-21): self-description at the API root; key via api.data.gov; endpoint list including member/{bioguideId} and house-vote beta endpoints (page text truncated after nomination)
  - <https://raw.githubusercontent.com/LibraryOfCongress/api.congress.gov/main/README.md> (retrieved 2026-09-21): README description and quote; rate limit 5,000 per hour; default and maximum page sizes; privacy-policy split; XML/JSON
  - <https://github.com/LibraryOfCongress/api.congress.gov/blob/main/Documentation/MemberEndpoint.md> (retrieved 2026-09-21): member endpoint forms; bioguideId originates in the Biographical Directory 1774 to present; member fields; vacancy data on House Clerk site
  - <https://raw.githubusercontent.com/LibraryOfCongress/api.congress.gov/main/ChangeLog.md> (retrieved 2026-09-21): dated 2026 changelog entries; 117th-Congress House roll-call votes added April 2026; member legislation sorting May 2026
  - <https://www.congress.gov/help/coverage-dates> (retrieved 2026-09-21): coverage table by collection: member profiles 1971 (92nd), House roll-call votes 2017 (115th), bill text 2007 XML, and footnotes on completeness
  - <https://www.congress.gov/help/using-data-offsite> (retrieved 2026-09-21): API as preferred developer route; GitHub resources; robots.txt blocking warning; bill status bulk data as joint GPO, LOC, House Clerk, Senate Secretary effort
  - <https://www.loc.gov/legal/> (retrieved 2026-09-21): Library's copyright statement placing determination on the user; no API-specific terms
  - <https://github.com/LibraryOfCongress/api.congress.gov> (retrieved 2026-09-21): repository exists; documentation folder lists endpoint docs including CRSReport and Treaty; GitHub license API reports none; last push 2026-09-21

## ProPublica Represent and the ProPublica Congress API

<https://projects.propublica.org/represent/>

- **Organisation.**
  ProPublica (Pro Publica Inc.)
- **Kind.**
  Newsroom database and API for Congress (discontinued)
- **Self-description, as read.**
  The Represent page describes the tool with the line "See what your representatives in Congress say and do" (ProPublica Represent page) and, in a notice updated July 10, 2024, states that Represent and the Congress API are no longer available, thanks users since the 2016 launch, and says the page is a partial archival snapshot from July 2024. The API documentation states the Congress API is no longer available and should be used only as historical reference, and recounts that the API began at The New York Times in 2009, moved to ProPublica in November 2016, and replaced the Sunlight Congress API that was sunset on Oct 1, 2017.
- **Subject scope.**
  Historical: members of Congress (all members, more detail for those serving since 1995), roll-call votes (House from 1991, Senate from 1989), bills from 1995, nominations from 2001, committees, statements and lobbying filings.
- **Sources it says it uses.**
  - API documentation describes legislative data from the House, Senate and Library of Congress
  - ProPublica volunteers contributed manual edits to the congress-legislators repository (per that project's README)
  - Whether each row linked to a primary filing: not verified
- **Outputs.**
  - Represent web application with member, bill and vote pages (archival snapshot only)
  - Congress API endpoints for members, votes, bills, nominations, committees, statements and lobbying (no longer served; no new keys)
- **Per-person derived score or rank, as observed.**
  Not verified; the pages read did not show per-member scores.
- **Identifiers exposed.**
  - Historical member response fields per the members documentation: id (bioguide-format, e.g. A000360), api_uri, govtrack_id, cspan_id, votesmart_id, icpsr_id, crp_id (OpenSecrets), google_entity_id, fec_candidate_id, ocd_id, lis_id
- **Per-filing conditions it states or computes.**
  - None observed on the pages read.
- **Code.**
  Not verified; no source repository was cited on the pages read.
- **Data licence.**
  API documentation states data was released under Creative Commons Attribution-NonCommercial-NoDerivs 3.0 United States, with commercial use available for a fee on request; terms barred wholesale republishing of raw data, altering data, charging for access or reselling, and required citing ProPublica.
- **API.**
  Discontinued; documentation kept as historical reference; no new API keys issued.
- **Funding or business model, as stated.**
  Not stated on the pages read; the site carries a donate link and describes its work as investigative journalism in the public interest.
- **How it frames what a listing means.**
  The Represent page frames itself as an archival snapshot and directs readers to ProPublica's ongoing politics coverage and other databases.
- **Status at retrieval.**
  defunct: the site states Represent and the Congress API are no longer available (notice updated July 10, 2024).
- **Corrected on second reading.**
  - *openness_data_license.* First read: API documentation states data was released under Creative Commons Attribution-NonCommercial-NoDerivs 3.0 United States On re-reading: The documentation attaches the CC BY-NC-ND 3.0 US license to use of the API ('Use of this API is available under a Creative Commons Attribution-NonCommercial-NoDerivs 3.0 United States License') and separately states 'The data returned by the Congress API is in the public domain.' The entry omits the public-domain statement and so describes ProPublica's data as more restricted than the page says. (<https://projects.propublica.org/api-docs/congress-api/>)
- **Not verified.**
  - Whether any API data remains downloadable
  - Per-member derived statistics the API may have carried
  - Source code repository
  - Per-member derived statistics the API carried
  - Source code repository (none cited on the pages read; propublica.github.io/congress-api-docs is linked from the congress-legislators README but was not fetched)
  - funding_or_business_model beyond the donate link
- **Confirmed by the second reader.** 6 claims, listed in the JSON.
- **Citations.**
  - <https://projects.propublica.org/represent/> (retrieved 2026-09-21): tagline quote; discontinuation notice; July 10, 2024 update date; archival snapshot framing; 2016 launch
  - <https://projects.propublica.org/api-docs/congress-api/> (retrieved 2026-09-21): API no longer available; history (NYT 2009, ProPublica Nov 2016, Sunlight sunset Oct 1, 2017); coverage dates; CC BY-NC-ND 3.0 US license; terms of use
  - <https://projects.propublica.org/api-docs/congress-api/members/> (retrieved 2026-09-21): identifier fields in the member response; status notice

## The unitedstates project (congress-legislators and congress)

<https://github.com/unitedstates>

- **Organisation.**
  The unitedstates GitHub organisation; volunteer maintained with contributors from GovTrack, ProPublica, MapLight, FiveThirtyEight and others (congress-legislators README); the congress scrapers were built by GovTrack.us and the Sunlight Foundation in 2013 and are maintained by GovTrack.us and other contributors
- **Kind.**
  Public-domain (CC0) data repositories and scrapers for Congress
- **Self-description, as read.**
  congress-legislators describes itself as members of the United States Congress from 1789 to the present in YAML, JSON and CSV, together with committees, committee membership, presidents and vice presidents, maintained by volunteer edits and automated imports; it says of the bioguide field, "This is the best field to use as a primary key." (congress-legislators README). The congress repository describes itself as public-domain data collectors for the work of Congress, converting official bulk bill status data, scraping House and Senate roll-call votes, and fetching documents from GovInfo.gov.
- **Subject scope.**
  Members of Congress 1789 to present (current and historical files), committees (current and historical), committee membership, district offices, social media accounts, presidents and vice presidents (executive.yaml); bills, amendments, resolutions and roll-call votes for the congress scrapers.
- **Sources it says it uses.**
  - congress-legislators automated imports: GovTrack.us, the Congressional Biographical Directory, Nelson and Stewart historical committee data, Martis's Historical Atlas of Political Parties, the Sunlight Labs Congress API, the Library of Congress THOMAS site, and C-SPAN's Congressional Chronicle; committee data scraped from House and Senate websites
  - congress scrapers: official GPO bulk bill status data (github.com/usgpo/bill-status), GovInfo.gov for bill text and status documents, House and Senate roll-call vote pages; a defunct THOMAS nominations scraper
  - Row-level linking to primary filings: not applicable (the repositories are identifier and status data, not filings); each id key is documented with the source site it points to
- **Outputs.**
  - legislators-current and legislators-historical in YAML, JSON and CSV (CSV and JSON on the gh-pages branch)
  - committees-current, committees-historical, committee-membership-current
  - legislators-social-media, legislators-district-offices, executive.yaml
  - congress scrapers emitting data.json and data.xml per bill and per vote, with a --govtrack flag for GovTrack-compatible IDs
- **Per-person derived score or rank, as observed.**
  None.
- **Identifiers exposed.**
  - Documented id keys in the README: bioguide (primary key), thomas, lis (Senate roll-call ID), fec (a list of FEC IDs per person), govtrack, opensecrets, votesmart, icpsr (Voteview), cspan, wikipedia (page name), ballotpedia (page name), maplight, house_history, bioguide_previous (list of alternative bioguide IDs), pictorial
  - Present in legislators-current.yaml but not documented in the README id list at retrieval: wikidata (538 of 539 current legislators) and google_entity_id (469)
  - Key counts in legislators-current.yaml at retrieval: govtrack 539, bioguide 539, wikipedia 538, wikidata 538, ballotpedia 525, opensecrets 523, votesmart 519, google_entity_id 469, pictorial 444, icpsr 319, cspan 265, maplight 262, thomas 224, house_history 163, lis 100
- **Per-filing conditions it states or computes.**
  - None.
- **Code.**
  github.com/unitedstates/congress-legislators (CC0-1.0; last push 2026-09-03; scripts tested on Python 3.6) and github.com/unitedstates/congress (CC0-1.0; last push 2025-10-05).
- **Data licence.**
  Both READMEs state the project is in the public domain within the United States and that copyright and related rights worldwide are waived through the CC0 1.0 Universal public domain dedication; all contributions are released under CC0.
- **API.**
  None; static files in the repositories (YAML on main, CSV and JSON on gh-pages) and locally run scrapers.
- **Funding or business model, as stated.**
  Not stated; the README describes volunteer maintenance and automated imports.
- **How it frames what a listing means.**
  No frame about persons; data-quality notes only, such as the bioguide_previous list for legislators once listed under multiple Bioguide IDs and the note that fec is a list.
- **Status at retrieval.**
  active: congress-legislators latest commit 2026-09-03 (a swearing-in and party fix); congress latest commit 2025-10-05.
- **Not verified.**
  - README documentation of the wikidata and google_entity_id keys (absent from the id list at retrieval)
  - Contents of the gh-pages CSV/JSON branch
  - Contents of the gh-pages branch (not fetched)
- **Confirmed by the second reader.** 6 claims, listed in the JSON.
- **Citations.**
  - <https://raw.githubusercontent.com/unitedstates/congress-legislators/main/README.md> (retrieved 2026-09-21): self-description, documented id keys with descriptions and the primary-key quote, data sources, maintainer statement, CC0 public-domain paragraph, gh-pages CSV/JSON note, users list including ProPublica
  - <https://raw.githubusercontent.com/unitedstates/congress/main/README.md> (retrieved 2026-09-21): scraper scope (GPO bulk bill status, GovInfo, House and Senate votes, defunct THOMAS nominations), origin 2013 GovTrack and Sunlight, maintainers, CC0 paragraph, --govtrack flag
  - <https://raw.githubusercontent.com/unitedstates/congress-legislators/main/legislators-current.yaml> (retrieved 2026-09-21): presence and counts of id keys including wikidata and google_entity_id
  - <https://github.com/unitedstates/congress-legislators> (retrieved 2026-09-21): repository description, CC0-1.0 license, last push 2026-09-03 (GitHub API)
  - <https://github.com/unitedstates/congress> (retrieved 2026-09-21): repository description, CC0-1.0 license, last push 2025-10-05 (GitHub API)

## Ballotpedia

<https://ballotpedia.org>

- **Organisation.**
  Ballotpedia, sponsored by the Wisconsin-based Lucy Burns Institute; the About page states the Lucy Burns Institute/Ballotpedia is a 501(c)(3) organisation
- **Kind.**
  Nonprofit online encyclopedia of American politics with paid data services
- **Self-description, as read.**
  Ballotpedia calls itself "the digital encyclopedia of American politics" (Ballotpedia:About) and says it provides curated, neutral, accurate and verifiable content on government officials and their offices, issues and policy, elections and candidates, produced by professional staff rather than open contributors; it reports 731,312 encyclopedic articles, a nonprofit mission to educate, no affiliation with campaigns or candidates, and a commitment to neutrality in all content.
- **Subject scope.**
  Federal, state, local and territorial candidates, incumbents and appointed figures (executives, legislators, judges); U.S. Congress; state executives, legislatures and courts; all state and territorial ballot measures and some local ones; school boards; the 100 largest cities plus state capitals; local election expansion in 32 states (37,036 elections in 2024, 35,050 in 2025, an estimated 40,000 in 2026); recall elections; redistricting; public policy topics. Stated aim: cover every election in the United States.
- **Sources it says it uses.**
  - The data-sales FAQ says staff research and compile data from Secretary of State offices, county election offices, news outlets, and the candidates or officeholders themselves, using official sources wherever possible
  - Whether each article statement links to a primary filing: not verified
- **Outputs.**
  - Encyclopedia articles on officials, offices, candidates, elections, measures and policy
  - Sample Ballot Lookup tool; newsletters; annual reports (2019 to 2025)
  - Paid datasets: candidate lists and results, officeholder lists (over 600 federal and statewide offices; roughly 15,000 state legislative and top-100-city offices), school board members (about 82,000 across 13,000 boards), ballot measures with arguments, endorsements and campaign finance, topical legislation trackers, policy analysis, static historical files back to 2018
  - Geographic APIs with lat/long lookups and bulk CSV/JSON delivery via a client portal and developer documentation
- **Per-person derived score or rank, as observed.**
  No per-officeholder score observed on the pages read. The site lists analytical products such as pivot counties, state supreme court partisanship, polling indexes, competitiveness reports and trifecta analyses.
- **Identifiers exposed.**
  - Article title (page name) functions as the public identifier and is what congress-legislators and Wikidata property P2390 store
  - The data-sales page notes that for its ultralocal offices it does not provide persistent person IDs across years, which indicates persistent person IDs exist in the paid datasets for other levels; the identifier scheme itself was not described on the developer pages read
- **Per-filing conditions it states or computes.**
  - None.
- **Code.**
  None found on the pages read.
- **Data licence.**
  Text on the encyclopedia is licensed under the GNU Free Documentation License: it may be copied, modified and redistributed only if made available on the same terms and with attribution (a live link back satisfies attribution). Paid datasets are governed by data terms of use under which the licensee must preserve confidentiality and receives no right to share the full datasets with others; use is permitted inside internal or external products with safeguards against bulk download.
- **API.**
  Paid. Geographic and bulk APIs documented at developer.ballotpedia.org; API keys are obtained through data sales; annual subscriptions; pricing varies by package starting at $500; single-state subscriptions on request.
- **Funding or business model, as stated.**
  The About page states it is a 501(c)(3) accepting donations from individuals and foundations, with other revenue from Premium Research Services, custom election data and political intelligence via its API, and digital ad sales.
- **How it frames what a listing means.**
  States that all content must be neutral, accurate and verifiable, that it is nonpartisan and not affiliated with campaigns or advocacy groups, and invites error reports; a separate Disclaimers page is linked in the footer (not fetched).
- **Status at retrieval.**
  active: the About page links a 2025 annual report; navigation carries 2026 and 2027 election pages; the data-sales page lists 2026 state coverage; the scope page shows an update date of May 16, 2024.
- **Not verified.**
  - Person identifier scheme in the developer documentation
  - The Disclaimers page
  - Whether article statements link to primary filings row by row
  - API pricing beyond the stated starting point
  - identifiers_exposed inference that persistent person IDs exist in paid datasets for other levels (the page only states they are absent for the local offices; the inference is the entry's own)
  - The Disclaimers page (not fetched)
  - API pricing beyond the $500 starting point
- **Confirmed by the second reader.** 8 claims, listed in the JSON.
- **Citations.**
  - <https://ballotpedia.org/Ballotpedia:About> (retrieved 2026-09-21): self-description and quote; article count; 501(c)(3); Lucy Burns Institute sponsorship; revenue sources; neutrality statements; coverage areas; 2025 annual report link; 2026 and 2027 navigation
  - <https://ballotpedia.org/Ballotpedia:Scope> (retrieved 2026-09-21): scope of offices and levels; local expansion figures and 32 states; May 16, 2024 update date; aim to cover every election
  - <https://ballotpedia.org/Ballotpedia:Buy_Political_Data> (retrieved 2026-09-21): paid datasets, delivery formats, officeholder list sizes, pricing from $500, sources statement, terms summary, persistent person ID note for ultralocal offices
  - <https://ballotpedia.org/Ballotpedia:Copyrights> (retrieved 2026-09-21): GFDL licensing of text and its conditions
  - <https://developer.ballotpedia.org/dictionaries-and-terms/terms-of-use> (retrieved 2026-09-21): data client terms: confidentiality, no right to share full datasets, purchase constitutes acceptance
  - <https://developer.ballotpedia.org/> (retrieved 2026-09-21): existence of geographic and bulk data API documentation; access via sales contact

## Vote Smart

<https://votesmart.org>

- **Organisation.**
  Vote Smart (formerly Project Vote Smart), nonprofit, Des Moines, Iowa (office at Drake University)
- **Kind.**
  Nonprofit voter-information database with a fee-based API
- **Self-description, as read.**
  Vote Smart says its sole mission is to provide "free, factual, unbiased information on candidates and elected officials" (votesmart.org About page) to all Americans, every day of the year; it recounts a founding more than thirty years ago by Presidents Ford and Carter and other leaders from both parties, describes itself as nonpartisan with no endorsements, advocacy or lobbying, and says its board seats were filled only in politically opposite pairs.
- **Subject scope.**
  Candidates and elected officials at federal and state levels (more than 220,000 candidates since 1992): biographies, voting records (key votes), issue positions (Political Courage Test), interest-group ratings (over 1,500 groups), endorsements, public statements, committees, vetoes, ballot measures, election summaries, and voter registration and polling-place information for all 50 states.
- **Sources it says it uses.**
  - Not stated on the pages read beyond a footer credit that legislative demographic data is provided by Aristotle International, Inc.; a page on the selection and description of key votes is linked but was not fetched
  - Whether each key vote links to the House Clerk or Senate roll-call record: not verified
- **Outputs.**
  - Candidate and official profiles at justfacts.votesmart.org (bio, votes, positions, ratings)
  - Key votes database with issue, state, year and chamber filters (a House vote dated 09/15/2026 was observed on a member page)
  - Interest-group ratings and endorsements; Political Courage Test; public statements
  - API (api.votesmart.org) returning XML or JSON for classes Address, Ballot Measure, CandidateBio, Candidates, Committee, District, Election, Leadership, Local, Npat, Office, Officials, Rating, State and Votes
  - A chat feature (Civic Sage) drawing on Vote Smart research; printed voter guides; a data subscription program
- **Per-person derived score or rank, as observed.**
  No Vote Smart-computed score observed. Member pages republish third-party interest-group ratings and offer a comparison of a member's votes against their stated positions.
- **Identifiers exposed.**
  - Vote Smart candidate ID (numeric, in profile URLs such as /candidate/key-votes/26732/nancy-pelosi and as candidateId in the API; carried as the votesmart key in congress-legislators and as Wikidata property P3344)
- **Per-filing conditions it states or computes.**
  - None.
- **Code.**
  None found on the pages read.
- **Data licence.**
  Site footer: all content copyright 1992 to 2021 Vote Smart unless otherwise attributed. API terms of use: individual use restricted to Vote Smart members; business or organisational use subject to fees; no use of the name, programs or data in any campaign activity; attribution not required but appreciated, and attribution to another party not permitted; keys are personal and non-transferable; service provided as-is with warranties disclaimed.
- **API.**
  api.votesmart.org with documentation last updated September 23, 2014; registration and API key required; fees for organisational use; the API page invites booking a demo. The public site meters free page views and prompts for login after a few (observed), and justfacts.votesmart.org returned HTTP 403 to non-browser clients.
- **Funding or business model, as stated.**
  The About page states 97 percent of support comes from Americans mailing checks of $250 or less, that it refuses financial assistance from organisations and special-interest groups that lobby or support or oppose candidates or issues, and links Form 990s for 2020 to 2024; the home page adds nonpartisan foundation funding and revenue from its data subscription program and other programs.
- **How it frames what a listing means.**
  Frames itself as nonpartisan and factual, with staff who check their politics at the door; the API terms disclaim warranties and forbid campaign use of the data.
- **Status at retrieval.**
  active: a key vote dated 09/15/2026 appears on a member's voting-record page; the site footer copyright still reads 1992 to 2021 and the API documentation is dated 2014.
- **Not verified.**
  - Key-vote selection methodology page
  - API fee schedule
  - Whether votes link to Congress.gov, House Clerk or Senate roll-call pages
  - Pages on justfacts.votesmart.org returned HTTP 403 to non-browser clients; read through the browser pane
  - Key-vote selection methodology page (linked as 'About the Selection and Descriptions of Key Votes'; not fetched)
  - API fee schedule (the register page shows no prices)
  - Whether key votes link to Congress.gov, House Clerk or Senate roll-call pages
- **Confirmed by the second reader.** 7 claims, listed in the JSON.
- **Citations.**
  - <https://www.votesmart.org/about> (retrieved 2026-09-21): mission quote; founding story; nonpartisan rules; funding statement (97 percent small checks, refusal of lobbying-group money); 990 links; Aristotle footer credit
  - <https://www.votesmart.org/> (retrieved 2026-09-21): voter tools list; interest-group count; candidate count since 1992; funding sources including data subscription program
  - <https://api.votesmart.org/docs/terms.html> (retrieved 2026-09-21): API terms of use: membership, fees, campaign-use ban, attribution, keys, disclaimer
  - <https://api.votesmart.org/docs/> (retrieved 2026-09-21): API classes; XML or JSON; documentation last updated September 23, 2014
  - <https://votesmart.org/share/api/register> (retrieved 2026-09-21): API feature list and demo booking; add-on datasets
  - <https://justfacts.votesmart.org/candidate/key-votes/26732/nancy-pelosi> (retrieved 2026-09-21): Vote Smart candidate ID in URL; key vote dated 09/15/2026; votes-versus-positions comparison; metered free views
  - <https://justfacts.votesmart.org/> (retrieved 2026-09-21): site sections (bio, votes, positions, ratings); Civic Sage feature; footer copyright range

## LegiStorm

<https://www.legistorm.com>

- **Organisation.**
  LegiStorm LLC, Washington, DC (founded 2006; Jock Friedly, Chief Executive Officer and Founder)
- **Kind.**
  Commercial public-affairs data platform (subscription) with some free public databases
- **Self-description, as read.**
  LegiStorm's home page carries the tagline "Congress Revealed" (legistorm.com home page); its company site says it is a comprehensive public affairs platform offering intelligence and tools for Congress and state legislatures, with a mission to give clients easy access to the information they need to achieve their objectives on Capitol Hill, and traces its start to making congressional salary information public in 2006, expanding by 2013 into staff directories, town halls, press releases and financial disclosures, then state coverage (2016) and lobbying analytics (2022).
- **Subject scope.**
  Congress: staff and member salaries, staff directories and contact lists, official expenses, staff turnover, town halls, hearing schedules, press releases and tweets, the revolving door; disclosures: personal financial disclosures of members and certain staff, privately funded travel from January 1, 2000 to present, foreign gifts, earmarks 2008 to 2010; lobbying filings; state legislators and staff; CRS, OMB, CBO and White House reports.
- **Sources it says it uses.**
  - Personal financial disclosures: public documents filed with Congress by all members and by staff earning at least 120 percent of the GS-15 base salary (about $111,000 in 2007), at least one staffer per member office, and Senate staff designated to accept campaign funds; LegiStorm posts images of the original disclosures with home addresses, phone numbers, Social Security numbers and minor children's names redacted
  - Privately funded travel: the financial disclosures required for privately sponsored official travel, with access to the original documentation
  - Foreign gifts: Federal Register publications supplemented by raw House Ethics Committee documents; the page states the Senate has no comparable public disclosure except through State Department reports
  - The about-our-data page does not name the House Clerk or Senate Office of Public Records; LegiStorm Pro lists original PDFs of congressional and lobbying disclosures
- **Outputs.**
  - Free public site: find a member, salaries, official expenses, turnover, Congress by the Numbers, personal financial disclosure browsing and search (with staffer disclosures marked Pro)
  - Pro or Premium: privately funded travel, foreign gifts, town halls, Congressional Record search, lobbying filing searches, revolving door, top lobbying firms, state legislature and staff data, press-release feed
  - Staff contact lists, staffer dossiers (PowerBriefs), custom email notifications, mobile app, weekly newsletters, policy reports
  - Data licensing and an API listed under custom solutions on the company site
- **Per-person derived score or rank, as observed.**
  Top Lobbying Firms (Premium) and a Members of Congress by Age report are the rankings named; no per-officeholder score observed on the pages read.
- **Identifiers exposed.**
  - Its own person pages; no external identifier scheme (bioguide, FEC, OpenSecrets, Wikidata) observed on the pages read
- **Per-filing conditions it states or computes.**
  - No computed per-filing condition observed on the pages read (no late-filing flag, trade-vote proximity, committee-industry overlap or transaction-versus-annual asset check). The PFD FAQ contains no information on filing deadlines, amendments or periodic transaction reports.
- **Code.**
  None found.
- **Data licence.**
  Proprietary; footer states copyright 2026 LegiStorm LLC, all rights reserved; a Terms of Use page is linked (not fetched).
- **API.**
  An API is listed under custom solutions on the company site; no public terms or documentation were found on the pages read.
- **Funding or business model, as stated.**
  Subscription platform (LegiStorm Pro, with free demos and a Start Free plan), purchases of staff contact lists and policy reports, data licensing, and an API; the company site cites 7,000-plus customers served and 350,000-plus hours of research.
- **How it frames what a listing means.**
  The PFD FAQ states that financial disclosure statements are not intended as net-worth statements and are not well suited to that purpose; the foreign-gifts page notes that diplomatic protocol often requires giving and accepting gifts; the travel FAQ notes that congressional rules allow private sponsorship only for official business and distinguishes such trips from taxpayer, campaign and foreign-government funded travel that is not disclosed the same way.
- **Status at retrieval.**
  active: home page blog posts dated September 2026 (latest September 17, 2026); footer copyright 2026; the financial-disclosure page reports 28 disclosures added in the past week.
- **Not verified.**
  - Whether disclosure rows link to the House Clerk or Senate eFD record rather than LegiStorm-hosted images
  - API terms and documentation
  - The Terms of Use page
  - Government sources for staff salary and expense data (the about-our-data page did not name them)
  - derived_scoring_or_ranking: a 'Members of Congress by Age' report was not found on any of the nine cited pages (no page is cited for it)
  - 'at least one staffer per member office' is the entry's paraphrase; the FAQ says 'principal assistants on members' personal staffs, as designated by the members'
  - The 2013 milestone's mention of town halls and press releases (the company page summary read only names staff directories and disclosures)
  - Whether disclosure rows link to the House Clerk or Senate eFD record
  - API terms and documentation; the Terms of Use page
- **Confirmed by the second reader.** 7 claims, listed in the JSON.
- **Citations.**
  - <https://www.legistorm.com/> (retrieved 2026-09-21): tagline quote; list of databases and Pro or Premium markers; free and paid tiers; blog posts dated September 2026
  - <https://info.legistorm.com/about> (retrieved 2026-09-21): mission, milestones 2006 to 2022, founder and CEO, customer counts, data licensing and API under custom solutions, 2026 copyright
  - <https://www.legistorm.com/pro.html> (retrieved 2026-09-21): LegiStorm Pro contents, audiences, subscription and demo model, original PDFs of disclosures
  - <https://www.legistorm.com/financial_disclosure.html> (retrieved 2026-09-21): images of original disclosures; who files; staffer disclosures marked Pro; disclosures added in past week
  - <https://www.legistorm.com/pfd/faq.html> (retrieved 2026-09-21): filer thresholds; redactions; not-a-net-worth-statement caveat; absence of deadline, amendment and PTR discussion
  - <https://www.legistorm.com/trip.html> (retrieved 2026-09-21): privately funded travel tracked for members and staff with original documentation, behind a subscription; LegiStorm LLC address
  - <https://www.legistorm.com/trip/faq.html> (retrieved 2026-09-21): travel database composed of privately funded travel disclosures from January 1, 2000; official-business rule; distinction from undisclosed travel types
  - <https://www.legistorm.com/foreign_gifts/about.html> (retrieved 2026-09-21): Foreign Gifts and Decorations Act basis; $335 minimal-value threshold as of 2008; Federal Register and House Ethics sources; Senate gap; Pro access; protocol caveat
  - <https://www.legistorm.com/index/about_our_data.html> (retrieved 2026-09-21): dataset list; Premium markers; no named government agencies

## Wikidata (as identity infrastructure for U.S. politicians)

<https://www.wikidata.org>

- **Organisation.**
  Wikimedia project; the operating organisation was not stated on the pages read
- **Kind.**
  Collaboratively edited open knowledge base with CC0 structured data
- **Self-description, as read.**
  The Main Page describes Wikidata as a free and open knowledge base that can be "read and edited by both humans and machines" (Wikidata Main Page), reporting 123,437,129 data entities at retrieval. The Data Access page describes four access routes (linked data interface, SPARQL query service, MediaWiki Action API, dumps) and asks clients to follow the User-Agent policy and honour rate-limit responses.
- **Subject scope.**
  General-purpose; for this cluster, the external-identifier properties that link items for U.S. politicians to other databases: P1157 US Congress Bio ID, P1839 US Federal Election Commission ID, P2686 OpenSecrets people ID, P12644 GovTrack person ID, P3344 Vote Smart candidate ID, P2390 Ballotpedia ID.
- **Sources it says it uses.**
  - Not applicable as a publisher of filings; each identifier property carries a formatter URL to the external database: bioguide.congress.gov/search/bio/$1 (P1157), fec.gov/data/candidate/$1 (P1839), opensecrets.org/personal-finances/net-worth?cid=$1 (P2686), govtrack.us/congress/person.xpd?id=$1 (P12644), justfacts.votesmart.org/candidate/$1 (P3344), ballotpedia.org/$1 (P2390)
- **Outputs.**
  - Items (QIDs) with statements and qualifiers
  - Linked data interface with content negotiation (.json, .rdf, .ttl) for known entities
  - SPARQL endpoint at query.wikidata.org/sparql
  - MediaWiki Action API (up to 50 entities per request)
  - Full database dumps
- **Per-person derived score or rank, as observed.**
  None.
- **Identifiers exposed.**
  - QID per item
  - P1157 US Congress Bio ID: format [A-Z]00[01]\d{3}; single-value and distinct-values constraints; subject must be human with politician occupation and U.S. citizenship; 12,708 records in the linked Mix'n'match catalog
  - P1839 US Federal Election Commission ID: format covering candidate IDs ([HS][A-Z0-9][A-Z]{2}[A-Z0-9]{5}) and committee IDs ([PC][0-9]{8}); distinct values; applies to humans and organisations; requires a party statement
  - P2686 OpenSecrets people ID: format [Nn]00\d{6}; single and distinct values; subject must be human
  - P12644 GovTrack person ID: numeric; single and distinct values; subject human with politician occupation
  - P3344 Vote Smart candidate ID: digits; single and distinct values
  - P2390 Ballotpedia ID: article title; distinct values; single value except lower state houses; MediaWiki page ID as required qualifier
- **Per-filing conditions it states or computes.**
  - None.
- **Code.**
  Not verified on the pages read (the platform software was not examined).
- **Data licence.**
  All structured data in the main, property and lexeme namespaces is made available under Creative Commons CC0; text in other namespaces is under Creative Commons Attribution-ShareAlike 4.0; every contributor applies CC0 to their contribution as a term of use.
- **API.**
  Linked data interface, SPARQL query service, MediaWiki Action API and dumps, all public; clients must follow the User-Agent policy and robot policies and respect 429 responses with Retry-After; the Data Access page advises the API is not for large result sets and dumps are not for current data.
- **Funding or business model, as stated.**
  Not stated on the pages read (a donate link is present).
- **How it frames what a listing means.**
  Not applicable to listings; the identifier properties carry editorial constraints (format, single value, distinct values, subject type) that flag but do not prevent inconsistent data.
- **Status at retrieval.**
  active: Main Page news items dated June 19 to 21, 2026 and November 12, 2025.
- **Not verified.**
  - Operating organisation and funding statements
  - Usage counts for P1839, P2686 and P12644
  - Platform software and its license
  - Operating organisation and funding statements (Main Page navigation lists the Wikimedia Foundation among sister sites but the pages read carry no operating statement)
- **Confirmed by the second reader.** 4 claims, listed in the JSON.
- **Citations.**
  - <https://www.wikidata.org/wiki/Wikidata:Main_Page> (retrieved 2026-09-21): self-description quote; entity count; dated 2025 and 2026 news items
  - <https://www.wikidata.org/wiki/Wikidata:Licensing> (retrieved 2026-09-21): CC0 for structured data; CC BY-SA 4.0 for other text; contributor CC0 term of use
  - <https://www.wikidata.org/wiki/Wikidata:Data_access> (retrieved 2026-09-21): access routes, SPARQL endpoint, API batch limit, dumps, User-Agent and rate-limit guidance
  - <https://www.wikidata.org/wiki/Property:P1157> (retrieved 2026-09-21): US Congress Bio ID label, formatter URL, format and subject constraints, Mix'n'match count
  - <https://www.wikidata.org/wiki/Property:P1839> (retrieved 2026-09-21): US FEC ID label, formatter URL, format regex covering candidate and committee IDs, constraints
  - <https://www.wikidata.org/wiki/Property:P2686> (retrieved 2026-09-21): OpenSecrets people ID label, formatter URL, format and constraints, examples
  - <https://www.wikidata.org/wiki/Property:P12644> (retrieved 2026-09-21): GovTrack person ID label, formatter URL, constraints
  - <https://www.wikidata.org/wiki/Property:P3344> (retrieved 2026-09-21): Vote Smart candidate ID label, formatter URL, constraints
  - <https://www.wikidata.org/wiki/Property:P2390> (retrieved 2026-09-21): Ballotpedia ID label, formatter URL, constraints and qualifiers

## Open States (Plural Open)

<https://open.pluralpolicy.com>

- **Organisation.**
  Plural (adopted the project in 2021); a Sunlight Foundation project 2009 to 2016; independently run 2016 to 2021
- **Kind.**
  State legislative data aggregator with open-source scrapers, API, bulk data and a curated people dataset
- **Self-description, as read.**
  Open States says it strives to improve civic engagement by providing data and tools for understanding the legislative process, aggregating legislative information from all 50 states, Washington, D.C., Puerto Rico and the U.S. Congress, standardising and cleaning it, and publishing it through its website, an API and bulk downloads; it states that legislative data is "collected from official sources, linked at the bottom of relevant pages" (Open States About page), with bill and vote data scraped several times a day and legislator data curated by its team and volunteers.
- **Subject scope.**
  Bills, votes, legislators, governors and some municipal leaders, committees and events for the 50 states, D.C. and Puerto Rico (the documentation site names states, D.C. and Puerto Rico; the About page also names the U.S. Congress, and the people repository ports the congress-legislators data into its schema).
- **Sources it says it uses.**
  - Official state legislature websites, read by scrapers, with the source linked at the bottom of relevant pages
  - People data curated manually in YAML; the us directory is ported from the CC0 congress-legislators repository
- **Outputs.**
  - Website for finding legislators and tracking state bills
  - API v3 (JSON) at v3.openstates.org with endpoints for jurisdictions, people, people.geo, bills, committees and events; a deprecated GraphQL v2 API
  - Bulk downloads
  - openstates/people YAML repository (legislature, executive, municipalities, retired, committees per state)
- **Per-person derived score or rank, as observed.**
  None observed.
- **Identifiers exposed.**
  - ocd-person IDs, ocd-jurisdiction IDs and ocd-bill UUIDs (Open Civic Data identifiers) per the people schema and API
  - An other_identifiers list per person with scheme, identifier and optional start and end dates (example scheme: votesmart), plus an ids block for accounts such as Twitter
  - An enhancement proposal (OSEP 5) on replacing pupa_id with a dedupe_key
- **Per-filing conditions it states or computes.**
  - None.
- **Code.**
  github.com/openstates: openstates-scrapers (GPL-3.0; last push 2026-09-21), openstates-core (MIT; last push 2026-09-17), people (CC0-1.0; last push 2026-09-21), documentation.
- **Data licence.**
  Terms of Service (effective September 15, 2021): no attribution required, no copyright claim over any data collected and published, no implied affiliation or endorsement; services provided as-is. The people repository is dedicated to the public domain under CC0.
- **API.**
  API keys required (register, then pass X-API-KEY header or apikey parameter); interactive documentation at v3.openstates.org/docs; the terms reserve a right to limit or block use that exceeds stated limits.
- **Funding or business model, as stated.**
  The About page lists funding prior to 2022: the Sunlight Foundation (2009 to 2016), Rita Allen Foundation, Minnesota Historical Society, Robert R. McCormick Foundation, Google.org, the Donald W. Reynolds Journalism Institute, and corporate contributions from Google Summer of Code, WeWork, Amazon Web Services and free plans from NewRelic and GitHub; since 2021 it is run by Plural, described as a company creating software for public policy data. Current funding is not stated.
- **How it frames what a listing means.**
  Terms summary: the project aims to be accurate and reliable but cannot provide guarantees, and use is contingent on accepting that.
- **Status at retrieval.**
  active: openstates/people and openstates-scrapers last pushed 2026-09-21; openstates-core 2026-09-17.
- **Not verified.**
  - Whether the live site currently serves U.S. Congress data (About says yes; documentation names only states, D.C. and Puerto Rico)
  - API rate limits and any paid tiers
  - A separate bulk-data license page
  - Whether the live site currently serves U.S. Congress data
  - API rate limits and paid tiers
  - Presence of /bills in the v3 endpoint list (not captured in the text extraction; other endpoints were)
- **Confirmed by the second reader.** 7 claims, listed in the JSON.
- **Citations.**
  - <https://open.pluralpolicy.com/about/> (retrieved 2026-09-21): self-description and quote; scope; scrapers and curated people data; Plural adoption 2021; history; funding history
  - <https://docs.openstates.org/> (retrieved 2026-09-21): Plural Open description; states, D.C. and Puerto Rico scope; move under Plural Open in 2023; volunteer-powered note
  - <https://docs.openstates.org/api-v3/> (retrieved 2026-09-21): API v3 root, key mechanism, endpoints, concepts (jurisdiction, person, bill)
  - <https://docs.openstates.org/data/> (retrieved 2026-09-21): data model concepts: jurisdiction, session, bill, vote, person, organization, post, membership
  - <https://open.pluralpolicy.com/tos/> (retrieved 2026-09-21): terms effective September 15, 2021; no attribution; no copyright claim over data; right to limit; as-is
  - <https://raw.githubusercontent.com/openstates/people/main/README.md> (retrieved 2026-09-21): people data layout; inspiration from and port of congress-legislators; CC0 dedication
  - <https://raw.githubusercontent.com/openstates/people/main/schema.md> (retrieved 2026-09-21): ocd-person and ocd-jurisdiction identifiers; other_identifiers with scheme, identifier, start_date, end_date; ids block
  - <https://github.com/openstates> (retrieved 2026-09-21): repository licenses and last push dates (GitHub API): scrapers GPL-3.0, core MIT, people CC0-1.0

## Voteview

<https://voteview.com>

- **Organisation.**
  UCLA Department of Political Science and Social Science Computing; project lead Jeffrey B. Lewis; directors emeritus Keith T. Poole and the late Howard Rosenthal
- **Kind.**
  Academic roll-call vote database with ideal-point estimation (DW-NOMINATE)
- **Self-description, as read.**
  Voteview says it lets users "view every congressional roll call vote in American history" (Voteview About page) on a map of the United States and on a liberal-conservative ideological map, using DW-NOMINATE, the scaling procedure developed by Poole and Rosenthal in the 1980s that places legislators so that closeness reflects similarity of voting records; the site is presented as a beta 3 rewrite of an older codebase, with data updated live as new votes are taken.
- **Subject scope.**
  Every Congress from the 1st (1789) through the 119th (2025 to 2027): members, roll-call votes, members' votes and party data for House and Senate.
- **Sources it says it uses.**
  - Not stated on the pages read; the data page says data is updated live as new votes are taken but does not name the House or Senate source feeds
  - Row-level linking to House Clerk or Senate roll-call records: not verified
- **Outputs.**
  - Downloads of Member Ideology, Congressional Votes, Members' Votes and Congressional Parties in CSV, JSON, DAT or ORD
  - A complete weekly MongoDB database dump (about 500 MB zipped) and archived prior releases
  - Party unity scores, presidential support scores, polarization plots, and analysis articles
  - Rvoteview R package; site source, district boundary JSON and member photos through a GitHub organisation
- **Per-person derived score or rank, as observed.**
  Per-member DW-NOMINATE scores (nominate_dim1 and nominate_dim2) for every member in every Congress; party unity scores; presidential support scores; an article tracking roll-call attendance rates of members running for president in 2020; an article explaining why NOMINATE estimated Alexandria Ocasio-Cortez as moderate as of June 2019.
- **Identifiers exposed.**
  - icpsr: integer 1 to 99999 identifying the member; a member who changed parties or later became president may carry separate codes so NOMINATE can be computed for each role
  - bioguide_id: the member's identifier in the Biographical Directory of Congress
  - state_icpsr: integer 0 to 99 for the state
- **Per-filing conditions it states or computes.**
  - None per filing. Attendance rate in roll-call votes was computed for presidential candidates as a per-person participation statistic.
- **Code.**
  The data page says most of the code for the website is available through the project's GitHub organisation (site source, district boundaries, photos, Rvoteview); the repository path was not confirmed (a lookup of voteview/voteview.com returned 404).
- **Data licence.**
  Not stated. The data page asks that the dataset be cited as Lewis, Poole, Rosenthal, Boche, Rudkin and Sonnet (2026), Voteview: Congressional Roll-Call Votes Database, and says the database dump is provided without warranty.
- **API.**
  None stated; downloads and database dumps.
- **Funding or business model, as stated.**
  The About page acknowledges support from the William and Flora Hewlett Foundation (grant 2016-3870), the National Science Foundation (NSF-SBS-0611974), UCLA Social Science Computing, and the University of Georgia.
- **How it frames what a listing means.**
  Database dump provided without warranty; archived releases may be missing new data or corrections and users are advised to use the current release; a methodology article addresses a counter-intuitive estimate.
- **Status at retrieval.**
  active: the data page's requested citation is dated 2026 and lists the 119th Congress; data described as updated live.
- **Not verified.**
  - Primary sources for the roll-call feeds
  - Data license
  - GitHub repository path for the site source
  - Primary sources for the roll-call feeds (not named on the pages read)
  - The 2020 presidential-candidate attendance article and the Ocasio-Cortez methodology article (not seen in the data page text extraction)
- **Confirmed by the second reader.** 8 claims, listed in the JSON.
- **Citations.**
  - <https://voteview.com/about> (retrieved 2026-09-21): self-description quote; UCLA hosting; project lead and directors emeritus; DW-NOMINATE description; funders; history
  - <https://voteview.com/data> (retrieved 2026-09-21): downloads and formats; 2026 citation request; live updates; MongoDB dump without warranty; archival note; ancillary analyses; GitHub organisation
  - <https://voteview.com/articles/data_help_members> (retrieved 2026-09-21): icpsr, bioguide_id and state_icpsr field definitions; multiple ICPSR codes after party switches; NOMINATE dimensions

## Biographical Directory of the United States Congress (Bioguide)

<https://bioguide.congress.gov>

- **Organisation.**
  Not stated on the pages read; hosted at bioguide.congress.gov, with the home page image credited to the Library of Congress
- **Kind.**
  Official biographical directory and the registry of the bioguide identifier
- **Self-description, as read.**
  The home page states that since 1859 the Biographical Directory has been "the primary source for biographical information on Members" (bioguide.congress.gov home page) of the United States Congress and the Continental Congresses, and offers a browse-biographies entry point and a link to a retro version of the site.
- **Subject scope.**
  Members of the Continental Congresses and the U.S. Congress, 1774 to present (per the Congress.gov member endpoint documentation, which says the bioguideId originates in this directory).
- **Sources it says it uses.**
  - It is itself the reference record: each entry carries a profileText biography, dates, job positions and related members; image assets carry credit lines (for example, the Collection of the U.S. House of Representatives) and a usageRight field
- **Outputs.**
  - Per-member pages at /search/bio/{ID}
  - A JSON record at /search/bio/{ID}.json (observed for P000197) with fields including usCongressBioId, familyName, givenName, birthDate, profileText, relationship (with the related member's own ID), image and asset metadata, and jobPositions
  - A retro version of the directory website
- **Per-person derived score or rank, as observed.**
  None.
- **Identifiers exposed.**
  - usCongressBioId (the bioguide ID: one letter plus six digits, e.g. P000197)
  - Related members referenced by their own bioguide IDs in the relationship field
- **Per-filing conditions it states or computes.**
  - None.
- **Code.**
  Not verified.
- **Data licence.**
  Not stated on the pages read; asset records carry a usageRight value (for example, Import to Congress.gov).
- **API.**
  An undocumented JSON endpoint per member was observed; no API documentation or terms were found. The site returned HTTP 403 to non-browser clients during this survey.
- **Funding or business model, as stated.**
  Not stated (government website).
- **How it frames what a listing means.**
  None observed.
- **Status at retrieval.**
  unknown: no explicitly dated content within the last twelve months was observed; the record fetched carried an asset upload date of 2024-06-21 and biography text referencing a 2024 event.
- **Not verified.**
  - The office that maintains the directory
  - License or terms for the data
  - Documentation for the JSON endpoint
  - Recent update dates
  - The office that maintains the directory (no page read names it)
  - Recent update dates (status 'unknown' stands)
- **Confirmed by the second reader.** 4 claims, listed in the JSON.
- **Citations.**
  - <https://bioguide.congress.gov/> (retrieved 2026-09-21): home page statement and quote; browse entry point; retro site link
  - <https://bioguide.congress.gov/search/bio/P000197.json> (retrieved 2026-09-21): JSON record structure: usCongressBioId, names, dates, profileText, relationship IDs, asset usageRight and upload date, jobPositions
  - <https://github.com/LibraryOfCongress/api.congress.gov/blob/main/Documentation/MemberEndpoint.md> (retrieved 2026-09-21): bioguideId originates in the Biographical Directory of the United States Congress, 1774 to present
  - <https://www.wikidata.org/wiki/Property:P1157> (retrieved 2026-09-21): formatter URL to bioguide.congress.gov/search/bio/$1 and ID format

## Pages the first reader could not reach

- https://www.govtrack.us/developers (HTTP 404)
- https://www.govtrack.us/congress/members/report-cards/2025 (HTTP 404; the 2024 report cards were used instead)
- https://www.govtrack.us/about/licensing (HTTP 404)
- https://ballotpedia.org/Ballotpedia:API (HTTP 404; developer.ballotpedia.org used instead)
- https://ballotpedia.org/Ballotpedia:Support_Ballotpedia (HTTP 404)
- https://ballotpedia.org/Ballotpedia:Neutrality_policy (HTTP 404)
- https://www.legistorm.com/about.html (HTTP 404; info.legistorm.com/about used instead)
- https://api.data.gov/terms/ (HTTP 404)
- https://openstates.org/about/ (301 redirect; followed to open.pluralpolicy.com/about/)

## Projects the second reader said were missing from this cluster

- **Google Civic Information API (Divisions API / OCD-ID lookup; Representatives endpoints turned down).** <https://developers.google.com/civic-information> Identity-resolution infrastructure the cluster's OCD-ID references (ProPublica ocd_id, Open States ocd-person/ocd-jurisdiction) depend on. Per the Google group notice 'Notice of Turndown of the Representatives API' (https://groups.google.com/g/google-civicinfo-api/c/9fwFn-dhktA), representativeInfoByAddress and representativeInfoByDivision were turned down on April 30, 2025 and a Divisions API method for looking up OCD-IDs by address remains. Worth an entry because it is the one address-to-officeholder route in this cluster that recently went defunct.
- **LegiScan.** <https://legiscan.com/> National legislative tracker covering all 50 states and Congress with a JSON API (free public tier and paid tiers per search results and third-party profiles). Sits squarely between GovTrack and Open States in this cluster and has an identifier scheme (people_id, bill_id) of its own. legiscan.com returned HTTP 403 to both WebFetch and curl in this survey, so its self-description could not be read; the entry should be written from a browser session.
- **Cicero (Azavea) address-to-official API.** <https://www.cicerodata.com/> Paid address-to-district and elected-official lookup with identifiers and verified social accounts across federal, state and local levels; one of the providers the Google Civic turndown notice points users toward. Belongs under identity resolution alongside Open States people.geo.
- **GPO GovInfo Bill Status bulk data and govinfo API.** <https://www.govinfo.gov/> Named as the upstream by GovTrack, the unitedstates/congress scrapers and the Congress.gov developer page (joint GPO/LOC/House Clerk/Senate Secretary effort), yet has no entry of its own even though the Congress.gov API does. If the cluster's purpose includes identifying which source is primary, the GPO bulk repository and its user guide deserve a row with their own license and coverage statements.
