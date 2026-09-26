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


def test_what_a_build_will_want_comes_from_the_two_captures_alone():
    people, _ = roster(
        _member("Allen", "Rick", "GA12"),
        _member("Johnson", "Mike", "LA04", "J000001"),
        _member("Johnson", "Dusty", "SD00", "J000002"),
    )
    rows = [
        dict(row("Allen", "Rick", seat="GA12"), doc_id="1", filing_type="P", year="2025"),
        dict(row("Allen", "Rick", seat="GA12"), doc_id="2", filing_type="O", year="2025"),
        dict(row("Allen", "Richard W.", seat="GA12"), doc_id="3", filing_type="O", year="2025"),
        dict(
            row("Johnson", "James Michael", seat="LA04"), doc_id="4", filing_type="P", year="2025"
        ),
        dict(
            row("Johnson", "James Michael", seat="OH01"), doc_id="5", filing_type="P", year="2025"
        ),
        dict(row("Nobody", "At All", seat="GA12"), doc_id="6", filing_type="P", year="2025"),
        dict(row("Allen", "Rick", seat="GA12"), doc_id="1", filing_type="P", year="2025"),
    ]
    wanted = build.wanted_from_rows(rows, people)
    assert [(w["doc_id"], w["why"]) for w in wanted] == [
        ("1", "attributed"),
        ("2", "attributed"),
        ("3", "held at the member's own seat"),
        ("4", "held at the member's own seat"),
    ]
    assert wanted[0]["url"].endswith("ptr-pdfs/2025/1.pdf") and wanted[1]["url"].endswith(
        "financial-pdfs/2025/2.pdf"
    )
    assert {w["seat"] for w in wanted} == {"GA12", "LA04"}


# ---- the published register is an input to every build (NEXT.md S.1b) --------------------
#
# These run the whole build, in a temporary directory, from small captures written here.
# The people in them are placeholders at seats no state has (XX01), visibly not persons,
# as fixtures/README.md requires; the cases are what happens to the register's own rows.

import hashlib  # noqa: E402
import json  # noqa: E402

import pytest  # noqa: E402

ADA = {"bioguide": "X000001", "last": "Example", "first": "Ada", "seat": "XX01"}
BEA = {"bioguide": "X000002", "last": "Placeholder", "first": "Bea", "seat": "XX02"}
CAL = {"bioguide": "X000003", "last": "Sample", "first": "Cal", "seat": "XX03"}
DAN = {"bioguide": "X000004", "last": "Nobody", "first": "Dan", "seat": "XX01"}


def roster_xml(congress: int, members: list[dict], sworn: str, seats=("XX01", "XX02", "XX03")):
    held = {m["seat"]: m for m in members}
    out = [f"<MemberData><title-info><congress-num>{congress}</congress-num></title-info><members>"]
    for seat in seats:
        m = held.get(seat)
        info = (
            f"<member-info><bioguideID>{m['bioguide']}</bioguideID>"
            f"<lastname>{m['last']}</lastname><firstname>{m['first']}</firstname>"
            f"<middlename/><official-name>{m['first']} {m['last']}</official-name>"
            f"<namelist>{m['last']}, {m['first']}</namelist><party>{m.get('party', 'I')}</party>"
            f'<district>1st</district><sworn-date date="{sworn}"/></member-info>'
            if m
            else "<member-info><bioguideID/></member-info>"
        )
        out.append(f"<member><statedistrict>{seat}</statedistrict>{info}</member>")
    return "".join(out) + "</members></MemberData>"


def index_xml(rows: list[tuple], year: int = 2025) -> str:
    """Index rows as (member, DocID), with the form code and the filing date optional."""
    out = ["<FinancialDisclosure>"]
    for m, doc_id, *rest in rows:
        code = rest[0] if rest else "O"
        filed = rest[1] if len(rest) > 1 else f"5/15/{year + 1}"
        out.append(
            f"<Member><Last>{m['last']}</Last><First>{m['first']}</First><Suffix/>"
            f"<FilingType>{code}</FilingType><StateDst>{m['seat']}</StateDst><Year>{year}</Year>"
            f"<FilingDate>{filed}</FilingDate><DocID>{doc_id}</DocID></Member>"
        )
    return "".join(out) + "</FinancialDisclosure>"


