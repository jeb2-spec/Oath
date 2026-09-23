"""Read a House Periodic Transaction Report as the Clerk's e-filing system writes it.

Pure functions over one document. Nothing here touches the network or the store. The
shape this module reads was measured on 2026-09-23 against all 417 transaction reports
in the Clerk's 2025 index, 363 of them produced by the Clerk's filing system (EO.Pdf)
and readable as text, the rest scanned paper.

The document is a table, and the table is read as a table: every text fragment pypdf
reports carries its position on the page, fragments sharing a baseline form a visual
line, and the column a fragment sits in says what it is. A transaction begins on the
line that carries a type in the Transaction Type column; that line also carries the
owner code (Owner column), the first line of the asset (Asset column), the two dates and
the first line of the amount band. Further asset lines and the band's second line sit
beneath it. Then come the labelled lines the form places under a transaction, each
keyed in the Asset column: `F S` filing status, `S O` subholding of, `L` location, `D`
description, `C` comments. A labelled line that wraps continues in the same column
without a key. Because the labels always come after the asset, a keyless line in that
column is an asset line until the first label appears and a label continuation after
it. A page break can fall anywhere, including between an asset's first and second line
or between the two halves of an amount band; the state carries across pages.

The Clerk's small-caps labels arrive as NUL bytes and are stripped before anything is
read. The legend for asset codes is the Clerk's, at
https://fd.house.gov/reference/asset-type-codes.aspx; the register does not restate it.

Two checks the index could never make are made here, and either failing refuses the
document rather than guessing: the seat in the header must be the roster seat of the
officeholder the index row was attributed to, and the filing ID in the document must be
the DocID the index gave it. A third check is per transaction: the asset text must end
in the Clerk's bracketed asset code, or the row is marked unconfirmed in its notes.

Owner codes as the form uses them: blank for the filer, SP spouse, JT joint, DC
dependent child. Transaction types as the form uses them: P purchase, S sale,
S (partial) partial sale, E exchange. Amount bands as printed, including "Over $X";
where a filer entered an exact figure instead of a band, the band is the whole
dollars on either side of it and the notes carry the figure as printed.
"""

from __future__ import annotations

import math
import re
from datetime import datetime

ASSET_CODES_LEGEND = "https://fd.house.gov/reference/asset-type-codes.aspx"

HEADER_NAME = re.compile(r"Name:\s*(.+)")
HEADER_STATUS = re.compile(r"Status:\s*(\S+)")
HEADER_SEAT = re.compile(r"State/District:\s*([A-Z]{2}\d{2})")
FILING_ID = re.compile(r"Filing ID #(\d+)")

# The table's columns as left edges, in points on a letter page. Measured on the Clerk's
# form: Owner 65, Asset 104 (label keys at 103.5, label values from 157), Transaction
# Type 261, Date 325, Notification Date 380, Amount 445, Cap. Gains 525. An amendment
# that fills the ID column shifts the table right by about sixteen points (asset 120,
# type 267). Each band opens well before its column and closes well after it, so a
# fragment is never on a fence.
COLUMNS = (
    ("id", 0),
    ("owner", 52),
    ("text", 95),
    ("mid", 132),
    ("type", 245),
    ("date", 305),
    ("notified", 360),
    ("amount", 420),
    ("gains", 500),
)

ASSET_TAG = re.compile(r"\[(?P<code>[A-Z]{2,3})\]\s*$")
TICKER = re.compile(r"\(([A-Z][A-Z0-9.$-]{0,9})\)\s*(?:\[[A-Z]{2,3}\])?\s*$")
LABEL_KEY = re.compile(r"^(?P<key>F\s?S|S\s?O|L|D|C)\s*:(?P<rest>.*)$")
LABELS = {
    "FS": "filing_status",
    "SO": "subholding_of",
    "L": "location",
    "D": "description",
    "C": "comments",
}

# The table heading, which every page repeats, and the footnote that closes the table.
HEADING_LAST = "$200?"
FOOTNOTE = re.compile(r"^\*\s*For the complete list of asset type abbreviations")
PAGE_FOOTER = re.compile(r"^Filing ID #\d+$")

OWNERS = {None: "self", "SP": "spouse", "JT": "joint", "DC": "dependent"}
ACTIONS = {"P": "purchase", "S": "sale", "S (partial)": "sale-partial", "E": "exchange"}


def iso(us_date: str) -> str:
    return datetime.strptime(us_date, "%m/%d/%Y").date().isoformat()


def amount_band(text: str) -> dict:
    """'$15,001 - $50,000' to {min: 15001, max: 50000}; 'Over $50,000,000' to an open top;
    an exact figure such as '$823.45' to the whole dollars on either side of it."""
    flat = re.sub(r"\s+", " ", text).strip()
    if flat.startswith("Over"):
        return {"min": int(flat.split("$")[1].replace(",", "")), "max": None, "currency": "USD"}
    if "-" not in flat:
        figure = float(flat.lstrip("$").replace(",", ""))
        return {"min": math.floor(figure), "max": math.ceil(figure), "currency": "USD"}
    low, high = (part.strip().lstrip("$") for part in flat.split("-"))
    return {"min": int(low.replace(",", "")), "max": int(high.replace(",", "")), "currency": "USD"}


