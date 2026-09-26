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


def later(register, members, rows, at, index=None):
    """Captures of a later read: the roster of `members`, the index of `rows`."""
    captures(
        register,
        roster_xml(119, members, "20250103"),
        index if index is not None else index_xml(rows),
        at,
        at.replace(":00Z", ":01Z"),
    )


def test_a_parser_that_drops_what_the_bytes_still_carry_refuses(register, monkeypatch):
    """The Council's second reading of S.1b (Seat C, R-1): the Clerk serves bytes that still
    carry a Member and a filing, and a change in the register's own parsers drops them. That
    is the register's reading, never the source's: the build refuses, and nothing is written."""
    rows = [(ADA, "30000001"), (BEA, "30000002"), (CAL, "30000003")]
    later(register, [ADA, BEA, CAL], rows, "2026-02-02T00:00:00Z")
    real_roster, real_index = build.load_roster, build.load_index

    def drops_bea(path):
        seats, people = real_roster(path)
        return seats, [p for p in people if p["bioguide"] != "X000002"]

    monkeypatch.setattr(build, "load_roster", drops_bea)
    with pytest.raises(SystemExit, match="carry an entry for oh:us:house:x000002"):
        build.build(2025)
    monkeypatch.setattr(build, "load_roster", real_roster)
    monkeypatch.setattr(
        build, "load_index", lambda path: [r for r in real_index(path) if r["doc_id"] != "30000002"]
    )
    with pytest.raises(SystemExit, match="carry an entry for fl:house-clerk:O:30000002"):
        build.build(2025)
    assert not changes_of(register)


def test_a_fact_misread_from_an_unchanged_entry_refuses_and_a_changed_entry_is_recorded(
    register, monkeypatch
):
    """Seat C, R-5: the roster's bytes change for another Member, and a change in the
    register's reading gives this Member's name otherwise. Her own entry is unchanged, so the
    source said nothing new about her, and the build refuses. Where her entry itself changes,
    the change is recorded, naming the entry it was read from."""
    rows = [(ADA, "30000001"), (BEA, "30000002")]
    later(register, [ADA, BEA, CAL], rows, "2026-02-02T00:00:00Z")
    real = build.load_roster

    def misread(path):
        seats, people = real(path)
        return seats, [
            dict(p, official_name="Beatrix Placeholder") if p["bioguide"] == "X000002" else p
            for p in people
        ]

    monkeypatch.setattr(build, "load_roster", misread)
    with pytest.raises(SystemExit, match="x000002 was last read from is unchanged"):
        build.build(2025)
    monkeypatch.setattr(build, "load_roster", real)
    later(register, [ADA, dict(BEA, first="Beatrix"), CAL], rows, "2026-02-09T00:00:00Z")
    assert build.build(2025) == 0
    changes = changes_of(register)
    assert {c["field"] for c in changes} == {"legal_name", "common_name"}
    entry = build.roster_entries(register / "data" / "cache" / "house-fd" / "MemberData.xml")
    assert {c["entry_sha256"] for c in changes} == {entry["X000002"]}
    assert all(c["before_content_hash"] for c in changes), "the bytes last built from, named"


def test_a_decided_fact_is_quiet_on_an_unchanged_entry_and_observed_when_it_changes(
    register, monkeypatch
):
    """Seat C, R-11: the maintainer's recorded decision that a fact stands silences the
    refusal on an unchanged entry; it never silences what the source's own bytes later show."""
    stands = {
        "id": "ch:corrected:oh:us:house:x000002:legal_name:2026-02-01T00:00:00Z",
        "row_id": "oh:us:house:x000002",
        "rows": "officeholders",
        "change": "corrected",
        "field": "legal_name",
        "was": "Bea Placeholder",
        "now": "Bea Placeholder",
        "kind": "register",
        "because": "The roster prints the name as published; the new reading is the register's.",
        "decided_by": "the maintainer",
        "decided_at": "2026-02-01T00:00:00Z",
        "capture": {
            "url": "https://clerk.house.gov/xml/lists/MemberData.xml",
            "retrieved_at": "2026-02-01T00:00:00Z",
            "content_hash": "0" * 64,
        },
        "frame": build.FRAME,
    }
    (register / "data" / "changes.ndjson").write_text(build.canonical(stands), encoding="utf-8")
    rows = [(ADA, "30000001"), (BEA, "30000002")]
    later(register, [ADA, BEA, CAL], rows, "2026-02-02T00:00:00Z")
    real = build.load_roster

    def misread(path):
        seats, people = real(path)
        return seats, [
            dict(p, official_name="Beatrix Placeholder") if p["bioguide"] == "X000002" else p
            for p in people
        ]

    monkeypatch.setattr(build, "load_roster", misread)
    assert build.build(2025) == 0, "the decision stands: no refusal"
    assert changes_of(register) == [stands], "and nothing recorded from an unchanged entry"
    monkeypatch.setattr(build, "load_roster", real)
    later(register, [ADA, dict(BEA, first="Beatrix"), CAL], rows, "2026-02-09T00:00:00Z")
    assert build.build(2025) == 0
    assert {c["field"] for c in changes_of(register)[1:]} == {"legal_name", "common_name"}


