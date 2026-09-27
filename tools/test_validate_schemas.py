"""Tests for tools/validate-schemas.py.

The repository's own schemas must pass the meta-check and their examples must
validate. A fixture register built in a temporary directory then exercises every
rule the validator enforces, red first: a broken schema, a dangling reference, an
unknown keyword, and rows that break each kind of rule with the field path named.
"""

from __future__ import annotations

import copy
import importlib.util
import json
import re
import shutil
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def load():
    spec = importlib.util.spec_from_file_location("validate_schemas", HERE / "validate-schemas.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


vs = load()
SCHEMAS = vs.load_schemas(ROOT)
EXAMPLE = SCHEMAS["officeholder.schema.json"]["examples"][0]


def test_repository_schemas_pass_the_meta_check():
    for name, schema in SCHEMAS.items():
        assert vs.check_schema(name, schema, SCHEMAS) == [], name


def test_officeholder_example_validates():
    assert (
        vs.validate(
            EXAMPLE, SCHEMAS["officeholder.schema.json"], SCHEMAS, "officeholder.schema.json"
        )
        == []
    )


def test_required_field_missing_names_the_path():
    row = copy.deepcopy(EXAMPLE)
    del row["source"]
    errors = vs.validate(
        row, SCHEMAS["officeholder.schema.json"], SCHEMAS, "officeholder.schema.json"
    )
    assert errors == ["$.source: required field is missing"]


def test_extra_field_is_rejected():
    row = copy.deepcopy(EXAMPLE)
    row["verdict"] = "none"
    errors = vs.validate(
        row, SCHEMAS["officeholder.schema.json"], SCHEMAS, "officeholder.schema.json"
    )
    assert errors == ["$.verdict: field is not allowed by the schema"]


def test_nested_office_errors_carry_the_full_path():
    row = copy.deepcopy(EXAMPLE)
    row["offices"][0]["jurisdiction"] = "us:galactic"
    row["offices"][0]["term_start"] = "2025-13-01"
    errors = vs.validate(
        row, SCHEMAS["officeholder.schema.json"], SCHEMAS, "officeholder.schema.json"
    )
    assert any(e.startswith("$.offices[0].jurisdiction:") for e in errors)
    assert any(e.startswith("$.offices[0].term_start:") and "date" in e for e in errors)


def test_retrieval_time_must_be_utc():
    row = copy.deepcopy(EXAMPLE)
    row["source"]["retrieved_at"] = "2026-09-21T00:00:00+02:00"
    errors = vs.validate(
        row, SCHEMAS["officeholder.schema.json"], SCHEMAS, "officeholder.schema.json"
    )
    assert errors == ["$.source.retrieved_at: '2026-09-21T00:00:00+02:00' is not a valid date-time"]
    row["source"]["retrieved_at"] = "2026-09-21T00:00:00Z"
    assert (
        vs.validate(row, SCHEMAS["officeholder.schema.json"], SCHEMAS, "officeholder.schema.json")
        == []
    )


def test_null_is_allowed_where_the_schema_says_so_and_nowhere_else():
    row = copy.deepcopy(EXAMPLE)
    row["party"] = None
    assert (
        vs.validate(row, SCHEMAS["officeholder.schema.json"], SCHEMAS, "officeholder.schema.json")
        == []
    )
    row["legal_name"] = None
    errors = vs.validate(
        row, SCHEMAS["officeholder.schema.json"], SCHEMAS, "officeholder.schema.json"
    )
    assert errors == ["$.legal_name: expected type string, got NoneType"]


def test_pattern_enum_const_minimum_and_min_items():
    schema = SCHEMAS["filing.schema.json"]
    row = {
        "id": "not-a-filing-id",
        "officeholder_id": EXAMPLE["id"],
        "form_type": "House-Napkin",
        "filed_at": "2026-01-01",
        "source": EXAMPLE["source"],
        "evidence_bundle": {
            "bundle_path": "data/captures/x/",
            "content_hash": "abc",
            "hash_algorithm": "md5",
            "witnesses": [],
        },
    }
    errors = vs.validate(row, schema, SCHEMAS, "filing.schema.json")
    joined = "\n".join(errors)
    assert "$.id:" in joined and "pattern" in joined
    assert "$.form_type:" in joined and "allowed values" in joined
    assert "$.evidence_bundle.content_hash:" in joined
    assert "$.evidence_bundle.hash_algorithm: must equal 'sha256'" in errors
    assert "$.evidence_bundle.witnesses: needs at least 1 items, has 0" in errors
    holding = {
        "id": "h",
        "filing_id": "f",
        "asset": "X",
        "category": "etf",
        "owner": "self",
        "value_range": {"min": -5, "max": None},
    }
    errors = vs.validate(holding, SCHEMAS["holding.schema.json"], SCHEMAS, "holding.schema.json")
    assert errors == ["$.value_range.min: -5 is below the minimum 0"]


def test_meta_check_catches_a_required_field_absent_from_properties():
    broken = copy.deepcopy(SCHEMAS["office.schema.json"])
    broken["required"].append("nope")
    problems = vs.check_schema(
        "office.schema.json", broken, {**SCHEMAS, "office.schema.json": broken}
    )
    assert problems == ["office.schema.json at #: required field 'nope' is not in properties"]


def test_meta_check_catches_an_unknown_keyword_and_a_dangling_ref():
    broken = copy.deepcopy(SCHEMAS["filing.schema.json"])
    broken["properties"]["filed_at"]["oneOf"] = []
    broken["properties"]["source"]["$ref"] = "nowhere.schema.json#/$defs/Source"
    problems = vs.check_schema(
        "filing.schema.json", broken, {**SCHEMAS, "filing.schema.json": broken}
    )
    assert any("keyword 'oneOf' is not in the validated subset" in p for p in problems)
    assert any("nowhere.schema.json" in p for p in problems)


def test_meta_check_catches_an_example_that_fails_its_own_schema():
    broken = copy.deepcopy(SCHEMAS["officeholder.schema.json"])
    broken["examples"][0]["id"] = "bad id"
    problems = vs.check_schema(
        "officeholder.schema.json", broken, {**SCHEMAS, "officeholder.schema.json": broken}
    )
    assert problems and problems[0].startswith(
        "officeholder.schema.json: examples[0] does not validate: $.id:"
    )


def test_meta_check_catches_a_wrong_id():
    broken = copy.deepcopy(SCHEMAS["office.schema.json"])
    broken["$id"] = "https://oath.jeb2-spec.dev/schemas/officer/v0.json"
    problems = vs.check_schema("office.schema.json", broken, SCHEMAS)
    assert problems == ["office.schema.json: $id names 'officer' but the file is 'office'"]


@pytest.fixture
def register(tmp_path: Path) -> Path:
    shutil.copytree(ROOT / "schemas", tmp_path / "schemas")
    (tmp_path / "data").mkdir()
    return tmp_path


def test_rows_are_validated_with_file_and_line(register: Path):
    good = json.dumps(EXAMPLE)
    bad = json.dumps({**EXAMPLE, "id": "bad id"})
    (register / "data" / "officeholders.ndjson").write_text(
        f"{good}\n\n{bad}\nnot json\n", encoding="utf-8", newline="\n"
    )
    problems, rows, files = vs.check_rows(register, vs.load_schemas(register))
    assert (rows, files) == (3, 1)
    assert problems[0].startswith("data/officeholders.ndjson:3: $.id:")
    assert problems[1].startswith("data/officeholders.ndjson:4: not valid JSON")
    assert len(problems) == 2


def test_unregistered_data_file_is_reported(register: Path):
    (register / "data" / "mystery.ndjson").write_text("{}\n", encoding="utf-8", newline="\n")
    problems, _, _ = vs.check_rows(register, vs.load_schemas(register))
    assert problems == ["data/mystery.ndjson: no schema is registered for this file"]


def test_main_on_the_repository_is_green(capsys):
    """Green on the real register. It stopped being empty when the House index landed."""
    assert vs.main([str(ROOT)]) == 0
    out = capsys.readouterr().out
    # The count is the tool's, not this line's: read it from the message rather than pin a
    # number that a new schema silently makes false.
    said = re.search(r"OK    (\d+) schemas valid; ([\d,]+) rows across (\d+) NDJSON", out)
    assert said, out
    assert int(said.group(1)) == len(SCHEMAS) >= 9
    assert int(said.group(3)) == len(list((ROOT / "data").glob("*.ndjson")))
    assert "rows across" in out and "NDJSON files validated" in out


def test_main_reports_failures_and_exits_nonzero(register: Path, capsys):
    (register / "data" / "offices.ndjson").write_text(
        json.dumps({"id": "of:us:x:2025", "jurisdiction": "us:federal"}) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    assert vs.main([str(register)]) == 1
    out = capsys.readouterr().out
    assert "FAIL  data/offices.ndjson:1: $.term_start: required field is missing" in out


def test_a_repeated_id_within_a_file_is_refused(tmp_path):
    """An id is a key. The Clerk's index once listed a DocID twice; the register must not."""
    vs = load()
    root = Path(__file__).resolve().parent.parent
    schemas = vs.load_schemas(root)
    first = (root / "data" / "officeholders.ndjson").read_text(encoding="utf-8").splitlines()[0]
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "officeholders.ndjson").write_text(
        first + "\n" + first + "\n", encoding="utf-8"
    )
    problems, rows, files = vs.check_rows(tmp_path, schemas)
    assert rows == 2 and files == 1
    assert any("already appears at line 1; an id is a key" in p for p in problems), problems


def test_the_rows_must_agree_with_one_another(tmp_path):
    """The Council's third reading of S.1b (Seat C, N-5): the check that the rows agree could
    be deleted without a test failing. Each disagreement it exists to find, found."""
    data = tmp_path / "data"
    data.mkdir()

    def write(name: str, *rows: dict) -> None:
        (data / f"{name}.ndjson").write_text("".join(json.dumps(r) + "\n" for r in rows), "utf-8")

    holder = {"id": "oh:1", "offices": [{"id": "of:1"}]}
    write("officeholders", holder)
    write(
        "filings",
        {"id": "fl:1", "officeholder_id": "oh:1", "office_id": "of:1"},
        {"id": "fl:2", "officeholder_id": "oh:9", "office_id": "of:1"},
        {"id": "fl:3", "officeholder_id": "oh:1", "office_id": "of:9"},
    )
    write(
        "transactions",
        {"id": "tx:1", "filing_id": "fl:1", "officeholder_id": "oh:1"},
        {"id": "tx:2", "filing_id": "fl:9", "officeholder_id": "oh:1"},
        {"id": "tx:3", "filing_id": "fl:1", "officeholder_id": "oh:2"},
    )
    write(
        "changes",
        {"id": "ch:1", "row_id": "fl:1", "rows": "filings"},
        {"id": "ch:2", "row_id": "fl:9", "rows": "filings"},
    )
    found = vs.joins(tmp_path)
    for says in (
        "fl:2 names oh:9, whom the register does not hold",
        "fl:3 is at of:9, an office oh:1 does not hold",
        "tx:2 names the filing fl:9",
        "tx:3 names oh:2, and its filing names oh:1",
        "ch:2 is about fl:9",
    ):
        assert any(says in line for line in found), says
    assert len(found) == 5, found


def test_validation_reports_rows_that_disagree(tmp_path):
    """The check runs with every validation, not only when asked for by name."""
    data = tmp_path / "data"
    data.mkdir()
    (data / "filings.ndjson").write_text(
        json.dumps({"id": "fl:9", "officeholder_id": "oh:9", "office_id": "of:9"}) + "\n", "utf-8"
    )
    problems, _, _ = vs.check_rows(tmp_path, SCHEMAS)
    assert any("fl:9 names oh:9, whom the register does not hold" in p for p in problems)


def test_min_length_refuses_what_a_gate_would_refuse():
    """A field a gate rejects as empty, or as a label where a reason belongs, is a field the schema
    rejects too. Two rules that disagree about one row are one rule a contributor cannot rely on,
    and the looser of the two is the one a future row will satisfy (INVARIANTS §2, §17).

    The case that needed it: `because` on a doctrine amendment. §17 asks the reason to say what the
    current text costs and what the change is expected to fix; the gate refuses a reason under
    twelve words, and before this the schema would have taken `""`.
    """
    schema = SCHEMAS["doctrine-amendment.schema.json"]
    good = schema["examples"][0]
    assert vs.validate(good, schema, SCHEMAS, "doctrine-amendment.schema.json") == []
    errors = vs.validate(
        dict(good, because="Cleanup.", approved_by="", sections=[""]),
        schema,
        SCHEMAS,
        "doctrine-amendment.schema.json",
    )
    joined = "\n".join(errors)
    assert "$.because: 8 characters, and this field needs at least 60" in errors
    assert "$.approved_by:" in joined and "needs at least 3" in joined
    assert "$.sections[0]:" in joined and "needs at least 1" in joined
    # And the gate refuses the same row, for the same reasons, in its own words.
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "hcc", Path(__file__).resolve().parents[1] / "tools/highlight-charter-change.py"
    )
    gate = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gate)
    assert gate.incomplete(good) == []
    assert any(
        "a reason, not a label" in g for g in gate.incomplete(dict(good, because="Cleanup."))
    )
    assert "approved_by" in gate.incomplete(dict(good, approved_by=""))


def test_a_hyphenated_schema_name_is_a_valid_id():
    """Schema names were single words until a row needed two. "amendments" alone would have read as
    a filer amending a report, which `amends` on a filing already means."""
    assert vs.ID_RULE.match("https://oath.jeb2-spec.dev/schemas/doctrine-amendment/v0.json")
    assert vs.ID_RULE.match("https://oath.jeb2-spec.dev/schemas/change/v0.json")
    assert not vs.ID_RULE.match("https://oath.jeb2-spec.dev/schemas/Doctrine_Amendment/v0.json")
    assert not vs.ID_RULE.match("https://oath.jeb2-spec.dev/schemas/-leading/v0.json")
