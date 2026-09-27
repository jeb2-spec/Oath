#!/usr/bin/env python3
"""A figure about the register names no person. INVARIANTS.md §7 and §13; COUNCIL.md §5, mode 8.

Reads the sealed state of the build (`data/meta.json`, its `state` sentence) and every run
record under `data/adapter-runs/` (the keys of `rejected_by_reason`, and every other string a
run record carries outside its sources), and fails where one of them names an officeholder the
register holds or places a row: a common or legal name from `data/officeholders.ndjson`, a seat
code, an officeholder id, or a DocID.

These two files are published, sealed and anchored, and `README.md` sends readers to them for
"what was set aside and why". They had no lint. The Council's fifth reading of S.1b found that
one line of the adapter had turned the one sentence the register seals about itself into
seventy-three named officeholders with a count each, ordered by that count, a third of the
counts being a count of exactly one row about exactly one person. Every other gate passed, and
the seal's own figure guard had been switched off by the same line. Six of the seven seats
reached it independently, and every one of them asked for this gate.

A count is a fact about the register. A count beside a name is a claim about a person, and this
register does not make claims about persons. So: no name, and nothing that stands in for one.

A build with no sealed state fails, and so does one with no run record: a gate that reads
nothing proves nothing. Standard library, and no code shared with the seal or the renderer.

    python tools/lint-no-names.py
    python tools/lint-no-names.py .
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# What stands in for a person: the seat they hold, their row's id, and the DocID of a filing.
# A filing year and a comma-grouped figure are facts about the build, so a four-digit run of
# digits passes and a longer one does not; digits inside a longer token are part of a fingerprint
# or a capture key, which are facts about bytes.
PLACES_SOMEONE = (
    (re.compile(r"\b[A-Z]{2}\d{2}\b"), "a seat"),
    (re.compile(r"\boh:us:[a-z0-9:-]+"), "an officeholder's id"),
    (re.compile(r"(?<![\w,-])\d{5,}(?![\w,-])"), "a DocID"),
)
# Where a run record legitimately carries a name: the sources it read, which are files at the
# Clerk, and the key that names the captures a build was made from. `read_at` is the same class:
# the Clerk's documents the build read, each by its DocID, with the time it read it, written so a
# later read that finds other bytes is measured from a dated read (the Council's fourth reading
# of S.1b, Seat G). It is a time beside a file, never a figure beside a person, and a DocID
# anywhere else in a run record still fails. Before 2026-09-27 no sealed run record carried it,
# so this gate had never read one; the first build to write it would have failed here.
NOT_ABOUT_A_PERSON = {"sources", "capture_key", "build", "adapter", "year", "read_at"}


def names(root: Path) -> list[str]:
    """Every name the register publishes for an officeholder it holds, longest first, so the
    fuller form of a name is reported rather than the surname inside it."""
    path = root / "data" / "officeholders.ndjson"
    found: set[str] = set()
    for line in path.read_text("utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        for key in ("common_name", "legal_name"):
            if row.get(key):
                found.add(row[key])
    return sorted(found, key=len, reverse=True)


def strings(value, skip: set[str] = frozenset()) -> list[str]:
    """Every string inside a run record, keys as well as values, by the keys that are about the
    register's own work. A key is read because `rejected_by_reason` says why rows wait in its
    keys, and that is where the defect this gate exists for put the names."""
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        return [s for k, v in value.items() if k not in skip for s in [k, *strings(v, skip)]]
    if isinstance(value, list):
        return [s for v in value for s in strings(v, skip)]
    return []


def problems(root: Path) -> list[str]:
    """Each place a sealed figure names a person or places them, in the words it used."""
    out: list[str] = []
    roster = names(root)
    surfaces: list[tuple[str, list[str]]] = []

    meta = root / "data" / "meta.json"
    if not meta.is_file():
        return [f"{meta}: no sealed state to read; a gate that reads nothing proves nothing"]
    state = json.loads(meta.read_text("utf-8")).get("state")
    if not isinstance(state, str) or not state.strip():
        return [f"{meta}: carries no state sentence"]
    surfaces.append(("data/meta.json (state)", [state]))

    records = sorted((root / "data" / "adapter-runs").glob("*.ndjson"))
    if not records:
        return ["data/adapter-runs/: no run record to read; the build records its own state"]
    for path in records:
        for line in path.read_text("utf-8").splitlines():
            if line.strip():
                said = strings(json.loads(line), NOT_ABOUT_A_PERSON)
                surfaces.append((f"data/adapter-runs/{path.name}", said))

    for where, said in surfaces:
        for text in said:
            for name in roster:
                if name in text:
                    out.append(f"{where}: names an officeholder the register holds ({name!r})")
                    break
            for pattern, what in PLACES_SOMEONE:
                found = pattern.search(text)
                if found:
                    out.append(f"{where}: carries {what} ({found.group(0)!r})")
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", default=".", help="repository root (default: .)")
    args = parser.parse_args(argv)
    found = problems(Path(args.root).resolve())
    for line in found:
        print(f"FAIL {line}")
    if found:
        print(
            f"\n{len(found)} place{'' if len(found) == 1 else 's'} where a figure about the "
            "register names a person or places them. A count is a fact about the register; a "
            "count beside a name is a claim about a person. Say the condition, not the person, "
            "and keep the specifics on the row (INVARIANTS.md §7, §13)."
        )
        return 1
    print("OK the sealed state and every run record name no officeholder and place no row")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
