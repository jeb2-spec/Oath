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
        (run.get("rejected_by_reason", {}).get("surname matches a sitting member"), "rows held"),
    ]
    return [(int(n), label) for n, label in figures if n]


def state_text_lacks(meta: dict, run: dict | None = None) -> str:
    """Which of the build's own figures the hand-written state text fails to carry.

    The state text is the one sentence a reader gets about the whole build, and it is
    sealed. A build whose figures changed and whose sentence did not is a count in prose
    the table contradicts. Checked: the row counts of the counted files, and, when the
    run record is given, the figures in it that move between builds. Each must appear as
    a whole number with thousands separators, not inside a larger number. Returns an
    empty string when every figure is present.
    """
    state = meta.get("state", "")
    wanted = [(meta.get("rows", {}).get(path), label) for path, label in COUNTED]
    wanted += run_figures(run or {})
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


def derive_state(root: Path, meta: dict) -> str:
    """The build's one sentence about itself, from the build's own figures and nothing typed.

    Reads the adapter's run record, the sealed rows, and each Signal's run record. Where the
    adapter wrote a reason, the sentence quotes it. Every figure `state_text_lacks` checks is
    in it by construction.
    """
    runs = current_runs(root)
    holders = read_rows(root / "data" / "officeholders.ndjson")
    filings = read_rows(root / "data" / "filings.ndjson")
    findings = read_rows(root / "data" / "findings.ndjson")
    signals = {row["id"]: row for row in read_rows(root / "data" / "signals.ndjson")}
    reports = sum(1 for f in filings if f.get("form_type") == "House-PTR")
    sentences = []
    for run in runs:
        counts, documents = run.get("counts", {}), run.get("documents", {})
        reasons = dict(run.get("rejected_by_reason", {}))
        held = reasons.pop(HELD_REASON, 0)
        index = next((s for s in run.get("sources", []) if s["name"].endswith("FD.zip")), {})
        starts = sorted({o["term_start"] for h in holders for o in h.get("offices", [])[:1]})
        congress = f" of the {(int(starts[0][:4]) - 1789) // 2 + 1}th Congress" if starts else ""
        attributed = (
            f"{plural(counts.get('accepted', 0), 'filing', 'filings')} attributed to "
            f"{counts.get('officeholders_with_a_filing', 0):,} sitting members from the Clerk's "
            f"{run.get('year')} filing index, retrieved {index.get('retrieved_at', '')[:10]}, "
            f"{counts.get('attributed_by_document', 0):,} of them settled by the document's own "
            "header where the name alone could not"
        )
        if counts.get("adjudicated"):
            attributed += f", {counts['adjudicated']:,} by a person's cited decision"
        not_attributed = ", ".join(
            f"{n:,} because {reason}"
            for reason, n in sorted(reasons.items(), key=lambda item: (-item[1], item[0]))
        )
        if held:
            not_attributed += (
                f"{', and ' if not_attributed else ''}{held:,} held for a person to decide because "
                f"the {HELD_REASON}"
            )
        sentence = (
            f"The House index layer and the transaction reports behind it. "
            f"{counts.get('seats', 0):,} seats{congress}, "
            f"{counts.get('filled', 0):,} of them filled "
            f"and {counts.get('vacant', 0):,} vacant; {attributed}. "
            f"{counts.get('rejected', 0):,} index rows are not attributed, each with a reason: "
            f"{not_attributed}."
        )
        if counts.get("index_rows_duplicated"):
            sentence += (
                " The index lists "
                f"{plural(counts['index_rows_duplicated'], 'DocID', 'DocIDs')} more "
                "than once, identically; the register keeps one row for each."
            )
        sentence += (
            f" Of the {reports:,} transaction reports attributed, "
            f"{documents.get('read', 0):,} were read from the Clerk's documents and "
            f"{documents.get('transactions', 0):,} transactions "
            "written, each checked against the seat and Filing ID printed in its report; "
            f"{documents.get('unreadable', 0):,} are scanned paper filings the register captured, "
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
            f"read, and no holdings are. {counts.get('quiet', 0):,} sitting members have no filing "
            "attributed."
        )
        sentences.append(sentence)
    summaries = [
        read_rows(path)[0]
        for path in sorted((root / "data" / "signal-runs").glob("*.ndjson"))
        if read_rows(path)
    ]
    if not summaries:
        sentences.append("No Signal is defined, so no Finding exists.")
    for summary in summaries:
        signal = signals.get(summary["signal_id"], {})
        by_state = summary.get("reports_by_state", {})
        skipped = sum(summary.get("rows_not_evaluated", {}).values())
        sentences.append(
            f"The Signal {signal.get('name', summary['signal_id'])} ({summary['signal_id']}) "
            f"evaluated {summary['rows_evaluated']:,} rows on the {by_state.get('evaluated', 0):,} "
            f"reports it read and found {summary['rows_after']:,} of them dated by the "
            "Clerk's index "
            f"after the deadline the rule sets, on {summary['reports_with_a_finding']:,} reports "
            f"attributed to {summary['officeholders_with_a_finding']:,} officeholders; "
            f"{skipped:,} rows were not evaluated, each with a reason, and "
            f"{by_state.get('not read', 0):,} reports were not read."
        )
    sentences.append(
        f"{ledger_sentence(findings)} Those gaps are counted, not hidden. Presence in this "
        "register is not evidence of wrongdoing."
    )
    return " ".join(sentences)


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


def seal(root: Path, build: str, built_at: str, derive: bool = False) -> str:
    verify = load_verify(Path(__file__).resolve().parent)
    meta_path = root / verify.META
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    meta["build"] = build
    meta["built_at"] = built_at
    meta["rows"] = verify.row_counts(root)
    if derive:
        meta["state"] = derive_state(root, meta)
    runs = current_runs(root)
    stale = (
        state_text_lacks(meta)
        if not runs
        else ", ".join(s for s in (state_text_lacks(meta, run) for run in runs) if s)
    )
    if stale:
        raise SystemExit(
            "refusing to seal: the state text in data/meta.json does not carry the build's "
            f"own counts ({stale}); rewrite it for this build first"
        )
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
