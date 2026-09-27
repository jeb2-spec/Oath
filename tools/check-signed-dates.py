#!/usr/bin/env python3
"""Whether the date the Clerk's index gives a transaction report is the day its filer signed it.

Every Finding here rests on one date per report, the `FilingDate` of the Clerk's index, and
nothing the Clerk or the Committee publishes says what that field records: the day the member
filed, or the day the Clerk published (docs/wanted/wanted.ndjson, wt:the-clerks-filing-date).
The documents answer it themselves. A report filed electronically ends on a line the filing
system prints, "Digitally Signed: <name> , MM/DD/YYYY". This reads that line on every
transaction report the register holds a hash for, on bytes whose SHA-256 is the sealed one,
and compares its date with the index's.

It needs the network (the Clerk's copies are fetched politely, one at a time, with the
adapter's user agent and pause) unless `--from` names a folder of copies already fetched; a
copy is used only if its hash is the sealed one, so a local folder cannot change the answer.
It prints counts and document ids, never a name. It exits 1 when any report it could read was
signed on another day than the index gives it, because then a sentence here about a report
dated after a deadline could be wrong about a person.

    python tools/check-signed-dates.py                  # fetch from the Clerk (about 25 minutes)
    python tools/check-signed-dates.py --from <folder>  # <DocID>.pdf copies already fetched
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

SIGNED = re.compile(r"Digitally Signed:[^\n]*?,\s*(\d{2})/(\d{2})/(\d{4})")


def signed_on(text: str) -> str | None:
    """The date the report's last signature line gives, as YYYY-MM-DD, or None."""
    found = SIGNED.findall(text)
    if not found:
        return None
    month, day, year = found[-1]
    return f"{year}-{month}-{day}"


def load(root: Path, name: str, path: str):
    spec = importlib.util.spec_from_file_location(name, root / path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--from", dest="folder", help="a folder of <DocID>.pdf copies")
    args = parser.parse_args(argv)
    root = Path(__file__).resolve().parent.parent
    ptr = load(root, "ptr", "src/adapters/house-fd/ptr.py")
    fetch = load(root, "fetch", "src/adapters/house-fd/fetch.py")
    rows = [
        json.loads(line)
        for line in (root / "data" / "filings.ndjson").read_text("utf-8").splitlines()
        if line.strip()
    ]
    reports = [r for r in rows if r.get("source_form_code") == "P" and r["source"].get("url")]
    fired = {
        json.loads(line)["producing_filings"][0]
        for line in (root / "data" / "findings.ndjson").read_text("utf-8").splitlines()
        if line.strip()
    }
    counts = {"same day": 0, "another day": 0, "no signature line": 0, "not the sealed bytes": 0}
    differs: list[str] = []
    with tempfile.TemporaryDirectory() as scratch:
        for report in reports:
            url = report["source"]["url"]
            name = url.rsplit("/", 1)[1]
            local = Path(args.folder) / name if args.folder else None
            if local is not None and local.is_file():
                data = local.read_bytes()
            else:
                request = urllib.request.Request(url, headers={"User-Agent": fetch.AGENT})
                with urllib.request.urlopen(request, timeout=60) as response:  # noqa: S310
                    data = response.read()
                time.sleep(fetch.PAUSE_SECONDS)
            if hashlib.sha256(data).hexdigest() != report["source"].get("content_hash"):
                counts["not the sealed bytes"] += 1
                continue
            path = Path(scratch) / name
            path.write_bytes(data)
            date = signed_on(ptr.extract_text(path))
            if date is None:
                counts["no signature line"] += 1
            elif date == report["filed_at"]:
                counts["same day"] += 1
            else:
                counts["another day"] += 1
                mark = ", a Finding rests on it" if report["id"] in fired else ""
                differs.append(f"{name}: index {report['filed_at']}, signed {date}{mark}")
    print(f"{len(reports):,} transaction reports with a sealed hash")
    for label, n in counts.items():
        print(f"  {n:5,}  {label}")
    for line in differs:
        print(f"  differs  {line}")
    if counts["another day"]:
        print("FAIL  the index date is not the signature date on every report the register read")
        return 1
    print(
        "OK    on every report whose signature line the register can read, the index date is "
        "the day the filer signed it"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
