"""Tests for src/surfaces/render.py: the pages stay a door and a record, never a scoreboard.

The cases here are the Council's first reading of these pages (PR #27), pinned so they
cannot come back: a quiet page is a matching gap and says so with its count; every
citation links; the chart shows every matched row; the six seats without a floor vote
carry the roster's own title; the landing never puts a number beside a person.
"""

from __future__ import annotations

import html
import importlib.util
import re
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
build_reasons = _load(ROOT / "src" / "adapters" / "house-fd" / "build.py", "house_fd_reasons")
ERA = dict(render.ERA)


@pytest.fixture(autouse=True)
def the_era_of_the_fixtures():
    """Each test starts from the 119th Congress, open, and no kept captures; a page that
    renders a closed year sets the era from its run, as main() does."""
    render.ERA.clear()
    render.ERA.update(
        ERA, roster_read="2026-09-22", last_roster_read="2026-09-22", first_read="2026-09-22"
    )
    render.KEPT.clear()
    yield


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
        "sworn_at": sworn,
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
    assert render.held_by_holder(REJECTED, HOLDERS) == {
        "oh:us:house:a000003": {"no_filing_id": 1, "elsewhere": 1}
    }
    also = REJECTED + [
        {
            "reason": "no sitting member has this name; the row is a candidate or a former member",
            "source_row": {"state_dst": "PR00", "last": "Commissioner", "first": "Third"},
        }
    ]
    counted = render.held_by_holder(also, HOLDERS)
    assert counted == {"oh:us:house:a000003": {"no_filing_id": 1, "elsewhere": 1, "other": 1}}, (
        "a same-surname row at the seat is counted whatever reason the adapter gave"
    )
    assert render.held_total(counted) == 2
    assert render.held_rows_at_own_seat(also, HOLDERS) == 1, (
        "the landing's 'N of them' counts only rows held because the surname matches, the same "
        "rows as its total (the Council's second reading of S.1b)"
    )


def test_a_quiet_page_is_a_matching_gap_and_says_so_with_its_count():
    page = render.render_officeholder(HOLDERS[2], [], META, striker, held_here={"no_filing_id": 1})
    assert "not yet matched" in page
    assert "or on the Clerk's document printing Status Member at this seat" in page
    assert "1 row of the index at this seat carries this surname" in page
    assert (
        "1 whose document carries no Filing ID line (scanned paper, or a form that prints none)"
        in page
    )
    assert "a gap in the register's name-matching" in page
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
    """The office in its Congress, named with its terms, and the sworn date as the roster
    records it; never "this Congress", which a later reader cannot place (Seat G)."""
    page = html.unescape(render.render_officeholder(HOLDERS[1], FILINGS[2:], META, striker))
    assert (
        "United States Representative for AL01 in the 119th Congress (terms from noon, 3 January "
        "2025, to noon, 3 January 2027) · sworn in 2026-09-01, per "
        '<a href="#how-to-read">the Clerk\'s roster</a> read 2026-09-22'
    ) in page, "the first use of the Clerk's roster leads to what it is (Seat F)"
    assert 'id="how-to-read"' in page
    assert "this Congress" not in page and "term 2025-01-03" not in page
    commissioner = render.render_officeholder(HOLDERS[2], [], META, striker)
    assert "Resident Commissioner for PR00 in the 119th Congress" in commissioner


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
    page = render.render_index(HOLDERS, OFFICES, FILINGS, RUN, META, striker, 1)
    assert ranking.check_index(page) == []
    assert frame.check_page(page) is None
    assert 'id="state-AL"' in page and "Vacant" in page
    assert 'data-id="of:us:house-al02:2025"' in page, "vacant rows carry the office id"


def test_the_state_of_the_record_names_no_person_and_counts_the_nonvoting_seats():
    section = render.state_of_record(META, RUN, HOLDERS, FILINGS, OFFICES, 1, "https://x/rows")
    assert "Example" not in section
    assert "3 with a floor vote" in section and "1 resident commissioner" in section
    assert "<dt>7</dt>" in section and "1 of them sit at an officeholder's own seat" in section
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
    assert "1 fetched and hashed, not read: scanned paper, or a form" in page
    assert "1 not fetched" in page and "not yet fetched" not in page
    assert "the register read each document" not in page
    section = render.state_of_record(
        META, RUN, HOLDERS, [read, scanned, pending], OFFICES, 1, "https://x/rows"
    )
    assert "<dt>1</dt><dd>of those 3 documents read" in section
    assert "1 more fetched and hashed, not read" in section


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


def test_a_decided_report_says_decision_whether_or_not_its_document_was_read():
    """The Council's fourth reading of S.1b (Seats C, E and G): a decided report whose document
    the register read said "name", because the reading alone marked it. What attributed a row
    is said on the row, and read from there."""
    note = (
        "Attributed by the maintainer's recorded decision of 2026-10-06, citing "
        "https://disclosures-clerk.house.gov/public_disc/ptr-pdfs/2025/9.pdf."
    )
    read = dict(filing("oh:us:house:a000001", "2025-06-01", 9), notes=note)
    read["extraction_confidence"] = "structured"
    read["source"] = dict(read["source"], content_hash="0" * 64)
    unread = dict(filing("oh:us:house:a000001", "2025-06-02", 10), notes=note)
    for row in (read, unread):
        assert render.how_attributed(row) == "decision", row["id"]
    page = render.render_officeholder(HOLDERS[0], [FILINGS[0], read, unread], META, striker)
    assert page.count('<td class="code">decision</td>') == 2
    assert '<td class="code">name</td>' in page, "the row the name join attributed"
    assert "3 rows of the Clerk's 2025 index attributed to this officeholder, 2 of them by " in (
        plain(page)
    )
    assert "the maintainer's recorded decision, which cites its evidence" in page
    section = render.state_of_record(
        META, RUN, HOLDERS, [FILINGS[0], read, unread], OFFICES, 1, "https://x/rows"
    )
    assert "2 by the maintainer's recorded decision, which cites its evidence" in section
    render.DECIDED.update({read["id"]: "2026-10-06"})
    try:
        assert render.finding_mark({}, read["id"]) == (
            " (attributed by the maintainer's recorded decision of 2026-10-06)"
        ), "the Signal page marks a Finding on a decided report, as it marks a moved one"
    finally:
        render.DECIDED.clear()


def test_the_pages_read_a_decision_in_the_adapters_own_words():
    """The adapter writes what attributed a row; the pages read it back. One wording, held."""
    build = _load(ROOT / "src" / "adapters" / "house-fd" / "build.py", "house_fd_build_words")
    note = build.decision_note(
        {"decided_at": "2026-10-06T12:00:00Z", "evidence_url": "https://example.com/9.pdf"}
    )
    assert (build.BY_DECISION, build.BY_HEADER) == (render.BY_DECISION, render.BY_HEADER)
    assert render.how_attributed({"id": "fl:x", "officeholder_id": "oh:x", "notes": note}) == (
        "decision"
    )
    assert render.DECIDED_ON.match(note).group(1) == "2026-10-06"


def test_rows_under_the_surname_at_another_seat_are_said_without_naming_the_seat():
    moved = [
        {
            "reason": "surname matches a sitting member (Commissioner, Example, PR00) but the "
            "given names differ; a human decides this one",
            "source_row": {"state_dst": "TX99", "last": "Commissioner", "first": "Other"},
        }
    ]
    counted = render.held_by_holder(moved, HOLDERS)
    assert counted == {"oh:us:house:a000003": {"elsewhere": 1}}
    assert render.held_rows_at_own_seat(moved, HOLDERS) == 0, (
        "a row at another seat is not at the member's own seat"
    )
    page = render.render_officeholder(
        HOLDERS[2], [], META, striker, held_here=counted["oh:us:house:a000003"]
    )
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
    assert render.held_by_holder(rows, [holder_cruz]) == {
        "oh:us:house:d000001": {"no_filing_id": 1}
    }


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


def transaction(filing_id: str, n: int, **over) -> dict:
    row = {
        "id": f"tx:house-clerk:{filing_id.rsplit(':', 1)[1]}:{n:03d}",
        "filing_id": filing_id,
        "officeholder_id": "oh:us:house:a000001",
        "owner": "unmarked",
        "asset": "Example Widgets Inc. Common Stock (EXW)",
        "asset_normalized": "EXW",
        "asset_code": "ST",
        "action": "purchase",
        "transaction_date": "2025-02-10",
        "notified_date": "2025-02-12",
        "amount_range": {"min": 1001, "max": 15000, "currency": "USD"},
        "notes": (
            "Asset code ST per the Clerk's legend "
            "(https://fd.house.gov/reference/asset-type-codes.aspx); type printed as P."
        ),
    }
    row.update(over)
    return row


def test_transactions_are_listed_as_filed_grouped_by_report_and_interpreted_not_at_all():
    read = dict(filing("oh:us:house:a000001", "2025-03-01", 1))
    read["source"] = dict(read["source"], content_hash="a" * 64)
    read["extraction_confidence"] = "structured"
    later = dict(filing("oh:us:house:a000001", "2025-06-01", 2))
    later["source"] = dict(later["source"], content_hash="c" * 64)
    later["extraction_confidence"] = "structured"
    rows = [
        transaction(read["id"], 1, filing_status="Deleted"),
        transaction(
            read["id"],
            2,
            owner="spouse",
            action="sale-partial",
            amount_range={"min": 50000000, "max": None, "currency": "USD"},
            notes="Asset code GS per the Clerk's legend (x); type printed as S (partial). "
            "Description, as filed: Called Security.",
        ),
        transaction(
            later["id"],
            1,
            owner="joint",
            action="exchange",
            amount_range={"min": 823, "max": 824, "currency": "USD"},
            notes="Asset code none per the Clerk's legend (x); type printed as E. "
            "Amount printed as $823.45, an exact figure rather than one of the form's bands.",
        ),
    ]
    page = render.render_officeholder(HOLDERS[0], [read, later], META, striker, 0, rows)
    section = page[page.index('<section id="transactions">') : page.index('<section id="requires"')]
    assert "Transactions reported" in section
    assert "House Committee on Ethics</a>" in section and "the form and" in section
    assert (
        "does not require the mark, so a row that is not marked says nothing about ownership"
        in section
    )
    assert "whether held by the member, the member's spouse or a dependent child" in section
    assert "not a gain or loss" in section and "appears under each" in section
    assert "<th>Transaction date</th>" in section and "<td>purchase, marked Deleted</td>" in section
    assert "· 2 rows, 1 marked Deleted ·" in section
    assert "the report itself may list them in another order" in section
    assert section.count('<h3 id="report-') == 2, "one heading per report read, in date order"
    assert section.index('id="report-1"') < section.index('id="report-2"')
    assert "Reports, by date filed (rows):" in section and "2025-03-01 (2)" in section
    assert (
        "<td>not marked</td>" in section
        and "<td>SP, spouse</td>" in section
        and "<td>JT, jointly held</td>" in section
    )
    assert "<td>partial sale</td>" in section and "<td>exchange</td>" in section
    assert '<td class="amt">$1,001 - $15,000</td>' in section
    assert '<td class="amt">Over $50,000,000</td>' in section
    assert '<td class="amt">$823.45</td>' in section, (
        "an exact figure is printed as the filer printed it"
    )
    assert '<span class="code">[ST]</span>' in section and "[none]" not in section
    assert '<span class="note">Description, as filed: Called Security.</span>' in section
    assert "Asset code" not in section.split("<tbody>")[1], (
        "the legend clause stays out of the cells"
    )
    for word in ("total", "average", "rank", "most", "largest"):
        assert word not in section.lower().split("<tbody>")[1]


