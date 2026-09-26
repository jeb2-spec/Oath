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


def roster_xml(congress: int, members: list[dict], sworn: str, seats=("XX01", "XX02", "XX03")):
    held = {m["seat"]: m for m in members}
    out = [f"<MemberData><title-info><congress-num>{congress}</congress-num></title-info><members>"]
    for seat in seats:
        m = held.get(seat)
        info = (
            f"<member-info><bioguideID>{m['bioguide']}</bioguideID>"
            f"<lastname>{m['last']}</lastname><firstname>{m['first']}</firstname>"
            f"<middlename/><official-name>{m['first']} {m['last']}</official-name>"
            f"<namelist>{m['last']}, {m['first']}</namelist><party>I</party>"
            f'<district>1st</district><sworn-date date="{sworn}"/></member-info>'
            if m
            else "<member-info><bioguideID/></member-info>"
        )
        out.append(f"<member><statedistrict>{seat}</statedistrict>{info}</member>")
    return "".join(out) + "</members></MemberData>"


def index_xml(rows: list[tuple[dict, str]], year: int = 2025) -> str:
    out = ["<FinancialDisclosure>"]
    for m, doc_id in rows:
        out.append(
            f"<Member><Last>{m['last']}</Last><First>{m['first']}</First><Suffix/>"
            f"<FilingType>O</FilingType><StateDst>{m['seat']}</StateDst><Year>{year}</Year>"
            f"<FilingDate>5/15/{year + 1}</FilingDate><DocID>{doc_id}</DocID></Member>"
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
        manifest[key] = {
            "url": url,
            "retrieved_at": at,
            "sha256": hashlib.sha256(text.encode()).hexdigest(),
        }
    (cache / "capture.json").write_text(json.dumps(manifest), encoding="utf-8")


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
    bea, bea_filing = "oh:us:house:x000002", "fl:house-clerk:O:30000002"
    captures(
        register,
        roster_xml(119, [ADA], "20250103"),
        index_xml([(ADA, "30000001"), (BEA, "30000002")]),
        "2026-02-02T00:00:00Z",
        "2026-02-02T00:00:01Z",
    )
    assert build.build(2025) == 0
    after = {name: rows_of(register, name) for name in ("officeholders", "filings", "offices")}
    assert after["officeholders"][bea] == before["officeholders"][bea], "carried as published"
    assert after["filings"][bea_filing] == before["filings"][bea_filing], "its attribution stands"
    assert set(after["offices"]) == set(before["offices"])
    (change,) = [json.loads(line) for line in rows_of(register, "changes").values()]
    assert (change["row_id"], change["rows"], change["change"]) == (
        bea,
        "officeholders",
        "not listed",
    )
    assert change["capture"]["retrieved_at"] == "2026-02-02T00:00:00Z"
    (rejected,) = (register / "data" / "rejected" / "house-fd").glob("2025-*.ndjson")
    assert "30000002" not in rejected.read_text("utf-8"), "a carried filing is not set aside too"
    record = run_record(register)
    assert record["carried"]["officeholders"] == 1 and record["carried"]["filings"] == 1
    assert record["changes"] == {"not listed": 1}

    # The roster lists her again: the change is recorded, and the first one stays.
    captures(
        register,
        roster_xml(119, [ADA, BEA], "20250103"),
        index_xml([(ADA, "30000001"), (BEA, "30000002")]),
        "2026-03-02T00:00:00Z",
        "2026-03-02T00:00:01Z",
    )
    assert build.build(2025) == 0
    changes = [json.loads(line) for line in rows_of(register, "changes").values()]
    assert [c["change"] for c in changes] == ["not listed", "listed again"]
    assert run_record(register)["carried"]["officeholders"] == 0


def test_a_filing_the_index_stops_listing_stays_and_the_change_is_shown(register):
    before = rows_of(register, "filings")
    captures(
        register,
        roster_xml(119, [ADA, BEA], "20250103"),
        index_xml([(ADA, "30000001")]),
        "2026-01-05T00:00:00Z",
        "2026-02-09T00:00:00Z",
    )
    assert build.build(2025) == 0
    assert (
        rows_of(register, "filings")["fl:house-clerk:O:30000002"]
        == before["fl:house-clerk:O:30000002"]
    )
    (change,) = [json.loads(line) for line in rows_of(register, "changes").values()]
    assert (change["rows"], change["change"]) == ("filings", "not listed")
    assert change["capture"]["url"].endswith("2025FD.zip")


def test_a_closed_year_is_carried_and_never_rebuilt_from_the_next_roster(register):
    """The 120th Congress's roster must not re-derive the 119th's rows: its office ids and
    swearing-in dates would put every 2025 transaction before the swearing-in."""
    before = {name: rows_of(register, name) for name in ("officeholders", "filings", "offices")}
    captures(
        register,
        roster_xml(120, [ADA, CAL], "20270103"),
        index_xml([(ADA, "30000001"), (BEA, "30000002"), (CAL, "30000003")]),
        "2027-01-11T00:00:00Z",
        "2027-01-11T00:00:01Z",
    )
    assert build.build(2025) == 0
    after = {name: rows_of(register, name) for name in ("officeholders", "filings", "offices")}
    assert after == before, "every row of the closed year, byte for byte"
    assert not rows_of(register, "changes"), "the year's roster was not read; nothing observed"
    (rejected,) = (register / "data" / "rejected" / "house-fd").glob("2025-*.ndjson")
    set_aside = [json.loads(line) for line in rejected.read_text("utf-8").splitlines()]
    assert [r["source_row"]["doc_id"] for r in set_aside] == ["30000003"]
    assert "is of the 119th Congress" in set_aside[0]["reason"]
    assert "lists the 120th" in set_aside[0]["reason"]
    record = run_record(register)
    assert record["congress"] == {"filing_year": 119, "roster": 120, "closed": True}
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
