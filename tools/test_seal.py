"""The seal refuses a state text that does not carry the build's own figures."""

from __future__ import annotations

import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent


def load():
    spec = importlib.util.spec_from_file_location("seal_tool", HERE / "seal.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


META = {
    "rows": {
        "data/officeholders.ndjson": 439,
        "data/filings.ndjson": 1197,
        "data/transactions.ndjson": 7346,
    }
}
RUN = {
    "counts": {"quiet": 11, "rejected": 1737, "attributed_by_document": 101},
    "documents": {"read": 409},
    "rejected_by_reason": {"surname matches a sitting member": 162},
}
GOOD = (
    "439 filled; 1,197 filings, 101 of them by the document; 1,737 rows not attributed, 162 held; "
    "409 documents read; 7,346 transactions; 11 quiet."
)


def test_a_state_text_with_every_figure_passes():
    seal = load()
    assert seal.state_text_lacks({**META, "state": GOOD}, RUN) == ""
    assert seal.state_text_lacks({**META, "state": GOOD}) == ""


def test_a_stale_state_text_names_what_it_lacks():
    seal = load()
    stale = {**META, "state": GOOD.replace("1,197", "1,097").replace("11 quiet", "46 quiet")}
    lacking = seal.state_text_lacks(stale, RUN)
    assert "filings 1,197" in lacking and "quiet members 11" in lacking
    assert "transactions" not in lacking


def test_a_figure_inside_a_larger_number_does_not_count():
    seal = load()
    tricked = {
        **META,
        "state": "11,197 rows and 17,346 things and 2439 seats; 1,737; 162; 409; 101; 11",
    }
    lacking = seal.state_text_lacks(tricked, RUN)
    assert "filings 1,197" in lacking and "transactions 7,346" in lacking
    assert "officeholders 439" in lacking


def test_a_run_record_without_its_set_aside_file_refuses_the_seal(tmp_path):
    seal = load()
    runs = tmp_path / "data" / "adapter-runs"
    held = tmp_path / "data" / "rejected" / "house-fd"
    runs.mkdir(parents=True)
    held.mkdir(parents=True)
    (runs / "house-fd-2025-8b40.ndjson").write_text('{"capture_key": "8b40"}\n')
    (held / "2025-8b40.ndjson").write_text("")
    assert [r["capture_key"] for r in seal.current_runs(tmp_path)] == ["8b40"]
    (runs / "house-fd-2025-a652.ndjson").write_text('{"capture_key": "a652"}\n')
    try:
        seal.current_runs(tmp_path)
    except SystemExit as exc:
        assert "has no set-aside file" in str(exc)
    else:
        raise AssertionError("a record whose set-aside file is gone must refuse the seal")