def test_unread_and_absent_transaction_reports_are_said_plainly():
    scanned = dict(filing("oh:us:house:a000001", "2025-04-01", 3))
    scanned["source"] = dict(scanned["source"], content_hash="b" * 64)
    scanned["extraction_confidence"] = None
    page = render.render_officeholder(HOLDERS[0], [scanned], META, striker, 0, [])
    assert "The report filed 2025-04-01 is fetched and not read" in page
    assert "its transactions are not listed here. It is linked above." in page
    quiet = render.render_officeholder(HOLDERS[0], [FILINGS[1]], META, striker, 0, [], 12)
    assert (
        "No transaction report in the Clerk's 2025 index is attributed to this officeholder"
        in quiet
    )
    assert (
        "12 transaction reports at this seat under this surname are set aside and not attributed"
        in quiet
    )
    assert "the transactions the reports list are below, as filed" not in quiet


def test_the_landing_counts_transactions_and_names_no_one_by_them():
    rows = [transaction(FILINGS[0]["id"], n) for n in range(1, 8)] + [
        transaction(FILINGS[0]["id"], 9, filing_status="Amended")
    ]
    section = render.state_of_record(
        META, RUN, HOLDERS, FILINGS, OFFICES, 1, "https://x/rows", rows
    )
    assert (
        "<dt>8</dt><dd>rows the read reports list, as filed (1 of them marked Amended or Deleted"
        in section
    )
    assert "no page sums the amounts, averages them, or compares them with anyone else's" in section
    assert "Example" not in section


def test_the_landing_takes_the_set_aside_link_and_the_transaction_count_in_that_order():
    page = render.render_index(
        HOLDERS,
        OFFICES,
        FILINGS,
        RUN,
        META,
        striker,
        1,
        "https://x/rows",
        [transaction(FILINGS[0]["id"], n) for n in range(1, 6)],
    )
    assert "<dt>5</dt><dd>rows the read reports list" in page
    assert 'href="https://x/rows">The rows, with reasons' in page


def test_held_transaction_reports_at_the_seat_are_counted_by_code():
    rows = [
        {
            "reason": "surname matches a sitting member (Commissioner, Example, PR00) but the "
            "given names differ; the document carries no Filing ID line; a human decides this one",
            "source_row": {
                "state_dst": "PR00",
                "last": "Commissioner",
                "first": "R.",
                "filing_type": "P",
            },
        },
        {
            "reason": "surname matches a sitting member (Commissioner, Example, PR00) but the "
            "given names differ; a human decides this one",
            "source_row": {
                "state_dst": "PR00",
                "last": "Commissioner",
                "first": "R.",
                "filing_type": "O",
            },
        },
    ]
    assert render.held_reports_by_holder(rows, HOLDERS) == {"oh:us:house:a000003": 1}


def test_labelled_lines_stand_on_their_own_and_the_filer_owns_the_punctuation():
    tx = transaction(
        FILINGS[0]["id"],
        1,
        notes="Asset code ST per the Clerk's legend (x); type printed as P. "
        "Subholding of: Example Trust. Description, as filed: Sold 10 units. "
        "Comments, as filed: Per best practices.",
    )
    cell = render.asset_cell(tx)
    assert cell.count('<span class="note">') == 3
    assert '<span class="note">Description, as filed: Sold 10 units.</span>' in cell
    assert "Filing status" not in cell


def test_the_glossary_links_the_legend_and_the_limitation_on_private_names():
    page = render.render_officeholder(HOLDERS[0], FILINGS[:1], META, striker, 0, [])
    how = page[page.index("<h2>How to read this page</h2>") :]
    assert 'href="https://fd.house.gov/reference/asset-type-codes.aspx"' in how
    assert "LIMITATIONS.md#9-private-citizens-are-out-of-scope" in how
    assert "on an amendment" not in page, (
        "the register does not read whether a report amends another"
    )


# ---- the first Signal on the pages ------------------------------------------------------
#
# Driven through the Signal itself and its definition file, so these pin what a reader is
# shown for the rows the register would actually hold, not for hand-made Findings.

signal_module = _load(ROOT / "src" / "signals" / "stock-act-ptr-after-deadline.py", "signal_ptr")
signal_run = _load(ROOT / "src" / "signals" / "run.py", "signal_run")
verdict = _load(ROOT / "tools" / "lint-verdict-language.py", "lint_verdict")
SIGNAL = signal_run.parse_definition(ROOT / "docs" / "signals" / "stock-act-ptr-after-deadline.md")
AT = "2026-09-23T14:13:28Z"


def read_report(holder_id: str, day: str, n: int, read: bool = True) -> dict:
    report = dict(filing(holder_id, day, n))
    report["source"] = dict(report["source"], content_hash="a" * 64)
    report["extraction_confidence"] = "structured" if read else None
    return report


def evaluated(holders: list[dict], reports: list[dict], rows: list[dict]):
    """The Signal's Findings, as a build would publish them, and its outcomes by holder."""
    found, outcomes = signal_module.evaluate(holders, reports, rows)
    found = [dict(f, fired_at=AT, build_hash="b" * 64) for f in found]
    by_holder: dict[str, list[dict]] = {}
    for outcome in outcomes:
        by_holder.setdefault(outcome["officeholder_id"], []).append(outcome)
    return found, outcomes, by_holder


def sworn(h: dict, day: str = "2025-01-03") -> dict:
    return dict(h, sworn_at=day)


def verdict_words(page: str) -> list[str]:
    return [word for line in page.splitlines() for word in verdict.hits(line)]


def between(page: str, start: str, end: str) -> str:
    at = page.index(start)
    return page[at : page.index(end, at)]


# One report: a row due 2025-02-11 by its notification (2025-01-12 + 30) and a row still
# inside both limits, on a report the Clerk's index dates 2025-03-20: 37 days after.
LATE = [
    transaction("fl:house-clerk:P:1", 1, transaction_date="2025-01-10", notified_date="2025-01-12"),
    transaction("fl:house-clerk:P:1", 2, transaction_date="2025-03-01", notified_date="2025-03-02"),
]
for _row in LATE:
    _row["filing_status"] = "New"


def test_a_finding_shows_its_report_its_arithmetic_and_what_it_is_not():
    holder_ = sworn(HOLDERS[0])
    report = read_report(holder_["id"], "2025-03-20", 1)
    found, _, by_holder = evaluated([holder_], [report], LATE)
    (finding_,) = found
    page = render.render_officeholder(
        holder_,
        [report],
        META,
        striker,
        0,
        LATE,
        0,
        [SIGNAL],
        found,
        {SIGNAL["id"]: by_holder[holder_["id"]]},
    )
    fired = between(page, "<h2>Signals that fired", "<h2>Signals that did not fire")
    assert 'id="signal-stock-act-ptr-after-deadline"' in fired and 'id="finding-1"' in fired
    assert render.esc(finding_["description"]) in fired
    assert render.esc(render.NOT_A_DETERMINATION) in fired
    assert f"python tools/rebuild.py {finding_['id']}" in fired
    assert 'href="../signals/stock-act-ptr-after-deadline/v1.html"' in fired
    assert '<td class="idx">2025-02-11</td>' in fired and "30 days after notice" in fired
    assert '<td class="idx">37</td>' in fired, "the days after, from the deadline to the index date"
    assert 'href="#report-1"' in fired, "the Finding links to its report's rows, as filed"
    assert "and fired on it, shown below" in fired
    quiet = page[page.index("<h2>Signals that did not fire") :]
    assert "None: the one signal defined in this build fired, above." in quiet
    assert 'fired on 1 report, <a href="#signals">below</a>' in page
    assert frame.check_page(page) is None
    assert verdict_words(page) == []


def test_a_quiet_signal_says_which_silence_it_is():
    on_time = [LATE[1]]
    cases = {
        "for none of them does the Clerk's index date the report later than the deadline the "
        "rule sets from the dates the report prints": (sworn(HOLDERS[0]), True, on_time),
        "1 row was not evaluated: 1 dated before 2025-03-05, the swearing-in the roster records "
        "for the 119th Congress, which does not say whether this officeholder served before "
        "it.": (
            sworn(HOLDERS[0], "2025-03-05"),
            True,
            [LATE[0]],
        ),
        "1 report is fetched and not read: scanned paper": (sworn(HOLDERS[0]), False, []),
    }
    for expected, (holder_, read, rows) in cases.items():
        report = read_report(holder_["id"], "2025-03-20", 1, read)
        found, _, by_holder = evaluated([holder_], [report], rows)
        assert found == []
        page = render.render_officeholder(
            holder_,
            [report],
            META,
            striker,
            0,
            rows,
            0,
            [SIGNAL],
            found,
            {SIGNAL["id"]: by_holder[holder_["id"]]},
        )
        fired = between(page, "<h2>Signals that fired", "<h2>Signals that did not fire")
        quiet = page[page.index("<h2>Signals that did not fire") :]
        assert "None, on the Signals defined in this build." in fired, expected
        assert 'id="signal-stock-act-ptr-after-deadline"' in quiet, expected
        assert render.esc(expected) in quiet, expected
        assert render.esc(render.QUIET_NOT_A_DETERMINATION) in quiet, "silence is no certificate"
        assert "did not fire: " in page and "on or before its deadline" not in page
    nothing = render.render_officeholder(
        sworn(HOLDERS[1]), [], META, striker, 0, [], 0, [SIGNAL], [], {SIGNAL["id"]: []}
    )
    assert "so there was nothing to evaluate" in nothing
    assert "not a statement that no report was due" in nothing


def test_no_signal_defined_keeps_the_founding_words():
    page = render.render_officeholder(HOLDERS[0], FILINGS[:1], META, striker, 0, [])
    assert "None. No signal is defined in this build." in page
    assert "<b>none defined</b> · so none can fire, for anyone." in page


def test_the_signal_page_lists_people_in_seat_order_and_passes_every_page_gate():
    holders = [sworn(HOLDERS[1]), sworn(HOLDERS[0])]
    for h in holders:
        h["sworn_at"] = "2025-01-03"
    reports = [
        read_report(holders[0]["id"], "2025-03-20", 7),
        read_report(holders[1]["id"], "2025-03-20", 1),
    ]
    rows = [dict(r, filing_id="fl:house-clerk:P:7", officeholder_id=holders[0]["id"]) for r in LATE]
    for n, r in enumerate(rows, 1):
        r["id"] = f"tx:house-clerk:7:{n:03d}"
    found, outcomes, _ = evaluated(holders, reports, rows + LATE)
    summary = signal_run.run_record(SIGNAL["id"], "c" * 64, outcomes)[0]
    page = render.render_signal_page(SIGNAL, summary, found, holders, META)
    assert ranking.check_summary(page) == []
    assert frame.check_page(page) is None
    assert verdict_words(page) == []
    table = between(page, '<table id="fired"', "</table>")
    assert table.index('data-seat="AK00"') < table.index('data-seat="AL01"'), "seat order"
    assert 'data-order="seat" data-lists="officeholders"' in table
    assert "no number stands beside a name" in table
    assert "<h2>What it does not say</h2>" in page and "Committee on Ethics" in page
    assert "python tools/rebuild.py &lt;finding-id&gt;" in page


