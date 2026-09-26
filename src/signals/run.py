#!/usr/bin/env python3
"""Run every defined Signal over the register and write what it found. PIPELINE.md Stage 4.

    python src/signals/run.py --at 2026-09-23T14:13:28Z   # write
    python src/signals/run.py --check                      # regenerate and compare; write nothing
    python src/signals/run.py --at <built_at> --correct <finding-id> --because "<what changed,
        and the URL of the primary source that shows it>"  # write one correction, then run

Reads the current definition of each Signal (`docs/signals/<slug>.md`), its
implementation (`src/signals/<slug>.py`), and the rows in `data/`, and writes, each
sorted and serialised canonically, so the same inputs give the same bytes:

  data/signals.ndjson                   every Signal version ever defined, one row each,
                                        derived from its definition, never typed
  data/findings.ndjson                  the ledger of Findings, append-only
  data/signal-runs/<slug>-v<n>.ndjson   what the run evaluated, report by report, fired
                                        or not, so silence is recorded as such

A new Finding takes two fields only a build can give it: `fired_at`, the build's
built_at (the retrieval time of the latest capture it read, never the clock), and
`build_hash`, the digest by the seal's own rule over the three files the Signal read.

Facts stay (CHARTER Vow V; INVARIANTS §12 and §14). A Finding already in the ledger is
never rewritten and never dropped. A run that would change one, or that no longer
produces one, stops and names it, because that is a correction a person writes by
supersession, with the evidence (docs/signals/README.md, Corrections). `--correct` writes
that correction exactly: the chain's current row gains `superseded_by` and nothing else,
and a new row `<id>:c<n>` carries what the Signal now produces, or, where it no longer
fires, the Signal's own words for what the record now shows. The person supplies only the
reason, which must cite a source by URL; the rest is derived, so a correction cannot say
something the record does not. A Finding of an earlier version of a Signal is carried
forward untouched; a version bump adds rows and removes none. Standard library.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import sys
from pathlib import Path

INPUTS = {
    "officeholder": "data/officeholders.ndjson",
    "filing": "data/filings.ndjson",
    "transaction": "data/transactions.ndjson",
}
SIGNALS = "data/signals.ndjson"
FINDINGS = "data/findings.ndjson"
RUNS = "data/signal-runs"
DEFINITIONS = "docs/signals"
SECTIONS = {
    "Description": "description",
    "Criteria": "criteria",
    "What this Signal does not say": "not_saying",
    "Worked example": "worked_example",
}
FRONT_KEYS = (
    "id",
    "slug",
    "version",
    "name",
    "standard",
    "standard_citation",
    "inputs",
    "supersedes",
    "fixture",
)
# Set once, by the build that first produced a Finding, and never again. A correction
# row carries its own id and may carry a note; neither makes its content differ.
PROVENANCE = ("fired_at", "build_hash")
UNCOMPARED = PROVENANCE + ("id", "notes")
CORRECTION = re.compile(r":c(\d+)$")
FRONTMATTER = re.compile(r"\A---\n(.*?)\n---\n", re.S)
CITED = re.compile(r"https?://\S+")


class Refusal(Exception):
    """A run that would break a rule the register keeps. It writes nothing."""


def canonical(obj: object) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n"


def read_ndjson(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def render_ndjson(rows: list[dict]) -> str:
    return "".join(canonical(row) for row in rows)


# ---- definitions ----------------------------------------------------------------------


def parse_definition(path: Path) -> dict:
    """A Signal's definition file as its row in data/signals.ndjson. Nothing is typed twice:
    the row is the file's frontmatter and sections, verbatim."""
    text = path.read_text(encoding="utf-8").replace("\r\n", "\n")
    head = FRONTMATTER.match(text)
    if not head:
        raise Refusal(f"{path.as_posix()}: no frontmatter between --- lines")
    front: dict[str, str] = {}
    for line in head.group(1).splitlines():
        if not line.strip():
            continue
        key, sep, value = line.partition(":")
        if not sep:
            raise Refusal(f"{path.as_posix()}: frontmatter line without a colon: {line!r}")
        front[key.strip()] = value.strip()
    missing = [key for key in FRONT_KEYS if key not in front]
    if missing:
        raise Refusal(f"{path.as_posix()}: frontmatter lacks {', '.join(missing)}")
    sections: dict[str, list[str]] = {}
    current = None
    for line in text[head.end() :].splitlines():
        if line.startswith("## "):
            current = line[3:].strip()
            sections[current] = []
        elif current is not None:
            sections[current].append(line)
    body = {name: "\n".join(lines).strip() for name, lines in sections.items()}
    empty = [name for name in SECTIONS if not body.get(name)]
    if empty:
        raise Refusal(f"{path.as_posix()}: the sections {', '.join(empty)} are missing or empty")
    row = {
        "id": front["id"],
        "slug": front["slug"],
        "version": int(front["version"]),
        "name": front["name"],
        "description": body["Description"],
        "standard": {"id": front["standard"], "citation": front["standard_citation"]},
        "inputs": [item.strip() for item in front["inputs"].split(",") if item.strip()],
        "criteria": body["Criteria"],
        "not_saying": body["What this Signal does not say"],
        "supersedes": None if front["supersedes"] in ("", "null") else front["supersedes"],
        "worked_example": {"fixture": front["fixture"], "expected": body["Worked example"]},
    }
    if row["id"] != f"sg:{row['slug']}:v{row['version']}":
        raise Refusal(f"{path.as_posix()}: id {row['id']} is not sg:<slug>:v<version>")
    if path.stem != row["slug"]:
        raise Refusal(
            f"{path.as_posix()}: the current definition of {row['slug']} lives at {row['slug']}.md"
        )
    unknown = [name for name in row["inputs"] if name not in INPUTS]
    if unknown:
        raise Refusal(f"{path.as_posix()}: inputs the runner cannot hand it: {', '.join(unknown)}")
    return row


