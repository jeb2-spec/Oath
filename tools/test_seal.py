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

    def o(who, state, before=0):
        swore = {"dated before this Congress's swearing-in": before} if before else {}
        return {"officeholder_id": who, "state": state, "not_evaluated": swore}

    outcomes = [
        o("a", "not read"),
        o("a", "not read"),
        o("b", "not read"),
        o("b", "evaluated", before=2),
        o("c", "evaluated"),
    ]
    assert seal.reach(outcomes) == {"paper_only": 1, "some_paper": 1, "before_swearing_in": 1}


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


def test_rows_kept_for_a_member_who_left_are_counted_in_the_sealed_sentence(tmp_path):
    """NEXT.md S.1b. A build that carries a departed Member's rows seals a sentence that says
    so and carries the register's totals, or the seal refuses it."""
    import json

    seal = load()
    verify = seal.load_verify(HERE)
    root = copy_register(tmp_path)
    holders = root / "data" / "officeholders.ndjson"
    kept = json.loads(holders.read_text("utf-8").splitlines()[0])
    kept["id"] = "oh:us:example:example"
    holders.write_text(holders.read_text("utf-8") + json.dumps(kept) + "\n", encoding="utf-8")
    path, run = the_run(root)
    run["carried"] = {"officeholders": 1, "offices": 0, "filings": 0, "transactions": 0}
    path.write_text(json.dumps(run) + "\n", encoding="utf-8")
    meta = json.loads((ROOT / "data" / "meta.json").read_text("utf-8"))
    meta["rows"] = verify.row_counts(root)
    text = seal.derive_state(root, meta)
    assert seal.state_text_lacks({**meta, "state": text}, run) == ""
    assert "the rows of 1 officeholder the roster no longer lists" in text
    assert f"so it holds {meta['rows']['data/officeholders.ndjson']:,} officeholders" in text
    assert "nothing published was removed" in text


def test_a_closed_year_seals_a_sentence_that_says_it_is_closed(tmp_path):
    import json

    seal = load()
    verify = seal.load_verify(HERE)
    root = copy_register(tmp_path)
    path, run = the_run(root)
    reason = (
        "filing year 2025 is of the 119th Congress, and the roster this build read lists the 120th"
    )
    run["congress"] = {"filing_year": 119, "roster": 120, "closed": True}
    run["counts"] = dict.fromkeys(("seats", "filled", "vacant", "accepted", "quiet"), 0)
    run["counts"]["rejected"] = 2
    run["documents"] = {"read": 0, "transactions": 0}
    run["rejected_by_reason"] = {reason: 2}
    path.write_text(json.dumps(run) + "\n", encoding="utf-8")
    meta = json.loads((ROOT / "data" / "meta.json").read_text("utf-8"))
    meta["rows"] = verify.row_counts(root)
    text = seal.derive_state(root, meta)
    assert seal.state_text_lacks({**meta, "state": text}, run) == ""
    assert text.startswith(
        "Filing year 2025, of the 119th Congress, is closed: the roster the register reads "
        "lists the 120th"
    )
    assert "0 seats" not in text and f"2 because {reason}" in text