def test_a_withdrawn_finding_is_said_as_a_withdrawal_never_as_a_finding():
    holder_ = sworn(HOLDERS[0])
    report = read_report(holder_["id"], "2025-03-20", 1)
    found, _, _ = evaluated([holder_], [report], LATE)
    (first,) = found
    note = "The Clerk's index re-dated the report 2025-02-01; a person checked it at the source."
    withdrawal = dict(
        first,
        id=first["id"] + ":c1",
        evidence=dict(first["evidence"], after=0, rows=[]),
        correction="source",
        notes=note,
    )
    ledger = [dict(first, superseded_by=withdrawal["id"]), withdrawal]
    on_time = [LATE[1]]
    _, outcomes, by_holder = evaluated([holder_], [report], on_time)
    page = render.render_officeholder(
        holder_,
        [report],
        META,
        striker,
        0,
        on_time,
        0,
        [SIGNAL],
        ledger,
        {SIGNAL["id"]: by_holder[holder_["id"]]},
    )
    fired = between(page, "<h2>Signals that fired", "<h2>Signals that did not fire")
    quiet = page[page.index("<h2>Signals that did not fire") :]
    assert "None, on the Signals defined in this build." in fired
    assert 'class="finding"' not in page, "a withdrawal is never drawn as a Finding"
    assert (
        f"the correction <code>{withdrawal['id']}</code>, written because the source changed, "
        "records that it does not fire there" in quiet
    )
    assert render.esc(note) in quiet and f"<code>{first['id']}</code>" in quiet
    one = "did not fire: for the one row it evaluated, the Clerk's index does not date the report"
    assert one in page
    assert "no longer" not in page.split("<h2>Signals that did not fire")[1].split("</section>")[0]
    summary = signal_run.run_record(SIGNAL["id"], "c" * 64, outcomes)[0]
    signal_page = render.render_signal_page(SIGNAL, summary, ledger, [holder_], META)
    assert "It fired on no report in this build." in signal_page
    assert "Findings it once produced and a correction withdrew" in signal_page


def test_a_corrected_finding_names_the_row_it_supersedes_and_is_drawn_once():
    holder_ = sworn(HOLDERS[0])
    report = read_report(holder_["id"], "2025-03-20", 1)
    found, _, by_holder = evaluated([holder_], [report], LATE)
    (first,) = found
    note = "The first reading printed the wrong notification date; corrected from the document."
    correction = dict(
        first,
        id=first["id"] + ":c1",
        correction="register",
        notes=note,
        fired_at="2026-10-01T00:00:00Z",
    )
    ledger = [dict(first, superseded_by=correction["id"]), correction]
    page = render.render_officeholder(
        holder_,
        [report],
        META,
        striker,
        0,
        LATE,
        0,
        [SIGNAL],
        ledger,
        {SIGNAL["id"]: by_holder[holder_["id"]]},
    )
    assert page.count('class="finding"') == 1, "the chain is drawn once, at its current row"
    assert (
        f"Corrected because the register erred: this row supersedes <code>{first['id']}</code>"
        in page
    )
    assert render.esc(note) in page
    assert f"python tools/rebuild.py {correction['id']}" in page


def test_the_landing_names_the_signal_and_links_its_page():
    holder_ = sworn(HOLDERS[0])
    report = read_report(holder_["id"], "2025-03-20", 1)
    found, outcomes, _ = evaluated([holder_], [report], LATE)
    summary = signal_run.run_record(SIGNAL["id"], "c" * 64, outcomes)[0]
    page = render.render_index(
        HOLDERS,
        OFFICES,
        FILINGS,
        RUN,
        META,
        striker,
        0,
        "https://x/rows",
        LATE,
        [(SIGNAL, summary)],
    )
    assert ranking.check_index(page) == []
    assert frame.check_page(page) is None
    assert 'href="signals/stock-act-ptr-after-deadline/v1.html"' in page
    assert "This build holds 1 signal" in page
    assert "signals defined, so 0 fired" not in page
    assert verdict_words(page) == []


def test_the_signal_page_counts_what_it_evaluated_and_who_it_cannot_reach():
    holder_ = sworn(HOLDERS[0])
    reports = [
        read_report(holder_["id"], "2025-03-20", 1),
        read_report(holder_["id"], "2025-04-01", 2),
    ]
    before = transaction(
        "fl:house-clerk:P:2", 1, transaction_date="2024-11-01", notified_date="2024-11-01"
    )
    before["filing_status"] = "New"
    paper = read_report("oh:us:house:a000003", "2025-05-01", 3, read=False)
    found, outcomes, _ = evaluated([holder_, sworn(HOLDERS[2])], reports + [paper], LATE + [before])
    summary = signal_run.run_record(SIGNAL["id"], "c" * 64, outcomes)[0]
    rejected = [
        {
            "reason": "surname matches a sitting member (Example, Ann, CA12) but ...",
            "source_row": {"filing_type": "P"},
        },
        {"reason": "no sitting member has this name; ...", "source_row": {"filing_type": "P"}},
        {"reason": "no sitting member has this name; ...", "source_row": {"filing_type": "O"}},
    ]
    reach = render.coverage(outcomes, rejected)
    assert reach == {
        "paper_only": 1,
        "some_paper": 0,
        "not_fetched": 0,
        "before_swearing_in": 1,
        "set_aside_held": 1,
        "set_aside_shut": 0,
        "set_aside_other": 1,
    }
    unfetched = render.coverage(outcomes, rejected, fetched=set())
    assert (unfetched["paper_only"], unfetched["not_fetched"]) == (0, 1), (
        "a report never fetched is not scanned paper (Seats D and E, third reading)"
    )
    page = render.render_signal_page(
        SIGNAL, summary, found, [holder_, HOLDERS[2]], META, outcomes, reach
    )
    record = between(page, '<section class="record">', "</section>")
    assert (
        "on 1 it evaluated at least one row, and it fired on 1 of those; on 1 it evaluated no row"
        in record
    )
    assert "<dt>1</dt><dd>officeholders whose transaction reports are all scanned paper" in record
    assert (
        "which it does not see: 1 under the surname of an officeholder the register holds"
    ) in record
    by_rows = render.coverage(
        outcomes,
        [dict(r, source_row=dict(r["source_row"], last="Alaska")) for r in rejected],
        [holder_],
    )
    assert (by_rows["set_aside_held"], by_rows["set_aside_other"]) == (2, 0), (
        "the split is read from the rows' names, never from the adapter's reasons"
    )
    assert "on or before its deadline" not in page
    assert ranking.check_summary(page) == [] and frame.check_page(page) is None
    landing = render.state_of_record(
        META,
        RUN,
        HOLDERS,
        FILINGS,
        OFFICES,
        1,
        "https://x",
        LATE,
        [(SIGNAL, summary)],
        {SIGNAL["id"]: reach},
    )
    assert (
        render.esc(render.coverage_sentence(reach)) in landing
        or render.coverage_sentence(reach) in landing
    )
    assert "Example" not in landing


def test_held_reports_at_the_seat_are_named_in_the_silence():
    text = render.which_quiet([], held_reports=12)
    assert text.endswith(
        "12 transaction reports at this seat under this surname are set aside, not attributed "
        "to this officeholder and not evaluated."
    )
    assert render.which_silence([], 12) == (
        "no transaction report is attributed; those at this seat are set aside"
    )


def test_an_earlier_versions_finding_stays_on_the_page_as_published():
    holder_ = sworn(HOLDERS[0])
    report = read_report(holder_["id"], "2025-03-20", 1)
    found, _, by_holder = evaluated([holder_], [report], LATE)
    v2 = dict(SIGNAL, id=SIGNAL["id"].replace(":v1", ":v2"), version=2)
    page = render.render_officeholder(
        holder_, [report], META, striker, 0, LATE, 0, [v2], found, {v2["id"]: []}, [SIGNAL, v2]
    )
    assert "Version 1, which version 2 replaced" in page
    assert page.count('class="finding"') == 1, "the version 1 Finding is still drawn"
    assert f"python tools/rebuild.py {found[0]['id']}" in page


def test_a_ledger_that_names_someone_the_rows_no_longer_hold_is_refused():
    finding_ = {"officeholder_id": "oh:us:house:gone", "superseded_by": None}
    assert render.unpaged_officeholders([finding_], HOLDERS) == ["oh:us:house:gone"]
    assert render.unpaged_officeholders([dict(finding_, superseded_by="x")], HOLDERS) == []


def test_the_footer_says_the_anchor_the_proof_holds(tmp_path):
    """The anchor is never sealed, so the pages read it from the proof, through the anchor
    tool's own reader: a build with no manifest says none, one with a manifest and no proof
    says the stamp is owed, and a confirmed proof names its block."""
    (tmp_path / "tools").mkdir()
    (tmp_path / "tools" / "anchor.py").write_bytes((ROOT / "tools" / "anchor.py").read_bytes())
    assert render.anchor_of(tmp_path, "0005-house-2025") == {"state": "none", "block": None}
    folder = tmp_path / "data" / "anchors"
    folder.mkdir(parents=True)
    manifest = b"0" * 64 + b"  data/example.ndjson\n"
    (folder / "0005-house-2025.manifest").write_bytes(manifest)
    (folder / "0005-house-2025.json").write_text(
        '{"build": "0005-house-2025", "built_at": "2026-09-23T14:13:28Z", "digest": "x"}\n'
    )
    owed = render.anchor_of(tmp_path, "0005-house-2025")
    assert owed == {"state": "owed", "block": None}
    words = {
        state: render.anchor_words({"anchor": {"state": state, "block": block}})
        for state, block in (("none", None), ("owed", None), ("pending", None), ("confirmed", 1))
    }
    assert "none yet" in words["none"]
    assert "the stamp is owed" in words["owed"] and "ANCHORS.md" in words["owed"]
    assert "awaiting a Bitcoin block" in words["pending"]
    assert "Bitcoin block 1," in words["confirmed"]
    confirmed = render.anchor_words({"anchor": {"state": "confirmed", "block": 915000}})
    assert "Bitcoin block 915,000, by OpenTimestamps" in confirmed
    assert "Anchor: none yet" in render.footer(META, home=True)


def departure(gone: dict, at: str = "2026-10-05T09:17:00Z") -> dict:
    return {
        "id": f"ch:not-listed:{gone['id']}:{at}",
        "row_id": gone["id"],
        "rows": "officeholders",
        "change": "not listed",
        "before": "2026-09-22T21:40:17Z",
        "capture": {
            "url": "https://clerk.house.gov/xml/lists/MemberData.xml",
            "retrieved_at": at,
            "content_hash": "0" * 64,
        },
        "build": "0006-house-2025",
        "frame": render.FRAME,
    }


def plain(page: str) -> str:
    return html.unescape(page)


