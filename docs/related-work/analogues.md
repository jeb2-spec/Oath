# Related-work record: International and structural analogues

*Read on 2026-09-21. A first reader wrote each entry from the project's own pages; a second reader, briefed to refute, re-fetched every cited page. Corrections are shown beside the claims they correct and both are kept. Presence in this record is not a claim about a project's quality, and absence is not either. Presence in the register is not evidence of wrongdoing: where a record below describes what a neighbour published about an officeholder, it describes the role and not the person, names no one outside a citation URL, and is not a Finding. Rendered from `data/analogues.json` by `render.py`; edit the JSON, not this file.*

## TheyWorkForYou (with ParlParse)

<https://www.theyworkforyou.com/>

- **Organisation.**
  mySociety (registered charity 1076346 in England and Wales; company 03277032; commercial subsidiary SocietyWorks Ltd)
- **Kind.**
  Parliamentary monitoring site for the UK's parliaments and assemblies: searchable debates, per-member pages, voting summaries, and a presentation of the Register of Members' Financial Interests with edition-by-edition change history; ParlParse is the scraper/parser that produces its structured data.
- **Self-description, as read.**
  Describes itself as making Parliament more accessible and accountable, on the premise that "information about our elected representatives should be easily understandable and accessible to everyone" (theyworkforyou.com/about). Run by mySociety, described there as a UK charity that helps people access information and participate in democracy. Lists its functions as making debates searchable for all the UK's parliaments, providing email alerts, and adding voting record summaries and more accessible registers of members' interests. ParlParse describes itself as structured versions of publicly available data from the UK parliament plus the code that generates them, powering TheyWorkForYou and The Public Whip.
- **Subject scope.**
  MPs (House of Commons), members of the House of Lords, MSPs (Scottish Parliament), MLAs (Northern Ireland Assembly) and Senedd members. Register of Members' Interests editions from May 2001 to 7 September 2026 on the regmem index; raw register XML snapshots from 2000-11-10 to 2026-09-07. Members data in people.json reaches back to the early 19th century for MPs via Hansard, 1999 for Lords, and the founding dates of the devolved bodies.
- **Sources it says it uses.**
  - Hansard (Parliamentary copyright), per the about page
  - data.parliament.uk member data via the ParlParse datadotparl scraper (github.com/mysociety/parlparse)
  - House of Commons Register of Members' Financial Interests, ingested as periodic XML snapshots (regmem[YYYY-MM-DD].xml) published at /pwdata/scrapedxml/regmem/
  - House of Commons Code of Conduct (publications.parliament.uk link on the regmem page) for the rules on what must be registered
  - IPSA expenses records, referenced by a Parliament ID on the MP page
  - Linking: the MP register page links to the member's UK Parliament profile at members.parliament.uk; a per-entry link to the official register edition on parliament.uk was not observed on the pages fetched
- **Outputs.**
  - Per-member pages with a Register of Interests section grouped by category (e.g. Employment and earnings - Ad hoc payments; Visits outside the UK; Miscellaneous), no totals
  - History of a member's register entries by register edition, and comparison of consecutive editions to show what changed
  - Spreadsheet downloads of register data (offered on the member register page)
  - Voting summaries by policy area, with recent votes listed individually
  - Debate search and email alerts
  - JSON/XML API (getPerson, getMPs, constituencies, debates, written answers, ministerial statements)
  - Raw XML via parser.theyworkforyou.com and /pwdata/scrapedxml/ (Hansard, members, register of interests); people.json in Popolo format
- **Per-person derived score or rank, as observed.**
  Voting summaries: a 0-100 score per policy area is mapped to seven phrases (consistently voted for; almost always voted for; generally voted for; voted a mixture of for and against; generally voted against; almost always voted against; consistently voted against), computed from designated scoring votes, with informative votes shown separately. The register-of-interests pages provide no rankings, totals or cross-member summaries (regmem index observation). No leaderboard observed.
- **Identifiers exposed.**
  - TheyWorkForYou person ID, an integer in the member URL (e.g. 10001), which ParlParse records as uk.org.publicwhip/person/<n>
  - Parliament ID (e.g. 172) shown under the Expenses section referencing IPSA records
  - Link to the member's members.parliament.uk profile
  - Wikipedia link (external reference only); Wikidata not shown on the MP page fetched
  - people.json (Popolo format) carries a unique identifier per person with memberships as continuous periods of office; other identifier schemes in that file were not enumerated on the parser page
- **Per-filing conditions it states or computes.**
  - None computed per filing. The register feature is change-tracking: users compare consecutive Register editions to identify changes, and view the history of one person's entries across editions (regmem index and member register page).
  - Voting: votes are classified as scoring votes (affect the summary) or informative votes (shown but not scored); absences are not counted because their significance cannot be reliably determined (voting-information page).
- **Code.**
  TheyWorkForYou: github.com/mysociety/theyworkforyou under a BSD-style licence (repository page). ParlParse: github.com/mysociety/parlparse under the GNU Affero General Public License v3 (LICENSE.txt; copyright Julian Todd, Matthew Somerville, Francis Irving, Mark Longair, UKCOD and others, 2003-2011).
- **Data licence.**
  Per /api/terms: parliamentary material is reusable under the Open Parliament Licence; TheyWorkForYou's own data under Creative Commons Attribution-ShareAlike 2.5; GB postcode/boundary data under the OS OpenData licence; Northern Ireland data under the Open Government Licence and NI End User Licence. Attribution requested with wording such as Data service provided by TheyWorkForYou. The terms state the provider gives no warranty as to ownership of the data.
- **API.**
  API key required (self-service signup). Free tier of 10 calls per day; paid plans from GBP 20 per month; charities free up to 1,000 calls per month or 50% discount above that. Terms at /api/terms. No Register of Members' Interests endpoint is listed on the API page; register data is available as XML snapshots instead.
- **Funding or business model, as stated.**
  The about page states the site is not publicly funded and invites donations as a registered charity (1076346). mySociety's about page describes charitable donations, grants (via impact reporting), and commercial services delivered through SocietyWorks Ltd. The API carries paid plans.
- **How it frames what a listing means.**
  Member register page: representatives in the UK's parliaments need to declare financial interests (employment, donations, gifts) that could be considered by others to influence their judgement or actions (paraphrased). Voting-information page: votes are not opinions but they matter; MPs may vote with party discipline rather than personal belief; whip instructions are not public so comparisons use party averages; absences are not counted; the summaries track political impact rather than ideology (paraphrased). API terms: no warranty as to ownership of the data.
- **Status at retrieval.**
  active: the regmem index lists a register edition dated 7 September 2026 and the raw XML directory shows regmem2026-09-07.xml modified 2026-09-08.
- **Corrected on second reading.**
  - *primary_sources_used (Linking) / could_not_verify.* First read: Only a members.parliament.uk profile link was observed on the member register page; a link to the official register on parliament.uk was not observed. On re-reading: The member register page also links to 'the official House of Commons page' for the Register of Members' Financial Interests at https://www.parliament.uk/mps-lords-and-offices/standards-and-financial-interests/parliamentary-commissioner-for-standards/registers-of-interests/register-of-members-financial-interests/. It is a link to the official register landing page, not to a specific edition or entry; the entry should say that rather than imply no primary-register link exists. (<https://www.theyworkforyou.com/mp/10001/diane_abbott/hackney_north_and_stoke_newington/register>)
- **Not verified.**
  - Whether people.json carries datadotparl_id, pims_id or Wikidata schemes (the parser page did not enumerate them)
  - Whether the member register page links to the specific official register edition on parliament.uk (only a members.parliament.uk profile link was observed)
  - Latest commit dates for the two repositories
  - https://www.theyworkforyou.com/data/ returned 404
  - openness_api: 'No Register of Members' Interests endpoint is listed on the API page' — the /api/ landing page lists example uses and points to /api/docs/ for the full endpoint list, which neither the entry nor this check fetched
  - funding_or_business_model: mySociety about page describing 'grants (via impact reporting)' and commercial services as funding streams — the about page as fetched names SocietyWorks and a Donate button but does not enumerate grants
  - citation for MP page 'voting summary presentation' — the fetched MP page shows a Voting Summary menu entry but the phrases themselves were not in the fetched text
  - organisation: company number — the TWFY about page prints the limited company number as 03277015 while mysociety.org/about prints 03277032; the entry's number matches its cited page, but the two mySociety pages disagree
  - Latest commit dates for both repositories (not displayed in fetched content)
  - Whether people.json carries datadotparl_id, pims_id or Wikidata schemes (members.html enumerates only uk.org.publicwhip/person and peeragetype)