def captures(root: Path, roster: str, index: str, roster_at: str, index_at: str, year=2025):
    cache = root / "data" / "cache" / "house-fd"
    cache.mkdir(parents=True, exist_ok=True)
    manifest = {}
    for name, text, at, url in (
        ("MemberData.xml", roster, roster_at, "https://clerk.house.gov/xml/lists/MemberData.xml"),
        (
            f"{year}FD.xml",
            index,
            index_at,
            f"https://disclosures-clerk.house.gov/public_disc/financial-pdfs/{year}FD.zip",
        ),
    ):
        (cache / name).write_text(text, encoding="utf-8")
        key = "MemberData.xml" if name == "MemberData.xml" else f"{year}FD.zip"
        if key != name:  # fetch.py keeps the archive it hashed beside what it extracted
            (cache / key).write_text(text, encoding="utf-8")
        manifest[key] = {
            "url": url,
            "retrieved_at": at,
            "sha256": hashlib.sha256(text.encode()).hexdigest(),
        }
    (cache / "capture.json").write_text(json.dumps(manifest), encoding="utf-8")


def kept(root: Path) -> set[str]:
    """The capture files the register keeps, by name."""
    folder = root / "data" / "captures" / "sha256"
    return {p.name for p in folder.iterdir()} if folder.is_dir() else set()


def changes_of(root: Path) -> list[dict]:
    return [json.loads(line) for line in rows_of(root, "changes").values()]


def rows_of(root: Path, name: str) -> dict[str, str]:
    path = root / "data" / f"{name}.ndjson"
    if not path.is_file():
        return {}
    return {json.loads(line)["id"]: line for line in path.read_text("utf-8").splitlines()}


def run_record(root: Path) -> dict:
    (path,) = (root / "data" / "adapter-runs").glob("house-fd-2025-*.ndjson")
    return json.loads(path.read_text("utf-8"))


@pytest.fixture
def register(tmp_path, monkeypatch):
    """A first build: two members, one filing each, in the 119th Congress."""
    monkeypatch.chdir(tmp_path)
    captures(
        tmp_path,
        roster_xml(119, [ADA, BEA], "20250103"),
        index_xml([(ADA, "30000001"), (BEA, "30000002")]),
        "2026-01-05T00:00:00Z",
        "2026-01-05T00:00:01Z",
    )
    assert build.build(2025) == 0
    return tmp_path


def test_a_member_the_roster_no_longer_lists_keeps_every_published_row(register):
    before = {name: rows_of(register, name) for name in ("officeholders", "filings", "offices")}
    bea = "oh:us:house:x000002"
    roster = roster_xml(119, [ADA], "20250103")
    captures(
        register,
        roster,
        index_xml([(ADA, "30000001"), (BEA, "30000002")]),
        "2026-02-02T00:00:00Z",
        "2026-02-02T00:00:01Z",
    )
    assert build.build(2025) == 0
    after = {name: rows_of(register, name) for name in ("officeholders", "filings", "offices")}
    assert after == before, "every published row, byte for byte"
    (change,) = changes_of(register)
    assert (change["row_id"], change["rows"], change["change"]) == (
        bea,
        "officeholders",
        "not listed",
    )
    assert change["capture"]["retrieved_at"] == "2026-02-02T00:00:00Z"
    assert change["before"] == "2026-01-05T00:00:00Z", "the last read that listed her"
    assert change["frame"] == "Presence in the register is not evidence of wrongdoing."
    sha = hashlib.sha256(roster.encode()).hexdigest()
    assert kept(register) == {f"{sha}.xml"}, "the roster that shows the change is kept"
    assert (register / "data" / "captures" / "sha256" / f"{sha}.xml").read_text() == roster
    (rejected,) = (register / "data" / "rejected" / "house-fd").glob("2025-*.ndjson")
    assert "30000002" not in rejected.read_text("utf-8"), "a published filing is not set aside"
    record = run_record(register)
    assert record["changes"] == {"not listed": 1} and "carried" not in record
    assert record["counts"]["filings"] == 2 and record["counts"]["quiet"] == 0

    # The roster lists her again: the change is recorded, and the first one stays.
    captures(
        register,
        roster_xml(119, [ADA, BEA], "20250103"),
        index_xml([(ADA, "30000001"), (BEA, "30000002")]),
        "2026-03-02T00:00:00Z",
        "2026-03-02T00:00:01Z",
    )
    assert build.build(2025) == 0
    assert [c["change"] for c in changes_of(register)] == ["not listed", "listed again"]
    assert run_record(register)["changes"] == {"not listed": 1, "listed again": 1}
    assert {name: rows_of(register, name) for name in before} == before


