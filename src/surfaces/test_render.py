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


def transaction(filing_id: str, n: int, **over) -> dict:
    row = {
        "id": f"tx:house-clerk:{filing_id.rsplit(':', 1)[1]}:{n:03d}",
        "filing_id": filing_id,
        "officeholder_id": "oh:us:house:a000001",
        "owner": "unmarked",
        "asset": "Example Widgets Inc. Common Stock (EXW)",
        "asset_normalized": "EXW",
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
    section = page[page.index('<section id="transactions">') : page.index("<h2>Signals that fired")]
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
    assert "The report filed 2025-04-01 is captured and not read" in page
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
        {"PR00": 1},
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
    assert render.held_reports_at_seat(rows, HOLDERS) == {"PR00": 1}


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

signal_module = _load(ROOT / "src" / "signals" / "stock-act-late-ptr.py", "signal_late_ptr")
signal_run = _load(ROOT / "src" / "signals" / "run.py", "signal_run")
verdict = _load(ROOT / "tools" / "lint-verdict-language.py", "lint_verdict")
SIGNAL = signal_run.parse_definition(ROOT / "docs" / "signals" / "stock-act-late-ptr.md")
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
    return [
        m.group(0)
        for line in page.splitlines()
        for m in verdict.PATTERN.finditer(line)
        if not verdict.is_frame_word(line, m.group(0))
    ]


def between(page: str, start: str, end: str) -> str:
    return page[page.index(start) : page.index(end)]


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
    assert 'id="signal-stock-act-late-ptr"' in fired and 'id="finding-1"' in fired
    assert render.esc(finding_["description"]) in fired
    assert render.esc(render.NOT_A_DETERMINATION) in fired
    assert f"python tools/rebuild.py {finding_['id']}" in fired
    assert 'href="../signals/stock-act-late-ptr/v1.html"' in fired
    assert '<td class="idx">2025-02-11</td>' in fired and "30 days after notice" in fired
    assert '<td class="idx">37</td>' in fired, "the days after, from the deadline to the index date"
    assert 'href="#report-1"' in fired, "the Finding links to its report's rows, as filed"
    assert "and fired on it, shown below" in fired
    quiet = page[page.index("<h2>Signals that did not fire") :]
    assert "None: every Signal defined in this build fired, above." in quiet
    assert "fired on 1 report, below" in page
    assert frame.check_page(page) is None
    assert verdict_words(page) == []


def test_a_quiet_signal_says_which_silence_it_is():
    on_time = [LATE[1]]
    cases = {
        "every one was on or before its deadline": (sworn(HOLDERS[0]), True, on_time),
        "1 row was not evaluated: 1 dated before the swearing-in the roster records.": (
            sworn(HOLDERS[0], "2025-03-05"),
            True,
            [LATE[0]],
        ),
        "1 report is captured and not read: scanned paper": (sworn(HOLDERS[0]), False, []),
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
        assert 'id="signal-stock-act-late-ptr"' in quiet and expected in quiet, expected
        assert "did not fire; below, which silence it is" in page
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
        f"the correction <code>{withdrawal['id']}</code> records that it no longer fires" in quiet
    )
    assert render.esc(note) in quiet and f"<code>{first['id']}</code>" in quiet
    assert "did not fire; below, which silence it is" in page
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
    correction = dict(first, id=first["id"] + ":c1", notes=note, fired_at="2026-10-01T00:00:00Z")
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
    assert f"Corrected: this row supersedes <code>{first['id']}</code>" in page
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
        {},
        "https://x/rows",
        LATE,
        [(SIGNAL, summary)],
    )
    assert ranking.check_index(page) == []
    assert frame.check_page(page) is None
    assert 'href="signals/stock-act-late-ptr/v1.html"' in page
    assert "This build holds 1 signal" in page
    assert "signals defined, so 0 fired" not in page
    assert verdict_words(page) == []
