"""Tests for tools/check-wanted.py: the wanted register says what it does not know."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _load():
    spec = importlib.util.spec_from_file_location("check_wanted", HERE / "check-wanted.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


wanted = _load()


def row(**over) -> dict:
    base = {
        "id": "wt:a-thing",
        "closes": "the-fee",
        "question": "Was the fee assessed on this report?",
        "today": "Nothing; the register holds no row about it.",
        "with_it": "The report could say whether the rule's own consequence followed.",
        "unit": "report",
        "joins_on": None,
        "holder": "House Committee on Ethics",
        "publicness": "unknown",
        "route": "Unknown; no route this project has established.",
        "candidates": [{"what": "The Committee's pages", "url": "https://example.invalid/"}],
        "verified": False,
        "check": "Read what the Committee publishes about late filing fees, and record the date.",
        "added": "2026-09-27",
    }
    base.update(over)
    return base


def site(tmp_path: Path, rows: list[dict]) -> list[str]:
    (tmp_path / "docs" / "wanted").mkdir(parents=True, exist_ok=True)
    (tmp_path / "docs" / "wanted" / "wanted.ndjson").write_text(
        "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8"
    )
    return [str(tmp_path)]


def every_group(extra: list[dict] | None = None) -> list[dict]:
    rows = [row(id=f"wt:{g}", closes=g) for g in wanted.GROUPS]
    return rows + (extra or [])


def test_a_row_may_not_say_a_thing_is_public_until_somebody_has_read_it(tmp_path, capsys):
    """The rule the file exists for. Believing a thing is public is not knowing it, and a
    confident sentence about an absent record costs nothing to write and cannot be checked."""
    bad = row(id="wt:claimed", publicness="published", verified=False)
    assert wanted.main(site(tmp_path, every_group([bad]))) == 1
    out = capsys.readouterr().out
    assert "nobody here has read a candidate at its source" in out
    assert "say unknown until somebody has looked" in out
    # The same row, once somebody has read one, passes.
    good = dict(bad, verified=True)
    good.pop("check")
    assert wanted.main(site(tmp_path, every_group([good]))) == 0


def test_not_public_is_a_claim_too(tmp_path, capsys):
    """Asserting a record is withheld is the claim this list is likeliest to get wrong, and the
    one a reader would treat as the harshest. It needs a reading like any other."""
    assert (
        wanted.main(site(tmp_path, every_group([row(id="wt:shut", publicness="not public")]))) == 1
    )
    assert "nobody here has read a candidate at its source" in capsys.readouterr().out


def test_a_row_that_does_not_know_must_say_how_to_find_out(tmp_path, capsys):
    unchecked = row(id="wt:idle")
    unchecked.pop("check")
    assert wanted.main(site(tmp_path, every_group([unchecked]))) == 1
    out = capsys.readouterr().out
    assert "carries no check" in out and "what to read, and where" in out


def test_a_verified_row_names_what_it_read(tmp_path, capsys):
    empty = row(id="wt:read-nothing", verified=True, candidates=[])
    empty.pop("check")
    assert wanted.main(site(tmp_path, every_group([empty]))) == 1
    assert "names no candidate, so there is nothing it read" in capsys.readouterr().out


def test_a_row_never_names_an_officeholder_or_what_stands_in_for_one(tmp_path, capsys):
    holders = tmp_path / "data"
    holders.mkdir(parents=True, exist_ok=True)
    (holders / "officeholders.ndjson").write_text(
        json.dumps({"id": "oh:us:house:x000001", "legal_name": "Alexander Quill"}) + "\n",
        encoding="utf-8",
    )
    (holders / "filings.ndjson").write_text(
        json.dumps({"id": "fl:house-clerk:P:20024346"}) + "\n", encoding="utf-8"
    )
    named = row(id="wt:named", today="Nothing about Alexander Quill's report is published.")
    assert wanted.main(site(tmp_path, every_group([named]))) == 1
    assert "names 'Alexander Quill'" in capsys.readouterr().out

    seated = row(id="wt:seated", today="Nothing about the report filed for AK00 is published.")
    assert wanted.main(site(tmp_path, every_group([seated]))) == 1
    assert "carries a seat" in capsys.readouterr().out

    doc = row(id="wt:doc", today="Nothing about report 20024346 is published.")
    assert wanted.main(site(tmp_path, every_group([doc]))) == 1
    assert "carries DocID 20024346" in capsys.readouterr().out


def test_a_statute_section_is_not_a_docid_and_a_word_is_not_a_name(tmp_path, capsys):
    """Both false positives a first draft of this gate reported against rows written in good
    faith. A gate that cries wolf on a statute citation, in a file whose whole job is to cite
    statutes, is a gate somebody switches off."""
    data = tmp_path / "data"
    data.mkdir(parents=True, exist_ok=True)
    (data / "officeholders.ndjson").write_text(
        json.dumps({"id": "oh:us:house:x000001", "legal_name": "Ed Case"}) + "\n", encoding="utf-8"
    )
    (data / "filings.ndjson").write_text(
        json.dumps({"id": "fl:house-clerk:P:20024346"}) + "\n", encoding="utf-8"
    )
    ok = row(
        id="wt:citations",
        today="The statute provides penalties at 5 U.S.C. 13106, and the register reads none.",
        with_it="A count, or a named case where one exists, with its docket number.",
        route="Federal dockets searched by the statute; fields of the index are not dates.",
    )
    assert wanted.main(site(tmp_path, every_group([ok]))) == 0


def test_a_group_the_page_cannot_render_fails_and_so_does_one_with_no_row(tmp_path, capsys):
    stray = row(id="wt:stray", closes="the-weather")
    assert wanted.main(site(tmp_path, every_group([stray]))) == 1
    assert "the page has no heading for" in capsys.readouterr().out

    short = [row(id=f"wt:{g}", closes=g) for g in wanted.GROUPS[:-1]]
    assert wanted.main(site(tmp_path, short)) == 1
    assert "has a heading for" in capsys.readouterr().out


def test_two_rows_may_not_share_an_id(tmp_path, capsys):
    assert (
        wanted.main(site(tmp_path, every_group([row(id=wanted.GROUPS[0].join(["wt:", ""]))]))) == 1
    )
    assert "two rows carry this id" in capsys.readouterr().out


def test_nothing_to_read_is_a_failure(tmp_path, capsys):
    """A gate that reads nothing proves nothing, and an empty wanted list would claim the loop
    is closed."""
    assert wanted.main([str(tmp_path)]) == 1
    assert "no wanted register" in capsys.readouterr().out
    assert wanted.main(site(tmp_path, [])) == 1
    assert "holds no row, and the loop is not closed" in capsys.readouterr().out


def test_the_shipped_rows_pass_their_own_gate():
    assert wanted.main([str(HERE.parent)]) == 0
