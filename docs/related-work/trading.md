# Related-work record: Congressional trading trackers and products

*Read on 2026-09-21. A first reader wrote each entry from the project's own pages; a second reader, briefed to refute, re-fetched every cited page. Corrections are shown beside the claims they correct and both are kept. Presence in this record is not a claim about a project's quality, and absence is not either. Presence in the register is not evidence of wrongdoing: where a record below describes what a neighbour published about an officeholder, it describes the role and not the person, names no one outside a citation URL, and is not a Finding. Rendered from `data/trading.json` by `render.py`; edit the JSON, not this file.*

## Capitol Trades

<https://www.capitoltrades.com/>

- **Organisation.**
  2iQ Research (Frankfurt am Main, Germany), per the site's Terms and Conditions and About page
- **Kind.**
  Free web platform aggregating U.S. congressional stock-trade disclosures, with trade, politician, issuer and state pages, editorial articles and a newsletter
- **Self-description, as read.**
  Describes itself as a platform offering access to real-time politician trading data, built on 2iQ's insider-transaction data experience and a process combining automated and manual record collection; says it is made free for the public as a matter of accountability and transparency, and that it supports the STOCK Act and its enforcement. On its Disclaimer page it calls itself "a financial data and content aggregator" (capitoltrades.com/disclaimer).
- **Subject scope.**
  U.S. Senators and Representatives. The trades page, set to a default three-year window on 2026-09-21, displayed 37,037 trades, 1,815 filings, $2.264B volume, 211 politicians and 3,053 issuers. Covers stocks and other asset types (an 'All Assets' toggle), with owner values such as Undisclosed and Spouse.
- **Sources it says it uses.**
  - Senate Financial Disclosures (eFD) reports (Disclaimer page, Citations section)
  - Official website of the Clerk of the U.S. House of Representatives (Disclaimer page)
  - ProPublica Congress API, used to cross-check and complement member details (Disclaimer page)
  - Per-row link to the primary filing: yes. The trade detail page read carried a 'View Original Filing' link to https://disclosures-clerk.house.gov/public_disc/ptr-pdfs/2026/20035480.pdf
- **Outputs.**
  - Trades table with columns Politician, Traded Issuer, Published, Traded, Filed After (days), Owner, Type (BUY/SELL), Size (range), Price
  - Trade detail pages with a filing summary (up to 15 trades from the same filing) and a link to the original filing
  - Politician pages (trades, filings, issuers, volume, last traded; About page says they show bio, committee memberships, tweets, trading activity and preferred sectors)
  - Issuer pages and state pages with trade counts and volume
  - Insights articles (dated, e.g. 2026-09-04) and a 'Buzz' feed
  - Weekly newsletter, Twitter feed, press kit download
- **Per-person derived score or rank, as observed.**
  No score, grade or report card observed. Ordered listings: the Politicians page lists members with trade count, issuers, volume and last-traded date (first entry displayed 13,686 trades); home page shows 'Featured Politicians' (trades, filings, issuers, volume), 'Featured Issuers' with three-year trade counts and price change percentages, and 'States' with trades, politicians and volume.
- **Identifiers exposed.**
  - Politician page URLs use an alphanumeric ID in the Bioguide ID pattern, e.g. /politicians/<letter and six digits> on three members' pages; the site does not label the scheme
  - Issuer pages use Capitol Trades' own numeric IDs, e.g. /issuers/429443
  - Trade pages use own numeric IDs, e.g. /trades/20003802803
  - Tickers with exchange suffix, e.g. ABBV:US
- **Per-filing conditions it states or computes.**
  - 'Filed After' column on every trade row and on trade detail pages: the number of days between the traded date and the publication/filing date (observed values 4, 9, 22, 28 days). No explicit 'late' flag or threshold was observed on the pages read.
  - About page states politician detail pages show committee memberships; no computed committee-conflict condition was observed.
- **Code.**
  No public code repository observed on the pages read.
- **Data licence.**
  No data license stated. Terms and Conditions (last updated February 14, 2022) name 2iQ Research as the operator and provide the service 'AS IS' with no warranty as to accuracy; the About page says the site is free for the public.
- **API.**
  No public API observed on the pages read.
- **Funding or business model, as stated.**
  Operated by 2iQ Research, a data vendor (Terms and Conditions; About page refers to the 2iQ data factory). The site is free to the public per the About page; a newsletter subscription is offered. No pricing observed.
- **How it frames what a listing means.**
  Disclaimer page: content is for informational purposes only; not investment advice; the operator is not a broker/dealer or investment adviser and has no access to non-public information about companies; describes the site as an educational forum for analysing information about politicians' investments; lists investment warnings. No statement about what a politician's presence in the listing does or does not mean was observed.
- **Status at retrieval.**
  active (trades published 'Today' on 2026-09-21; Insights articles dated 2026-09-04 and 2026-08-28)
- **Not verified.**
  - WebFetch returned HTTP 429/403 for capitoltrades.com; pages were read through the browser instead
  - Whether the politician URL IDs are Bioguide IDs: bioguide.congress.gov and congress.gov both returned HTTP 403, so the scheme was not confirmed against the source
  - Committee memberships on politician detail pages (stated on About; not read directly)
  - Existence of any API or data-license page beyond the footer links
  - Committee memberships on politician detail pages: the /politicians/S000250 page text read did not show a committee section (it may sit behind 'Show details'); the About page claim stands, the page rendering was not confirmed
  - Existence of any API or data-license page beyond footer links (footer has Sitemap, Privacy Policy, Terms & Conditions, Imprint, Disclaimer; no API page)
- **Confirmed by the second reader.** 12 claims, listed in the JSON.
- **Citations.**
  - <https://www.capitoltrades.com/> (retrieved 2026-09-21): Latest trades feed, featured politicians/issuers/states, 'Why Capitol Trades' text, dated insights
  - <https://www.capitoltrades.com/trades> (retrieved 2026-09-21): Trade table columns including Filed After (days), Owner, Size, Price; three-year totals; footer links
  - <https://www.capitoltrades.com/politicians> (retrieved 2026-09-21): Politician listing with trades, issuers, volume, last traded
  - <https://www.capitoltrades.com/about-us> (retrieved 2026-09-21): Self-description, 2iQ relationship, mission statement, free-to-public statement, politician page contents
  - <https://www.capitoltrades.com/disclaimer> (retrieved 2026-09-21): Disclaimer text; Citations section naming Senate eFD, House Clerk website, ProPublica Congress API
  - <https://www.capitoltrades.com/terms-and-conditions> (retrieved 2026-09-21): Operator identity (2iQ Research, Frankfurt), last-updated date, AS IS terms
  - <https://www.capitoltrades.com/trades/20003802803> (retrieved 2026-09-21): Trade detail fields and 'View Original Filing' link to a disclosures-clerk.house.gov PTR PDF; politician URL with S000250

## Unusual Whales politics

<https://unusualwhales.com/politics>

