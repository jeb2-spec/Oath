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


def listing(attributes: str, rows: list[tuple[str, str, str]]) -> str:
    """A Signal page's table: (row key attribute, seat, last cell)."""
    body = "".join(
        f'<tr {key}><td>{seat}</td><td><a href="../../officeholders/{seat}.html">N</a></td>'
        f"<td>{last}</td></tr>"
        for key, seat, last in rows
    )
    return (
        f"<html><body><table {attributes}><thead><tr><th>Seat</th><th>Name</th><th>Reports</th>"
        f"</tr></thead><tbody>{body}</tbody></table></body></html>"
    )


def test_a_signal_page_in_seat_order_with_dates_passes():
    page = listing(
        'id="fired" data-order="seat" data-lists="officeholders"',
        [('data-seat="AK00"', "AK00", "2025-03-01"), ('data-seat="AL01"', "AL01", "2025-04-02")],
    )
    assert lint.check_summary(page) == []


def test_a_table_that_links_to_officeholders_is_checked_undeclared():
    """A list of persons is one whatever its author called it."""
    page = listing('id="fired"', [("", "AL01", "2025-03-01"), ("", "AK00", "2025-04-02")])
    assert "the fired table declares no data-order" in lint.check_summary(page)


def test_a_signal_page_ordered_by_its_findings_fails():
    page = listing(
        'id="fired" data-order="findings" data-lists="officeholders"',
        [('data-findings="3"', "AL01", "2025-03-01"), ('data-findings="1"', "AK00", "2025-04-02")],
    )
    assert any("does not permit" in f for f in lint.check_summary(page))


def test_a_count_beside_a_name_on_a_signal_page_fails():
    page = listing(
        'id="fired" data-order="seat" data-lists="officeholders"',
        [('data-seat="AK00"', "AK00", "4"), ('data-seat="AL01"', "AL01", "1")],
    )
    failures = lint.check_summary(page)
    assert "row 1 carries a bare number (4) beside a person" in failures


def test_a_summary_page_that_lists_no_one_passes():
    page = "<html><body><table><tr><td>1,292</td><td>rows</td></tr></table></body></html>"
    assert lint.check_summary(page) == []


def test_the_walk_reads_every_signal_page_and_names_the_failing_one(tmp_path: Path, capsys):
    (tmp_path / "signals" / "a-signal").mkdir(parents=True)
    (tmp_path / "index.html").write_text(index("seat", [("AK00", "A")]), encoding="utf-8")
    ranked = listing(
        'id="fired" data-order="seat" data-lists="officeholders"',
        [('data-seat="AL01"', "AL01", "2025-03-01"), ('data-seat="AK00"', "AK00", "2025-04-02")],
    )
    (tmp_path / "signals" / "a-signal" / "v1.html").write_text(ranked, encoding="utf-8")
    assert lint.main([str(tmp_path), "--site", "."]) == 1
    out = capsys.readouterr().out
    assert "signals/a-signal/v1.html: rows are not in the declared seat order" in out
