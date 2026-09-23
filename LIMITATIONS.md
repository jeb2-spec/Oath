# Limitations

Stated in the order a careful reader would raise them. A page that hides its threats to validity is the same failure as a record that hides its corrections. Anything worth building carries what it cannot do beside what it can.

This is a living file. As Oath encounters new limitations in the wild (a source that goes dark, a state whose regime cannot be reconciled to the schema, a class of Signal the register cannot honestly compute) the limitation is recorded here in the same commit that documents the encounter.

## 1. Presence is not proof

An Officeholder appears in the register because they hold or held an elective Office. Nothing more. A Signal firing describes a condition that the law itself recognises as concerning; it does not adjudicate one, and the presence of the condition is not evidence that a violation has occurred. Every published surface must carry this frame. Any downstream use of the register that strips it (an aggregator that shows only fired Signals, a headline that reads a description as a verdict) is a misuse the project cannot prevent, but is one the project's own surfaces will not commit.

## 2. "Appearance" is subjective by design

5 CFR § 2635.101(b)(14) asks officials to avoid the appearance of impropriety in the eyes of a reasonable person. That standard is what much of Oath measures against, and it is subjective by construction. The project surfaces conditions in which the appearance question plausibly arises; it does not resolve the question. Where possible, a Signal's definition will name the specific facts that produced the appearance, and a Finding will link to them. The reader draws the line.

## 3. State variance is large

Fifty states run fifty regimes. California, New York, and Texas publish machine-readable disclosures; other states require paper filings retrieved in person from a state ethics commission. Some states require annual disclosure by legislators; some require it only from statewide officers; some do not require it at all. Coverage will be uneven, and the state-coverage matrix will be maintained in [SOURCES.md](SOURCES.md) with dates last verified. A state's absence from a Finding does not mean its officeholders are without conditions worth surfacing; it may mean the source cannot be ingested at all.

## 4. Local offices are largely unregulated

Many county, municipal, and school-board offices have no financial disclosure requirement, or one so light it produces no useful record. Coverage below the state level will be sparse, and the register will not attempt to invent it. Local Officeholders may be listed with no Findings, or omitted entirely where the source does not exist. Neither absence should be read as endorsement.

## 5. Blind trusts obscure holdings by design

A qualified blind trust under 5 U.S.C. app. 4 § 102(f) removes the Officeholder's knowledge of the trust's holdings, and the register cannot pierce it. The existence and type of the trust are recorded; the underlying holdings are not, because they are not disclosed. This is the intended effect of the trust as a legal instrument, and the register respects it.

## 6. Coverage is bounded by digitisation

Retrospective coverage runs back only to the earliest date the primary source publishes electronically. Earlier filings exist on paper in agency archives. The register will note their existence where the archive is known; it will not synthesise their contents. Where a source's electronic corpus contains scanned images without extracted text, extraction quality is bounded by the OCR pipeline used, and the extraction confidence is recorded on the row.

In the House transaction reports the register has read so far, 54 of 417 are scanned paper filings; the register captures and hashes them and reads nothing from them, so their transactions are absent from `data/transactions.ndjson` and their filing rows say so through a hash without an extraction. What the register does read, it carries as printed: 31 transactions carry a notification date earlier than the transaction date, and a handful carry years no filing period covers. These are the filer's entries, not the register's, and the register does not correct them.

## 7. Late and amended filings

Filings arrive late. Filings are amended. A Finding computed against a filing set is valid as of the build; a later filing or amendment may change the underlying facts. The register will surface the amendment (as a new row) and, where the amendment invalidates a Finding, will supersede the Finding in the following build.

## 8. Family financial information is out of scope

The project excludes financial details of Officeholders' spouses and children beyond what the Officeholder is themselves required by law to disclose. Where the Officeholder's filing includes a spouse's holdings (as many federal filings do), those rows enter the register bound to the filing that discloses them. Independent private financial lives of family members do not.

## 9. Private citizens are out of scope

Only Officeholders in the sense defined in the [README](README.md) §3 appear as subjects in the register. Donors, lobbyists, business counterparties, and family members are named only where they appear on a Filing the Officeholder is required by law to make. A donor's or counterparty's independent activity is not the register's subject.

## 10. Aggregators are not primary

OpenSecrets, ProPublica *Represent*, Ballotpedia, LegiStorm, Follow the Money, MapLight, Capitol Trades, and other aggregators do valuable work and are cited throughout. They are not the sole basis for any Finding. Where a Finding cites an aggregator, it also cites the primary source the aggregator drew from; where the two disagree, the primary source wins and the disagreement is recorded.

## 11. The register is silent by default

A Signal fires only where the record contains the condition it defines. Silence in the register is a legitimate result and is recorded as such: an Officeholder for whom no Signal has fired is an Officeholder for whom, on the ingested record and the defined Signals, no Signal has fired. It is not a certification of ethics, and no page will imply that.

An algorithm that has to say *something* about every Officeholder is an algorithm that will start inventing. Oath does not.

## 12. Signal definitions carry the project's judgement

A Signal is a definition, not a discovery. Which conditions the project defines as signals, and which it does not, reflects the project's judgement about what the record can honestly surface. That judgement is fallible. Signal definitions are visible, versioned, and open to challenge. A Signal that should not fire, or should fire in cases it does not, is a bug and a PR waiting to happen. Silent redefinition is prohibited.

## 13. Integrity is not accuracy

A tamper-evident record of a mistake is still a mistake, held perfectly still. The Seal proves the register is unchanged since the build. It does not prove any statement in the register is true. Accuracy comes from the underlying source; a mistake in the primary filing propagates here, and the register will surface corrections of its own in the manner of [errata](https://github.com/jeb2-spec/errata).

## 14. Adversarial use

A comprehensive, structured, machine-readable register of officeholders' financial conditions is dual-use. It supports the intended use (a reader reconciling a record against a standard) and it can support adversarial uses (targeted harassment, opposition research, misrepresentation of quiet Signals as damning ones). The project's surfaces are designed for the intended use, and the frame stays on every page. But the data is public by design and by law, and once distributed cannot be recalled. This limitation is stated because it is true, not because the project can eliminate it.

## 15. One project, day zero

As of the founding build, the register is scaffolding. No data has been ingested. No Signal has fired. No Finding has been published. Nothing about the project's practice can be validated yet from this repository. Everything stated in this file is a commitment; nothing here is yet a result.

The point of stating that plainly, at the founding, is that it does not stay true. When it stops being true, this section changes.