- **Confirmed by the second reader.** 13 claims, listed in the JSON.
- **Citations.**
  - <https://www.theyworkforyou.com/about/> (retrieved 2026-09-21): self-description, mySociety as operator, Hansard source, not publicly funded, charity number 1076346
  - <https://www.theyworkforyou.com/api/> (retrieved 2026-09-21): API key required, plans from GBP 20/month, reduced non-profit rates, endpoints
  - <https://www.theyworkforyou.com/api/terms> (retrieved 2026-09-21): data licences (Open Parliament Licence, CC BY-SA 2.5, OS OpenData, OGL/NI), attribution, free tier, charity terms, no-warranty statement
  - <https://www.theyworkforyou.com/regmem/> (retrieved 2026-09-21): register editions May 2001 to 7 September 2026, edition comparison, Code of Conduct link, no rankings or totals
  - <https://www.theyworkforyou.com/mp/10001/diane_abbott/hackney_north_and_stoke_newington> (retrieved 2026-09-21): person ID 10001, Parliament ID 172 under Expenses/IPSA, register categories, voting summary presentation, Wikipedia link
  - <https://www.theyworkforyou.com/mp/10001/diane_abbott/hackney_north_and_stoke_newington/register> (retrieved 2026-09-21): link to members.parliament.uk profile, history of entries by edition, explanatory text on declaring interests, spreadsheet downloads
  - <https://www.theyworkforyou.com/voting-information/> (retrieved 2026-09-21): 0-100 score and seven phrases, scoring vs informative votes, caveats about party discipline and absences
  - <https://www.theyworkforyou.com/pwdata/scrapedxml/regmem/> (retrieved 2026-09-21): register XML snapshots from regmem2000-11-10.xml to regmem2026-09-07.xml
  - <https://parser.theyworkforyou.com/> (retrieved 2026-09-21): ParlParse self-description, members data and Hansard, powers TheyWorkForYou and Public Whip
  - <https://parser.theyworkforyou.com/members.html> (retrieved 2026-09-21): people.json in Popolo format, uk.org.publicwhip/person/ identifier scheme, historical scope
  - <https://github.com/mysociety/parlparse> (retrieved 2026-09-21): scraper from data.parliament.uk, Popolo posts files for Westminster and devolved bodies
  - <https://raw.githubusercontent.com/mysociety/parlparse/master/LICENSE.txt> (retrieved 2026-09-21): ParlParse licence GNU AGPL v3 and copyright holders
  - <https://github.com/mysociety/theyworkforyou> (retrieved 2026-09-21): TheyWorkForYou code under a BSD-style licence
  - <https://www.mysociety.org/about/> (retrieved 2026-09-21): charity and company numbers, SocietyWorks Ltd, funding streams, flagship projects

## abgeordnetenwatch.de

<https://www.abgeordnetenwatch.de/>

- **Organisation.**
  Parlamentwatch e.V. (non-profit association, donation-financed)
- **Kind.**
  Parliamentary monitoring platform for Germany (Bundestag, state parliaments, EU Parliament) with side-activity and side-income (Nebentaetigkeiten/Nebeneinkuenfte) records per politician, roll-call votes, citizen questions to representatives, a research desk, and an open CC0 API.
- **Self-description, as read.**
  Describes its work under the heading Gemeinsam fuer Transparenz and says it works through citizen participation and transparency for a self-determined, democratic society (about page, paraphrased). Its Nebentaetigkeiten research desk describes itself as investigating side incomes, side activities and potential conflicts of interest of politicians in the Bundestag. The June 2026 overview states that whether members comply with disclosure duties "laesst sich von aussen jedoch schwer ueberpruefen" (abgeordnetenwatch.de, 22 June 2026).
- **Subject scope.**
  Bundestag members for side-activity data (the API entity documentation says sidejob data covers German federal parliament members only); parliaments, parliamentary periods, politicians, candidacies/mandates and named votes across parliaments in the API; research articles also cover state-level candidates (e.g. Berlin, September 2026) and EU members.
- **Sources it says it uses.**
  - Side-activity data published by the Bundestag administration (werden von der Bundestagsverwaltung veroeffentlicht), then processed for the API (api/entitaeten/sidejob)
  - The June 2026 article states its figures come from the disclosures published on the Bundestag website and cites the Abgeordnetengesetz thresholds and deadlines
  - Linking: profile entries carry a recording date and last-modification date and an Open Data link; a per-entry link to the Bundestag's official disclosure page was not observed on the profile fetched
- **Outputs.**
  - Politician profile pages with a sortable Nebentaetigkeiten table (activity, client/organisation, recording date, interval, income) and per-entry details (mandate period, category, topics, location, organisation address)
  - Research articles with a sortable database of all 630 Bundestag members' disclosed side income, faction totals, and interactive maps by constituency
  - API v2 JSON across parliaments, periods, politicians, mandates, sidejobs, sidejob organisations, votes
  - Press releases and campaigns
- **Per-person derived score or rank, as observed.**
  The 22 June 2026 overview lists the members with the highest disclosed side income (three named members, at about EUR 2.7 million, EUR 1.5 million, and EUR 439,000; the names are on the cited page), gives totals (EUR 10.6 million disclosed since the term began; 232 of 630 members with side income; 159 with board positions), and offers a sortable table of all members. Politician API records carry counts statistic_questions and statistic_questions_answered. No composite per-person score observed.
- **Identifiers exposed.**
  - Own numeric IDs for every entity (politicians, mandates, sidejobs, organisations, taxonomy terms)
  - ext_id_bundestagsverwaltung: the Bundestag administration's ID on politician records
  - qid_wikidata: Wikidata QID on politician records
  - abgeordnetenwatch_url and api_url per record