def test_rows_name_the_entry_they_were_read_from_and_a_published_row_gains_it(register):
    """Each new row names its entry in the source's bytes. A row published before entries
    were kept gains it from the first later entry that states the facts it carries, and a row
    that entry states otherwise does not."""
    cache = register / "data" / "cache" / "house-fd"
    holders = {k: json.loads(v) for k, v in rows_of(register, "officeholders").items()}
    filings = {k: json.loads(v) for k, v in rows_of(register, "filings").items()}
    assert (
        holders["oh:us:house:x000001"]["roster_entry_sha256"]
        == (build.roster_entries(cache / "MemberData.xml")["X000001"])
    )
    assert (
        filings["fl:house-clerk:O:30000001"]["index_entry_sha256"]
        == (build.index_entries(cache / "2025FD.xml")["30000001"])
    )
    for name, key in (("officeholders", "roster_entry_sha256"), ("filings", "index_entry_sha256")):
        stripped = []
        for line in rows_of(register, name).values():
            row = json.loads(line)
            row.pop(key)
            row.pop("index_row", None)
            stripped.append(build.canonical(row))
        (register / "data" / f"{name}.ndjson").write_text("".join(stripped), encoding="utf-8")
    later(
        register,
        [ADA, dict(BEA, party="D"), CAL],
        [(ADA, "30000001"), (BEA, "30000002")],
        "2026-02-02T00:00:00Z",
    )
    assert build.build(2025) == 0
    holders = {k: json.loads(v) for k, v in rows_of(register, "officeholders").items()}
    assert "roster_entry_sha256" in holders["oh:us:house:x000001"]
    assert "roster_entry_sha256" not in holders["oh:us:house:x000002"], (
        "an entry that states a fact otherwise is not the one the row was read from"
    )
    filings = {k: json.loads(v) for k, v in rows_of(register, "filings").items()}
    assert all("index_entry_sha256" in f and "index_row" in f for f in filings.values())


