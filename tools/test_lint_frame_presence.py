"""Tests for tools/lint-frame-presence.py (INVARIANTS.md §7)."""

from __future__ import annotations

import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _load():
    spec = importlib.util.spec_from_file_location("lint_frame", HERE / "lint-frame-presence.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


lint = _load()

FRAMED = (
    "<html><body><header><p>Presence in the register is not evidence of wrongdoing.</p>"
    "<h1>A</h1></header></body></html>"
)
LATE = (
    "<html><body><header><h1>A</h1></header>"
    "<p>presence in the register is not evidence of wrongdoing</p></body></html>"
)
MISSING = "<html><body><header><h1>A</h1></header><p>Filings.</p></body></html>"
NO_HEADER = (
    "<html><body><h1>A</h1>"
    "<p>Presence in the register is not evidence of wrongdoing.</p></body></html>"
)


def test_frame_in_header_passes():
    assert lint.check_page(FRAMED) is None


def test_case_and_punctuation_do_not_matter():
    shouted = FRAMED.replace(
        "Presence in the register is not evidence of wrongdoing.",
        "PRESENCE, in the register... is NOT evidence of wrongdoing",
    )
    assert lint.check_page(shouted) is None


def test_frame_outside_header_fails():
    assert lint.check_page(LATE) == "the frame is on the page but outside the header"


def test_missing_frame_fails():
    assert lint.check_page(MISSING) == "the frame is missing"


def test_no_header_fails():
    assert lint.check_page(NO_HEADER) == "no <header> element"


def test_site_walk_names_the_failing_page(tmp_path: Path):
    pages = tmp_path / "officeholders"
    pages.mkdir()
    (pages / "good.html").write_text(FRAMED, encoding="utf-8")
    (pages / "bad.html").write_text(MISSING, encoding="utf-8")
    failures, checked = lint.check(tmp_path)
    assert checked == 2
    assert failures == ["officeholders\\bad.html: the frame is missing"] or failures == [
        "officeholders/bad.html: the frame is missing"
    ]


def test_nothing_rendered_is_not_a_failure(tmp_path: Path, capsys):
    assert lint.main([str(tmp_path)]) == 0
    assert "nothing rendered" in capsys.readouterr().out
