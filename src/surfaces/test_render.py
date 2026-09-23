"""Tests for src/surfaces/render.py: the pages stay a door and a record, never a scoreboard.

The cases here are the Council's first reading of these pages (PR #27), pinned so they
cannot come back: a quiet page is a matching gap and says so with its count; every
citation links; the chart shows every matched row; the six seats without a floor vote
carry the roster's own title; the landing never puts a number beside a person.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

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


def office(seat: str, title: str = "United States Representative") -> dict:
    return {
        "id": f"of:us:house-{seat.lower()}:2025",
        "seat": seat,
        "state": seat[:2],
        "district": seat[2:],
        "title": title,
        "term_start": "2025-01-03",
        "term_end": None,
        "jurisdiction": "us:federal",
    }


def holder(seat: str, name: str, key: str, sworn: str = "2025-01-03", title: str | None = None):
    return {
        "id": f"oh:us:house:{key}",
        "legal_name": name,
        "offices": [office(seat, title) if title else office(seat)],
        "notes": f"Sworn {sworn}. Presence in the register is not evidence of wrongdoing.",
        "source": {"url": "https://example.com", "retrieved_at": "2026-09-22T21:40:17Z"},
    }


def filing(holder_id: str, day: str, n: int, code: str = "P") -> dict:
    return {
        "id": f"fl:house-clerk:{code}:{n}",
        "officeholder_id": holder_id,
        "filed_at": day,
        "form_type": "House-PTR" if code == "P" else "other",
        "source_form_code": code,
        "source": {"url": "https://example.com/doc.pdf", "retrieved_at": "2026-09-22T21:40:20Z"},
    }


OFFICES = [office("AK00"), office("AL01"), office("AL02"), office("PR00", "Resident Commissioner")]
HOLDERS = [
    holder("AK00", "Example Alaska", "a000001"),
    holder("AL01", "Example Alabama", "a000002", sworn="2026-09-01"),
    holder("PR00", "Example Commissioner", "a000003", title="Resident Commissioner"),
]
FILINGS = [
    filing("oh:us:house:a000001", "2025-03-01", 1),
    filing("oh:us:house:a000001", "2025-03-09", 2, code="O"),
    filing("oh:us:house:a000002", "2026-05-30", 3),
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
    "rejected_by_reason": {"surname matches a sitting member": 7},
    "sources": [
        {
            "name": "2025FD.zip",
            "retrieved_at": "2026-09-22T21:40:20Z",
            "last_modified": "Tue, 22 Sep 2026 13:00:11 GMT",
        },
        {"name": "MemberData.xml", "retrieved_at": "2026-09-22T21:40:17Z"},
    ],
}
REJECTED = [
    {
        "reason": "surname matches a sitting member (Commissioner, Example, PR00) but "
        "the given names differ; the document carries no Filing ID line (scanned paper, or a "
        "form that prints none) and cannot confirm the filer; a human decides this one",
        "source_row": {"state_dst": "PR00", "last": "Commissioner", "first": "E. X."},
    },
    {
        "reason": "surname matches a sitting member (Commissioner, Example, PR00) but "
        "the given names differ; a human decides this one",
        "source_row": {"state_dst": "TX99", "last": "Commissioner", "first": "Other"},
    },
    {
        "reason": "no sitting member has this name; the row is a candidate or a former member",
        "source_row": {"state_dst": "PR00", "last": "Someone", "first": "Else"},
    },
]


def test_held_rows_are_counted_only_at_the_members_own_seat_by_why_they_wait():
    assert render.held_at_seat(REJECTED, HOLDERS) == {"PR00": {"no_filing_id": 1, "elsewhere": 1}}
    also = REJECTED + [
        {
            "reason": "no sitting member has this name; the row is a candidate or a former member",
            "source_row": {"state_dst": "PR00", "last": "Commissioner", "first": "Third"},
        }
    ]
    counted = render.held_at_seat(also, HOLDERS)
    assert counted == {"PR00": {"no_filing_id": 1, "elsewhere": 1, "other": 1}}, (
        "a same-surname row at the seat is counted whatever reason the adapter gave"
    )
    assert render.held_total(counted) == 2


def test_a_quiet_page_is_a_matching_gap_and_says_so_with_its_count():
    page = render.render_officeholder(HOLDERS[2], [], META, striker, held_here={"no_filing_id": 1})
    assert "not yet matched" in page
    assert "or on the Clerk's document printing Status Member at this seat" in page
    assert "1 row of the index at this seat carries this surname" in page
    assert (
        "1 whose document carries no Filing ID line (scanned paper, or a form that prints none)"
        in page
    )
    assert "not a statement that no filing was made" in page
    assert "not a statement about what was filed" in page
    assert "each link below" not in page, "no links below on a quiet page"
    assert "Nothing is attributed" not in page


def test_a_page_with_rows_prints_bare_codes_and_the_clerks_ownership():
    page = render.render_officeholder(HOLDERS[0], FILINGS[:2], META, striker)
    assert '<td class="code">P</td>' in page and '<td class="code">O</td>' in page
    assert "(other)" not in page and "(House-PTR)" not in page
    assert "the Clerk does not publicly define it" in page


def test_every_citation_links():
    page = render.render_officeholder(HOLDERS[0], FILINGS[:2], META, striker)
    for href in (
        render.USC_3331,
        render.USC_CH131,
        render.STOCK_ACT,
        render.STANDARDS_C1,
        render.STANDARDS_S1,
        render.STANDARDS_S2,
    ):
        assert f'href="{href}"' in page


def test_the_office_line_carries_the_roster_title_and_sworn_date_not_a_term():
    page = render.render_officeholder(HOLDERS[1], FILINGS[2:], META, striker)
    assert "sworn 2026-09-01, per the roster read 2026-09-22" in page
    assert "term 2025-01-03" not in page
    commissioner = render.render_officeholder(HOLDERS[2], [], META, striker)
    assert "Resident Commissioner · seat PR00" in commissioner


def test_the_seal_caption_says_it_changes_with_every_build():
    page = render.render_officeholder(HOLDERS[0], FILINGS[:2], META, striker)
    assert "It changes with every build." in page
    assert "changes when the record changes" not in page


def test_every_state_in_the_data_gets_a_tile_and_nonvoting_seats_are_dashed():
    html = render.tile_map(OFFICES)
    for code in ("AK", "AL", "PR"):
        assert f'href="#state-{code}"' in html
    assert 'class="tile nv"' in html and ">PR<small>1</small>" in html
    assert ">AL<small>2</small>" in html


def test_the_index_passes_both_gates_with_state_rows_and_a_vacancy():
    page = render.render_index(HOLDERS, OFFICES, FILINGS, RUN, META, striker, {"PR00": 1})
    assert ranking.check_index(page) == []
    assert frame.check_page(page) is None
    assert 'id="state-AL"' in page and "Vacant" in page
    assert 'data-id="of:us:house-al02:2025"' in page, "vacant rows carry the office id"


def test_the_state_of_the_record_names_no_person_and_counts_the_nonvoting_seats():
    section = render.state_of_record(META, RUN, HOLDERS, FILINGS, OFFICES, 1, "https://x/rows")
    assert "Example" not in section
    assert "3 with a floor vote" in section and "1 resident commissioner" in section
    assert "<dt>7</dt>" in section and "1 of them sit at a member's own seat" in section
    assert 'href="https://x/rows"' in section
    assert "signals defined, so 0 fired" in section
    assert "width:75%" in section, "the bar floors rather than rounding 3 of 4 up"


def test_the_rhythm_shows_every_matched_row_across_years():
    svg, first, last, total = render.rhythm_chart(FILINGS)
    assert (first, last, total) == ("Mar 2025", "May 2026", 3)
    assert "Example" not in svg


def test_the_lede_no_longer_promises_every_filing():
    page = render.render_index(HOLDERS, OFFICES, FILINGS, RUN, META, striker)
    assert "every financial disclosure they have filed" not in page
    assert "the register could match to the name" in page
    assert "a written rule catches" not in page
    assert "Most pages will stay quiet" not in page


def test_a_scanned_document_is_captured_not_read_and_the_page_says_which():
    read = dict(filing("oh:us:house:a000001", "2025-03-01", 1))
    read["source"] = dict(read["source"], content_hash="a" * 64)
    read["extraction_confidence"] = "structured"
    scanned = dict(filing("oh:us:house:a000001", "2025-04-01", 2))
    scanned["source"] = dict(scanned["source"], content_hash="b" * 64)
    scanned["extraction_confidence"] = None
    pending = filing("oh:us:house:a000001", "2025-05-01", 3, code="O")
    assert render.documents_read([read, scanned, pending]) == (1, 1)
    page = render.render_officeholder(HOLDERS[0], [read, scanned, pending], META, striker)
    assert "partly read" in page
    assert "1 of 3 documents read and hashed" in page
    assert "1 captured and hashed, not read: scanned paper, or a form" in page
    assert "1 not yet captured" in page
    assert "the register read each document" not in page
    section = render.state_of_record(
        META, RUN, HOLDERS, [read, scanned, pending], OFFICES, 1, "https://x/rows"
    )
    assert "<dt>1</dt><dd>of 3 documents read" in section
    assert "1 more captured and hashed, not read" in section


def test_a_row_attributed_by_the_document_says_so_on_the_page_and_the_landing():
    by_header = dict(filing("oh:us:house:a000001", "2025-06-01", 9))
    by_header["notes"] = (
        "Attributed by the document's own header: the Clerk's index writes the filer as "
        "'Ex A. Alaska'; the document prints 'Hon. Ex A. Alaska', Status Member, State/District "
        "AK00, Filing ID 9; the Clerk's roster names the holder of AK00 'Example Alaska'."
    )
    page = render.render_officeholder(
        HOLDERS[0], [FILINGS[0], by_header], META, striker, held_here={"before_sworn": 1}
    )
    assert "2 rows of the Clerk's 2025 index attributed to this officeholder" in page
    assert "1 of them by the document's own header" in page
    assert "matched to this name" not in page
    assert '<td class="code">document</td>' in page and '<td class="code">name</td>' in page
    assert "<th>How</th>" in page
    assert "1 dated by the index before the swearing-in" in page, "held rows show on every page"
    section = render.state_of_record(
        META, RUN, HOLDERS, [FILINGS[0], by_header], OFFICES, 1, "https://x/rows"
    )
    assert "1 of them by the document's own header" in section
    assert "or the Clerk's document confirmed the filer at that seat" in section
    assert "matched to their name" not in section


def test_rows_under_the_surname_at_another_seat_are_said_without_naming_the_seat():
    moved = [
        {
            "reason": "surname matches a sitting member (Commissioner, Example, PR00) but the "
            "given names differ; a human decides this one",
            "source_row": {"state_dst": "TX99", "last": "Commissioner", "first": "Other"},
        }
    ]
    counted = render.held_at_seat(moved, HOLDERS)
    assert counted == {"PR00": {"elsewhere": 1}}
    assert render.held_total(counted) == 0, "a row at another seat is not at the member's own seat"
    page = render.render_officeholder(HOLDERS[2], [], META, striker, held_here=counted["PR00"])
    assert "1 row of the index under this surname sits at another seat" in page
    assert "holds it because the surname alone matched, and does not say whose it is" in page
    assert "TX99" not in page
    assert "No row of the index at this seat carries this surname" not in page


def test_a_shared_particle_is_not_the_members_surname_on_the_page_count():
    holder_cruz = holder("TX15", "Monica De La Cruz", "d000001")
    holder_cruz["common_name"] = "De La Cruz, Monica"
    rows = [
        {
            "reason": "no sitting member has this name; the row is a candidate or a former member",
            "source_row": {"state_dst": "TX15", "last": "De Barros", "first": "J."},
        },
        {
            "reason": "surname matches a sitting member (De La Cruz, Monica, TX15) but the given "
            "names differ; the document carries no Filing ID line and cannot confirm the filer; "
            "a human decides this one",
            "source_row": {"state_dst": "TX15", "last": "De La Cruz", "first": "Carlos"},
        },
    ]
    assert render.held_at_seat(rows, [holder_cruz]) == {"TX15": {"no_filing_id": 1}}


def test_the_run_record_is_picked_by_the_set_aside_files_key_never_by_filename(tmp_path):
    runs = tmp_path / "data" / "adapter-runs"
    held = tmp_path / "data" / "rejected" / "house-fd"
    runs.mkdir(parents=True)
    held.mkdir(parents=True)
    (runs / "house-fd-2025-8b40.ndjson").write_text(
        '{"capture_key": "8b40", "counts": {"accepted": 2}}\n'
    )
    (runs / "house-fd-2025-a652.ndjson").write_text(
        '{"capture_key": "a652", "counts": {"accepted": 1}}\n'
    )
    (held / "2025-8b40.ndjson").write_text("")
    run, files = render.pick_run(tmp_path)
    assert run["capture_key"] == "8b40" and [f.name for f in files] == ["2025-8b40.ndjson"]
    (held / "2025-8b40.ndjson").unlink()
    (held / "2025-ffff.ndjson").write_text("")
    with pytest.raises(SystemExit):
        render.pick_run(tmp_path)
    (held / "2025-ffff.ndjson").unlink()
    (held / "2025-8b40.ndjson").write_text("")
    (runs / "house-fd-2025-a652.ndjson").unlink()
    run, _ = render.pick_run(tmp_path)
    assert run["capture_key"] == "8b40", "one record needs no key to be picked"
    (held / "2024-aaaa.ndjson").write_text("")
    (runs / "house-fd-2024-aaaa.ndjson").write_text('{"capture_key": "aaaa"}\n')
    with pytest.raises(SystemExit):
        render.pick_run(tmp_path), "two years each pair; the landing has no design for that yet"
