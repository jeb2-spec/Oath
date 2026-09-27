"""The correction a person makes, proven end to end. INVARIANTS.md §14; BYLAWS.md §5, §6.

A correction is a row a reader can see, citing a primary source whose bytes the register
keeps; the fact moves, what it was stays in the row, and the §14 gate lets exactly that move
through. Found necessary by the Council's reading of S.1b: once the gate refused every fact
moved in place, nothing a person could do would correct a filing's date or attribution.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


correct = load("correct", ROOT / "tools" / "correct.py")
gate = load("check_removals", ROOT / "tools" / "check-removals.py")
schemas = load("validate_schemas", ROOT / "tools" / "validate-schemas.py")

ROW = {
    "id": "fl:house-clerk:P:1",
    "officeholder_id": "oh:us:house:x000001",
    "filed_at": "2025-02-25",
    "source": {"url": "u", "retrieved_at": "2026-01-01T00:00:00Z", "content_hash": None},
}
URL = "https://disclosures-clerk.house.gov/public_disc/financial-pdfs/2025FD.zip"
EVIDENCE = b"the index, as the Clerk now serves it"
RETRIEVED = "2026-10-05T09:17:33Z"


@pytest.fixture
def register(tmp_path, monkeypatch):
    """A throwaway repository whose branch `published` holds one filing."""
    (tmp_path / "data").mkdir()
    (tmp_path / "tools").mkdir()
    shutil.copy(ROOT / "SOURCES.md", tmp_path / "SOURCES.md")
    shutil.copy(ROOT / "tools" / "check-aggregator-sole.py", tmp_path / "tools")
    (tmp_path / "data" / "filings.ndjson").write_text(correct.canonical(ROW), encoding="utf-8")
    for args in (
        ["init", "-q", "-b", "published"],
        ["add", "-A"],
        ["-c", "user.email=t@example.com", "-c", "user.name=t", "commit", "-q", "-m", "p"],
    ):
        subprocess.run(["git", "-C", str(tmp_path), *args], check=True, capture_output=True)
    (tmp_path / "evidence.zip").write_bytes(EVIDENCE)
    monkeypatch.setenv("OATH_PUBLISHED_REF", "published")
    return tmp_path


def run(root: Path, *extra: str) -> int:
    return correct.main(
        [
            str(root),
            "--row",
            "fl:house-clerk:P:1",
            "--field",
            "filed_at",
            "--kind",
            "source",
            "--because",
            "The Clerk's index read 2026-10-05 dates the report 2025-02-26.",
            "--evidence-url",
            URL,
            "--evidence-file",
            str(root / "evidence.zip"),
            "--decided-by",
            "the maintainer",
            "--decided-at",
            "2026-10-06T12:00:00Z",
            "--evidence-retrieved-at",
            RETRIEVED,
            *extra,
        ]
    )


def changes(root: Path) -> list[dict]:
    path = root / "data" / "changes.ndjson"
    return [json.loads(line) for line in path.read_text("utf-8").splitlines()]


def test_a_correction_moves_the_fact_keeps_what_it_was_and_passes_the_gate(register):
    assert gate.main([str(register)]) == 0
    assert run(register, "--now", "2025-02-26") == 0
    row = json.loads((register / "data" / "filings.ndjson").read_text("utf-8"))
    assert row == dict(ROW, filed_at="2025-02-26")
    (change,) = changes(register)
    assert (change["change"], change["field"], change["was"], change["now"], change["kind"]) == (
        "corrected",
        "filed_at",
        "2025-02-25",
        "2025-02-26",
        "source",
    )
    assert change["capture"]["retrieved_at"] == RETRIEVED, (
        "the evidence's own time, not the decision's"
    )
    kept = register / "data" / "captures" / "sha256" / f"{change['capture']['content_hash']}.zip"
    assert kept.read_bytes() == EVIDENCE, "the evidence's bytes are kept, named by their hash"
    assert gate.main([str(register)]) == 0, "the gate lets exactly this move through"
    loaded = schemas.load_schemas(ROOT)
    assert (
        schemas.validate(change, loaded["change.schema.json"], loaded, "change.schema.json") == []
    )


def test_the_same_move_without_its_row_is_refused_by_the_gate(register):
    moved = dict(ROW, filed_at="2025-02-26")
    (register / "data" / "filings.ndjson").write_text(correct.canonical(moved), encoding="utf-8")
    assert gate.main([str(register)]) == 1


def test_a_value_that_stands_is_recorded_and_nothing_moves(register):
    before = (register / "data" / "filings.ndjson").read_bytes()
    assert run(register, "--stands") == 0
    assert (register / "data" / "filings.ndjson").read_bytes() == before
    (change,) = changes(register)
    assert change["was"] == change["now"] == "2025-02-25"
    assert gate.main([str(register)]) == 0


@pytest.mark.parametrize(
    "extra, says",
    [
        (["--now", "2025-02-25"], "nothing to move"),
        (["--stands", "--now", "2025-02-26"], "give no --now"),
        ([], "give --now"),
        (["--now", "x", "--field", "no_such_fact"], "carries no no_such_fact"),
    ],
)
def test_a_correction_that_says_nothing_or_too_much_is_refused(register, capsys, extra, says):
    assert run(register, *extra) == 1
    assert says in capsys.readouterr().out
    assert not (register / "data" / "changes.ndjson").exists()


def test_the_evidence_must_be_a_primary_source_and_hashed(register, capsys):
    args = [str(register), "--row", "fl:house-clerk:P:1", "--field", "filed_at"]
    tail = ["--kind", "source", "--because", "why", "--decided-by", "the maintainer"]
    tail += ["--evidence-retrieved-at", RETRIEVED]
    for url, evidence in (
        ("https://www.opensecrets.org/x", register / "evidence.zip"),
        ("http://disclosures-clerk.house.gov/x", register / "evidence.zip"),
        (URL, register / "missing.zip"),
    ):
        code = correct.main(
            [*args, "--now", "2025-02-26", "--evidence-url", url, "--evidence-file", str(evidence)]
            + tail
        )
        assert code == 1
    out = capsys.readouterr().out
    assert "primary source" in out and "hashes the bytes" in out
    assert not (register / "data" / "changes.ndjson").exists()


def test_a_row_the_register_does_not_hold_is_refused(register, capsys):
    code = correct.main(
        [
            str(register),
            "--row",
            "fl:house-clerk:P:2",
            "--field",
            "filed_at",
            "--now",
            "x",
            "--kind",
            "register",
            "--because",
            "why",
            "--evidence-url",
            URL,
            "--evidence-file",
            str(register / "evidence.zip"),
            "--decided-by",
            "the maintainer",
            "--evidence-retrieved-at",
            RETRIEVED,
        ]
    )
    assert code == 1 and "not in data/filings.ndjson" in capsys.readouterr().out


@pytest.mark.parametrize("when", ["", "2026-10-05", "2026-10-05 09:17:33"])
def test_the_evidence_says_when_its_bytes_were_retrieved(register, capsys, when):
    """Seat G on the second reading: a correction dated its evidence by the day it was made,
    so one capture could carry two retrieval times."""
    args = [a for a in _args(register) if a != RETRIEVED]
    args[args.index("--evidence-retrieved-at") + 1 : args.index("--evidence-retrieved-at") + 1] = [
        when
    ]
    assert correct.main([*args, "--now", "2025-02-26"]) == 1
    assert "when the evidence's bytes were retrieved" in capsys.readouterr().out


def _args(root: Path) -> list[str]:
    return [
        str(root),
        "--row",
        "fl:house-clerk:P:1",
        "--field",
        "filed_at",
        "--kind",
        "source",
        "--because",
        "why",
        "--evidence-url",
        URL,
        "--evidence-file",
        str(root / "evidence.zip"),
        "--decided-by",
        "the maintainer",
        "--evidence-retrieved-at",
        RETRIEVED,
    ]


HOLDERS = [
    {
        "id": f"oh:us:house:x00000{n}",
        "offices": [{"id": f"of:us:house-xx0{n}:2025", "term_start": "2025-01-03"}],
    }
    for n in (1, 2, 3)
]
HOLDERS[2]["offices"] = [{"id": "of:us:house-xx03:2023", "term_start": "2023-01-03"}]
OFFICES = [
    {"id": "of:us:house-xx01:2025", "term_start": "2025-01-03"},
    {"id": "of:us:house-xx02:2025", "term_start": "2025-01-03"},
    {"id": "of:us:house-xx03:2023", "term_start": "2023-01-03"},
]
FILING = dict(ROW, office_id="of:us:house-xx01:2025")
TRADES = [
    {
        "id": f"tx:house-clerk:1:00{n}",
        "filing_id": "fl:house-clerk:P:1",
        "officeholder_id": "oh:us:house:x000001",
    }
    for n in (1, 2)
]


@pytest.fixture
def attributed(register):
    """The register with officeholders, offices and the filing's two transactions."""
    for name, rows in (
        ("officeholders", HOLDERS),
        ("offices", OFFICES),
        ("filings", [FILING]),
        ("transactions", TRADES),
    ):
        text = "".join(correct.canonical(r) for r in rows)
        (register / "data" / f"{name}.ndjson").write_text(text, encoding="utf-8")
    for args in (
        ["add", "-A"],
        ["-c", "user.email=t@example.com", "-c", "user.name=t", "commit", "-q", "-m", "q"],
    ):
        subprocess.run(["git", "-C", str(register), *args], check=True, capture_output=True)
    return register


