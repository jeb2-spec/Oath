#!/usr/bin/env python3
"""Retrieve the House Clerk's roster and filing index, and record what arrived.

PIPELINE.md Stage 1. Two files, both public, both served without authentication:

  https://clerk.house.gov/xml/lists/MemberData.xml
  https://disclosures-clerk.house.gov/public_disc/financial-pdfs/<year>FD.zip

The bytes land in `data/cache/house-fd/`, which is gitignored. Beside them,
`capture.json` records for each retrieval the url, the time it was retrieved, the
SHA-256 of the bytes, and the response headers that say when the source last
changed. Every row the adapter writes cites that record, so a reader can ask which
retrieval a row came from and check the hash themselves.

The index is not an annual artefact. The 2025 archive was last modified the day it
was first retrieved here, partway through 2026, so it is a live file that grows as
filings arrive. A build is therefore a statement about one retrieval, not about a
year, which is exactly what a seal is for.

Politeness: one request at a time, a real user agent naming the project, and a
pause between requests. The Clerk publishes no robots.txt (the path returns 404,
checked 2026-09-22) and SOURCES.md F.1 records that bulk download is permitted.

    python src/adapters/house-fd/fetch.py --year 2025
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
import urllib.request
import zipfile
from datetime import UTC, datetime
from pathlib import Path

CACHE = Path("data/cache/house-fd")
AGENT = (
    "Oath-register/0.1 (public-record research; +https://github.com/jeb2-spec/Oath; "
    "operator@veraproject.xyz)"
)
ROSTER = "https://clerk.house.gov/xml/lists/MemberData.xml"
INDEX = "https://disclosures-clerk.house.gov/public_disc/financial-pdfs/{year}FD.zip"
PAUSE_SECONDS = 3


def retrieve(url: str, destination: Path) -> dict:
    """Fetch one url to a file and return what should be recorded about it."""
    request = urllib.request.Request(url, headers={"User-Agent": AGENT})
    with urllib.request.urlopen(request, timeout=300) as response:  # noqa: S310 (https, fixed hosts)
        body = response.read()
        headers = dict(response.headers)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(body)
    return {
        "url": url,
        "retrieved_at": datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "sha256": hashlib.sha256(body).hexdigest(),
        "bytes": len(body),
        "last_modified": headers.get("Last-Modified"),
        "etag": headers.get("ETag"),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--year", type=int, required=True, help="filing year, e.g. 2025")
    args = parser.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    manifest_path = CACHE / "capture.json"
    manifest = {}
    if manifest_path.is_file():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    for url, name in (
        (ROSTER, "MemberData.xml"),
        (INDEX.format(year=args.year), f"{args.year}FD.zip"),
    ):
        record = retrieve(url, CACHE / name)
        manifest[name] = record
        print(f"{name}: {record['bytes']} bytes, sha256 {record['sha256'][:16]}...")
        print(f"  source last modified {record['last_modified']}")
        time.sleep(PAUSE_SECONDS)

    archive = CACHE / f"{args.year}FD.zip"
    with zipfile.ZipFile(archive) as zf:
        for member in zf.namelist():
            zf.extract(member, CACHE)
            print(f"  extracted {member}")

    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n"
    )
    print(f"\nrecorded {manifest_path}")
    print("Next: python src/adapters/house-fd/build.py --year", args.year)
    return 0


if __name__ == "__main__":
    sys.exit(main())
