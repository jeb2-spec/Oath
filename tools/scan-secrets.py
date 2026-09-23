#!/usr/bin/env python3
"""No secret, and no piece of one person's life, ever lands in git. INVARIANTS.md §10.

Scans every file git tracks for the common shapes of a secret (private keys, cloud and
platform tokens, credential assignments) and, because this register is public and speaks
about people, for two shapes of a maintainer's own life that have no place in it: a
personal home path, and an e-mail address at a personal mail provider. An organisation's
published contact address is a citation and may stay. A hit fails the run and names the
file and line, with the matched text cut short so the tool does not repeat what it found.

Known false positives live in `.secrets.baseline` at the repository root, one object per
line of the JSON list: {"path": ..., "match": ..., "reason": ...}. A baseline entry allows
exactly that text in exactly that file and nothing else. Standard library only.

    python tools/scan-secrets.py            # the repository this file sits in
    python tools/scan-secrets.py <root>
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

PATTERNS = [
    ("private key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA |PGP )?PRIVATE KEY-----")),
    ("AWS access key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    (
        "GitHub token",
        re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36,}\b|\bgithub_pat_[A-Za-z0-9_]{22,}\b"),
    ),
    ("Slack token", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b")),
    ("API key", re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b|\bAIza[0-9A-Za-z_-]{35}\b")),
    (
        "credential assignment",
        re.compile(
            r"(?i)\b(?:api[_-]?key|secret[_-]?key|access[_-]?token|auth[_-]?token|password|passwd)"
            r"\b\s*[:=]\s*[\"']?[A-Za-z0-9_\-/+=]{16,}[\"']?"
        ),
    ),
    ("personal path", re.compile(r"\b[A-Za-z]:\\Users\\(?!Public\b|Default\b|<)[^\\\s\"'`]+")),
    ("personal path", re.compile(r"(?<![\w/])/(?:Users|home)/(?!Shared\b|<)[^/\s\"'`]+/")),
    ("e-mail address", re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")),
]

# An address at a personal mail provider is a piece of one person's life; an organisation's
# published contact address (a regulator's API desk, a watchdog's tips line) is a citation
# and may stay. The operator's own address is on the project's domain and passes as one.
PERSONAL_EMAIL_DOMAINS = {
    "gmail.com",
    "googlemail.com",
    "yahoo.com",
    "ymail.com",
    "outlook.com",
    "hotmail.com",
    "live.com",
    "msn.com",
    "icloud.com",
    "me.com",
    "mac.com",
    "aol.com",
    "proton.me",
    "protonmail.com",
    "pm.me",
    "fastmail.com",
    "hey.com",
    "comcast.net",
    "att.net",
    "verizon.net",
}

SKIP_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".pdf", ".zip", ".woff", ".woff2", ".ico", ".svg"}


def tracked_files(root: Path) -> list[Path]:
    out = subprocess.run(
        ["git", "ls-files", "-z"], cwd=root, capture_output=True, check=True
    ).stdout
    return [root / p for p in out.decode("utf-8").split("\0") if p]


def load_baseline(root: Path) -> set[tuple[str, str]]:
    path = root / ".secrets.baseline"
    if not path.is_file():
        return set()
    entries = json.loads(path.read_text(encoding="utf-8"))
    return {(e["path"], e["match"]) for e in entries}


def email_allowed(address: str) -> bool:
    return address.lower().rsplit("@", 1)[-1] not in PERSONAL_EMAIL_DOMAINS


def redact(match: str) -> str:
    return match if len(match) <= 8 else match[:4] + "…" + f"({len(match)} chars)"


def scan_text(rel_path: str, text: str, baseline: set[tuple[str, str]]) -> list[str]:
    """Every hit in one file, as 'path:line: kind: redacted match'."""
    hits = []
    for lineno, line in enumerate(text.splitlines(), 1):
        for kind, pattern in PATTERNS:
            for m in pattern.finditer(line):
                found = m.group(0)
                if kind == "e-mail address" and email_allowed(found):
                    continue
                if (rel_path, found) in baseline:
                    continue
                hits.append(f"{rel_path}:{lineno}: {kind}: {redact(found)}")
    return hits


def scan(root: Path) -> tuple[list[str], int]:
    baseline = load_baseline(root)
    problems: list[str] = []
    scanned = 0
    for path in tracked_files(root):
        if path.suffix.lower() in SKIP_SUFFIXES or path.name == ".secrets.baseline":
            continue
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, FileNotFoundError):
            continue
        scanned += 1
        problems += scan_text(path.relative_to(root).as_posix(), text, baseline)
    return problems, scanned


def main(argv: list[str] | None = None) -> int:
    root = Path(argv[0] if argv else ".").resolve()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    problems, scanned = scan(root)
    if problems:
        for p in problems:
            print(f"FAIL  {p}")
        print(f"\n{len(problems)} hits across {scanned} tracked text files. Nothing landed.")
        return 1
    print(
        f"OK    {scanned} tracked text files scanned; no secret, key, token, personal path or "
        "personal e-mail address."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
