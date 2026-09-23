"""Tests for src/surfaces/render.py: the landing page stays a door and never a scoreboard."""

from __future__ import annotations

import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


render = _load(HERE / "render.py", "render_surface")
ranking = _load(ROOT / "tools" / "lint-no-ranking.py", "lint_no_ranking")
frame = _load(ROOT / "tools" / "lint-frame-presence.py", "lint_frame")
striker = _load(ROOT / "tools" / "strike-mark.py", "strike_mark")

DIGEST = "e8a70ee80faada3f329b6e2927630d752a1b0d20474c30159726ffd161884687"
META = {
    "build": "0001-house-2025",
    "built_at": "2026-09-22T21:40:20Z",
    "digest": DIGEST,
    "state": "",
    "anchor": {"state": "none"},
}


def office(seat: str) -> dict:
    return {
        "id": f"of:us:house-{seat.lower()}:2025",
        "seat": seat,
        "state": seat[:2],
        "district": seat[2:],
        "title": "United States Representative",
        "term_start": "2025-01-03",
        "term_end": None,
        "jurisdiction": "us:federal",
    }


def holder(seat: str, name: str, key: str) -> dict:
    return {
        "id": f"oh:us:house:{key}",
        "legal_name": name,
        "offices": [office(seat)],
        "source": {"url": "https://example.com", "retrieved_at": "2026-09-22T21:40:17Z"},
    }


def filing(holder_id: str, day: str, n: int) -> dict:
    return {
        "id": f"fl:house-clerk:P:{n}",
        "officeholder_id": holder_id,
        "filed_at": day,
        "form_type": "House-PTR",
        "source_form_code": "P",
        "source": {"url": "https://example.com/doc.pdf", "retrieved_at": "2026-09-22T21:40:20Z"},
    }


OFFICES = [office("AK00"), office("AL01"), office("AL02"), office("PR00")]
HOLDERS = [
    holder("AK00", "Example Alaska", "a000001"),
    holder("AL01", "Example Alabama", "a000002"),
    holder("PR00", "Example Commissioner", "a000003"),
]
FILINGS = [
    filing("oh:us:house:a000001", "2025-03-01", 1),
    filing("oh:us:house:a000001", "2025-03-09", 2),
    filing("oh:us:house:a000002", "2025-11-30", 3),
]
RUN = {
    "year": 2025,
    "counts": {
        "seats": 4,
        "filled": 3,
        "vacant": 1,
        "accepted": 3,
        "officeholders_with_a_filing": 2,
    },
    "rejected_by_reason": {"surname matches exactly one sitting member": 7},
    "sources": [
        {
            "name": "2025FD.zip",
            "retrieved_at": "2026-09-22T21:40:20Z",
            "last_modified": "Tue, 22 Sep 2026 13:00:11 GMT",
        },
        {"name": "MemberData.xml", "retrieved_at": "2026-09-22T21:40:17Z"},
    ],
}


def test_every_state_in_the_data_gets_a_tile():
    html = render.tile_map(OFFICES)
    for code in ("AK", "AL", "PR"):
        assert f'href="#state-{code}"' in html
    assert 'class="tile t"' in html, "a territory without a map position joins the last row"
    assert ">AL<small>2</small>" in html, "the small number is seats, a fact about the office"


def test_the_index_passes_the_no_ranking_gate_with_state_rows_and_a_vacancy():
    page = render.render_index(HOLDERS, OFFICES, FILINGS, RUN, META, striker)
    assert ranking.check_index(page) == []
    assert 'id="state-AL"' in page and "Vacant" in page


def test_the_index_carries_the_frame_in_its_header():
    page = render.render_index(HOLDERS, OFFICES, FILINGS, RUN, META, striker)
    assert frame.check_page(page) is None


def test_the_state_of_the_record_names_no_person_beside_a_number():
    section = render.state_of_record(META, RUN, HOLDERS, FILINGS, OFFICES)
    assert "Example" not in section, "no officeholder appears in the state of the record"
    assert "<dt>7</dt>" in section and "held for a person" in section
    assert "signals defined, so 0 fired" in section


def test_the_rhythm_counts_months_across_the_chamber():
    svg = render.rhythm_chart(FILINGS, 2025)
    assert ">2</text>" in svg and ">1</text>" in svg
    assert "Mar" in svg and "Nov" in svg and "Example" not in svg


def test_the_checklist_is_the_same_shape_for_everyone():
    with_rows = render.checks_section(HOLDERS[0], FILINGS[:2], RUN, held=7)
    without = render.checks_section(HOLDERS[2], [], RUN, held=7)
    for text in (with_rows, without):
        assert "Identity" in text and "Documents" in text and "Signals" in text
        assert "<b>not yet</b>" in text and "<b>none defined</b>" in text
    assert "2 filings attributed" in with_rows
    assert "nothing attributed" in without and "7 rows" in without