def rows(root: Path, name: str) -> dict[str, dict]:
    text = (root / "data" / f"{name}.ndjson").read_text("utf-8")
    return {json.loads(line)["id"]: json.loads(line) for line in text.splitlines()}


def test_an_attribution_moves_whole_or_not_at_all(attributed):
    """Seat C on the second reading (R-3): moving a filing's officeholder left its office and
    its trades with the first officeholder, so one person's page showed the report and
    another's the trades. The office and every trade now move with it, each a correction of
    its own citing the same evidence, and the gate and the joins pass."""
    args = [a if a != "filed_at" else "officeholder_id" for a in _args(attributed)]
    assert correct.main([*args, "--now", "oh:us:house:x000002"]) == 0
    filing = rows(attributed, "filings")["fl:house-clerk:P:1"]
    assert (filing["officeholder_id"], filing["office_id"]) == (
        "oh:us:house:x000002",
        "of:us:house-xx02:2025",
    )
    assert {t["officeholder_id"] for t in rows(attributed, "transactions").values()} == {
        "oh:us:house:x000002"
    }
    moved = {(c["row_id"], c["field"]) for c in changes(attributed)}
    assert moved == {
        ("fl:house-clerk:P:1", "officeholder_id"),
        ("fl:house-clerk:P:1", "office_id"),
        ("tx:house-clerk:1:001", "officeholder_id"),
        ("tx:house-clerk:1:002", "officeholder_id"),
    }
    assert len({c["capture"]["content_hash"] for c in changes(attributed)}) == 1
    assert gate.main([str(attributed)]) == 0
    assert schemas.joins(attributed) == []


