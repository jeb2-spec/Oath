#!/usr/bin/env python3
"""Strike the Oath mark. ECOSYSTEM.md §2.

A wax seal rendered as guilloche, struck from a seed and the build's digest.
Nothing here is drawn by hand: every curve is computed from bytes, so the same
inputs strike the same bytes on any machine, and one changed row in the register
strikes a visibly different seal. The mark is proof, not a picture of proof.

Two marks share one die:

  the officeholder seal   seed = the officeholder's identifier
                          the ring carries one tick per Signal defined against
                          them and one bar per Signal that fired; today, none
  the build mark          seed = the digest itself, with the wordmark inside

Craft rules kept from ECOSYSTEM.md §2.4: struck, not drawn; lettering as
geometry rather than a font request, so a browser without the font renders it
identically; every stroke uses currentColor, so the page's own ink colours it in
either theme. Standard library.

    python tools/strike-mark.py --seed oh:us:house:a000055 --digest <sha256>
    python tools/strike-mark.py --seed <sha256> --digest <sha256> --wordmark
"""

from __future__ import annotations

import argparse
import hashlib
import math
import sys

TAU = 2 * math.pi
SAMPLES = 144  # points per curve; enough to read as a continuous engraved line


def die(seed: str, digest: str) -> bytes:
    """The bytes the whole mark is computed from. Change either input, change them all."""
    return hashlib.sha256(f"{seed}\n{digest}".encode()).digest()


def _f(value: float) -> str:
    """A coordinate, one decimal, no trailing zero noise, stable across platforms."""
    text = f"{value:.1f}"
    return text[:-2] if text.endswith(".0") else text


def closed_path(points: list[tuple[float, float]]) -> str:
    head = f"M{_f(points[0][0])},{_f(points[0][1])}"
    rest = "".join(f"L{_f(x)},{_f(y)}" for x, y in points[1:])
    return head + rest + "Z"


def rosette(d: bytes, cx: float, cy: float, radius: float) -> list[str]:
    """Nested guilloche curves. The count, lobes, depth and phase all come from the die."""
    count = 4 + d[0] % 3
    paths = []
    for i in range(count):
        base = radius * (0.50 + 0.42 * i / max(count - 1, 1))
        lobes = 5 + d[1 + i] % 9
        depth = 0.05 + (d[7 + i] % 100) / 1000
        phase = d[13 + i] / 255 * TAU
        second = 2 * lobes + d[19 + i] % 3
        points = []
        for s in range(SAMPLES):
            t = TAU * s / SAMPLES
            r = base * (
                1
                + depth * math.sin(lobes * t + phase)
                + depth / 3 * math.sin(second * t + 2 * phase)
            )
            points.append((cx + r * math.cos(t), cy + r * math.sin(t)))
        paths.append(closed_path(points))
    return paths


def wax_edge(d: bytes, cx: float, cy: float, radius: float) -> str:
    """The seal's rim, slightly irregular the way pressed wax is."""
    phase = d[25] / 255 * TAU
    points = []
    for s in range(SAMPLES):
        t = TAU * s / SAMPLES
        r = radius * (1 + 0.014 * math.sin(3 * t + phase) + 0.009 * math.sin(7 * t + 2 * phase))
        points.append((cx + r * math.cos(t), cy + r * math.sin(t)))
    return closed_path(points)


def ring_marks(cx: float, cy: float, radius: float, ticks: int, bars: int) -> list[str]:
    """One tick per Signal defined, one bar per Signal fired. Bars take the first positions."""
    out = []
    for i in range(ticks):
        angle = -TAU / 4 + TAU * i / ticks
        bar = i < bars
        inner, outer, width = (
            (radius - 6, radius + 6, 2.4) if bar else (radius - 3.5, radius + 3.5, 1)
        )
        x1, y1 = cx + inner * math.cos(angle), cy + inner * math.sin(angle)
        x2, y2 = cx + outer * math.cos(angle), cy + outer * math.sin(angle)
        cls = "bar" if bar else "tick"
        out.append(
            f'<line class="{cls}" x1="{_f(x1)}" y1="{_f(y1)}" x2="{_f(x2)}" y2="{_f(y2)}" '
            f'stroke-width="{width}"/>'
        )
    return out


