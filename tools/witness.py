#!/usr/bin/env python3
"""Whether an outside archive holds the bytes of each document a published Finding rests on.

The register keeps no filed document (the Council's third reading of S.1b, Seat B: a kept copy
would outlast the Clerk's withdrawal or redaction of a private person's name, and the §14 gate
would then refuse its removal). It keeps each document's SHA-256 instead, sealed with the build.
A hash proves which bytes were read only while someone still holds bytes to hash. If the Clerk
later serves the document in other bytes, or stops serving it, a reader holding the hash has
nothing left to check it against.

The Internet Archive crawls the Clerk's site on its own account. This asks it, for every
document a published Finding rests on, which captures of that document's address it holds;
fetches one capture of each distinct payload, byte for byte (the `id_` form, without the
Archive's own page around it); and hashes what arrived. A document is **held** only when a
capture's bytes hash to the sealed hash. Anything else is said as what it is: **differs**
(captures exist and none of them is the bytes the register read), **none** (no capture is
listed), **unchecked** (the Archive could not be asked).

It observes and never submits. Asking the Archive to capture a document would make a copy
because of the register, and whether the register should do that is the Council's question
(docs/design/an-outside-witness.md), not this tool's.

A copy whose bytes match shows that someone other than the register holds what the register
read, and since when. It says nothing about whether the document is accurate. Integrity is not
accuracy.

It prints counts and document ids, never a name. It exits 1 when a document could not be
checked or an outside copy differs, because either is for a person to read before anything is
said about it.

    python tools/witness.py                                   # the published Findings
    python tools/witness.py --report witness.json --summary summary.md
"""

from __future__ import annotations

import argparse
import base64
import gzip
import hashlib
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

TOOL = "tools/witness.py@1"
ARCHIVE = "https://web.archive.org"
AGENT = (
    "Oath-register/0.1 (public-record research; +https://github.com/jeb2-spec/Oath; "
    "operator@veraproject.xyz)"
)
PAUSE_SECONDS = 3
PAYLOADS_PER_DOCUMENT = 5
FRAME = (
    "A copy whose bytes hash to the sealed hash shows that the Internet Archive holds the bytes "
    "the register read, and since when. It says nothing about whether the document is accurate."
)

Get = Callable[[str], tuple[bytes, dict]]


def get(url: str) -> tuple[bytes, dict]:
    """Fetch one address at the Archive, retrying once after a refusal or a dropped connection."""
    if not url.startswith(ARCHIVE + "/"):
        raise ValueError(f"this tool asks only the Internet Archive, not {url}")
    for attempt in (1, 2):
        request = urllib.request.Request(url, headers={"User-Agent": AGENT})
        try:
            with urllib.request.urlopen(request, timeout=120) as response:  # noqa: S310
                body = response.read()
                headers = {k.lower(): v for k, v in response.headers.items()}
            break
        except (urllib.error.URLError, TimeoutError, ConnectionError) as error:
            if attempt == 2:
                raise
            code = getattr(error, "code", None)
            time.sleep(60 if code == 429 else 10)
    if headers.get("content-encoding", "").lower() == "gzip":
        body = gzip.decompress(body)
    time.sleep(PAUSE_SECONDS)
    return body, headers


def captures(document_url: str, fetch: Get) -> list[dict]:
    """The Archive's index of successful captures of one address, oldest first."""
    query = urllib.parse.urlencode(
        {
            "url": document_url,
            "output": "json",
            "fl": "timestamp,original,statuscode,digest",
            "filter": "statuscode:200",
        }
    )
    body, _ = fetch(f"{ARCHIVE}/cdx/search/cdx?{query}")
    text = body.decode("utf-8").strip()
    if not text:
        return []
    rows = json.loads(text)
    if not rows:
        return []
    header, *entries = rows
    listed = [dict(zip(header, entry, strict=True)) for entry in entries]
    return sorted(listed, key=lambda row: row["timestamp"])


def when(timestamp: str) -> str:
    """The Archive's fourteen-digit capture time as ISO 8601 UTC."""
    moment = datetime.strptime(timestamp, "%Y%m%d%H%M%S").replace(tzinfo=UTC)
    return moment.isoformat().replace("+00:00", "Z")


def archive_digest(body: bytes) -> str:
    """The digest the Archive's index gives a payload: base 32 of its SHA-1."""
    return base64.b32encode(hashlib.sha1(body).digest()).decode("ascii")  # noqa: S324


