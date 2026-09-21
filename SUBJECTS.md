# Subjects

*Who the register covers, why, and what it does not.*

Oath at its founding covers **major active federal officeholders and governors**, currently serving, whose office gives them meaningful power over the quality of life of Americans, over other peoples, or over other nations. It is a modern-active register. Working back through prior terms is deferred to a later phase, when the modern-active core is real.

The scope is stated here so it is testable and so a stranger can hold the register to it. [SPEC.md §S1](SPEC.md) requires every Oath-shaped register to have this document, mechanically applied. This is Oath's.

---

## 1. The rule

A subject is *in scope* if all three are true:

1. They currently hold an elective office in the United States that falls in one of the categories in §2 below, **or** they have been Senate-confirmed to an executive-branch office named in §2.
2. Their term has not ended as of the current build's date.
3. Their office is in the current congressional session (for federal legislators) or in a term that includes the current build's date (for others).

A subject who was in scope and whose term ends does not leave the register. Their record stays (Vow V: facts stay). Their office row is marked with its term end date; no new filings enter the register for them after that date; the register does not remove a byte of what was.

## 2. Categories of covered office

### 2.1 Federal, elective

- **President of the United States.**
- **Vice President of the United States.**
- **United States Senators**, all one hundred, current session.
- **United States Representatives**, all voting members of the current Congress. Non-voting delegates and the Resident Commissioner are covered on the same shape.

### 2.2 Federal, Senate-confirmed executive-branch (national-security, foreign-affairs, or economic-policy authority)

Covered because their office directly affects Americans and, in most cases, other peoples and nations. The list is deliberately narrow at the founding and expands only by pull request per §5.

- **Cabinet secretaries** of the executive departments: State, Treasury, Defense, Justice, Interior, Agriculture, Commerce, Labor, Health and Human Services, Housing and Urban Development, Transportation, Energy, Education, Veterans Affairs, Homeland Security.
- **Attorney General**, **Deputy Attorney General**, **Solicitor General**.
- **Director of National Intelligence**.
- **Director of the Central Intelligence Agency**.
- **Director of the Federal Bureau of Investigation**.
- **United States Trade Representative**.
- **Ambassador to the United Nations**.
- **National Security Advisor** (this is a White House staff role and not Senate-confirmed; included by exception for foreign-affairs authority; flagged as such in the row).
- **Chair of the Federal Reserve** and **Members of the Board of Governors of the Federal Reserve System**.
- **Chairs** of the Securities and Exchange Commission, the Commodity Futures Trading Commission, the Federal Trade Commission, the Federal Communications Commission, and the National Labor Relations Board.

### 2.3 Federal legislative leadership (already covered under 2.1, listed for salience)

Their office is a Senate or House seat and their inclusion is not a special exception; the register annotates leadership roles on the officeholder row where they apply.

- Speaker of the House. Majority and Minority Leaders. Whips.
- Senate Majority Leader. Senate Minority Leader. Whips.
- Committee Chairs and Ranking Members of the House and Senate.

### 2.4 State executive

