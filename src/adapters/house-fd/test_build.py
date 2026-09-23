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


def test_a_row_at_a_members_seat_with_another_given_name_is_held_not_matched():
    """A CA38 row under the sitting member's surname with a different given name. The name
    join holds it; it does not decide who filed it."""
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


def test_the_capture_key_names_the_bytes_and_nothing_else():
    """Same source bytes, same key, whenever they were fetched. The refresh loop rests on this."""
    a = {"sha256": "aa" * 32, "retrieved_at": "2026-09-22T21:40:20Z"}
    b = {"sha256": "bb" * 32, "retrieved_at": "2026-09-22T21:40:17Z"}
    later_a = {"sha256": "aa" * 32, "retrieved_at": "2026-09-29T09:17:00Z"}
    key = build.capture_key(a, b)
    assert len(key) == 12 and all(c in "0123456789abcdef" for c in key)
    assert build.capture_key(later_a, b) == key
    assert build.capture_key(b, a) != key


def _member(last, first, seat, bioguide="X000001", sworn="20250103", official=None):
    return dict(
        person(last, first, seat=seat, bioguide=bioguide),
        sworn=sworn,
        official_name=official or f"{first} {last}",
    )


def test_the_surname_pick_is_the_one_member_or_the_one_at_the_rows_seat():
    people, by_surname = roster(
        _member("Allen", "Rick", "GA12"),
        _member("Johnson", "Mike", "LA04", "J000001"),
        _member("Johnson", "Dusty", "SD00", "J000002"),
        _member("Van Duyne", "Beth", "TX24", "V000001"),
        _member("Van Drew", "Jeff", "NJ02", "V000002"),
    )
    assert (
        build.surname_neighbour(row("Allen", "Richard", seat="GA12"), by_surname)["seat"] == "GA12"
    )
    assert (
        build.surname_neighbour(row("Allen", "Richard", seat="TX34"), by_surname)["seat"] == "GA12"
    )
    assert (
        build.surname_neighbour(row("Johnson", "James Michael", seat="LA04"), by_surname)["seat"]
        == "LA04"
    )
    assert build.surname_neighbour(row("Johnson", "James Michael", seat="OH01"), by_surname) is None
    assert (
        build.surname_neighbour(row("Van Duyne", "Elizabeth Ann", seat="TX24"), by_surname)["seat"]
        == "TX24"
    )
    assert (
        build.surname_neighbour(row("Van Drew", "Jeff Mr", seat="NJ02"), by_surname)["seat"]
        == "NJ02"
    )
    assert build.surname_neighbour(row("Nobody", "At All"), by_surname) is None
    _, cruz = roster(_member("De La Cruz", "Monica", "TX15", "D000001"))
    assert build.surname_neighbour(row("De Barros", "Jonathan", seat="CT05"), cruz) is None, (
        "a shared particle is not a shared surname"
    )
    assert build.surname_neighbour(row("De La Cruz", "Carlos", seat="TX35"), cruz)["seat"] == "TX15"
    got, why = build.match(row("Johnson", "James Michael", seat="LA04"), people, by_surname)
    assert got is None and why.startswith("surname matches a sitting member (Johnson, Mike, LA04)")


def test_the_document_header_attributes_or_holds_and_never_says_who_a_filer_is_not():
    """Roster 'Rick', index 'Richard W.', same seat. The document, not a guess, settles it."""
    member = _member("Allen", "Rick", "GA12", official="Rick W. Allen")
    index_row = dict(row("Allen", "Richard W.", seat="GA12"), doc_id="10074380")
    head = {
        "name": "Hon. Richard W. Allen",
        "status": "Member",
        "seat": "GA12",
        "filing_id": "10074380",
    }
    verdict, clause = build.attribute_by_header(head, index_row, member, "2025-05-15")
    assert verdict == "attributed" and "Status Member, State/District GA12" in clause

    candidate = dict(head, status="Congressional Candidate", name="Someone Else")
    verdict, clause = build.attribute_by_header(candidate, index_row, member, "2025-05-15")
    assert verdict == "held"
    assert "Status 'Congressional Candidate' for the filer named 'Someone Else'" in clause
    assert "is not" not in clause, "the register never says who a filer is not"

    verdict, clause = build.attribute_by_header(
        dict(head, filing_id=""), index_row, member, "2025-05-15"
    )
    assert verdict == "held" and "carries no Filing ID line" in clause and "scanned" in clause
    assert (
        build.attribute_by_header(dict(head, filing_id="99"), index_row, member, "2025-05-15")[0]
        == "held"
    )
    assert (
        build.attribute_by_header(dict(head, seat="GA11"), index_row, member, "2025-05-15")[0]
        == "held"
    )
    verdict, clause = build.attribute_by_header(
        dict(head, name="Hon. Richard W. Other"), index_row, member, "2025-05-15"
    )
    assert verdict == "held" and "does not carry the roster surname" in clause
    verdict, clause = build.attribute_by_header(head, index_row, member, "2025-01-01")
    assert verdict == "held"
    assert "before the swearing-in for this Congress that the roster records (2025-01-03)" in clause
    assert "the roster does not say who held the seat before that date" in clause


def test_an_index_docid_listed_twice_identically_is_carried_once_and_says_so():
    a = {"doc_id": "1", "last": "A", "first": "A", "state_dst": "XX01", "filing_type": "P"}
    b = {"doc_id": "2", "last": "B", "first": "B", "state_dst": "XX02", "filing_type": "O"}
    b2 = dict(b, filing_type="X")
    capture = {"url": "u", "retrieved_at": "t", "sha256": "h"}
    rejected = []
    kept, duplicated = build.collapse_duplicates([a, dict(a), b], rejected, capture)
    assert kept == [a, b] and duplicated == {"1": 2} and rejected == []
    rejected = []
    kept, duplicated = build.collapse_duplicates([a, b, b2], rejected, capture)
    assert kept == [a] and duplicated == {}
    assert len(rejected) == 2 and all(
        "more than once with differing rows" in r["reason"] for r in rejected
    )


def test_the_capture_stage_recognises_the_adapters_own_held_reason():
    spec = importlib.util.spec_from_file_location("house_fd_documents", HERE / "documents.py")
    documents = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(documents)
    people, by_surname = roster(_member("Allen", "Rick", "GA12"))
    _, why = build.match(row("Allen", "Richard", seat="GA12"), people, by_surname)
    found = documents.HELD.search(why)
    assert found and found.group(1) == "GA12", "a wording change here would silently stop captures"