def wordmark(cx: float, cy: float, scale: float) -> str:
    """The word *oath* as monoline geometry: two bowls, three stems, one arch, one bar.

    Designed once in a 100 by 34 box, then placed. No font is requested anywhere.
    """
    ox, oy = cx - 50 * scale, cy - 17 * scale

    def p(x: float, y: float) -> str:
        return f"{_f(ox + x * scale)},{_f(oy + y * scale)}"

    r = _f(10 * scale)
    return (
        f'<g class="wordmark" fill="none" stroke-width="{_f(2.6 * scale)}" '
        f'stroke-linecap="round" stroke-linejoin="round">'
        f'<circle cx="{_f(ox + 12 * scale)}" cy="{_f(oy + 22 * scale)}" r="{r}"/>'
        f'<circle cx="{_f(ox + 38 * scale)}" cy="{_f(oy + 22 * scale)}" r="{r}"/>'
        f'<path d="M{p(48, 12)}L{p(48, 32)}"/>'
        f'<path d="M{p(60, 2)}L{p(60, 32)}M{p(54, 12)}L{p(68, 12)}"/>'
        f'<path d="M{p(78, 2)}L{p(78, 32)}M{p(78, 22)}A{r},{r} 0 0 1 {p(98, 22)}L{p(98, 32)}"/>'
        "</g>"
    )


def strike(
    seed: str, digest: str, ticks: int = 0, bars: int = 0, with_wordmark: bool = False
) -> str:
    """The mark as a complete SVG document string. Deterministic in its inputs."""
    if bars > ticks:
        raise ValueError("a Signal cannot fire without being defined: bars must not exceed ticks")
    d = die(seed, digest)
    size = 240.0
    c = size / 2
    seal_r = 88.0
    ring_r = 104.0
    title = "The Oath mark" if with_wordmark else "Oath seal"
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {_f(size)} {_f(size)}" '
        f'width="{_f(size)}" height="{_f(size)}" role="img" aria-labelledby="t d">',
        f'<title id="t">{title}</title>',
        f'<desc id="d">Struck from {seed} at build {digest[:12]}. '
        "It changes when the record changes. It says nothing about the person.</desc>",
        '<g stroke="currentColor" fill="none">',
        f'<circle class="ring" cx="{_f(c)}" cy="{_f(c)}" r="{_f(ring_r)}" stroke-width="0.8"/>',
        *ring_marks(c, c, ring_r, ticks, bars),
        f'<path class="wax" d="{wax_edge(d, c, c, seal_r)}" stroke-width="1.6" '
        'fill="currentColor" fill-opacity="0.06"/>',
        '<g class="guilloche" stroke-width="0.55" stroke-opacity="0.85">',
        *(f'<path d="{path}"/>' for path in rosette(d, c, c, seal_r * 0.86)),
        "</g>",
        f'<circle class="centre" cx="{_f(c)}" cy="{_f(c)}" r="1.6" fill="currentColor"/>',
    ]
    if with_wordmark:
        parts.append(
            f'<circle cx="{_f(c)}" cy="{_f(c)}" r="{_f(seal_r * 0.46)}" '
            'fill="var(--paper, #fff)" stroke="none"/>'
        )
        parts.append(wordmark(c, c + 2, 0.66))
    parts.append("</g></svg>")
    return "\n".join(parts) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument(
        "--seed", required=True, help="officeholder id, or the digest for the build mark"
    )
    parser.add_argument("--digest", required=True, help="the build digest from data/meta.json")
    parser.add_argument("--ticks", type=int, default=0, help="Signals defined against the seed")
    parser.add_argument("--bars", type=int, default=0, help="Signals that fired")
    parser.add_argument(
        "--wordmark", action="store_true", help="strike the build mark with the word"
    )
    parser.add_argument("--out", help="write here instead of stdout")
    args = parser.parse_args(argv)
    svg = strike(args.seed, args.digest, args.ticks, args.bars, args.wordmark)
    if args.out:
        with open(args.out, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(svg)
        print(f"struck {args.out} ({len(svg)} bytes)")
    else:
        sys.stdout.write(svg)
    return 0


if __name__ == "__main__":
    sys.exit(main())