def test_a_filing_the_index_stops_listing_stays_and_the_change_is_shown(register):
    before = rows_of(register, "filings")
    index = index_xml([(ADA, "30000001")])
    captures(
        register,
        roster_xml(119, [ADA, BEA], "20250103"),
        index,
        "2026-01-05T00:00:00Z",
        "2026-02-09T00:00:00Z",
    )
    assert build.build(2025) == 0
    assert rows_of(register, "filings") == before
    (change,) = changes_of(register)
    assert (change["rows"], change["change"]) == ("filings", "not listed")
    assert change["capture"]["url"].endswith("2025FD.zip")
    assert kept(register) == {f"{hashlib.sha256(index.encode()).hexdigest()}.zip"}


def test_a_later_index_that_states_a_fact_otherwise_is_a_change_not_an_edit(register):
    """The Clerk moves a published filing's date. The row keeps the date it was published
    with; the change, and the capture that shows it, are rows of their own. Once."""
    before = rows_of(register, "filings")
    moved = index_xml([(ADA, "30000001", "O", "5/16/2026"), (BEA, "30000002")])
    for week in ("2026-02-09", "2026-02-16"):
        captures(
            register,
            roster_xml(119, [ADA, BEA], "20250103"),
            moved,
            f"{week}T00:00:00Z",
            f"{week}T00:00:01Z",
        )
        assert build.build(2025) == 0
    assert rows_of(register, "filings") == before
    (change,) = changes_of(register)
    assert (change["change"], change["field"], change["was"], change["now"]) == (
        "read otherwise",
        "filed_at",
        "2026-05-15",
        "2026-05-16",
    )
    assert change["capture"]["retrieved_at"] == "2026-02-09T00:00:01Z", "one change, once"
    captures(
        register,
        roster_xml(119, [ADA, BEA], "20250103"),
        index_xml([(ADA, "30000001"), (BEA, "30000002")]),
        "2026-02-23T00:00:00Z",
        "2026-02-23T00:00:01Z",
    )
    assert build.build(2025) == 0
    last = changes_of(register)[-1]
    assert (last["was"], last["now"]) == ("2026-05-15", "2026-05-15"), "read as published again"


def test_the_same_index_row_read_otherwise_refuses_because_the_register_changed(
    register, monkeypatch
):
    """Nothing about the source moved; only the register's reading. It must not rewrite a
    published row, nor record the change as the Clerk's."""
    monkeypatch.setattr(build, "iso", lambda text: "2026-05-14")
    with pytest.raises(SystemExit, match="the register's reading did"):
        build.build(2025)