def test_a_trade_never_moves_alone_and_no_office_no_move(attributed, capsys):
    args = [a for a in _args(attributed)]
    trade = [*args]
    trade[trade.index("--row") + 1] = "tx:house-clerk:1:001"
    trade[trade.index("--field") + 1] = "officeholder_id"
    assert correct.main([*trade, "--now", "oh:us:house:x000002"]) == 1
    assert "a transaction's officeholder is its filing's" in capsys.readouterr().out
    elsewhere = [a if a != "filed_at" else "officeholder_id" for a in args]
    assert correct.main([*elsewhere, "--now", "oh:us:house:x000003"]) == 1
    assert "holds 0 offices of the Congress" in capsys.readouterr().out
    assert not (attributed / "data" / "changes.ndjson").exists()


# ---- the Council's third reading of S.1b ---------------------------------------------------

PDF = b"%PDF the Clerk's document, as the maintainer holds it"
PDF_SHA = __import__("hashlib").sha256(PDF).hexdigest()
DOC_URL = "https://disclosures-clerk.house.gov/public_disc/ptr-pdfs/2025/1.pdf"
TX = {"id": "tx:house-clerk:1:001", "filing_id": "fl:house-clerk:P:1", "asset": "A Trust FBO X"}
HOLDER = {
    "id": "oh:us:house:x000001",
    "offices": [
        {"id": "of:us:house-xx01:2025", "seat": "XX01", "term_start": "2025-01-03"},
        {"id": "of:us:house-xx02:2025", "seat": "XX02", "term_start": "2025-01-03"},
    ],
}