def test_a_row_the_index_lists_under_another_year_is_set_aside_with_the_reason(register):
    """Seat C, C-10: a row of the 2025 index whose Year column says 2024 would take another
    year's document URL, and a later build could not tell whose index it came from."""
    index = index_xml([(ADA, "30000001"), (BEA, "30000002"), (CAL, "30000005")]).replace(
        "<Year>2025</Year><FilingDate>5/15/2026</FilingDate><DocID>30000005",
        "<Year>2024</Year><FilingDate>5/15/2026</FilingDate><DocID>30000005",
    )
    later(register, [ADA, BEA, CAL], [], "2026-02-02T00:00:00Z", index=index)
    assert build.build(2025) == 0
    assert "fl:house-clerk:O:30000005" not in rows_of(register, "filings")
    (rejected,) = (register / "data" / "rejected" / "house-fd").glob("2025-*.ndjson")
    reasons = {
        json.loads(line)["source_row"]["doc_id"]: json.loads(line)["reason"]
        for line in rejected.read_text("utf-8").splitlines()
    }
    assert reasons["30000005"] == (
        "the Clerk's 2025 index lists this row under year 2024; the register attributes a row "
        "of an index only where the row's year is the index's own"
    )


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
    assert reasons["30000010"].startswith(
        "the maintainer's recorded decision names an officeholder the roster stopped listing, "
        "for a filing the index dates after the last roster read that listed them; the register "
        "cannot show them in office after that read, and under SUBJECTS.md §1 it enters no new "
        "filing for an officeholder after their term ("
    ), "grouped without the person: the id and the dates are in the parentheses"
    assert reasons["30000010"].endswith(
        "(oh:us:house:x000002; dated 2026-03-01; last listed 2026-01-05)"
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
    assert "the Clerk's roster read 2027-01-11 lists the 120th" in set_aside["30000003"]
    record = run_record(register)
    closing = json.loads(
        (register / "data" / "cache" / "house-fd" / "capture.json").read_text("utf-8")
    )["MemberData.xml"]
    assert record["congress"] == {
        "filing_year": 119,
        "roster": 120,
        "closed": True,
        "last_roster_read": "2026-06-01T00:00:00Z",
        "closed_by": {
            "url": closing["url"],
            "retrieved_at": "2027-01-11T00:00:00Z",
            "sha256": closing["sha256"],
            "congress": 120,
        },
    }, (
        "the last roster of the year's own Congress the register read, carried, and the read "
        "that closed it"
    )
    assert f"{closing['sha256']}.xml" in kept(register), "the roster that closed the year is kept"
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


def test_a_reading_that_finds_rows_after_every_published_one_adds_them(reports, monkeypatch):
    """Seat C, R-8: the same bytes, read by a reader that now finds a trade the first reading
    missed, after every published row. The published rows stand as they were; the new one is
    a fact the register lacked, added, and never a change at the source. A row found anywhere
    but after them would move a published row, and refuses."""
    before = rows_of(reports, "transactions")
    third = dict(TX, asset="Third Holdings")
    monkeypatch.setattr(StubReader, "rows", staticmethod(lambda tx: [*tx, third]))
    assert build.build(2025) == 0
    after = rows_of(reports, "transactions")
    assert {k: after[k] for k in before} == before
    assert list(after) == [*before, "tx:house-clerk:20000001:003"]
    assert json.loads(after["tx:house-clerk:20000001:003"])["asset"] == "Third Holdings"
    assert not changes_of(reports)
    monkeypatch.setattr(StubReader, "rows", staticmethod(lambda tx: [tx[0], third, *tx[1:]]))
    with pytest.raises(SystemExit, match="the register's reading did"):
        build.build(2025)


def test_a_row_its_document_refused_keeps_its_reason_when_the_year_closes(reports):
    """Seat C on the second reading: a row the document refused carries its DocID, not the
    index row, so a closed year's build set it aside again with the closed reason and lost
    why it had been refused."""
    index = index_xml([(ADA, "20000001", "P", "3/1/2025"), (ADA, "20000002", "P", "3/2/2025")])
    later(reports, [ADA], [], "2026-02-02T00:00:00Z", index=index)
    sha = document(reports, "20000002", ADA, [TX], "2026-02-02T00:00:02Z")
    body = (reports / "data/cache/house-fd/docs/20000002.pdf").read_text("utf-8")
    wrong = body.replace("Filing ID #20000002", "Filing ID #29999999")
    (reports / "data/cache/house-fd/docs/20000002.pdf").write_text(wrong, encoding="utf-8")
    manifest = reports / "data/cache/house-fd/docs/captures.json"
    captured = json.loads(manifest.read_text("utf-8"))
    captured["20000002"]["sha256"] = hashlib.sha256(wrong.encode()).hexdigest()
    manifest.write_text(json.dumps(captured), encoding="utf-8")
    assert sha != captured["20000002"]["sha256"]
    assert build.build(2025) == 0

    def reasons():
        (path,) = (reports / "data" / "rejected" / "house-fd").glob("2025-*.ndjson")
        return {
            json.loads(line)["source_row"]["doc_id"]: json.loads(line)["reason"]
            for line in path.read_text("utf-8").splitlines()
        }

    refused = reasons()["20000002"]
    assert refused.startswith("the document refused the attribution")
    captures(
        reports,
        roster_xml(120, [ADA], "20270103"),
        index,
        "2027-01-11T00:00:00Z",
        "2027-01-11T00:00:01Z",
    )
    assert build.build(2025) == 0
    assert reasons()["20000002"] == refused, "the reason it was refused for, kept"


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


# ---- the adapter's own output, sealed and validated as the refresh does it -----------------
#
# The Council's second reading of S.1b found that the seal refused the very departure and
# closed year S.1b exists for, while every test passed: the seal's tests built run records
# the adapter does not write. These run the adapter, then the seal with its state derived,
# then the schema validator, on the same tree (Seats A, C, E, F and G).

ROOT = HERE.parents[2]


def tool(name: str):
    spec = importlib.util.spec_from_file_location(
        name.replace("-", "_"), ROOT / "tools" / f"{name}.py"
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def sealed(root: Path, build_id: str, built_at: str) -> str:
    """Seal the tree as the refresh does and return its state; validate every row first."""
    validator = tool("validate-schemas")
    problems, rows, _ = validator.check_rows(root, validator.load_schemas(ROOT))
    assert not problems and rows, problems[:5]
    seal = tool("seal")
    verify = seal.load_verify(ROOT / "tools")
    for name in verify.DOCTRINE:
        (root / name).write_text(f"{name}, as sealed for the test\n", encoding="utf-8")
    meta = root / "data" / "meta.json"
    if not meta.is_file():
        meta.write_text("{}\n", encoding="utf-8")
    digest = seal.seal(root, build_id, built_at, derive=True)
    assert verify.compute_digest(root) == digest
    return json.loads(meta.read_text("utf-8"))["state"]


def test_a_departure_builds_seals_and_validates(register):
    sealed(register, "0001-house-2025", "2026-01-05T00:00:01Z")
    later(
        register,
        [ADA, CAL],
        [(ADA, "30000001"), (BEA, "30000002"), (CAL, "30000003")],
        "2026-02-02T00:00:00Z",
    )
    assert build.build(2025) == 0
    state = sealed(register, "0002-house-2025", "2026-02-02T00:00:01Z")
    assert state.startswith(
        "The register holds 3 offices, 3 officeholders, 3 filings and 0 transactions."
    ), "every officeholder the register holds, the one the roster stopped listing among them"
    assert "2 of them filled and 1 vacant on the Clerk's roster read 2026-02-02" in state
    assert "1 change is recorded" in state and "1 no longer listed by a later capture" in state
    (change,) = changes_of(register)
    assert change["build"] == "0002-house-2025", "stamped with the build that sealed it"
    assert (
        tool("check-removals").problems(
            "data/officeholders.ndjson",
            list(map(json.loads, rows_of(register, "officeholders").values())),
            [],
        )
        == []
    )


def test_a_closed_year_after_a_departure_builds_seals_and_validates(register):
    later(register, [ADA], [(ADA, "30000001"), (BEA, "30000002")], "2026-02-02T00:00:00Z")
    assert build.build(2025) == 0
    sealed(register, "0002-house-2025", "2026-02-02T00:00:01Z")
    captures(
        register,
        roster_xml(120, [ADA, CAL], "20270103"),
        index_xml([(ADA, "30000001"), (BEA, "30000002"), (CAL, "30000003")]),
        "2027-01-11T00:00:00Z",
        "2027-01-11T00:00:01Z",
    )
    assert build.build(2025) == 0
    state = sealed(register, "0003-house-2025", "2027-01-11T00:00:01Z")
    assert "The register has closed filing year 2025" in state
    assert "the Clerk's roster read 2027-01-11 listed the 120th" in state
    assert "each with the reason the register gave it when it set the row aside" in state
    assert (
        "Members of the 119th Congress, as its roster listed them when the register last " in state
    )


def test_a_refused_seal_stamps_nothing(register):
    """Seats C and F: a seal that refuses leaves every change row as it was, so no row names
    a build that was never sealed."""
    later(register, [ADA], [(ADA, "30000001"), (BEA, "30000002")], "2026-02-02T00:00:00Z")
    assert build.build(2025) == 0
    before = (register / "data" / "changes.ndjson").read_text("utf-8")
    seal = tool("seal")
    for name in seal.load_verify(ROOT / "tools").DOCTRINE:
        (register / name).write_text("sealed\n", encoding="utf-8")
    (register / "data" / "meta.json").write_text(
        '{"state": "a stale sentence"}\n', encoding="utf-8"
    )
    with pytest.raises(SystemExit, match="refusing to seal"):
        seal.seal(register, "0002-house-2025", "2026-02-02T00:00:01Z")
    assert (register / "data" / "changes.ndjson").read_text("utf-8") == before
