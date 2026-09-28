# Contributing

Thank you for wanting to make this real.

Before you open a pull request, read three files, in this order, and know that opening a PR is a written commitment to them:

1. [CHARTER.md](CHARTER.md). Five vows, short on purpose. When everything else is negotiable, they are not.
2. [BYLAWS.md](BYLAWS.md). Governance, roles, corrections and supersessions, contributor agreement (§7 is what you are agreeing to when you open a PR), and the removal policy.
3. [RUBRIC.md](RUBRIC.md), if your PR touches a Signal or a Finding. Five pass/fail gates; the PR sits at review until each is answered.

Beyond that, the shape of a good contribution:

- **Small, named commits.** One purpose per commit. A PR with three orthogonal purposes should be three PRs.
- **Gates last.** Run `python scripts/oath-doctor.py` after your final edit, not before it; it runs every gate that exists and says which are still planned. CI runs the same set on every push. A gate that fails locally will fail there.
- **No verdict language.** Every user-facing sentence passes the "would the subject read this back to you comfortably in a room?" test. See [INVARIANTS.md §1](INVARIANTS.md).
- **Corrections and supersessions preserve the past.** Nothing is deleted; everything is superseded. See Charter Vow V and [BYLAWS.md §6](BYLAWS.md).
- **Conflict of interest disclosure is required.** Every PR body carries a `## Conflict of interest disclosure` heading. `None.` is a valid answer when true. See [BYLAWS.md §7](BYLAWS.md).
- **Council review before publishing anything that names an officeholder in a new way.** New Signal, Signal version bump, new naming template, the first batch of adjudications. See [COUNCIL.md](COUNCIL.md).
- **Attribution follows the `Co-Authored-By` convention.** If an AI collaborator helped, disclose it in the trailer.

## How the record is obtained and kept current

The register reads primary sources and nothing else. Each source has an adapter under `src/adapters/`, in two stages that anyone can run:

```bash
python src/adapters/house-fd/fetch.py --year 2025
python src/adapters/house-fd/documents.py --year 2025 --codes P,O,X
python src/adapters/house-fd/build.py --year 2025
python tools/seal.py --build <sequence>-house-2025 --built-at <the retrieval time fetch.py recorded>
```

`fetch.py` retrieves and records: the URL, the retrieval time, the SHA-256 of the bytes, and the server's last-modified. `documents.py` does the same for the document behind each transaction report, annual report and extension form, two seconds apart, and needs `pypdf` (`python -m pip install -e .[extract]`). `build.py` touches no network; it writes rows from the recorded capture, so anyone holding the same bytes gets the same rows. What the adapter cannot attribute beyond doubt goes to `data/rejected/` with the reason, and every run writes a one-line record to `data/adapter-runs/` naming the captures it read. Both are sealed with the rows.

On a schedule, [`refresh.yml`](.github/workflows/refresh.yml) does the same in GitHub Actions: fetch, build, and if the record changed, re-seal, run every gate, and open a pull request for the maintainer. If nothing changed it says so and stops. A pull request opened by the workflow does not trigger CI on itself, so the workflow runs the full gate set before pushing and its log is the evidence; the merge runs CI on `main`.

Adapters are Python, standard library, for the reason in [`src/README.md`](src/README.md): the sealed rows and the tool that seals them share one language. Signals are TypeScript.

## Adjudicating a held row

The adapter does not attribute a filing on a surname alone, because a surname with a different given name is usually the same person and also the exact shape of a relative running for the seat. Where the index places such a row at the member's own seat, the document behind it decides: the adapter attributes the row when the Clerk's document prints Status `Member`, that seat, that Filing ID and a filer name carrying the roster surname, and the index dates it no earlier than the swearing-in the roster records. Everything else is held in `data/rejected/` for a person to decide, with what the document printed quoted on the row: a document that prints another filer status, a scanned filing, a row at a seat other than the member's, a filing dated before the swearing-in. There are about a hundred and sixty of them.

To decide one: open an issue with the *Adjudicate a held row* template, or go straight to a PR that adds one line to [`src/adapters/house-fd/adjudications.ndjson`](src/adapters/house-fd/adjudications.ndjson):