@pytest.fixture
def ledger(tmp_path, monkeypatch):
    """A repository whose published filing was read from a document, with two transactions."""
    (tmp_path / "data").mkdir()
    (tmp_path / "tools").mkdir()
    shutil.copy(ROOT / "SOURCES.md", tmp_path / "SOURCES.md")
    shutil.copy(ROOT / "tools" / "check-aggregator-sole.py", tmp_path / "tools")
    filing = dict(
        ROW,
        office_id="of:us:house-xx01:2025",
        source={"url": DOC_URL, "retrieved_at": RETRIEVED, "content_hash": PDF_SHA},
    )
    for name, rows in (
        ("filings", [filing]),
        ("transactions", [TX, dict(TX, id="tx:house-clerk:1:002", asset="Other")]),
        ("officeholders", [HOLDER]),
    ):
        (tmp_path / "data" / f"{name}.ndjson").write_text(
            "".join(correct.canonical(r) for r in rows), encoding="utf-8"
        )
    for args in (
        ["init", "-q", "-b", "published"],
        ["add", "-A"],
        ["-c", "user.email=t@example.com", "-c", "user.name=t", "commit", "-q", "-m", "p"],
    ):
        subprocess.run(["git", "-C", str(tmp_path), *args], check=True, capture_output=True)
    (tmp_path / "1.pdf").write_bytes(PDF)
    monkeypatch.setenv("OATH_PUBLISHED_REF", "published")
    return tmp_path


def fix(root: Path, row: str, field: str, *extra: str) -> int:
    return correct.main(
        [
            str(root),
            "--row",
            row,
            "--field",
            field,
            "--because",
            "The report reads so.",
            "--evidence-url",
            DOC_URL,
            "--evidence-file",
            str(root / "1.pdf"),
            "--evidence-retrieved-at",
            RETRIEVED,
            "--decided-by",
            "the maintainer",
            "--decided-at",
            "2026-10-06T12:00:00Z",
            *extra,
        ]
    )


def test_a_filed_document_is_cited_by_its_hash_and_never_kept(ledger, capsys):
    """Seat B on the third reading (N1): a document can carry the names of private people; a
    kept copy would outlast the Clerk's withdrawal or redaction of it, and the gate would
    refuse its removal. It is cited by its URL, time and SHA-256, and a kept PDF fails."""
    assert (
        fix(ledger, "fl:house-clerk:P:1", "filed_at", "--now", "2025-02-26", "--kind", "source")
        == 0
    )
    assert "never kept" in capsys.readouterr().out
    (change,) = changes(ledger)
    assert change["capture"]["content_hash"] == PDF_SHA
    assert not (ledger / "data" / "captures").exists()
    assert gate.main([str(ledger)]) == 0
    kept = ledger / "data" / "captures" / "sha256"
    kept.mkdir(parents=True)
    (kept / f"{PDF_SHA}.pdf").write_bytes(PDF)
    assert gate.main([str(ledger)]) == 1, "a kept filed document fails"


@pytest.mark.parametrize(
    "url, name, body, kept",
    [
        ("https://clerk.house.gov/xml/lists/MemberData.xml", "roster.xml", b"<x/>", True),
        (
            "https://disclosures-clerk.house.gov/public_disc/financial-pdfs/2025FD.zip",
            "2025FD.zip",
            b"PK\x03\x04",
            True,
        ),
        (
            "https://efdsearch.senate.gov/search/view/ptr/abc/",
            "report.html",
            b"<p>a row</p>",
            False,
        ),
        (
            "https://disclosures-clerk.house.gov/public_disc/ptr-pdfs/2025/1",
            "evidence.bin",
            PDF,
            False,
        ),
    ],
)
def test_only_the_roster_and_the_index_are_kept_whatever_a_file_is_called(
    ledger, url, name, body, kept
):
    """Seat B on the fourth reading (F2): "a filed document is never kept" was tested by a
    ".pdf" suffix, so a report served from a URL that does not end .pdf, or under any other
    file name, was kept whole and then required to be kept for good. The register keeps the two
    captures the adapter fetches, the Clerk's roster and a filing year's index, by what the URL
    is; everything else is cited by its fingerprint, and a kept file whose bytes are a PDF
    fails whatever it is called."""
    (ledger / name).write_bytes(body)
    assert (
        correct.main(
            [
                str(ledger),
                "--row",
                "fl:house-clerk:P:1",
                "--field",
                "filed_at",
                "--now",
                "2025-02-26",
                "--kind",
                "source",
                "--because",
                "The source reads so.",
                "--evidence-url",
                url,
                "--evidence-file",
                str(ledger / name),
                "--evidence-retrieved-at",
                RETRIEVED,
                "--decided-by",
                "the maintainer",
                "--decided-at",
                "2026-10-06T12:00:00Z",
            ]
        )
        == 0
    )
    folder = ledger / "data" / "captures" / "sha256"
    assert folder.is_dir() is kept, url
    assert gate.main([str(ledger)]) == 0, "the gate honours what the tool wrote"
    if not kept:
        folder.mkdir(parents=True)
        (folder / f"{hashlib.sha256(body).hexdigest()}{Path(name).suffix}").write_bytes(body)
        assert gate.main([str(ledger)]) == 1, "keeping it anyway fails"