def is_band(text: str) -> bool:
    """Whether the amount reads as one of the form's bands rather than an exact figure."""
    flat = re.sub(r"\s+", " ", text).strip()
    return flat.startswith("Over") or "-" in flat


def header(text: str) -> dict:
    """What the document says about itself: filer, status, seat, filing id. Empty when absent."""
    text = text.replace("\x00", "")
    name = HEADER_NAME.search(text)
    status = HEADER_STATUS.search(text)
    seat = HEADER_SEAT.search(text)
    filing_id = FILING_ID.search(text)
    return {
        "name": name.group(1).strip() if name else "",
        "status": status.group(1).strip() if status else "",
        "seat": seat.group(1) if seat else "",
        "filing_id": filing_id.group(1) if filing_id else "",
    }


def column(x: float) -> str:
    """The table column a fragment's left edge falls in."""
    name = COLUMNS[0][0]
    for candidate, left in COLUMNS:
        if x >= left:
            name = candidate
    return name


def lines_of(fragments: list[tuple[float, float, str]]) -> list[list[tuple[float, str]]]:
    """Visual lines of one page: fragments grouped by baseline, top to bottom, left to right.

    A fragment is (x, y, text) in points with y growing downward. Fragments whose
    baselines lie within two points share a line. Empty fragments are dropped.
    """
    cleaned = []
    for x, y, text in fragments:
        text = re.sub(r"\s+", " ", text.replace("\x00", "")).strip()
        if text:
            cleaned.append((x, y, text))
    cleaned.sort(key=lambda f: (f[1], f[0]))
    lines: list[list[tuple[float, str]]] = []
    last_y = None
    for x, y, text in cleaned:
        if last_y is None or abs(y - last_y) > 2:
            lines.append([])
            last_y = y
        lines[-1].append((x, text))
    for line in lines:
        line.sort(key=lambda f: f[0])
    return lines


def table_lines(pages: list[list[list[tuple[float, str]]]]) -> list[list[tuple[float, str]]]:
    """The lines that belong to the transactions table, across pages, in reading order.

    On each page the table begins after the heading's last line and ends at the footnote;
    the page footer's filing id line is dropped wherever it falls.
    """
    out = []
    for page in pages:
        active = False
        for line in page:
            joined = " ".join(text for _, text in line)
            if not active:
                active = any(text == HEADING_LAST for _, text in line)
                continue
            if FOOTNOTE.match(joined):
                break
            if PAGE_FOOTER.match(joined):
                continue
            out.append(line)
    return out


def transactions(pages: list[list[list[tuple[float, str]]]]) -> list[dict]:
    """Every transaction in the document, in document order.

    `pages` is the document as pages of visual lines, as `lines_of` builds them. Each
    item: owner, asset, asset_code, ticker, action, raw_type, transaction_date,
    notified_date, amount (the band as an object), asset_confirmed (the asset text ended
    in the Clerk's tag), and, when the document gives them, filing_status,
    subholding_of, location, description and comments.
    """
    rows: list[dict] = []
    current: dict | None = None
    last_label: str | None = None
    for line in table_lines(pages):
        by_column: dict[str, list[str]] = {}
        for x, text in line:
            by_column.setdefault(column(x), []).append(text)
        if "type" in by_column:
            current = {
                "_owner": " ".join(by_column.get("owner", [])) or None,
                "_asset": by_column.get("text", []) + by_column.get("mid", []),
                "_amount": by_column.get("amount", []),
                "raw_type": " ".join(by_column["type"]),
                "transaction_date": " ".join(by_column.get("date", [])),
                "notified_date": " ".join(by_column.get("notified", [])),
                "_labels": {},
            }
            rows.append(current)
            last_label = None
            continue
        if current is None:
            continue
        first_x, first_text = line[0]
        key = LABEL_KEY.match(first_text) if column(first_x) == "text" else None
        if key:
            last_label = LABELS[re.sub(r"\s", "", key.group("key"))]
            value = [key.group("rest")] + [text for _, text in line[1:]]
            current["_labels"][last_label] = " ".join(value).strip()
        elif last_label is not None:
            tail = " ".join(text for _, text in line)
            current["_labels"][last_label] = f"{current['_labels'][last_label]} {tail}".strip()
        else:
            current["_asset"].extend(by_column.get("text", []) + by_column.get("mid", []))
            current["_amount"].extend(by_column.get("amount", []))
    return [finish(row) for row in rows]


