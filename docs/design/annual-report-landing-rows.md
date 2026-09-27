# The annual Signal's rows in the sealed doctrine, written and waiting

*Written 2026-09-27, read at the source that day, and corrected by the Council's second reading
([record](../council/2026-09-27-the-annual-report-signal-built.md)). STANDARDS.md and SOURCES.md are
sealed doctrine, so these rows enter them only in the sealed build that first carries the annual
Signal, together with its definition moving from `docs/design/` to `docs/signals/`. Until then they
live here, so they outlast any one session's working tree. When they land, this file goes.*

## STANDARDS.md: S.1, replacing the section as it stands

```markdown
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
```

## STANDARDS.md: S.2, the one sentence that changes

In **Codified**, the last sentence becomes: "The quotation was returned by a search of the Code's publishers on 2026-09-26, and read at the source, in these words, on 2026-09-27."

## SOURCES.md: F.1, three bullets

The **Retention** bullet becomes:

```markdown
- **Retention.** A Member of Congress's reports are kept available to the public until six years after the individual ceases to be a Member, and every other report for six years after its receipt; after that a report is destroyed unless needed in an ongoing investigation (5 U.S.C. § 13107(d), read at the source 2026-09-27). The register keeps the SHA-256 of every document it reads, beside what it read, and not the document itself; an outside witness for each document a Finding rests on is owed (INVARIANTS §16).
```

A bullet is added after **The documents, read 2026-09-23**:

```markdown
- **The documents' own headers, read 2026-09-27.** An e-filed report names itself in its header: *Filing Type* (Annual Report, Amendment Report), *Status*, *Filing Year*, *Filing Date*, and the date its last line says it was digitally signed. The Committee's extension form prints no *Filing Type* line; it prints *Status*, *Filing Year*, *Request Date*, *Extension Length*, *Original Due Date*, *New Due Date* and *Report Type Due*. In the build read that day, 399 documents coded `O` and attributed to members print *Annual Report* and *Member*, and 229 coded `X` print an extension's fields. On 398 of the 399 annual reports whose header the register read in the build that day, the Filing Date, the signature date and the index date were the same day; on one, the index gives the day before the date the report prints twice, which is the register's only evidence on the filing system's clock (`docs/wanted/wanted.ndjson`, `wt:the-clerks-filing-date`, `wt:the-form-codes`, `wt:the-filing-systems-clock`). The adapter reads these lines from every document coded other than `P` that it fetches, only where a labelled line says one thing, and records them on the row as `printed` (`schemas/filing.schema.json`), with the document's SHA-256 as the row's `source.content_hash`. The register still interprets no index code: a Signal about a kind of report reads what the report prints about itself.
```

The **Adapter status** bullet becomes:

```markdown
- **Adapter status.** Index layer and transaction-report documents landed, `src/adapters/house-fd/`. Annual reports and extension forms: their headers are read; what an annual report discloses is not.
```
