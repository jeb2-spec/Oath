"""Tests for ptr.py against a document shaped like the Clerk's e-filed transaction reports.

No real person appears here. The names, seat and filing id are placeholders; the
layout is the one the Clerk's system prints, measured on 2026-09-23: text fragments at
the form's column positions, the owner code in its own column, the asset ending in the
Clerk's bracketed code, the type and dates and band on the transaction's first line, and
labelled lines beneath it that may wrap. The fixture is two pages, with a page break
falling inside a transaction, because the real documents do that.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _load():
    spec = importlib.util.spec_from_file_location("house_fd_ptr", HERE / "ptr.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


ptr = _load()
NUL = "\x00" * 5

# Column left edges in points, as measured on the form.
ID, OWNER, ASSET, KEY, VALUE, TYPE, DATE, NOTIFIED, AMOUNT, GAINS = (
    25.5,
    65.25,
    104.25,
    103.5,
    156.75,
    261.0,
    325.5,
    380.25,
    444.75,
    525.0,
)

TEXT = f"""P{NUL} T{NUL} R{NUL}
Clerk of the House of Representatives � Legislative Resource Center � B81 Cannon Building
F{NUL} I{NUL}
Name: Hon. Example Placeholder
Status: Member
State/District: XX01
Filing ID #12345678
"""


def heading(y: float) -> list[tuple[float, float, str]]:
    return [
        (ID, y, "ID"),
        (OWNER, y, "Owner"),
        (ASSET, y, "Asset"),
        (TYPE, y, "Transaction"),
        (DATE, y, "Date"),
        (NOTIFIED, y, "Notification"),
        (AMOUNT, y, "Amount"),
        (GAINS, y, "Cap."),
        (TYPE, y + 11, "Type"),
        (NOTIFIED, y + 11, "Date"),
        (GAINS, y + 11, "Gains >"),
        (GAINS, y + 22, "$200?"),
    ]


PAGE_ONE = [
    (117.0, 34.0, f"P{NUL} T{NUL} R{NUL}"),
    (69.0, 73.0, "Clerk of the House of Representatives � Legislative Resource Center"),
    (22.0, 108.0, f"F{NUL} I{NUL}"),
    (22.0, 126.0, "Name:"),
    (99.0, 126.0, "Hon. Example Placeholder"),
    (22.0, 142.0, "Status:"),
    (99.0, 142.0, "Member"),
    (22.0, 158.0, "State/District:"),
    (99.0, 158.0, "XX01"),
    (22.0, 194.0, f"T{NUL}"),
    *heading(217.0),
    # Transaction 1: the filer's own, one asset line, the tag on the next line.
    (ASSET, 261.0, "Example Widgets Inc. Common Stock (EXW)"),
    (TYPE, 261.0, "P"),
    (DATE, 261.0, "12/06/2024"),
    (NOTIFIED, 261.0, "01/06/2025"),
    (AMOUNT, 261.0, "$1,001 - $15,000"),
    (ASSET, 271.5, "[ST]"),
    (KEY, 289.0, f"F{NUL} S{NUL}:"),
    (VALUE, 289.0, "New"),
    # Transaction 2: a three-line asset and a band that wraps.
    (ASSET, 320.0, "Placeholder Partners, L.P. -"),
    (TYPE, 320.0, "S (partial)"),
    (DATE, 320.0, "12/06/2024"),
    (NOTIFIED, 320.0, "01/06/2025"),
    (AMOUNT, 320.0, "$15,001 -"),
    (ASSET, 330.5, "Common Units Representing Limited"),
    (AMOUNT, 330.5, "$50,000"),
    (ASSET, 341.0, "Partnership Interests (PLP)"),
    (150.0, 341.0, "[ST]"),
    (KEY, 358.0, f"F{NUL} S{NUL}:"),
    (VALUE, 358.0, "New"),
    # Transaction 3: the spouse's, an open top band, three labelled lines.
    (OWNER, 390.0, "SP"),
    (ASSET, 390.0, "Sample Municipal Bond 2031"),
    (140.0, 390.0, "[GS]"),
    (TYPE, 390.0, "S"),
    (DATE, 390.0, "11/30/2024"),
    (NOTIFIED, 390.0, "12/20/2024"),
    (AMOUNT, 390.0, "Over $50,000,000"),
    (KEY, 407.0, f"F{NUL} S{NUL}:"),
    (VALUE, 407.0, "New"),
    (KEY, 420.0, f"S{NUL} O{NUL}:"),
    (VALUE, 420.0, "Stocks, Bonds, & Mutual Funds"),
    (KEY, 433.0, f"L{NUL}:"),
    (VALUE, 433.0, "US"),
    (KEY, 446.0, f"D{NUL}:"),
    (VALUE, 446.0, "Called Security"),
    # Transaction 4 begins here and continues on the next page.
    (OWNER, 480.0, "JT"),
    (ASSET, 480.0, "Example Exchange Fund"),
    (TYPE, 480.0, "E"),
    (DATE, 480.0, "12/07/2024"),
    (NOTIFIED, 480.0, "01/06/2025"),
    (AMOUNT, 480.0, "$100,001 -"),
    (22.0, 760.0, "Filing ID #12345678"),
]

PAGE_TWO = [
    *heading(217.0),
    # The rest of transaction 4: the asset's second line and the band's second half.
    (ASSET, 261.0, "(EXF) [OT]"),
    (AMOUNT, 261.0, "$250,000"),
    (KEY, 278.0, f"F{NUL} S{NUL}:"),
    (VALUE, 278.0, "Amended"),
    (KEY, 291.0, f"D{NUL}:"),
    (VALUE, 291.0, "exchange of units, as filed"),
    (KEY, 304.0, f"C{NUL}:"),
    (VALUE, 304.0, "A long comment that the form wraps because it runs past the width of the"),
    (KEY, 317.0, "table on the page."),
    (ID, 340.0, "* For the complete list of asset type abbreviations, please visit"),
    (250.0, 340.0, "https://fd.house.gov/reference/asset-type-codes.aspx"),
    (22.0, 370.0, "I P O"),
    (
        22.0,
        400.0,
        "I CERTIFY that the statements I have made on the attached Periodic Transaction Report",
    ),
]

PAGES = [ptr.lines_of(PAGE_ONE), ptr.lines_of(PAGE_TWO)]


def test_header_reads_seat_and_filing_id_through_the_nul_bytes():
    head = ptr.header(TEXT)
    assert head == {
        "name": "Hon. Example Placeholder",
        "status": "Member",
        "seat": "XX01",
        "filing_id": "12345678",
    }


def test_lines_group_fragments_by_baseline_top_to_bottom_left_to_right():
    lines = ptr.lines_of([(300.0, 50.0, "b"), (100.0, 51.0, "a"), (100.0, 80.0, f"c{NUL}")])
    assert lines == [[(100.0, "a"), (300.0, "b")], [(100.0, "c")]]


def test_every_transaction_is_read_in_order_with_owner_type_dates_and_band():
    rows = ptr.transactions(PAGES)
    assert [r["action"] for r in rows] == ["purchase", "sale-partial", "sale", "exchange"]
    assert [r["owner"] for r in rows] == ["unmarked", "unmarked", "spouse", "joint"]
    assert rows[0]["asset"] == "Example Widgets Inc. Common Stock (EXW)"
    assert rows[0]["ticker"] == "EXW" and rows[0]["asset_code"] == "ST"
    assert rows[0]["transaction_date"] == "2024-12-06"
    assert rows[0]["notified_date"] == "2025-01-06"
    assert rows[0]["amount"] == {"min": 1001, "max": 15000, "currency": "USD"}
    assert all(r["asset_confirmed"] for r in rows)


def test_a_band_split_across_lines_and_an_open_top_band_both_read():
    rows = ptr.transactions(PAGES)
    assert rows[1]["amount"] == {"min": 15001, "max": 50000, "currency": "USD"}
    assert rows[2]["amount"] == {"min": 50000000, "max": None, "currency": "USD"}


def test_multi_line_assets_keep_their_whole_name():
    rows = ptr.transactions(PAGES)
    assert rows[1]["asset"] == (
        "Placeholder Partners, L.P. - Common Units Representing Limited Partnership Interests (PLP)"
    )
    assert rows[1]["ticker"] == "PLP"


def test_the_labelled_lines_belong_to_the_row_above_them_and_wrapped_ones_stay_whole():
    rows = ptr.transactions(PAGES)
    assert rows[2]["subholding_of"] == "Stocks, Bonds, & Mutual Funds"
    assert rows[2]["location"] == "US"
    assert rows[2]["description"] == "Called Security"
    assert rows[3]["filing_status"] == "Amended"
    assert rows[3]["description"] == "exchange of units, as filed"
    assert rows[3]["comments"] == (
        "A long comment that the form wraps because it runs past the width of the "
        "table on the page."
    )
    assert "subholding_of" not in rows[0] and "description" not in rows[1]


def test_a_transaction_split_by_a_page_break_is_one_transaction():
    rows = ptr.transactions(PAGES)
    assert len(rows) == 4
    assert rows[3]["asset"] == "Example Exchange Fund (EXF)"
    assert rows[3]["ticker"] == "EXF" and rows[3]["asset_code"] == "OT"
    assert rows[3]["amount"] == {"min": 100001, "max": 250000, "currency": "USD"}


def test_page_furniture_headers_and_labels_never_leak_into_an_asset_name():
    rows = ptr.transactions(PAGES)
    for r in rows:
        for leak in (
            "Filing ID",
            "Notification",
            "F S",
            ": New",
            "S O",
            "D:",
            "$200?",
            "Name:",
            "Clerk of the House",
            "State/District",
            "Owner",
            "I CERTIFY",
            "For the complete list",
        ):
            assert leak not in r["asset"], (leak, r["asset"])
    assert rows[2]["asset"] == "Sample Municipal Bond 2031" and rows[2]["ticker"] is None


def test_an_exact_figure_where_the_form_offers_a_band_is_kept_to_the_dollar():
    assert ptr.amount_band("$823.45") == {"min": 823, "max": 824, "currency": "USD"}
    assert ptr.amount_band("$2,000.00") == {"min": 2000, "max": 2000, "currency": "USD"}
    assert ptr.is_band("$1,001 - $15,000") and ptr.is_band("Over $50,000,000")
    assert not ptr.is_band("$823.45")
    page = ptr.lines_of(
        [
            *heading(217.0),
            (ASSET, 261.0, "Example Fund II, LP [PS]"),
            (TYPE, 261.0, "P"),
            (DATE, 261.0, "04/03/2025"),
            (NOTIFIED, 261.0, "04/28/2025"),
            (AMOUNT, 261.0, "$823.45"),
        ]
    )
    rows = ptr.transactions([page])
    assert rows[0]["amount"] == {"min": 823, "max": 824, "currency": "USD"}
    assert "Amount printed as $823.45, an exact figure" in ptr.notes(rows[0])


def test_an_asset_without_the_clerks_tag_is_marked_unconfirmed_not_dropped():
    page = ptr.lines_of(
        [
            *heading(217.0),
            (ASSET, 261.0, "Some wrapped description text"),
            (TYPE, 261.0, "P"),
            (DATE, 261.0, "01/02/2025"),
            (NOTIFIED, 261.0, "01/03/2025"),
            (AMOUNT, 261.0, "$1,001 - $15,000"),
        ]
    )
    rows = ptr.transactions([page])
    assert len(rows) == 1 and rows[0]["asset_confirmed"] is False
    assert rows[0]["asset"] == "Some wrapped description text"
    assert "unconfirmed" in ptr.notes(rows[0])


def test_notes_carry_the_legend_the_type_and_the_documents_own_lines():
    rows = ptr.transactions(PAGES)
    note = ptr.notes(rows[2])
    assert "Asset code GS" in note and "asset-type-codes" in note and "type printed as S." in note
    assert "Subholding of: Stocks, Bonds, & Mutual Funds." in note
    assert "Location, as filed: US." in note
    assert "Description, as filed: Called Security." in note
    assert "Filing status: Amended." in ptr.notes(rows[3])
    assert "Comments, as filed: A long comment" in ptr.notes(rows[3])
    assert "Filing status" not in ptr.notes(rows[0]), "New is the default and is not repeated"


def test_the_document_must_agree_with_the_row_it_was_attributed_to():
    assert ptr.verify(TEXT, "XX01", "12345678") == ("ok", "")
    status, reason = ptr.verify(TEXT, "XX02", "12345678")
    assert status == "contradiction" and "holds XX02" in reason
    status, reason = ptr.verify(TEXT, "XX01", "99")
    assert status == "contradiction" and "DocID 99" in reason
    status, reason = ptr.verify("Name: Nobody\nState/District: XX01\n", "XX01", "1")
    assert status == "unreadable" and "no Filing ID" in reason


def test_a_seat_mismatch_with_a_confirming_name_is_a_discrepancy_not_a_contradiction():
    def confirms(printed: str) -> bool:
        return "Example Placeholder" in printed

    def denies(printed: str) -> bool:
        return False

    status, reason = ptr.verify(TEXT, "XX02", "12345678", name_confirms=confirms)
    assert status == "discrepancy"
    assert "State/District XX01" in reason and "holds XX02" in reason
    status, _ = ptr.verify(TEXT, "XX02", "12345678", name_confirms=denies)
    assert status == "contradiction"
    status, _ = ptr.verify(TEXT, "XX01", "99", name_confirms=confirms)
    assert status == "contradiction", "a different filing id is never a discrepancy"


def test_the_register_adds_no_punctuation_the_filer_did_not_write():
    assert (
        ptr.labelled("Description, as filed", "Sold 10 units.")
        == "Description, as filed: Sold 10 units."
    )
    assert (
        ptr.labelled("Description, as filed", "Sold 10 units")
        == "Description, as filed: Sold 10 units."
    )
    assert ptr.labelled("Comments, as filed", "Why?") == "Comments, as filed: Why?"
    assert "self" not in ptr.OWNERS.values(), "the House form never states the filer's own"
