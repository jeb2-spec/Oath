# Related-work record: Money-in-politics aggregators

*Read on 2026-09-21. A first reader wrote each entry from the project's own pages; a second reader, briefed to refute, re-fetched every cited page. Corrections are shown beside the claims they correct and both are kept. Presence in this record is not a claim about a project's quality, and absence is not either. Presence in the register is not evidence of wrongdoing: where a record below describes what a neighbour published about an officeholder, it describes the role and not the person, names no one outside a citation URL, and is not a Finding. Rendered from `data/aggregators.json` by `render.py`; edit the JSON, not this file.*

## OpenSecrets

<https://www.opensecrets.org/>

- **Organisation.**
  OpenSecrets, a 501(c)(3) formed in 2021 by the merger of the Center for Responsive Politics (CRP) and the National Institute on Money in Politics (NIMP)
- **Kind.**
  Nonprofit money-in-politics data aggregator and newsroom (federal and, since the merger, state campaign finance; lobbying; 527s; personal financial disclosures)
- **Self-description, as read.**
  Describes itself as nonpartisan, independent and nonprofit, with a mission to serve as the trusted authority on money in American politics by providing data, analysis and tools for policymakers, storytellers and citizens. Names three goals: data (collect, clean and create access), insights (analysis, reports, tools) and engagement (a community of users). The June 2, 2021 press release says CRP and NIMP joined to form a combined organisation integrating federal, state and local data on campaign finance and lobbying, with opensecrets.org retained as the URL and followthemoney.org continuing to be updated until a new site launched later in 2021. The FAQ says nearly all its data originates with an official government source, to which it adds processing and research (industry coding of contributors, employer standardisation, household attribution).
- **Subject scope.**
  Federal candidates and officeholders (campaign committees, leadership PACs, PAC and individual contributions, industries, elections); lobbying (clients, registrants, lobbyists, bills lobbied); 527 committees; personal financial disclosures of members of Congress (annual reports 2008-2018 on the section landing page; Periodic Transaction Reports back to 2012), executive-branch and judicial filers; Revolving Door; state-level campaign finance (served through followthemoney.org for state data through 2024).
- **Sources it says it uses.**
  - Federal Election Commission (congressional and presidential campaign finance; profile pages state figures are based on FEC data with an as-of date)
  - Senate Office of Public Records (lobbying)
  - State agencies across the country (state-level campaign finance)
  - Internal Revenue Service (527 committees)
  - Senate Office of Public Records and Office of the Clerk of the House (personal financial disclosures of members of Congress, per the personal-finance methodology)
  - U.S. Office of Government Ethics (executive-branch disclosures) and the Judicial Conference of the U.S. (judicial filings)
  - Press reports and official announcements (Revolving Door database; not a government source)
  - Linking to the primary filing: the personal-finances Reports tab offers the original disclosure files by filing year; per-row links from campaign-finance profile pages to individual FEC filings were not observed on the pages read
- **Outputs.**
  - Candidate and officeholder profiles: summary, PACs, individual donors and demographics, organizations, industries, elections, committee assignments
  - Personal-finances profiles: net worth, assets, liabilities, transactions (Periodic Transaction Reports and annual-report transactions, CSV download), reports (original disclosure files), other data
  - Bulk Data: compressed CSV tables with data dictionaries for campaign finance, lobbying, 527s, personal finance, and reference tables; account approval required
  - News and analysis articles (dated items in September 2026)
  - Custom research and commercial data licensing (commercial@opensecrets.org)
  - API: discontinued as of April 15, 2025