- **Organisation.**
  Unusual Whales (the About page says it is run by a small team with zero outside funding; the Subversive ETFs prospectus supplement of July 31, 2026 names 'Unusual Whales, Inc.')
- **Kind.**
  Politics section of a subscription market-data platform: congressional trade feed, politician profiles and portfolios, FEC data, an 'unusual trades' detector, annual reports, and a paid API
- **Self-description, as read.**
  The politics page is titled 'US Politics: Track Congressional & Senate Stock Trades'. The About page describes the company as an options, equity and flow platform for retail traders that also works on awareness of congressional trading and corporate lobbying, and cites its annual Congressional Trading Reports. The 2025 report's methodology states: "We scraped all Periodic Transaction Reports (PTRs) disclosed by Congress members this year" (unusualwhales.com/congress-trading-report-2025).
- **Subject scope.**
  Members of the U.S. House and Senate (profiles show chamber, party and district). The overview's 'Top Republicans' list also included an entry for the President, labelled House, with a trade count. Portfolios feature covers annual financial disclosures; FEC section covers PAC and candidate contributions.
- **Sources it says it uses.**
  - Periodic Transaction Reports (PTRs) and annual Financial Disclosure (FD) reports (2025 report methodology; most PTRs are machine-scrapable, some are filed by hand)
  - FEC data (politics FEC section; API tag fec_donation_conflict)
  - Committee assignments (used by USONAR and the committee_conflict tag; source of assignment data not named on pages read)
  - Per-row link to the primary filing: not observed. The per-disclosure page read showed a generated narrative and a transaction table with no link to a House Clerk or Senate eFD document