def test_a_code_the_index_changes_on_a_published_docid_is_one_change_not_a_second_row(register):
    before = rows_of(register, "filings")
    captures(
        register,
        roster_xml(119, [ADA, BEA], "20250103"),
        index_xml([(ADA, "30000001", "X"), (BEA, "30000002")]),
        "2026-02-09T00:00:00Z",
        "2026-02-09T00:00:01Z",
    )
    assert build.build(2025) == 0
    assert rows_of(register, "filings") == before, "no fl:house-clerk:X:30000001 beside it"
    assert [(c["field"], c["was"], c["now"]) for c in changes_of(register)] == [
        ("source_form_code", "O", "X")
    ]


def test_a_party_the_roster_states_otherwise_is_a_change_never_a_stopped_refresh(register):
    before = rows_of(register, "officeholders")
    captures(
        register,
        roster_xml(119, [dict(ADA, party="D"), BEA], "20250103"),
        index_xml([(ADA, "30000001"), (BEA, "30000002")]),
        "2026-02-09T00:00:00Z",
        "2026-02-09T00:00:01Z",
    )
    assert build.build(2025) == 0
    assert rows_of(register, "officeholders") == before
    (change,) = changes_of(register)
    assert (change["rows"], change["field"], change["was"], change["now"]) == (
        "officeholders",
        "party",
        "I",
        "D",
    )


def test_the_same_roster_read_otherwise_refuses(register, monkeypatch):
    real = build.load_roster

    def misread(path):
        seats, people = real(path)
        return seats, [dict(p, party="X") for p in people]

    monkeypatch.setattr(build, "load_roster", misread)
    with pytest.raises(SystemExit, match="the register's reading did"):
        build.build(2025)


def test_a_rebuild_from_the_same_captures_writes_the_same_bytes(register):
    """The run record is the register's state, not this build's deltas, so a second build
    from the same captures seals the same digest (the Council's reading of S.1b)."""
    captures(
        register,
        roster_xml(119, [ADA], "20250103"),
        index_xml([(ADA, "30000001"), (BEA, "30000002")]),
        "2026-02-02T00:00:00Z",
        "2026-02-02T00:00:01Z",
    )
    assert build.build(2025) == 0
    first = {p: p.read_bytes() for p in sorted((register / "data").rglob("*.ndjson"))}
    assert build.build(2025) == 0
    assert {p: p.read_bytes() for p in sorted((register / "data").rglob("*.ndjson"))} == first


def test_a_person_may_attribute_a_new_row_to_a_member_the_roster_no_longer_lists(register):
    """A report a departed Member filed while the roster listed them, indexed after it
    stopped, is set aside by the name join, and a person's cited decision attributes it to
    the office they held. One filed after the last read that listed them is not entered
    (SUBJECTS.md §1), and the build goes on (the Council's reading of S.1b)."""
    later = index_xml(
        [
            (ADA, "30000001"),
            (BEA, "30000002"),
            (BEA, "30000009", "O", "12/20/2025"),
            (BEA, "30000010", "O", "3/1/2026"),
        ]
    )
    captures(
        register,
        roster_xml(119, [ADA], "20250103"),
        later,
        "2026-02-02T00:00:00Z",
        "2026-02-02T00:00:01Z",
    )
    assert build.build(2025) == 0
    assert "fl:house-clerk:O:30000009" not in rows_of(register, "filings")
    decisions = register / "src" / "adapters" / "house-fd" / "adjudications.ndjson"
    decisions.parent.mkdir(parents=True, exist_ok=True)
    decisions.write_text(
        "".join(
            json.dumps(
                {
                    "doc_id": doc_id,
                    "officeholder_id": "oh:us:house:x000002",
                    "evidence_url": "https://example.com/the-document",
                    "decided_by": "the maintainer",
                    "decided_at": "2026-02-03",
                }
            )
            + "\n"
            for doc_id in ("30000009", "30000010")
        ),
        encoding="utf-8",
    )
    assert build.build(2025) == 0
    assert "fl:house-clerk:O:30000010" not in rows_of(register, "filings")
    (rejected,) = (register / "data" / "rejected" / "house-fd").glob("2025-*.ndjson")
    reasons = {
        json.loads(line)["source_row"]["doc_id"]: json.loads(line)["reason"]
        for line in rejected.read_text("utf-8").splitlines()
    }
    assert "SUBJECTS.md §1 enters no new filing" in reasons["30000010"]
    assert (
        "after 2026-01-05, the last day the register can show them in office" in reasons["30000010"]
    )
    row = json.loads(rows_of(register, "filings")["fl:house-clerk:O:30000009"])
    assert (row["officeholder_id"], row["office_id"]) == (
        "oh:us:house:x000002",
        "of:us:house-xx02:2025",
    )
    assert row["extraction_confidence"] == "manual"


