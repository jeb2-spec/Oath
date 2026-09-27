"""The §14 gate, proven red before green. INVARIANTS.md §14; CHARTER Vow V.

Each test makes the change the gate exists to refuse and requires the refusal, and each
lets through what a later build legitimately does: fill a null, add a field, add a term,
add a change row at the end, keep a capture. The published side of the end-to-end cases is
a real git ref in a throwaway repository, because that is what the gate reads in CI.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "check_removals", ROOT / "tools" / "check-removals.py"
)
gate = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(gate)

FILINGS = "data/filings.ndjson"
CHANGES = "data/changes.ndjson"
FRAME = "Presence in the register is not evidence of wrongdoing."


def filing(**extra) -> dict:
    row = {
        "id": "fl:house-clerk:P:1",
        "officeholder_id": "oh:us:house:x000001",
        "office_id": "of:us:house-xx01:2025",
        "extraction_confidence": None,
        "notes": None,
        "source": {"url": "u", "retrieved_at": "2026-01-01T00:00:00Z", "content_hash": None},
    }
    row.update(extra)
    return row


def test_a_published_row_that_disappears_is_refused():
    fails = gate.problems(FILINGS, [], [filing()])
    assert fails and "gone from the tree" in fails[0]


def test_a_fact_changed_in_place_is_refused():
    moved = filing(officeholder_id="oh:us:house:x000002")
    fails = gate.problems(FILINGS, [moved], [filing()])
    assert fails and "officeholder_id" in fails[0]


def test_a_removed_key_is_refused():
    row = filing()
    del row["office_id"]
    fails = gate.problems(FILINGS, [row], [filing()])
    assert fails and "office_id: " in fails[0] and "gone" in fails[0]


def test_facts_accrue_a_null_filled_a_key_added_a_term_added():
    now = filing(extraction_confidence="structured", asset_code="ST")
    assert gate.problems(FILINGS, [now], [filing()]) == []
    holder = {"id": "oh:1", "offices": [{"id": "of:1", "term_end": None}]}
    grown = {"id": "oh:1", "offices": [{"id": "of:1", "term_end": "2027-01-03"}, {"id": "of:2"}]}
    assert gate.problems("data/officeholders.ndjson", [grown], [holder]) == []
    shrunk = {"id": "oh:1", "offices": []}
    assert gate.problems("data/officeholders.ndjson", [shrunk], [holder])


def test_a_filled_fact_cannot_be_emptied_again():
    fails = gate.problems(FILINGS, [filing()], [filing(extraction_confidence="structured")])
    assert fails and "extraction_confidence" in fails[0]


def test_every_published_fact_stays_the_time_read_the_notes_and_the_hash_among_them():
    """The adapter carries a published row byte for byte, so nothing it carries may move: a
    re-read time, the notes (which carry the filer's own words) and the hash of the bytes it
    was read from are facts too (the Council's reading of S.1b). Each is named as the one
    fact that moved, so the test cannot pass on a gate that returns anything non-empty."""
    before = filing(source={"url": "u", "retrieved_at": "t1", "content_hash": "a"}, notes="n")
    for now, where in (
        (
            filing(source={"url": "u", "retrieved_at": "t2", "content_hash": "a"}, notes="n"),
            "source.retrieved_at",
        ),
        (
            filing(source={"url": "u", "retrieved_at": "t1", "content_hash": "b"}, notes="n"),
            "source.content_hash",
        ),
        (
            filing(source={"url": "u", "retrieved_at": "t1", "content_hash": None}, notes="n"),
            "source.content_hash",
        ),
        (
            filing(source={"url": "u", "retrieved_at": "t1", "content_hash": "a"}, notes="m"),
            "notes",
        ),
    ):
        fails = gate.problems(FILINGS, [now], [before])
        assert isinstance(fails, list) and len(fails) == 1, fails
        assert f"fl:house-clerk:P:1 {where}: " in fails[0], fails


RIGHT = {
    "id": "ch:corrected:fl:house-clerk:P:1:officeholder_id:2026-10-06T12:00:00Z",
    "change": "corrected",
    "row_id": "fl:house-clerk:P:1",
    "field": "officeholder_id",
    "was": "oh:us:house:x000001",
    "now": "oh:us:house:x000002",
    "kind": "register",
    "because": "The document's header names the other Member.",
    "decided_by": "the maintainer",
    "decided_at": "2026-10-06T12:00:00Z",
    "capture": {"url": "https://disclosures-clerk.house.gov/public_disc/ptr-pdfs/2025/1.pdf"},
}
PRIMARY = {"disclosures-clerk.house.gov"}


def test_a_persons_correction_lets_exactly_its_move_through():
    moved = filing(officeholder_id="oh:us:house:x000002")
    corrected, fails = gate.corrections([RIGHT], PRIMARY)
    assert fails == [] and gate.problems(FILINGS, [moved], [filing()], corrected) == []
    for wrong in (dict(RIGHT, now="oh:us:house:x000003"), dict(RIGHT, field="office_id")):
        assert gate.problems(FILINGS, [moved], [filing()], gate.corrections([wrong], PRIMARY)[0])
    elsewhere = filing(officeholder_id="oh:us:house:x000002", office_id="of:other")
    assert gate.problems(FILINGS, [elsewhere], [filing()], corrected), "one move, not two"


def test_a_correction_without_what_makes_it_one_is_honoured_for_nothing():
    """Seat C on the second reading (R-4): a hand-written correction citing a blog, with no
    reason and no one who decided, moved a filing and the gate said OK. INVARIANTS.md §14: a
    supersession without a primary-source citation fails."""
    for lacking, says in (
        ({"capture": {"url": "https://example.com/blog"}}, "primary"),
        ({"capture": {"url": "http://disclosures-clerk.house.gov/x"}}, "primary"),
        ({"because": " "}, "a reason"),
        ({"decided_by": ""}, "who decided"),
        ({"kind": "opinion"}, "a kind"),
        ({"decided_at": None}, "when it was decided"),
    ):
        corrected, fails = gate.corrections([dict(RIGHT, **lacking)], PRIMARY)
        assert corrected == set() and len(fails) == 1 and says in fails[0], (lacking, fails)
    moved = filing(officeholder_id="oh:us:house:x000002")
    blog = gate.corrections([dict(RIGHT, capture={"url": "https://example.com/blog"})], PRIMARY)
    assert gate.problems(FILINGS, [moved], [filing()], blog[0]), "and the move it names fails"


def test_the_changes_file_only_grows_at_its_end_byte_for_byte():
    one = json.dumps({"id": "ch:1", "row_id": "oh:1"}, sort_keys=True) + "\n"
    two = json.dumps({"id": "ch:2", "row_id": "oh:2"}, sort_keys=True) + "\n"
    assert gate.appended(one + two, one) == []
    assert gate.appended(two + one, one), "a published row moved"
    assert gate.appended(json.dumps({"row_id": "oh:1", "id": "ch:1"}) + "\n" + two, one), (
        "the same row re-serialised is not the same bytes"
    )
    edited = {"id": "ch:1", "row_id": "oh:1", "change": "not listed"}
    assert gate.problems(CHANGES, [dict(edited, change="listed again")], [edited])


def repo_with(tmp_path: Path, files: dict[str, str | bytes]) -> Path:
    """A throwaway repository whose branch `published` holds `files`."""
    for rel, body in files.items():
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        if isinstance(body, bytes):
            (tmp_path / rel).write_bytes(body)
        else:
            (tmp_path / rel).write_text(body, encoding="utf-8")
    for args in (
        ["init", "-q", "-b", "published"],
        ["add", "-A"],
        ["-c", "user.email=t@example.com", "-c", "user.name=t", "commit", "-q", "-m", "p"],
    ):
        subprocess.run(["git", "-C", str(tmp_path), *args], check=True, capture_output=True)
    return tmp_path


def lines(*rows: dict) -> str:
    return "".join(json.dumps(r, sort_keys=True) + "\n" for r in rows)


def change(capture: bytes) -> dict:
    return {
        "id": "ch:not-listed:oh:1:2026-01-01T00:00:00Z",
        "row_id": "oh:1",
        "rows": "officeholders",
        "change": "not listed",
        "capture": {
            "url": "https://clerk.house.gov/xml/lists/MemberData.xml",
            "retrieved_at": "2026-01-01T00:00:00Z",
            "content_hash": hashlib.sha256(capture).hexdigest(),
        },
        "frame": FRAME,
    }


def test_the_gate_reads_the_published_ref(tmp_path, monkeypatch, capsys):
    root = repo_with(tmp_path, {FILINGS: lines(filing(), filing(id="fl:house-clerk:P:2"))})
    monkeypatch.setenv("OATH_PUBLISHED_REF", "published")
    assert gate.main([str(root)]) == 0
    (root / FILINGS).write_text(lines(filing()), encoding="utf-8")
    assert gate.main([str(root)]) == 1
    assert "fl:house-clerk:P:2 is published, and gone" in capsys.readouterr().out


def test_a_kept_capture_stays_is_named_by_its_hash_and_backs_every_change(tmp_path, monkeypatch):
    roster = b"<MemberData>the roster as read</MemberData>"
    sha = hashlib.sha256(roster).hexdigest()
    kept = f"data/captures/sha256/{sha}.xml"
    root = repo_with(tmp_path, {kept: roster, CHANGES: lines(change(roster))})
    monkeypatch.setenv("OATH_PUBLISHED_REF", "published")
    assert gate.main([str(root)]) == 0
    (root / kept).write_bytes(roster + b" ")
    assert gate.main([str(root)]) == 1, "altered"
    (root / kept).unlink()
    assert gate.main([str(root)]) == 1, "gone, and the change row cites it"
    (root / kept).write_bytes(roster)
    (root / "data" / "captures" / "sha256" / "not-a-hash.xml").write_bytes(b"x")
    assert gate.main([str(root)]) == 1, "not named by its hash"


def test_an_unreadable_ref_fails_rather_than_passes(tmp_path, monkeypatch):
    root = repo_with(tmp_path, {FILINGS: lines(filing())})
    monkeypatch.setenv("OATH_PUBLISHED_REF", "no-such-ref")
    assert gate.main([str(root)]) == 1


def test_the_repository_keeps_every_published_row():
    assert gate.main([str(ROOT)]) == 0


# ---- each guard has a failing input (the Council's third reading of S.1b, Seat C, N-5) -----


def test_a_correction_that_names_no_fact_is_honoured_for_nothing():
    unnamed = {k: v for k, v in RIGHT.items() if k != "field"}
    corrected, fails = gate.corrections([unnamed], PRIMARY)
    assert corrected == set() and "the fact it is about" in fails[0]


def test_a_correction_that_lacks_what_makes_it_one_fails_by_itself(tmp_path, monkeypatch, capsys):
    """Whether or not it moved anything: a row of the changes that cannot stand fails."""
    tools = tmp_path / "tools"
    tools.mkdir()
    (tools / "check-aggregator-sole.py").write_bytes(
        (ROOT / "tools" / "check-aggregator-sole.py").read_bytes()
    )
    root = repo_with(
        tmp_path,
        {"SOURCES.md": (ROOT / "SOURCES.md").read_text("utf-8"), FILINGS: lines(filing())},
    )
    monkeypatch.setenv("OATH_PUBLISHED_REF", "published")
    (root / CHANGES).write_text(lines(dict(RIGHT, kind="opinion", now=RIGHT["was"])), "utf-8")
    assert gate.main([str(root)]) == 1
    assert "a correction without a kind" in capsys.readouterr().out


def test_without_the_registry_no_correction_is_honoured(tmp_path, monkeypatch, capsys):
    """No SOURCES.md, or no reader for it, and nothing is trusted: the gate honours no
    correction rather than every one."""
    root = repo_with(tmp_path, {FILINGS: lines(filing())})
    monkeypatch.setenv("OATH_PUBLISHED_REF", "published")
    assert gate.primary_hosts(root) == set()
    (root / FILINGS).write_text(lines(filing(officeholder_id=RIGHT["now"])), "utf-8")
    (root / CHANGES).write_text(lines(RIGHT), "utf-8")
    assert gate.main([str(root)]) == 1
    out = capsys.readouterr().out
    assert "on a host SOURCES.md registers as primary" in out and "x000001" in out


def test_a_change_whose_capture_the_register_never_kept_fails(tmp_path, monkeypatch):
    """The Council's fourth reading of S.1b (Seat C): the rule that every change row's roster or
    index capture is kept had one test, which deleted a kept file, and a different rule caught
    that first. A change citing a capture the register never kept at all fails by itself."""
    roster = b"<MemberData>the roster as read</MemberData>"
    root = repo_with(tmp_path, {CHANGES: lines(change(roster))})
    monkeypatch.setenv("OATH_PUBLISHED_REF", "published")
    assert gate.main([str(root)]) == 1, "nothing under data/captures/sha256 backs it"
    kept = root / "data" / "captures" / "sha256" / f"{hashlib.sha256(roster).hexdigest()}.xml"
    kept.parent.mkdir(parents=True, exist_ok=True)
    kept.write_bytes(roster)
    assert gate.main([str(root)]) == 0, "and it passes once the register keeps it"