```json
{"doc_id":"20032062","officeholder_id":"oh:us:house:a000055","evidence_url":"https://disclosures-clerk.house.gov/...","decided_by":"your name or handle","decided_at":"2026-09-22","note":"the index writes the legal name; the roster the common one"}
```

The evidence is the primary source that ties the document to the person, usually the document itself, which names its filer. The next build applies the decision, says on the filing's row that the maintainer's recorded decision attributed it, citing the evidence, reads its document like any other, and carries the hash of the adjudication file in the run record, so anyone can see which decisions shaped which build. A decision without its evidence is refused at build time.

The first batch of adjudications goes to the [Council](COUNCIL.md) before it merges, because attributing a document to a person by human judgement is a new way of naming an officeholder.

## What the project needs most

In order:

- **Adjudications.** The held rows, above. Each one closes a gap the build publishes as a number.
- **What the first Signal cannot yet reach.** `stock-act-ptr-after-deadline` landed on 2026-09-26 ([docs/signals/stock-act-ptr-after-deadline.md](docs/signals/stock-act-ptr-after-deadline.md)). Its limits are the next work: the signed date on each e-filed report, set beside the Clerk's index date; the Committee's instructions on government securities, read at the source; and the earlier indexes and service dates that would let it evaluate a returning Member's transactions from before this Congress (NEXT.md).
- **The Senate adapter.** SOURCES.md F.2. No bulk download, an agreement gate, and a report-identifier scheme nobody has recorded yet; the first session past the gate records the scheme before anything else.
- **Watching the sources.** When a source moves or changes shape, the *A primary source changed* issue template is the way to say so.

## Now that the repository is public

Everything lives on GitHub on purpose. The rendered register publishes with GitHub Pages ([`pages.yml`](.github/workflows/pages.yml)) at <https://jeb2-spec.github.io/Oath/> on every push to main, and every CI run also keeps the rendered site as a downloadable artifact for fourteen days. The site has been public since 2026-09-23 and the repository since 2026-09-26.

Branch protection is also free only for public repositories on a personal account. On the day of the flip, require the `verify` workflow (its check is named *the gates*) to pass before merge and require review from the code owners in [`.github/CODEOWNERS`](.github/CODEOWNERS), which makes the maintainer's approval of doctrine changes ([INVARIANTS.md §17](INVARIANTS.md)) mechanical rather than remembered. Two facts about GitHub shape how. The author of a pull request cannot approve it, and the assistant's pull requests are opened under the maintainer's own account, so a required code-owner review would stop every one of them that touches a code-owned path. And a pull request opened with the refresh workflow's token does not trigger CI, so a required check would wait forever on a refresh pull request, whose gates run inside the refresh job before it pushes. Keep the maintainer able to bypass the rule, or both stall.

## What to do if you find a problem in a published Finding

Two paths, both documented in [BYLAWS.md §6](BYLAWS.md):

- **Fact correction** (wrong person, wrong filing, wrong date, wrong amount): open a PR that adds a correction citing the primary source that reveals it. For a row of the register itself (an officeholder, a filing, a transaction) that is `tools/correct.py`, which the maintainer runs: it writes a `corrected` row to `data/changes.ndjson` naming the fact, what it was and what it is, keeps the evidence's bytes with the time they were fetched (a filed document it cites by its hash and never keeps, and a filer's own text by the hash of what it said), and moves the fact, and moves an attribution whole, with the filing's office and its transactions; for a Finding it is `src/signals/run.py --correct`, which adds a row that supersedes it. Both stay in the register, beside what they correct.
- **Demonstrated change** (a later primary-source filing shows the subject's conduct has changed such that the Finding's condition no longer applies): open a PR that adds a supersession row citing the primary source that shows the change. Both rows stay.

Off-the-record requests are not honored. Every change is a row in the register a reader can see. The *Correct a row* issue template is the front door.

## Reporting a security or trust issue

See [SECURITY.md](SECURITY.md).

## The larger question you probably have

Yes, this repository is unusually dense for its state. That is because the discipline it enforces is what makes the register worth reading; adding it after the fact is much harder than adding it now. If a rule seems overkill, read the [Charter](CHARTER.md) again, and then the section of the [Invariants](INVARIANTS.md) that names the specific failure the rule catches. If it still seems overkill, open a PR that names why. That kind of pushback is welcome.
