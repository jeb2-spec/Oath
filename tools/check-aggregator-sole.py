#!/usr/bin/env python3
"""No aggregator is the sole source for a Finding. INVARIANTS.md §5; RUBRIC.md gate 1.

Reads the source registry from SOURCES.md itself: every URL host in a section whose
heading says *primary* is a primary source, every host in a section whose heading says
*corroborating* or *aggregator* is an aggregator. Then, for every Finding in
`data/findings.ndjson`, it follows each producing filing, and the officeholder, to the
row's own `source.url`, and fails when a host is registered only as an aggregator, or is
not registered at all. The registry is the document a reader already reads, so a new
source enters by the same pull request that adds it to SOURCES.md. Standard library.

    python tools/check-aggregator-sole.py

Example of a failing input: a filing whose source.url is on opensecrets.org, named by a
Finding.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlsplit

HOST = re.compile(r"https?://([A-Za-z0-9.-]+)")


def registry(text: str) -> tuple[set[str], set[str]]:
    """(primary hosts, aggregator hosts) from the level-two sections of SOURCES.md."""
    primary: set[str] = set()
    aggregators: set[str] = set()
    kind = None
    for line in text.splitlines():
        if line.startswith("## "):
            heading = line.lower()
            kind = (
                "primary"
                if "primary" in heading
                else "aggregator"
                if "corroborating" in heading or "aggregator" in heading
                else None
            )
            continue
        if kind is None:
            continue
        hosts = {h.lower().rstrip(".") for h in HOST.findall(line)}
        (primary if kind == "primary" else aggregators).update(hosts)
    return primary, aggregators


def read(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text("utf-8").splitlines() if line.strip()]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("root", nargs="?", default=".", help="repository root (default: .)")
    args = parser.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    root = Path(args.root).resolve()
    primary, aggregators = registry((root / "SOURCES.md").read_text("utf-8"))
    if not primary:
        print("FAIL  SOURCES.md registers no primary source; nothing could be traced")
        return 1
    filings = {row["id"]: row for row in read(root / "data" / "filings.ndjson")}
    holders = {row["id"]: row for row in read(root / "data" / "officeholders.ndjson")}
    findings = read(root / "data" / "findings.ndjson")
    problems, hosts_used = [], set()
    for found in findings:
        sources = [("officeholder", holders.get(found["officeholder_id"]))]
        sources += [("filing", filings.get(fid)) for fid in found["producing_filings"]]
        for kind, row in sources:
            if row is None:
                problems.append(f"{found['id']}: names a {kind} the register does not hold")
                continue
            host = (urlsplit(row.get("source", {}).get("url", "")).hostname or "").lower()
            hosts_used.add(host)
            if host in primary:
                continue
            if host in aggregators:
                problems.append(
                    f"{found['id']}: its {kind} {row['id']} rests on {host}, an aggregator"
                )
            else:
                problems.append(
                    f"{found['id']}: its {kind} {row['id']} rests on {host or 'no URL'}, "
                    "not in SOURCES.md"
                )
    if problems:
        print(f"FAIL  {len(problems)} Finding sources are not a registered primary source:")
        for line in problems:
            print(f"      {line}")
        return 1
    used = ", ".join(sorted(hosts_used)) or "none"
    print(
        f"OK    {len(findings)} Findings; every producing filing and officeholder rests on a "
        "primary "
        f"source SOURCES.md registers ({used}); no aggregator is the sole source of any."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