def test_an_officeholder_the_roster_no_longer_lists_keeps_a_page_and_no_seat():
    """NEXT.md S.1b and the Council's reading of it. The register keeps every row it published
    about a Member who left, and their page, and says so; the page says the roster gives no
    reason and no date, links the capture, and says what stops. The index never shows them
    holding a seat: it names them at their seat as listed until a date, with a link, and
    lists them below the seats with the interval the change fell in."""
    gone = HOLDERS[0]
    filing_gone = dict(
        departure(gone, "2026-10-06T00:00:00Z"),
        id="ch:not-listed:x:2026-10-06T00:00:00Z",
        row_id=FILINGS[1]["id"],
        rows="filings",
    )
    changes = {gone["id"]: [departure(gone)], FILINGS[1]["id"]: [filing_gone]}
    render.KEPT["0" * 64] = "data/captures/sha256/" + "0" * 64 + ".xml"
    raw = render.render_index(HOLDERS, OFFICES, FILINGS, RUN, META, striker, changes=changes)
    page = plain(raw)
    seats, kept = page.split(
        "<h2>No longer listed on the Clerk's roster during the 119th Congress</h2>"
    )
    roll = seats.split("<h2>Every seat in the register</h2>")[1]
    ak00 = roll[roll.index('data-seat="AK00"') :].split("</tr>")[0]
    assert "Vacant on the Clerk's roster read 2026-09-22" in ak00
    assert (
        "Last listed here on the roster read the register built from, 2026-09-22, and not on "
        "the one read 2026-10-05" in ak00
    ), "reachable from the seat, dated both ways, and by the read a build was made from"
    assert f'href="officeholders/{render.slug(gone["id"])}.html"' in ak00
    assert render.slug(gone["id"]) in kept
    assert '<td class="idx">2026-09-22</td><td class="idx">2026-10-05</td>' in kept
    assert "the roster does not say when or why a person leaves a seat" in kept
    assert "holds only Members the roster stopped listing after the register first read it" in kept
    assert "SUBJECTS.md#1-the-rule" in kept
    assert 'href="#not-listed"' in page, "the door says where they are"
    assert ranking.check_index(raw) == []
    assert frame.check_page(raw) is None
    raw_own = render.render_officeholder(gone, FILINGS[:2], META, striker, changes=changes)
    own = plain(raw_own)
    assert "The Clerk's roster read 2026-10-05 no longer lists this officeholder" in own
    assert "; recorded in build 0006-house-2025)" in own, "the build at the sentence's end"
    assert "search it for AK00" in own, "a check a reader can take on a phone"
    assert "the register kept no copy of that one" in own, "the earlier read, said as not kept"
    assert "The roster does not say when or why a person leaves a seat" in own
    assert (
        "A report the Clerk's index dates after 2026-09-22, the last roster read the register "
        "built from that listed them, is not attributed to them while the roster does not list "
        "them" in own
    )
    assert "the last roster read the register built from before it, on 2026-09-22" in own
    for words in ("the last roster the register read", "and cannot be", "by anyone"):
        assert words not in own, words
    assert "Every row on this page was published while the roster listed them" in own
    assert "Everything on this page" not in own and "the capture that shows it" not in own
    assert render.HOUSE_FINDER in own and render.CLERK_SITE in own, "the next step"
    assert "data/captures/sha256/" + "0" * 64 + ".xml" in own, "the capture that shows it, kept"
    assert "No longer in the Clerk's index read 2026-10-06" in own
    assert "which does not say why" in own
    assert frame.check_page(raw_own) is None
    other = plain(
        render.render_officeholder(HOLDERS[1], FILINGS[2:], META, striker, changes=changes)
    )
    assert "no longer lists this officeholder" not in other


def test_a_member_listed_again_shows_both_reads():
    """Vow V: the reader who returns sees what the record was and what it is now (Seat G)."""
    gone = HOLDERS[1]
    back = dict(
        departure(gone, "2026-11-02T09:17:00Z"),
        id=f"ch:listed-again:{gone['id']}:2026-11-02T09:17:00Z",
        change="listed again",
    )
    changes = {gone["id"]: [departure(gone), back]}
    own = plain(render.render_officeholder(gone, FILINGS[2:], META, striker, changes=changes))
    masthead, checks = between(own, "<header", "</header>"), between(own, "<dt>Identity", "</dd>")
    assert "The Clerk's roster read 2026-10-05 did not list them" in checks
    assert "The Clerk's roster read 2026-11-02 lists them again" in checks
    assert "did not list" not in masthead, (
        "a lapse the roster ended is said where the page says what it can check, never in "
        "the masthead, where one the Clerk may have made would read as a departure"
    )
    assert "no longer lists this officeholder" not in own


def test_the_landing_counts_departures_and_changes_and_no_ones_rows():
    """The Council's reading of S.1b (Seats A, D and E): a count of one Member's filings or
    transactions beside their leaving is a count about a person, whatever it is filed under."""
    gone = HOLDERS[0]
    changes = {gone["id"]: [departure(gone)]}
    section = plain(
        render.state_of_record(
            META, RUN, HOLDERS, FILINGS, OFFICES, 1, "https://x/rows", changes=changes, seated=2
        )
    )
    assert (
        "Members of the 119th Congress the Clerk's roster stopped listing during that Congress "
        "keep their pages" in section
    )
    assert "<dt>1</dt><dd>Member" not in section, (
        "a count of one departure is a count about one person (Seats B and F, third reading)"
    )
    assert "None is about a person" not in section and "none is a measure of anyone" in section
    assert "<dt>1</dt><dd>change a later read of the Clerk's roster, index or documents" in section
    assert "except a party, which no page shows" in section
    assert "a refresh that failed published nothing" in section
    assert "When this build was made, the register read" in section
    assert "or when the maintainer published a correction" in section
    assert "every Monday at 09:17 UTC" in section
    assert "2 filled and 2 vacant" in section, "a Member the roster no longer lists fills no seat"
    assert "with the copy of the roster or the index the register kept" in section, (
        "a read of the roster cites bytes the register keeps"
    )
    replaced = {
        "fl:house-clerk:P:1": [
            {
                "id": "ch:replaced:fl:house-clerk:P:1:2026-10-05T00:00:00Z",
                "row_id": "fl:house-clerk:P:1",
                "rows": "filings",
                "change": "replaced",
                "was": "a" * 64,
                "now": "b" * 64,
                "capture": {"url": "https://x/1.pdf", "retrieved_at": "2026-10-05T00:00:00Z"},
            }
        ]
    }
    with_doc = plain(
        render.state_of_record(
            META, RUN, HOLDERS, FILINGS, OFFICES, 1, "https://x/rows", changes=replaced, seated=2
        )
    )
    assert "both files' fingerprints, since the register keeps no filed document" in with_doc, (
        "a read of a document keeps neither file, and the line says so (Seats F and G)"
    )


def test_a_closed_year_says_whose_seats_these_are_and_counts_the_rows_it_holds():
    """A closed year: the Congress ended, the seats are its own as last read, and the
    counts are the register's, not the closed build's zeros (Seats A, B, D, E, F, G)."""
    closed = dict(
        RUN,
        counts=dict.fromkeys(("seats", "filled", "vacant", "filings"), 0),
        congress={
            "filing_year": 119,
            "roster": 120,
            "closed": True,
            "last_roster_read": "2026-12-28T09:17:00Z",
        },
        sources=[s for s in RUN["sources"] if s["name"] != "MemberData.xml"],
    )
    section = plain(
        render.state_of_record(META, closed, HOLDERS, FILINGS, OFFICES, 0, "https://x/r")
    )
    assert "<dt>0</dt><dd>seats in the House" not in section
    assert f"<dt>{len(OFFICES)}</dt><dd>seats in the House in the 119th Congress" in section
    assert f"<dt>{len(FILINGS)}</dt><dd>index rows the register holds" in section
    assert "the 119th Congress's roster was last read 2026-12-28" in section
    page = plain(render.render_index(HOLDERS, OFFICES, FILINGS, closed, META, striker))
    assert "terms ended at noon on 3 January 2027 (U.S. Const. amend. XX, section 1)" in page
    assert "Members of the 120th Congress are not in this build" in page
    assert "who holds each seat now" in page and "who represents you now" not in page
    assert "Find who represented you in the 119th Congress" in page
    assert "listed when the register last read it for that Congress, 2026-12-28" in page
    assert "Find your representative<" not in page
    own = plain(render.render_officeholder(HOLDERS[0], FILINGS[:2], META, striker))
    assert "The 119th Congress's terms ended at noon on 3 January 2027" in own
    assert "this Congress" not in page + own


def test_a_finding_whose_report_a_later_capture_shows_otherwise_says_so_beside_it():
    """Seat B's lawyer's letter: the Finding stands as produced, and the page says, beside it,
    what the index now shows and that a person's correction is the way it changes."""
    holder_ = sworn(HOLDERS[0])
    report = read_report(holder_["id"], "2025-03-20", 1)
    found, _, by_holder = evaluated([holder_], [report], LATE)
    moved = {
        "id": f"ch:read-otherwise:{report['id']}:filed_at:2026-10-05T09:17:01Z",
        "row_id": report["id"],
        "rows": "filings",
        "change": "read otherwise",
        "field": "filed_at",
        "was": "2025-03-20",
        "now": "2025-03-19",
        "capture": {
            "url": "https://x/2025FD.zip",
            "retrieved_at": "2026-10-05T09:17:01Z",
            "content_hash": "1" * 64,
        },
        "frame": render.FRAME,
    }
    page = render.render_officeholder(
        holder_,
        [report],
        META,
        striker,
        0,
        LATE,
        0,
        [SIGNAL],
        found,
        {SIGNAL["id"]: by_holder[holder_["id"]]},
        changes={report["id"]: [moved]},
    )
    fired = plain(between(page, "<h2>Signals that fired", "<h2>Signals that did not fire"))
    assert "The Clerk's index read 2026-10-05 gives the date filed as 2025-03-19" in fired
    assert "This Finding stands as produced" in fired and "BYLAWS.md §5</a> and" in fired
    signal_page = render.render_signal_page(
        SIGNAL,
        signal_run.run_record(SIGNAL["id"], "c" * 64, by_holder[holder_["id"]])[0],
        found,
        [holder_],
        META,
        changes={report["id"]: [moved], holder_["id"]: [departure(holder_)]},
    )
    assert (
        "(the index read 2026-10-05 gives one of its facts otherwise; the Clerk gives no reason)"
        in signal_page
    ), "dated, so a last build does not speak of the reader's own day (Seat G, R3-6)"
    assert render.BYLAWS_6 in page, "the route to a correction, linked (Seats A and B)"
    assert "not on the Clerk's roster read 2026-10-05, which gives no reason" in plain(signal_page)
    assert "says nothing about any group of them" in signal_page
    assert ranking.check_summary(signal_page) == [] and frame.check_page(signal_page) is None


def test_a_row_under_another_given_name_at_a_departed_seat_is_said_apart():
    """The Council's fourth reading of S.1b (Seats B, D and E): a row at the seat of a Member
    the roster no longer lists, under their surname but another given name, was classed by its
    date alone and offered for a decision, which framed a relative's filing as the Member's.
    The register says the given names differ and that it has not read the document. And a
    document kind is that Member's only where the register set the row aside while the roster
    still listed them; the header check of a successor at the seat is about the successor
    (Seat D)."""
    gone = holder("PA08", "Pat Departed", "d000001")
    rows = [
        {
            "reason": build_reasons.DEPARTED_OTHER_NAME + " (Departed, Pat, PA08; last listed "
            "2026-09-28)",
            "source_row": {
                "state_dst": "PA08",
                "last": "Departed",
                "first": "Casey",
                "filing_type": "C",
                "filing_date": "9/15/2026",
            },
        },
        {
            "reason": "surname matches a sitting member (Successor, Sam, PA08) but the given "
            "names differ; the index dates the filing 2026-09-26, before the swearing-in the "
            "roster records for the 119th Congress (2026-10-10); a human decides this one",
            "source_row": {
                "state_dst": "PA08",
                "last": "Departed",
                "first": "Casey",
                "filing_type": "C",
                "filing_date": "9/26/2026",
            },
        },
    ]
    counted = render.held_by_holder(rows, [gone], {gone["id"]: "2026-09-28"})
    assert counted == {gone["id"]: {"left_other_name": 1, "left_open": 1}}, counted
    said = render.aside_sentence(counted[gone["id"]], "2026-09-28")
    assert "1 under another given name, whose document the register has not read" in said
    assert "before the swearing-in" not in said, "the successor's own check is not about them"
    assert "2 rows of the index at this seat carry this surname and are set aside" in said