def current_definitions(root: Path) -> list[Path]:
    """`<slug>.md` for every Signal; an earlier version, `<slug>.v<n>.md`, is kept to be read."""
    folder = root / DEFINITIONS
    return sorted(
        path
        for path in folder.glob("*.md")
        if path.name != "README.md" and not re.search(r"\.v\d+$", path.stem)
    )


def load_signal(root: Path, slug: str):
    path = root / "src" / "signals" / f"{slug}.py"
    if not path.is_file():
        raise Refusal(f"{slug}: no implementation at {path.relative_to(root).as_posix()}")
    spec = importlib.util.spec_from_file_location(slug.replace("-", "_"), path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def inputs_digest(root: Path) -> str:
    """The seal's rule (tools/verify.py) over the files a Signal reads: one line per file,
    its SHA-256, two spaces, its path; lines sorted; the SHA-256 of the lines."""
    lines = sorted(
        f"{hashlib.sha256((root / rel).read_bytes()).hexdigest()}  {rel}\n".encode()
        for rel in INPUTS.values()
    )
    return hashlib.sha256(b"".join(lines)).hexdigest()


# ---- the ledger ----------------------------------------------------------------------


def comparable(row: dict) -> dict:
    return {key: value for key, value in row.items() if key not in UNCOMPARED}


def fires(row: dict) -> bool:
    """A ledger row that records a firing. A correction recording that a Signal no longer
    fires on a report carries evidence with no row after the deadline."""
    return bool((row.get("evidence") or {}).get("after", 1))


def merge(
    ledger: list[dict], computed: list[dict], signal_id: str, at: str, digest: str
) -> list[dict]:
    """The ledger with this run's Findings added. Refuses, naming every case, rather than
    rewrite a Finding in place or let one go silently."""
    mine = [row for row in ledger if row["signal_id"] == signal_id]
    known = {row["id"] for row in mine}
    heads: dict[str, dict] = {}
    for row in mine:
        if row.get("superseded_by") is None:
            base = CORRECTION.sub("", row["id"])
            if base in heads:
                raise Refusal(
                    f"{base}: two rows in the ledger are both current; a chain has one head"
                )
            heads[base] = row
    now = {row["id"]: row for row in computed}
    problems, added = [], []
    for base in sorted(set(heads) | set(now) | {CORRECTION.sub("", i) for i in known}):
        head, found = heads.get(base), now.get(base)
        if head is None and found is None:
            continue
        if head is None:
            if base in known:
                problems.append(f"{base}: superseded, with no current row at the end of its chain")
                continue
            added.append({**found, "fired_at": at, "build_hash": digest})
        elif found is None:
            if fires(head):
                problems.append(
                    f"{head['id']}: published, and this run no longer produces it; facts stay, "
                    "so a person writes its correction by supersession, with the evidence"
                )
        elif not fires(head) or comparable(head) != comparable(found):
            problems.append(
                f"{head['id']}: published, and this run would produce it differently; a Finding "
                "is never rewritten in place, so a person writes the correction by supersession"
            )
    if problems:
        raise Refusal("the ledger would change a published Finding:\n  " + "\n  ".join(problems))
    return sorted(ledger + added, key=lambda row: row["id"])


def correct(
    ledger: list[dict],
    computed: list[dict],
    outcomes: list[dict],
    finding_id: str,
    because: str,
    at: str,
    digest: str,
    module,
) -> list[dict]:
    """The ledger with one correction written, or a refusal saying why there is none to write.

    The chain's current row gains `superseded_by` and nothing else. The new row is what the
    Signal now produces for the report, or, where it no longer fires there, the Signal's
    `withdrawal` row; either way it carries the person's reason as its notes, this build's
    time and the digest of the rows read."""
    if not CITED.search(because or ""):
        raise Refusal(
            "a correction cites the primary source that shows what changed: --because must "
            "say what changed and carry the source's URL"
        )
    base = CORRECTION.sub("", finding_id)
    chain = [row for row in ledger if CORRECTION.sub("", row["id"]) == base]
    heads = [row for row in chain if row.get("superseded_by") is None]
    if not chain:
        raise Refusal(f"{base}: not in the ledger, so there is nothing to correct")
    if len(heads) != 1:
        raise Refusal(f"{base}: the chain has {len(heads)} current rows; it must have one")
    head = heads[0]
    found = {row["id"]: row for row in computed}.get(base)
    if found is not None:
        if fires(head) and comparable(found) == comparable(head):
            raise Refusal(
                f"{head['id']}: the Signal still produces it as published; nothing to correct"
            )
        row = dict(found)
    else:
        if not fires(head):
            raise Refusal(f"{head['id']}: already records that the Signal does not fire there")
        if not hasattr(module, "withdrawal"):
            raise Refusal(f"{head['id']}: this Signal defines no words for a withdrawal")
        report = head["producing_filings"][0]
        row = module.withdrawal(head, next((o for o in outcomes if o["filing_id"] == report), None))
    n = 1 + max((int(m.group(1)) for r in chain if (m := CORRECTION.search(r["id"]))), default=0)
    row.update(id=f"{base}:c{n}", notes=because.strip(), fired_at=at, build_hash=digest)
    kept = [dict(r, superseded_by=row["id"]) if r is head else r for r in ledger]
    return sorted(kept + [row], key=lambda r: r["id"])


def run_record(signal_id: str, digest: str, outcomes: list[dict]) -> list[dict]:
    """What the run evaluated: one summary line, then one line per report, in id order."""
    by_state: dict[str, int] = {}
    not_evaluated: dict[str, int] = {}
    for outcome in outcomes:
        by_state[outcome["state"]] = by_state.get(outcome["state"], 0) + 1
        for reason, n in outcome["not_evaluated"].items():
            not_evaluated[reason] = not_evaluated.get(reason, 0) + n
    fired = [o for o in outcomes if o["finding_id"]]
    summary = {
        "signal_id": signal_id,
        "inputs_digest": digest,
        "reports": len(outcomes),
        "reports_by_state": by_state,
        "rows_evaluated": sum(o["evaluated"] for o in outcomes),
        "rows_after": sum(o["after"] for o in outcomes),
        "rows_not_evaluated": not_evaluated,
        "reports_with_a_finding": len(fired),
        "officeholders_with_a_finding": len({o["officeholder_id"] for o in fired}),
    }
    return [summary] + sorted(outcomes, key=lambda o: o["filing_id"])


# ---- the run -------------------------------------------------------------------------


def plan(root: Path, at: str | None, correction: tuple[str, str] | None = None) -> dict[str, str]:
    """Every file this run would write, as path -> text. Refuses before writing anything.
    With a correction, (finding id, reason), that correction is written into the ledger
    first, and then the run goes on as any other."""
    rows = {name: read_ndjson(root / rel) for name, rel in INPUTS.items()}
    digest = inputs_digest(root)
    ledger = read_ndjson(root / FINDINGS)
    carried = {row["id"]: row for row in read_ndjson(root / SIGNALS)}
    files: dict[str, str] = {}
    for path in current_definitions(root):
        definition = parse_definition(path)
        module = load_signal(root, definition["slug"])
        if (definition["id"], definition["version"]) != (module.SIGNAL_ID, module.VERSION):
            raise Refusal(
                f"{definition['slug']}: the definition says {definition['id']} and the "
                f"implementation says {module.SIGNAL_ID}; they must name one version"
            )
        carried[definition["id"]] = definition
        findings, outcomes = module.evaluate(
            rows["officeholder"], rows["filing"], rows["transaction"]
        )
        new = [f for f in findings if f["id"] not in {r["id"] for r in ledger}]
        if new and not at:
            raise Refusal("new Findings need the build's time: pass --at <built_at>")
        if correction and correction[0].startswith(f"fn:{definition['id']}:"):
            if not at:
                raise Refusal("a correction needs the build's time: pass --at <built_at>")
            ledger = correct(
                ledger, findings, outcomes, correction[0], correction[1], at, digest, module
            )
            correction = None
        ledger = merge(ledger, findings, definition["id"], at or "", digest)
        record = run_record(definition["id"], digest, outcomes)
        run_path = f"{RUNS}/{definition['slug']}-v{definition['version']}.ndjson"
        files[run_path] = render_ndjson(record)
    if correction:
        raise Refusal(f"{correction[0]}: no current Signal produced it; nothing to correct")
    files[SIGNALS] = render_ndjson(sorted(carried.values(), key=lambda row: row["id"]))
    files[FINDINGS] = render_ndjson(ledger)
    return files


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("root", nargs="?", default=".", help="repository root (default: .)")
    parser.add_argument("--at", help="the build's built_at, ISO 8601 UTC; given to new Findings")
    parser.add_argument(
        "--check", action="store_true", help="regenerate everything and compare; write nothing"
    )
    parser.add_argument(
        "--correct", metavar="FINDING_ID", help="write the correction of this published Finding"
    )
    parser.add_argument(
        "--because",
        metavar="TEXT",
        help="with --correct: what changed, citing the primary source that shows it by URL",
    )
    args = parser.parse_args(argv)
    if args.correct and args.check:
        parser.error("--correct writes; --check writes nothing; give one")
    if bool(args.correct) != bool(args.because):
        parser.error("--correct and --because go together")
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    root = Path(args.root).resolve()
    try:
        files = plan(root, args.at, (args.correct, args.because) if args.correct else None)
    except Refusal as refusal:
        print(f"REFUSED  {refusal}")
        return 1
    if args.check:
        stale = []
        for rel, text in files.items():
            path = root / rel
            if not path.is_file() or path.read_text(encoding="utf-8") != text:
                stale.append(rel)
        if stale:
            print("FAIL  the Signal files are not what the definitions and rows produce:")
            for rel in stale:
                print(f"      {rel}")
            print("      Run: python src/signals/run.py --at <built_at>, then re-seal.")
            return 1
        print(
            f"OK    {len(files)} Signal files regenerate byte-identically from the rows "
            "and definitions."
        )
        return 0
    for rel, text in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
    findings = read_ndjson(root / FINDINGS)
    for rel in sorted(files):
        if rel.startswith(RUNS):
            summary = read_ndjson(root / rel)[0]
            print(
                f"{summary['signal_id']}: {summary['reports']} reports; "
                f"{summary['rows_evaluated']} rows evaluated, "
                f"{summary['rows_after']} after the deadline; "
                f"{summary['reports_with_a_finding']} reports with a Finding, "
                f"{summary['officeholders_with_a_finding']} officeholders"
            )
    print(f"wrote {', '.join(sorted(files))}; the ledger holds {len(findings)} Findings")
    print(
        "Re-seal in this commit: python tools/seal.py --build <id> --built-at <time> --derive-state"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