def witness(document: dict, fetch: Get) -> dict:
    """What the Archive holds of one document, measured against its sealed hash."""
    row = {
        "filing_id": document["filing_id"],
        "url": document["url"],
        "content_hash": document["content_hash"],
    }
    try:
        listed = captures(document["url"], fetch)
    except Exception as error:  # noqa: BLE001 (any failure to ask is reported, never guessed past)
        return {**row, "outcome": "unchecked", "error": f"{type(error).__name__}: {error}"}
    row["captures"] = len(listed)
    if not listed:
        return {**row, "outcome": "none"}
    earliest: dict[str, dict] = {}
    for entry in listed:
        earliest.setdefault(entry["digest"], entry)
    read = []
    for entry in list(earliest.values())[:PAYLOADS_PER_DOCUMENT]:
        raw = f"{ARCHIVE}/web/{entry['timestamp']}id_/{entry['original']}"
        try:
            body, _ = fetch(raw)
        except Exception as error:  # noqa: BLE001
            read.append({"captured_at": when(entry["timestamp"]), "error": type(error).__name__})
            continue
        sha256 = hashlib.sha256(body).hexdigest()
        read.append(
            {
                "captured_at": when(entry["timestamp"]),
                "sha256": sha256,
                "matches": sha256 == document["content_hash"],
                "archive_digest_agrees": archive_digest(body) == entry["digest"],
                "replay": f"{ARCHIVE}/web/{entry['timestamp']}/{entry['original']}",
            }
        )
    row["payloads"] = len(earliest)
    row["read"] = read
    held = [capture for capture in read if capture.get("matches")]
    if held:
        first = held[0]
        return {
            **row,
            "outcome": "held",
            "held_since": first["captured_at"],
            "replay": first["replay"],
        }
    if all("error" in capture for capture in read):
        return {**row, "outcome": "unchecked", "error": "no capture could be read"}
    return {**row, "outcome": "differs"}


def documents(root: Path) -> list[dict]:
    """Every document a published Finding rests on, once each, in filing-id order."""
    filings: dict[str, dict] = {}
    for line in (root / "data" / "filings.ndjson").read_text("utf-8").splitlines():
        if line.strip():
            row = json.loads(line)
            filings[row["id"]] = row
    wanted: set[str] = set()
    for line in (root / "data" / "findings.ndjson").read_text("utf-8").splitlines():
        if line.strip():
            wanted.update(json.loads(line)["producing_filings"])
    out = []
    for filing_id in sorted(wanted):
        source = filings[filing_id]["source"]
        out.append(
            {"filing_id": filing_id, "url": source["url"], "content_hash": source["content_hash"]}
        )
    return out


def summary(report: dict) -> str:
    """The report as Markdown, for a job summary: counts, then one line per document."""
    totals = report["totals"]
    lines = [
        "## An outside witness for the documents the Findings rest on",
        "",
        f"Checked {report['checked_at']} by `{report['tool']}`, at {report['build']}.",
        "",
        "| Outcome | Documents |",
        "| --- | --- |",
    ]
    lines += [f"| {outcome} | {n} |" for outcome, n in totals.items()]
    lines += ["", report["frame"], "", "| Document | Outcome | Held since | Captures |"]
    lines += ["| --- | --- | --- | --- |"]
    for row in report["documents"]:
        name = row["url"].rsplit("/", 1)[1]
        since = row.get("held_since", "")
        lines.append(f"| {name} | {row['outcome']} | {since} | {row.get('captures', '')} |")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None, fetch: Get = get) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--root", default=str(Path(__file__).resolve().parent.parent))
    parser.add_argument("--report", help="write the whole report here as JSON")
    parser.add_argument("--summary", help="append the report as Markdown here")
    args = parser.parse_args(argv)
    root = Path(args.root)
    meta = json.loads((root / "data" / "meta.json").read_text("utf-8"))
    rows = [witness(document, fetch) for document in documents(root)]
    totals = {outcome: 0 for outcome in ("held", "differs", "none", "unchecked")}
    for row in rows:
        totals[row["outcome"]] += 1
    report = {
        "tool": TOOL,
        "checked_at": datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "build": f"build {meta.get('build')}, digest {str(meta.get('digest'))[:12]}",
        "archive": ARCHIVE,
        "frame": FRAME,
        "totals": totals,
        "documents": rows,
    }
    if args.report:
        Path(args.report).write_text(json.dumps(report, indent=1) + "\n", "utf-8")
    if args.summary:
        with open(args.summary, "a", encoding="utf-8") as out:
            out.write(summary(report))
    print(f"{len(rows):,} documents a published Finding rests on")
    for outcome, n in totals.items():
        print(f"  {n:5,}  {outcome}")
    for row in rows:
        if row["outcome"] in ("differs", "unchecked"):
            name = row["url"].rsplit("/", 1)[1]
            print(f"  {row['outcome']:9}  {name}  {row.get('error', '')}".rstrip())
    print(FRAME)
    if totals["differs"] or totals["unchecked"]:
        print("FAIL  a document could not be checked, or an outside copy is other bytes")
        return 1
    print("OK    every document was checked; each is held or has no outside copy listed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