def test_a_listed_holders_row_is_said_by_the_date_before_their_swearing_in():
    """Seat F on the fourth reading (N31): a row at a seat whose surname two holders share,
    carrying neither given name, counted on the successor's page as one whose document could
    not confirm the filer, though the index dates it long before they were sworn in."""
    successor = holder("PA08", "Sam Departed", "s000001", sworn="2026-10-10")
    row = {
        "reason": "surname matches a sitting member (Departed, Sam, PA08) but the given names "
        "differ; the document carries no Filing ID line and cannot confirm the filer; a human "
        "decides this one",
        "source_row": {
            "state_dst": "PA08",
            "last": "Departed",
            "first": "Casey",
            "filing_type": "P",
            "filing_date": "4/14/2025",
        },
    }
    assert render.held_by_holder([row], [successor]) == {successor["id"]: {"before_sworn": 1}}


def test_a_held_report_counts_only_for_the_holder_whose_given_name_it_carries():
    """Seat A on the fourth reading (A3-1's residue): the count of set-aside transaction
    reports was keyed by surname alone, so a successor's page said a report the predecessor
    filed under their own given name was set aside at the successor's seat."""
    departed = holder("PA08", "Pat Departed", "d000002")
    successor = holder("PA08", "Sam Departed", "s000002", sworn="2026-10-10")
    rows = [
        {
            "reason": "held",
            "source_row": {
                "state_dst": "PA08",
                "last": "Departed",
                "first": "Pat",
                "filing_type": "P",
            },
        }
    ]
    assert render.held_reports_by_holder(rows, [departed, successor]) == {departed["id"]: 1}


def test_two_holders_of_one_seat_each_count_only_the_rows_under_their_own_surname():
    """Carrying a Member the roster no longer lists puts two holders at one seat. Found by
    the Council's reading of S.1b: counted by seat, whichever holder sorted last took the
    other's set-aside rows onto their page."""
    rows = [
        {
            "reason": "surname matches a sitting member (Departed, Pat, PA08) but the given "
            "names differ; the document carries no Filing ID line and cannot confirm the "
            "filer; a human decides this one",
            "source_row": {
                "state_dst": "PA08",
                "last": "Departed",
                "first": "P.",
                "filing_type": "P",
            },
        },
        {
            "reason": "no sitting member has this name; the row is a candidate or a former member",
            "source_row": {
                "state_dst": "PA08",
                "last": "Successor",
                "first": "S.",
                "filing_type": "T",
            },
        },
    ]
    for first, second in (("a999999", "z999999"), ("z999999", "a999999")):
        departed = holder("PA08", "Pat Departed", first)
        successor = holder("PA08", "Sam Successor", second)
        both = [departed, successor]
        counted = render.held_by_holder(rows, both)
        assert counted == {
            departed["id"]: {"no_filing_id": 1},
            successor["id"]: {"other": 1},
        }, (first, second)
        assert render.held_reports_by_holder(rows, both) == {departed["id"]: 1}
        assert render.held_rows_at_own_seat(rows, both) == 1


def test_a_departed_members_rows_are_said_as_decidable_or_not_and_never_mislabelled():
    """The Council's second reading of S.1b (Seats A, D, E): after a departure the page called
    the Member's set-aside rows documents that "print another seat or another Filing ID", and
    promised a decision on rows no decision can attribute."""
    gone = HOLDERS[0]
    no_sitting = "no sitting member has this name; the row is a candidate or a former member"
    rows = [
        {
            "reason": no_sitting,
            "source_row": {"state_dst": "AK00", "last": "Alaska", "filing_date": "9/1/2026"},
        },
        {
            "reason": no_sitting,
            "source_row": {"state_dst": "AK00", "last": "Alaska", "filing_date": "11/2/2026"},
        },
        {
            "reason": "the maintainer's recorded decision names an officeholder the roster stopped "
            "listing, for a filing the index dates after the last roster read that listed "
            "them; the register cannot show them in office after that read, and under "
            "SUBJECTS.md §1 it enters no new filing for an officeholder after their term "
            "(oh:us:house:a000001; dated 2026-11-09; last listed 2026-09-22)",
            "source_row": {"state_dst": "AK00", "last": "Alaska", "filing_date": "11/9/2026"},
        },
    ]
    counted = render.held_by_holder(rows, HOLDERS, {gone["id"]: "2026-09-22"})
    assert counted == {gone["id"]: {"left_open": 1, "left_closed": 1, "after_term": 1}}
    said = plain(render.aside_sentence(counted[gone["id"]], "2026-09-22"))
    assert (
        "1 is set aside for the maintainer to decide by hand: 1 dated on or before 2026-09-22, "
        "the last roster read the register built from that listed them" in said
    )
    assert "2 are not attributed here" in said
    for words in ("another seat or another Filing ID", "since", "this name", "by anyone"):
        assert words not in said, words
    assert render.held_by_holder(rows, HOLDERS) == {gone["id"]: {"other": 2, "after_term": 1}}, (
        "without a departure the reason stands as the adapter gave it"
    )


def test_rows_set_aside_while_a_member_sat_keep_what_their_documents_printed():
    """The Council's third reading of S.1b (all seven seats): once the roster stops listing a
    Member, a row set aside while it listed them, whose document prints a candidate's status or
    carries no Filing ID line, must not read as one the index listed under their name since
    they left, or as one the join once attributed. It keeps what its document printed. A row
    at the seat under the surname whose reason names a namesake elsewhere (Seat D) is theirs,
    by date. And where a successor at the seat bears the surname (Seat A), a row counts for
    the holder whose given name it carries."""
    gone = HOLDERS[0]
    kept = "the roster no longer lists the member at this seat whose surname the row carries"
    while_sat = kept + "; while it did, the row was set aside because surname matches a sitting "
    rows = [
        {
            "reason": while_sat + "member (Alaska, Ann, AK00) but the given names differ; the "
            "document prints Status 'Congressional Candidate' for the filer named 'Al Alaska' at "
            "AK00, not Member; the header does not attribute the row to the seat's member; a "
            "human decides this one (Alaska, Ann, AK00; last listed 2026-09-22)",
            "source_row": {
                "state_dst": "AK00",
                "last": "Alaska",
                "first": "Al",
                "filing_date": "4/14/2025",
            },
        },
        {
            "reason": while_sat + "member (Alaska, Ann, AK00) but the given names differ; the "
            "document carries no Filing ID line (scanned paper, or a form that prints none) and "
            "cannot confirm the filer; a human decides this one (Alaska, Ann, AK00; last listed "
            "2026-09-22)",
            "source_row": {
                "state_dst": "AK00",
                "last": "Alaska",
                "first": "Example",
                "filing_date": "5/1/2025",
            },
        },
        {
            "reason": "surname matches a sitting member (Alaska, Ned, TX09) but the given names "
            "differ; a human decides this one",
            "source_row": {
                "state_dst": "AK00",
                "last": "Alaska",
                "first": "Example",
                "filing_date": "9/1/2026",
            },
        },
    ]
    counted = render.held_by_holder(rows, HOLDERS, {gone["id"]: "2026-09-22"})
    assert counted == {gone["id"]: {"status": 1, "no_filing_id": 1, "left_open": 1}}
    said = plain(render.aside_sentence(counted[gone["id"]], "2026-09-22"))
    assert "1 whose document prints a filer status other than Member" in said
    for words in ("since", "this name", "no longer attributes", "by anyone"):
        assert words not in said, words
    successor = dict(gone, id="oh:us:house:z000001", legal_name="Al Alaska")
    successor["common_name"] = "Alaska, Al"
    both = [gone, successor]
    counted = render.held_by_holder(rows, both, {gone["id"]: "2026-09-22"})
    assert counted[successor["id"]] == {"status": 1}, "the row under his given name is his"
    assert counted[gone["id"]] == {"no_filing_id": 1, "left_open": 1}


def test_a_seat_whose_member_was_sworn_late_says_what_the_register_cannot_show():
    """Seat E: the register holds no one who held a seat before the Member it first read there,
    and a page should say so where it matters, whether or not anyone has left since."""
    late = [dict(HOLDERS[0], sworn_at="2025-06-10")] + HOLDERS[1:]
    page = plain(render.render_index(late, OFFICES, FILINGS, RUN, META, striker))
    roll = between(page, "<h2>Every seat in the register</h2>", "</table>")
    ak00 = roll[roll.index('data-seat="AK00"') :].split("</tr>")[0]
    assert (
        "Sworn in 2025-06-10; the register holds no earlier holder of this seat in that Congress, "
        "and any filing by one is among the rows set aside" in ak00
    ), "no 'filing under another name', which reads in translation as an alias (Seat F)"
    al02 = roll[roll.index('data-seat="AL02"') :].split("</tr>")[0]
    assert "The register holds no Member of this seat in that Congress" in al02, (
        "a seat vacant since before the first read says so too (Seat E)"
    )
    on_time = roll[roll.index('data-seat="PR00"') :].split("</tr>")[0]
    assert "Sworn in" not in on_time, "a seat whose holder was sworn with the Congress says nothing"
    al01 = roll[roll.index('data-seat="AL01"') :].split("</tr>")[0]
    assert "Sworn in 2026-09-01" in al01, "and every seat sworn after the terms began says so"
    assert "a Member of the 119th Congress who left before then is not in it" in roll, (
        "said on every build, not only once someone has left"
    )
    assert (
        ranking.check_index(render.render_index(late, OFFICES, FILINGS, RUN, META, striker)) == []
    )


def test_a_late_sworn_quiet_page_says_the_date_and_asks_nothing_of_the_member():
    """Seat A on the fourth reading (A4-1): a Member the roster records as sworn after the
    terms began got a quiet page saying the register "does not say whether a report was due
    from them", where a Member sworn with the Congress got the register's own limit. The same
    facts, and one page raised an obligation, on a register whose one Signal is about reports
    the index dates late."""
    late = render.quiet_words("2025-12-04")
    on_time = render.quiet_words("2025-01-03")
    assert "2025-12-04" in late and "after the Congress's terms began" in late
    assert "due" not in late and "owed" not in late, "no page asks what a Member may have owed"
    assert on_time.endswith("not a statement about what was filed."), (
        "and a Member sworn with the Congress gets the register's own limit"
    )
    assert late.endswith("this is not a statement about what was filed.")


def test_a_name_the_roster_restates_is_shown_and_a_party_is_not():
    """Seats A and F: a later roster that gives a name or a swearing-in date otherwise was
    recorded and shown on no page, though the landing said every change is beside its row."""
    holder_ = HOLDERS[1]

    def restated(field, was, now):
        return dict(
            departure(holder_),
            id=f"ch:read-otherwise:{holder_['id']}:{field}:2026-10-05T09:17:00Z",
            change="read otherwise",
            field=field,
            was=was,
            now=now,
        )

    changes = {
        holder_["id"]: [
            restated("sworn_at", "2025-01-03", "2025-01-06"),
            restated("party", "I", "D"),
        ]
    }
    own = plain(render.render_officeholder(holder_, FILINGS[2:], META, striker, changes=changes))
    identity = between(own, "<dt>Identity", "</dd>")
    assert "gives the swearing-in date as 2025-01-06; the register published 2025-01-03" in identity
    assert "party" not in own.lower().replace("third party", "")


def test_the_footer_dates_the_reads_and_leaves_the_time_to_the_anchor():
    """Seat G: "sealed" beside the time of the latest read said what the time is not."""
    foot = render.footer(dict(META, built_at="2026-10-05T09:17:33Z"), home=True)
    assert "from the sources as read up to <code>2026-10-05T09:17:33Z</code>" in foot
    assert "its anchor, a timestamp proof, fixes when it provably existed" in foot
    assert ", sealed <code>" not in foot


