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
# The groups as the adapter writes them, from the register's own set-aside rows: the held ones are
# one condition each, and none is the bare "surname matches a sitting member" that this fixture
# carried for two passes. An exact-key lookup against that shorter key silently returned nothing,
# so the held figure left the sealed sentence and the guard that required it went quiet with it: a
# fixture one shape behind the code hid both (the Council's fifth reading of S.1b, Seats A, C, D).
HELD = "surname matches a sitting member but the given names differ; "
DECIDES = "a human decides this one"
RUN = {
    "counts": {"quiet": 11, "rejected": 1737, "attributed_by_document": 101},
    "documents": {"read": 409},
    "rejected_by_reason": {
        "no sitting member has this name; the row is a candidate or a former member": 1575,
        HELD + DECIDES: 127,
        HELD + "the document carries no Filing ID line (scanned paper, or a form that prints "
        f"none) and cannot confirm the filer; {DECIDES}": 28,
        HELD + "the document prints a Status other than Member for the filer the document names, "
        f"at the seat it prints; the header does not attribute the row to the seat's member; "
        f"{DECIDES}": 6,
        HELD + "the index dates the filing before the swearing-in for this Congress that the "
        f"roster records; the roster does not say who held the seat before that date, so the "
        f"register does not; {DECIDES}": 1,
    },
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


ROOT = HERE.parent


def test_the_derived_state_carries_every_figure_the_seal_checks():
    """The scheduled refresh seals with --derive-state; the sentence it writes must pass the
    same check a hand-written one does, on the register as it stands."""
    import json

    seal = load()
    verify = seal.load_verify(HERE)
    meta = json.loads((ROOT / "data" / "meta.json").read_text("utf-8"))
    meta["rows"] = verify.row_counts(ROOT)
    text = seal.derive_state(ROOT, meta)
    for run in seal.current_runs(ROOT):
        assert seal.state_text_lacks({**meta, "state": text}, run) == ""
    assert text == seal.derive_state(ROOT, meta), "the same tree gives the same sentence"
    findings = meta["rows"].get("data/findings.ndjson", 0)
    assert f"The ledger holds {findings:,} Finding" in text
    assert text.endswith("Presence in this register is not evidence of wrongdoing.")


def test_a_register_without_signals_says_so(tmp_path):
    seal = load()
    (tmp_path / "data").mkdir()
    text = seal.derive_state(tmp_path, {"rows": {}})
    assert "No Signal is defined, so no Finding exists." in text


def test_the_ledger_sentence_counts_corrections_once_there_are_any():
    seal = load()
    fired = {"superseded_by": None, "evidence": {"after": 2}}
    assert seal.ledger_sentence([fired, fired]) == "The ledger holds 2 Findings."
    corrected = [dict(fired, superseded_by="fn:1:c1"), fired]
    assert seal.ledger_sentence(corrected) == (
        "The ledger holds 2 Findings, 1 of them superseded by a correction and kept."
    )
    withdrawn = [
        dict(fired, superseded_by="fn:1:c1"),
        {"superseded_by": None, "evidence": {"after": 0}},
    ]
    assert seal.ledger_sentence(withdrawn) == (
        "The ledger holds 2 Findings, 1 of them superseded by a correction and kept, and 1 a "
        "correction recording that the Signal no longer fires on a report."
    )


def test_the_congress_is_named_with_its_own_ordinal():
    seal = load()
    assert [seal.ordinal(n) for n in (119, 120, 121, 122, 123, 111, 112, 113)] == [
        "119th",
        "120th",
        "121st",
        "122nd",
        "123rd",
        "111th",
        "112th",
        "113th",
    ]


def test_held_rows_are_counted_by_why_they_wait():
    seal = load()
    held = "surname matches a sitting member (Example, Ann, CA12) but the given names differ"
    rows = [
        {"reason": held + "; a human decides this one", "source_row": {"state_dst": "TX01"}},
        {"reason": held + "; a human decides this one", "source_row": {"state_dst": "TX02"}},
        {"reason": held + "; the document carries no Filing ID line", "source_row": {}},
        {"reason": "no sitting member has this name", "source_row": {}},
    ]
    assert seal.held_clause(rows) == (
        "2 at a seat other than the member's, and 1 whose documents carry no Filing ID line"
    )


def test_who_a_signal_cannot_reach_is_counted_by_officeholder():
    seal = load()

    def o(who, state, before=0, report="fl:read"):
        swore = {"dated before this Congress's swearing-in": before} if before else {}
        return {
            "officeholder_id": who,
            "filing_id": report,
            "state": state,
            "not_evaluated": swore,
        }

    outcomes = [
        o("a", "not read"),
        o("a", "not read"),
        o("b", "not read"),
        o("b", "evaluated", before=2),
        o("c", "evaluated"),
    ]
    assert seal.reach(outcomes) == {
        "unread_only": 1,
        "some_unread": 1,
        "not_fetched": 0,
        "before_swearing_in": 1,
    }
    # A report the register has not fetched is not scanned paper, and never counted as it (the
    # Council's fourth reading of S.1b, Seat F): d's one report is unfetched, so d is neither
    # "all scanned paper" nor "some".
    filings = [
        {"id": "fl:read", "source": {"content_hash": "0" * 64}},
        {"id": "fl:unfetched", "source": {"content_hash": None}},
    ]
    with_unfetched = [*outcomes, o("d", "not read", report="fl:unfetched")]
    assert seal.reach(with_unfetched, filings) == {
        "unread_only": 1,
        "some_unread": 1,
        "not_fetched": 1,
        "before_swearing_in": 1,
    }


def test_the_seal_points_at_the_anchor_and_never_seals_its_state():
    """A proof is completed after the seal, so the sealed meta names where the proof lives
    and says nothing about whether Bitcoin holds it yet."""
    pointer = load().anchor_pointer("0006-house-2025")
    assert pointer["proof"] == "data/anchors/0006-house-2025.manifest.ots"
    assert pointer["manifest"] == "data/anchors/0006-house-2025.manifest"
    assert pointer["ledger"] == "ANCHORS.md"
    assert "state" not in pointer and "block" not in pointer


def copy_register(tmp_path: Path) -> Path:
    import shutil

    shutil.copytree(
        ROOT / "data", tmp_path / "data", ignore=shutil.ignore_patterns("cache", "anchors")
    )
    return tmp_path


def the_run(root: Path) -> tuple[Path, dict]:
    import json

    (path,) = (root / "data" / "adapter-runs").glob("house-fd-2025-*.ndjson")
    return path, json.loads(path.read_text("utf-8"))


def test_changes_are_counted_by_kind_and_never_by_anyone_s_rows(tmp_path):
    """NEXT.md S.1b and the Council's reading of it: a build whose register records changes
    seals a sentence that says so, in totals by kind; a count of one Member's filings or
    transactions beside their leaving is never in it."""
    import json

    seal = load()
    verify = seal.load_verify(HERE)
    root = copy_register(tmp_path)
    path, run = the_run(root)

    def change(kind: str, n: int, **more) -> dict:
        at = f"2026-10-0{n}T09:17:00Z"
        return {
            "id": f"ch:{kind}:{n}",
            "row_id": f"fl:x:{n}",
            "change": kind,
            "capture": {"retrieved_at": at},
            **more,
        }

    decision = {
        "decided_at": "2026-10-06T12:00:00Z",
        "decided_by": "the maintainer",
        "because": "b",
    }
    rows = [
        change("not listed", 1),
        change("read otherwise", 2),
        change("read otherwise", 3),
        *(change("corrected", n, **decision) for n in (4, 5, 6)),
    ]
    (root / "data" / "changes.ndjson").write_text(
        "".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8"
    )
    run["changes"] = {"not listed": 1}  # a run record a correction never rewrote (Seat C, N-8)
    path.write_text(json.dumps(run) + "\n", encoding="utf-8")
    meta = json.loads((ROOT / "data" / "meta.json").read_text("utf-8"))
    meta["rows"] = verify.row_counts(root)
    text = seal.derive_state(root, meta)
    assert seal.state_text_lacks({**meta, "state": text}, run) == ""
    assert (
        "3 changes later reads showed are recorded, each a row of its own citing the read, of "
        "these kinds: a row a later read no longer lists and a fact a later read states "
        "otherwise; 1 decision the maintainer recorded, correcting a published fact or recording "
        "that it stands, each citing the evidence."
    ) in text, "counted from the changes themselves, decisions as decisions"
    assert "1 no longer" not in text and "2 stated" not in text, (
        "no count by kind, which, small, is a count about one person (Seat C, N-9)"
    )
    assert text.startswith(
        "The register holds 441 offices, 439 officeholders, 1,197 filings and 7,346 "
        "transactions. A row it has published stays, gaining only facts it lacked;"
    ), "the register's totals, never one person's, and the rule it holds them by"
    assert "carried" not in text and "derive again" not in text


def test_the_congress_is_named_with_its_terms_and_nothing_leans_on_the_present(tmp_path):
    """A later reader needs the Congress's dates, not its number, and no "sitting" or "this
    Congress" (the Council's reading of S.1b, Seat G)."""
    import json

    seal = load()
    verify = seal.load_verify(HERE)
    root = copy_register(tmp_path)
    meta = json.loads((ROOT / "data" / "meta.json").read_text("utf-8"))
    meta["rows"] = verify.row_counts(root)
    text = seal.derive_state(root, meta)
    assert (
        "seats of the 119th Congress (terms from noon, 3 January 2025, to noon, 3 January 2027)"
    ) in text
    assert "the swearing-in the roster records for the 119th Congress" in text
    assert "this Congress" not in text and "sitting members" not in text, (
        "only the adapter's own reasons, quoted, say sitting, beside the roster's date"
    )
    assert seal.congress_named(2027).startswith("120th Congress (terms from noon, 3 January 2027")


def test_a_change_row_is_stamped_with_the_build_that_first_seals_it(tmp_path):
    import json

    seal = load()
    data = tmp_path / "data"
    data.mkdir()
    first = {"id": "ch:1", "build": "0005-house-2025"}
    second = {"id": "ch:2"}
    (data / "changes.ndjson").write_text(
        "".join(
            json.dumps(r, sort_keys=True, separators=(",", ":")) + "\n" for r in (first, second)
        ),
        encoding="utf-8",
    )
    before = (data / "changes.ndjson").read_text("utf-8").splitlines()[0]
    assert seal.stamp_changes(tmp_path, "0006-house-2025") == 1
    lines = (data / "changes.ndjson").read_text("utf-8").splitlines()
    assert lines[0] == before, "a stamped row is never touched again"
    assert json.loads(lines[1])["build"] == "0006-house-2025"
    assert seal.stamp_changes(tmp_path, "0007-house-2025") == 0


def test_a_closed_year_seals_a_sentence_that_says_the_register_closed_it(tmp_path):
    import json

    seal = load()
    verify = seal.load_verify(HERE)
    root = copy_register(tmp_path)
    path, run = the_run(root)
    reason = (
        "filing year 2025 is of the 119th Congress, whose terms ended at noon on 2027-01-03, and "
        "the roster this build read lists the 120th"
    )
    run["congress"] = {
        "filing_year": 119,
        "roster": 120,
        "closed": True,
        "closed_by": {"retrieved_at": "2027-01-11T09:17:05Z", "congress": 120},
    }
    run["counts"] = dict.fromkeys(("seats", "filled", "vacant", "filings", "quiet"), 0)
    run["counts"]["rejected"] = 2
    run["documents"] = {"read": 0, "transactions": 0}
    run["rejected_by_reason"] = {reason: 2}
    path.write_text(json.dumps(run) + "\n", encoding="utf-8")
    meta = json.loads((ROOT / "data" / "meta.json").read_text("utf-8"))
    meta["rows"] = verify.row_counts(root)
    text = seal.derive_state(root, meta)
    assert seal.state_text_lacks({**meta, "state": text}, run) == ""
    assert (
        "The register has closed filing year 2025 (the reports the Clerk's index lists under "
        "2025): they belong to the 119th Congress (terms from noon, 3 January 2025, to noon, 3 "
        "January 2027), whose terms ended under the Twentieth Amendment, section 1, and the "
        "Clerk's roster read 2027-01-11 listed the 120th."
    ) in text, "dated by the read that closed the year, never by the roster read now"
    assert "the roster the register reads" not in text and " now" not in text
    assert "gives the 119th Congress's offices the day their terms ended" in text
    assert "0 seats" not in text and f"2 because {reason}" in text


def test_a_different_file_that_reads_as_the_published_rows_is_its_own_kind():
    """The Council's fifth reading of S.1b (Seats C, D and F): the fifth pass made every file the
    Clerk serves that is not the one last seen a change row, whether or not its rows read
    otherwise. One kind of words then said of a replacement with an empty `differs` that the file
    reads otherwise, which the change row itself, and the page, say it does not."""
    seal = load()
    otherwise = {
        "id": "a",
        "change": "replaced",
        "differs": [{"row": "tx:x:1", "fields": ["asset"]}],
    }
    same = {"id": "b", "change": "replaced", "differs": []}
    said = seal.changes_sentence([otherwise])
    assert (
        "which reads otherwise" in said and "reads as the rows the register published" not in said
    )
    said = seal.changes_sentence([same])
    assert "reads as the rows the register published" in said
    assert "which reads otherwise" not in said, "the change row says the rows read the same"
    both = seal.changes_sentence([otherwise, same])
    assert "these kinds" in both and both.count("a different file") == 2


def test_a_state_that_lacks_the_changes_is_refused():
    """Seat G on the third reading (R3-4): the check read no change, so a sentence that left
    the maintainer's corrections out sealed."""
    seal = load()
    decision = {"change": "corrected", "decided_at": "t", "decided_by": "m", "because": "x"}
    changes = [
        {"id": "a", "change": "not listed"},
        {"id": "a2", "change": "read otherwise"},
        {"id": "b", **decision},
        {"id": "c", **decision},
    ]
    lacking = seal.state_text_lacks({"state": "Nothing about changes.", "rows": {}}, None, changes)
    assert "changes later reads showed 2" in lacking and "the maintainer's decisions 1" in lacking
    assert (
        seal.state_text_lacks({"state": "2 changes; 1 decision.", "rows": {}}, None, changes) == ""
    )
    # With one kind of read the sentence gives no count, so the seal requires none. It used to
    # demand one, and passed only because a standalone "1" happened to occur elsewhere in the
    # sentence (the Council's fifth reading of S.1b, Seat C).
    one_kind = [{"id": "a", "change": "not listed"}, {"id": "a2", "change": "not listed"}]
    assert "changes later reads showed" not in seal.state_text_lacks(
        {"state": "Nothing about changes.", "rows": {}}, None, one_kind
    )
    assert "of this kind" in seal.changes_sentence(one_kind)
    assert "2" not in seal.changes_sentence(one_kind), "no count beside one kind, at any count"


def test_held_rows_counts_every_group_whose_reason_begins_with_the_held_one():
    """The figure was looked up by an exact key the adapter stopped writing, so it read 0, the
    sealed sentence lost the aggregate, and the guard that required the figure skipped it because a
    zero figure is skipped: the lookup, the sentence and the check all went quiet together (the
    Council's fifth reading of S.1b, Seats A, C, D, E and F). The keys here are the ones the
    adapter really writes."""
    seal = load()
    assert seal.held_rows(RUN) == 162
    assert all(
        key.startswith(seal.HELD_REASON) for key in RUN["rejected_by_reason"] if "differ" in key
    )
    assert seal.held_rows({"rejected_by_reason": {}}) == 0
