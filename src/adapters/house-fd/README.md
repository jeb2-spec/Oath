# house-fd

The adapter for the U.S. House of Representatives financial disclosure record, [SOURCES.md](../../../SOURCES.md) F.1. Two stages, run in order:

```bash
python src/adapters/house-fd/fetch.py --year 2025
python src/adapters/house-fd/build.py --year 2025
```

`fetch.py` retrieves and records. `build.py` reads what was recorded and writes canonical rows. Nothing in `build.py` touches the network, so a build is reproducible from a capture by anyone holding the same bytes.

## What it reads, and why two files

| File | Publisher | What it is authoritative for |
| --- | --- | --- |
| `MemberData.xml` | Office of the Clerk | who holds a seat |
| `<year>FD.zip` | Office of the Clerk | what was filed |

The roster is the piece the project was missing. It carries a `bioguideID` for every sitting member, which is the identifier the field already agrees on ([RELATED.md](../../../RELATED.md) §5.1), and it comes from the Clerk rather than from a community dataset, so identity rows satisfy [INVARIANTS.md](../../../INVARIANTS.md) §5 without an aggregator anywhere in the chain.

It also distinguishes a seat from the person in it. On the retrieval recorded here the roster holds 441 seats, 439 filled and 2 vacant, and the vacant rows carry no name, no identifier and no sworn date. That maps exactly onto Oath's split between an Office and an Officeholder.

## The join, and why it refuses so much

The filing index carries no person identifier. A filing reaches an officeholder only through a name and a state-district, and two measured facts decide the design.

**Most of the index is not officeholders.** Of 2,939 rows in the 2025 index, 1,718 sit at a real seat under a surname that is not the sitting member's. They are candidates for that seat. [SUBJECTS.md](../../../SUBJECTS.md) §3 excludes candidates who did not win, so the majority of the file is out of scope and has to be dropped rather than ingested. An adapter that trusted the state-district column would have put roughly 1,700 non-officeholders into the register.

**Seats move and names differ.** Two sitting members hold each other's former districts between the two files. Four carry diacritics the index drops. Four more have multi-part surnames the two sources split differently, so the roster's "Watson Coleman, Bonnie" is the index's "Coleman, Bonnie Watson".

So the join matches on the name and treats the seat as corroboration, never the reverse. A row is accepted when the roster's name tokens equal the index row's or are contained in them, after folding away diacritics, punctuation, honorifics and generational suffixes. Everything else is written to `data/rejected/house-fd/` with the reason.

The hardest refusal is deliberate. Where a surname matches a sitting member but the given names disagree, the row is not accepted on the name. That case is usually the roster's common name against the index's legal name, "Bill" against "William", and it is usually the same person. Usually is not the standard the Charter's fourth vow sets, and the same pattern also describes a relative running for the seat the incumbent holds. The adapter never guesses one into the register.