# ---- the Council's third reading of S.1b: corrections, shown where they moved a row --------


def corrected(row_id: str, rows: str, field: str, was, now, at="2026-10-06T12:00:00Z", **more):
    return {
        "id": f"ch:corrected:{row_id}:{field}:{at}",
        "row_id": row_id,
        "rows": rows,
        "change": "corrected",
        "field": field,
        "was": was,
        "now": now,
        "kind": "register",
        "because": "The Clerk's document prints another filer; the register joined it wrongly.",
        "decided_by": "the maintainer",
        "decided_at": at,
        "capture": {
            "url": "https://disclosures-clerk.house.gov/public_disc/ptr-pdfs/2025/1.pdf",
            "retrieved_at": "2026-10-06T11:00:00Z",
            "content_hash": "d" * 64,
        },
        "frame": render.FRAME,
        **more,
    }


def test_a_moved_report_is_said_on_the_page_it_left_and_the_page_it_reached():
    """Seats A, B, D, E, F and G on the third reading: a correction that moves a report's
    attribution left no trace on the page it left, called the row "name" on the page it
    reached, printed the other officeholder's id, and dropped the Finding's chain between the
    two pages. Each page now says what happened, in words and links."""
    left, reached = sworn(HOLDERS[0]), sworn(HOLDERS[1])
    report = read_report(left["id"], "2025-03-20", 1)
    found, _, by_holder = evaluated([left], [report], LATE)
    (first,) = found
    head = dict(first, id=first["id"] + ":c1", officeholder_id=reached["id"], correction="register")
    head["notes"] = "The register joined the report wrongly."
    ledger = [dict(first, superseded_by=head["id"]), head]
    moved = dict(report, officeholder_id=reached["id"])
    history = [
        corrected(report["id"], "filings", "officeholder_id", left["id"], reached["id"]),
        corrected(
            report["id"], "filings", "office_id", "of:us:house-ak00:2025", "of:us:house-al01:2025"
        ),
    ]
    changes = {report["id"]: history}
    render.NAMES.update({left["id"]: left["legal_name"], reached["id"]: reached["legal_name"]})
    render.LEDGER[:] = ledger
    try:
        page = plain(
            render.render_officeholder(
                reached,
                [moved],
                META,
                striker,
                0,
                [dict(t, officeholder_id=reached["id"]) for t in LATE],
                0,
                [SIGNAL],
                [head],
                {SIGNAL["id"]: by_holder[left["id"]]},
                changes=changes,
            )
        )
        assert '<td class="code">correction</td>' in page, "never 'name' for a moved row"
        assert "the register had attributed this report to" in page
        assert (
            f'{render.slug(left["id"])}.html" data-cross="correction">{left["legal_name"]}</a>'
            in page
        )
        assert left["id"] not in page.replace(render.slug(left["id"]), ""), "no raw id"
        assert "the office was" not in page, "the office moves with its attribution, one note"
        assert (
            "Attributed to this officeholder by the maintainer's correction of 2026-10-06" in page
        )
        assert (
            f'on the page of <a href="{render.slug(left["id"])}.html" data-cross="correction">'
            in page
        ), "the Finding's chain names the page it came from"
        assert "For 1 of them the maintainer recorded a correction" in page
        assert "A later read of the Clerk's index shows" not in page, "a correction is not a read"
        gone = plain(
            render.render_officeholder(
                left,
                [],
                META,
                striker,
                0,
                [],
                0,
                [SIGNAL],
                [dict(first, superseded_by=head["id"])],
                {SIGNAL["id"]: []},
                changes=changes,
                moved_away=[(moved, history[0])],
            )
        )
        assert (
            "1 report the register published on this page is attributed to another officeholder "
            "by the maintainer's recorded correction" in gone
        )
        cross = f'{render.slug(reached["id"])}.html" data-cross="correction">'
        assert f"{cross}{reached['legal_name']}</a>" in gone
        assert f"The Finding <code>{first['id']}</code>" in gone and "is superseded" in gone
        assert frame.check_page(gone) is None and verdict_words(gone) == []
        signal_page = render.render_signal_page(
            SIGNAL,
            signal_run.run_record(SIGNAL["id"], "c" * 64, [])[0],
            ledger,
            [left, reached],
            META,
            changes=changes,
        )
        assert "(attributed here by the maintainer's correction of 2026-10-06)" in signal_page
    finally:
        render.LEDGER.clear()


def test_a_value_that_stands_is_shown_with_the_read_it_answers_and_a_later_read_again():
    """Seats B, F and G on the third reading: a decision that the published date stands made
    the note beside the Finding, and the Signal page's mark, vanish; and a later read the
    decision never saw vanished too. A decision answers the reads before it."""
    holder_ = sworn(HOLDERS[0])
    report = read_report(holder_["id"], "2025-03-20", 1)
    found, _, by_holder = evaluated([holder_], [report], LATE)

    def read(now: str, at: str) -> dict:
        return {
            "id": f"ch:read-otherwise:{report['id']}:filed_at:{at}",
            "row_id": report["id"],
            "rows": "filings",
            "change": "read otherwise",
            "field": "filed_at",
            "was": "2025-03-20",
            "now": now,
            "capture": {
                "url": "https://x/2025FD.zip",
                "retrieved_at": at,
                "content_hash": "1" * 64,
            },
            "frame": render.FRAME,
        }

    stands = corrected(report["id"], "filings", "filed_at", "2025-03-20", "2025-03-20")
    history = [read("2025-03-17", "2026-10-05T09:17:01Z"), stands]

    def pages(history: list[dict]) -> tuple[str, str]:
        changes = {report["id"]: history}
        page = plain(
            render.render_officeholder(
                holder_,
                [report],
                META,
                striker,
                0,
                LATE,
                0,
                [SIGNAL],
                found,
                {SIGNAL["id"]: by_holder[holder_["id"]]},
                changes=changes,
            )
        )
        signal_page = render.render_signal_page(
            SIGNAL,
            signal_run.run_record(SIGNAL["id"], "c" * 64, by_holder[holder_["id"]])[0],
            found,
            [holder_],
            META,
            changes=changes,
        )
        return page, signal_page

    page, signal_page = pages(history)
    fired = between(page, "<h2>Signals that fired", "<h2>Signals that did not fire")
    assert "The Clerk's index read 2026-10-05 gives the date filed as 2025-03-17" in fired
    assert "the maintainer recorded on 2026-10-06 that the published value stands" in fired
    assert (
        "(the index read 2026-10-05 gives one of its facts otherwise; the Clerk gives no reason; "
        "the maintainer recorded on 2026-10-06 that the published value stands)" in signal_page
    )
    assert "keeps it until the maintainer decides" not in page, "decided, and said so"
    page, signal_page = pages([*history, read("2025-03-16", "2026-10-12T09:17:01Z")])
    fired = between(page, "<h2>Signals that fired", "<h2>Signals that did not fire")
    assert "The Clerk's index read 2026-10-12 gives the date filed as 2025-03-16" in fired
    assert "published value stands" not in fired, "a decision never answers a later read"
    assert "(the index read 2026-10-12 gives one of its facts otherwise" in signal_page


def test_a_replaced_document_says_which_rows_differ_and_that_neither_file_is_kept():
    """Seats B, F and G on the third reading: the note beside a replaced report implied the
    register kept the file its rows came from; it keeps neither, and it says which rows read
    otherwise, by row and fact, never what they say."""
    note = plain(
        render.change_notes(
            [
                {
                    "id": "ch:replaced:fl:house-clerk:P:1:2026-10-05T09:17:02Z",
                    "row_id": "fl:house-clerk:P:1",
                    "rows": "filings",
                    "change": "replaced",
                    "field": "source.content_hash",
                    "was": "a" * 64,
                    "now": "b" * 64,
                    "differs": [
                        {"row": "tx:house-clerk:1:002", "fields": ["notes"]},
                        {"row": "tx:house-clerk:1:003", "only_in": "this file"},
                    ],
                    "capture": {
                        "url": "https://disclosures-clerk.house.gov/public_disc/ptr-pdfs/2025/1.pdf",
                        "retrieved_at": "2026-10-05T09:17:02Z",
                        "content_hash": "b" * 64,
                    },
                    "frame": render.FRAME,
                }
            ]
        )
    )
    assert "was a different file from the one the register first read" in note
    assert (
        "1 of the rows the register published read otherwise there, in the notes the register "
        "wrote from the report's lines" in note
    )
    assert "it lists 1 row the first file does not" in note
    assert "The register keeps neither file" in note and "the copy the register kept" not in note


def test_the_landing_counts_the_rows_no_decision_attributes_apart():
    """Seats A, D and E on the third reading: the landing said every held row waited for the
    maintainer to decide by hand, while a departed Member's page said one could not be
    attributed. The landing counts them as the pages class them."""
    gone = HOLDERS[0]
    rows = [
        {
            "reason": "the roster no longer lists the member at this seat whose surname the row "
            "carries, and the index dates the filing after the last roster read the register "
            "built from that listed them (Alaska, Example, AK00; last listed 2026-09-22)",
            "source_row": {"state_dst": "AK00", "last": "Alaska", "filing_date": "11/2/2026"},
        },
        {
            "reason": "surname matches a sitting member (Alabama, Other, AL01) but the given "
            "names differ; a human decides this one",
            "source_row": {"state_dst": "AL01", "last": "Alabama", "filing_date": "5/1/2025"},
        },
    ]
    counts = render.set_aside_counts(rows, HOLDERS, {gone["id"]: "2026-09-22"})
    assert counts == {"waits": 1, "at_seat": 1, "shut": 1}
    section = plain(
        render.state_of_record(META, RUN, HOLDERS, FILINGS, OFFICES, counts, "https://x/rows")
    )
    assert "<dt>1</dt><dd>index rows set aside for the maintainer to decide by hand" in section
    assert "1 more is not attributed, because the register cannot show the officeholder" in section


# ---- the two page guards the fourth reading found unmeasured (Seat A, A4-9) -----------------


def test_a_closed_years_row_dated_after_the_terms_is_never_offered_for_a_decision():
    """Seat A on the fourth reading: `closed_after` could be taken out of UNDECIDABLE and the
    whole suite still passed. Such a row would read "set aside for the maintainer to decide by
    hand" again, though no decision can attribute it."""
    holder_row = holder("AK00", "Example Alaska", "a000001")
    rows = [
        {
            "reason": "the register closed the filing year; the index dates this row after those "
            "terms, and nothing attributes it (Alaska, Example, AK00)",
            "source_row": {
                "state_dst": "AK00",
                "last": "Alaska",
                "first": "Example",
                "filing_type": "P",
                "filing_date": "1/8/2027",
            },
        }
    ]
    counted = render.held_by_holder(rows, [holder_row])
    assert counted == {holder_row["id"]: {"closed_after": 1}}
    assert "closed_after" in render.UNDECIDABLE, "no decision attributes it"
    said = render.aside_sentence(counted[holder_row["id"]])
    assert "for the maintainer to decide by hand" not in said
    assert "is not attributed here: 1 dated by the index after the Congress's terms ended" in said
    assert render.set_aside_counts(rows, [holder_row]) == {"waits": 0, "at_seat": 0, "shut": 1}


