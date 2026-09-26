#!/usr/bin/env python3
"""Facts stay. Change is shown by supersession, not by removal. INVARIANTS.md §14; CHARTER Vow V.

Compares the register's rows in the tree with the published ones, the same paths on
`origin/main` (or the ref in OATH_PUBLISHED_REF; on a push to main CI sets it to main as it
stood before the push), and fails when:

  1. a published row is gone from the tree: an office, an officeholder, a filing, a
     holding, a transaction, or a change row;
  2. anything a published row carries changed in place. A row only gains: a null may be
     filled, a list may grow at its end, an object may gain keys; nothing it carries moves,
     the time it was read and the hash of the bytes it was read from included. The one
     exception is the maintainer's correction: a row of data/changes.ndjson whose change
     is "corrected" names the row, the fact, the value it carried and the value it now
     carries, and cites the evidence (tools/correct.py writes it); that move, and no other,
     passes;
  3. data/changes.ndjson is not the published file with rows added at its end, byte for
     byte: a change row records what a capture showed, and never changes;
  4. a capture the register keeps is gone or altered. Every file under data/captures/sha256/ is
     named by the SHA-256 of its bytes and never changes, and every change row's capture is
     kept there, so a change can be checked from the repository alone; except a filed
     document (a PDF), which is cited by its SHA-256 and never kept, because it can carry the
     names of private people and a kept copy would outlast the Clerk's withdrawal or redaction
     of it (EVIDENCE.md §7; the Council's third reading of S.1b, Seat B). A kept PDF fails;
  5. a correction does not say what makes it one: its kind (the source, or the register),
     its reason, who decided and when, and evidence at an https URL on a host SOURCES.md
     registers as primary. Such a row is honoured for nothing, and fails by itself, however
     it was written (the Council's second reading of S.1b, Seat C). A correction of a
     transaction's asset or notes names what the fact carried by its SHA-256 (`was_sha256`),
     so the filer's text is not kept in the changes, and the gate matches it by that hash.

Findings and Signal definitions have their own gates (check-supersessions,
check-signal-versions). It fails rather than passes when it cannot read the published ref.
Standard library.

A published row stays even when a later capture no longer lists it, or states one of its
facts otherwise: the adapter carries it as published and records what the capture showed as
a change row of its own (src/adapters/house-fd/build.py). So a Member who leaves office, a
filing the Clerk's index stops listing, a filing the index dates otherwise, and a filing
year whose Congress has ended all keep their rows, and this gate is what holds the adapter
to that.

    python tools/check-removals.py

Example of a failing input: an officeholder the roster no longer lists, dropped from
data/officeholders.ndjson instead of carried, or a published filing's officeholder_id moved
to another person with no correction row naming the move.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlsplit

FILES = (
    "data/offices.ndjson",
    "data/officeholders.ndjson",
    "data/filings.ndjson",
    "data/holdings.ndjson",
    "data/transactions.ndjson",
    "data/changes.ndjson",
)
APPENDED = "data/changes.ndjson"
CAPTURES = "data/captures/sha256"
KEPT = re.compile(r"^([0-9a-f]{64})(\.[A-Za-z0-9]+)?$")
MISSING = object()


def git(root: Path, *args: str, text: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-C", str(root), *args],
        capture_output=True,
        text=text,
        **({"encoding": "utf-8"} if text else {}),
    )


def readable(root: Path, ref: str) -> bool:
    return git(root, "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}").returncode == 0


def published_text(root: Path, ref: str, rel: str) -> str:
    """The file's text as published at `ref`; empty when the ref has no such file."""
    shown = git(root, "show", f"{ref}:{rel}")
    return shown.stdout if shown.returncode == 0 else ""


def rows_of(text: str) -> list[dict]:
    return [json.loads(line) for line in text.splitlines() if line.strip()]


def read(path: Path) -> str:
    return path.read_text("utf-8") if path.is_file() else ""


