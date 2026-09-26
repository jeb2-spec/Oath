#!/usr/bin/env python3
"""A person corrects a published row, or records that it stands, citing the evidence.

INVARIANTS.md §14 says change is shown by supersession, not by removal, and BYLAWS.md §5
and §6 say how a correction is made: a person, the primary source that shows it, a row a
reader can see. This is that row's writer for the register's own rows (an officeholder, a
filing, a transaction); a Finding is corrected by `src/signals/run.py --correct`.

It writes one row to the end of data/changes.ndjson, whose change is "corrected": the row,
the fact (`--field`, a path such as filed_at or source.content_hash), what it carried
(`was`), what it carries now (`now`), the kind (the source now states it otherwise, or the
register read or joined it wrongly), the reason, who decided and when, and the evidence as
a capture: the URL at a source SOURCES.md registers as primary, and the SHA-256 of the
evidence's bytes, which it keeps at data/captures/sha256/<sha256> so the correction can be checked
from the repository alone. Then it moves the fact in the row. tools/check-removals.py lets
that move through, and no other.

With `--stands` it moves nothing: it records that the published value stands against a
reading that disagrees (the adapter's join, or a document), and the adapter, which refuses
to go on while a published attribution is in question, goes on. Either way the adapter
never again weighs that fact of that row against what it reads.

    python tools/correct.py --row fl:house-clerk:P:20027846 --field filed_at --now 2025-02-26 \\
        --kind source --because "The Clerk's index read 2026-10-05 dates the report 2025-02-26." \\
        --evidence-url https://disclosures-clerk.house.gov/public_disc/financial-pdfs/2025FD.zip \\
        --evidence-file 2025FD.zip --decided-by "the maintainer"

Then run the Signal (`python src/signals/run.py --at <built_at>`): where the move changes
a Finding, it refuses and names it, and `run.py --correct` supersedes it with the same
evidence. Then re-seal. Standard library.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlsplit

FILES = {"oh": "officeholders", "fl": "filings", "tx": "transactions"}
FRAME = "Presence in the register is not evidence of wrongdoing."
KINDS = ("source", "register")
MISSING = object()


class Refusal(Exception):
    pass


def canonical(row: dict) -> str:
    """One NDJSON line, as the adapter writes it."""
    return json.dumps(row, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n"


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
    decided_by: str,
    decided_at: str,
) -> tuple[str, list[str], dict, str]:
    """(the rows file, its new lines, the change row, the kept capture's path) for one
    correction, or a refusal saying why there is none to write."""
    rows = FILES.get(row_id.split(":", 1)[0])
    if rows is None:
        raise Refusal(f"{row_id}: not a row of the register's own files ({', '.join(FILES)})")
    if kind not in KINDS:
        raise Refusal(f"a correction's kind is one of {', '.join(KINDS)}, not {kind!r}")
    if not because.strip() or not decided_by.strip():
        raise Refusal("a correction says why (--because) and who decided (--decided-by)")
    host = (urlsplit(evidence_url).hostname or "").lower()
    primary = primary_hosts(root)
    if urlsplit(evidence_url).scheme != "https" or host not in primary:
        raise Refusal(
            "a correction cites a primary source: --evidence-url must be an https URL at a "
            f"host SOURCES.md registers as primary ({', '.join(sorted(primary))})"
        )
    if not evidence:
        raise Refusal("--evidence-file is empty; a correction keeps the bytes it rests on")
    path = root / "data" / f"{rows}.ndjson"
    lines = path.read_text("utf-8").splitlines(keepends=True) if path.is_file() else []
    found = [n for n, line in enumerate(lines) if json.loads(line)["id"] == row_id]
    if not found:
        raise Refusal(f"{row_id}: not in data/{rows}.ndjson")
    row = json.loads(lines[found[0]])
    was = fact(row, field)
    if was is MISSING:
        raise Refusal(f"{row_id}: carries no {field}")
    if stands and now is not MISSING:
        raise Refusal("--stands records that the published value stands; give no --now")
    if not stands and now is MISSING:
        raise Refusal("give --now, the value the row should carry, or --stands")
    if stands:
        now = was
    elif now == was:
        raise Refusal(f"{row_id}: {field} already carries {json.dumps(now)}; nothing to move")
    sha = hashlib.sha256(evidence).hexdigest()
    kept = f"data/captures/sha256/{sha}{Path(evidence_name).suffix}"
    change = {
        "id": f"ch:corrected:{row_id}:{field}:{decided_at}",
        "row_id": row_id,
        "rows": rows,
        "change": "corrected",
        "field": field,
        "was": was,
        "now": now,
        "kind": kind,
        "because": because.strip(),
        "decided_by": decided_by.strip(),
        "decided_at": decided_at,
        "capture": {"url": evidence_url, "retrieved_at": decided_at, "content_hash": sha},
        "frame": FRAME,
    }
    changes = root / "data" / "changes.ndjson"
    if changes.is_file() and any(
        json.loads(line)["id"] == change["id"] for line in changes.read_text("utf-8").splitlines()
    ):
        raise Refusal(f"{change['id']} is already recorded")
    if not stands:
        lines[found[0]] = canonical(moved(row, field, now))
    return f"data/{rows}.ndjson", lines, change, kept


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
        rel, lines, change, kept = correction(
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
            args.decided_by,
            decided_at,
        )
    except Refusal as refusal:
        print(f"REFUSED  {refusal}")
        return 1
    what = (
        "stands" if args.stands else f"{json.dumps(change['was'])} -> {json.dumps(change['now'])}"
    )
    print(f"{change['row_id']} {change['field']}: {what}")
    print(f"evidence kept at {kept}")
    if args.dry_run:
        print("dry run: nothing written")
        return 0
    target = root / kept
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.is_file():
        target.write_bytes(evidence.read_bytes())
    (root / rel).write_text("".join(lines), encoding="utf-8", newline="\n")
    with (root / "data" / "changes.ndjson").open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(canonical(change))
    print(
        f"wrote {rel} and data/changes.ndjson. Next: python src/signals/run.py --at <built_at>; "
        "where it refuses a Finding this moves, supersede it with run.py --correct, citing "
        "the same evidence; then re-seal."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
