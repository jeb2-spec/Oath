"""Fixture tests for tools/check-crossrefs.py.

The good fixture must pass. The bad fixture plants four defects, one of each kind the
gate catches, and every one must be reported. The repository itself must pass, which
is the gate doing its job on the documents that motivated it.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
FIXTURES = ROOT / "fixtures" / "tools" / "check-crossrefs"


def _load():
    spec = importlib.util.spec_from_file_location("check_crossrefs", HERE / "check-crossrefs.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_good_fixture_resolves_and_ignores_legal_citations():
    failures, checked = _load().check(FIXTURES / "good")
    assert failures == []
    assert checked >= 9, "the good fixture should exercise every reference form"


def test_bad_fixture_reports_each_planted_defect():
    failures, _ = _load().check(FIXTURES / "bad")
    joined = "\n".join(failures)
    assert "INVARIANTS.md §99 does not resolve" in joined
    assert "README.md §4 does not resolve" in joined
    assert "anchor #13-the-meta-invariant has no heading" in joined
    assert "link to docs/missing.md names a file that is not tracked" in joined
    assert len(failures) == 4, joined


def test_fenced_code_is_not_scanned():
    failures, _ = _load().check(FIXTURES / "good")
    assert not any("<anchor>" in f for f in failures)


def test_repository_resolves():
    failures, checked = _load().check(ROOT)
    assert failures == [], "\n".join(failures)
    assert checked > 100


def test_main_returns_nonzero_on_failure(capsys):
    module = _load()
    assert module.main([str(FIXTURES / "bad")]) == 1
    assert module.main([str(FIXTURES / "good")]) == 0
    out = capsys.readouterr().out
    assert "FAIL" in out and "OK" in out
