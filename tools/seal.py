#!/usr/bin/env python3
"""Seal a build: write the register's digest and row counts into data/meta.json.

This is the build's last step before anchoring. It records the build id and the
build time it is given (never the clock, so two runs from the same inputs produce
the same bytes), counts the rows in every NDJSON file, and writes the digest that
tools/verify.py recomputes. It shares the manifest rule with the verifier by
importing it; tools/tamper-test.py recomputes the same rule with code that shares
nothing, which is what makes the check non-circular.

With --derive-state it first writes the build's one sentence about itself, the state
text, from the build's own figures: the adapter's run record, the rows, and each
Signal's run record, quoting the adapter's own reasons. Every figure in it is derived,
none typed, which is how the scheduled refresh can seal a build nobody is watching;
errata learnt that a count typed by hand goes stale four times before anyone notices.
Without the flag the state text is taken as written, and either way the seal refuses
one that does not carry the build's figures.

    python3 tools/seal.py --build 0001 --built-at 2026-09-22T00:00:00Z
    python3 tools/seal.py --build 0005-house-2025 --built-at 2026-09-23T14:13:28Z --derive-state
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path


def load_verify(tools_dir: Path):
    spec = importlib.util.spec_from_file_location("verify", tools_dir / "verify.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


COUNTED = (
    ("data/officeholders.ndjson", "officeholders"),
    ("data/filings.ndjson", "filings"),
    ("data/transactions.ndjson", "transactions"),
    ("data/findings.ndjson", "findings"),
)
HELD_REASON = "surname matches a sitting member"
HELD_SEAT = re.compile(r"surname matches a sitting member \(.+?, ([A-Z]{2}\d{2})\)")
# Why a held row waits, by the words the adapter's reason carries; the first match wins.
HELD_KINDS = (
    ("carries no Filing ID line", "whose documents carry no Filing ID line"),
    ("not Member", "whose documents print a filer status other than Member"),
    ("before the swearing-in", "dated before the swearing-in the roster records"),
)


def run_figures(run: dict) -> list[tuple[int, str]]:
    """The run record's figures the state text is expected to carry: the ones that move
    between builds while the roster stands still."""
    counts = run.get("counts", {})
    documents = run.get("documents", {})
    figures = [
        (counts.get("quiet"), "quiet members"),
        (counts.get("rejected"), "rows not attributed"),
        (counts.get("attributed_by_document"), "rows attributed by the document"),
        (documents.get("read"), "documents read"),
        (held_rows(run), "rows held"),
    ]
    return [(int(n), label) for n, label in figures if n]


def held_rows(run: dict) -> int:
    """The rows set aside because a row's surname matches a sitting member, whatever clause the
    group carries after that. Looked up by an exact key, the figure went silent the moment the
    adapter grouped those reasons by their words, and the guard that would have caught it is the
    one it switched off (the Council's fifth reading of S.1b, Seat E)."""
    return sum(
        n for key, n in run.get("rejected_by_reason", {}).items() if key.startswith(HELD_REASON)
    )


def change_figures(changes: list[dict]) -> list[tuple[int, str]]:
    """The figures the changes sentence carries: later reads, and the maintainer's decisions. With
    one kind of read the sentence gives no count, so neither does this: a guard that requires a
    figure the sentence will not print passes only by an accident of the digits elsewhere in it
    (the Council's fifth reading of S.1b, Seat C)."""
    later = [c for c in changes if c.get("change") != "corrected"]
    reads = 0 if len(change_kinds(later)) == 1 else len(later)
    decided = len(
        {
            (c.get("decided_at"), c.get("decided_by"), c.get("because"))
            for c in changes
            if c.get("change") == "corrected"
        }
    )
    return [(reads, "changes later reads showed"), (decided, "the maintainer's decisions")]


def state_text_lacks(meta: dict, run: dict | None = None, changes: list[dict] | None = None) -> str:
    """Which of the build's own figures the hand-written state text fails to carry.

    The state text is the one sentence a reader gets about the whole build, and it is
    sealed. A build whose figures changed and whose sentence did not is a count in prose
    the table contradicts. Checked: the row counts of the counted files, and, when the
    run record is given, the figures in it that move between builds; and, when the change rows
    are given, how many changes later reads showed and how many decisions the maintainer
    recorded (the Council's third reading of S.1b, Seat G). Each must appear as a whole number
    with thousands separators, not inside a larger number. Returns an empty string when every
    figure is present.
    """
    state = meta.get("state", "")
    wanted = [(meta.get("rows", {}).get(path), label) for path, label in COUNTED]
    wanted += run_figures(run or {})
    wanted += change_figures(changes or [])
    missing = []
    for count, label in wanted:
        if not count:
            continue
        pattern = r"(?<![\d,])" + re.escape(f"{count:,}") + r"(?![\d,])"
        if not re.search(pattern, state):
            missing.append(f"{label} {count:,}")
    return ", ".join(missing)


def current_runs(root: Path) -> list[dict]:
    """The run records in the tree, each paired with its set-aside file by year and key.

    A record `house-fd-<year>-<key>` must have `data/rejected/house-fd/<year>-<key>.ndjson`
    beside it; a record without one is the leftover of a build the tree no longer holds,
    and a tree that carries one is refused, because a page once read such a record.
    """
    runs = sorted((root / "data" / "adapter-runs").glob("*.ndjson"))
    out = []
    for path in runs:
        name = path.stem.split("-", 2)[-1] if path.stem.count("-") >= 2 else path.stem
        adapter = path.stem[: -len(name) - 1] if name != path.stem else ""
        set_aside = root / "data" / "rejected" / adapter / f"{name}.ndjson"
        if not set_aside.is_file():
            raise SystemExit(
                f"refusing to seal: {path.as_posix()} has no set-aside file "
                f"{set_aside.as_posix()}; "
                "the tree carries one run record per adapter and year, each with its set-aside file"
            )
        lines = [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        if lines:
            out.append(json.loads(lines[-1]))
    return out


def read_rows(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text("utf-8").splitlines() if line.strip()]


def plural(n: int, one: str, many: str) -> str:
    return f"{n:,} {one if n == 1 else many}"


def ordinal(n: int) -> str:
    """121st, 122nd, 123rd, 124th; 111th, 112th, 113th."""
    suffix = "th" if 11 <= n % 100 <= 13 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


def held_clause(rows: list[dict]) -> str:
    """Why the rows held for a person wait, counted, as the adapter's reasons give it."""
    counts: dict[str, int] = {}
    for row in rows:
        reason = row.get("reason", "")
        if not reason.startswith(HELD_REASON):
            continue
        kind = next((words for marker, words in HELD_KINDS if marker in reason), None)
        if kind is None:
            seat = HELD_SEAT.match(reason)
            here = seat and row.get("source_row", {}).get("state_dst") == seat.group(1)
            kind = (
                "at the member's own seat that the document does not settle"
                if here
                else "at a seat other than the member's"
            )
        counts[kind] = counts.get(kind, 0) + 1
    parts = [f"{n:,} {kind}" for kind, n in sorted(counts.items(), key=lambda i: (-i[1], i[0]))]
    if len(parts) > 1:
        parts[-1] = f"and {parts[-1]}"
    return ", ".join(parts)


def reach(outcomes: list[dict], filings: list[dict] | None = None) -> dict[str, int]:
    """Who a Signal's run could not reach, in counts of officeholders: those whose reports are
    all fetched and not read, those with some, and those with rows dated before this
    Congress's swearing-in, which it does not evaluate. A report the register has not fetched
    is counted apart and never called scanned paper, as the pages count it (the Council's
    fourth reading of S.1b, Seat F)."""
    fetched = {f["id"]: bool((f.get("source") or {}).get("content_hash")) for f in filings or []}
    states: dict[str, set[str]] = {}
    before: set[str] = set()
    unfetched = 0
    for o in outcomes:
        state = o["state"]
        if state == "not read" and fetched.get(o.get("filing_id"), True) is False:
            unfetched += 1
            state = "not fetched"
        states.setdefault(o["officeholder_id"], set()).add(state)
        if o["not_evaluated"].get("dated before this Congress's swearing-in"):
            before.add(o["officeholder_id"])
    return {
        "paper_only": sum(1 for s in states.values() if s == {"not read"}),
        "some_paper": sum(1 for s in states.values() if "not read" in s and s != {"not read"}),
        "not_fetched": unfetched,
        "before_swearing_in": len(before),
    }


def derive_state(root: Path, meta: dict) -> str:
    """The build's one sentence about itself, from the build's own figures and nothing typed.

    Reads the adapter's run record, the sealed rows, and each Signal's run record. Where the
    adapter wrote a reason, the sentence quotes it. Every figure `state_text_lacks` checks is
    in it by construction.
    """
    runs = current_runs(root)
    holders = read_rows(root / "data" / "officeholders.ndjson")
    filings = read_rows(root / "data" / "filings.ndjson")
    transactions = len(read_rows(root / "data" / "transactions.ndjson"))
    offices = len(read_rows(root / "data" / "offices.ndjson"))
    findings = read_rows(root / "data" / "findings.ndjson")
    signals = {row["id"]: row for row in read_rows(root / "data" / "signals.ndjson")}
    reports = sum(1 for f in filings if f.get("form_type") == "House-PTR")
    sentences = [register_sentence(offices, len(holders), len(filings), transactions)]
    for run in runs:
        counts, documents = run.get("counts", {}), run.get("documents", {})
        reasons = dict(run.get("rejected_by_reason", {}))
        held = sum(reasons.pop(k) for k in list(reasons) if k.startswith(HELD_REASON))
        index = next((s for s in run.get("sources", []) if s["name"].endswith("FD.zip")), {})
        roster = next((s for s in run.get("sources", []) if s["name"] == "MemberData.xml"), {})
        starts = sorted({o["term_start"] for h in holders for o in h.get("offices", [])[:1]})
        congress = f" of the {congress_named(int(starts[0][:4]))}" if starts else ""
        mine = [f for f in filings if f"/{run.get('year')}/" in f.get("source", {}).get("url", "")]
        reads = sorted({f["source"]["retrieved_at"][:10] for f in mine if f.get("source")})
        latest = index.get("retrieved_at", "")[:10]
        span = (
            f"as the register read them from {reads[0]} to {latest}"
            if reads and reads[0] != latest
            else f"as the register read them on {latest}"
        )
        attributed = (
            f"{plural(counts.get('filings', counts.get('accepted', 0)), 'filing', 'filings')} "
            f"of the Clerk's {run.get('year')} filing index (the reports it lists under "
            f"{run.get('year')}), {span}, attributed to "
            + plural(counts.get("officeholders_with_a_filing", 0), "officeholder", "officeholders")
            + ", "
            f"{counts.get('attributed_by_document', 0):,} of them settled by the document's own "
            "header where the name alone could not"
        )
        if counts.get("adjudicated"):
            attributed += f", {counts['adjudicated']:,} by the maintainer's recorded decision"
        not_attributed = ", ".join(
            f"{n:,} because {reason}"
            for reason, n in sorted(reasons.items(), key=lambda item: (-item[1], item[0]))
        )
        if held:
            why = held_clause(
                read_rows(
                    root
                    / "data"
                    / "rejected"
                    / "house-fd"
                    / f"{run['year']}-{run['capture_key']}.ndjson"
                )
            )
            not_attributed += (
                f"{', and ' if not_attributed else ''}{held:,} set aside for the maintainer to "
                f"decide by hand because the {HELD_REASON}" + (f": {why}" if why else "")
            )
        closed = run.get("congress", {}).get("closed")
        lead = (
            closed_sentence(run)
            + " The House index layer and the transaction reports behind it, as the register "
            f"holds them for the {ordinal(run['congress']['filing_year'])} Congress: "
            if closed
            else "The House index layer and the transaction reports behind it. "
            f"{counts.get('seats', 0):,} seats{congress}, "
            f"{counts.get('filled', 0):,} of them filled "
            f"and {counts.get('vacant', 0):,} vacant on the Clerk's roster read "
            f"{roster.get('retrieved_at', '')[:10]}; "
        )
        sentence = (
            f"{lead}{attributed}. "
            f"{counts.get('rejected', 0):,} index rows are not attributed"
            + (
                (
                    ", each with the reason the register gave it when it set the row aside, while "
                    "the year was open or since: "
                    if closed
                    else ", each with a reason: "
                )
                + f"{not_attributed}."
                if not_attributed
                else "."
            )
        )
        if counts.get("index_rows_duplicated"):
            sentence += (
                " The index lists "
                f"{plural(counts['index_rows_duplicated'], 'DocID', 'DocIDs')} more "
                "than once, identically; the register keeps one row for each."
            )
        sentence += (
            f" Of the {counts.get('reports', reports):,} transaction reports attributed, "
            f"{documents.get('read', 0):,} were read from the Clerk's documents and "
            f"{documents.get('transactions', 0):,} transactions "
            "written, each checked against the seat and Filing ID printed in its report; "
            f"{documents.get('unreadable', 0):,} are scanned paper filings the register fetched, "
            "hashed and does not read"
        )
        if documents.get("seat_discrepancies"):
            sentence += (
                f"; {documents['seat_discrepancies']:,} of the "
                f"{documents.get('read', 0):,} print a "
                "seat other than the roster's and carry that discrepancy on the row"
            )
        forms = plural(
            documents.get("header_only", 0),
            "annual report or other form",
            "annual reports and other forms",
        )
        sentence += (
            f". {forms} "
            "behind attributed rows had their headers read and hashed; their schedules are not yet "
            f"read, and no holdings are. {counts.get('quiet', 0):,} Members "
            + (
                f"of the {ordinal(run['congress']['filing_year'])} Congress, as its roster listed "
                "them when the register last read it,"
                if closed
                else "the roster lists"
            )
            + " have no filing attributed."
        )
        changes = read_rows(root / "data" / "changes.ndjson")
        if changes:
            sentence += " " + changes_sentence(changes)
        sentences.append(sentence)
    latest: dict[str, dict] = {}
    for row in signals.values():
        if row["version"] >= latest.get(row["slug"], {}).get("version", 0):
            latest[row["slug"]] = row
    records = [
        read_rows(root / "data" / "signal-runs" / f"{s['slug']}-v{s['version']}.ndjson")
        for s in sorted(latest.values(), key=lambda s: s["id"])
    ]
    records = [record for record in records if record]
    set_aside = (
        sum(
            1
            for run in runs
            for row in read_rows(
                root
                / "data"
                / "rejected"
                / "house-fd"
                / f"{run['year']}-{run['capture_key']}.ndjson"
            )
            if row.get("source_row", {}).get("filing_type") == "P"
        )
        if runs
        else 0
    )
    if not records:
        sentences.append("No Signal is defined, so no Finding exists.")
    for record in records:
        summary, outcomes = record[0], record[1:]
        signal = signals.get(summary["signal_id"], {})
        by_state = summary.get("reports_by_state", {})
        skipped = sum(summary.get("rows_not_evaluated", {}).values())
        cannot = reach(outcomes, filings)
        sentences.append(
            f"The Signal {signal.get('name', summary['signal_id'])} ({summary['signal_id']}) "
            f"evaluated {summary['rows_evaluated']:,} rows on the {by_state.get('evaluated', 0):,} "
            f"reports it read, and for {summary['rows_after']:,} of them the Clerk's index dates "
            "the report after the deadline the rule sets, on "
            f"{summary['reports_with_a_finding']:,} reports "
            f"attributed to {summary['officeholders_with_a_finding']:,} officeholders; "
            f"{skipped:,} rows were not evaluated, each with a reason, and "
            f"{by_state.get('not read', 0):,} reports were not read. It cannot reach "
            f"{plural(cannot['paper_only'], 'officeholder', 'officeholders')} whose transaction "
            f"reports are all scanned paper, or some of the reports of "
            f"{cannot['some_paper']:,} more"
            + (
                f"; it has not read {plural(cannot['not_fetched'], 'report', 'reports')} the "
                "register has not fetched"
                if cannot["not_fetched"]
                else ""
            )
            + "; it does not evaluate the rows dated before the "
            f"swearing-in the roster records for the {congress_of_register(holders)} on the "
            "reports of "
            f"{plural(cannot['before_swearing_in'], 'officeholder', 'officeholders')}; and the "
            f"{plural(set_aside, 'transaction report', 'transaction reports')} the index sets "
            "aside, not attributed to an officeholder, are outside it."
        )
    sentences.append(
        f"{ledger_sentence(findings)} Those gaps are counted, not hidden. Presence in this "
        "register is not evidence of wrongdoing."
    )
    return " ".join(sentences)


def congress_named(year: int) -> str:
    """The Congress whose terms begin in an odd year, named with its terms, as the Twentieth
    Amendment, section 1, sets them: from noon on 3 January to noon on 3 January two years
    on. A later reader needs the dates, not the number."""
    n = (year - 1787) // 2
    start = 1787 + 2 * n
    return (
        f"{ordinal(n)} Congress (terms from noon, 3 January {start}, "
        f"to noon, 3 January {start + 2})"
    )


def congress_of_register(holders: list[dict]) -> str:
    starts = sorted({o["term_start"] for h in holders for o in h.get("offices", [])[:1]})
    return f"{ordinal((int(starts[0][:4]) - 1787) // 2)} Congress" if starts else "Congress"


def register_sentence(offices: int, holders: int, filings: int, transactions: int) -> str:
    """What the register holds, register-wide, and the rule it holds it by. An officeholder
    the roster no longer lists is one of the officeholders, never counted apart here, so the
    sentence isolates no one (the Council's second reading of S.1b)."""
    return (
        f"The register holds {plural(offices, 'office', 'offices')}, "
        f"{plural(holders, 'officeholder', 'officeholders')}, "
        f"{plural(filings, 'filing', 'filings')} and "
        f"{plural(transactions, 'transaction', 'transactions')}. A row it has published stays, "
        "gaining only facts it lacked; a fact it carries moves only by a correction the "
        "maintainer records with the evidence, which is a row of its own; and an officeholder "
        "the roster no longer lists keeps their rows."
    )


CHANGE_WORDS = {
    "not listed": "a row a later read no longer lists",
    "listed again": "a row a later read lists again",
    "read otherwise": "a fact a later read states otherwise",
    "replaced": "a document a later read found served as a different file, which reads otherwise",
}
# The fifth pass made every file the Clerk serves that is not the one last seen a change row of its
# own, whether or not its rows read otherwise, so a replacement with an empty `differs` now exists.
# One kind said of both that the file reads otherwise, which the change row itself contradicts (the
# Council's fifth reading of S.1b, Seats C, D and F). Two kinds, by what the rows say.
READS_SAME = (
    "a document a later read found served as a different file, which reads as the rows the "
    "register published"
)


def change_kinds(reads: list[dict]) -> list[str]:
    """The kinds the changes sentence lists, in CHANGE_WORDS' order, a replacement split by
    whether the other file's rows read otherwise."""
    out = []
    for kind, words in CHANGE_WORDS.items():
        rows = [c for c in reads if c["change"] == kind]
        if not rows:
            continue
        if kind != "replaced":
            out.append(words)
            continue
        if any(c.get("differs") for c in rows):
            out.append(words)
        if any(not c.get("differs") for c in rows):
            out.append(READS_SAME)
    return out


def changes_sentence(changes: list[dict]) -> str:
    """What later reads showed about published rows, and what the maintainer decided, from
    data/changes.ndjson itself, never from a run record a correction does not rewrite (the
    Council's third reading of S.1b, Seats C, D and G): the total, and the kinds without a
    count for each, since a small count by kind is a count about one person (Seat C, N-9); and
    the maintainer's decisions counted as decisions, not as the rows one decision writes."""
    reads = [c for c in changes if c.get("change") != "corrected"]
    decided = {
        (c.get("decided_at"), c.get("decided_by"), c.get("because"))
        for c in changes
        if c.get("change") == "corrected"
    }
    parts = []
    if reads:
        kinds = change_kinds(reads)
        listed = kinds[0] if len(kinds) == 1 else ", ".join(kinds[:-1]) + " and " + kinds[-1]
        if len(kinds) == 1:
            # With one kind the total is the count by kind, and when small that is a count about
            # one person, which this sentence rules out: give the kind and no number, at every
            # count (Seat F, N29; the fifth reading, Seats C and F). change_figures drops the
            # figure with it, so the seal does not require a number the sentence will not print.
            shown = (
                "A change a later read showed is"
                if len(reads) == 1
                else ("Changes later reads showed are")
            )
            parts.append(
                f"{shown} recorded, each a row of its own citing the read, of this kind: {listed}"
            )
        else:
            shown = plural(
                len(reads), "change a later read showed is", "changes later reads showed are"
            )
            parts.append(
                f"{shown} recorded, each a row of its own citing the read, of these kinds: {listed}"
            )
    if decided:
        parts.append(
            f"{plural(len(decided), 'decision', 'decisions')} the maintainer recorded, "
            "correcting a published fact or recording that it stands, each citing the evidence"
        )
    return "; ".join(parts) + "."


def closed_sentence(run: dict) -> str:
    """A filing year whose Congress has ended: the register has closed it, keeps its rows as
    published, and attributes a new row of it only by the maintainer's recorded decision.
    Dated by the roster read that closed it, never by the roster the register reads now."""
    congress = run.get("congress", {})
    ours = congress.get("filing_year", 0)
    by = congress.get("closed_by") or {}
    later = ordinal(by.get("congress") or congress.get("roster", 0))
    read = (
        f"the Clerk's roster read {by['retrieved_at'][:10]} listed the {later}"
        if by.get("retrieved_at")
        else f"a later roster the register read listed the {later}"
    )
    return (
        f"The register has closed filing year {run.get('year')} (the reports the Clerk's index "
        f"lists under {run.get('year')}): they belong to the {congress_named(1787 + 2 * ours)}, "
        f"whose terms ended under the Twentieth Amendment, section 1, and {read}. It keeps "
        f"every row of the year as published, gives the {ordinal(ours)} Congress's offices the "
        "day their terms ended, and attributes a new row of the year only by the maintainer's "
        "recorded decision, which cites the evidence and is published with it; the Clerk may "
        f"still list reports under {run.get('year')}."
    )


def ledger_sentence(findings: list[dict]) -> str:
    """How many Findings the ledger holds, and, once any exist, how many are corrections.
    A correction that records a Signal no longer fires carries no row after the deadline."""
    text = f"The ledger holds {plural(len(findings), 'Finding', 'Findings')}"
    superseded = sum(1 for f in findings if f.get("superseded_by"))
    withdrawn = sum(
        1
        for f in findings
        if not f.get("superseded_by") and not (f.get("evidence") or {}).get("after", 1)
    )
    if superseded:
        text += f", {superseded:,} of them superseded by a correction and kept"
    if withdrawn:
        text += (
            f", and {withdrawn:,} "
            f"{'a correction' if withdrawn == 1 else 'corrections'} recording that the Signal no "
            "longer fires on a report"
        )
    return text + "."


def anchor_pointer(build: str) -> dict:
    """Where this build's anchor lives, never its state: a proof is completed after the seal,
    so a state sealed here would be out of date the day Bitcoin took it (NEXT.md S.4)."""
    return {
        "ledger": "ANCHORS.md",
        "manifest": f"data/anchors/{build}.manifest",
        "proof": f"data/anchors/{build}.manifest.ots",
        "note": (
            "The anchor's state is not sealed, because a proof is completed after the seal. "
            "The proof beside this build's manifest says whether its stamp is owed, pending in "
            "the OpenTimestamps calendars, or confirmed in a Bitcoin block; ots verify checks "
            "it, and tools/anchor.py regenerates the table in ANCHORS.md from the proofs."
        ),
    }


def stamp_changes(root: Path, build: str) -> int:
    """Name, on each change row not yet sealed, the build that first seals it, so a later
    reader holding one build's files can say when the register recorded a change (the
    Council's reading of S.1b). A stamped row is never touched again."""
    path = root / "data" / "changes.ndjson"
    if not path.is_file():
        return 0
    lines, stamped = [], 0
    for line in path.read_text(encoding="utf-8").splitlines(keepends=True):
        row = json.loads(line)
        if "build" not in row:
            row["build"] = build
            line = json.dumps(row, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
            line += "\n"
            stamped += 1
        lines.append(line)
    if stamped:
        path.write_text("".join(lines), encoding="utf-8", newline="\n")
    return stamped


def seal(root: Path, build: str, built_at: str, derive: bool = False) -> str:
    verify = load_verify(Path(__file__).resolve().parent)
    meta_path = root / verify.META
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    meta["build"] = build
    meta["built_at"] = built_at
    meta["anchor"] = anchor_pointer(build)
    meta["rows"] = verify.row_counts(root)
    if derive:
        meta["state"] = derive_state(root, meta)
    runs = current_runs(root)
    changes = read_rows(root / "data" / "changes.ndjson")
    stale = (
        state_text_lacks(meta, None, changes)
        if not runs
        else ", ".join(s for s in (state_text_lacks(meta, run, changes) for run in runs) if s)
    )
    if stale:
        raise SystemExit(
            "refusing to seal: the state text in data/meta.json does not carry the build's "
            f"own counts ({stale}); rewrite it for this build first"
        )
    # Only now, with the sentence checked: a refused seal stamps nothing, so no row names a
    # build that was never sealed (the Council's second reading of S.1b).
    stamp_changes(root, build)
    meta["rows"] = verify.row_counts(root)
    meta["digest"] = ""
    meta_path.write_text(
        json.dumps(meta, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    meta["digest"] = verify.compute_digest(root)
    meta_path.write_text(
        json.dumps(meta, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return meta["digest"]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Seal a build: write its digest into data/meta.json."
    )
    parser.add_argument("--build", required=True, help="build identifier, e.g. 0001")
    parser.add_argument("--built-at", required=True, help="ISO 8601 UTC, e.g. 2026-09-22T00:00:00Z")
    parser.add_argument(
        "--derive-state",
        action="store_true",
        help="write the state text from the build's own figures before sealing",
    )
    parser.add_argument("root", nargs="?", default=".", help="repository root (default: .)")
    args = parser.parse_args(argv)
    digest = seal(Path(args.root).resolve(), args.build, args.built_at, args.derive_state)
    print(f"sealed build {args.build} at {args.built_at}\n  digest    {digest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