def test_the_filers_own_text_is_corrected_by_its_hash(ledger):
    """Seat B on the third reading (N2): a line a filer has the Clerk remove, a private
    person's name among them, is not kept in the register's changes; the correction names what
    the asset was by its SHA-256, and the gate honours it by that hash."""
    assert fix(ledger, "tx:house-clerk:1:001", "asset", "--now", "A Trust", "--kind", "source") == 0
    (change,) = changes(ledger)
    assert "was" not in change and "A Trust FBO X" not in json.dumps(change)
    assert change["was_sha256"] == __import__("hashlib").sha256(b'"A Trust FBO X"').hexdigest()
    assert gate.main([str(ledger)]) == 0
    loaded = schemas.load_schemas(ROOT)
    assert (
        schemas.validate(change, loaded["change.schema.json"], loaded, "change.schema.json") == []
    )


def test_rows_a_report_lists_are_accepted_by_count_citing_its_own_bytes(ledger, capsys):
    """Seat C on the third reading (N-2): rows a later reading finds in the very bytes a
    report's rows were published from enter only by the maintainer's decision that the report
    lists that many; the decision cites those bytes, and its kind is register."""
    row = "fl:house-clerk:P:1"
    assert fix(ledger, row, "transactions", "--now", "3", "--json", "--kind", "source") == 1
    assert fix(ledger, row, "transactions", "--now", "2", "--json", "--kind", "register") == 1
    assert "more than the 2 published" in capsys.readouterr().out
    (ledger / "1.pdf").write_bytes(b"%PDF other bytes")
    assert fix(ledger, row, "transactions", "--now", "3", "--json", "--kind", "register") == 1
    assert "source.content_hash" in capsys.readouterr().out
    (ledger / "1.pdf").write_bytes(PDF)
    before = {p.name: p.read_bytes() for p in (ledger / "data").glob("*.ndjson")}
    assert fix(ledger, row, "transactions", "--now", "3", "--json", "--kind", "register") == 0
    (change,) = changes(ledger)
    assert (change["field"], change["was"], change["now"]) == ("transactions", 2, 3)
    after = {p.name: p.read_bytes() for p in (ledger / "data").glob("*.ndjson")}
    assert {k: v for k, v in after.items() if k != "changes.ndjson"} == before, "nothing moves"
    assert gate.main([str(ledger)]) == 0


def test_a_list_or_an_office_its_holder_does_not_hold_is_refused(ledger, capsys):
    """Seat C on the third reading (N-7): a correction moves one fact, a value; and an office
    moves only to one its officeholder holds, or with its attribution."""
    code = fix(ledger, HOLDER["id"], "offices", "--now", "[]", "--json", "--kind", "register")
    assert code == 1 and "moves one fact, a value" in capsys.readouterr().out
    args = ["--kind", "register"]
    assert (
        fix(ledger, "fl:house-clerk:P:1", "office_id", "--now", "of:us:house-xx09:2025", *args) == 1
    )
    assert "not an office" in capsys.readouterr().out
    assert (
        fix(ledger, "fl:house-clerk:P:1", "office_id", "--now", "of:us:house-xx02:2025", *args) == 0
    )


def test_a_dry_run_says_what_it_would_keep_and_writes_nothing(register, capsys):
    """Seat G on the third reading (R3-10)."""
    assert run(register, "--now", "2025-02-26", "--dry-run") == 0
    out = capsys.readouterr().out
    assert "would be kept" in out and "kept at" not in out.replace("would be kept at", "")
    assert not (register / "data" / "changes.ndjson").exists()
    assert not (register / "data" / "captures").exists()


def test_a_correction_already_recorded_is_refused(register, capsys):
    """The Council's fourth reading of S.1b (Seat C): the rule that a change id already in the
    ledger is refused had no failing input. Twice the same correction, and the second is refused
    before it writes, so a change row is never written over."""
    assert run(register, "--now", "2025-02-26") == 0
    (recorded,) = changes(register)
    assert run(register, "--now", "2025-02-27") == 1, (
        "the same row, fact and decision time: the id is the one already recorded"
    )
    assert f"{recorded['id']} is already recorded" in capsys.readouterr().out
    assert changes(register) == [recorded], "and the ledger is what it was"
