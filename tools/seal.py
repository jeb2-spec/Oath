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
import re
import sys
from pathlib import Path


def load_verify(tools_dir: Path):
    spec = importlib.util.spec_from_file_location("verify", tools_dir / "verify.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


COUNTED = (
    ("data/officeholders.ndjson", "officeholders"),
    ("data/filings.ndjson", "filings"),
    ("data/transactions.ndjson", "transactions"),
)


def run_figures(run: dict) -> list[tuple[int, str]]:
    """The run record's figures the state text is expected to carry: the ones that move
    between builds while the roster stands still."""
    counts = run.get("counts", {})
    documents = run.get("documents", {})
    figures = [
        (counts.get("quiet"), "quiet members"),
        (counts.get("rejected"), "rows not attributed"),
        (counts.get("attributed_by_document"), "rows attributed by the document"),
        (documents.get("read"), "documents read"),
        (run.get("rejected_by_reason", {}).get("surname matches a sitting member"), "rows held"),
    ]
    return [(int(n), label) for n, label in figures if n]


def state_text_lacks(meta: dict, run: dict | None = None) -> str:
    """Which of the build's own figures the hand-written state text fails to carry.

    The state text is the one sentence a reader gets about the whole build, and it is
    sealed. A build whose figures changed and whose sentence did not is a count in prose
    the table contradicts. Checked: the row counts of the counted files, and, when the
    run record is given, the figures in it that move between builds. Each must appear as
    a whole number with thousands separators, not inside a larger number. Returns an
    empty string when every figure is present.
    """
    state = meta.get("state", "")
    wanted = [(meta.get("rows", {}).get(path), label) for path, label in COUNTED]
    wanted += run_figures(run or {})
    missing = []
    for count, label in wanted:
        if not count:
            continue
        pattern = r"(?<![\d,])" + re.escape(f"{count:,}") + r"(?![\d,])"
        if not re.search(pattern, state):
            missing.append(f"{label} {count:,}")
    return ", ".join(missing)


def current_runs(root: Path) -> list[dict]:
    """The run records in the tree, each paired with its set-aside file by year and key.

    A record `house-fd-<year>-<key>` must have `data/rejected/house-fd/<year>-<key>.ndjson`
    beside it; a record without one is the leftover of a build the tree no longer holds,
    and a tree that carries one is refused, because a page once read such a record.
    """
    runs = sorted((root / "data" / "adapter-runs").glob("*.ndjson"))
    out = []
    for path in runs:
        name = path.stem.split("-", 2)[-1] if path.stem.count("-") >= 2 else path.stem
        adapter = path.stem[: -len(name) - 1] if name != path.stem else ""
        set_aside = root / "data" / "rejected" / adapter / f"{name}.ndjson"
        if not set_aside.is_file():
            raise SystemExit(
                f"refusing to seal: {path.as_posix()} has no set-aside file "
                f"{set_aside.as_posix()}; "
                "the tree carries one run record per adapter and year, each with its set-aside file"
            )
        lines = [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        if lines:
            out.append(json.loads(lines[-1]))
    return out


def seal(root: Path, build: str, built_at: str) -> str:
    verify = load_verify(Path(__file__).resolve().parent)
    meta_path = root / verify.META
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    meta["build"] = build
    meta["built_at"] = built_at
    meta["rows"] = verify.row_counts(root)
    runs = current_runs(root)
    stale = (
        state_text_lacks(meta)
        if not runs
        else ", ".join(s for s in (state_text_lacks(meta, run) for run in runs) if s)
    )
    if stale:
        raise SystemExit(
            "refusing to seal: the state text in data/meta.json does not carry the build's "
            f"own counts ({stale}); rewrite it for this build first"
        )
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