- **Governors** of the fifty states, currently serving.
- **Lieutenant Governors** where independently elected (excluded where they run on a joint ticket, unless the state's disclosure regime files them separately). Documented state-by-state as coverage extends.

### 2.5 Deliberately deferred to a later phase

The following are important, and the register does not pretend they are not. They are deferred because coverage of the categories above must be real before the register can honestly add more.

- **State Attorneys General.** High national and international impact (multistate actions, foreign-litigation exposure). Added in the same phase as state legislators, per NEXT.md.
- **State legislators.** Coverage varies widely by state; the register extends state by state, prioritised by disclosure-regime completeness.
- **Federal judiciary.** The judiciary is not elected at the federal level. The financial disclosure regime is different (Judicial Financial Disclosure Reports under the Ethics in Government Act, adjudicated by the Judicial Conference). Adding the judiciary requires a distinct pipeline; it is a Phase 6+ decision.
- **Mayors, county executives, school boards, city councils.** Coverage below the state level is deferred indefinitely because the disclosure regimes are absent or too light in most jurisdictions to produce a useful record. Documented at the source level in SOURCES.md as adapters would land.

## 3. What is excluded, and why

**Former officeholders' current lives.** The register describes the record generated while the person held office. It does not follow them into private life, post-office consulting, book deals, or lobbying activities. Post-office activity is covered by other regimes (LDA registrations, if they lobby; agency post-employment rules under 18 U.S.C. § 207).

**Family members' independent private lives.** The register includes only the disclosures the officeholder themselves is required by law to make. When a filing includes a spouse's or dependent's assets by statute, those rows enter bound to the filing that disclosed them; independent family financial lives do not.

**Business counterparties, donors, lobbyists.** They are named on filings the officeholder makes. Their own conduct is not the register's subject.

**Candidates who lost.** The register covers officeholders. A candidate who did not win an office is not an officeholder. FEC filings during their campaign remain public at the FEC; the register does not synthesise them into a per-candidate page.

## 4. The mechanical check

Every officeholder row in the register carries an `office_id` that resolves to a row in `data/offices.ndjson`. Every `office_id` names a `category` from §2 above and a `term_start` and `term_end`. A tool at `tools/check-subject-scope.py` (planned, Phase 1) runs against the build and:

- Fails if any officeholder row has no matching office.
- Fails if any office row names a category not in §2.
- Fails if any office row's term has ended before the build date and the row's officeholder is being updated with new filings.

The check is a gate. It runs in CI.

## 5. Extending the scope

A pull request that adds a category to §2 above requires:

- **The reason.** Why this category belongs on the list Oath cares about. The founding criterion (impact on Americans and on other peoples or nations) is the test; a category that does not clearly meet it does not enter.
- **A Standard.** The disclosure regime that governs the category, added as a row in [STANDARDS.md](STANDARDS.md). A category with no public disclosure regime cannot be added to Oath; the register has nothing to work with.
- **A Source.** The primary source that publishes the disclosures, added to [SOURCES.md](SOURCES.md).
- **A Council session.** Per [COUNCIL.md](COUNCIL.md) §2; a change to §2 above is a category-of-subject change and Council-reviewed.
- **The maintainer's approval.** Per [BYLAWS.md](BYLAWS.md).

Removing a category is the same shape. Categories are only removed by pull request; the check in §4 fails a build if a category disappears without the removed rows being superseded (facts stay).

## 6. The retrospective plan (deferred)

The register at the founding is a modern-active record. Working back through prior Congresses, prior Administrations, and prior gubernatorial terms is deferred to Phase 6 or later. When it comes online:

- One Congress or Administration at a time, oldest cited backward from the current.
- Rows added the same way as modern rows: primary-source citation, retrieval timestamp, schema validation.
- No signals that fire against historical figures without a version bump that names the retroactive application.
- The [Council](COUNCIL.md) reviews the retroactive Signal application. Historical firings are not automatic; they are a distinct editorial decision.

Retrospective coverage is not a small thing. Doing it early would mean shipping historical Findings before the modern pipeline is proven; that is the specific failure mode a foundation-first project has to avoid. First the arrow flies straight in the present. Then the historical work.

## 7. Why this scope

The register covers the officeholders whose sworn commitment is publicly disclosed, whose office gives them power the reader is affected by, and whose disclosure regime is complete enough to produce a checkable record. That is the intersection of three things: **public sworn commitment**, **material impact**, and **checkable disclosure**. Everything in §2 satisfies all three. Everything in §2.5 satisfies one or two but not the third yet, and is deferred until it does.

The register does not cover officeholders whose disclosure regime is too light to work with, because there is nothing to check. It does not cover officeholders whose office gives them no material impact on quality of life or on other nations, because the register would then be doing the reader's editorial work for them. It does not cover retired officeholders' current lives because that is not the scope of any oath.

The scope is not the argument for the register. The scope is the answer to *"who is this about?"* so that the argument can proceed cleanly.