def test_the_landing_takes_its_set_aside_counts_from_the_page_kinds():
    """Seat A on the fourth reading: the landing's count could be swapped back for the old
    by-seat count and nothing failed, because no test rendered through the wiring. The landing
    and the pages count the same rows the same way."""
    holder_row = holder("AK00", "Example Alaska", "a000001")
    rows = [
        {
            "reason": "surname matches a sitting member (Alaska, Example, AK00) but the given "
            "names differ; the document carries no Filing ID line; a human decides this one",
            "source_row": {
                "state_dst": "AK00",
                "last": "Alaska",
                "first": "E.",
                "filing_type": "P",
                "filing_date": "3/1/2025",
            },
        },
        {
            "reason": "the register closed the filing year; the index dates this row after those "
            "terms, and nothing attributes it (Alaska, Example, AK00)",
            "source_row": {
                "state_dst": "AK00",
                "last": "Alaska",
                "first": "Example",
                "filing_type": "P",
                "filing_date": "1/8/2027",
            },
        },
    ]
    counts = render.set_aside_counts(rows, [holder_row])
    assert counts == {"waits": 1, "at_seat": 1, "shut": 1}
    section = plain(
        render.state_of_record(META, RUN, HOLDERS, FILINGS, OFFICES, counts, "https://x/rows")
    )
    assert "<dt>1</dt><dd>index rows set aside for the maintainer to decide by hand" in section
    assert "1 of them sit at an officeholder's own seat under their surname" in section
    assert "1 more is not attributed" in section, "and the row no decision attributes, apart"


def test_a_read_that_gives_the_published_value_again_is_said_and_counted_as_that():
    """Seats A, B and F on the fourth reading: a later read that gives back the value the row
    carries was written as a disagreement awaiting the maintainer, and counted in the caption
    among the reads that show a row otherwise."""
    agrees = {
        "id": "ch:read-otherwise:fl:house-clerk:P:1:filed_at:2026-10-12T00:00:00Z",
        "row_id": "fl:house-clerk:P:1",
        "rows": "filings",
        "change": "read otherwise",
        "field": "filed_at",
        "was": "2025-03-01",
        "now": "2025-03-01",
        "capture": {
            "url": "https://x/2025FD.zip",
            "retrieved_at": "2026-10-12T00:00:00Z",
            "content_hash": "0" * 64,
        },
    }
    page = plain(
        render.render_officeholder(
            HOLDERS[0], [FILINGS[0]], META, striker, changes={FILINGS[0]["id"]: [agrees]}
        )
    )
    assert "again gives the date filed as the register published it" in page
    assert "keeps it until the maintainer decides" not in page, "the two agree; nothing is pending"
    assert "A later read of the Clerk's index shows" not in page, (
        "and the caption counts what it says (Seat A)"
    )


# ---- P.1, the pages a reader can use (docs/design/pages-a-reader-can-use.md) --------------
#
# One test per change, each failing without it: the answer first and the same shape whatever
# the signal found (§2.1); a quiet page with the standards below the record and nothing
# removed (§2.2); a Finding's dates drawn from its own rows (§2.3); a long report folded and a
# report a Finding rests on open (§2.4); the practical thing where a reader reaches it (§2.5).

ON_TIME = [LATE[1]]


def signal_page(h: dict, reports: list[dict], rows: list[dict], held_reports: int = 0):
    found, _, by_holder = evaluated([h], reports, rows)
    return found, render.render_officeholder(
        h,
        reports,
        META,
        striker,
        0,
        rows,
        held_reports,
        [SIGNAL],
        found,
        {SIGNAL["id"]: by_holder.get(h["id"], [])},
    )


def answer_of(page: str) -> str:
    return between(page, '<section id="answer"', "</section>")


def shape(text: str) -> str:
    """An answer with its counts, and the quantifier English makes them take, folded away:
    what is left is the shape a reader meets, which must not depend on whether a signal fired
    (COUNCIL §5, mode 6; the design note §2.1)."""
    text = text.replace("at least one of", "Q of").replace("any of", "Q of")
    # A square's state and where it links are the result, drawn; the rest must match.
    text = re.sub(r"sq s-(after|checked|unchecked)", "sq S", text)
    text = re.sub(r"#(finding|report)-", "#T-", text)
    return re.sub(r"\b(\d[\d,]*|none)\b", "N", text)


def test_the_answer_comes_first_and_reads_the_same_whether_or_not_the_signal_fired():
    h = sworn(HOLDERS[0])
    report = read_report(h["id"], "2025-03-20", 1)
    found, fired = signal_page(h, [report], LATE)
    assert found, "the fixture fires"
    _, quiet = signal_page(h, [report], ON_TIME)
    for page in (fired, quiet):
        main = page[page.index('<main id="main">') :]
        order = [
            main.index('<section id="answer"'),
            main.index('<section class="checks">'),
            main.index('<section id="signals">'),
            main.index('<section id="transactions">'),
            main.index('<section id="requires"'),
            main.index("<h2>How to read this page</h2>"),
        ]
        assert order == sorted(order), "answer, checks, signal, record, standards, terms"
        answer = answer_of(page)
        assert "The register read 1 of 1 transaction report attributed to this officeholder" in (
            answer
        ), "the register's own coverage is the first number a reader meets"
        assert render.esc(render.EITHER_WAY) in answer
        assert f'href="{render.USC_13105}"' in answer, "the standard is cited and linked"
        assert verdict_words(answer) == [] and frame.check_page(page) is None
    assert (
        "The Clerk's index dates 1 of the 1 report checked after the deadline, by 37 days, for at "
        "least one trade on it."
    ) in answer_of(fired), "the count names its noun, and the days are the days (Seats A, B, D)"
    assert "The Clerk's index dates none of the 1 report checked after the deadline." in (
        answer_of(quiet)
    )
    for page in (fired, quiet):
        result = between(answer_of(page), "<p>The register read", "</p>")
        assert render.esc(render.FRAME) in result, (
            "the frame is inside the result's own paragraph, so no crop carries one without the "
            "other (Seat D)"
        )
        assert "on time" not in answer_of(page), "no timeliness word beside a result (Seat D)"

    # Everything but the result's own sentence is the same on both pages, in the same order.
    def frame_of(answer: str) -> str:
        return re.sub(r"The Clerk's index dates [^.]*\.", "RESULT.", answer)

    assert shape(frame_of(answer_of(fired))) == shape(frame_of(answer_of(quiet))), (
        "the same sentences, links and order on both pages; only the result differs"
    )


def test_the_answers_counts_are_the_signals_own_and_agree_with_the_page():
    h = sworn(HOLDERS[0])
    scanned = read_report(h["id"], "2025-02-01", 1, read=False)
    before = read_report(h["id"], "2025-01-10", 2)
    late = read_report(h["id"], "2025-03-20", 3)
    rows = [
        dict(
            transaction(before["id"], 1, transaction_date="2024-12-02", notified_date="2024-12-03"),
            filing_status="New",
        ),
    ] + [dict(r, id=r["id"].replace(":1:", ":3:"), filing_id=late["id"]) for r in LATE]
    found, page = signal_page(h, [scanned, before, late], rows)
    answer = answer_of(page)
    assert "The register read 2 of 3 transaction reports" in answer, "the scanned one is unread"
    assert "and checked 1 against" in answer, "a report whose rows all predate the oath is read"
    assert "The Clerk's index dates 1 of the 1 report checked after the deadline" in answer
    assert "Not checked: 1 scanned paper or not yet fetched; 1 with no trade the rule reaches." in (
        answer
    ), "each silence named where it is (Seats A and E)"
    assert page.count('<article class="finding"') == len(found) == 1
    assert "It evaluated 2 rows on 1 report attributed to this officeholder" in page


def test_an_answer_with_nothing_checked_never_reads_as_a_clean_result():
    h = sworn(HOLDERS[0])
    _, unread = signal_page(h, [read_report(h["id"], "2025-03-20", 1, read=False)], [])
    answer = answer_of(unread)
    assert "The register read 0 of 1 transaction report" in answer and "checked 0" in answer
    assert "It could check none of them: it is scanned paper or not yet fetched" in answer
    assert "a fact about what the register could read, not about what was filed" in answer
    assert "dates none" not in answer, "nothing checked is not a clean result"
    _, nothing = signal_page(sworn(HOLDERS[2]), [], [], held_reports=2)
    answer = answer_of(nothing)
    assert "No transaction report in the Clerk's 2025 index is attributed to this officeholder" in (
        answer
    )
    assert "It says nothing about whether this officeholder had anything to report." in answer
    assert "2 transaction reports at this seat under this surname are set aside" in answer
    assert "dates none" not in answer


def test_a_quiet_page_puts_the_standards_below_the_record_and_removes_nothing():
    h = sworn(HOLDERS[0])
    _, page = signal_page(h, [read_report(h["id"], "2025-03-20", 1)], ON_TIME)
    assert render.REQUIRES in page, "the standards are whole, word for word"
    requires = between(page, '<section id="requires"', "</section>")
    assert "a report listed on this page is a filing made under that requirement" in requires
    assert "listed below" not in requires, "the standards now sit below the reports"
    assert page.index(render.OATH) > page.index('<section id="transactions">')
    assert f'href="{render.STOCK_ACT}"' in requires and f'href="{render.USC_CH131}"' in requires


def the_figure(page: str) -> str:
    return between(page, '<figure class="dates">', "</figure>")


def test_each_finding_draws_its_dates_from_its_own_rows_and_says_what_it_does_not_show():
    h = sworn(HOLDERS[0])
    report = read_report(h["id"], "2025-03-20", 1)
    # Three rows after the deadline on one report: one due on a Saturday (notified 2025-01-16,
    # due 2025-02-15), one due 2025-02-11, and one due a day before the report's date.
    rows = [
        dict(LATE[0]),
        dict(
            transaction(report["id"], 3, transaction_date="2025-01-16", notified_date="2025-01-16"),
            filing_status="New",
        ),
        dict(
            transaction(report["id"], 4, transaction_date="2025-02-17", notified_date="2025-02-17"),
            filing_status="New",
        ),
    ]
    (finding_,), page = signal_page(h, [report], rows)
    figure = the_figure(page)
    drawing = between(figure, "<svg", "</svg>")
    table = between(page, "<tbody>", "</tbody>")
    assert drawing.count('<rect class="after"') == table.count("<tr>") == 3, "a line per row"
    assert render.dates_figure(finding_) == render.dates_figure(finding_), "it regenerates"
    widths = [float(w) for w in re.findall(r'class="after"[^>]*width="([\d.]+)"', drawing)]
    days = [int(d) for d in re.findall(r'<text class="days"[^>]*>(\d+)</text>', drawing)]
    assert days == [37, 33, 1], "the count at the end of each line is the table's days after"
    assert widths[0] > widths[1] > widths[2], "a longer span draws a longer bar, to scale"
    assert drawing.count('<circle class="next"') == 1, "the Saturday deadline's next business day"
    label = re.search(r'aria-describedby="(dates-[a-z0-9-]+)"', figure).group(1)
    assert 'aria-label="3 lines; days from the deadline to the report' in figure, "spoken short"
    assert f'<figcaption id="{label}">' in figure
    caption = between(figure, "<figcaption", "</figcaption>")
    assert "It does not show why the span is what it is" in caption
    assert "anything the House Committee on Ethics has determined" in caption
    assert "2025-03-20" in caption and "2025-01-10" in caption, "the scale's two ends, named"
    words = re.sub(r"<[^>]+>", " ", drawing).split()
    assert all(re.fullmatch(r"\d{4}-\d{2}-\d{2}|\d[\d,]*", w) for w in words), (
        "the drawing carries dates and counts only; its words are in the caption, where a "
        "translation reaches them (Seat F)"
    )
    assert verdict_words(figure) == []