- **Per-filing conditions it states or computes.**
  - No automated per-filing condition observed. The June 2026 article states the legal conditions it reads the data against: a three-month deadline to report side activities; publication threshold of EUR 1,000 per month or EUR 3,000 per year; a 5% threshold for company holdings; fines of up to EUR 70,000 imposable by the Bundestag President.
  - Sidejob records carry income (exact), income_level (11 brackets, 0 = EUR 1-1,000 up to 10 = over EUR 250,000), interval (one-time, monthly, annual), income_total at reference dates, and data_change_date.
  - Missing or late disclosures are reported case by case in research articles (e.g. the 18 February 2026 article on an EU member's undisclosed trip funding), not computed as a flag.
- **Code.**
  not verified: no official code repository was found on the pages fetched. Third-party API clients exist on GitHub (a CLI under AGPL-3.0-or-later, an MCP server, an R wrapper), none maintained by Parlamentwatch e.V. as far as the pages show.
- **Data licence.**
  CC0 1.0 (API page: Die Daten stellen wir unter der CC0 1.0-Lizenz zur Verfuegung; also in every API response meta block).
- **API.**
  REST JSON at /api/v2/ (meta reports version 2.9.0). No API key mentioned. Fair-use limit of 30 requests per minute per IP; bulk queries requested outside 22:00-06:00 with pauses; HTTP 429 when exceeded.
- **Funding or business model, as stated.**
  Parlamentwatch e.V., described on its funding page as a donation-financed non-profit; over 12,500 regular supporters as of December 2025; seed funding of EUR 85,000 from OLIN gGmbH in 2013-2016 to build fundraising capacity; member of the Initiative Transparente Zivilgesellschaft; 2024 annual report available as PDF.
- **How it frames what a listing means.**
  The June 2026 overview states that the figures are what members themselves disclose and that compliance with disclosure duties is hard to verify from outside. The profile page's Nebentaetigkeiten section carries no explanatory or disclaimer text of its own.
- **Status at retrieval.**
  active: research index shows articles dated 18 September 2026 and 4 September 2026; a profile entry shows a modification date of 10.09.2026.
- **Not verified.**
  - An official code repository for the platform
  - Whether each profile entry links to the Bundestag's official disclosure page
  - Any API terms of use beyond the fair-use rate limit
  - https://www.abgeordnetenwatch.de/ueber-uns/finanzierung returned 404 (the funding page was found at /ueber-uns/mehr/finanzierung)
  - openness_code: no official repository found — a web search surfaced only third-party clients (maschinenlesbar-org/abgeordnetenwatch-cli, Movm/abgeordnetenwatch-mcp, untergeekDE/abgeoRdnetenwatchr), consistent with the entry but not proof of absence
  - funding_or_business_model: the phrase 'donation-financed non-profit' is a paraphrase; the funding page's own wording is that project costs are to be financed through building up Förderungen (regular supporters)
  - Any API terms of use beyond the fair-use section
- **Confirmed by the second reader.** 12 claims, listed in the JSON.
- **Citations.**
  - <https://www.abgeordnetenwatch.de/api> (retrieved 2026-09-21): API v2, CC0 1.0 licence, 30 requests/minute fair use, HTTP 429
  - <https://www.abgeordnetenwatch.de/api/v2/sidejobs?range_end=2> (retrieved 2026-09-21): sidejob fields (income, income_level, interval, income_total, data_change_date, mandates, organisation), meta licence CC0, API version 2.9.0
  - <https://www.abgeordnetenwatch.de/api/v2/politicians?range_end=1> (retrieved 2026-09-21): politician fields including ext_id_bundestagsverwaltung and qid_wikidata, statistic_questions counts
  - <https://www.abgeordnetenwatch.de/api/entitaeten/sidejob> (retrieved 2026-09-21): source is the Bundestag administration, 11 income brackets, intervals, eight categories, federal scope
  - <https://www.abgeordnetenwatch.de/ueber-uns> (retrieved 2026-09-21): self-description, Parlamentwatch e.V., side-income focus, 2024 annual report reference
  - <https://www.abgeordnetenwatch.de/ueber-uns/mehr/finanzierung> (retrieved 2026-09-21): donation financing, 12,500+ regular supporters (Dec 2025), OLIN gGmbH seed funding, Initiative Transparente Zivilgesellschaft
  - <https://www.abgeordnetenwatch.de/recherchen/nebentaetigkeiten> (retrieved 2026-09-21): research desk description and article dates through 18 September 2026
  - <https://www.abgeordnetenwatch.de/recherchen/nebentaetigkeiten/diese-nebeneinkuenfte-haben-die-abgeordneten-im-bundestag> (retrieved 2026-09-21): 22 June 2026 date, Bundestag-published source, legal thresholds and deadline, top earners and totals, caveat quote
  - <https://www.abgeordnetenwatch.de/profile/friedrich-merz> (retrieved 2026-09-21): profile table fields, per-entry details, Open Data link, no disclaimer text, modification date 10.09.2026

## OpenSanctions (Politically Exposed Persons dataset)

<https://www.opensanctions.org/datasets/peps/>

- **Organisation.**
  OpenSanctions Datenbanken GmbH (Berlin, staff across Europe)
- **Kind.**
  Commercially licensed open-data provider aggregating sanctions lists, politically exposed persons and other public-interest entities into one FollowTheMoney-model dataset; the PEP dataset covers current and former holders of public office worldwide, including a daily-updated US Members of Congress dataset read from the Congress.gov API.
- **Self-description, as read.**
  Describes itself as "a financial crime data provider" (opensanctions.org/docs/about) that builds an international database of persons and companies of political, criminal or economic interest by aggregating sanctions lists, lists of politically exposed persons and other public-interest information from hundreds of sources into a single, structured, continuously updated dataset (paraphrased). The PEP dataset page describes office-holders drawn both directly from official sources such as governments and from third-party aggregations.
- **Subject scope.**
  People who currently hold or previously held positions classified by role (gov.head, gov.executive, gov.legislative, gov.judicial, gov.security, gov.financial, role.diplo, gov.soe, pol.party, gov.religious) and jurisdiction (gov.national, gov.igo, gov.state, gov.muni). Retention after leaving office: 50 years for national heads of state or government, 20 years for other national-level positions and IGO/diplomatic positions, 5 years for all others; excluded are people deceased more than 5 years, likely over 110, or lacking birth/death/position dates. PEP dataset: about 1.95 million entities, 932,463 searchable, 713,334 distinct targets. US Members of Congress dataset: 1,340 persons, current and recent members.
- **Sources it says it uses.**
  - PEP dataset built from 202 sources, including Wikidata (182,256 persons in relevant categories; 366,561 PEP records), the mySociety EveryPolitician archive (40,262), national parliamentary sources (UK Commons 1,687; US Congress 1,342; EU Parliament 2,714) and regional sources (Spanish mayors and councillors 94,373)
  - US Members of Congress dataset reads the Congress.gov API at api.congress.gov/v3/member/ (JSON), published by the Library of Congress, updated daily
  - Linking: entity pages list the datasets an entity appears in and each dataset page cites its source URL; a per-row link to the underlying official page was not observed on the entity pages fetched
- **Outputs.**
  - Entity pages with positions, occupancies, topics, family relationships and dataset provenance
  - Bulk downloads of datasets in multiple formats, daily, with version stamps
  - Matching, search and entities APIs; yente open-source API server with a client SDK, CLI and MCP server; on-premise option
  - Dataset pages with entity counts, source description, licence line and last-updated timestamp
- **Per-person derived score or rank, as observed.**
  None per person observed. Entities carry topic tags (e.g. role.pep, poi, sanction, counter-sanctioned); a position carries one role topic and one jurisdiction topic, and where a position spans several the one representing the greatest level of influence is used (methodology page). No score, rank or leaderboard seen.
- **Identifiers exposed.**
  - Wikidata Q-IDs used directly as entity IDs for people with a Wikidata match (e.g. Q22686, Q170581), with the Wikidata ID shown as a property
  - Source-prefixed IDs derived from publisher-supplied stable keys (e.g. us-congress-6058a31e..., ofac-81717, eu-fsf-1234)
  - EveryPolitician UUIDs carried as evpo-<uuid> referents (e.g. evpo-5cf6d53c-962d-453c-833e-bcaad613c34c on the Q170581 page)
  - NK- cluster IDs assigned at deduplication for merged profiles without a Wikidata equivalent
  - A referents array per entity acting as a forwarding table of retired IDs, kept for 6 months after a merge
  - Bioguide ID on US Congress records: not verified (not stated on the dataset page)
- **Per-filing conditions it states or computes.**
  - None per filing. The PEP condition is structural: a Person is tagged role.pep once linked by an Occupancy to a qualifying Position (methodology page).
  - The retention windows are described by the project as its own judgment rather than a regulatory requirement, with occupancy end dates recorded so users can apply a different policy.
- **Code.**
  Data pipeline open source at github.com/opensanctions/opensanctions under the MIT License; yente API server and client also open source (API docs).
- **Data licence.**
  Creative Commons Attribution-NonCommercial 4.0 (CC BY-NC 4.0); commercial use requires a data licence; some files under datasets/ are unmodified third-party materials with their own terms (repository COPYRIGHT.md).
- **API.**
  API key required for all requests. Free trial keys for business email addresses; free access for journalism, civil-society advocacy and academic research. Pay-as-you-go metering per logical query (matching, reconciliation) or per request (search); volume discounts from 20,000 monthly requests; no contract lock-in; on-premise deployment via yente.
- **Funding or business model, as stated.**
  Commercial data licences to compliance platforms, fintechs, investigation tools, government agencies and research institutions; three licence types (Screening API pay-as-you-go with 30-day trial; Screening License flat rate for in-house use; Reseller/OEM). A 2021 grant from Germany's Federal Ministry for Education and Research (BMBF) funded a rebuild. The about page states the company has operated on revenue since incorporation with no outside investors.
- **How it frames what a listing means.**
  PEP documentation: being classified as a PEP is not an allegation; it is a risk category arising from the nature of senior public office; for financial institutions it means additional questions at onboarding or review, not refusal of service; the project publishes data about public offices and the people who hold them and does not make decisions about individual customers (paraphrased from opensanctions.org/docs/pep/). Entity pages note that counter-sanctions are designations imposed by countries with weak democratic institutions (paraphrased).
- **Status at retrieval.**
  active: PEP dataset last updated 21 September 2026 with daily frequency; US Members of Congress dataset version 20260921084401 with a change on 19 September 2026.
- **Not verified.**
  - Whether Bioguide IDs are carried on US Congress records
  - API rate limits
  - A correction or removal policy (the FAQ page fetched was a navigation hub)
  - The full source list on the methodology page (the fetched excerpt named only Wikidata and official declarations)
  - organisation: 'staff across Europe' — not in the fetched about page text
  - Whether Bioguide IDs are carried on US Congress records (dataset page does not mention them)
  - API rate limits (not stated on docs/api)
  - A correction or removal policy
  - Note: the about page states the GmbH was established in 2023, a detail the entry omits; the methodology's exclusion list also includes positions with no recorded end more than 40 years after start, which the entry's exclusion list does not mention
- **Confirmed by the second reader.** 13 claims, listed in the JSON.
- **Citations.**
  - <https://www.opensanctions.org/docs/about/> (retrieved 2026-09-21): self-description quote, company name and location, funding model, BMBF grant, no outside investors, code repository
  - <https://www.opensanctions.org/docs/pep/methodology/> (retrieved 2026-09-21): PEP definition, Position/Occupancy/Person model, role and jurisdiction topics, retention windows, exclusions, judgment-not-regulation statement
  - <https://www.opensanctions.org/docs/pep/> (retrieved 2026-09-21): PEP status is not an allegation, intended use, project's stated role
  - <https://www.opensanctions.org/datasets/peps/> (retrieved 2026-09-21): entity counts, 202 sources with named examples and counts, CC BY-NC 4.0 line, last updated 21 September 2026, inclusion statement
  - <https://www.opensanctions.org/datasets/us_congress/> (retrieved 2026-09-21): Congress.gov API source, daily updates, entity counts, version and change dates
  - <https://www.opensanctions.org/licensing/> (retrieved 2026-09-21): CC BY-NC 4.0, three commercial licence types, company name
  - <https://www.opensanctions.org/docs/api/> (retrieved 2026-09-21): API key requirement, free access for journalism/civil society/academia, metering, volume discounts, yente client and on-premise
  - <https://www.opensanctions.org/docs/identifiers/> (retrieved 2026-09-21): Wikidata Q-IDs, source-prefixed IDs, NK- cluster IDs, referents forwarding table, 6-month retention of stale referents
  - <https://www.opensanctions.org/docs/entities/> (retrieved 2026-09-21): FollowTheMoney entity structure (id, schema, properties)
  - <https://www.opensanctions.org/entities/Q22686/> (retrieved 2026-09-21): Wikidata ID as entity ID, topics, positions, counter-sanctions note
  - <https://www.opensanctions.org/entities/Q170581/> (retrieved 2026-09-21): us-congress- and evpo- referent IDs, datasets an entity appears in, positions
  - <https://github.com/opensanctions/opensanctions> (retrieved 2026-09-21): MIT code licence, CC BY-NC 4.0 data, third-party files under own terms

## LittleSis

<https://littlesis.org/>

- **Organisation.**
  Public Accountability Initiative (PAI), a 501(c)(3) founded in early 2008; the site says PAI is known more broadly as LittleSis
- **Kind.**
  Volunteer-edited relationship database of people and organisations in business and government (entities, typed relationships, lists, network maps) with a keyless JSON API and bulk data; described by its maintainers as power research.
- **Self-description, as read.**
  The repository README calls it "a free database of who-knows-who at the heights of business and government" (github.com/public-accountability/littlesis-rails). The site says it brings transparency to influential social networks by tracking the key relationships of politicians, business leaders, lobbyists, financiers and their institutions; that the information is public but scattered and it brings it together; and that it is meant to support journalists, watchdogs and grassroots activists. PAI describes its work as power research that informs movement strategies, builds coalitions and supports campaigns that challenge power structures (paraphrased).
- **Subject scope.**
  US-focused. Roughly 400,000 people and organisations and over 1.6 million connections (repository README). Entity types include Person, Organization, Business Person, Public Company, Political Candidate, Elected Representative, Political Fundraising Committee, Lobbyist and others (API docs and search response). Subjects are selected by the mission to track people and groups with inordinate wealth, influence on public policy and access to government officials (disclaimer page).
- **Sources it says it uses.**
  - The database page states data derives from government filings, news articles and other reputable sources; some datasets are updated automatically by bots and the rest by the user community
  - Identifier fields on records point to FEC (candidate and committee IDs), OpenSecrets (crp_id), the Congressional Bioguide, GovTrack and Vote Smart; relationship records carry a filings count and amounts (e.g. a Campaign Contribution relationship with amount 500, filings 1)
  - Linking: whether each relationship links to the underlying filing URL was not observed in the API responses fetched (a filings count is present)
- **Outputs.**
  - Entity profiles (people and organisations) with aliases, types, summary, tags
  - Relationship records in 12 categories with amounts, dates, is_current flag
  - Lists (some flagged is_ranked, e.g. Fortune 1000 Companies 2008), maps, and a blog (Eyes on the Ties)
  - JSON API v2.0 and bulk data; trainings and workshops on power research
- **Per-person derived score or rank, as observed.**
  Search results are ordered by the number of relationships an entity has (API docs give the example that a search for Bush places George Bush before Jeb Bush for that reason); connections are sorted by the connected entity's link_count; lists carry an is_ranked flag. No per-person score observed.
- **Identifiers exposed.**
  - Own numeric entity and relationship IDs
  - qid (Wikidata QID) field on every entity (null in the records fetched)
  - ElectedRepresentative extension: bioguide_id (e.g. P000197), govtrack_id (400314), crp_id (OpenSecrets, N00007360), pvs_id (Vote Smart, 26732), watchdog_id
  - PoliticalCandidate extension: house_fec_id (H8CA05035), senate_fec_id, pres_fec_id, crp_id, is_federal/is_state/is_local
  - PoliticalFundraising extension: fec_id (e.g. C00213512); Org extension: fedspending_id, lda_registrant_id
- **Per-filing conditions it states or computes.**
  - None observed; the data model records typed relationships with amounts and dates, not per-filing conditions.
- **Code.**
  github.com/public-accountability/littlesis-rails under GPL-3.0 (repository page); the about page says the software is open source.
- **Data licence.**
  CC BY-SA 4.0 (API response meta: LittleSis CC BY-SA 4.0 with licence link; disclaimer page: no agreement beyond the Creative Commons Attribution-ShareAlike 4.0 International License).
- **API.**
  No API keys or authentication; requests may be rate-limited (HTTP 503 on limit). Endpoints: /api/entities/:id, /api/entities?ids=, /extensions, /relationships, /connections, /lists, /api/entities/search?q=, /api/relationships/:id; up to 300 entities per batch request; a bulk data page is offered.
- **Funding or business model, as stated.**
  not verified: no funding statement was found on the pages fetched; the organisation identifies itself as a 501(c)(3).
- **How it frames what a listing means.**
  Disclaimer page: an open-content collaborative project with no formal peer review; the team cannot guarantee the validity of the information; no implied warranty; staff make editorial decisions; analysts must contribute information that is relevant to the mission, accurate and documented by publicly available original sources; a review form exists to request review of particular pages (paraphrased).
- **Status at retrieval.**
  active: entity records in the API carry updated_at timestamps of 2026-08-06 and 2026-07-24.
- **Not verified.**
  - Funding sources of PAI
  - Whether each relationship links to the underlying filing URL
  - Terms on the bulk data page
  - Latest commit date of the repository
  - littlesis.org pages were blocked to WebFetch by the Anubis bot check and were read through the browser instead
  - subject_scope: 'Lobbyist' as an entity type — not observed on the API docs page or in the search response fetched
  - Funding sources of PAI (no statement on any page fetched; consistent with the entry)
  - Whether each relationship links to the underlying filing URL (only a filings count is in the API example)
  - Terms on the bulk data page; latest commit date
- **Confirmed by the second reader.** 12 claims, listed in the JSON.
- **Citations.**
  - <https://littlesis.org/about> (retrieved 2026-09-21): PAI self-description, power research framing, open-source statement, trainings (read via browser; WebFetch was blocked by the site's bot check)
  - <https://littlesis.org/database/about> (retrieved 2026-09-21): database self-description, sources (government filings, news articles), bots plus community, 501(c)(3), founded 2008, public API and bulk data
  - <https://littlesis.org/api> (retrieved 2026-09-21): no keys, rate limiting, endpoints, CC BY-SA 4.0 meta, search ranking by relationship count, relationship fields and filings count
  - <https://littlesis.org/disclaimer> (retrieved 2026-09-21): no formal peer review, validity not guaranteed, analyst agreement, review form, CC BY-SA 4.0
  - <https://littlesis.org/api/entities/search?q=Nancy%20Pelosi> (retrieved 2026-09-21): identifier fields (qid, bioguide_id, govtrack_id, crp_id, pvs_id, watchdog_id, house_fec_id, fec_id, fedspending_id, lda_registrant_id), updated_at dates in 2026
  - <https://github.com/public-accountability/littlesis-rails> (retrieved 2026-09-21): who-knows-who quote, GPL-3.0, entity and connection counts, stack, project history

## OCCRP Aleph

<https://aleph.occrp.org/>

- **Organisation.**
  Organized Crime and Corruption Reporting Project (OCCRP), operating through the legal entity Journalism Development Network (JDN); US 501(c)(3), EIN 26-0898750; Dutch ANBI status
- **Kind.**
  Investigative data platform for searching documents and structured data, cross-referencing names against datasets, and building network diagrams and timelines; a hosted public instance for journalists and researchers, an open-source codebase (alephdata/aleph) now in maintenance mode, and a successor hosted product, Aleph Pro.
- **Self-description, as read.**
  The documentation describes Aleph as a data platform created and maintained by OCCRP, "built to help investigative journalists track people and companies" (docs.aleph.occrp.org), usually as part of corruption investigations. It lists finding patterns in large datasets, securely storing documents, making scanned files searchable, mapping entity connections, cross-referencing names against many sources, and building chronologies. OCCRP describes itself as a nonprofit newsroom that exposes crime and corruption so the public can hold power to account (paraphrased).
- **Subject scope.**
  Datasets and investigations across categories that the user documentation names as company registries, leaks, sanctions lists, licenses and concessions, court archives and persons of interest, each tagged by country, update frequency and access restrictions; entities cover persons, companies, assets, vessels, contracts and events. What the public instance holds specifically on officeholders (PEP lists, declarations) could not be verified from outside.
- **Sources it says it uses.**
  - not verified for specific government sources: the documentation describes dataset categories (sanctions lists, company registries, court archives, persons of interest) and one named example (UK People with significant control) but the dataset listing on aleph.occrp.org was not retrievable (the /pages/about route rendered blank and the collections API returned HTTP 401)
  - Linking of rows to primary filings: not verified
- **Outputs.**
  - Search across datasets with filters by category and country; dataset overview pages with counts by entity type
  - Investigations (workspaces) with uploads, entity editing, network diagrams, timelines and cross-referencing against datasets the user can access
  - Entity pages built on the FollowTheMoney model
  - Export for account holders; an API (unauthenticated collection listing returned 401 at retrieval)
- **Per-person derived score or rank, as observed.**
  None observed.
- **Identifiers exposed.**
  - FollowTheMoney entities carry identification-number properties (key-terms page); specific external schemes (Bioguide, FEC, Wikidata) not verified on the pages fetched
- **Per-filing conditions it states or computes.**
  - None observed.
- **Code.**
  github.com/alephdata/aleph under the MIT License. The repository README states the project is sunsetting, in maintenance mode with official support ending 31 December 2025, with the team's focus moved to Aleph Pro, described as a rewrite.
- **Data licence.**
  not verified: no data licence page was found; datasets carry their own access restrictions per the documentation.
- **API.**
  An API exists (developer documentation is linked from docs.aleph.occrp.org). An unauthenticated request to https://aleph.occrp.org/api/2/collections returned HTTP 401 at retrieval. Aleph Pro FAQ access tiers: nonprofit journalism organisations free with 1 TB storage and unlimited users; public-interest groups (civic tech, civil society) at cost; commercial tiers launching in 2026; public browsing of aleph.occrp.org stated to continue.
- **Funding or business model, as stated.**
  OCCRP lists institutional donors including government agencies (Dutch Ministry of Foreign Affairs, US Department of State, UK Foreign Office, the Swedish development agency, New Zealand's foreign ministry), foundations (MacArthur, Open Society Foundations, Skoll, Schmidt Family), the Dutch Postcode Lottery, GroundTruth Project, Founders Pledge and the Institute for Nonprofit News, plus hundreds of individual donors; a founding grant from the UN Democracy Fund. Aleph Pro: free for nonprofit journalism, at cost for public-interest groups, paid tiers for commercial users.
- **How it frames what a listing means.**
  not verified: no statement about what presence in a dataset means was found on the pages fetched; the key-terms page describes datasets and entities without such a frame.
- **Status at retrieval.**
  active: the Aleph Pro FAQ (dated 6 June 2025, updated 11 December 2025) states the public instance remains accessible and migrated to Aleph Pro infrastructure on 15 December 2025; the open-source repository README states official support for the open-source codebase ended 31 December 2025 (maintenance mode).
- **Not verified.**
  - What aleph.occrp.org holds on officeholders (PEP lists, declarations); the dataset listing was not retrievable
  - Data licence for datasets on the public instance
  - Whether an account is required to search public datasets
  - The user-guide page fetched (docs.aleph.occrp.org/users/) contained only navigation
  - https://aleph.occrp.org/pages/about rendered blank; https://www.occrp.org/en/who-we-are and /en/support-us returned 404
  - What aleph.occrp.org holds on officeholders (dataset listing not retrievable without authentication)
  - disclaimer_or_frame: absence of a presence-meaning statement is consistent with the key-terms page fetched, but a broader statement may exist on pages not reachable here
  - Latest commit date of alephdata/aleph
- **Confirmed by the second reader.** 9 claims, listed in the JSON.
- **Citations.**
  - <https://docs.aleph.occrp.org/> (retrieved 2026-09-21): self-description quote, OCCRP as creator and maintainer, capabilities
  - <https://docs.aleph.occrp.org/users/search/datasets/> (retrieved 2026-09-21): dataset organisation, categories (company registries, leaks, sanctions lists, licenses and concessions), access restrictions vary
  - <https://docs.aleph.occrp.org/users/getting-started/key-terms/> (retrieved 2026-09-21): definitions of dataset, investigation, entity; identification-number properties; example dataset; persons-of-interest category
  - <https://github.com/alephdata/aleph> (retrieved 2026-09-21): MIT licence, description, sunsetting notice with support ending 31 December 2025, Aleph Pro rewrite
  - <https://www.occrp.org/en/announcement/aleph-pro-frequently-asked-questions-on-the-future-of-occrps-investigative-data-platform> (retrieved 2026-09-21): dates, Aleph Pro description, public instance continuity and 15 December 2025 migration, access tiers
  - <https://www.occrp.org/en/about-us> (retrieved 2026-09-21): OCCRP self-description, JDN legal entity, ANBI status, founding and UNDEF grant
  - <https://www.occrp.org/en/about-us/who-supports-our-work> (retrieved 2026-09-21): donor categories and named donors, 501(c)(3) and EIN, disclosure policy reference
  - <https://aleph.occrp.org/api/2/collections?limit=10&q=sanctions> (retrieved 2026-09-21): unauthenticated collections request returned HTTP 401

## EveryPolitician

<https://everypolitician.org/>

- **Organisation.**
  Originally mySociety (project on hold from 26 June 2019); everypolitician.org relaunched in February 2026 as a project of OpenSanctions Datenbanken GmbH
- **Kind.**
  Global database of political office-holders (persons, positions, occupancies) built on Wikidata plus crawlers of official sources; originally a per-legislature dataset in Popolo JSON and CSV compiled from parliament websites by scrapers.
- **Self-description, as read.**
  The current site calls itself "a global database of political office-holders, from rulers, law-makers to judges and more" (everypolitician.org) and says it aims to let citizens identify who holds which positions and powers; it describes itself as built on Wikidata, built by volunteers worldwide, and revived and reimagined as part of OpenSanctions after being placed on hold in 2019. mySociety's 2019 post described the original as over five years of work compiling data on 78,382 politicians from 233 countries and territories, with the data frozen but still available for download and reuse (paraphrased).
- **Subject scope.**
  Current site: 702,610 politicians in 211,185 positions across 263 countries and territories (home page); the February 2026 announcement gave nearly 690,000 office-holders across 261 countries and territories and defines politicians as anyone holding public authority, from presidents and legislators to judges, senior officials and military commanders. Original: members of national legislatures, 233 countries and territories, data current to 21 May 2019 (OpenSanctions archive dataset page).
- **Sources it says it uses.**
  - Current: Wikidata via the WikiProject every politician (people) and the Govdirectory WikiProject (positions); automated crawlers of official government sources; PoliLoom, which uses large language models to extract politician data from Wikipedia articles for human review before submission to Wikidata
  - Original: parliament websites read by the everypolitician-scrapers fleet (mySociety post)
  - Linking: per-row links to the official source were not verified
- **Outputs.**
  - Current: profiles by country and position on everypolitician.org; bulk download via the OpenSanctions Politically Exposed Persons collection; a free API for journalists and public-interest users; commercial licensing via OpenSanctions; PoliLoom contribution tool; source code on GitHub
  - Original: Popolo JSON and CSV per legislature via countries.json (frozen), preserved by OpenSanctions as the everypolitician archive dataset (92,315 entities)
- **Per-person derived score or rank, as observed.**
  None observed.
- **Identifiers exposed.**
  - Current: Wikidata QIDs for entities (about page)
  - Original: per-person UUIDs, visible in OpenSanctions as evpo-<uuid> referents (e.g. evpo-5cf6d53c-962d-453c-833e-bcaad613c34c on the Q170581 page), cross-referenced to Wikidata (Q208879 example on the archive dataset page)
  - Other schemes in the original Popolo identifiers array: not verified (docs.everypolitician.org did not resolve)
- **Per-filing conditions it states or computes.**
  - None observed.
- **Code.**
  Current site: github.com/opensanctions/everypolitician.org under the MIT license. Original: github.com/everypolitician (everypolitician-data, everypolitician-scrapers); licence not stated on the repository page fetched.
- **Data licence.**
  Current: Creative Commons Attribution-NonCommercial 4.0, with commercial screening products offered separately through OpenSanctions. Original data licence: not verified (mySociety's post says the frozen data remains available for download and reuse).
- **API.**
  Current: through the OpenSanctions API, free for journalists and public-interest users, commercial licensing otherwise (February 2026 announcement). Original: no API verified; data was offered as downloads.
- **Funding or business model, as stated.**
  Current: part of OpenSanctions' commercial data-licensing model (the about page points commercial screening and due-diligence use to OpenSanctions). Original: mySociety's post attributes the pause to the maintenance burden of near-weekly elections worldwide and constant scraper upkeep; the funding basis of the original is not verified on the pages fetched.
- **How it frames what a listing means.**
  Current about page states no explicit inclusion criteria beyond its crowdsourced, Wikipedia-inspired method; positions are classified under the OpenSanctions PEP methodology, whose documentation states PEP status is not an allegation. Original repository README and mySociety post carry the on-hold notice.
- **Status at retrieval.**
  Original mySociety project: on hold since 26 June 2019 per mySociety's announcement and the everypolitician-data README; OpenSanctions' archive dataset page states mySociety ceased updates. Current everypolitician.org: active and merged into OpenSanctions per its about page (revived as part of OpenSanctions) and the 18 February 2026 relaunch article; PoliLoom article dated 24 March 2026; home page counts retrieved today.
- **Not verified.**
  - The original data licence and the identifier schemes in the original Popolo files (docs.everypolitician.org did not resolve)
  - The licence of the everypolitician-data repository
  - The current site's methodology page (https://everypolitician.org/methodology/ returned 404)
  - The funding basis of the original mySociety project
  - self_description / primary_sources_used attributed to the about page: 'built by volunteers worldwide', 'automated crawlers of official government sources' and 'Wikidata QIDs for entities (about page)' — two fetches of everypolitician.org/about did not surface these statements; the crawler and Wikidata-first claims are supported by the 18 Feb 2026 article and the GitHub README instead, and QIDs are evidenced only via OpenSanctions entity pages. Re-cite to those sources or drop the about-page attribution.
  - Original data licence and Popolo identifier schemes (docs.everypolitician.org did not resolve for the entry; not re-tested here)
  - Current methodology page (header link exists; the entry reports 404)
  - Funding basis of the original mySociety project
- **Confirmed by the second reader.** 9 claims, listed in the JSON.
- **Citations.**
  - <https://everypolitician.org/> (retrieved 2026-09-21): self-description quote, built on Wikidata, maintained by OpenSanctions, counts (702,610 politicians; 263 countries), CC BY-NC 4.0, header and footer links
  - <https://everypolitician.org/about/> (retrieved 2026-09-21): mySociety origin, 2019 hold, revival as part of OpenSanctions, Wikidata WikiProjects, PoliLoom, Wikidata QIDs, licence, commercial use via OpenSanctions
  - <https://www.mysociety.org/2019/06/26/placing-everypolitician-on-hold/> (retrieved 2026-09-21): 26 June 2019 pause, 78,382 politicians and 233 countries, reasons, data frozen but downloadable, code on GitHub, Wikidata migration
  - <https://github.com/everypolitician/everypolitician-data> (retrieved 2026-09-21): repository description, on-hold notice, countries.json
  - <https://github.com/opensanctions/everypolitician.org> (retrieved 2026-09-21): MIT licence, 261 countries, Wikidata plus government sources, integration with the OpenSanctions PEP dataset
  - <https://www.opensanctions.org/articles/2026-02-18-every-politician/> (retrieved 2026-09-21): 18 February 2026 relaunch, new home for the project, counts, crawler plus Wikidata method, free API for journalists, commercial licensing
  - <https://www.opensanctions.org/articles/2026-03-24-poliloom/> (retrieved 2026-09-21): PoliLoom LLM extraction, human verification, submission to Wikidata and EveryPolitician, 24 March 2026
  - <https://www.opensanctions.org/datasets/everypolitician/> (retrieved 2026-09-21): archive of the mySociety data, coverage to 21 May 2019, entity counts, Wikidata identifiers, kept for historical PEP documentation
  - <https://www.opensanctions.org/entities/Q170581/> (retrieved 2026-09-21): evpo-<uuid> identifier carried as a referent

## Transparency International (asset and interest declaration work)

<https://www.transparency.org/>

- **Organisation.**
  Transparency International e.V., international secretariat in Berlin, with national chapters in more than 100 countries
- **Kind.**
  Advocacy and research organisation. On officeholder asset declarations it publishes policy papers, helpdesk answers and topic guides through its Knowledge Hub, and reports on chapter-level monitoring; no central dataset of officeholder declarations was found on transparency.org. (Its EU office's Integrity Watch platform is a separate entry.)
- **Self-description, as read.**
  Describes itself as working to stop corruption and promote transparency, accountability and integrity at all levels and across all sectors of society, with a vision of government, politics, business, civil society and daily life free of corruption (paraphrased from the-organisation page). On declarations, its 2013 piece frames an asset declaration as a person's balance sheet covering assets, liabilities and all sources of income, and its 2020 OGP paper proposes that the Open Government Partnership could incubate "a future open data standard for asset declarations" (2020 policy paper PDF).
- **Subject scope.**
  Income, interest and asset declaration systems for public officials generally, across countries; recommendations aimed at Open Government Partnership member governments; chapter monitoring of politicians' declarations in Georgia and Russia (2013 article); national examples such as Ukraine's digital declarations of roughly one million public servants and Georgia's electronic monitoring system (2020 paper).
- **Sources it says it uses.**
  - None as a data publisher on this topic. The 2020 paper cites national declaration systems (Ukraine's online portal; Georgia's electronic monitoring) and a civil-society analyst (BIRN in Albania) as examples
  - The 2013 article reports that TI chapters in Russia and Georgia study politicians' declarations over time, and that in Georgia declaration figures are cross-referenced with the public company registry
  - Linking to primary filings: not applicable on the pages fetched
- **Outputs.**
  - Policy paper: Recommendations on Asset and Interest Declarations for OGP Action Plans (5 November 2020; 11-page PDF; authors Lucas Amin and Jose Maria Marin)
  - Knowledge Hub items tagged asset-declarations: Improving and Enforcing Income, Interest and Asset Declaration Systems (4 June 2024); Topic Guide on Income and Asset Disclosure (12 June 2015); Topic Guide on Public Sector Integrity (2015); Albania overview (2014); Foreign Exchange Controls and Assets Declarations (2011)
  - News piece: Holding politicians to account: asset declarations (17 January 2013)
  - Annual report and news items (September 2026)
- **Per-person derived score or rank, as observed.**
  None per person observed on the pages fetched.
- **Identifiers exposed.**
  - None; not a publisher of officeholder records on the pages fetched
- **Per-filing conditions it states or computes.**
  - None computed. Principles stated in the 2013 article: declarations from the leadership of all three branches, filed at the start of office, updated annually and continued through a cooling-off period; exact values or value ranges; a monitoring agency to collect, verify, investigate, prosecute and sanction. The 2020 paper describes digital collection with structured forms as enabling algorithmic verification and risk-assessment tools (paraphrased).
- **Code.**
  None.
- **Data licence.**
  not applicable: publications only; no data licence observed.
- **API.**
  None.
- **Funding or business model, as stated.**
  The organisation page states support from a range of donors including government agencies, multilateral institutions, foundations, the private sector and individuals, unrestricted or earmarked, under a policy of accepting funding from any donor provided it does not impair independence or endanger integrity and reputation; annual reports, audited statements and IATI reporting are cited.
- **How it frames what a listing means.**
  The 2020 publication page frames disclosure systems as helping to ensure officials remain honest and are seen to remain honest; the 2013 article frames declarations as enabling civil society to hold leaders to account, for instance where leaders appear to live beyond their means (paraphrased). The 2020 PDF carries a standard accuracy note by the authors.
- **Status at retrieval.**
  active: transparency.org news items dated 15 September 2026 and 14 September 2026.
- **Not verified.**
  - Whether TI or any chapter currently operates a public dataset of officeholder declarations (none found on transparency.org)
  - The content of the 4 June 2024 Knowledge Hub item beyond its title and date
  - The current status of the Georgia and Russia chapter monitoring described in 2013
  - subject_scope: 'Georgia's electronic monitoring system' as an example in the 2020 paper — the PDF text search found Georgia only in the OGP member list; the passage may exist but was not located
  - Whether TI or any chapter currently operates a public dataset of officeholder declarations on transparency.org (none found; but see Declarator.org under missing_in_cluster, which is operated by TI's Russia chapter)
  - Content of the 4 June 2024 Knowledge Hub item beyond title and date
  - Current status of the Georgia and Russia chapter monitoring described in 2013
- **Confirmed by the second reader.** 10 claims, listed in the JSON.
- **Citations.**
  - <https://www.transparency.org/en/the-organisation> (retrieved 2026-09-21): self-description, legal form and Berlin secretariat, chapter structure, funding policy and accountability
  - <https://www.transparency.org/en/news> (retrieved 2026-09-21): news items dated 15 and 14 September 2026 (status)
  - <https://www.transparency.org/en/news/holding-politicians-to-account-asset-declarations> (retrieved 2026-09-21): 17 January 2013 date, balance-sheet framing, contents of a declaration, principles, Georgia and Russia chapter monitoring
  - <https://www.transparency.org/en/publications/recommendations-on-asset-and-interest-declarations-for-ogp-action-plans> (retrieved 2026-09-21): 5 November 2020 date, purpose, honest-and-seen-to-be-honest framing, PDF link
  - <https://files.transparencycdn.org/images/2020_PolicyPaper_AssetInterestDeclarationsOGP_English.pdf> (retrieved 2026-09-21): open data standard quote, authors, Ukraine and Georgia examples, online publication and algorithmic verification passages, 11 pages
  - <https://knowledgehub.transparency.org/tag/asset-declarations> (retrieved 2026-09-21): list of tagged publications with dates including the 4 June 2024 item

## Integrity Watch EU

<https://www.integritywatch.eu/>

- **Organisation.**
  Transparency International EU (Brussels; describes itself as an independent non-profit; EU Transparency Register 501222919-71)
- **Kind.**
  Open-data monitoring hub for EU decision-makers: MEP declarations of private and financial interests and side incomes, MEP and Commission lobby meetings, and the EU lobby register; with a Data Hub (data.integritywatch.eu) aggregating 24 national Integrity Watch platforms that cover asset and interest declarations, lobby meetings, party financing, procurement and ownership registers.
- **Self-description, as read.**
  Describes itself as "a hub that allows everyone to monitor the integrity of the EU's decision makers" (integritywatch.eu/about.php), launched in October 2014 by Transparency International EU, set against the presence of nearly 13,000 lobby organisations in Brussels. TI EU describes the wider Integrity Watch family as online tools that let citizens, journalists and civil society monitor the integrity of decisions made by politicians in the EU (paraphrased).
- **Subject scope.**
  Members of the European Parliament (2019-2024 and 2024-2029 legislatures) for side activities and income declarations and lobby meetings; European Commissioners and cabinets for lobby meetings; organisations in the EU Transparency Register. Data Hub: 24 country platforms across the EU, the Balkans, the UK and Tuerkiye.
- **Sources it says it uses.**
  - EU Open Data Portal; EU Transparency Register; individual MEP pages on the European Parliament website (about page)
  - MEP incomes: Source: Latest declaration, with the date of the latest declaration shown per MEP; meetings: Source: European Parliament
  - The about page states the data is exclusively retrieved from the EU institutions' official websites and is entirely self-reported
  - Linking of each row to the declaration document on the Parliament site: not verified
- **Outputs.**
  - Sortable MEP income table (Name, Country, Group, Activities, Estimated Annual Income, DPI Updates) organised by declaration section (previous occupations, current remunerated activities, board memberships, business holdings with public-policy implications, other)
  - Interactive charts and filters by country and legislature
  - Commission and MEP lobby-meeting tables (daily updates), lobbyist register data (daily), MEP incomes (monthly)
  - Data Hub aggregating national platforms; TI EU reports built on the data (the 2024 article cites 52,206 Commission meetings, 64,151 Parliament meetings, 12,771 lobby organisations, 1,822 MEP side activities in the most recent mandate)
- **Per-person derived score or rank, as observed.**
  Estimated annual income per MEP is a computed field, derived from the periodicity (hourly, monthly, annual) given in the original declarations; the table is sortable, so members can be ordered by that estimate. No composite score observed.
- **Identifiers exposed.**
  - not verified: no identifier scheme observed on the pages fetched (rows show name, country and political group)
- **Per-filing conditions it states or computes.**
  - No computed per-filing condition observed. The MEP income page states, as a register-level caveat, that a number of declarations are currently missing from the European Parliament website and that the section still shows 2019-2024 declarations while 2024 ones are processed. The meetings page cites the rule that MEPs must publish lobby meetings with third-country representatives and lobbyists acting for third countries.
- **Code.**
  not verified: no code repository found on the pages fetched.
- **Data licence.**
  Data published under the ODbL v1.0 open data licence (about page). TI EU's site describes the Integrity Watch work as licensed under a CC BY-NC-ND 3.0 licence (transparency.eu page, which prints it as CCC BY-NC-ND 3.0).
- **API.**
  not verified: no API observed on the pages fetched.
- **Funding or business model, as stated.**
  About page: current supporters KR Foundation, Adessium Foundation and Waverly Street Foundation, with earlier support from the European Commission and Open Society Initiative for Europe. The Data Hub was funded by the EU's Internal Security Fund - Police. TI EU's funders page lists a 2026 budget of about EUR 1 million from the TI Secretariat, Adessium, Waverly Street, KR Foundation, Stiftung Mercator, Google Charitable Fund, the European Commission, the UK FCDO and Open Society Foundations.
- **How it frames what a listing means.**
  About page: TI EU and Integrity Watch EU bear no responsibility for the accuracy of the original data, since all of it is self-reported through EU institutions (paraphrased). Income figures are labelled as estimates. The Data Hub carries an EU disclaimer that EU institutions are not responsible for any use of the information.
- **Status at retrieval.**
  unknown: no content dated within the last twelve months was observed on integritywatch.eu (the meetings page shows an unrendered last-updated placeholder; the income page's status note about 2024 declarations is undated; TI EU's decade article is dated 24 October 2024). The about page states daily and monthly update cycles, and TI EU's funders page references a 2026 budget.
- **Corrected on second reading.**
  - *derived_scoring_or_ranking.* First read: Estimated annual income per MEP is a computed field, derived from the periodicity (hourly, monthly, annual) given in the original declarations (cited to mepincomes.php). On re-reading: Neither the raw HTML nor the browser-rendered mepincomes.php contains any methodology text; the words hourly, periodicity, estimate and calculated do not appear. The page exposes only the column label 'Estimated annual income' and template fields income_amt_total_eur_manual and income_amt_total_eur_auto. The derivation method should be marked not verified or re-sourced. (<https://www.integritywatch.eu/mepincomes.php>)
- **Not verified.**
  - Last-update date of the platform
  - Any identifier scheme for MEPs
  - An API or code repository
  - Per-row links to the declaration PDFs on the European Parliament site
  - signal_precedents: 'the section still shows 2019-2024 declarations while 2024 ones are processed' — the rendered modal says the tool is being updated 'with the declarations of financial interests of the 9th legislature' (the 9th legislature is 2019-2024), so the note may predate the 2024 election; which legislature is currently displayed could not be determined
  - subject_scope: Data Hub coverage of 'the Balkans, the UK and Türkiye' — the hub page as fetched describes EU member states, candidate countries and regional neighbours without naming Türkiye
  - openness_code / openness_api: no repository or API found on pages fetched (consistent with entry; absence not proven)
  - Per-row links to declaration PDFs on the European Parliament site; last-update date of the platform
- **Confirmed by the second reader.** 10 claims, listed in the JSON.
- **Citations.**
  - <https://www.integritywatch.eu/about.php> (retrieved 2026-09-21): self-description quote, TI EU as operator, October 2014 launch, data coverage, sources, update frequencies, ODbL v1.0, no-responsibility disclaimer, funders
  - <https://www.integritywatch.eu/mepincomes.php> (retrieved 2026-09-21): sortable table columns, declaration sections, estimated annual income method, latest-declaration source and date, missing-declarations and 2019-2024 caveat
  - <https://www.integritywatch.eu/mepmeetings.php> (retrieved 2026-09-21): European Parliament source, third-country meetings rule, unrendered last-updated placeholder
  - <https://transparency.eu/integritywatch/> (retrieved 2026-09-21): TI EU description of Integrity Watch, CC BY-NC-ND 3.0 statement, national platforms and Data Hub
  - <https://transparency.eu/integrity-watch-eu-at-10-a-decade-of-holding-the-eu-to-account-through-open-data/> (retrieved 2026-09-21): 24 October 2024 date, 2014 launch, dataset counts, 19 platforms in 17 countries, planned Balkan platforms
  - <https://data.integritywatch.eu/> (retrieved 2026-09-21): Data Hub description, 24 country platforms, data types, EU Internal Security Fund funding, EU disclaimer
  - <https://transparency.eu/who-supports-us/> (retrieved 2026-09-21): TI EU 2026 budget and named funders, funding-independence policy

## Pages the first reader could not reach

- https://aleph.occrp.org/pages/about (rendered blank; single-page app)
- https://aleph.occrp.org/api/2/collections (HTTP 401 without authentication)
- https://docs.aleph.occrp.org/users/ (returned navigation only)
- http://docs.everypolitician.org/ (DNS did not resolve)
- https://everypolitician.org/methodology/ (HTTP 404)
- https://www.theyworkforyou.com/data/ (HTTP 404)
- https://www.abgeordnetenwatch.de/ueber-uns/finanzierung (HTTP 404; funding page found at /ueber-uns/mehr/finanzierung)
- https://www.occrp.org/en/who-we-are (HTTP 404; about page found at /en/about-us)
- https://www.occrp.org/en/support-us (HTTP 404; donors page found at /en/about-us/who-supports-our-work)
- https://www.opensanctions.org/docs/aleph/ (HTTP 404)
- https://www.opensanctions.org/docs/faq/ (navigation hub only; no FAQ content)
- https://transparency.eu/about/ (HTTP 404)
- https://public-accountability.org/ (301 redirect to littlesis.org)
- https://littlesis.org/* via WebFetch (blocked by the Anubis bot check; pages were read through the browser instead)
- https://www.theyworkforyou.com/api/docs/getPerson (loaded, but did not list response fields or identifier schemes)

## Projects the second reader said were missing from this cluster

- **Declarator.org (Transparency International – Russia).** <https://declarator.org/en/about/> A database of income and asset declarations of Russian public servants (parliament, government, judges, regional and municipal officials, state enterprises) aggregated from official agency websites, with the original declaration files kept under a Files tab and an open-source parser on GitHub; copyright line 2011–2026. It is the closest structural analogue in this cluster to Oath's declaration-ingestion shape, and it answers the TI entry's open question about whether any chapter operates a declarations dataset.
- **Wikidata WikiProject every politician.** <https://www.wikidata.org/wiki/Wikidata:WikiProject_every_politician> The upstream that both the EveryPolitician and OpenSanctions entries cite as their people source; the cluster discusses QIDs as identifiers without an entry for the project that maintains them.
- **Parltrack.** <https://parltrack.org/about> EU legislative and MEP tracking scraped from europarl.europa.eu with ODbL v1.0 bulk dumps and AGPLv3+ code, hosted by AS250.net Foundation; copyright line 2011-2024. A second EU-level analogue beside Integrity Watch EU with a different openness posture (dumps, no API key).
- **OpenAustralia Foundation: OpenAustralia.org and They Vote For You.** <https://www.openaustralia.org.au/> A fork of TheyWorkForYou and ParlParse applied to the Australian parliament, with They Vote For You (theyvoteforyou.org.au, code at github.com/openaustralia/theyvoteforyou) producing per-politician voting summaries; the same derived-score pattern the TWFY entry flags, in a second jurisdiction. theyvoteforyou.org.au/about returned HTTP 403 to WebFetch.
- **openparliament.ca.** <https://openparliament.ca/about/> Volunteer-run Canadian parliamentary monitoring site (launched 2010) with an API and bulk data and code on GitHub; a solo-operator precedent that speaks directly to Oath's solo-operator test.