- **Per-person derived score or rank, as observed.**
  Per-person estimated net worth with a rank against the chamber (one member's 2018 net-worth page shows 'Rank: 6th in the House'). Section-level tables: 'Richest Members of Congress, 2018', 'Poorest Members of Congress, 2018' and 'Biggest wealth increase in Congress, 2008-2018' (top ten each, exportable to CSV), plus a median estimated-net-worth-over-time chart. The methodology states net worth is computed as a minimum-maximum range from reported value ranges and that the midpoint (average) is used for ranking filers by wealth. Per-candidate Top Contributors and top industry lists; 'Top Assets' aggregates across filers.
- **Identifiers exposed.**
  - OpenSecrets candidate ID (CID), format N followed by eight digits, e.g. cid=N00007360 in personal-finances and members-of-congress URLs
  - A numeric 'mpid' in current profile URLs, e.g. /profiles/jen-kiggans/us_congress/summary?mpid=1191305
  - Bulk reference files: CRP_IDs.xls (candidate IDs and other information), CRP_Categories.txt (industry codes), CRP_PFDRangeData.xls (range values for personal-finance calculations)
  - Bulk table named 'FEC Committees (PACs and Candidate and Party Committees)'; whether FEC committee IDs are carried in it was not verified (data dictionaries not opened)
- **Per-filing conditions it states or computes.**
  - None computed on the pages read. The transactions page footnote states the reporting rule it displays against: under the Ethics in Government Act as amended by the STOCK Act, members must report each purchase, sale or exchange of securities over $1,000, with a PTR due within 30 days of receiving notice of the transaction and not more than 45 days after the transaction; the page lists transactions with date and value range but no late-filing or other per-filing flag was observed
  - Coding rules (not per-filing conditions): a contribution receives an ideological code instead of an industry code when the contributor gives to an ideological PAC and the candidate has also received money from PACs representing that same ideological interest; contributions from members of one household are attributed to the primary earner's employer
- **Code.**
  No public code repository stated on the pages read.
- **Data licence.**
  Creative Commons Attribution-NonCommercial-ShareAlike 3.0 United States for site content and for Bulk Data; Bulk Data is for educational use after account registration, email confirmation, approval, and agreement to Terms of Service; attribution requested near the citation with a link; commercial republishing 'may involve a fee'; Revolving Door data is excluded from the Creative Commons download.
- **API.**
  The API page states: "As of April 15, 2025, our API offerings have been discontinued." (opensecrets.org/api). It directs data needs to commercial@opensecrets.org for a custom data solution. The still-posted API Terms of Service (last modified April 7, 2009) provided free educational, research and non-commercial use under CC BY-NC-SA, required citation, prohibited solicitation and commercial use without permission, prohibited scraping or storing a collection of the data, and disclaimed warranties.
- **Funding or business model, as stated.**
  501(c)(3) tax-exempt charity. About page: institutional grants, contributions from individuals, and income earned from custom research and licensing data for commercial use. FAQ: operated since 1983 on private-foundation grants and individual contributions, with some revenue from research fees and data contracts. The 2021 merger press release says the Hewlett Foundation provided critical support for the merger review and integration.
- **How it frames what a listing means.**
  Profile pages (Notes and References): clusters of contributions from people tied to one employer can indicate organized bundling, but in other cases the reason may be unrelated to the organization; totals by industry and ideology are conservative estimates; itemized figures may not match summary figures; a lag exists between filing and publication. Personal-finance methodology includes a 'What is missing from these disclosures?' section (personal residences and personal property not reported unless held for investment; federal retirement accounts not reported; two value ranges have no upper limit; salary not included) and notes net worth is an estimate within a range. No general statement about what a person's presence in the database implies was observed on the pages read.
- **Status at retrieval.**
  active (news articles dated September 9-16, 2026; profile pages state FEC summary data as of August 4, 2026 and transaction-level data as of July 17, 2026)
- **Corrected on second reading.**
  - *disclaimer_or_frame.* First read: No general statement about what a person's presence in the database implies was observed on the pages read. On re-reading: The cited FAQ page does state the presence criterion: 'Once a candidate files with the Federal Election Commission or a state agency, they're eligible to appear on OpenSecrets.org' and 'Once a candidate files with the FEC or a state agency, we list that candidate on our site' (with the $5,000 registration threshold explained under 'Why don't you list third-party candidates?'). That is a statement that presence means a filing exists, not a judgement about the person; the entry should record it rather than say none was observed. The FAQ also carries an accuracy caveat ('inaccuracies may result'). (<https://www.opensecrets.org/resources/faq>)
  - *subject_scope.* First read: personal financial disclosures of members of Congress (... Periodic Transaction Reports back to 2012) On re-reading: The cited transactions page states the PTR database is House-only: 'This database only displays reports for Members of the House of Representatives. We hope to have data on Senators included soon.' and 'This page displays the 50 most recent transactions reported by Members of the House of Representative.' Scope should read House PTRs back to 2012, not members of Congress generally. (<https://www.opensecrets.org/personal-finances/nancy-pelosi/transactions?cid=N00007360&year=2018>)
- **Not verified.**
  - https://www.opensecrets.org/about/methodology and https://www.opensecrets.org/about/tos returned the site's generic error page; the methodology content used here comes from the profile-page Methodology section and the personal-finance methodology page instead
  - Whether campaign-finance rows on profile pages link to individual FEC filings (not observed on pages read)
  - Whether bulk tables carry FEC candidate/committee IDs (data dictionaries and the Open Data User's Guide were not opened)
  - Whether personal-finance annual-report data on the site has been extended beyond 2018 (section landing page says 2018 filings are the latest available)
  - Full text of the Terms and Conditions page (only the opening was captured)
  - merger press release citation 'related articles dated September 2026 (status)': the captured page text was truncated before any related-articles list; status was instead confirmed from opensecrets.org/news
  - Whether campaign-finance rows on profile pages link to individual FEC filings (page text does not expose link targets)
  - Whether CRP_IDs.xls or the 'FEC Committees' table carries FEC candidate/committee IDs (dictionaries behind the bulk-data login were not opened)
  - The PTR listing on one member's transactions page for year=2018 shows 2014-dated PTR rows; whether the 'Recent PTR' block is filtered by year at all is unclear from the page
  - Full text of Terms and Conditions (only the opening was captured, as the entry says)
- **Confirmed by the second reader.** 13 claims, listed in the JSON.
- **Citations.**
  - <https://www.opensecrets.org/about/> (retrieved 2026-09-21): Self-description (mission, three goals), 501(c)(3) status, funding sources (grants, individuals, custom research and commercial data licensing)
  - <https://www.opensecrets.org/news/2021/06/opensecrets-merger-press-release/> (retrieved 2026-09-21): June 2, 2021 merger of CRP and NIMP to form OpenSecrets; URLs retained; followthemoney.org to be updated until new site; Hewlett Foundation support; 'Created in 2021 by the merger'; related articles dated September 2026 (status)
  - <http://www.opensecrets.org/api> (retrieved 2026-09-21): API discontinued as of April 15, 2025 (quoted); custom data solution contact; CC BY-NC-SA 3.0 US statement
  - <https://www.opensecrets.org/open-data/api-terms-of-service> (retrieved 2026-09-21): Historical API terms (last modified April 7, 2009): educational/non-commercial use, CC BY-NC-SA, citation, no solicitation or commercial use, no scraping/storing, as-is disclaimer
  - <https://www.opensecrets.org/open-data/bulk-data> (retrieved 2026-09-21): Bulk Data scope (campaign finance, lobbying, 527s, personal finances, reference tables), CSV format with data dictionaries, educational use, attribution terms, commercial fee, Revolving Door excluded, CC license
  - <https://www.opensecrets.org/open-data> (retrieved 2026-09-21): Bulk Data sign-up steps (Terms of Service, registration, approval); commercial republishing generally involves a fee
  - <https://www.opensecrets.org/open-data/bulk-data-documentation> (retrieved 2026-09-21): Bulk table list including 'FEC Committees' and personal-finance Transactions; reference files CRP_IDs.xls, CRP_Categories.txt, CRP_PFDRangeData.xls
  - <https://www.opensecrets.org/resources/faq> (retrieved 2026-09-21): Government sources by dataset (FEC, Senate Office of Public Records, state agencies, IRS, congressional information-collectors, press reports for Revolving Door); funding since 1983; human coding of industries
  - <https://www.opensecrets.org/personal-finances/methodology> (retrieved 2026-09-21): Personal-finance sources (Senate Office of Public Records, House Clerk, OGE, Judicial Conference), years 2008-2018, net-worth range and midpoint ranking method, STOCK Act description, 'What is missing from these disclosures?' caveats
  - <https://www.opensecrets.org/personal-finances> (retrieved 2026-09-21): 'Richest', 'Poorest' and 'Biggest wealth increase' tables for 2018, CSV export, median net worth chart, tables based on 2018 filings
  - <https://www.opensecrets.org/personal-finances/nancy-pelosi/net-worth?cid=N00007360&year=2018> (retrieved 2026-09-21): Per-person rank ('Rank: 6th in the House'), CID identifier in URL, top industries and top assets per filer
  - <https://www.opensecrets.org/personal-finances/nancy-pelosi/reports?cid=N00007360> (retrieved 2026-09-21): Reports tab: original disclosure files accessible by filing year (primary-filing linking for personal finances)
  - <https://www.opensecrets.org/personal-finances/nancy-pelosi/transactions?cid=N00007360&year=2018> (retrieved 2026-09-21): PTR and annual-report transaction listings with date and value ranges; footnote stating the STOCK Act 30-day/45-day reporting rule; CSV download; no per-filing flag observed
  - <https://www.opensecrets.org/members-of-congress/nancy-pelosi/summary?cid=N00007360> (retrieved 2026-09-21): Profile page methodology and FAQ: FEC as source, as-of dates (August 4 and July 17, 2026), industry and ideology coding rules, household attribution, bundling frame, conservative-estimate and lag caveats
  - <https://www.opensecrets.org/profiles/jen-kiggans/us_congress/summary?mpid=1191305> (retrieved 2026-09-21): Current profile URL scheme exposing a numeric mpid; committee assignments shown; same FEC as-of dates
  - <https://www.opensecrets.org/about/terms-and-conditions> (retrieved 2026-09-21): Existence of a site Terms and Conditions agreement governing use of the Services (only the opening of the page was captured)

## FollowTheMoney (National Institute on Money in Politics)

<https://www.followthemoney.org/>

- **Organisation.**
  National Institute on Money in Politics (earlier the National Institute on Money in State Politics), which the site says joined with the Center for Responsive Politics to become OpenSecrets; the site's license names OpenSecrets as licensor
- **Kind.**
  State campaign-finance and lobbying database, continued under OpenSecrets after the 2021 merger; federal data has moved to opensecrets.org
- **Self-description, as read.**
  The home page states that the National Institute on Money in Politics and the Center for Responsive Politics "joined forces to become OpenSecrets" (followthemoney.org), and that the site displays state campaign finance data through the 2024 election while federal data has moved to OpenSecrets.org. The About page describes the purpose as promoting an accountable democracy by compiling campaign-donor, lobbyist and other information from government disclosure agencies nationwide and making it freely available; founded 1999; recognised with a 2015 MacArthur Award; the Campaign Finance Institute merged with NIMP in 2018.
- **Subject scope.**
  State elections: contributions to statewide, legislative and court offices (2000 onward), ballot measures (2003 onward), independent spending in selected states (2006 onward); state lobbying registrations (2006 onward) and lobbying spending in selected states (2002 onward); selected local races (2006 onward). Federal: presidential, Senate and House contributions and independent spending 2010-2020 and party committee contributions 2009-2020 (now served by opensecrets.org).
- **Sources it says it uses.**
  - State disclosure agencies in all 50 states (per About page)
  - Federal Election Commission for federal campaigns since 2010 (per About page)
  - Linking each row to the primary filing: not verified; the entity-details page could not be loaded
- **Outputs.**
  - Entity-details pages per candidate, committee, donor or lobbyist (eid-keyed URLs)
  - myFollowTheMoney free accounts with web access and downloads capped at 1,000 records per year for general users; expanded access on application for accredited academic institutions, journalism organisations, and registered 501(c)(3), (5) and (6) entities
  - APIs: an 'Ask Anything' API documented in a PDF and an Entity Details API mirroring the entity page (XML or JSON)
- **Per-person derived score or rank, as observed.**
  None observed on the pages that loaded; the entity-details page, where per-person totals or rankings would appear, could not be loaded (see could_not_verify).
- **Identifiers exposed.**
  - Entity ID ('eid', numeric), used in entity-details URLs (e.g. entity-details?eid=210204) and as the required parameter of the Entity Details API
- **Per-filing conditions it states or computes.**
  - None observed on the pages read
- **Code.**
  No public code repository stated on the pages read.
- **Data licence.**
  Creative Commons Attribution-NonCommercial-ShareAlike 3.0 United States; the Terms of Data Use name the National Institute on Money in State Politics (now operating as OpenSecrets) as licensor; attribution required in reports, articles, mashups or visual displays; data may not be used for political campaigns or contribution solicitation, or sold to third parties; commercial entities need a separate commercial license; expanded access is denied to electoral entities (527s, super PACs, party committees, 501(c)(4)s, candidate committees).
- **API.**
  Available after creating a free myFollowTheMoney account; Entity Details API at http://api.followthemoney.org/entity.php?eid=...&APIKey=...&mode=xml|json; Ask Anything API documented in PDF; no rate limits stated on the pages read; the documentation page says detailed documentation for the Entity Details API is being developed.
- **Funding or business model, as stated.**
  About page describes a 501(c)(3) tax-exempt charitable organisation and references Form 990s and financial statements; now part of OpenSecrets (see the OpenSecrets entry for the merged organisation's stated funding).
- **How it frames what a listing means.**
  No statement about what a listing means for a person was observed on the pages that loaded; the Terms of Data Use restrict uses (no campaign, solicitation or resale use) rather than framing the data's meaning.
- **Status at retrieval.**
  merged (the home page states NIMP and CRP joined forces to become OpenSecrets; federal data moved to opensecrets.org; state data displayed through the 2024 election; copyright 2026)
- **Not verified.**
  - Entity-details page (HTTP 403 via fetch; bot-check page via browser): per-person totals or rankings, any disclaimer, and whether rows link to state or FEC filings
  - Whether the site continues to be updated after the 2024 election
  - Relationship between eid and other identifier schemes (OpenSecrets CID, FEC ID)
  - Entity-details page (eid=210204): returns a bot-verification interstitial in the browser and 403 via fetch, so per-person totals, rankings, disclaimers and links to state or FEC filings remain unchecked, as the entry says
  - Relationship between eid and OpenSecrets CID or FEC IDs
- **Confirmed by the second reader.** 8 claims, listed in the JSON.
- **Citations.**
  - <https://www.followthemoney.org/> (retrieved 2026-09-21): Merger notice (quoted), state data through 2024, federal data 2010-2020 moved to OpenSecrets, data coverage by category and year, CC BY-NC-SA 3.0 US license by OpenSecrets, copyright 2026
  - <https://www.followthemoney.org/about-us/> (retrieved 2026-09-21): Purpose statement, founded 1999, 2015 MacArthur Award, 2018 Campaign Finance Institute merger, sources (state agencies in all 50 states; FEC since 2010), 501(c)(3) status and 990s reference
  - <https://www.followthemoney.org/our-data/apis/> (retrieved 2026-09-21): APIs available after a free myFollowTheMoney account; CC BY-NC-SA license; documentation, support and examples sections
  - <https://www.followthemoney.org/our-data/apis/documentation> (retrieved 2026-09-21): Ask Anything API (PDF) and Entity Details API; base URL api.followthemoney.org/entity.php; eid and APIKey parameters; xml/json modes; no rate limits stated; documentation being developed
  - <https://www.followthemoney.org/our-data/terms-of-data-use/> (retrieved 2026-09-21): License and licensor, attribution, non-commercial and no-solicitation restrictions, 1,000-record annual cap, expanded-access categories and exclusions

## MapLight

<https://maplight.org/>

- **Organisation.**
  MapLight, a 501(c)(3) nonprofit founded in 2005
- **Kind.**
  Nonprofit civic-technology organisation that builds campaign-finance, lobbying and ethics disclosure software for state and local governments; earlier money-and-votes research data now offered as an archived dataset
- **Self-description, as read.**
  The home page states "MapLight creates technology to improve democracy" (maplight.org) under the heading Technology for Democracy. The About page describes a nonpartisan 501(c)(3) founded in 2005 that provides campaign finance, lobbying and ethics disclosure solutions to state and local governments, naming the California Secretary of State, Minneapolis, Denver and Maine as clients, and that operated Voter's Edge, a nonpartisan voting guide for California voters; awards listed from 2007 to 2015.
- **Subject scope.**
  Software products: Campaign Finance (e-filing and disclosure), Lobbying Filings (registration and reporting), Ethics Filings (personal financial disclosures), E-Signatures (candidate and ballot-measure petitions); Data Series: Bill Positions, a dataset of organisational positions on congressional legislation covering 2007-2021 (more than 225,000 positions on more than 14,000 bills).
- **Sources it says it uses.**
  - Bill Positions dataset: companies' websites, press releases, government documents, congressional hearing testimony and other public-record sources (per the Data Series page)
  - Sources for the earlier money-and-votes database (classic.maplight.org) could not be loaded
  - Linking rows to primary filings: not stated on the pages read
- **Outputs.**
  - Disclosure software operated for government clients (e-filing, lobbying, ethics, e-signatures)
  - Bill Positions dataset, available for academic and research use for a licensing fee; the page states the complete dataset is no longer being updated
  - Earlier public money-and-votes database at classic.maplight.org (unreachable at retrieval)
- **Per-person derived score or rank, as observed.**
  None observed on the pages read.
- **Identifiers exposed.**
  - Not stated on the pages read
- **Per-filing conditions it states or computes.**
  - None observed on the pages read; the classic site's money-and-votes methodology (any contribution-to-vote timing window) could not be loaded
- **Code.**
  No public code repository stated on the pages read.
- **Data licence.**
  Bill Positions: 'available for academic and research use for a modest licensing fee' (Data Series page); no open license stated for any dataset on the pages read.
- **API.**
  None stated on the pages read.
- **Funding or business model, as stated.**
  501(c)(3) nonprofit (About page). The Solutions page lists software products and government customers (California Secretary of State, Maine Ethics Commission, City and County of Denver via testimonials); the Data Series page states a licensing fee for the Bill Positions data. The 'How we're funded' page could not be loaded, so foundation or donor funding is not verified.
- **How it frames what a listing means.**
  None observed on the pages read.
- **Status at retrieval.**
  unknown (pages show a 2025 copyright line but no content dated within the last twelve months and no explicit current notice; the Bill Positions dataset is stated to be no longer updated)
- **Not verified.**
  - classic.maplight.org pages (TLS handshake failure via fetch; navigation denied in the browser): money-and-votes methodology, data sources (third-party search snippets mention CRP/OpenSecrets and GovTrack, not verified on MapLight's own page), timing windows, and the Federal Money and Politics Data Set terms
  - https://maplight.org/how-were-funded (HTTP 403 via fetch; a sign-up wall in the browser): funding sources
  - https://maplight.org/about/ returned 404 (the /about-us page was used instead)
  - Any content dated within the last twelve months
  - Whether any page on maplight.org carries content dated within the last twelve months (the News page's newest item is Dec 1, 2024; a blog or other section could exist but was not found)
  - Money-and-votes methodology and sources on classic.maplight.org (unreachable)
- **Confirmed by the second reader.** 5 claims, listed in the JSON.
- **Citations.**
  - <https://maplight.org/> (retrieved 2026-09-21): Self-description (quoted), product list (Campaign Finance, Lobbying Filings, Ethics Filings, E-Signatures, Data Series), copyright 2025
  - <https://www.maplight.org/about-us> (retrieved 2026-09-21): 501(c)(3), founded 2005, nonpartisan, government disclosure solutions, named clients, Voter's Edge, awards 2007-2015, no mention of the earlier research database
  - <https://www.maplight.org/data-series> (retrieved 2026-09-21): Bill Positions dataset 2007-2021, counts, sources, licensing fee for academic and research use, no longer being updated
  - <https://www.maplight.org/solutions> (retrieved 2026-09-21): Five product lines, customers named in testimonials, founded 2005, copyright 2025

## Sunlight Foundation

<https://sunlightfoundation.com/>

- **Organisation.**
  Sunlight Foundation (nonprofit; ceased operations in 2020)
- **Kind.**
  Defunct open-government nonprofit; website maintained as a static archive; tools transferred to other organisations in 2016 and 2020
- **Self-description, as read.**
  The home page states that as of September 2020 the Sunlight Foundation is no longer active and that "This site is maintained as a static archive only." (sunlightfoundation.com). The board chair's note of September 24, 2020 (Michael R. Klein) says the board determined the organisation's role was no longer essential to its original mission, that staff and activities were transferred to other institutions or discontinued, and that its intellectual property, name and records were transferred to the Internet Archive and the Berkman Klein Center at Harvard.
- **Subject scope.**
  Historically: open-government data tools and APIs for Congress and states (Congress API, Capitol Words, Open States, Influence Explorer and Real-Time Influence Explorer, Foreign Influence Explorer, Political Party Time, Politwoops, Political Ad Sleuth, Scout, Hall of Justice, House Staff Directory, House Expenditure Database).
- **Sources it says it uses.**
  - Not stated on the archive pages read; influenceexplorer.com (a Sunlight product page) references the OpenFEC API in an August 18, 2015 post
  - Linking rows to primary filings: not applicable to the archive; not verified for the retired tools
- **Outputs.**
  - Static archive of the website
  - Disposition of tools per the November 1, 2016 Sunlight Labs update (see notes)
  - APIs page directing users to successors (Congress API operated by ProPublica; Open States run independently)
- **Per-person derived score or rank, as observed.**
  None observed on the pages read.
- **Identifiers exposed.**
  - None observed on the pages read
- **Per-filing conditions it states or computes.**
  - None observed on the pages read
- **Code.**
  A github.com/sunlightlabs organisation appeared in search results but was not fetched; not verified.
- **Data licence.**
  Not stated on the pages read.
- **API.**
  The APIs page states Sunlight is no longer the provider of these services after the closure of Sunlight Labs (2016); the Congress API is operated by ProPublica; Open States is independently run by former Sunlight staff. influenceexplorer.com states the Influence Explorer and TransparencyData APIs were deprecated starting September 2015 and turned off beginning January 2016.
- **Funding or business model, as stated.**
  not verified (no funding statement on the archive pages read)
- **How it frames what a listing means.**
  Static-archive notice on every page; no content framing observed.
- **Status at retrieval.**
  defunct (home page: no longer active as of September 2020; board chair note dated September 24, 2020)
- **Not verified.**
  - Disposition of the non-foreign Influence Explorer after 2016 (not named in the 2016 post)
  - Whether influenceexplorer.com still serves data (the page fetched is 2015-era content)
  - Funding history
  - Existence and content of the sunlightlabs GitHub organisation (search result only)
  - Disposition of the non-foreign Influence Explorer after 2016
  - Whether influenceexplorer.com still serves data (the fetched content is 2015-era)
  - Funding history (no funding statement on the archive pages read)
- **Confirmed by the second reader.** 4 claims, listed in the JSON.
- **Citations.**
  - <https://sunlightfoundation.com/> (retrieved 2026-09-21): Closure notice as of September 2020 and static-archive statement (quoted)
  - <https://sunlightfoundation.com/2020/09/24/a-note-from-the-sunlight-foundations-board-chair/> (retrieved 2026-09-21): Closure reasoning, transfer of staff and activities, transfer of IP, name and records to the Internet Archive and Berkman Klein Center, author Michael R. Klein
  - <https://sunlightfoundation.com/2016/11/01/sunlight-labs-update-nonprofits-step-up-to-preserve-tools-for-transparency/> (retrieved 2026-09-21): November 1, 2016 disposition of Sunlight Labs tools: ProPublica (Congress API, Capitol Words, Politwoops, House Staff Directory, House Expenditure Database), CRP (Foreign Influence Explorer, Political Party Time), Marshall Project (Hall of Justice), Open States alumni group led by James Turk (Open States), Cornell LII (Docket Wrench successor), Commerce (Census API wrapper); retired Real-Time Influence Explorer, Political Ad Sleuth, Scout; Email Congress without a home; author Kat Duffy
  - <https://sunlightfoundation.com/api/> (retrieved 2026-09-21): Sunlight no longer provides the APIs; Congress API operated by ProPublica; Open States independently run by former Sunlight staff; Politwoops at ProPublica
  - <https://www.influenceexplorer.com/> (retrieved 2026-09-21): Influence Explorer and TransparencyData APIs deprecated from September 2015 and turned off from January 2016; described as a product of the Sunlight Foundation

## Open States / Plural

<https://openstates.org/ (redirects to https://pluralpolicy.com/open); https://open.pluralpolicy.com/; https://docs.openstates.org/>

- **Organisation.**
  Plural Policy, Inc., which adopted the Open States project in 2021; Plural was acquired by SAI360 (announced December 1, 2025)
- **Kind.**
  Open state-legislative data project (scrapers, API, bulk downloads, curated people data) operated by a commercial legislative- and regulatory-tracking software company
- **Self-description, as read.**
  The GitHub organisation page describes Open States as striving to improve civic engagement at the state level by providing data and tools regarding state legislatures, aggregating legislative information from all 50 states, Washington D.C. and Puerto Rico, standardising it and publishing it via the website, an API and bulk downloads, and as a project of Plural since 2021. pluralpolicy.com/open says Plural is carrying the legacy forward from the Open States project it adopted in 2021 and makes the collection available for bulk download and via its API. Plural's home page describes AI-native legislative and regulatory tracking software for government affairs teams; the About page says Plural was acquired by SAI360, a governance, risk and compliance platform, and that the acquisition did not change what it builds.
- **Subject scope.**
  State legislatures in all 50 states, D.C. and Puerto Rico: jurisdictions, sessions, bills (with text), votes, people (state legislators, governors, some municipal leaders), organisations and committees, posts, memberships, events; legislative district geography. The Plural commercial product also covers Congress and 40+ countries.
- **Sources it says it uses.**
  - State legislature websites, read by the openstates-scrapers (GPL-3.0) repository; people data historically scraped and now manually curated in the people repository
  - Whether bill and vote records carry a link to the source page on the legislature site was not verified on the pages read
- **Outputs.**
  - API v3 (REST) at https://v3.openstates.org/ with interactive docs at /docs and /redoc; GraphQL API marked deprecated
  - Bulk data: legislator YAML and CSV, per-session bill and vote CSV and JSON archives (including full bill text), legislative district polygons (November 2018), monthly PostgreSQL database dumps (September 2026 version referenced)
  - Free bill search and legislator finder at pluralpolicy.com/open; open.pluralpolicy.com serves API key registration and bulk downloads while most other tools were disabled after a June 7, 2023 transition notice
  - Plural commercial product: AI bill and regulation summaries, legislator and staff contact data, alerts, dashboards
- **Per-person derived score or rank, as observed.**
  None observed on the pages read.
- **Identifiers exposed.**
  - Person id: a UUID per person in the people schema (documentation refers to OCD-person IDs); jurisdictions use ocd-jurisdiction identifiers; bills addressable by ocd-bill UUID or by jurisdiction/session/identifier; committee and event ids in API paths
  - People schema 'ids' block: twitter, youtube, instagram, facebook
  - People schema 'other_identifiers': free-form entries of scheme (required), identifier (required), start_date and end_date (optional); no bioguide, FEC, OpenSecrets, Wikidata, VoteSmart or Ballotpedia schemes are enumerated on the schema page
  - pupa_id being replaced by dedupe_key (per an enhancement proposal referenced on the docs index)
- **Per-filing conditions it states or computes.**
  - None observed on the pages read
- **Code.**
  github.com/openstates (28 repositories): openstates-scrapers (Python, GPL-3.0, updated Sep 21, 2026), people (CC0-1.0, updated Sep 21, 2026), jurisdictions (AGPL-3.0), openstates-core (MIT), openstates.org (MIT), api-v3 (MIT), documentation (CC-BY-4.0), openstates-geo (MIT), scraper-audit (GPL-3.0).
- **Data licence.**
  People data: public domain in the United States with copyright waived via a CC0 dedication (people repository README and contributing docs). Bulk data page: "data is provided under a public domain dedication" with attribution described as appreciated (open.pluralpolicy.com/data). No separate terms of use for API data were found on the pages read.
- **API.**
  API v3 at https://v3.openstates.org/; API key required, obtained from an account profile at open.pluralpolicy.com/accounts/profile/ and passed as an X-API-KEY header or apikey query parameter; endpoints for jurisdictions, people, people.geo, bills, committees, events; rate limits and tiers not stated on the pages read.
- **Funding or business model, as stated.**
  Plural sells subscriptions: Essential $59/month or $609/year, Professional $5,000/year, Enterprise custom pricing; states over 500 teams across advocacy, academia and government affairs; free tools alongside. SAI360 announced its acquisition of Plural Policy on December 1, 2025 with financial terms not disclosed; the announcement does not mention Open States.
- **How it frames what a listing means.**
  None observed on the pages read.
- **Status at retrieval.**
  active (GitHub repositories updated September 17-21, 2026; monthly database dump for September 2026 referenced; Plural pages published September 10, 2026)
- **Corrected on second reading.**
  - *identifiers_exposed.* First read: no bioguide, FEC, OpenSecrets, Wikidata, VoteSmart or Ballotpedia schemes are enumerated on the schema page On re-reading: The schema page uses 'votesmart' as its worked example for other_identifiers: 'scheme: origin of this identifier (e.g. "votesmart")' with 'identifier ... (e.g. 13823)'. It enumerates no list, but VoteSmart is named on the page; the entry should say the page gives votesmart as an example and enumerates no closed list. (<https://github.com/openstates/people/blob/main/schema.md>)
- **Not verified.**
  - API rate limits, quotas or paid tiers (not stated on the API v3 docs or the portal page)
  - Whether other_identifiers entries in the published people data include bioguide, FEC, OpenSecrets or Wikidata identifiers
  - Whether bill and vote records carry source URLs to the legislature site
  - Open States history page contains no chronology; the 2016 alumni transfer is documented on Sunlight's site, the 2021 adoption on pluralpolicy.com/open
  - Whether 'OCD-person IDs' is the wording used on the docs index (the fetch summary did not surface that phrase)
  - API rate limits or tiers: not on the cited pages; a web-search snippet attributes tiers (default 500/day, legacy and bronze 5,000/day, silver 50,000/day) to github.com/openstates/issues/discussions/205, but that discussion returned 404 via fetch and NOT_FOUND via the GitHub GraphQL API, so it cannot be confirmed; the entry's 'no rate limit documented' should not be read as 'no rate limit exists'
- **Confirmed by the second reader.** 10 claims, listed in the JSON.
- **Citations.**
  - <https://openstates.org/> (retrieved 2026-09-21): 301 redirect to https://pluralpolicy.com/open
  - <https://pluralpolicy.com/open> (retrieved 2026-09-21): Plural adopted the Open States project in 2021; bulk download and API; API key managed at open.pluralpolicy.com; copyright 2026
  - <https://open.pluralpolicy.com/> (retrieved 2026-09-21): API key portal, bulk downloads, GitHub link, June 7, 2023 transition notice, most tools disabled, 'Plural / SAI360' branding
  - <https://open.pluralpolicy.com/data/> (retrieved 2026-09-21): Bulk data offerings (legislator YAML/CSV, per-session CSV/JSON, geo data Nov 2018, monthly PostgreSQL dumps with a September 2026 version), public domain dedication (quoted), update cadence
  - <https://docs.openstates.org/> (retrieved 2026-09-21): API v3, GraphQL deprecated, coverage of 50 states plus D.C. and Puerto Rico, OCD-person IDs, pupa_id to dedupe_key proposal, openstates/documentation repository
  - <https://docs.openstates.org/api-v3/> (retrieved 2026-09-21): Base URL, API key requirement and registration URL, header/query parameter, endpoint list, interactive docs; no rate limits or terms stated
  - <https://docs.openstates.org/data/> (retrieved 2026-09-21): Data model concepts (jurisdictions, sessions, bills, votes, persons, organizations, posts, memberships); no license stated on that page
  - <https://github.com/openstates> (retrieved 2026-09-21): Organisation description, repository list with licenses and update dates, project of Plural since 2021
  - <https://github.com/openstates/people> (retrieved 2026-09-21): Contents (YAML on legislators, governors, some municipal leaders), CC0 dedication, move from scraping to manual curation
  - <https://github.com/openstates/people/blob/main/schema.md> (retrieved 2026-09-21): Person id as UUID, ids block (twitter, youtube, instagram, facebook), other_identifiers as free-form scheme/identifier with optional dates, ocd-jurisdiction format
  - <https://docs.openstates.org/contributing/people/> (retrieved 2026-09-21): People data in the public domain via CC0; contributors waive copyright
  - <https://docs.openstates.org/contributing/openstates-org/> (retrieved 2026-09-21): open.pluralpolicy.com historically provided free tools, API key registration and bulk data; functionality migrating into the Plural application; Django
  - <https://pluralpolicy.com/> (retrieved 2026-09-21): Product description, pricing tiers, customer count, coverage (50 states, D.C., Puerto Rico, Congress, 40+ countries), page published September 10, 2026
  - <https://pluralpolicy.com/about> (retrieved 2026-09-21): Acquisition by SAI360 described as acquired not absorbed; customer types; remote-first; no Open States history on the page
  - <https://pluralpolicy.com/news/sai360-announces-acquisition-of-plural-policy-expanding-ai-regulatory-change-management/> (retrieved 2026-09-21): December 1, 2025 acquisition of Plural Policy by SAI360; terms not disclosed; no mention of Open States

## FEC open data (fec.gov/data and the OpenFEC API)

<https://www.fec.gov/data/ ; https://api.open.fec.gov/developers/>

- **Organisation.**
  Federal Election Commission (U.S. government agency)
- **Kind.**
  Primary publisher of federal campaign-finance filings: browse site, RESTful API (OpenFEC 1.0) and bulk data files
- **Self-description, as read.**
  The developers page describes an API that allows users to explore the way candidates and committees fund their campaigns, a RESTful web service supporting full-text and field-specific searches on FEC data, with bulk downloads on the main site and data updated nightly. It states: "Information is tied to the underlying forms by file ID and image ID." (api.open.fec.gov/developers). fec.gov/data presents candidate and committee financial profiles, receipts, disbursements, loans and debts, filings and reports, and notes the information is produced and disseminated at U.S. taxpayer expense.
- **Subject scope.**
  Federal candidates and committees (authorized campaign committees, PACs, party committees, independent-expenditure-only groups, corporations and unions filing communication costs); itemized receipts (Schedule A), disbursements (B), loans (C), debts (D), independent expenditures (E), party-coordinated expenditures (F), communication costs (Form 7), electioneering communications; summary and detailed financial reports (Forms 3, 3X, 3P, 13); bulk files by two-year cycle from 1979 through 2026; form images with availability back to 1972; PostgreSQL dumps from 1975 to present.
- **Sources it says it uses.**
  - Itself: reports and statements filed electronically, plus paper filings scanned into the database; summary data enters the databases and report images post to fec.gov within 48 hours of receipt
  - Rows are tied to the underlying form by file ID and image ID (developers page), i.e. each API record can be traced to the filing image
- **Outputs.**
  - fec.gov/data browse interface for candidates, committees, receipts, disbursements, filings
  - OpenFEC API 1.0 (candidate, committee, dates, financial, filings, schedules A-F, communication cost, electioneering endpoints; /swagger schema)
  - Bulk data files: candidate master and summary, committee master and summary, candidate-committee linkages, PAC summary, leadership PACs, Forms 1 and 2, individual contributions, committee-to-candidate, operating expenditures, communication costs, electioneering, independent expenditures, inter-committee transactions, false and fictitious filings, daily .fec compilations, PostgreSQL database dumps; weekly Schedule A dumps
  - Source code on GitHub (fecgov/openFEC)
- **Per-person derived score or rank, as observed.**
  None observed on the pages read (the API provides aggregates by candidate and committee; no per-person rank or leaderboard was observed on the pages read).
- **Identifiers exposed.**
  - Candidate ID (e.g. P00003335), used as candidate_id in the API
  - Committee ID (e.g. C00431445), used as committee_id in the API
  - Filing image numbers; file ID and image ID tying records to the underlying forms
  - Form type codes (F1, F2, F3, F3X, F3P, F13, F7 and others)
- **Per-filing conditions it states or computes.**
  - None; the FEC publishes filings and does not compute per-filing conditions on the pages read (the bulk list includes a 'False and Fictitious Filings' file, 2016-2026, which is an agency-designated category rather than a computed signal)
- **Code.**
  https://github.com/fecgov/openFEC (develop branch, 8,950 commits, open issues and pull requests at retrieval). LICENSE.md refers to the FEC Default License; the FEC LICENSE.md states the project is a U.S. government work in the public domain within the United States, waives copyright worldwide via CC0 1.0 Universal, releases contributions under CC0, and notes FEC data may not be used for commercial solicitation or to sell contributor lists.
- **Data licence.**
  Public domain / CC0 for the code and government works. Data-use restriction under 52 U.S.C. 30111(a)(4) and 11 CFR 104.15: information about individual contributors (names, addresses) copied from reports may not be sold or used to solicit contributions or for commercial purposes; exceptions include committees' own contributor lists, names of political committees, use in newspapers, magazines and books whose principal purpose is not solicitation or commerce, and bona fide academic research (AO 1986-25). The bulk-data page repeats that individual contributors' names and addresses may not be sold or used for commercial purposes or to solicit contributions.
- **API.**
  API key via api.data.gov signup form; DEMO_KEY for trial (api.data.gov: 30 requests per IP per hour, 50 per IP per day); a registered key allows up to 1,000 calls per hour (api.data.gov default across participating agencies); 100 results per page; a 7,200-calls-per-hour (120 per minute) key can be requested by email to APIinfo@fec.gov; key passed as X-Api-Key header, api_key parameter, or HTTP Basic username; use is stated to be subject to the Terms of Service and Acceptable Use policy (link target not verified); questions handled through a community-led group.
- **Funding or business model, as stated.**
  Federal agency; fec.gov/data states the information is produced and disseminated at U.S. taxpayer expense.
- **How it frames what a listing means.**
  The about-campaign-finance-data page states the information is not intended to replace the law or change its meaning and creates no rights or obligations (paraphrased). The sale-or-use page and bulk-data page carry the contributor-information restriction. No statement about what a candidate's or committee's listing implies was observed.
- **Status at retrieval.**
  active (2026 election-cycle data highlighted on fec.gov/data; bulk files through the 2026 cycle; API data updated nightly)
- **Not verified.**
  - The target of the 'Terms of Service and Acceptable Use policy' link on the developers page (the page's link hrefs could not be captured; https://api.data.gov/terms/ and https://api.data.gov/docs/ returned 404)
  - Whether the API exposes a sub_id or other transaction-level identifier (not on the page text captured)
  - The 'raising' and 'spending' summary tables on fec.gov/data (not captured; no ranking claim made)
  - Rate limiting specifics beyond those stated on the developers page and the api.data.gov developer manual
  - Target URL of the 'Terms of Service and Acceptable Use policy' link on the developers page (link hrefs not exposed in page text)
  - Whether the API exposes sub_id or another transaction-level identifier
  - The 'raising' and 'spending' summary tables on fec.gov/data (a 'top fundraisers and spenders' comparison is present but was not examined for ranking semantics)
- **Confirmed by the second reader.** 8 claims, listed in the JSON.
- **Citations.**
  - <https://www.fec.gov/data/> (retrieved 2026-09-21): Data published, identifier examples (P00003335, C00431445, image numbers), OpenFEC API and GitHub links, taxpayer-expense statement, 2026 cycle data
  - <https://api.open.fec.gov/developers/> (retrieved 2026-09-21): OpenFEC 1.0 description (quoted), nightly updates, file ID and image ID linkage, API key signup, DEMO_KEY, 1,000 calls per hour, 100 results per page, 7,200 per hour on request, Terms of Service and Acceptable Use reference, contributor-use restriction, source code, endpoint families and schedule definitions
  - <https://www.fec.gov/campaign-finance-data/about-campaign-finance-data/> (retrieved 2026-09-21): Electronic and scanned paper filings, 48-hour posting, form types with availability from 1972, disclaimer that the information does not replace the law, API and bulk links
  - <https://www.fec.gov/data/browse-data/?tab=bulk-data> (retrieved 2026-09-21): Bulk file inventory and year ranges (1979-2026), formats, PostgreSQL dumps 1975-present, contributor sale/use restriction, 48-hour lag note
  - <https://www.fec.gov/updates/sale-or-use-contributor-information/> (retrieved 2026-09-21): 52 U.S.C. 30111(a)(4) and 11 CFR 104.15 restriction, what is protected, exceptions including AO 1986-25
  - <https://github.com/fecgov/openFEC> (retrieved 2026-09-21): Repository description, API Umbrella for rate limiting and authentication, commit count and activity, public developers URL
  - <https://github.com/fecgov/openFEC/blob/develop/LICENSE.md> (retrieved 2026-09-21): Mix of public-domain government work and other open-source works; reference to the FEC Default License
  - <https://github.com/fecgov/FEC/blob/master/LICENSE.md> (retrieved 2026-09-21): U.S. government work in the public domain, CC0 1.0 worldwide waiver, contributions under CC0, note on FEC data-use restriction
  - <https://api.data.gov/docs/developer-manual/> (retrieved 2026-09-21): 40-character API key, 1,000 requests per hour default, DEMO_KEY 30 per hour and 50 per day per IP, key passing methods, rate-limit headers and HTTP 429

## Transparency USA

<https://www.transparencyusa.org/>

- **Organisation.**
  Transparency USA, a 501(c)(3) nonprofit based in Midland, Texas
- **Kind.**
  Nonprofit aggregator of state-level campaign-finance data (25 states) with lobbying data for Texas
- **Self-description, as read.**
  The About page states the mission is to provide "clear, accurate, easy-to-understand information about the money in state politics" (transparencyusa.org/about-us). It describes a database of campaign-finance data for 25 named states covering state-level candidates, PACs, donors and payees (with Texas lobbying), organised by two-year election cycles, with state profiles listing current politicians and the laws regulating campaign finance in each state; it says raw data from the state agency is posted immediately upon receipt and then de-duplicated and corrected. The home page shows counters of 130.87+ million transactions, 25 states, 298,463 candidates and committees, and $100.7 billion in tracked political spending, and says the database is constantly updated as new numbers are released.
- **Subject scope.**
  State-level candidates, officeholders (governor, attorney general, state legislators), PACs, donors and payees in Alabama, Arizona, California, Colorado, Florida, Georgia, Idaho, Illinois, Indiana, Iowa, Michigan, Minnesota, Nevada, New Hampshire, New Mexico, New York, North Carolina, Ohio, Pennsylvania, South Carolina, Texas, Virginia, Washington, Wisconsin and Wyoming; contributions and expenditures by two-year cycle; Texas lobbying.
- **Sources it says it uses.**
  - State agencies to which candidates and PACs file donation and expenditure reports (About page); the FAQ directs federal queries to fec.gov
  - Linking each row to the primary filing: not verified
- **Outputs.**
  - State profiles, entity pages, transaction history and an Advanced Transaction Search by date range or amount
  - Big-picture lists: top 10 donors in a state per cycle; totals by party
  - Articles and an email subscription; 'Our Data on Your Site' and 'Data Sales' services; CSV delivery (FAQ); custom data ranges priced on request
  - 'Claim Your Page' verification (free) and page customisation (bio, links)
- **Per-person derived score or rank, as observed.**
  'Top 10 donors in your state this election cycle' and totals of contributions and expenditures by party (About page); a 'Top Viewed Entities' section appears in the site navigation. No per-person score or report card was observed.
- **Identifiers exposed.**
  - Not stated on the pages read
- **Per-filing conditions it states or computes.**
  - None observed on the pages read
- **Code.**
  No public code repository stated on the pages read.
- **Data licence.**
  No license stated on the pages read. The FAQ says legal uses of the data vary by state and advises consulting an attorney licensed in the relevant state; data delivered via CSV.
- **API.**
  Not verified (the Data Sales page could not be loaded; the FAQ mentions CSV delivery only).
- **Funding or business model, as stated.**
  Stated as a non-profit, non-partisan 501(c)(3) (About page); the site solicits donations ('Chip in $10'); custom data ranges are offered with pricing on request; page customisation is offered to verified entities.
- **How it frames what a listing means.**
  The FAQ states the site displays campaign-finance information that candidates, officeholders and PACs have been required by law to submit to a state agency, and that it cannot change individual transactions unless they have first been changed in the official reports filed or amended with the state agency; it invites error reports and says errors are corrected as quickly as possible.
- **Status at retrieval.**
  unknown (the home page asserts ongoing updates but no dated content was captured on the pages read)
- **Corrected on second reading.**
  - *openness_api.* First read: Not verified (the Data Sales page could not be loaded; the FAQ mentions CSV delivery only). On re-reading: The Data Sales page loads in a browser and states: 'Data can be delivered via CSV file, JSON file, or API access.' with a quote available from editors@transparencyusa.org. So JSON and API delivery are offered (on request, priced), not CSV only. (<https://www.transparencyusa.org/data-sales>)
- **Not verified.**
  - Data Sales page (bot-check interstitial): whether JSON or API delivery and pricing are offered (a search snippet claimed CSV, JSON or API; not verified on the site)
  - Any identifier scheme on entity pages
  - Whether transaction rows link to the state filing
  - Any content dated within the last twelve months
  - Cost of page customisation (the FAQ text was cut before the answer)
  - 'Top Viewed Entities' in the site navigation (not present in the captured page text of the three cited pages)
  - Identifier scheme on entity pages and whether transaction rows link to the state filing (entity pages not opened)
  - Status: the Articles page (browser) shows items dated 02/28/2023 and 02/27/2023 at the top; whether the list is sorted newest-first, and therefore whether any article is newer than February 2023, is not determinable from the page text. The FAQ also says '24 states' and lists 24 (omitting Idaho) while the About page and home page say 25; the entry's 25 follows the About page
- **Confirmed by the second reader.** 6 claims, listed in the JSON.
- **Citations.**
  - <https://www.transparencyusa.org/> (retrieved 2026-09-21): Counters (transactions, states, candidates and committees, tracked spending), statement of constant updating, donation appeal, Midland, Texas address
  - <https://www.transparencyusa.org/about-us> (retrieved 2026-09-21): Mission (quoted), 25 states listed, scope (candidates, PACs, donors, payees, Texas lobbying), cycle organisation, top-10 donor and party totals, raw data from state agencies posted on receipt then cleaned, corrections invitation, 501(c)(3) statement
  - <https://www.transparencyusa.org/faq> (retrieved 2026-09-21): Data types, CSV delivery, legal uses vary by state, removal policy tied to amended official reports, verification and page customisation, federal queries directed to fec.gov

## ProPublica FEC Itemizer and Campaign Finance API

<https://projects.propublica.org/itemizer/>

- **Organisation.**
  ProPublica
- **Kind.**
  Newsroom tool for browsing FEC electronic filings, with an accompanying Campaign Finance API
- **Self-description, as read.**
  The Itemizer page describes itself as a way to browse electronic campaign-finance filings from the Federal Election Commission and see individual contributions and expenditures reported by committees raising money for federal elections; created by Derek Willis and Sisi Wei, with Aaron Bycoffe, and stated to be updated regularly. The API documentation describes an API that retrieves data from FEC filings and other sources, originally created by The New York Times in 2008, providing candidate and committee summaries and itemized data, updated daily with electronic filings ingested every 15 minutes.
- **Subject scope.**
  Federal electronic filings: candidates and committees from 1980 to present; electronic filings from 2001, paper filings from 1999; Senate candidate and party committee reports included as of October 2018; lobbyist bundler data 2012 to present.
- **Sources it says it uses.**
  - Federal Election Commission electronic filings (Itemizer page and API docs); 'other sources' mentioned in the API docs without naming them
  - Whether each row links to the FEC filing image: not stated on the pages read
- **Outputs.**
  - FEC Itemizer web tool
  - ProPublica Campaign Finance API (key issued through the ProPublica Data Store)
- **Per-person derived score or rank, as observed.**
  None observed on the pages read.
- **Identifiers exposed.**
  - Not stated on the pages read (identifier formats are not documented in the API page text captured)
- **Per-filing conditions it states or computes.**
  - None observed on the pages read
- **Code.**
  No public code repository stated on the pages read.
- **Data licence.**
  API documentation states the data is provided under Creative Commons Attribution-NonCommercial-NoDerivs 3.0, with conditions: no republishing raw data as a standalone product, no charging for access without authorisation, citation of ProPublica required, accuracy not guaranteed, users indemnify ProPublica. The Data Store terms state: "We do not guarantee the accuracy or completeness of the data." (projects.propublica.org/datastore/terms) and prohibit republishing raw data in its entirety, altering it except for corrections, charging for access or advertising against it, and sublicensing or reselling; the Itemizer page notes use is subject to ProPublica's Data Terms of Use and the FEC's sale-or-use restrictions.
- **API.**
  API key required, requested through the Data Store; usage limited to 5,000 requests per day, with rate limits stated to be subject to change; no deprecation notice observed.
- **Funding or business model, as stated.**
  not verified (no funding statement on the pages read)
- **How it frames what a listing means.**
  Accuracy and completeness are not guaranteed (Data Store terms, quoted above); no statement about what a listing implies for a filer was observed.
- **Status at retrieval.**
  active (Itemizer page states it is updated regularly and references 2026 filings; API docs state daily updates with no shutdown notice)
- **Not verified.**
  - Identifier formats used by the API (candidate_id, committee_id, filing ids)
  - Whether Itemizer rows link to the FEC filing image
  - Funding for the tool
  - The exact 2026 references on the Itemizer page (reported by the page fetch summary)
  - Identifier formats used by the API (not documented on the page text)
  - Whether 'rate limits are subject to change' is stated verbatim (the 5,000/day cap is confirmed; the change clause was not surfaced)
- **Confirmed by the second reader.** 5 claims, listed in the JSON.
- **Citations.**
  - <https://projects.propublica.org/itemizer/> (retrieved 2026-09-21): Self-description, creators, FEC electronic filings as source, Senate reports as of October 2018, updated regularly, references to 2026 filings, link to the Campaign Finance API, subject to Data Terms of Use and FEC restrictions
  - <https://projects.propublica.org/api-docs/campaign-finance/> (retrieved 2026-09-21): API origin (NYT, 2008), FEC filings and other sources, daily updates and 15-minute electronic filing ingest, API key via Data Store, 5,000 requests per day, CC BY-NC-ND 3.0 terms and conditions, coverage date ranges
  - <https://projects.propublica.org/datastore/terms/> (retrieved 2026-09-21): Data Store terms: no republishing raw data in entirety, no alteration except corrections, no charging or advertising against it, no sublicensing, citation required, accuracy disclaimer (quoted)

## Pages the first reader could not reach

- https://www.opensecrets.org/about/methodology (site error page in the browser; HTTP 403 via fetch)
- https://www.opensecrets.org/about/tos (site error page in the browser)
- https://www.opensecrets.org/about/ via fetch (HTTP 403; read through the browser instead)
- https://www.followthemoney.org/entity-details?eid=210204 (HTTP 403 via fetch; bot-check interstitial in the browser)
- http://classic.maplight.org/us-congress/guide/data, http://classic.maplight.org/data/get/federal-money-and-politics-dataset, http://classic.maplight.org/content/media-fact-sheet (TLS handshake failure via fetch; navigation denied in the browser)
- https://maplight.org/about/ (HTTP 404; /about-us used instead)
- https://maplight.org/how-were-funded (HTTP 403 via fetch; sign-up wall in the browser)
- https://www.transparencyusa.org/ and /about-us and /faq via fetch (HTTP 403; read through the browser instead)
- https://www.transparencyusa.org/about (HTTP 404; /about-us used instead)
- https://www.transparencyusa.org/data-sales (bot-check interstitial in the browser)
- https://api.data.gov/terms/ and https://api.data.gov/docs/ (HTTP 404; the developer manual at /docs/developer-manual/ was used)
- https://api.data.gov/docs/rate-limits/ (fetch returned no page content)

## Projects the second reader said were missing from this cluster

- **Capitol Trades.** <https://www.capitoltrades.com/> Live aggregator of congressional Periodic Transaction Reports (STOCK Act filings) with per-politician trade counts, filings, issuers and volume; home page shows trades dated the day of retrieval and insight posts dated August-September 2026. Named in Oath's own CLAUDE.md as a shoulder the project stands on, yet absent from the cluster. Its 'Why Capitol Trades?' framing (investment research) is a contrast worth recording.
- **Quiver Quantitative.** <https://www.quiverquant.com/> Commercial aggregator whose flagship dataset is 'Congress Trading' built from PTR filings, with a 'Congress Backtester'; belongs beside Capitol Trades as a money-in-politics/PTR aggregator with an investment-product frame.
- **Unusual Whales (Politics).** <https://unusualwhales.com/politics> Page titled 'Track Congressional & Senate Stock Trades'; a third PTR aggregator in the same family; existence confirmed by fetch, content not examined further.
- **LegiStorm.** <https://www.legistorm.com/> Subscription database ('Congress Revealed') offering Financial Disclosures, Privately Funded Travel and staff Salaries products; named in Oath's CLAUDE.md as a comparator; paywalled 'Pro' tiers with free registration. Covers personal financial disclosures, which the cluster otherwise reaches only through OpenSecrets' 2018-capped section.
- **LittleSis (Public Accountability Initiative).** <https://littlesis.org/> Self-described 'free, open-source research platform ... a database of who-knows-who at the heights of business and government'; power-mapping aggregator that links officeholders, donors and organisations, with posts dated September 2026. Whether it ingests campaign-contribution data was not verified from the home page (fetch was blocked by an Anubis bot check; the browser loaded it).