- **Outputs.**
  - Politics overview: Top Democrats/Top Republicans by trade count, most held stocks, holdings distribution, recent trades feed (reporter, chamber/party/district, ticker, asset description with [ST]/[OP] codes and FILING STATUS notes, type, amount range, transaction date, filing date)
  - Sub-sections: Politics Flow, Politicians, Portfolios, Midterms, Insider Trades, FEC Data, Unusual Trades (USONAR radar)
  - Per-politician profile pages (Bioguide-style biography text, recent trades, corporate PAC donations, recent FEC contributions)
  - Per-disclosure pages at own UUIDs with a narrative summary and a transaction table
  - Annual Congressional Trading Reports (2024, 2025 editions; 2025 dated January 2026)
  - Public API endpoints: /api/congress/recent-trades, /api/congress/late-reports, /api/congress/congress-trader, /api/congress/politicians, /api/congress/unusual-trades (+ /by-tickers, /chart-data, /stats), /api/politician-portfolios/* (enterprise); MCP server; skill.md
- **Per-person derived score or rank, as observed.**
  Top Democrats / Top Republicans ranked by trade count on the overview. The 2025 report estimates per-politician weighted returns by reconstructing portfolios from amount-range midpoints and benchmarks them to SPY (headline: only 32.2% of Congress beat SPY's +16.8%); it names top performers and, in a section on STOCK Act violations, lists the members with the longest disclosure delays (e.g. a 953-day gap) and the largest single late filing (504 transactions). USONAR positions trades on axes of 14-day alpha vs SPY and loss avoidance. The API /congress/unusual-trades/stats returns aggregate statistics described as including top politicians, party/chamber breakdowns, committee groups, industry groups and biggest trades.
- **Identifiers exposed.**
  - Own UUID politician_id (e.g. e138f347-ae92-4cfb-8f41-7036ff09a213) and politician_slug in the OpenAPI spec
  - Own UUID trade id and disclosure id (site URLs /politics/disclosure/<uuid>)
  - Profile URLs keyed by name, e.g. /politics/profile/<name>
  - No bioguide, FEC, OpenSecrets, Wikidata or GovTrack identifiers found in the OpenAPI spec (text search returned none); FEC section identifiers not read
- **Per-filing conditions it states or computes.**
  - Late reports: API endpoint /api/congress/late-reports 'Returns the recent late reports by congress members' with optional date and ticker filters; the spec does not state the threshold that makes a report late. The 2025 report frames the STOCK Act as requiring disclosure within 45 days and counts 1,200+ late-disclosed transactions across 50+ filings and 40 politicians, as of trades disclosed by December 29, 2025.
  - Unusual-trade reason tags (API, premium): committee_conflict, first_person_to_trade, low_marketcap, unusual_industry, unusually_large_trade, fec_donation_conflict; each trade carries unusual_activity_tags and unusual_activity_meta explaining why each flag was applied.
  - USONAR (site guide): trades are flagged when politicians trade stocks in sectors their committees regulate, especially when the trade significantly outperforms the market (14-day alpha vs SPY), occurs shortly before major market-moving events, the politician sells before a downturn (loss avoidance), or there is a jurisdictional conflict with committee assignments.
  - Trade-level fields: is_amendment (Politician Trades schema); filed_at_date and transaction_date; FILING STATUS notes shown in asset descriptions.
- **Code.**
  No public code repository observed. An MCP server and a skill.md are offered for the API.
- **Data licence.**
  Terms of Service (last updated June 15, 2021): site and data are for personal use only; no scraping, copying, republishing or redistribution; automated extraction prohibited. Public API page: the API is strictly for personal use and redistribution is not allowed, with account termination for violations.
- **API.**
  Paid API: API Basic $150/month (40,000 requests/day) and API Advanced $375/month (unlimited), 7-day free trial, 2-year historical lookback; 'Congressional and Insider Trades' in both tiers. /congress/unusual-trades endpoints are marked premium (contact dev@unusualwhales.com); /politician-portfolios endpoints are marked enterprise only.
- **Funding or business model, as stated.**
  Subscriptions: Retail Basic $50/month, Retail Pro $75/month, Retail Max $120/month (lower annual rates), each listing 'Politician Trade Information'; API tiers as above; enterprise data offering. The About page states the company has zero outside funding. The Subversive ETFs prospectus supplement of July 31, 2026 states the funds no longer use Unusual Whales, Inc. as Data Provider.
- **How it frames what a listing means.**
  Terms: information is for informational purposes only, not investment advice; no warranty as to timeliness or accuracy; not a registered investment adviser. Pricing page: 'Not financial advice'. The 2025 report states its goal is to draw attention to potential conflicts of interest and invites members of Congress to email congress@unusualwhales.com to correct calculated returns. Page titles frame the Unusual Trades section as detecting suspicious political trading.
- **Status at retrieval.**
  active (trades with filing date 2026-09-21 displayed; 2025 report dated January 2026)
- **Corrected on second reading.**
  - *identifiers_exposed.* First read: No bioguide, FEC, OpenSecrets, Wikidata or GovTrack identifiers found in the OpenAPI spec (text search returned none) On re-reading: FEC identifiers do appear in the spec: the 'Company Politics Candidates' example carries 'fec_candidate_id: H8MI09068' and a contribution example carries 'pdf_url: https://docquery.fec.gov/cgi-bin/fecimg/?...'. Bioguide, OpenSecrets, Wikidata and GovTrack are genuinely absent. The claim should read 'no bioguide/OpenSecrets/Wikidata/GovTrack identifiers; FEC candidate IDs appear in the FEC/company-politics schemas'. (<https://api.unusualwhales.com/api/openapi>)
  - *notes_for_oath / primary_sources_used.* First read: the site's own identifiers are UUIDs with no external crosswalk observed; per-row link to the primary filing not observed On re-reading: True for the public site page and the public Politician Trades schema, but the spec's 'Annual Disclosure' schema (enterprise /api/politician-portfolios/disclosures) documents a 'url' field ('The URL to the disclosure PDF') with the example https://disclosures-clerk.house.gov/public_disc/financial-pdfs/2024/10067467.pdf. The API does expose a primary-filing URL for annual disclosures at the enterprise tier; the survey should say so rather than 'not observed'. (<https://api.unusualwhales.com/api/openapi>)
  - *citations (congress-trading-report-2025, 'ETF data-provider statement').* First read: The 2025 report supports an 'ETF data-provider statement' On re-reading: The report says 'In 2023, we launched $NANC and $GOP, two ETFs to help retail investors follow these partisan portfolios'. It does not use the words 'data provider'. The data-provider role is documented in the funds' prospectus dated January 28, 2026 and its July 31, 2026 supplement, which should be the citation. (<https://subversiveetfs.com/prospectus>)
  - *disclaimer_or_frame.* First read: Page titles frame the Unusual Trades section as detecting suspicious political trading (presented as the project's frame, with nothing further) On re-reading: Incomplete in Oath's favour. The 2025 report's USONAR section states: 'While USONAR identifies unusual trades, it is a data visualization tool designed to flag outliers for public review; it does not allege insider trading or illegality.' A survey recording the project's frame must record that limiting statement alongside the page title. (<https://unusualwhales.com/congress-trading-report-2025>)
- **Not verified.**
  - WebFetch of the politics page returned only header content; the page was read through the browser
  - The threshold used by /congress/late-reports to mark a report late (not stated in the spec)
  - Source of committee-assignment data used for committee_conflict and USONAR
  - Identifiers used in the FEC section (not read)
  - The 2024 Congressional Trading Report (not read)
  - unusualwhales.com/terms-of-service and /terms-and-conditions returned HTTP 404; /terms was read instead
  - Threshold used by /congress/late-reports (spec description gives none; confirmed absent)
  - Source of committee-assignment data behind committee_conflict and USONAR (not stated on pages read)
  - Identifiers used in the site's FEC section pages (not read; only the API spec was checked)
- **Confirmed by the second reader.** 13 claims, listed in the JSON.
- **Citations.**
  - <https://unusualwhales.com/politics> (retrieved 2026-09-21): Overview layout, top-trader lists by trade count, recent trades fields, section links, disclosure and profile URL patterns
  - <https://unusualwhales.com/politics/sonar> (retrieved 2026-09-21): USONAR guide text defining flagging conditions and chart axes
  - <https://unusualwhales.com/politics/profile/Pete%20Sessions> (retrieved 2026-09-21): Profile page fields: biography, recent trades table, PAC donations, FEC contributions
  - <https://unusualwhales.com/politics/disclosure/ce6091d6-756d-4001-a19e-1e380a9ff1b0> (retrieved 2026-09-21): Per-disclosure page with narrative and transaction table; no primary-filing link observed
  - <https://unusualwhales.com/congress-trading-report-2025> (retrieved 2026-09-21): Methodology (PTR scraping, midpoint estimation, SPY benchmark, cutoff date), 45-day framing, late-filing counts, ranking of performers and late filers, correction invitation, ETF data-provider statement
  - <https://unusualwhales.com/pricing> (retrieved 2026-09-21): Retail subscription tiers and prices; politician trade information included; 'Not financial advice'
  - <https://unusualwhales.com/public-api> (retrieved 2026-09-21): API tiers, prices, request limits, lookback, personal-use and no-redistribution statement
  - <https://unusualwhales.com/terms> (retrieved 2026-09-21): Terms of Service: last updated date, personal use, anti-scraping, no redistribution, accuracy and advice disclaimers
  - <https://unusualwhales.com/about> (retrieved 2026-09-21): Self-description, zero outside funding statement, history of congressional trading reports
  - <https://api.unusualwhales.com/docs> (retrieved 2026-09-21): List of congress and politician_portfolios endpoints
  - <https://api.unusualwhales.com/api/openapi> (retrieved 2026-09-21): Endpoint descriptions (late-reports, recent-trades, unusual-trades, politician-portfolios), Senate Stock and Politician Trades schemas, unusual_activity_tags enum, UUID politician_id, absence of bioguide/FEC identifiers

## Quiver Quantitative

<https://www.quiverquant.com/>

- **Organisation.**
  Quiver Quantitative, Inc. (site footer copyright 2020-2026; About page says founded February 2020 by two college students)
- **Kind.**
  Retail alternative-data platform with a free dashboard, a premium tier, backtested strategies, and a paid API; congressional trading is one of its datasets
- **Self-description, as read.**
  Home page taglines 'Trade Like an Insider' and 'Track the forces that move the markets'; About page says it scrapes alternative stock data from across the internet into a free dashboard to bridge an information gap between institutional and non-professional investors. The Congress Trading page explains the STOCK Act 45-day disclosure requirement and says: "We download those disclosures, parse them for stock trades" (quiverquant.com/congresstrading/).
- **Subject scope.**
  U.S. Senators and Representatives (live, historical and bulk congress, house and senate trading endpoints), plus a 'Bulk Trump Stock Trades' endpoint, live congress stock holdings from annual disclosures, and live net worth estimates.
- **Sources it says it uses.**
  - Congressional STOCK Act disclosures, which the site says it downloads and parses; the specific agencies (House Clerk, Senate eFD) were not named on the pages read
  - Annual financial disclosure statements for the Estimated Live Stock Portfolio (politician page note)
  - Per-row link to the primary filing: not observed on the pages read (the trades table shows Stock, Transaction, Politician, Filed, Traded, Description, and estimated excess return)
- **Outputs.**
  - Congress Trading page: trades table with Filed and Traded dates and 'Estimated excess return of the underlying stock since the transaction'
  - Politician pages (e.g. /congresstrading/politician/<name>-<bioguide id>): trades, a 'Return Since <date>' strategy chart vs SPY, Estimated Live Stock Portfolio from annual disclosures, Net Worth dashboard link
  - 'Most Active Congressional Traders - Last Year' (trade count and estimated volume); 'Highest Net Worth Congressmembers'; 'Politician Stock Portfolio Leaderboard' (premium)
  - Congress Backtester and Quiver Strategies (backtested strategies built on Quiver datasets, premium); alerts
  - API (api.quiverquant.com): Live/Historical/Bulk Congress Trading, Recent/Historical House and Senate Trading, Live/Bulk Congress Politicians, Live Congress Stock Holdings, Bulk Trump Stock Trades
  - Python client 'quiverquant' on PyPI (MIT License, v0.2.6, May 7, 2026)
  - Portfolios published on Autopilot under the pilot name Quiver Quantitative (e.g. 'Congress Buys')
- **Per-person derived score or rank, as observed.**
  'Most Active Congressional Traders - Last Year' ranked by number of trades and estimated volume; 'Politician Stock Portfolio Leaderboard' of top-performing politician portfolios (premium); 'Highest Net Worth Congressmembers'; per-trade ExcessReturn, PriceChange and SPYChange fields; per-politician return since a start date vs SPY; API Live Congress Politicians returns TradeCount, TradeVolume and NetWorth per member.
- **Identifiers exposed.**
  - BioGuideID: field in Live Congress Trading and Live Congress Politicians API responses; also embedded in politician page URLs (e.g. ...-P000197)
  - CandidateID: field in the Live Congress Politicians response (scheme not stated on the docs page)
  - Ticker, District, Party, House (Representatives or Senate), State
- **Per-filing conditions it states or computes.**
  - ExcessReturn per trade: estimated return of the stock compared to the S&P 500 since the transaction date (API field description); PriceChange and SPYChange likewise
  - ReportDate and TransactionDate are both returned per trade; no late-filing flag or days-late field was observed on the endpoints read
  - Amount is the lower bound of the disclosed range; the politicians endpoint offers volume_method of range_start, average (default) or range_end
- **Code.**
  Python client package 'quiverquant' on PyPI under the MIT License (v0.2.6, May 7, 2026). The GitHub URL github.com/Quiver-Quantitative/quiverquant returned HTTP 404, so the repository location was not verified.
- **Data licence.**
  Terms of Use (last modified June 25, 2026): 'Quiver Data' is proprietary; licensed for personal, non-commercial use only; no redistribution, republication, resale or incorporation into third-party products without written authorization; an API License Agreement is incorporated by reference.
- **API.**
  Paid API with Bearer-token auth; landing page states pricing 'starting from just $30/month'; docs group endpoints as public, Tier 1 and Tier 2; tutorial mentions a Hobbyist plan.
- **Funding or business model, as stated.**
  Free Visitor tier; Premium at $25/month (or yearly) with strategies, alerts and backtesting; API subscriptions; enterprise agreements for commercial use (Terms). A Labor Day promotion (50% off first year, ending September 7) was displayed.
- **How it frames what a listing means.**
  Disclaimers page: content should not be construed as advice; backtests and strategy results are not a guarantee of future results; site content may be lagged, outdated or otherwise inaccurate; nothing constitutes a solicitation or recommendation. Congress Trading page: performance results are based on historical backtesting and are hypothetical. Politician page holdings note: holdings come from annual disclosures, occasionally contain parsing errors, and exclude recent transactions.
- **Status at retrieval.**
  active (promotion dated September 7 shown on 2026-09-21; Terms modified June 25, 2026; PyPI release May 7, 2026)
- **Corrected on second reading.**
  - *openness_code.* First read: The GitHub URL github.com/Quiver-Quantitative/quiverquant returned HTTP 404, so the repository location was not verified On re-reading: The PyPI page lists the project homepage as https://github.com/Quiver-Quantitative/python-api, which exists ('Python package for the Quiver API', MIT, 58 stars). The 404 was for a guessed URL; the repository location is stated on the cited PyPI page. (<https://pypi.org/project/quiverquant/>)
  - *disclaimer_or_frame.* First read: Disclaimers page: content should not be construed as advice On re-reading: The Disclaimers page's wording is narrower: 'Quiver Quantitative Inc. is neither a law firm nor a certified public accounting firm and no portion of our website ... should be construed as legal or accounting advice', plus the no-solicitation and not-a-guarantee sentences. The 'not investment advice' framing sits in the Terms/other pages, not this one. (<https://www.quiverquant.com/disclaimers/>)
- **Not verified.**
  - Which government sites (House Clerk, Senate eFD) are read; not named on pages read
  - Whether trade rows link to the primary filing
  - Strategies page (quiverquant.com/strategies/ exceeded the fetch size limit)
  - Exact API tier prices and rate limits
  - GitHub repository location (URL tried returned 404)
  - Whether the Politician Stock Portfolio Leaderboard is premium-only (the link exists; gating not checked)
  - Exact API tier prices and rate limits beyond 'starting from $30/month'
  - Which government sites are read (not named on pages read; confirmed absent from the Congress Trading page)
  - Strategies page content
- **Confirmed by the second reader.** 9 claims, listed in the JSON.
- **Citations.**
  - <https://www.quiverquant.com/> (retrieved 2026-09-21): Taglines, pricing tiers, promotion, API and strategies mentions, footer links
  - <https://www.quiverquant.com/congresstrading/> (retrieved 2026-09-21): STOCK Act framing, download-and-parse statement, table fields, rankings, hypothetical-performance disclaimer
  - <https://www.quiverquant.com/aboutus/> (retrieved 2026-09-21): Founding date, mission, scraping description
  - <https://www.quiverquant.com/congresstrading/politician/Nancy%20Pelosi-P000197> (retrieved 2026-09-21): Politician page fields, return-vs-SPY chart, holdings disclaimer, Bioguide-style ID in URL
  - <https://api.quiverquant.com/> (retrieved 2026-09-21): API pricing statement, endpoint categories, copyright
  - <https://api.quiverquant.com/docs/#/operations/live_congresstrading_retrieve> (retrieved 2026-09-21): Live Congress Trading response fields including BioGuideID, ReportDate, TransactionDate, Amount, ExcessReturn, PriceChange, SPYChange
  - <https://api.quiverquant.com/docs/#/operations/live_congress_politicians_retrieve> (retrieved 2026-09-21): Politicians response fields including BioGuideID, CandidateID, TradeCount, TradeVolume, NetWorth; volume_method options; tier groupings
  - <https://www.quiverquant.com/disclaimers/> (retrieved 2026-09-21): Disclaimer statements
  - <https://www.quiverquant.com/termsofservice/> (retrieved 2026-09-21): Data ownership, non-commercial licence, redistribution prohibition, last-modified date
  - <https://www.quiverquant.com/api-setup/> (retrieved 2026-09-21): Tutorial, Hobbyist plan mention, congress politicians endpoint example
  - <https://pypi.org/project/quiverquant/> (retrieved 2026-09-21): Python client, MIT License, version and release date, congress_trading function and columns

## House Stock Watcher

<https://housestockwatcher.com/>

- **Organisation.**
  not verified (site unreachable). A related data-listing gist naming the house-stock-watcher-data S3 bucket is by GitHub user timothycarambat, who also owns the senate-stock-watcher-data repository
- **Kind.**
  Reported as a web application and public JSON dataset of House stock-trade disclosures (per the companion gist); the site itself could not be reached
- **Self-description, as read.**
  not verified. The domain did not resolve (DNS ENOTFOUND for housestockwatcher.com and www.housestockwatcher.com on 2026-09-21) and web.archive.org could not be fetched.
- **Subject scope.**
  not verified. The companion gist describes the data as congressional stock-watcher transactions sorted by disclosure_date.
- **Sources it says it uses.**
  - not verified for the original site
  - Data URL referenced by the gist: https://house-stock-watcher-data.s3-us-west-2.amazonaws.com/data/all_transactions.json, which returned HTTP 403 Forbidden on 2026-09-21
- **Outputs.**
  - all_transactions.json on the house-stock-watcher-data S3 bucket (per the gist; unreachable at retrieval)
  - A disclosure_date field in MM/DD/YYYY format (the gist parses it)
- **Per-person derived score or rank, as observed.**
  not verified
- **Identifiers exposed.**
  - not verified
- **Per-filing conditions it states or computes.**
  - not verified
- **Code.**
  not verified. github.com/timothycarambat/house-stock-watcher-data returned HTTP 404, and the GitHub API listing of that user's repositories contained no repository with 'house' or 'stock' in its name.
- **Data licence.**
  not verified
- **API.**
  not verified. The S3 JSON endpoint named in the gist returned HTTP 403.
- **Funding or business model, as stated.**
  not verified
- **How it frames what a listing means.**
  not verified
- **Status at retrieval.**
  unknown (domain did not resolve; data bucket returned 403; no page stating closure was found)
- **Corrected on second reading.**
  - *openness_code.* First read: the GitHub API listing of that user's repositories contained no repository with 'house' or 'stock' in its name On re-reading: timothycarambat/senate-stock-watcher-data exists under that user (GitHub search API: 100 stars, pushed 2021-03-16, owner.login timothycarambat, not a fork), and the same survey cites it. The accurate statement is that the user has no repository with 'house' in its name; 'stock' matches senate-stock-watcher-data. (<https://api.github.com/search/repositories?q=senate-stock-watcher>)
- **Not verified.**
  - Everything about the site's own pages (DNS failure)
  - Archived snapshots (web.archive.org not fetchable from this tool)
  - Original GitHub repository (404) and any license
  - S3 dataset contents (403)
  - Everything about the site's own pages (DNS failure confirmed; no archive checked)
  - Original House repository and license
  - S3 dataset contents (403 confirmed)
  - organisation: the gist author link is the only basis; the site's operator is not verified
- **Confirmed by the second reader.** 4 claims, listed in the JSON.
- **Citations.**
  - <https://gist.github.com/timothycarambat/db52c7b475edc0bdf0771e064874a2c5> (retrieved 2026-09-21): Gist dated September 15, 2021 naming the house-stock-watcher-data and senate-stock-watcher-data S3 all_transactions.json URLs and the disclosure_date field

## Senate Stock Watcher

<https://senatestockwatcher.com/>

- **Organisation.**
  GitHub user timothycarambat (owner of the senate-stock-watcher-data repository, whose homepage field is https://senatestockwatcher.com/)
- **Kind.**
  Web application plus a public GitHub data repository of JSON files of Senate periodic transaction reports
- **Self-description, as read.**
  The repository README describes Senate Stock Watcher as a web application that "shows metrics and analytics for tickers, senators, and filings" reported by U.S. Senators (github.com/timothycarambat/senate-stock-watcher-data README). The GitHub description says the repository holds the same data as senatestockwatcher.com.
- **Subject scope.**
  U.S. Senators, current and past, as filed on efdsearch.senate.gov (README).
- **Sources it says it uses.**
  - Senate eFD: the README says the data is originally sourced from the Senate's financial disclosure office at efdsearch.senate.gov
  - Per-row link to the primary filing: yes, each filing record carries a ptr_link to the original Senate filing (README field list)
- **Outputs.**
  - data/transaction_report_for_MM_DD_YYYY.json daily files
  - aggregate/all_transactions.json, all_ticker_transactions.json, and per-senator summaries; YAML versions
  - Transaction fields: transaction_date, owner, ticker, asset_description, asset_type, type, amount, comment
  - Filing fields: first_name, last_name, office, ptr_link, date_recieved, transactions[]
  - scripts/ directory of processing utilities
- **Per-person derived score or rank, as observed.**
  None observed in the repository README.
- **Identifiers exposed.**
  - Senator first_name, last_name and office strings
  - ptr_link URL to the Senate eFD filing
  - No bioguide or other external identifier observed
- **Per-filing conditions it states or computes.**
  - None observed. The README notes that some filings are scanned PDFs without extracted transactions and that gaps were being backfilled with an external repository.
- **Code.**
  Public GitHub repository (data and scripts): https://github.com/timothycarambat/senate-stock-watcher-data; default branch master; 100 stars; not archived.
- **Data licence.**
  No license file (GitHub API reports license: null); no usage statement in the README summary.
- **API.**
  No API. Aggregate JSON was served from https://senate-stock-watcher-data.s3-us-west-2.amazonaws.com/aggregate/all_transactions.json per the companion gist; that URL returned HTTP 403 on 2026-09-21.
- **Funding or business model, as stated.**
  Not stated on pages read.
- **How it frames what a listing means.**
  None observed in the README summary.
- **Status at retrieval.**
  unknown (repository last pushed 2021-03-16 per GitHub API and not archived; the README says it will be updated continually; the site domain did not resolve on 2026-09-21; no page states the project has ended)
- **Not verified.**
  - The live site (DNS failure for senatestockwatcher.com and www.senatestockwatcher.com)
  - Archived snapshots (web.archive.org not fetchable)
  - Current availability of the S3 aggregate (403)
  - Any license or disclaimer beyond the README
  - Live site content and archived snapshots
  - Funding or business model (not stated anywhere read)
- **Confirmed by the second reader.** 7 claims, listed in the JSON.
- **Citations.**
  - <https://github.com/timothycarambat/senate-stock-watcher-data> (retrieved 2026-09-21): README self-description, eFD source, field lists, directory layout, backfilling note
  - <https://raw.githubusercontent.com/timothycarambat/senate-stock-watcher-data/master/README.md> (retrieved 2026-09-21): Exact self-description and source sentences, transaction and filing fields including ptr_link and date_recieved
  - <https://api.github.com/repos/timothycarambat/senate-stock-watcher-data> (retrieved 2026-09-21): Description, homepage, created_at 2020-04-19, pushed_at 2021-03-16, archived false, license null, stars 100
  - <https://gist.github.com/timothycarambat/db52c7b475edc0bdf0771e064874a2c5> (retrieved 2026-09-21): S3 aggregate JSON URL used for the senate data

## Autopilot

<https://joinautopilot.com/>

- **Organisation.**
  Autopilot Holdings Corporation, with subsidiary Autopilot Advisers, LLC, described on the site as an SEC-registered investment adviser
- **Kind.**
  Investment app that copies published portfolios ('Pilots') into a user's linked brokerage account, including a Pelosi Tracker portfolio and other politician trackers
- **Self-description, as read.**
  Page title: "Invest alongside politicians & real-time traders" (joinautopilot.com). The home page says users pick a portfolio, connect a brokerage, and trades are executed automatically. The Pelosi Tracker page says the tracker began in 2022 as a co-founder's social-media tool for monitoring trades disclosed by members of Congress, that the team read new filings each morning and called out trades they considered potential conflicts of interest, and that the app turns public filings into investment insights; it states over $1.1B invested by over 180,000 people and a goal of supporting a politician stock-trading ban.
- **Subject scope.**
  Politicians' disclosed trades as mirrored portfolios (Pelosi Tracker+, Mullin Tracker, 'Congress Buys' by pilot Quiver Quantitative, and 14 portfolios by pilot Unusual Whales), alongside non-political portfolios (Inverse Cramer, hedge-fund trackers, creator portfolios).
- **Sources it says it uses.**
  - Public STOCK Act filings, described as disclosures of members' own, spouses' and dependents' trades due up to 45 days after the trade (Pelosi Tracker page); the FAQ says positions update as soon as a report is filed
  - No government site is named; per-row links to filings were not observed
- **Outputs.**
  - Portfolios to copy, with 'Top Performers' returns over 1W to 2Y windows and 'Popular' ranking by amount invested
  - Pilots directory (e.g. Unusual Whales 14 portfolios, Quiver Quantitative 10 portfolios)
  - Pelosi Tracker story page, FAQ, Manifesto, Disclaimer, Terms, Privacy, Form ADV Part 2A and Client Relationship Summary links
- **Per-person derived score or rank, as observed.**
  'Top Performers' ranking of portfolios by percentage return for a selected window (e.g. Pelosi Tracker+ shown at +69.6% and Congress Buys at +61.0% on 2026-09-21) and 'Popular' ranking by dollars invested (Pelosi Tracker+ $553.4M). No per-politician scores beyond portfolio returns.
- **Identifiers exposed.**
  - Own numeric landing IDs for portfolios, e.g. /landing/1/8735 (Pelosi Tracker+)
  - No person identifiers observed
- **Per-filing conditions it states or computes.**
  - None computed. The Pelosi Tracker page describes an editorial practice of reading new filings each morning and calling out trades the team considers potential conflicts of interest; no defined condition is stated.
- **Code.**
  None observed.
- **Data licence.**
  Not stated on pages read (Terms page not read).
- **API.**
  None observed.
- **Funding or business model, as stated.**
  Subscriptions (FAQ refers to Autopilot Premium and Autopilot+; additional fees may apply; prices not shown on pages read). Disclaimer page discloses a referral arrangement with Public Holdings, Inc. paying $50 to $5,000 per newly funded referred account, described as a conflict of interest.
- **How it frames what a listing means.**
  Footer: information is educational and illustrative, not a recommendation or offer; relies on sources believed reliable but cannot guarantee accuracy or completeness; past performance not indicative. Disclaimer page: Autopilot Holdings is not an investment adviser, advice is provided by Autopilot Advisers (SEC-registered); investing involves risk of loss; brokerage-affiliation disclosure.
- **Status at retrieval.**
  active (copyright 2026; Pelosi Tracker page references 'As of January 2026')
- **Corrected on second reading.**
  - *notes_for_oath.* First read: Its 'Pilots' include Unusual Whales and Quiver Quantitative, so its politician portfolios sit downstream of those trackers. On re-reading: Overstated. The home page attributes Pelosi Tracker+ and Mullin Tracker to 'Autopilot' itself, not to either Pilot; only the Unusual Whales- and Quiver-authored portfolios (e.g. 'Congress Buys' by Quiver Quantitative) are downstream of those trackers. The data source behind Autopilot's own politician portfolios is not stated. (<https://joinautopilot.com/>)
- **Not verified.**
  - WebFetch returned HTTP 429 for joinautopilot.com pages; read through the browser
  - Subscription prices and the Terms page
  - How Pelosi Tracker+ differs from Pelosi Tracker
  - Which data vendor supplies filings to the app
  - Which data vendor supplies filings to the app (the Unusual Whales 2025 report says 'we partnered with our friends at Autopilot to help retail copytrade politicians', which shows a partnership but not a data-supply relationship)
  - Landing ID /landing/1/8735 for Pelosi Tracker+ (not checked)
- **Confirmed by the second reader.** 9 claims, listed in the JSON.
- **Citations.**
  - <https://joinautopilot.com/> (retrieved 2026-09-21): Home page self-description, featured and top-performer portfolios, pilots list, how-it-works, footer disclaimer and corporate names
  - <https://www.joinautopilot.com/pelosi-tracker> (retrieved 2026-09-21): Origin story, STOCK Act 45-day framing, public-filings data source, invested totals, ban advocacy statement
  - <https://www.joinautopilot.com/faq> (retrieved 2026-09-21): Subscriptions, brokerage integration, timing of position updates after a filing, proportional rebalancing
  - <https://www.joinautopilot.com/disclaimer> (retrieved 2026-09-21): Adviser structure, risk disclaimers, Public Holdings referral arrangement

## Subversive Congressional Democrats Trading ETF (NANC) and Subversive Congressional Republicans Trading ETF (GOP, formerly KRUZ)

<https://subversiveetfs.com/>

- **Organisation.**
  Adviser: Tidal Investments LLC (a Tidal Financial Group company); distributor Foreside Fund Services, LLC; fund sponsor Subversive Markets Lab, LLC (prospectus supplement July 31, 2026). Data Provider was Unusual Whales, Inc. until the July 31, 2026 supplement, which states the Adviser now obtains PTR information directly.
- **Kind.**
  Two actively managed exchange-traded funds whose portfolios are built from members of Congress' Periodic Transaction Reports
- **Self-description, as read.**
  Fund pages: NANC invests in equity securities purchased or sold by Democratic members of Congress and their spouses; GOP does the same for Republican members. The NANC fact sheet says the fund gives access to near-real-time trading disclosures of members of Congress and that the adviser does not express a view and will "only buy or sell what members of Congress hold" (NANC fact sheet, June 30, 2026). The site notes that on 03.21.2025 KRUZ changed its ticker to GOP; the July 31, 2026 supplement renamed the funds from 'Unusual Whales Subversive Democratic/Republican Trading ETF'.
- **Subject scope.**
  Sitting U.S. Senators and Representatives registered with the Democratic Party (NANC) or Republican Party (GOP) and their family members (spouse and dependent children), using PTRs from the past three years; trades made before swearing-in are excluded. Appendix A of the prospectus (as of July 31, 2026) lists the Congresspeople covered.
- **Sources it says it uses.**
  - Periodic Transaction Reports filed under the STOCK Act with the Senate Office of Public Records or the Clerk of the House and made available online under the Ethics in Government Act (prospectus)
  - No per-row filing links; the funds publish holdings, not filings
- **Outputs.**
  - Fund pages with performance (as of 08/31/2026 and 06/30/2026), top-10 holdings (as of 09/21/2026), expense ratio, net assets
  - Daily holdings CSV (TidalFG_Holdings_NANC.csv), fact sheets, prospectus, summary prospectuses, SAI, shareholder reports
- **Per-person derived score or rank, as observed.**
  No per-person score. Portfolio construction weights holdings by the level of reported trading: securities with large, recurring or multi-member purchases are overweighted; small purchases, recent sales and one-off trades are excluded or underweighted; range midpoints are used; purchases are netted against sales; same-day PTRs of the same security are netted; 100 to 200 holdings under normal circumstances. Fund performance is shown against the S&P 500 TR (NANC fact sheet: NAV 21.06% one-year vs 22.32% as of 06/30/2026).
- **Identifiers exposed.**
  - None for persons. Fund identifiers only (NANC CUSIP 81752T510, ISIN US81752T5103 on the fact sheet)
- **Per-filing conditions it states or computes.**
  - None. The prospectus states PTRs are due within 30 days of awareness and no later than 45 days after the transaction, and lists 'Reporting Delay Risk' and 'Ethics in Government Act (EIGA) Risk' regarding commercial use of PTRs.
- **Code.**
  None.
- **Data licence.**
  Not applicable; holdings CSV is published on the site without a stated license.
- **API.**
  None.
- **Funding or business model, as stated.**
  Unitary management fee: NANC 0.72% per the fund page and prospectus (the June 30, 2026 fact sheet shows 0.73%); GOP 0.73% per the fund page. GOP net assets $93.55M as of 09/21/2026; NANC AUM $282.2M on the June 30, 2026 fact sheet. A sponsorship agreement with Subversive Markets Lab, LLC shares remaining profits and shortfalls (July 31, 2026 supplement).
- **How it frames what a listing means.**
  Fact sheet: the fund does not express a view or opinion and only buys or sells what members of Congress hold; past performance does not guarantee future results. Prospectus risk factors: reporting delays may cause the fund to buy higher or sell lower than members did; high portfolio turnover; uncertainty about commercial use of PTRs under EIGA; limited operating history; possible legislative restrictions.
- **Status at retrieval.**
  active (holdings as of 2026-09-21; prospectus supplement dated August 20, 2026)
- **Corrected on second reading.**
  - *funding_or_business_model.* First read: Unitary management fee: ... GOP 0.73% per the fund page On re-reading: The GOP fund page figure of 0.73% is the expense ratio. The prospectus fee table gives GOP's Management Fee as 0.72% and Total Annual Fund Operating Expenses as 0.73%; the management-fee table on the fees page lists both funds at 0.72%. Label 0.73% as GOP's expense ratio, not its unitary management fee. (<https://subversiveetfs.com/prospectus>)
  - *signal_precedents.* First read: lists 'Reporting Delay Risk' and 'Ethics in Government Act (EIGA) Risk' On re-reading: The prospectus risk heading is 'Ethics in Government Act Risk.' (no parenthetical); the quoted label should match. 'Reporting Delay Risk.' is exact. (<https://subversiveetfs.com/prospectus>)
- **Not verified.**
  - Rebalancing frequency (not stated in the text read)
  - The base summary prospectus text (the summary-prospectus link served the August 20, 2026 supplement)
  - subversiveetfs.com/about/ returned HTTP 404
  - How the Adviser now obtains PTR data directly (method not described)
  - Rebalancing frequency
  - How the Adviser now obtains PTR data directly (method not described in the supplement)
  - subversiveetfs.com/about/ status (not re-checked)
  - NANC inception date discrepancy (fund page 02/06/2023 vs fact sheet 02/07/2023) is on the pages but not claimed by the entry
- **Confirmed by the second reader.** 11 claims, listed in the JSON.
- **Citations.**
  - <https://subversiveetfs.com/> (retrieved 2026-09-21): Issuer description, fund descriptions, KRUZ to GOP ticker change, adviser and distributor, PTR-based methodology summary, risk disclosures
  - <https://subversiveetfs.com/nanc/> (retrieved 2026-09-21): NANC objective, STOCK Act/EIGA framing, inception date, expense ratio 0.72%, as-of dates, document links, Democratic-Party-only rule
  - <https://subversiveetfs.com/gop/> (retrieved 2026-09-21): GOP objective, Republican-Party-only rule, expense ratio 0.73%, net assets and as-of dates
  - <https://subversiveetfs.com/prospectus> (retrieved 2026-09-21): Prospectus dated January 28, 2026 with supplements of July 31, 2026 (name change; removal of Unusual Whales, Inc. as Data Provider; sponsor SML) and August 20, 2026 (Appendix A list); Principal Investment Strategies text on PTRs, family members, 3-year lookback, midpoint weighting, netting, 100-200 holdings, exclusions
  - <https://subversiveetfs.com/nanc/fact-sheet> (retrieved 2026-09-21): Fund details, no-view statement, performance vs S&P 500 TR, top holdings as of 06/30/2026, CUSIP and ISIN
  - <https://subversiveetfs.com/nanc/summary-prospectus> (retrieved 2026-09-21): August 20, 2026 supplement text amending Principal Investment Strategies and adding Appendix A
  - <https://unusualwhales.com/congress-trading-report-2025> (retrieved 2026-09-21): Unusual Whales' statement (January 2026) that it was the data provider for NANC and GOP

## house-stock-watcher-data (TattooedHead)

<https://github.com/TattooedHead/house-stock-watcher-data>

- **Organisation.**
  GitHub user TattooedHead
- **Kind.**
  Public GitHub data repository plus scraper that publishes House Periodic Transaction Report trades as JSON
- **Self-description, as read.**
  GitHub description: "Free public House of Representatives stock trade disclosures." The README says the author wrote it with Claude Code because they believed such a tool should be available after finding nothing currently working that did this.
- **Subject scope.**
  U.S. House of Representatives PTR filings (yearly filing indexes from the House Clerk site).
- **Sources it says it uses.**
  - House Clerk financial disclosure site: the repository's CLAUDE.md says the scraper downloads yearly filing indexes, identifies new PTR documents, fetches their PDFs and parses trade tables
  - Per-row link to the primary filing: yes, each record carries filing_id and source_url
- **Outputs.**
  - data/all_transactions.json (11,651,400 bytes at retrieval), data/filings_manifest.json, data/jammed_rows.jsonl (problem rows)
  - Record fields: transaction_date, disclosure_date, ticker, asset_description, asset_type, type, amount, amount_mid, representative, district, owner, filing_id, source_url
  - scraper/fetch.py run by GitHub Actions on a schedule
- **Per-person derived score or rank, as observed.**
  None observed.
- **Identifiers exposed.**
  - representative name and district strings
  - filing_id and source_url of the House Clerk PTR
  - No bioguide or other external person identifier observed
- **Per-filing conditions it states or computes.**
  - None observed. Both transaction_date and disclosure_date are recorded per row.
- **Code.**
  Public repository with scraper and data; created 2026-05-29; default branch main; 1 star.
- **Data licence.**
  No license file (GitHub API reports license: null).
- **API.**
  None; JSON files in the repository.
- **Funding or business model, as stated.**
  Not stated.
- **How it frames what a listing means.**
  None observed in the README.
- **Status at retrieval.**
  active (last push 2026-09-19 per GitHub API)
- **Not verified.**
  - Relationship, if any, to the original housestockwatcher.com project (not stated)
  - Scraper schedule interval (not stated)
  - Data quality beyond the presence of a jammed_rows.jsonl log
  - notes_for_oath asserts 'separately authored from the original House Stock Watcher' while could_not_verify says the relationship is not stated; the repository says nothing either way, so 'separately authored' is an inference, not a verified fact
  - Scraper schedule interval (not stated in CLAUDE.md)
- **Confirmed by the second reader.** 6 claims, listed in the JSON.
- **Citations.**
  - <https://github.com/TattooedHead/house-stock-watcher-data> (retrieved 2026-09-21): Repository description, README statement of purpose, directory layout
  - <https://api.github.com/repos/TattooedHead/house-stock-watcher-data> (retrieved 2026-09-21): created_at 2026-05-29, pushed_at 2026-09-19, archived false, license null, stars 1
  - <https://raw.githubusercontent.com/TattooedHead/house-stock-watcher-data/main/CLAUDE.md> (retrieved 2026-09-21): House Clerk source, GitHub Actions schedule, output files, record fields, parsing guards
  - <https://api.github.com/repos/TattooedHead/house-stock-watcher-data/contents/data> (retrieved 2026-09-21): Data file names and sizes

## Finnhub Congressional Trading endpoint

<https://finnhub.io/docs/api/congressional-trading>

- **Organisation.**
  Finnhub (finnhub.io)
- **Kind.**
  Endpoint of a commercial financial-data API returning stock trades disclosed by members of Congress for a given symbol
- **Self-description, as read.**
  The documentation describes the endpoint as returning stock trades data disclosed by members of Congress, marked 'Premium Access Required'; the page title reads "Congressional Stock Trades API." (finnhub.io/docs/api/congressional-trading).
- **Subject scope.**
  Trades by members of Congress, queried per company symbol and date range (GET /stock/congressional-trading?symbol=&from=&to=).
- **Sources it says it uses.**
  - Not named on the documentation page
  - Per-row link to the primary filing: no such field in the documented response
- **Outputs.**
  - JSON response: data[] with amountFrom, amountTo, assetName, filingDate, name, ownerType, position, symbol, transactionDate, transactionType (Sale or Purchase)
- **Per-person derived score or rank, as observed.**
  None on the endpoint.
- **Identifiers exposed.**
  - name and position strings; symbol
  - No person identifier scheme in the documented response
- **Per-filing conditions it states or computes.**
  - None. filingDate and transactionDate are both returned.
- **Code.**
  Official client libraries are listed (Python, Go, JavaScript, Ruby, Kotlin, PHP); the data itself is not open.
- **Data licence.**
  not verified (terms page not read).
- **API.**
  Premium-tier endpoint of the Finnhub REST API; a 30 calls/second limit applies on top of plan limits (docs page).
- **Funding or business model, as stated.**
  Paid API subscription tiers (premium access required for this endpoint); plan prices not read.
- **How it frames what a listing means.**
  not verified on the pages read.
- **Status at retrieval.**
  unknown (documentation page is live but carries no date)
- **Not verified.**
  - Data source agencies
  - Terms of use and data license
  - Plan pricing
  - Any disclaimer
  - Terms of use and data license (not read)
- **Confirmed by the second reader.** 7 claims, listed in the JSON.
- **Citations.**
  - <https://finnhub.io/docs/api/congressional-trading> (retrieved 2026-09-21): Endpoint path, parameters, premium requirement, response fields, rate-limit statement, client libraries

## Pages the first reader could not reach

- https://housestockwatcher.com/ (DNS ENOTFOUND)
- https://www.housestockwatcher.com/ (DNS ENOTFOUND)
- https://senatestockwatcher.com/ (DNS ENOTFOUND)
- https://www.senatestockwatcher.com/ (DNS ENOTFOUND)
- https://web.archive.org/web/2024/https://housestockwatcher.com/ (tool cannot fetch web.archive.org)
- https://web.archive.org/web/2024/https://senatestockwatcher.com/ (tool cannot fetch web.archive.org)
- https://house-stock-watcher-data.s3-us-west-2.amazonaws.com/data/all_transactions.json (HTTP 403)
- https://senate-stock-watcher-data.s3-us-west-2.amazonaws.com/aggregate/all_transactions.json (HTTP 403)
- https://github.com/timothycarambat/house-stock-watcher-data (HTTP 404)
- https://github.com/Quiver-Quantitative/quiverquant (HTTP 404)
- https://www.quiverquant.com/strategies/ (response exceeded 10 MB fetch limit)
- https://subversiveetfs.com/about/ (HTTP 404)
- https://unusualwhales.com/terms-of-service (HTTP 404; /terms read instead)
- https://unusualwhales.com/terms-and-conditions (HTTP 404)
- https://bioguide.congress.gov/search/bio/S000250 (HTTP 403)
- https://www.congress.gov/member/pete-sessions/S000250 (HTTP 403)
- https://site.financialmodelingprep.com/developer/docs/senate-trading-api (HTTP 403)
- https://www.capitoltrades.com/ via WebFetch (HTTP 429/403; read through the browser instead)
- https://www.joinautopilot.com/ via WebFetch (HTTP 429; read through the browser instead)

## Projects the second reader said were missing from this cluster

- **Financial Modeling Prep senate-trading / house-trading endpoints.** <https://site.financialmodelingprep.com/developer/docs/stable/senate-trading> A commercial API vendor with dedicated Senate and House trade and disclosure endpoints (senate-trading, house-trading, senate-latest, house-latest, by-name variants); the same kind of product as the Finnhub entry and more congress-specific. Surfaced by search; pages not read.
- **Barchart Politician Insider Trading.** <https://www.barchart.com/investing-ideas/politician-insider-trading> A widely used free tracker page of congressional buys and sells with per-politician search, updated twice daily per Barchart's own help text. Surfaced by search; page not read.
- **InsiderFinance Congress Trades.** <https://www.insiderfinance.io/congress-trades> A congress-trades tracker and politician-portfolio product. Surfaced by search; page not read.
- **Congresstrading.com.** <https://en.wikipedia.org/wiki/Congresstrading.com> Wikipedia describes it as a commercial database of congressional financial disclosures founded October 2020; a direct member of this cluster. Site not read; the Wikipedia article is the URL surfaced.
- **jeremiak/us-senate-financial-disclosure-data.** <https://github.com/jeremiak/us-senate-financial-disclosure-data> Named in the Senate Stock Watcher README as the repository its gaps are backfilled from; an open Senate disclosure dataset that sits beside the two stock-watcher repos. Not read.
- **Congress Stock Tracker (congressstock.com), GovTrades, TraderCongress, PelosiTracker.app.** <https://www.congressstock.com/> Four further tracker sites surfaced by a single search (also https://www.govtrades.com/, https://tradercongress.com/, https://pelositracker.app/). None read; listed so the survey can decide whether they merit entries rather than as verified members.