def test_a_closed_year_is_carried_and_never_rebuilt_from_the_next_roster(register):
    """The 120th Congress's roster must not re-derive the 119th's rows: its office ids and
    swearing-in dates would put every 2025 transaction before the swearing-in. The rows stay;
    the offices of the ended Congress get the day their terms ended (U.S. Const. amend. XX,
    section 1); a row set aside keeps its reason."""
    captures(
        register,
        roster_xml(119, [ADA, BEA], "20250103"),
        index_xml([(ADA, "30000001"), (BEA, "30000002"), (DAN, "30000004")]),
        "2026-06-01T00:00:00Z",
        "2026-06-01T00:00:01Z",
    )
    assert build.build(2025) == 0
    before = {name: rows_of(register, name) for name in ("officeholders", "filings", "offices")}
    captures(
        register,
        roster_xml(120, [ADA, CAL], "20270103"),
        index_xml([(ADA, "30000001"), (BEA, "30000002"), (DAN, "30000004"), (CAL, "30000003")]),
        "2027-01-11T00:00:00Z",
        "2027-01-11T00:00:01Z",
    )
    assert build.build(2025) == 0
    after = {name: rows_of(register, name) for name in ("officeholders", "filings", "offices")}
    assert after["filings"] == before["filings"], "every filing, byte for byte"
    for name in ("offices", "officeholders"):
        assert set(after[name]) == set(before[name])
        for row_id, line in before[name].items():
            filled = line.replace('"term_end":null', '"term_end":"2027-01-03"')
            assert after[name][row_id] == filled, "only the ended terms' end is filled"
    assert not changes_of(register), "the year's roster was not read; nothing observed"
    (rejected,) = (register / "data" / "rejected" / "house-fd").glob("2025-*.ndjson")
    set_aside = {
        json.loads(line)["source_row"]["doc_id"]: json.loads(line)["reason"]
        for line in rejected.read_text("utf-8").splitlines()
    }
    assert set_aside["30000004"].startswith("no sitting member has this name"), (
        "a row set aside while the year was open keeps its own reason"
    )
    assert "is of the 119th Congress" in set_aside["30000003"]
    assert "lists the 120th" in set_aside["30000003"]
    record = run_record(register)
    assert record["congress"] == {
        "filing_year": 119,
        "roster": 120,
        "closed": True,
        "last_roster_read": "2026-06-01T00:00:00Z",
    }, "the last roster of the year's own Congress the register read, carried"
    assert [s["name"] for s in record["sources"]] == ["2025FD.zip"]
    manifest = json.loads(
        (register / "data" / "cache" / "house-fd" / "capture.json").read_text("utf-8")
    )
    assert record["capture_key"] == build.capture_key(manifest["2025FD.zip"], None, None), (
        "a closed year's key names the index alone, so the roster moving on rebuilds nothing"
    )


def test_the_join_never_moves_a_published_attribution(register):
    """Another member bearing the same name would draw a published filing to themselves."""
    twin = dict(ADA, bioguide="X000009", seat="XX03")
    captures(
        register,
        roster_xml(119, [BEA, twin], "20250103"),
        index_xml([(ADA, "30000001"), (BEA, "30000002")]),
        "2026-04-06T00:00:00Z",
        "2026-04-06T00:00:01Z",
    )
    with pytest.raises(SystemExit, match="never moves a published attribution"):
        build.build(2025)


