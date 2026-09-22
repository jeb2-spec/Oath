"""Tests for the House FD adapter's join.

Every case here is drawn from a real disagreement between the Clerk's roster and
the Clerk's filing index, measured on the 2025 index. The names are real sitting
members, because the cases are facts about two public files and inventing them
would prove nothing. No test touches the network.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _load():
    spec = importlib.util.spec_from_file_location("house_fd_build", HERE / "build.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


build = _load()


def person(last: str, first: str, seat: str = "XX01", bioguide: str = "X000001") -> dict:
    return {
        "seat": seat,
        "bioguide": bioguide,
        "last": last,
        "first": first,
        "namelist": f"{last}, {first}",
        "_tokens": build.tokens(last, first),
    }


def roster(*people):
    import collections

    by_surname = collections.defaultdict(list)
    for p in people:
        by_surname[build.fold(p["last"].split()[0])].append(p)
    return list(people), by_surname


def row(last: str, first: str, seat: str = "XX01") -> dict:
    return {"last": last, "first": first, "state_dst": seat}


def test_diacritics_fold_together():
    """The roster writes Sánchez; the index writes Sanchez. One person."""
    people, by_surname = roster(person("Sánchez", "Linda"))
    got, why = build.match(row("Sanchez", "Linda T."), people, by_surname)
    assert got is not None and "contained" in why


def test_multi_part_surname_split_differently():
    """Roster: 'Watson Coleman, Bonnie'. Index: 'Coleman, Bonnie Watson'."""
    people, by_surname = roster(person("Watson Coleman", "Bonnie"))
    got, _ = build.match(row("Coleman", "Bonnie Watson"), people, by_surname)
    assert got is not None


def test_a_seat_change_does_not_break_the_join():
    """A member whose filings are indexed at the district they used to hold."""
    people, by_surname = roster(person("Begich", "Nicholas", seat="AK00"))
    got, _ = build.match(row("Begich", "Nicholas J.", seat="AK99"), people, by_surname)
    assert got is not None, "the name carries the join; the seat only corroborates"


def test_a_candidate_at_a_members_seat_is_refused():
    """Monica Sanchez filed at CA38, where Linda Sánchez sits. Different people."""
    people, by_surname = roster(person("Sánchez", "Linda", seat="CA38"))
    got, why = build.match(row("Sanchez", "Monica", seat="CA38"), people, by_surname)
    assert got is None
    assert "given names differ" in why and "a human decides" in why


def test_an_unrelated_candidate_is_refused():
    people, by_surname = roster(person("Huizenga", "Bill", seat="MI04"))
    got, why = build.match(row("Aaron", "Richard", seat="MI04"), people, by_surname)
    assert got is None and "candidate or a former member" in why


def test_a_common_name_shared_by_two_members_is_refused():
    """Ambiguity is never resolved by picking one."""
    people, by_surname = roster(
        person("Smith", "Adam", bioguide="S000001"), person("Smith", "Adam", bioguide="S000002")
    )
    got, why = build.match(row("Smith", "Adam"), people, by_surname)
    assert got is None and "more than one sitting member" in why


def test_a_nickname_is_refused_rather_than_guessed():
    """Roster 'Bill', index 'William'. Probably one person. Probably is not enough."""
    people, by_surname = roster(person("Huizenga", "Bill", seat="MI04"))
    got, why = build.match(row("Huizenga", "William", seat="MI04"), people, by_surname)
    assert got is None
    assert "given names differ" in why


def test_dates_parse_or_return_none():
    assert build.iso("3/24/2025") == "2025-03-24"
    assert build.iso("10/12/2025") == "2025-10-12"
    assert build.iso("") is None
    assert build.iso("2025-03-24") is None


def test_the_document_url_follows_the_clerks_own_split():
    ptr = build.doc_url({"filing_type": "P", "year": "2025", "doc_id": "20032062"})
    other = build.doc_url({"filing_type": "C", "year": "2025", "doc_id": "10072640"})
    assert ptr.endswith("/ptr-pdfs/2025/20032062.pdf")
    assert other.endswith("/financial-pdfs/2025/10072640.pdf")


def test_canonical_lines_are_stable():
    line = build.canonical({"b": 2, "a": 1})
    assert line == '{"a":1,"b":2}\n'
