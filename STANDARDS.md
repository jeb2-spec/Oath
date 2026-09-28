# Standards

The legal and regulatory frameworks against which every Signal in Oath is defined. Every row in this file cites a primary source. When a Signal fires, it cites a row here; when a row here is cited, the reader can walk from Signal → Standard → statute or regulation, in three clicks and no dependence on this project.

This file grows as coverage extends. Federal Standards are documented first. State analogues are added per jurisdiction as ingest for that state comes online.

## Constitutional

### C.1. Oath of Office
- **Source.** U.S. Const. Art. VI § 3 (the oaths clause); Art. II § 1 cl. 8 (the presidential oath); 5 U.S.C. § 3331 (statutory federal officers' oath).
- **Text of the federal officers' oath (5 U.S.C. § 3331).** *"I, ___, do solemnly swear (or affirm) that I will support and defend the Constitution of the United States against all enemies, foreign and domestic; that I will bear true faith and allegiance to the same; that I take this obligation freely, without any mental reservation or purpose of evasion; and that I will well and faithfully discharge the duties of the office on which I am about to enter. So help me God."*
- **What it binds.** Every federal officer, on assumption of office. State officers are bound by their state's own analogue, defined in each state constitution.
- **Why it is C.1.** The oath is the single act that turns a citizen into an officeholder. It is the standard every other standard in this file implements.

### C.2. Foreign Emoluments Clause
- **Source.** U.S. Const. Art. I § 9 cl. 8.
- **Text.** *"No Title of Nobility shall be granted by the United States: And no Person holding any Office of Profit or Trust under them, shall, without the Consent of the Congress, accept of any present, Emolument, Office, or Title, of any kind whatever, from any King, Prince, or foreign State."*
- **What it prohibits.** Any Officeholder accepting any present, emolument, office, or title from any foreign state, without congressional consent.
- **Scope note.** The clause has never received a Supreme Court merits ruling; the Trump-era litigation (CREW v. Trump, D.C. v. Trump, Blumenthal v. Trump) was dismissed on standing grounds in Trump v. CREW, 141 S. Ct. 1262 (2021). Signals defined against this Standard surface the receipt of the prohibited category, not the legal conclusion.

### C.3. Domestic Emoluments Clause
- **Source.** U.S. Const. Art. II § 1 cl. 7.
- **Text.** *"The President shall, at stated Times, receive for his Services, a Compensation, which shall neither be increased nor diminished during the Period for which he shall have been elected, and he shall not receive within that Period any other Emolument from the United States, or any of them."*
- **What it prohibits.** The President receiving any emolument other than the fixed compensation, from the United States or any State.
- **Scope note.** Applies only to the President.

## Statutory

### S.1. Ethics in Government Act of 1978
- **Source.** Title I of the Ethics in Government Act of 1978 (Pub. L. 95-521), which Pub. L. 117-286 (27 December 2022) moved from 5 U.S.C. app. 4 into 5 U.S.C. chapter 131 (<https://uscode.house.gov/view.xhtml?req=granuleid:USC-prelim-title5-chapter131&num=0&edition=prelim>). The sections below were read at uscode.house.gov on 2026-09-27.
- **Regulator.** Office of Government Ethics (OGE) for the Executive Branch; House Committee on Ethics for the House; Senate Select Committee on Ethics for the Senate.
- **What it requires.** Annual public financial disclosure by senior federal officers, on OGE Form 278e (Executive Branch) or its Congressional analogues, covering assets, income, transactions, positions, liabilities, gifts, and reimbursements above defined thresholds.
- **Who, and by when.** 5 U.S.C. § 13103(d): an individual described in subsection (f) who *"performs the duties of the position or office for a period in excess of 60 days in that calendar year shall file on or before May 15 of the succeeding year"* a report for it. Subsection (f)(9) lists *"a Member of Congress as defined in section 13101"*, and § 13101 defines a Member of Congress as *"a United States Senator, a Representative in Congress, a Delegate to Congress, or the Resident Commissioner from Puerto Rico."*
- **Extensions.** § 13103(g)(1): *"Reasonable extensions of time for filing any report may be granted under procedures prescribed by the supervising ethics office for each branch, but the total of such extensions shall not exceed 90 days."* § 13103(g)(2) extends the date, for an individual serving in or in support of the Armed Forces in a designated combat zone, to 180 days after the later of the last day of that service or of hospitalization from it.
- **Fee.** § 13106(d): an individual who files a required report *"more than 30 days after the later of"* the date it is required to be filed or, where an extension is granted under § 13103(g), *"the last day of the filing extension period"*, pays a filing fee of $200, at the direction of the supervising ethics office, which may waive it. The register computes no fee for anyone.
- **Regulator's instructions.** The House Committee on Ethics' Instruction Guide for calendar year 2025 (<https://ethics.house.gov/wp-content/uploads/2026/07/7-8-2026-2025-Published-Instruction-Guide.pdf>, read 2026-09-27) states that an annual report whose due date falls on a weekend or federal holiday is due the next business day; that an extension deadline 90 days from the original due date is not moved for a weekend or holiday; and that *"pursuant to the STOCK Act, the Clerk is required to post notice of all FD extensions granted for Members and Candidates on the public website of the Office of the Clerk."* The federal holidays the Guide's rule turns on are those of 5 U.S.C. § 6103(a) (<https://uscode.house.gov/view.xhtml?req=granuleid:USC-prelim-title5-section6103&num=0&edition=prelim>, read 2026-09-27), on the days observed.
- **Reporting thresholds (current).** Assets over $1,000; income over $200 from any source; transactions over $1,000; liabilities over $10,000; gifts aggregating over $480 from any source in a calendar year.
- **Retention.** § 13107(d): a report is retained by the office it is filed with, and made available to the public, for a Member of Congress, *"until a date that is 6 years from the date the individual ceases to be a Member of Congress"*, and for every other report for 6 years after its receipt; after that it is destroyed unless needed in an ongoing investigation. The register keeps the SHA-256 of every document whose header it reads, beside what it read, and not the document: once the Clerk destroys a report, its hash confirms a copy kept elsewhere and cannot stand in for one, and an outside witness for each document a Finding rests on is owed (INVARIANTS §16).
- **Scope note.** The Signal defined against this Standard ([docs/signals/annual-report-after-extension-limit.md](docs/signals/annual-report-after-extension-limit.md)) compares the date on a Member's annual report with the latest date any extension the statute allows could reach. Whether a report was late, whether an extension was granted, and what follows, are for the Committee on Ethics, and the register reads none of its decisions.

### S.2. Stop Trading on Congressional Knowledge (STOCK) Act of 2012
- **Source.** Pub. L. 112–105 (<https://www.govinfo.gov/app/details/PLAW-112publ105>, read 2026-09-23).
- **Regulator.** House Committee on Ethics; Senate Select Committee on Ethics.
- **What it requires.** Members of Congress and covered staff report each purchase, sale, or exchange of any stock, bond, commodity future, or other security involving amounts over $1,000, whether the asset is owned by the member, the member's spouse or a dependent child (the Committee's instructions), within 30 days of receiving notice of the transaction and no later than 45 days after the transaction date. The Committee's instructions keep some transactions off these reports; they are named below.
- **Penalty.** The Committee's form for these reports says: *"A $200 penalty shall be assessed against anyone who files more than 30 days late."* (CY 2025 form, read 2026-09-21; recorded in [docs/related-work/data/watchdogs.json](docs/related-work/data/watchdogs.json)). Its filing-deadlines page, read the same day, adds that the fee may be waived in exceptional circumstances. The register computes no fee for anyone and sees none of the Committee's decisions. Separately, the Ethics in Government Act provides for penalties for knowingly and willfully falsifying a report or failing to file one (5 U.S.C. § 13106; the form cites 18 U.S.C. § 1001); nothing about the date a report is dated says anything about either.
- **Codified.** 5 U.S.C. § 13105(l), in Title I of the Ethics in Government Act as it now stands in 5 U.S.C. chapter 131 (<https://uscode.house.gov/view.xhtml?req=granuleid:USC-prelim-title5-section13105&num=0&edition=prelim>): a report of a transaction is due *"not later than 30 days after receiving notification of any transaction required to be reported under section 13104(a)(5)(B), but in no case later than 45 days after such transaction."* The quotation was returned by a search of the Code's publishers on 2026-09-26, and read at the source, in these words, on 2026-09-27.
- **Regulator's instructions.** The House Committee on Ethics states the deadline as the earlier of 30 days from being made aware of the transaction or 45 days from the transaction (<https://ethics.house.gov/financial-disclosure>, read 2026-09-23). Its Periodic Transaction Report form and instructions for CY 2025 (<https://ethics.house.gov/wp-content/uploads/2026/02/Final-CY-2025-PTR-Form-1.pdf>, read 2026-09-21 and 2026-09-23; the reading of 2026-09-21 is recorded in [docs/related-work/data/watchdogs.json](docs/related-work/data/watchdogs.json)):
  - cover transactions in *"stocks, bonds, commodities, futures, or other securities (e.g., cryptocurrencies)"* over $1,000 by the filer, the spouse or dependent children;
  - exclude real property, widely held investment funds, transactions solely between the filer, the spouse and dependent children, the Thrift Savings Plan, stock splits, bequests and inheritances, and bank account openings and deposits;
  - state that the due date is not extended for a weekend or holiday;
  - define the columns the register carries: the type of transaction (purchase, sale, partial sale, exchange); the SP/DC/JT ownership column, which a filer *"may, but [is] not required to"* mark; the category of value of the total purchase or sale price (or the fair market value of an exchange); and the dates of transaction and of notification.

  Its memorandum of 30 January 2023 (<https://ethics.house.gov/wp-content/uploads/2023/01/FINAL-PTR-Due-Date-Pink-Sheet.pdf>), whose text the same record extracts, lists ETFs, mutual funds, real property, bank accounts, certificates of deposit, 529 plans, 401(k) rollovers and the Thrift Savings Plan as reported on the annual report only. It also states that no extension is available for these reports, and sets the fee: a minimum of $200 per late report after a 30-day grace period.
- **Returned by a search and not yet read at the source.** Two sets of statements were found only by search.
  - *The current wording, restated.* A later memorandum on the same subject (<https://ethics.house.gov/wp-content/uploads/2024/06/PTRPinksheet_current.pdf>) and the Committee's instruction guides for calendar years 2023, 2024 and 2025 state the same rule as the CY 2025 form. A search returned them on 2026-09-26. They add that a report filed electronically is timely on or before the due date, and one on paper when postmarked by the last business day before it. Whether the Committee's table puts government securities on these reports is not settled in anything read here.
  - *An older rule.* Earlier instructions said otherwise, as a search returned them: the CY 2017 instruction guide and the CY 2021 form moved a due date on a weekend or holiday to the next business day, and a 45th day to the last business day before it.

  The first Signal below reads the rule the CY 2025 form states. It evaluates no deadline before 2025 and no asset the instructions do not plainly put on these reports ([docs/signals/stock-act-ptr-after-deadline.md](docs/signals/stock-act-ptr-after-deadline.md)).
- **Scope note.** The STOCK Act does *not* prohibit congressional trading in general; it prohibits trading on material non-public information obtained through congressional duties (already covered by insider trading law) and it requires timely disclosure. The Signals defined against this Standard describe the reports it requires against the dates it sets. Whether a report was late, and what follows from it, is for the Committee on Ethics, and the register sees none of its decisions.

### S.3. Federal Bribery, Graft, and Conflicts of Interest
- **Source.** 18 U.S.C. Ch. 11, in particular:
  - § 201 (bribery of public officials)
  - § 203 (compensation to Members of Congress for representational services)
  - § 205 (activities of officers and employees in claims against the United States)
  - § 208 (acts affecting a personal financial interest)
- **Regulator.** Department of Justice; House and Senate ethics committees for referral; OGE for Executive Branch guidance.
- **Scope note.** § 208 is the federal *actual* conflict-of-interest criminal statute; it applies to Executive Branch officers and employees participating personally and substantially in matters affecting their financial interest. Signals defined against this Standard surface Executive Branch actions taken in matters implicating disclosed financial interests.

### S.4. Federal Election Campaign Act (as amended)
- **Source.** 52 U.S.C. § 30101 et seq. (also BCRA and successor amendments).
- **Regulator.** Federal Election Commission (FEC).
- **What it requires.** Registration and periodic disclosure by candidates for federal office and their committees, of contributions received and expenditures made, on FEC Forms 3 (candidate committees) and 3X (other political committees).
- **Retention.** FEC filings are permanently public.

### S.5. Lobbying Disclosure Act of 1995
- **Source.** 2 U.S.C. § 1601 et seq., as amended by the Honest Leadership and Open Government Act of 2007 (Pub. L. 110–81).
- **Regulator.** Secretary of the Senate; Clerk of the House.
- **What it requires.** Quarterly disclosure by lobbyists and lobbying firms of their clients, issues, and expenditures; semiannual LD-203 disclosures of political contributions by registered lobbyists.
- **Relevance to Oath.** Lobbying filings identify the counterparties named in Signals bearing on legislation the Officeholder acted on.

### S.6. Hatch Act
- **Source.** 5 U.S.C. §§ 7321–7326.
- **Regulator.** Office of Special Counsel (OSC).
- **Scope note.** The Hatch Act's core restrictions apply to federal *employees*; elected federal officials (the President, Vice President, Members of Congress) are largely outside its scope. Oath's coverage under this Standard is limited to appointed officials for whom the Act applies.

## Regulatory

### R.1. Standards of Ethical Conduct for Executive Branch Employees
- **Source.** 5 CFR § 2635.
- **Regulator.** Office of Government Ethics (OGE), with agency ethics officials.
- **Key subparts.**
  - § 2635.101. Basic obligation of public service, including § 2635.101(b)(14): *"Employees shall endeavor to avoid any actions creating the appearance that they are violating the law or the ethical standards set forth in this part."* The *appearance* standard is load-bearing throughout Oath's signal definitions.
  - § 2635 Subpart B. Gifts from outside sources.
  - § 2635 Subpart C. Gifts between employees.
  - § 2635 Subpart D. Conflicting financial interests, implementing 18 U.S.C. § 208.
  - § 2635 Subpart E. Impartiality in performing official duties (the *covered relationships* rules).
  - § 2635 Subpart F. Seeking other employment.
  - § 2635 Subpart G. Misuse of position.
- **Scope note.** These regulations bind Executive Branch employees, including political appointees. Members of Congress and Congressional staff are governed by their chambers' own rules.

### R.2. Congressional Ethics Rules
- **Source.**
  - House: *Rules of the House of Representatives*, Rule XXIII (Code of Official Conduct); *House Ethics Manual* (Committee on Ethics).
  - Senate: *Standing Rules of the Senate*, Rule XXXVII (Conflict of Interest); *Senate Ethics Manual* (Select Committee on Ethics).
- **Regulator.** House Committee on Ethics; Senate Select Committee on Ethics; Office of Congressional Ethics (OCE, House-side referral body).
- **Scope note.** Congressional rules parallel and in some cases exceed the Executive Branch standards. Where a Signal derives from a chamber rule, the rule and its manual section are cited on the Signal definition.

## State analogues

State ethics laws vary substantially. As Oath's coverage extends to state officeholders, the Standards for each state are added here in the form:

- **[STATE]-1. [Statute name].** Citation, regulator, what it requires, retention, scope.
- **[STATE]-2. [State ethics commission rules].**
- **[STATE]-3. [State campaign finance act].**

The first two states covered will be documented here in full. Subsequent states follow the same shape.

## How to add a Standard

Standards are added by pull request. The template requires:

1. The primary source (statute, CFR section, constitutional clause, or state analogue).
2. The regulator or enforcing body.
3. A one-paragraph description of what it requires or prohibits.
4. The retention rule for filings made under it.
5. Any scope notes that constrain its application.

A Standard is *not* an opinion about what the law ought to be. It is a citation to what the law is, in a form a Signal can point at.
