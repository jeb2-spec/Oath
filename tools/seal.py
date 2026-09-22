#!/usr/bin/env python3
"""Seal a build: write the register's digest and row counts into data/meta.json.

This is the build's last step before anchoring. It records the build id and the
build time it is given (never the clock, so two runs from the same inputs produce
the same bytes), counts the rows in every NDJSON file, and writes the digest that
tools/verify.py recomputes. It shares the manifest rule with the verifier by
importing it; tools/tamper-test.py recomputes the same rule with code that shares
nothing, which is what makes the check non-circular.

    python3 tools/seal.py --build 0001 --built-at 2026-09-22T00:00:00Z
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path


def load_verify(tools_dir: Path):
    spec = importlib.util.spec_from_file_location("verify", tools_dir / "verify.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def seal(root: Path, build: str, built_at: str) -> str:
    verify = load_verify(Path(__file__).resolve().parent)
    meta_path = root / verify.META
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    meta["build"] = build
    meta["built_at"] = built_at
    meta["rows"] = verify.row_counts(root)
    meta["digest"] = ""
    meta_path.write_text(
        json.dumps(meta, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    meta["digest"] = verify.compute_digest(root)
    meta_path.write_text(
        json.dumps(meta, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return meta["digest"]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Seal a build: write its digest into data/meta.json."
    )
    parser.add_argument("--build", required=True, help="build identifier, e.g. 0001")
    parser.add_argument("--built-at", required=True, help="ISO 8601 UTC, e.g. 2026-09-22T00:00:00Z")
    parser.add_argument("root", nargs="?", default=".", help="repository root (default: .)")
    args = parser.parse_args(argv)
    digest = seal(Path(args.root).resolve(), args.build, args.built_at)
    print(f"sealed build {args.build} at {args.built_at}\n  digest    {digest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
