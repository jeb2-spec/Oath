# docs/related-work/

The verified records behind [RELATED.md](../../RELATED.md), one per cluster of neighbouring projects. RELATED.md is the paper's related-work section; these files are the rows it was written from.

## What is here

- `data/<cluster>.json`. The primary record for a cluster: the first reader's entries and the skeptic's verdicts, with the retrieval date, exactly as returned. Edit these, not the rendered files.
- `<cluster>.md`. The same record rendered for reading, by `render.py`. Corrections the skeptic made are shown beside the claims they correct, and both are kept.
- `render.py`. Standard-library Python. `python3 docs/related-work/render.py` regenerates every `.md` from its JSON.

## How the records were made

On the retrieval date in each file, for every cluster:

1. **Sweep.** One reader, given the cluster's project list, read each project's own About, methodology, data, API, licence, and terms pages and wrote one entry per project on the project's own terms, citing the page behind each claim. Where a page would not load, the entry says so under *could_not_verify* and the field reads *not verified*.
2. **Verify.** A second reader, given only the entries and a brief to refute rather than confirm, re-fetched every cited page and returned, per entry, the claims it confirmed, the claims the page contradicts (with the correction and its URL), the claims it could not check, and any projects the cluster omitted. The brief told it to check hardest the claims that would flatter Oath by comparison.
3. **Critic.** A third reader, given the full list of what the survey covered, searched for what it missed; its findings and the skeptics' omissions were swept and verified the same way and appear as their own clusters.

Two fields the readers produced are not in these records: the first reader's working notes for the synthesis in RELATED.md §5, and the skeptic's flags on the tone of those notes. Several of those notes evaluated a neighbour rather than describing it, which is exactly what the flags were for; they were used to write §5 and are not published as record.

## The frame

Presence in these records is not a claim about a project's quality, and absence is not either. A project is here because it works with the same public record Oath does.

Presence in the register is not evidence of wrongdoing. Several neighbours publish complaints, rankings, and per-person figures about named officeholders. Where a record describes that, it describes the role (a House member, a senator, a White House official) and not the person, names no officeholder outside a citation URL, and reproduces no ranked list. These records are about the neighbours; nothing in them is a Finding. If a project's maintainers find their entry wrong, the correction path is a pull request against the JSON; the corrected entry supersedes the old one and both stay readable, as with any row in the register.

## The schema of an entry

`name`, `organisation`, `url`, `kind`, `self_description`, `subject_scope`, `primary_sources_used[]`, `outputs[]`, `derived_scoring_or_ranking`, `identifiers_exposed[]`, `signal_precedents[]`, `openness_code`, `openness_data_license`, `openness_api`, `funding_or_business_model`, `disclaimer_or_frame`, `status_as_of_retrieval`, `citations[]` (`url`, `retrieved`, `supports`), `could_not_verify[]`, `added_by_sweep`.

A skeptic's verdict per entry: `confirmed[]`, `refuted[]` (`field`, `claim`, `correction`, `citation_url`), `unverifiable[]`.

*Status* means what the pages showed on the retrieval date: *active* if content dated within the previous twelve months was seen; *merged* or *closed* only if a page says so; *unknown* otherwise.
