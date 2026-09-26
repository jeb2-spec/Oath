#!/usr/bin/env python3
"""Every rendered page that names an officeholder opens with the frame. INVARIANTS.md §7.

Reads every page under `docs/build/officeholders/`, the index, which lists every seat,
and every page under `docs/build/signals/`, which lists the officeholders a Signal's
Findings are attributed to, and requires the sentence *Presence in the register is not
evidence of wrongdoing* to appear, verbatim after case and punctuation are folded away,
inside the page's first `<header>` element, which is the header region ECOSYSTEM.md
§1.3 puts it in. A page with the frame anywhere else, or nowhere, fails. A page that
lists names is where a reader is likeliest to take presence for proof, so a Signal's
page is held to the rule its Findings' pages are. Standard library.

This gate shares no code with the renderer. The sentence is written here on its
own so that a renderer which drifts from it is caught rather than followed.

    python tools/lint-frame-presence.py
    python tools/lint-frame-presence.py --site docs/build
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

FRAME = "Presence in the register is not evidence of wrongdoing"
HEADER = re.compile(r"<header\b[^>]*>(.*?)</header>", re.S | re.I)
TAGS = re.compile(r"<[^>]+>")


def fold(text: str) -> str:
    """Lowercase, letters and digits only. Punctuation and whitespace do not count."""
    return re.sub(r"[^a-z0-9]", "", text.lower())


def check_page(text: str) -> str | None:
    """None when the page carries the frame in its header; otherwise the reason."""
    match = HEADER.search(text)
    if not match:
        return "no <header> element"
    header_text = fold(TAGS.sub(" ", match.group(1)))
    if fold(FRAME) in header_text:
        return None
    if fold(FRAME) in fold(TAGS.sub(" ", text)):
        return "the frame is on the page but outside the header"
    return "the frame is missing"


# The pages that name an officeholder, by kind, and where each kind lives in the site.
KINDS = (
    ("index", "index.html"),
    ("officeholder", "officeholders/*.html"),
    ("signal", "signals/**/*.html"),
)


def pages(site: Path) -> list[tuple[str, Path]]:
    if not site.is_dir():
        return []
    return [(kind, path) for kind, pattern in KINDS for path in sorted(site.glob(pattern))]


def check(site: Path) -> tuple[list[str], int]:
    found = pages(site)
    failures = []
    for _, path in found:
        reason = check_page(path.read_text(encoding="utf-8"))
        if reason:
            failures.append(f"{path.relative_to(site)}: {reason}")
    return failures, len(found)


def tally(site: Path) -> str:
    """How many pages of each kind were read, in words."""
    counts: dict[str, int] = {}
    for kind, _ in pages(site):
        counts[kind] = counts.get(kind, 0) + 1
    parts = [f"{n} {kind} page{'' if n == 1 else 's'}" for kind, n in counts.items()]
    return ", ".join(parts[:-1]) + (" and " if len(parts) > 1 else "") + parts[-1]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("root", nargs="?", default=".", help="repository root (default: .)")
    parser.add_argument("--site", default="docs/build", help="rendered site (default: docs/build)")
    args = parser.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    site = Path(args.root).resolve() / args.site
    failures, checked = check(site)
    for line in failures:
        print(f"FAIL  {line}")
    if failures:
        print(f"\n{len(failures)} of {checked} pages that name an officeholder lack the frame.")
        return 1
    if checked == 0:
        print(f"OK    0 pages under {args.site}; nothing rendered, so nothing is unframed.")
        print("      Render first: python src/surfaces/render.py")
        return 0
    print(f"OK    {tally(site)} carry the frame in their header.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