def shown(value) -> str:
    if value is MISSING:
        return "gone"
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def canon(value) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def compare(old, new, path: tuple = ()):
    """Yield (path, old, new) for every way `new` fails to keep what `old` carried."""
    if old is None:
        return
    if isinstance(old, dict):
        if not isinstance(new, dict):
            yield path, old, new
            return
        for key, value in old.items():
            if key not in new:
                yield (*path, key), value, MISSING
            else:
                yield from compare(value, new[key], (*path, key))
        return
    if isinstance(old, list):
        if not isinstance(new, list) or len(new) < len(old):
            yield path, old, new
            return
        for index, value in enumerate(old):
            yield from compare(value, new[index], (*path, index))
        return
    if old != new:
        yield path, old, new


def primary_hosts(root: Path) -> set[str]:
    """The hosts SOURCES.md registers as primary, read the way the §5 gate reads them; none
    when the registry or its reader is missing, so no correction is honoured on trust."""
    tool, sources = root / "tools" / "check-aggregator-sole.py", root / "SOURCES.md"
    if not tool.is_file() or not sources.is_file():
        return set()
    spec = importlib.util.spec_from_file_location("aggregator_sole", tool)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module.registry(sources.read_text("utf-8"))[0]


def lacking(change: dict, primary: set[str]) -> list[str]:
    """What a correction lacks for the gate to honour it."""
    missing = []
    if change.get("kind") not in ("source", "register"):
        missing.append("a kind (source or register)")
    for key, words in (("because", "a reason"), ("decided_by", "who decided")):
        if not str(change.get(key) or "").strip():
            missing.append(f"{words} ({key})")
    if not change.get("decided_at"):
        missing.append("when it was decided (decided_at)")
    url = (change.get("capture") or {}).get("url", "")
    if urlsplit(url).scheme != "https" or (urlsplit(url).hostname or "").lower() not in primary:
        missing.append("evidence at an https URL on a host SOURCES.md registers as primary")
    if "field" not in change:
        missing.append("the fact it is about (field)")
    return missing


def was_key(value) -> str:
    """How a correction names what a fact carried: its canonical JSON."""
    return canon(value)


def hashed_key(value) -> str:
    """How a correction of the filer's own text names what it carried: the SHA-256 of its
    canonical JSON (tools/correct.py, `was_sha256`)."""
    return "sha256:" + hashlib.sha256(canon(value).encode("utf-8")).hexdigest()


def corrections(
    changes: list[dict], primary: set[str] | None = None
) -> tuple[set[tuple[str, str, str, str]], list[str]]:
    """Each move a whole correction names, (row, fact, what it was, what it is), and a failure
    for each correction that lacks what makes it one. What it was is `was_key` of the value,
    or `hashed_key`'s form where the correction keeps only its SHA-256. `primary` is None only
    where the caller has already checked the corrections it passes."""
    moves, fails = set(), []
    for c in changes:
        if c.get("change") != "corrected":
            continue
        missing = [] if primary is None else lacking(c, primary)
        if missing:
            fails.append(
                f"{APPENDED}: {c.get('id', '?')} is a correction without {', '.join(missing)}; "
                "the gate honours it for nothing"
            )
            continue
        was = f"sha256:{c['was_sha256']}" if "was_sha256" in c else was_key(c.get("was"))
        moves.add((c["row_id"], c["field"], was, canon(c.get("now"))))
    return moves, fails


def problems(rel: str, tree: list[dict], before: list[dict], corrected=frozenset()) -> list[str]:
    """Every way one file's rows in the tree fail to keep the published ones."""
    fails = []
    here = {row["id"]: row for row in tree}
    for old in before:
        new = here.get(old["id"])
        if new is None:
            fails.append(f"{rel}: {old['id']} is published, and gone from the tree")
            continue
        for path, was, now in compare(old, new):
            where = ".".join(str(p) for p in path) or "(the row)"
            if now is not MISSING and (
                (old["id"], where, was_key(was), canon(now)) in corrected
                or (old["id"], where, hashed_key(was), canon(now)) in corrected
            ):
                continue
            fails.append(f"{rel}: {old['id']} {where}: {shown(was)} -> {shown(now)}")
    return fails


def appended(tree: str, published: str) -> list[str]:
    """The changes file must be the published one with rows added at its end."""
    if tree.startswith(published):
        return []
    at = next(
        (
            n
            for n, (a, b) in enumerate(zip(tree.splitlines(), published.splitlines(), strict=False))
            if a != b
        ),
        min(len(tree.splitlines()), len(published.splitlines())),
    )
    return [
        f"{APPENDED}: the published rows are not kept byte for byte at its start (line {at + 1}); "
        "a change row never changes, and new ones are added at the end"
    ]


