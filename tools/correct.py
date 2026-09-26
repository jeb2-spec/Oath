#!/usr/bin/env python3
"""The maintainer corrects a published row, or records that it stands, citing the evidence.

INVARIANTS.md §14 says change is shown by supersession, not by removal, and BYLAWS.md §5
and §6 say how a correction is made: a person, the primary source that shows it, a row a
reader can see. This is that row's writer for the register's own rows (an officeholder, a
filing, a transaction); a Finding is corrected by `src/signals/run.py --correct`.

It writes to the end of data/changes.ndjson one row whose change is "corrected" for each fact
it moves: the row, the fact (`--field`, a path such as filed_at or source.content_hash), what
it carried (`was`), what it carries now (`now`), the kind (the source now states it
otherwise, or the register read or joined it wrongly), the reason, who decided and when,
and the evidence as a capture: the URL at a source SOURCES.md registers as primary, when
those bytes were retrieved, and their SHA-256, which it keeps at
data/captures/sha256/<sha256><ext> so the correction can be checked from the repository
alone, unless the evidence is a filed document (a PDF): that it cites by its SHA-256 and
never keeps, because a filed document can carry the names of private people and a kept copy
would outlast the Clerk's withdrawal or redaction of it (EVIDENCE.md §7). A correction of a
transaction's asset or notes, the filer's own text, keeps the SHA-256 of what it carried
(`was_sha256`), never the text. Then it moves the facts. tools/check-removals.py lets those
moves through, and no other.

An attribution moves whole. Moving a filing's officeholder_id also moves its office_id to
the office the officeholder named holds in the same Congress, and the officeholder_id of
every transaction of the filing, each as a correction row of its own citing the same
evidence; a transaction's officeholder is never moved by itself (the Council's second
reading of S.1b, Seat C). An officeholder named who holds no single office in that Congress
is refused.

With `--stands` it moves nothing: it records that the published value stands against a
reading that disagrees (the adapter's join, or a document), and the adapter, which refuses
to go on while a published attribution is in question, goes on. The adapter never again
refuses that fact of that row on a reading of an unchanged entry; what the source's own
bytes later show about it is still recorded.

With `--field transactions` on a filing it moves nothing either: it records how many rows the
report's own bytes list (`--now`, as JSON), where a later reading of the very bytes its rows
were published from finds more. The adapter refuses such rows until this decision names the
bytes (the evidence is the document, whose SHA-256 must be the filing's) and the count; the
source did not change, so its kind is register.

    python tools/correct.py --row fl:house-clerk:P:<DocID> --field filed_at --now <YYYY-MM-DD> \\
        --kind source --because "The Clerk's index read <date> dates the report <YYYY-MM-DD>." \\
        --evidence-url https://disclosures-clerk.house.gov/public_disc/financial-pdfs/<y>FD.zip \\
        --evidence-file <y>FD.zip --evidence-retrieved-at <YYYY-MM-DDTHH:MM:SSZ> \\
        --decided-by "the maintainer"

Then run the Signal (`python src/signals/run.py --at <built_at>`): where the move changes
a Finding, it refuses and names it, and `run.py --correct` supersedes it with the same
evidence. Then re-seal. Standard library.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import sys
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlsplit

FILES = {"oh": "officeholders", "fl": "filings", "tx": "transactions"}
# A transaction's facts that are the filer's own text: a correction keeps their hash, not them.
AS_FILED = frozenset({"asset", "notes"})
FRAME = "Presence in the register is not evidence of wrongdoing."
KINDS = ("source", "register")
MISSING = object()
UTC_TIME = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


class Refusal(Exception):
    pass


def canonical(row: dict) -> str:
    """One NDJSON line, as the adapter writes it."""
    return json.dumps(row, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n"


def json_of(value) -> str:
    """A value as canonical JSON, the form whose SHA-256 a correction keeps for as-filed text,
    and the form tools/check-removals.py hashes to match it."""
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def primary_hosts(root: Path) -> set[str]:
    """The hosts SOURCES.md registers as primary, read the way the §5 gate reads them."""
    spec = importlib.util.spec_from_file_location(
        "aggregator_sole", root / "tools" / "check-aggregator-sole.py"
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    primary, _ = module.registry((root / "SOURCES.md").read_text("utf-8"))
    return primary


def fact(row: dict, field: str):
    """The value at a dotted path in a row, or MISSING."""
    value = row
    for key in field.split("."):
        if not isinstance(value, dict) or key not in value:
            return MISSING
        value = value[key]
    return value


def moved(row: dict, field: str, now) -> dict:
    """The row with the fact at `field` set to `now`, every other byte as it was."""
    head, _, rest = field.partition(".")
    return {**row, head: moved(row[head], rest, now) if rest else now}


def read_lines(root: Path, rows: str) -> list[str]:
    path = root / "data" / f"{rows}.ndjson"
    return path.read_text("utf-8").splitlines(keepends=True) if path.is_file() else []


def moves_of(
    root: Path, row_id: str, field: str, was, now
) -> list[tuple[str, str, object, object]]:
    """Every (row, fact, was, now) a correction moves: one fact, or an attribution whole."""
    moves = [(row_id, field, was, now)]
    kind = row_id.split(":", 1)[0]
    if field == "officeholder_id" and kind == "tx":
        raise Refusal(
            f"{row_id}: a transaction's officeholder is its filing's; correct the filing's "
            "officeholder_id, and its transactions move with it"
        )
    if field == "office_id" and kind == "fl":
        filing = next(
            json.loads(line)
            for line in read_lines(root, "filings")
            if json.loads(line)["id"] == row_id
        )
        holder = next(
            (
                json.loads(line)
                for line in read_lines(root, "officeholders")
                if json.loads(line)["id"] == filing["officeholder_id"]
            ),
            {},
        )
        if now not in {o["id"] for o in holder.get("offices", [])}:
            raise Refusal(
                f"{now}: not an office {filing['officeholder_id']} holds; an office moves only "
                "to one its officeholder holds, or with its attribution (correct officeholder_id)"
            )
    if field != "officeholder_id" or kind != "fl":
        return moves
    holders = {
        json.loads(line)["id"]: json.loads(line) for line in read_lines(root, "officeholders")
    }
    if now not in holders:
        raise Refusal(f"{now}: not an officeholder the register holds")
    filing = next(
        json.loads(line) for line in read_lines(root, "filings") if json.loads(line)["id"] == row_id
    )
    offices = {json.loads(line)["id"]: json.loads(line) for line in read_lines(root, "offices")}
    began = (offices.get(filing["office_id"]) or {}).get("term_start")
    theirs = [o["id"] for o in holders[now].get("offices", []) if o.get("term_start") == began]
    if len(theirs) != 1:
        raise Refusal(
            f"{now} holds {len(theirs)} offices of the Congress {filing['office_id']} is of; an "
            "attribution moves only to an officeholder who held one office in it"
        )
    if theirs[0] != filing["office_id"]:
        moves.append((row_id, "office_id", filing["office_id"], theirs[0]))
    for line in read_lines(root, "transactions"):
        tx = json.loads(line)
        if tx.get("filing_id") == row_id:
            moves.append((tx["id"], "officeholder_id", tx["officeholder_id"], now))
    return moves


def correction(
    root: Path,
    row_id: str,
    field: str,
    now,
    stands: bool,
    kind: str,
    because: str,
    evidence_url: str,
    evidence: bytes,
    evidence_name: str,
    evidence_retrieved_at: str,
    decided_by: str,
    decided_at: str,
) -> tuple[dict[str, list[str]], list[dict], str]:
    """(each rows file it rewrites, as its new lines; the change rows; the kept capture's
    path) for one correction, or a refusal saying why there is none to write."""
    rows = FILES.get(row_id.split(":", 1)[0])
    if rows is None:
        raise Refusal(f"{row_id}: not a row of the register's own files ({', '.join(FILES)})")
    if kind not in KINDS:
        raise Refusal(f"a correction's kind is one of {', '.join(KINDS)}, not {kind!r}")
    if not because.strip() or not decided_by.strip():
        raise Refusal("a correction says why (--because) and who decided (--decided-by)")
    if not UTC_TIME.match(evidence_retrieved_at or ""):
        raise Refusal(
            "--evidence-retrieved-at gives when the evidence's bytes were retrieved, as "
            "YYYY-MM-DDTHH:MM:SSZ; a correction never dates its evidence by the day it was made"
        )
    host = (urlsplit(evidence_url).hostname or "").lower()
    primary = primary_hosts(root)
    if urlsplit(evidence_url).scheme != "https" or host not in primary:
        raise Refusal(
            "a correction cites a primary source: --evidence-url must be an https URL at a "
            f"host SOURCES.md registers as primary ({', '.join(sorted(primary))})"
        )
    if not evidence:
        raise Refusal("--evidence-file is empty; a correction hashes the bytes it rests on")
    sha = hashlib.sha256(evidence).hexdigest()
    lines = read_lines(root, rows)
    found = [n for n, line in enumerate(lines) if json.loads(line)["id"] == row_id]
    if not found:
        raise Refusal(f"{row_id}: not in data/{rows}.ndjson")
    if stands and now is not MISSING:
        raise Refusal("--stands records that the published value stands; give no --now")
    if not stands and now is MISSING:
        raise Refusal("give --now, the value the row should carry, or --stands")
    row = json.loads(lines[found[0]])
    if field == "transactions" and rows == "filings":
        mine = [json.loads(line) for line in read_lines(root, "transactions")]
        was = sum(1 for tx in mine if tx["filing_id"] == row_id)
        if stands or kind != "register" or not isinstance(now, int) or now <= was:
            raise Refusal(
                "--field transactions records, as --now (JSON), how many rows the report's own "
                f"bytes list, more than the {was} published; its kind is register, because the "
                "source did not change"
            )
        if sha != (row.get("source") or {}).get("content_hash"):
            raise Refusal(
                "--field transactions cites the document the rows were published from: the "
                "evidence's SHA-256 must be the filing's source.content_hash"
            )
        moves = [(row_id, field, was, now)]
        stands = True  # moves no fact of any row
    else:
        was = fact(row, field)
        if was is MISSING:
            raise Refusal(f"{row_id}: carries no {field}")
        if isinstance(was, (list, dict)):
            raise Refusal(
                f"{row_id}: {field} is a {'list' if isinstance(was, list) else 'group of facts'}; "
                "a correction moves one fact, a value, named by its path"
            )
        if stands:
            moves = [(row_id, field, was, was)]
        elif now == was:
            raise Refusal(f"{row_id}: {field} already carries {json.dumps(now)}; nothing to move")
        else:
            moves = moves_of(root, row_id, field, was, now)
    document = any(
        name.lower().endswith(".pdf") for name in (urlsplit(evidence_url).path, evidence_name)
    )
    kept = "" if document else f"data/captures/sha256/{sha}{Path(evidence_name).suffix}"
    changes, files = [], {}
    recorded = root / "data" / "changes.ndjson"
    known = (
        {json.loads(line)["id"] for line in recorded.read_text("utf-8").splitlines() if line}
        if recorded.is_file()
        else set()
    )
    for moved_id, moved_field, moved_was, moved_now in moves:
        moved_rows = FILES[moved_id.split(":", 1)[0]]
        as_filed = moved_rows == "transactions" and moved_field in AS_FILED
        change = {
            "id": f"ch:corrected:{moved_id}:{moved_field}:{decided_at}",
            "row_id": moved_id,
            "rows": moved_rows,
            "change": "corrected",
            "field": moved_field,
            **(
                {"was_sha256": hashlib.sha256(json_of(moved_was).encode()).hexdigest()}
                if as_filed
                else {"was": moved_was}
            ),
            "now": moved_now,
            "kind": kind,
            "because": because.strip(),
            "decided_by": decided_by.strip(),
            "decided_at": decided_at,
            "capture": {
                "url": evidence_url,
                "retrieved_at": evidence_retrieved_at,
                "content_hash": sha,
            },
            "frame": FRAME,
        }
        if change["id"] in known:
            raise Refusal(f"{change['id']} is already recorded")
        changes.append(change)
        if stands:
            continue
        rel = f"data/{moved_rows}.ndjson"
        current = files.get(rel) or read_lines(root, moved_rows)
        at = next(n for n, line in enumerate(current) if json.loads(line)["id"] == moved_id)
        current[at] = canonical(moved(json.loads(current[at]), moved_field, moved_now))
        files[rel] = current
    return files, changes, kept


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("root", nargs="?", default=".", help="repository root (default: .)")
    parser.add_argument("--row", required=True, help="the row's id")
    parser.add_argument("--field", required=True, help="the fact, a path such as filed_at")
    parser.add_argument("--now", help="the value the row should carry (a string)")
    parser.add_argument("--json", action="store_true", help="read --now as JSON, not a string")
    parser.add_argument("--stands", action="store_true", help="the published value stands")
    parser.add_argument("--kind", required=True, choices=KINDS)
    parser.add_argument("--because", required=True, help="one sentence: what the evidence shows")
    parser.add_argument("--evidence-url", required=True, help="where the evidence is published")
    parser.add_argument("--evidence-file", required=True, help="a copy of the evidence's bytes")
    parser.add_argument(
        "--evidence-retrieved-at",
        required=True,
        help="when those bytes were retrieved from the URL, YYYY-MM-DDTHH:MM:SSZ",
    )
    parser.add_argument("--decided-by", required=True, help="who decided, by role")
    parser.add_argument("--decided-at", help="when, ISO 8601 UTC (default: now)")
    parser.add_argument("--dry-run", action="store_true", help="say what it would write")
    args = parser.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    root = Path(args.root).resolve()
    now = MISSING if args.now is None else (json.loads(args.now) if args.json else args.now)
    decided_at = args.decided_at or datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    evidence = Path(args.evidence_file)
    try:
        files, changes, kept = correction(
            root,
            args.row,
            args.field,
            now,
            args.stands,
            args.kind,
            args.because,
            args.evidence_url,
            evidence.read_bytes() if evidence.is_file() else b"",
            evidence.name,
            args.evidence_retrieved_at,
            args.decided_by,
            decided_at,
        )
    except Refusal as refusal:
        print(f"REFUSED  {refusal}")
        return 1
    for change in changes:
        was = change.get("was", "(the filer's text, kept as its SHA-256)")
        what = (
            "stands"
            if args.stands
            else f"{json.dumps(was, ensure_ascii=False)} -> {json.dumps(change['now'])}"
        )
        print(f"{change['row_id']} {change['field']}: {what}")
    sha = changes[0]["capture"]["content_hash"]
    if args.dry_run:
        cited = f"would be kept at {kept}" if kept else f"cited by its SHA-256, {sha}"
        print(f"evidence {cited}\ndry run: nothing written")
        return 0
    if kept:
        target = root / kept
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.is_file():
            target.write_bytes(evidence.read_bytes())
        print(f"evidence kept at {kept}")
    else:
        print(f"evidence cited by its SHA-256, {sha}; a filed document is never kept")
    for rel, lines in files.items():
        (root / rel).write_text("".join(lines), encoding="utf-8", newline="\n")
    with (root / "data" / "changes.ndjson").open("a", encoding="utf-8", newline="\n") as handle:
        for change in changes:
            handle.write(canonical(change))
    print(
        f"wrote {', '.join(sorted(files)) or 'no rows'} and data/changes.ndjson. Next: python "
        "src/signals/run.py --at <built_at>; where it refuses a Finding this moves, supersede "
        "it with run.py --correct, citing the same evidence; then re-seal."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
