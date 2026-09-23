#!/usr/bin/env python3
"""Capture the documents behind the filing index. NEXT.md Phase 3 I.1b, first half.

PIPELINE.md Stage 1 for the document layer: retrieve each filing's document from the
Clerk, keep the exact bytes and the response headers, record the SHA-256 and the
retrieval time, and write nothing else. Extraction happens in `build.py`, from these
captures, so a build is reproducible by anyone holding the same bytes.

Which documents: every filing in `data/filings.ndjson` whose code is in `--codes`
(default P, the transaction reports, which the Clerk serves from its own ptr-pdfs
path). `--seats NC` limits a run to one delegation, which is how the extractor was
piloted. Documents already on disk are adopted, not fetched again: their retrieval
time comes from the Date header the Clerk sent with them.

Politeness: one request at a time, a pause between requests, a user agent that names
the project and how to reach whoever runs it.

    python src/adapters/house-fd/documents.py --year 2025
    python src/adapters/house-fd/documents.py --year 2025 --seats NC
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
import urllib.request
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from pathlib import Path

DOCS = Path("data/cache/house-fd/docs")
MANIFEST = DOCS / "captures.json"
AGENT = (
    "Oath-register/0.1 (public-record research; +https://github.com/jeb2-spec/Oath; "
    "operator@veraproject.xyz)"
)
PAUSE_SECONDS = 2


def read_ndjson(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def header_value(headers_path: Path, name: str) -> str | None:
    if not headers_path.is_file():
        return None
    for line in headers_path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.lower().startswith(name.lower() + ":"):
            return line.split(":", 1)[1].strip()
    return None


def utc(dt: datetime) -> str:
    return dt.astimezone(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def record(doc_id: str, url: str) -> dict:
    """What is recorded about one captured document, from the bytes and headers on disk."""
    pdf = DOCS / f"{doc_id}.pdf"
    body = pdf.read_bytes()
    date = header_value(DOCS / f"{doc_id}.headers", "Date")
    retrieved = utc(parsedate_to_datetime(date)) if date else utc(datetime.now(UTC))
    return {
        "url": url,
        "retrieved_at": retrieved,
        "sha256": hashlib.sha256(body).hexdigest(),
        "bytes": len(body),
        "content_type": header_value(DOCS / f"{doc_id}.headers", "Content-Type"),
        "last_modified": header_value(DOCS / f"{doc_id}.headers", "Last-Modified"),
    }


def fetch(doc_id: str, url: str) -> None:
    request = urllib.request.Request(url, headers={"User-Agent": AGENT})
    with urllib.request.urlopen(request, timeout=120) as response:  # noqa: S310 (https, fixed host)
        body = response.read()
        lines = [f"HTTP/1.1 {response.status} {response.reason}"]
        lines += [f"{k}: {v}" for k, v in response.headers.items()]
    (DOCS / f"{doc_id}.pdf").write_bytes(body)
    (DOCS / f"{doc_id}.headers").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--year", type=int, required=True, help="filing year, e.g. 2025")
    parser.add_argument("--codes", default="P", help="comma-separated Clerk codes (default P)")
    parser.add_argument("--seats", default="", help="comma-separated state codes, e.g. NC,VA")
    args = parser.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    codes = {c.strip() for c in args.codes.split(",") if c.strip()}
    states = {s.strip().upper() for s in args.seats.split(",") if s.strip()}
    holders = {h["id"]: h for h in read_ndjson(Path("data/officeholders.ndjson"))}
    wanted = []
    for f in read_ndjson(Path("data/filings.ndjson")):
        if f.get("source_form_code") not in codes:
            continue
        seat = holders[f["officeholder_id"]]["offices"][0]["seat"]
        if states and seat[:2] not in states:
            continue
        wanted.append((f["id"].rsplit(":", 1)[1], f["source"]["url"]))

    DOCS.mkdir(parents=True, exist_ok=True)
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8")) if MANIFEST.is_file() else {}
    fetched = adopted = 0
    for doc_id, url in wanted:
        pdf = DOCS / f"{doc_id}.pdf"
        if not pdf.is_file() or pdf.stat().st_size == 0:
            fetch(doc_id, url)
            fetched += 1
            time.sleep(PAUSE_SECONDS)
        elif doc_id not in manifest:
            adopted += 1
        manifest[doc_id] = record(doc_id, url)
    MANIFEST.write_text(
        json.dumps(manifest, indent=1, sort_keys=True) + "\n", encoding="utf-8", newline="\n"
    )
    print(
        f"{len(wanted)} documents wanted for codes {sorted(codes)}"
        + (f" in {sorted(states)}" if states else "")
        + f"; fetched {fetched}, adopted {adopted} already on disk; manifest holds {len(manifest)}"
    )
    print(f"recorded {MANIFEST}")
    print("Next: python src/adapters/house-fd/build.py --year", args.year)
    return 0


if __name__ == "__main__":
    sys.exit(main())