**The document decides those rows, where it can.** When the index places such a row at the member's own seat, `documents.py` captures the document behind it and `build.py` reads its header, which the Clerk's e-filing system prints on every report: the filer's name, a filer status, the seat as `State/District`, and the `Filing ID`. The member the surname points at is found by the surname's words: a member is near when every word of the roster surname is in the row's surname, so a shared particle (De, Van) is not a shared name; the one near member, or, where several are near (Johnson, Davis), the one of them who holds the seat the row names. The seat corroborates the pick and decides nothing by itself. A member whose district changed between Congresses is reached by the name route, which tolerates a printed seat that differs from the roster's and notes it, and not by this one, which needs the seat to corroborate; such a member's held rows sit at the former seat, and the member's page says so without naming it. The row is attributed when the document prints Status `Member`, the member's seat, this row's DocID as its Filing ID, and a filer name carrying the roster surname, and the index dates the filing no earlier than the swearing-in the roster records for this Congress. The filing row then carries the whole basis in `notes`: what the index wrote, what the document printed, what the roster names the holder. Everything else is held for a person, with what the document printed quoted on the row: a document that prints another filer status (the form prints `Congressional Candidate` for a candidate), a document with no Filing ID line (scanned paper, or a form that prints none), a document printing another seat or another Filing ID, or a filing the index dates before the swearing-in. The register never says who a filer is not. Whether a report a member filed as a candidate, before the swearing-in, belongs on the member's page is a question for [SUBJECTS.md](../../../SUBJECTS.md) that is not yet decided; such rows are held, not attributed and not refused. The date gate exists so that a same-surname predecessor at the same seat within the year would not pass; the roster records one sworn date per seat, the swearing-in of this Congress, so a returning member's own filing dated in the first two days of January is held by design and can be adjudicated by hand with the document as evidence. On 2026-09-23 the rows so read came to 101 attributed (37 members; on reading, every printed name is a form of the roster's, which is an observation, not a gate beyond the surname test), 28 held with no Filing ID line, 6 held with Status `Congressional Candidate`, and 1 held on the date. A batch of 126 hand adjudications proposed before the documents were read would have attributed four rows whose documents print Status `Congressional Candidate` under given names that differ from the members'; the Council's first reading also found that the pick, when it required a surname unique in the chamber, never reached six members' rows at all, and the seat-corroborated pick above is the repair; its second reading found the first-word pick treating a shared particle as a shared surname, and the word-exact pick is that repair.

## What one retrieval produced

| | |
| --- | --- |
| Seats | 441 |
| Officeholders | 439 |
| Filings attributed | 1,197 |
| Of them by the document's own header | 101 |
| Officeholders with at least one filing | 428 |
| Index rows not attributed | 1,737 |
| Sitting members with nothing attributed | 11 |
| Transaction reports read | 409 of 463 |
| Transactions written | 7,346 |

Of the rows not attributed, 1,575 match no sitting member's name, which is the expected shape of a file that is mostly candidates. The other 162 carry a sitting member's surname with a different given name and are held for a person: 127 at a seat other than the member's; 28 at the member's own seat whose documents carry no Filing ID line (scanned paper, or a form that prints none; on reading, all 28 yield no text); 6 at the member's own seat whose documents print Status `Congressional Candidate`, quoted on the row; 1 dated by the index two days before the swearing-in the roster records. The 35 held at a member's own seat cite the document that was read. The index also lists 4 DocIDs more than once, identically (one of them three times); the register keeps one row for each, and that row says so, whether it was attributed or set aside.

Those 11 quiet members and those 164 held rows are the adapter's known incompleteness. They are counted in `data/meta.json` rather than hidden. Closing them is a person's work, one cited adjudication at a time, and the path is in [CONTRIBUTING.md](../../../CONTRIBUTING.md).

## Form codes are carried, not interpreted

The index labels each filing with a single letter. Twelve appear in the 2025 file and no Clerk page read on 2026-09-22 defines them, which SOURCES.md F.1 already records. The adapter stores the letter verbatim in `source_form_code` and sets `form_type` to `other`.

The one exception is `P`, mapped to `House-PTR`. That is not an inference from the letter. The Clerk serves those documents from a `ptr-pdfs` path while every other code is served from `financial-pdfs`, so the publisher's own filing system makes the distinction. When a Clerk document defining the remaining codes is found, it goes in SOURCES.md and the mapping follows it.

## Reproducing a build

`fetch.py` writes `capture.json` beside the bytes, recording for each retrieval the URL, the retrieval time, the SHA-256 of the bytes, and the `Last-Modified` the server reported. Every row cites that record, so a reader can ask which retrieval a row came from and hash the file themselves.

The index is not an annual artefact. The 2025 archive was last modified partway through 2026, so it is a live file that grows as filings arrive. A build is a statement about one retrieval, not about a year, which is what the seal is for.

Two builds from one capture produce byte-identical output. The rejected file and the run record are named for the captures they came from (twelve hex characters of the hash of both files' hashes), never for the day the build ran, so an unchanged source is an unchanged tree and the seal holds. Rejections from earlier captures live in git history.

## The documents

`documents.py` captures the document behind each filing the same way `fetch.py` captures the index: exact bytes, response headers, SHA-256 and retrieval time, recorded in `data/cache/house-fd/docs/captures.json`. It fetches only the codes asked for (default `P`, the transaction reports) and can be limited to a delegation with `--seats NC`, which is how the reader was piloted on North Carolina's twenty-one reports before it ran on the chamber.

`ptr.py` reads a captured transaction report as pure functions over one document. The document is a table, and it is read as a table: every text fragment pypdf reports carries its position on the page, fragments sharing a baseline form a visual line, and the column a fragment sits in says what it is. A transaction begins on the line that carries a type in the Transaction Type column, with the owner code, the asset's first line, the two dates and the band's first line beside it; further asset lines and the band's second line sit beneath; then come the form's labelled lines (filing status, subholding of, location, description, comments), which may wrap. Reading by position is what makes a page break falling inside a transaction, a label that wraps, and an amendment whose table sits sixteen points to the right all read the same. The register learnt each of those shapes from the documents themselves on 2026-09-23, and the reader's tests carry them.

Two checks the index could never make happen here. The Filing ID printed in the document must be the DocID the index gave it, and the seat printed in the document must be the roster seat of the officeholder it was attributed to. A document that disagrees on the Filing ID refuses the filing row rather than guessing. A document that disagrees on the seat refuses the row unless its printed name confirms the officeholder by the join's own test, in which case the row stands and carries the discrepancy in `notes`: a filer's profile can print the seat held in the previous Congress, and three reports do. A third check is per transaction: the asset text must end in the Clerk's bracketed asset code, or the row's notes say the asset is unconfirmed. A document with no Filing ID line is a scanned paper filing; the row stands, the document's hash is recorded, and nothing is read from it.

On the chamber-wide run of 2026-09-23, 409 of the 463 transaction reports were read (3 with the seat discrepancy noted), 54 were scanned and not read, none was refused, and 7,346 transactions were written, every asset confirmed by its tag. A further 55 documents behind rows the header attributed are annual reports and other forms: their headers were read and their hashes recorded, and the register does not yet read their schedules. `build.py` does the reading from the captures, sets `content_hash` and `extraction_confidence` on the filing rows it read, and writes `data/transactions.ndjson`. Each transaction is shown on its officeholder's page, as filed and grouped by report, a surface that goes to the Council before it publishes; the columns are the ones the Committee on Ethics form defines, and the form's ownership column is optional, so a blank is carried as `unmarked` (3,505 rows), never as the filer's own. The register said `self` for those rows in build 0003 and corrected it in build 0004 on reading the form.

This is the register's one dependency outside the standard library: `pypdf`, declared in `pyproject.toml` under `extract`. The verifier never imports it.

## Run records

Every build writes one line to `data/adapter-runs/house-fd-<year>-<capture key>.ndjson`, and removes the record of any earlier capture, so the tree carries one run record per adapter and year, named for the same key as the set-aside file, and earlier records live in git history with the builds they sealed. The line carries: the adapter, the two captures with their URLs, retrieval times, hashes and last-modified headers, the hash of the adjudication file that shaped the build, the documents block (the manifest hash and how many documents were captured, read, read with a seat discrepancy, unreadable, refused, and how many transactions they yielded), the counts (seats, filled, vacant, index rows, accepted, adjudicated, officeholders with a filing, quiet, rejected), and the rejections by reason. It is sealed with the rows, so the provenance of a build is inside the build.

## Adjudications

A person can decide a held row the document could not: a scanned filing, a filing whose document prints a filer status other than Member, a filing at a seat other than the member's, a filing dated before the swearing-in the roster records. `adjudications.ndjson`, beside this README, carries one decision per line: `doc_id`, `officeholder_id`, `evidence_url`, `decided_by`, `decided_at`, and an optional `note`. The build applies each decision to the row with that DocID, marks the filing's `extraction_confidence` as `manual`, and refuses to build if a decision lacks any of the five fields, because a decision without its evidence is not one the register can carry. The file's hash rides in the run record. The path for contributors is in [CONTRIBUTING.md](../../../CONTRIBUTING.md).

## Keeping it current

`.github/workflows/refresh.yml` runs all three stages on a schedule and opens a pull request only when the source served different bytes, with every gate already run. The test is the capture key against the last build's run record, never a diff of the rows: every row carries its retrieval time, so a diff reports a change on every run, and the first live run did exactly that and opened a pull request for a non-change. `build.py --capture-key` prints the key without building. `documents.py` decides what to capture from the last build's rows and set-aside file, so a filing or a held row that first appears in a refreshed index is built without its document and captured on the following run: a build can be one refresh behind its own source on those rows, and each such row says so (no content hash on a filing; the clause "the document has not been captured" on a held row). Nothing about the loop needs a server, a database, or a secret.

## Why this is Python

The project's `src/README.md` originally said TypeScript for adapters. This adapter is Python, for one decisive reason and one supporting one.

The canonical NDJSON is covered by the seal, and the tool that computes the seal is standard-library Python. Two languages serialising JSON is two chances to disagree about key order, Unicode escaping, or number formatting, and a disagreement there is a digest that moves for no reason a reader can see. One writer and one sealer in one language removes the whole class of bug.

Supporting it: `zipfile`, `xml.etree`, `urllib`, `unicodedata` and `hashlib` are all standard library, so ingest needs no dependency install at all. That is the solo-operator test in [CLAUDE.md](../../../CLAUDE.md) applied to the thing that runs on a schedule. Signals remain TypeScript; they are pure functions over rows and do not write the sealed store.
