"""Tests for tools/strike-mark.py and tools/check-mark.py (ECOSYSTEM.md §2)."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name.replace("-", "_"), HERE / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


strike = _load("strike-mark")
check = _load("check-mark")
DIGEST = "e8a70ee80faada3f329b6e2927630d752a1b0d20474c30159726ffd161884687"


def test_same_inputs_strike_identical_bytes():
    assert strike.strike("oh:us:house:a000055", DIGEST) == strike.strike(
        "oh:us:house:a000055", DIGEST
    )


def test_one_changed_row_changes_the_seal():
    other = DIGEST[:-1] + ("0" if DIGEST[-1] != "0" else "1")
    assert strike.strike("oh:us:house:a000055", DIGEST) != strike.strike(
        "oh:us:house:a000055", other
    )


def test_two_officeholders_get_different_seals_at_one_build():
    assert strike.strike("oh:us:house:a000055", DIGEST) != strike.strike(
        "oh:us:house:b001323", DIGEST
    )


def test_the_seal_names_what_it_is_and_is_not():
    svg = strike.strike("oh:us:house:a000055", DIGEST)
    assert "It says nothing about the person." in svg
    assert "<title" in svg and 'role="img"' in svg


def test_ring_carries_one_mark_per_signal():
    svg = strike.strike("oh:us:house:a000055", DIGEST, ticks=5, bars=2)
    assert svg.count('class="tick"') == 3 and svg.count('class="bar"') == 2


def test_a_bar_needs_a_tick():
    with pytest.raises(ValueError):
        strike.strike("x", DIGEST, ticks=0, bars=1)


def test_the_wordmark_is_geometry_not_a_font():
    svg = strike.strike(DIGEST, DIGEST, with_wordmark=True)
    assert 'class="wordmark"' in svg and "font" not in svg.lower()


def test_no_stroke_names_a_colour():
    svg = strike.strike("oh:us:house:a000055", DIGEST)
    assert "currentColor" in svg and "#0" not in svg and "rgb(" not in svg


def test_check_mark_accepts_a_good_strike_and_names_a_bad_one():
    good = strike.strike("oh:us:house:a000055", DIGEST, ticks=3, bars=1)
    assert check.check_one(good, ticks=3, bars=1) == []
    assert any("asked for" in p for p in check.check_one(good, ticks=4, bars=1))
    clipped = good.replace('r="104"', 'r="140"')
    assert any("clipped" in p for p in check.check_one(clipped, ticks=3, bars=1))


def test_the_gate_is_green_on_the_repository(capsys):
    assert check.main([str(ROOT)]) == 0
    assert "legible and deterministic" in capsys.readouterr().out