def test_a_long_report_folds_and_a_report_a_finding_rests_on_stays_open():
    h = sworn(HOLDERS[0])
    quiet_long = read_report(h["id"], "2025-03-20", 1)
    fired_long = read_report(h["id"], "2025-04-20", 2)
    short = read_report(h["id"], "2025-05-20", 3)

    def rows_on(report: dict, n: int, traded: str, notified: str) -> list[dict]:
        return [
            dict(
                transaction(report["id"], i, transaction_date=traded, notified_date=notified),
                filing_status="New",
            )
            for i in range(1, n + 1)
        ]

    rows = (
        rows_on(quiet_long, 30, "2025-03-01", "2025-03-02")
        + rows_on(fired_long, 30, "2025-02-01", "2025-02-02")
        + rows_on(short, 3, "2025-05-01", "2025-05-02")
    )
    found, page = signal_page(h, [quiet_long, fired_long, short], rows)
    assert [f["producing_filings"][0] for f in found] == [fired_long["id"]]
    section = between(page, '<section id="transactions">', '<section id="requires"')
    assert section.count("<details>") == 1 and section.count("<details open>") == 1
    assert "<summary>The 30 rows of this report, as filed</summary>" in section
    assert (
        "<summary>The 30 rows of this report, as filed; a Finding rests on this report</summary>"
    ) in section
    folded = between(section, 'id="report-1"', 'id="report-2"')
    assert "<details>" in folded, "the report no Finding rests on is the folded one"
    assert section.count('<td class="idx">2025-05-01</td>') == 3, "a short report stays open"
    assert section.count('<td class="amt">') == 63, "every row is still in the page"


def test_the_practical_thing_is_where_a_reader_reaches_it():
    h = sworn(HOLDERS[0])
    _, page = signal_page(h, [read_report(h["id"], "2025-03-20", 1)], LATE)
    answer = answer_of(page)
    assert '<code translate="no">python tools/verify.py</code>' in answer
    assert f'build <code translate="no">{render.esc(render.build_label(META))}</code>' in answer
    for target in ("verify", "signals", "transactions", "requires"):
        assert f'href="#{target}"' in answer and f'id="{target}"' in page, target
    footer = page[page.index("<footer>") :]
    assert '<p id="verify">Cite the build, not the page.' in footer, "and it stays at the foot"


def test_the_answer_says_the_days_and_what_decides_them():
    """Seats A and B: a count of reports ranked the records backwards, three one-day Findings
    reading as more than one of 197 days. The answer says the days, and says where a weekend
    deadline met by the next business day, or a notice after the 45-day limit, decides one."""
    h = sworn(HOLDERS[0])
    # Notified 2025-01-18: 30 days is 2025-02-17, Washington's Birthday, a federal holiday; the
    # index dates the report 2025-02-18, the next business day: one day after, by the 2025 form.
    weekend = read_report(h["id"], "2025-02-18", 1)
    rows = [
        dict(
            transaction(
                weekend["id"], 1, transaction_date="2025-01-17", notified_date="2025-01-18"
            ),
            filing_status="New",
        )
    ]
    found, page = signal_page(h, [weekend], rows)
    assert found and found[0]["evidence"]["rows"][0]["deadline_falls_on"], "a holiday deadline"
    answer = answer_of(page)
    assert "by 1 day, for at least one trade on it." in answer
    assert (
        "For that report, the deadline fell on a weekend or holiday and the report is dated by the "
        "next business day; the 2025 form says such a deadline does not move."
    ) in answer
    late_notice = read_report(h["id"], "2025-06-20", 2)
    rows = [
        dict(
            transaction(
                late_notice["id"], 1, transaction_date="2025-01-10", notified_date="2025-06-20"
            ),
            filing_status="New",
        )
    ]
    found, page = signal_page(h, [late_notice], rows)
    assert found, "the fixture fires"
    answer = answer_of(page)
    assert "For that report, the notice date printed is more than 45 days after the trade" in (
        answer
    )
    days = found[0]["evidence"]["rows"][0]["days_after"]
    assert f"by {days} days" in answer


def test_an_answer_that_read_everything_and_checked_nothing_says_why_in_one_line():
    """Seat E: 'read 6 of 6' then blaming what the register could read was a contradiction."""
    h = sworn(HOLDERS[0], "2025-03-05")
    report = read_report(h["id"], "2025-03-20", 1)
    _, page = signal_page(h, [report], [LATE[0]])
    answer = answer_of(page)
    assert "The register read 1 of 1 transaction report" in answer and "checked 0" in answer
    assert "It could check none of them: no trade on them is one the rule reaches." in answer
    assert "scanned" not in between(answer, "<p>", "</p>")


def test_a_member_sworn_late_is_said_in_the_answer():
    """Seat E: the quiet a thirty-second reader meets first names the swearing-in date."""
    h = sworn(HOLDERS[0], "2025-11-12")
    _, page = signal_page(h, [], [])
    assert "The Clerk's roster records their swearing-in on 2025-11-12" in answer_of(page)


def test_the_figure_keeps_every_mark_inside_its_scale_across_a_year_and_a_sunday_report():
    """Seat C: a report dated on a Sunday, before the next business day after a Saturday
    deadline, put the tick past the upright line and on top of the count; and no test crossed
    a year boundary."""
    h = sworn(HOLDERS[0])
    # Notified 2025-11-13: due 2025-12-13, a Saturday; the index dates the report 2025-12-14,
    # a Sunday, one day after and a day before the first business day after it, 2025-12-15.
    sunday = read_report(h["id"], "2025-12-14", 1)
    rows = [
        dict(
            transaction(sunday["id"], 1, transaction_date="2025-11-13", notified_date="2025-11-13"),
            filing_status="New",
        )
    ]
    (finding_,), _ = signal_page(h, [sunday], rows)
    figure = render.dates_figure(finding_)
    drawing = between(figure, "<svg", "</svg>")
    ring = float(re.search(r'<circle class="next" cx="([\d.]+)"', drawing).group(1))
    count = float(re.search(r'<text class="days" x="([\d.]+)"', drawing).group(1))
    assert ring <= render.FIG_W - render.FIG_RIGHT < count, "the ring inside the scale, clear of it"
    # A Finding from November to January: the month ticks fall at the first of December and of
    # January, each where the scale puts it.
    later = read_report(h["id"], "2026-01-20", 2)
    rows = [
        dict(
            transaction(later["id"], 1, transaction_date="2025-11-20", notified_date="2025-11-20"),
            filing_status="New",
        )
    ]
    (finding_,), _ = signal_page(h, [later], rows)
    drawing = between(render.dates_figure(finding_), "<svg", "</svg>")
    ticks = [
        float(x) for x in re.findall(r'<line class="axis" x1="([\d.]+)" y1="[\d.]+" x2', drawing)
    ][1:]
    span = (render.date(2026, 1, 20) - render.date(2025, 11, 20)).days
    inner = render.FIG_W - render.FIG_LEFT - render.FIG_RIGHT
    expect = [
        round(render.FIG_LEFT + (d - render.date(2025, 11, 20)).days / span * inner, 1)
        for d in (render.date(2025, 12, 1), render.date(2026, 1, 1))
    ]
    assert ticks == expect, (ticks, expect)


def test_the_landing_shows_the_house_at_a_glance_and_names_no_one():
    holder_ = sworn(HOLDERS[0])
    report = read_report(holder_["id"], "2025-03-20", 1)
    found, outcomes, _ = evaluated([holder_], [report], LATE)
    summary = signal_run.run_record(SIGNAL["id"], "c" * 64, outcomes)[0]
    page = render.render_index(
        HOLDERS,
        OFFICES,
        FILINGS,
        RUN,
        META,
        striker,
        0,
        "https://x/rows",
        LATE,
        [(SIGNAL, summary)],
        None,
        None,
        {SIGNAL["id"]: outcomes},
        found,
    )
    glance = between(page, '<section class="glance" id="glance">', "</section>")
    assert "lists 1 transaction report" in glance and "attributed to 1 member" in glance
    assert glance.count('class="sq s-after"') == 2, "one in the squares, one in the key"
    assert "officeholders/" not in glance, "no square and no sentence links to a person"
    assert 'href="signals/stock-act-ptr-after-deadline/v1.html">the 1 member, in seat order' in (
        glance
    )
    assert (
        page.index('id="glance"') < page.index('id="find"') < page.index("What every member swore")
    )
    assert ranking.check_index(page) == [] and frame.check_page(page) is None
    assert verdict_words(page) == []


def test_the_strip_teaches_the_marks_and_draws_the_process_never_a_person():
    """The comic layer is the institution's and the process's: four panels, each teaching one mark
    the Findings' figures use; no person drawn, named or linked; a person's name is never lettered
    in the comic face (the maintainer's direction of 2026-09-27)."""
    holder_ = sworn(HOLDERS[0])
    report = read_report(holder_["id"], "2025-03-20", 1)
    unread = read_report(holder_["id"], "2025-04-20", 2, read=False)
    found, outcomes, _ = evaluated([holder_], [report, unread], LATE)
    summary = signal_run.run_record(SIGNAL["id"], "c" * 64, outcomes)[0]
    page = render.render_index(
        HOLDERS,
        OFFICES,
        FILINGS + [report, unread],
        RUN,
        META,
        striker,
        0,
        "https://x/rows",
        LATE,
        [(SIGNAL, summary)],
        None,
        None,
        {SIGNAL["id"]: outcomes},
        found,
    )
    strip = between(page, '<section class="howto" id="how">', "</section>")
    assert strip.count('<li class="panel">') == 4
    for mark in ("trade", "notice", "deadline", "after"):
        assert render.KEY_MARKS[mark] in strip, mark
    assert "officeholders/" not in strip and verdict_words(strip) == []
    assert "it does not ask anyone to stop trading" in strip
    assert "lists 2 of these reports. 1 of them arrived as scanned paper" in strip
    assert page.index('id="how"') < page.index('id="glance"')
    person = render.render_officeholder(HOLDERS[0], FILINGS[:1], META, striker, 0, [])
    assert 'class="comic"' not in person, "a person's name is never lettered as a comic"


def test_the_notice_clock_counts_trades_reports_and_members_and_names_no_one():
    """The one date the filer writes: every trade by the days from the trade to its printed
    notice. A count of trades alone would let one report look like many, so each band says its
    reports and members too; a notice printed before the trade is said as dates that cannot both
    be right; the chart carries dates and counts, never a name."""
    report = read_report(HOLDERS[0]["id"], "2025-06-20", 1)
    rows = [
        dict(
            transaction(report["id"], 1, transaction_date="2025-01-10", notified_date="2025-06-20"),
            owner="spouse",
        ),
        dict(
            transaction(report["id"], 2, transaction_date="2025-06-01", notified_date="2025-06-01")
        ),
        dict(
            transaction(report["id"], 3, transaction_date="2025-06-05", notified_date="2025-06-02")
        ),
    ]
    section = render.notice_section(rows, [report])
    assert "3 trades on the transaction reports" in section
    assert "<b>1</b> printed more than 45 days after the trade" in section
    assert (
        "1 trade on 1 report by 1 member. For 1 of these trades the filer marked the asset as a "
        "spouse's, and 1 is on a report dated the same day as the notice it prints." in section
    )
    assert "<b>1</b> printed before the trade itself, dates that cannot both be right" in section
    assert "(1 the same day)" in section
    assert "officeholders/" not in section and verdict_words(section) == []
    drawing = between(section, "<svg", "</svg>")
    words = re.sub(r"<[^>]+>", " ", drawing).replace("&lt;", "<").split()
    assert all(re.fullmatch(r"<0|\d+\+?", w) for w in words), words
    assert render.notice_section([], []) == ""
