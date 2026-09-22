#!/usr/bin/env python3
"""Verify the Oath register: recompute its seal and compare it to the recorded digest.

The seal is one SHA-256 over a manifest of the sealed files. The manifest is built
like this, so that a stranger can rebuild it with sha256sum and sort:

  1. Take every file under data/ whose name ends in .ndjson; the eleven doctrine
     documents named in DOCTRINE below; and data/meta.json with its "digest" key
     removed and re-serialised as canonical JSON (keys sorted, separators "," and
     ":", UTF-8, non-ASCII kept, one trailing newline).
  2. For each file, one line: the SHA-256 of its bytes in lowercase hex, two
     spaces, the path relative to the repository root with forward slashes, and a
     newline.
  3. Sort the lines by their bytes. The digest is the SHA-256 of the sorted lines.

It prints OK when the recomputed digest matches data/meta.json, FAIL otherwise, and
"Integrity is not accuracy." on every run, because a seal proves the record is
unchanged since the build and nothing else. Gate for INVARIANTS.md §9 (the seal
covers the disclosures) and RUBRIC.md gate 4. Standard-library Python 3.11+, and
short enough to read in one sitting on purpose.

Example of a failing input: change one character of a disclosure in data/meta.json.

    python3 tools/verify.py            # verify the repository you are standing in
    python3 tools/verify.py <root>     # verify another checkout or a build bundle
    python3 tools/verify.py --manifest # print the manifest instead, for comparison
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

DOCTRINE = [
    "CHARTER.md",
    "RUBRIC.md",
    "INVARIANTS.md",
    "BYLAWS.md",
    "COUNCIL.md",
    "METHODOLOGY.md",
    "STANDARDS.md",
    "SOURCES.md",
    "LIMITATIONS.md",
    "SPEC.md",
    "ECOSYSTEM.md",
]
META = "data/meta.json"
SENTENCE = "Integrity is not accuracy."


def canonical_meta(meta: dict) -> bytes:
    """data/meta.json as sealed: without its digest, as canonical JSON."""
    body = {k: v for k, v in meta.items() if k != "digest"}
    return (
        json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n"
    ).encode("utf-8")


def sealed_files(root: Path) -> list[tuple[str, bytes]]:
    """Every sealed file as (relative path, bytes), in manifest order."""
    items: list[tuple[str, bytes]] = []
    for path in sorted(root.glob("data/**/*.ndjson")):
        items.append((path.relative_to(root).as_posix(), path.read_bytes()))
    for name in DOCTRINE:
        path = root / name
        if not path.is_file():
            raise FileNotFoundError(f"{name} is sealed and is missing")
        items.append((name, path.read_bytes()))
    meta_path = root / META
    if not meta_path.is_file():
        raise FileNotFoundError(f"{META} is missing")
    items.append((META, canonical_meta(json.loads(meta_path.read_text(encoding="utf-8")))))
    return items


def manifest(root: Path) -> bytes:
    lines = [
        f"{hashlib.sha256(data).hexdigest()}  {rel}\n".encode() for rel, data in sealed_files(root)
    ]
    return b"".join(sorted(lines))


def compute_digest(root: Path) -> str:
    return hashlib.sha256(manifest(root)).hexdigest()


def row_counts(root: Path) -> dict[str, int]:
    """Non-empty lines per NDJSON file, keyed by relative path."""
    counts: dict[str, int] = {}
    for path in sorted(root.glob("data/**/*.ndjson")):
        with path.open("rb") as fh:
            counts[path.relative_to(root).as_posix()] = sum(1 for line in fh if line.strip())
    return counts


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Recompute the register's seal and compare it to data/meta.json.",
        epilog=(
            "Gate: INVARIANTS.md §9, the seal covers the disclosures; RUBRIC.md gate 4. "
            "Catches: any change to a sealed NDJSON row, a doctrine document, or "
            "data/meta.json (its disclosures included) after the build was sealed. "
            "Example failing input: one character changed in a disclosure in data/meta.json."
        ),
    )
    parser.add_argument("root", nargs="?", default=".", help="repository root (default: .)")
    parser.add_argument("--manifest", action="store_true", help="print the manifest and exit")
    args = parser.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    root = Path(args.root).resolve()

    try:
        if args.manifest:
            sys.stdout.write(manifest(root).decode("utf-8"))
            return 0
        meta = json.loads((root / META).read_text(encoding="utf-8"))
        stored = str(meta.get("digest", ""))
        computed = compute_digest(root)
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        print(f"\nFAIL  cannot verify: {exc}\n      {SENTENCE}")
        return 1

    print(f"\n  stored    {stored or '(none recorded)'}")
    print(f"  computed  {computed}\n")
    if stored != computed:
        print("FAIL  contents do not match the recorded digest.")
        print("      Something changed after this build was sealed.")
        print(f"      {SENTENCE}")
        return 1

    counts = row_counts(root)
    total = sum(counts.values())
    print("OK    contents match the recorded digest.")
    print(
        f"      {total} rows across {len(counts)} NDJSON files; "
        f"{len(DOCTRINE)} doctrine documents; {META}."
    )
    if total == 0:
        print("      The register is empty by design at this build.")
    print("\n      This proves the contents are unchanged since the build.")
    print("      It does not prove any statement in them is true.")
    print(f"      {SENTENCE}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
