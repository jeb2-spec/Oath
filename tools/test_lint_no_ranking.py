"""Tests for tools/lint-no-ranking.py (INVARIANTS.md §13)."""

from __future__ import annotations

import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _load():
    spec = importlib.util.spec_from_file_location("lint_rank", HERE / "lint-no-ranking.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


lint = _load()


def index(order: str | None, rows: list[tuple[str, str]], extra_cell: str | None = None) -> str:
    attr = f' data-order="{order}"' if order is not None else ""
    body = ""
    for key, name in rows:
        keyattr = f' data-{order}="{key}"' if order else ""
        cells = f"<td>{key}</td><td><a href='x'>{name}</a></td>"
        if extra_cell is not None:
            cells += f"<td>{extra_cell}</td>"
        body += f"<tr{keyattr}>{cells}</tr>"
    return (
        f'<table id="officeholders"{attr}><thead><tr><th>Seat</th><th>Name</th></tr></thead>'
        f"<tbody>{body}</tbody></table>"
    )


def test_seat_order_with_no_numbers_passes():
    page = index("seat", [("AK00", "A"), ("AL01", "B"), ("AL02", "C")])
    assert lint.check_index(page) == []


def test_name_order_is_also_permitted():
    page = index("name", [("Adams", "Adams"), ("Baker", "Baker")])
    assert lint.check_index(page) == []


def test_rows_out_of_declared_order_fail():
    page = index("seat", [("AL02", "C"), ("AK00", "A")])
    assert "rows are not in the declared seat order" in lint.check_index(page)


def test_an_order_the_invariant_does_not_permit_fails():
    page = index("findings", [("3", "A"), ("1", "B")])
    failures = lint.check_index(page)
    assert any("does not permit" in f for f in failures)


def test_an_undeclared_order_fails():
    page = index(None, [("AK00", "A")])
    assert "the officeholders table declares no data-order" in lint.check_index(page)


def test_a_bare_number_beside_a_person_fails():
    page = index("seat", [("AK00", "A"), ("AL01", "B")], extra_cell="7")
    failures = lint.check_index(page)
    assert any("bare number" in f for f in failures)


def test_a_date_is_not_a_bare_number():
    page = index("seat", [("AK00", "A")], extra_cell="2025-01-03")
    assert lint.check_index(page) == []


def test_missing_table_fails():
    assert lint.check_index("<html><body><p>nothing</p></body></html>") == [
        'no table with id="officeholders"; the index cannot be checked'
    ]


def test_nothing_rendered_is_not_a_failure(tmp_path: Path, capsys):
    assert lint.main([str(tmp_path)]) == 0
    assert "nothing rendered" in capsys.readouterr().out