def finish(row: dict) -> dict:
    """The transaction as the register stores it, from the assembled cells."""
    asset_text = " ".join(row["_asset"]).strip()
    tag = ASSET_TAG.search(asset_text)
    ticker = TICKER.search(asset_text)
    out = {
        "owner": OWNERS.get(row["_owner"], "self"),
        "asset": ASSET_TAG.sub("", asset_text).strip() if tag else asset_text,
        "asset_code": tag.group("code") if tag else None,
        "asset_confirmed": tag is not None,
        "ticker": ticker.group(1) if ticker else None,
        "action": ACTIONS.get(row["raw_type"], "other"),
        "raw_type": row["raw_type"],
        "transaction_date": iso(row["transaction_date"]),
        "notified_date": iso(row["notified_date"]),
        "amount": amount_band(" ".join(row["_amount"])),
        "raw_amount": re.sub(r"\s+", " ", " ".join(row["_amount"])).strip(),
    }
    out.update(row["_labels"])
    return out


def notes(tx: dict) -> str:
    """The transaction's notes field: the Clerk's code and legend, the type as printed, and
    the document's own labelled lines. Says so when the asset text could not be confirmed."""
    parts = [
        f"Asset code {tx.get('asset_code') or 'none'} per the Clerk's legend "
        f"({ASSET_CODES_LEGEND}); type printed as {tx['raw_type']}."
    ]
    if tx.get("subholding_of"):
        parts.append(f"Subholding of: {tx['subholding_of']}.")
    if tx.get("location"):
        parts.append(f"Location, as filed: {tx['location']}.")
    if tx.get("description"):
        parts.append(f"Description, as filed: {tx['description']}.")
    if tx.get("comments"):
        parts.append(f"Comments, as filed: {tx['comments']}.")
    if tx.get("filing_status") and tx["filing_status"].lower() != "new":
        parts.append(f"Filing status: {tx['filing_status']}.")
    if tx.get("raw_amount") and not is_band(tx["raw_amount"]):
        parts.append(
            f"Amount printed as {tx['raw_amount']}, an exact figure rather than one of the "
            "form's bands."
        )
    if not tx.get("asset_confirmed"):
        parts.append("Asset text unconfirmed: it did not end in the Clerk's asset tag.")
    return " ".join(parts)


def verify(
    text: str, expected_seat: str, expected_doc_id: str, name_confirms=None
) -> tuple[str, str]:
    """How the document stands to the index row it was attributed to.

    Returns (status, reason). Status is one of:
      "ok"            the document names the same seat and the same filing id;
      "unreadable"    the text carries no Filing ID line, so it is scanned or another
                      form; the row stands, nothing is read from the document;
      "discrepancy"   the document names a different seat, but its printed name
                      confirms the officeholder (`name_confirms`, given the printed
                      name, returned true) and the filing id agrees; the row stands,
                      the document is read, and the caller carries the reason on the
                      row, because a filer's profile can print the seat held before;
      "contradiction" the document names a different filing id, or a different seat
                      without a confirming name, which refuses the row itself, because
                      the document is the primary record and the index row's
                      attribution is what it contradicts.
    """
    head = header(text)
    if not head["filing_id"]:
        return (
            "unreadable",
            "the document carries no Filing ID line; it is scanned or a different form",
        )
    if head["filing_id"] != str(expected_doc_id):
        return (
            "contradiction",
            f"the document says Filing ID {head['filing_id']}; the index row is DocID "
            f"{expected_doc_id}",
        )
    if not head["seat"]:
        return "unreadable", "the document carries no State/District line"
    if head["seat"] != expected_seat:
        reason = (
            f"the document says State/District {head['seat']}; the officeholder it was "
            f"attributed to holds {expected_seat}"
        )
        if name_confirms is not None and name_confirms(head["name"]):
            return "discrepancy", reason
        return "contradiction", reason
    return "ok", ""


def read(pdf_path) -> tuple[str, list[list[list[tuple[float, str]]]]]:
    """The document's text and its pages of visual lines, in one pass over the file.

    Imports the one reader dependency lazily. Positions come from pypdf's text visitor:
    the text matrix composed with the current transformation matrix gives the point on
    the page, and y is measured from the top so that reading order is ascending. On
    some pages pypdf also reports the page's whole text once more as a single fragment
    at the page origin; a fragment with a line break inside it is that repeat, never a
    table cell, and is dropped.
    """
    try:
        import pypdf  # the register's one extraction dependency; see NEXT.md, obtaining the record
    except ImportError as exc:  # pragma: no cover
        raise SystemExit("reading documents needs pypdf: python -m pip install pypdf") from exc
    reader = pypdf.PdfReader(str(pdf_path))
    texts, pages = [], []
    for page in reader.pages:
        height = float(page.mediabox.height)
        fragments: list[tuple[float, float, str]] = []

        def visit(text, cm, tm, font_dict, font_size, fragments=fragments, height=height):
            x = tm[4] * cm[0] + tm[5] * cm[2] + cm[4]
            y = tm[4] * cm[1] + tm[5] * cm[3] + cm[5]
            if "\n" not in text.strip():
                fragments.append((x, height - y, text))

        texts.append(page.extract_text(visitor_text=visit) or "")
        pages.append(lines_of(fragments))
    return "\n".join(texts), pages


def extract_text(pdf_path) -> str:
    """The document's text alone, for callers that only need the header."""
    return read(pdf_path)[0]