def test_the_header_holds_a_row_that_carries_another_kept_officeholders_name():
    """A Member who left files after a successor of the same surname is sworn in at the
    seat; the surname alone would give the successor the report."""
    successor = _member("Bresnahan", "Sam", "PA08", official="Sam Bresnahan")
    index_row = dict(row("Bresnahan", "Robert", seat="PA08"), doc_id="20099999")
    head = {
        "name": "Hon. Robert Bresnahan",
        "status": "Member",
        "seat": "PA08",
        "filing_id": "20099999",
    }
    others = [("robert", frozenset({"bresnahan"}))]
    verdict, clause = build.attribute_by_header(head, index_row, successor, "2026-12-01", others)
    assert verdict == "held" and "another officeholder the register holds at this seat" in clause
    mine = dict(head, name="Hon. Sam Bresnahan")
    assert build.attribute_by_header(mine, index_row, successor, "2026-12-01", others)[0] == (
        "attributed"
    )


def test_a_roster_of_an_earlier_congress_than_the_year_refuses():
    with pytest.raises(SystemExit, match="falls in the 120th"):
        build.closed_year(2027, 119)
    assert build.closed_year(2025, 120) and not build.closed_year(2026, 119)


def test_the_terms_of_a_congress_follow_the_twentieth_amendment():
    assert build.term_start(119) == "2025-01-03" and build.term_start(120) == "2027-01-03"
    assert [build.congress_of(y) for y in (2025, 2026, 2027)] == [119, 119, 120]
    assert [build.ordinal(n) for n in (119, 120, 121, 122, 123, 111)] == [
        "119th",
        "120th",
        "121st",
        "122nd",
        "123rd",
        "111th",
    ]


# ---- documents: the same bytes read the same; other bytes that read otherwise are shown ----

real_ptr = build.load_ptr()


class StubReader:
    """Reads a document written here as JSON, the header text and the rows; the header and
    the checks are the reader's own, so only the parsing of a real PDF is stood in for."""

    header = staticmethod(real_ptr.header)
    verify = staticmethod(real_ptr.verify)
    rows = staticmethod(lambda tx: tx)

    @staticmethod
    def read(pdf):
        doc = json.loads(Path(pdf).read_text("utf-8"))
        return doc["text"], doc["tx"]

    @staticmethod
    def extract_text(pdf):
        return StubReader.read(pdf)[0]

    @staticmethod
    def transactions(pages):
        return [dict(t) for t in StubReader.rows(pages)]

    @staticmethod
    def notes(tx):
        return f"Asset code {tx['asset_code']} per the Clerk's legend."


TX = {
    "owner": "unmarked",
    "asset": "Example Holdings",
    "ticker": None,
    "asset_code": "ST",
    "action": "purchase",
    "transaction_date": "2025-02-01",
    "notified_date": "2025-02-02",
    "amount": {"currency": "USD", "max": 15000, "min": 1001},
    "filing_status": "New",
}


def document(root: Path, doc_id: str, member: dict, txs: list[dict], at: str, pad: str = ""):
    """A captured document for DocID, as documents.py would record it."""
    docs = root / "data" / "cache" / "house-fd" / "docs"
    docs.mkdir(parents=True, exist_ok=True)
    text = (
        f"Name: Hon. {member['first']} {member['last']}\nStatus: Member\n"
        f"State/District: {member['seat']}\nFiling ID #{doc_id}\n{pad}"
    )
    body = json.dumps({"text": text, "tx": txs}, sort_keys=True)
    (docs / f"{doc_id}.pdf").write_text(body, encoding="utf-8")
    manifest_path = docs / "captures.json"
    manifest = json.loads(manifest_path.read_text("utf-8")) if manifest_path.is_file() else {}
    manifest[doc_id] = {
        "url": f"https://disclosures-clerk.house.gov/public_disc/ptr-pdfs/2025/{doc_id}.pdf",
        "retrieved_at": at,
        "sha256": hashlib.sha256(body.encode()).hexdigest(),
    }
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    return hashlib.sha256(body.encode()).hexdigest()


