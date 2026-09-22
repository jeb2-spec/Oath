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

The hardest refusal is deliberate. Where a surname matches exactly one sitting member but the given names disagree, the row is rejected, not accepted. That case is usually the roster's common name against the index's legal name, "Bill" against "William", and it is usually the same person. Usually is not the standard the Charter's fourth vow sets, and the same pattern also describes a relative running for the seat the incumbent holds. A human adjudicates those; the adapter never guesses one into the register.

## What one retrieval produced

| | |
| --- | --- |
| Seats | 441 |
| Officeholders | 439 |
| Filings attributed | 1,097 |
| Officeholders with at least one filing | 393 |
| Index rows rejected | 1,842 |
| Sitting members with nothing attributed | 46 |

Of the rejections, 1,587 are rows whose name matches no sitting member, which is the expected shape of a file that is mostly candidates. The other 255 carry a surname matching exactly one sitting member whose given names differ, and every one of them is waiting on a person to decide.

Those 46 quiet members and those 255 held rows are the adapter's known incompleteness. They are counted in `data/meta.json` rather than hidden, and closing them is the next task here: a reviewed, cited adjudication file mapping a legal name to a roster name, versioned like any other artefact.

## Form codes are carried, not interpreted

The index labels each filing with a single letter. Twelve appear in the 2025 file and no Clerk page read on 2026-09-22 defines them, which SOURCES.md F.1 already records. The adapter stores the letter verbatim in `source_form_code` and sets `form_type` to `other`.

The one exception is `P`, mapped to `House-PTR`. That is not an inference from the letter. The Clerk serves those documents from a `ptr-pdfs` path while every other code is served from `financial-pdfs`, so the publisher's own filing system makes the distinction. When a Clerk document defining the remaining codes is found, it goes in SOURCES.md and the mapping follows it.

## Reproducing a build

`fetch.py` writes `capture.json` beside the bytes, recording for each retrieval the URL, the retrieval time, the SHA-256 of the bytes, and the `Last-Modified` the server reported. Every row cites that record, so a reader can ask which retrieval a row came from and hash the file themselves.

The index is not an annual artefact. The 2025 archive was last modified partway through 2026, so it is a live file that grows as filings arrive. A build is a statement about one retrieval, not about a year, which is what the seal is for.

Two builds from one capture produce byte-identical output. The rejected file and the run record are named for the captures they came from (twelve hex characters of the hash of both files' hashes), never for the day the build ran, so an unchanged source is an unchanged tree and the seal holds. Rejections from earlier captures live in git history.

## Run records

Every build writes one line to `data/adapter-runs/house-fd-<year>-<capture key>.ndjson`: the adapter, the two captures with their URLs, retrieval times, hashes and last-modified headers, the hash of the adjudication file that shaped the build, the counts (seats, filled, vacant, index rows, accepted, adjudicated, officeholders with a filing, quiet, rejected), and the rejections by reason. It is sealed with the rows, so the provenance of a build is inside the build.

## Adjudications

A person can decide a held row. `adjudications.ndjson`, beside this README, carries one decision per line: `doc_id`, `officeholder_id`, `evidence_url`, `decided_by`, `decided_at`, and an optional `note`. The build applies each decision to the row with that DocID, marks the filing's `extraction_confidence` as `manual`, and refuses to build if a decision lacks any of the five fields, because a decision without its evidence is not one the register can carry. The file's hash rides in the run record. The path for contributors is in [CONTRIBUTING.md](../../../CONTRIBUTING.md).

## Keeping it current

`.github/workflows/refresh.yml` runs both stages on a schedule and opens a pull request only when the source served different bytes, with every gate already run. The test is the capture key against the last build's run record, never a diff of the rows: every row carries its retrieval time, so a diff reports a change on every run, and the first live run did exactly that and opened a pull request for a non-change. `build.py --capture-key` prints the key without building. Nothing about the loop needs a server, a database, or a secret.

## Why this is Python

The project's `src/README.md` originally said TypeScript for adapters. This adapter is Python, for one decisive reason and one supporting one.

The canonical NDJSON is covered by the seal, and the tool that computes the seal is standard-library Python. Two languages serialising JSON is two chances to disagree about key order, Unicode escaping, or number formatting, and a disagreement there is a digest that moves for no reason a reader can see. One writer and one sealer in one language removes the whole class of bug.

Supporting it: `zipfile`, `xml.etree`, `urllib`, `unicodedata` and `hashlib` are all standard library, so ingest needs no dependency install at all. That is the solo-operator test in [CLAUDE.md](../../../CLAUDE.md) applied to the thing that runs on a schedule. Signals remain TypeScript; they are pure functions over rows and do not write the sealed store.