def document(url: str) -> bool:
    """Whether a capture's URL is a filed document (a PDF), cited and never kept."""
    return urlsplit(url).path.lower().endswith(".pdf")


def capture_problems(root: Path, ref: str, changes: list[dict]) -> list[str]:
    """Kept captures stay, byte for byte, each named by its hash, and every change cites one."""
    fails = []
    folder = root / CAPTURES
    here = {p.name: p for p in folder.iterdir() if p.is_file()} if folder.is_dir() else {}
    listed = git(root, "ls-tree", "-r", "--name-only", ref, "--", CAPTURES).stdout.split()
    for rel in listed:
        name = rel.rsplit("/", 1)[-1]
        body = git(root, "show", f"{ref}:{rel}", text=False).stdout
        if name not in here:
            fails.append(f"{rel}: a kept capture is published, and gone from the tree")
        elif here[name].read_bytes() != body:
            fails.append(f"{rel}: a kept capture changed; its bytes never change")
    for name, path in sorted(here.items()):
        named = KEPT.match(name)
        if named is None or hashlib.sha256(path.read_bytes()).hexdigest() != named.group(1):
            fails.append(f"{CAPTURES}/{name}: not named by the SHA-256 of its bytes")
        if name.lower().endswith(".pdf"):
            fails.append(
                f"{CAPTURES}/{name}: a filed document is kept; the register cites a document by "
                "its SHA-256 and never keeps it (EVIDENCE.md §7)"
            )
    hashes = {KEPT.match(n).group(1) for n in here if KEPT.match(n)}
    for change in changes:
        if document(change["capture"]["url"]):
            continue
        if change["capture"]["content_hash"] not in hashes:
            fails.append(
                f"{APPENDED}: {change['id']} cites a capture the register does not keep "
                f"({change['capture']['content_hash'][:12]}) under {CAPTURES}/"
            )
    return fails


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("root", nargs="?", default=".", help="repository root (default: .)")
    args = parser.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    root = Path(args.root).resolve()
    ref = os.environ.get("OATH_PUBLISHED_REF", "origin/main")
    if not readable(root, ref):
        print(
            f"FAIL  cannot read the published rows at {ref}; fetch it "
            "(git fetch origin main) and run again. Nothing was checked."
        )
        return 1
    changes = rows_of(read(root / APPENDED))
    needs = any(c.get("change") == "corrected" for c in changes)
    corrected, fails = corrections(changes, primary_hosts(root) if needs else set())
    rows, held = 0, 0
    for rel in FILES:
        before_text = published_text(root, ref, rel)
        tree_text = read(root / rel)
        before, tree = rows_of(before_text), rows_of(tree_text)
        rows += len(tree)
        held += len(before)
        fails += problems(rel, tree, before, corrected)
        if rel == APPENDED:
            fails += appended(tree_text, before_text)
    fails += capture_problems(root, ref, changes)
    if fails:
        print(
            f"FAIL  {len(fails)} against {ref}: a published fact removed or changed, a kept "
            "capture gone, or a change row that cannot stand:"
        )
        for line in fails:
            print(f"      {line}")
        print(
            "      A published row stays, byte for byte, and only gains facts it lacked "
            "(INVARIANTS.md §14). What a later capture shows otherwise is a change row of its "
            "own, citing the capture, which the register keeps; a fact found wrong moves only "
            "by the maintainer's correction row that names it (tools/correct.py), with the "
            "evidence."
        )
        return 1
    rows_moved = [c for c in changes if c.get("change") == "corrected"]
    decisions = len({(c["decided_at"], c["decided_by"], c["because"]) for c in rows_moved})
    print(
        f"OK    {rows:,} rows in the register; {held:,} published at {ref}, every one present "
        "and carrying every fact it was published with, or gaining only facts it lacked"
        + (
            f"; {decisions:,} recorded {'decision' if decisions == 1 else 'decisions'} "
            f"({len(rows_moved):,} change {'row' if len(rows_moved) == 1 else 'rows'}), each "
            "saying its kind, its reason, who decided and when, and citing evidence at an https "
            "URL on a host SOURCES.md registers as primary."
            if rows_moved
            else "."
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