@pytest.fixture
def reports(tmp_path, monkeypatch):
    """A first build with one transaction report, read: two rows."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(build, "load_ptr", lambda: StubReader)
    captures(
        tmp_path,
        roster_xml(119, [ADA], "20250103"),
        index_xml([(ADA, "20000001", "P", "3/1/2025")]),
        "2026-01-05T00:00:00Z",
        "2026-01-05T00:00:01Z",
    )
    document(
        tmp_path, "20000001", ADA, [TX, dict(TX, asset="Other Holdings")], "2026-01-05T00:00:02Z"
    )
    assert build.build(2025) == 0
    assert len(rows_of(tmp_path, "transactions")) == 2
    return tmp_path


def test_the_same_bytes_read_otherwise_refuse_because_the_reader_changed(reports, monkeypatch):
    """C-1: a reader that yields fewer rows from the very bytes they were read from must not
    record the Clerk as dropping a trade."""
    monkeypatch.setattr(StubReader, "rows", staticmethod(lambda tx: tx[:1]))
    with pytest.raises(SystemExit, match="the register's reading did"):
        build.build(2025)
    assert not changes_of(reports)


def test_other_bytes_that_read_otherwise_are_a_replacement_shown_beside_the_rows(reports):
    before = {name: rows_of(reports, name) for name in ("filings", "transactions")}
    sha = document(reports, "20000001", ADA, [TX], "2026-02-02T00:00:00Z")
    assert build.build(2025) == 0
    assert {name: rows_of(reports, name) for name in before} == before, "carried as published"
    (change,) = changes_of(reports)
    assert (change["change"], change["rows"], change["now"]) == ("replaced", "filings", sha)
    assert (
        change["was"]
        == json.loads(before["filings"]["fl:house-clerk:P:20000001"])["source"]["content_hash"]
    )
    assert f"{sha}.pdf" in kept(reports), "the bytes that show it are kept"
    assert build.build(2025) == 0 and len(changes_of(reports)) == 1, "once"


def test_other_bytes_that_read_the_same_change_nothing(reports):
    before = {name: rows_of(reports, name) for name in ("filings", "transactions")}
    document(
        reports,
        "20000001",
        ADA,
        [TX, dict(TX, asset="Other Holdings")],
        "2026-02-02T00:00:00Z",
        pad="\n",
    )
    assert build.build(2025) == 0
    assert {name: rows_of(reports, name) for name in before} == before
    assert not changes_of(reports)


def test_a_document_first_read_later_adds_its_facts_and_rows(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(build, "load_ptr", lambda: StubReader)
    captures(
        tmp_path,
        roster_xml(119, [ADA], "20250103"),
        index_xml([(ADA, "20000001", "P", "3/1/2025")]),
        "2026-01-05T00:00:00Z",
        "2026-01-05T00:00:01Z",
    )
    assert build.build(2025) == 0
    first = json.loads(rows_of(tmp_path, "filings")["fl:house-clerk:P:20000001"])
    assert first["source"]["content_hash"] is None and first["extraction_confidence"] is None
    sha = document(tmp_path, "20000001", ADA, [TX], "2026-02-02T00:00:00Z")
    assert build.build(2025) == 0
    now = json.loads(rows_of(tmp_path, "filings")["fl:house-clerk:P:20000001"])
    assert now["source"]["content_hash"] == sha and now["extraction_confidence"] == "structured"
    assert {k: v for k, v in now.items() if k not in ("source", "extraction_confidence")} == {
        k: v for k, v in first.items() if k not in ("source", "extraction_confidence")
    }
    assert list(rows_of(tmp_path, "transactions")) == ["tx:house-clerk:20000001:001"]
    assert not changes_of(tmp_path), "facts it lacked, filled; nothing changed"
