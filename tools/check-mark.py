#!/usr/bin/env python3
"""Strike the mark against many digests and require the geometry to stay legible.

ECOSYSTEM.md §2.4: a gate strikes and verifies. For a spread of synthetic digests,
every officeholder in the register at the real digest, and the build mark, this
checks that:

  - the SVG parses and every coordinate lies inside the viewBox (nothing clipped);
  - the ring is present and its outer edge sits inside the canvas;
  - every tick and bar requested is present, and bars never exceed ticks;
  - the wax rim never crosses the ring, so the two read as seal and ring;
  - striking twice gives identical bytes, and the bytes stay under a budget, so
    four hundred pages carrying their own seal stay light.

Standard library. Exit 1 on any failure.

    python tools/check-mark.py
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

BUDGET_BYTES = 20_000
NUM = re.compile(r"-?\d+(?:\.\d+)?")


def load_striker(root: Path):
    spec = importlib.util.spec_from_file_location("strike_mark", root / "tools" / "strike-mark.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def check_one(svg: str, ticks: int, bars: int) -> list[str]:
    problems = []
    try:
        rootel = ET.fromstring(svg)
    except ET.ParseError as exc:
        return [f"does not parse: {exc}"]
    view = rootel.get("viewBox", "0 0 0 0").split()
    size = float(view[2])
    ns = "{http://www.w3.org/2000/svg}"

    for el in rootel.iter():
        for attr in ("d", "x1", "y1", "x2", "y2", "cx", "cy"):
            value = el.get(attr)
            if value is None:
                continue
            for number in NUM.findall(value):
                if not 0 <= float(number) <= size:
                    problems.append(f"{el.tag.replace(ns, '')} {attr} leaves the canvas ({number})")
                    break

    ring = [el for el in rootel.iter(f"{ns}circle") if el.get("class") == "ring"]
    if not ring:
        problems.append("no ring")
    else:
        r = float(ring[0].get("r", 0)) + float(ring[0].get("stroke-width", 1)) / 2 + 6
        if float(ring[0].get("cx")) + r > size or float(ring[0].get("cx")) - r < 0:
            problems.append("the ring or its marks are clipped")

    got_ticks = sum(1 for el in rootel.iter(f"{ns}line") if el.get("class") == "tick")
    got_bars = sum(1 for el in rootel.iter(f"{ns}line") if el.get("class") == "bar")
    if got_ticks + got_bars != ticks:
        problems.append(f"asked for {ticks} marks on the ring, struck {got_ticks + got_bars}")
    if got_bars != bars:
        problems.append(f"asked for {bars} bars, struck {got_bars}")

    wax = [el for el in rootel.iter(f"{ns}path") if el.get("class") == "wax"]
    if wax and ring:
        far = max(
            abs(float(n) - float(ring[0].get("cx"))) for n in NUM.findall(wax[0].get("d", ""))
        )
        if far >= float(ring[0].get("r")) - 4:
            problems.append("the wax rim reaches the ring")

    if len(svg.encode("utf-8")) > BUDGET_BYTES:
        problems.append(f"{len(svg.encode('utf-8'))} bytes is over the {BUDGET_BYTES} budget")
    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("root", nargs="?", default=".", help="repository root (default: .)")
    args = parser.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    root = Path(args.root).resolve()
    striker = load_striker(root)

    cases: list[tuple[str, str, int, int, bool]] = []
    for i in range(48):
        digest = hashlib.sha256(str(i).encode()).hexdigest()
        cases.append((f"oh:us:house:x{i:06d}", digest, i % 7, min(i % 3, i % 7), False))
        cases.append((digest, digest, 0, 0, True))

    meta = root / "data" / "meta.json"
    holders = root / "data" / "officeholders.ndjson"
    real = 0
    if meta.is_file() and holders.is_file():
        digest = json.loads(meta.read_text(encoding="utf-8"))["digest"]
        with holders.open(encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    cases.append((json.loads(line)["id"], digest, 0, 0, False))
                    real += 1

    failures = []
    for seed, digest, ticks, bars, word in cases:
        first = striker.strike(seed, digest, ticks, bars, word)
        second = striker.strike(seed, digest, ticks, bars, word)
        problems = check_one(first, ticks, bars)
        if first != second:
            problems.append("two strikes differ")
        for problem in problems:
            failures.append(f"{seed[:28]} @ {digest[:8]} ticks={ticks} bars={bars}: {problem}")

    try:
        striker.strike("x", "y", ticks=1, bars=2)
        failures.append("a bar without a tick was allowed")
    except ValueError:
        pass

    for line in failures[:40]:
        print(f"FAIL  {line}")
    if failures:
        print(f"\n{len(failures)} problems across {len(cases)} strikes.")
        return 1
    print(
        f"OK    {len(cases)} strikes legible and deterministic: 96 synthetic, "
        f"{real} officeholders at the real digest."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
