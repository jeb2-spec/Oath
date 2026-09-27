#!/usr/bin/env python3
"""Validate the schemas, and every canonical row against its schema.

Two jobs, one run.

  1. Every file in schemas/ is a well-formed JSON Schema draft 2020-12 in the subset
     this register uses: $schema, $id (https://oath.jeb2-spec.dev/schemas/<name>/v<n>.json,
     matching the file name), type, required (each name present in properties),
     properties, additionalProperties, pattern (compiles), enum (non-empty), const,
     format (date, date-time, uri), items, minItems, minimum, default, $ref (resolves,
     locally or to another file in schemas/), $defs, examples (each one validates
     against its own schema), title, description. Any other keyword fails loudly, so
     nothing is silently ignored.

  2. Every line of every canonical NDJSON file under data/ (officeholders, offices,
     filings, holdings, transactions, findings, signals, changes) validates against its schema.
     An invalid row is reported with its file, line, field path, and the rule it broke,
     as METHODOLOGY.md §2.1 requires. Rows under data/rejected/ are not validated; they
     are the rejects.

  3. The rows agree with one another: every filing names an officeholder the register holds
     and an office that officeholder holds; every transaction names a filing the register
     holds and that filing's officeholder; every change names a row of the file it says.
     A correction that moved one of these facts and not the others would leave a trade on
     one person's page and its report on another's (the Council's second reading of S.1b).

Formats are assertions here, not annotations: INVARIANTS.md §4 requires a retrieval
timestamp in ISO 8601 UTC, so date-time must carry a zero offset. Gate for
INVARIANTS.md §2, §3, §4, and §6. Standard-library Python 3.11+.

Example of a failing input, as one line in data/officeholders.ndjson:

    {"id": "oh:us:x:y", "legal_name": "A", "offices": [], "source": {"url": "u"}}
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

KEYWORDS = {
    "$schema",
    "$id",
    "$ref",
    "$defs",
    "title",
    "description",
    "type",
    "required",
    "properties",
    "additionalProperties",
    "pattern",
    "enum",
    "const",
    "format",
    "items",
    "minItems",
    "maxItems",
    "minLength",
    "minimum",
    "default",
    "examples",
}
TYPES = {"string", "integer", "number", "boolean", "null", "array", "object"}
FORMATS = {"date", "date-time", "uri"}
DRAFT = "https://json-schema.org/draft/2020-12/schema"
# A schema's name is lower case words joined by hyphens: single words until a row needed two
# (doctrine-amendment), and "amendments" alone would have read as a filer amending a report,
# which `amends` on a filing already means.
ID_RULE = re.compile(r"^https://oath\.jeb2-spec\.dev/schemas/([a-z][a-z-]*)/v(\d+)\.json$")
CANONICAL = {
    "officeholders": "officeholder",
    "offices": "office",
    "filings": "filing",
    "holdings": "holding",
    "transactions": "transaction",
    "findings": "finding",
    "signals": "signal",
    "changes": "change",
    # An amendment to the antidrift core is a row of the register like any other: schema'd,
    # sealed, and never edited once published (INVARIANTS §17; tools/highlight-charter-change.py).
    "doctrine-amendments": "doctrine-amendment",
}
# The run records live one directory down, so the glob above never saw them, and every page's
# answer is counted from them: a malformed row would have put a wrong number on a named person's
# page with no gate to say which. The first row of each is the run, the rest are its outcomes, one
# per report (the Council's second reading of the built answer, Seat G).
RUN_RECORDS = "signal-runs"
RUN_ROW, OUTCOME_ROW = "signal-run", "signal-outcome"


def load_schemas(root: Path) -> dict[str, dict]:
    return {
        p.name: json.loads(p.read_text(encoding="utf-8"))
        for p in sorted((root / "schemas").glob("*.schema.json"))
    }


def resolve(ref: str, current: str, schemas: dict[str, dict]) -> tuple[dict, str]:
    """Return (subschema, document name) for a $ref like '#/$defs/X' or 'a.schema.json#/$defs/X'."""
    doc_name, _, pointer = ref.partition("#")
    doc_name = doc_name or current
    if doc_name not in schemas:
        raise KeyError(f"$ref '{ref}' names a schema file that does not exist: {doc_name}")
    node: Any = schemas[doc_name]
    for part in [p for p in pointer.split("/") if p]:
        if not isinstance(node, dict) or part not in node:
            raise KeyError(f"$ref '{ref}' does not resolve at '{part}'")
        node = node[part]
    return node, doc_name


def type_ok(value: Any, name: str) -> bool:
    if name == "null":
        return value is None
    if name == "boolean":
        return isinstance(value, bool)
    if name == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if name == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if name == "string":
        return isinstance(value, str)
    if name == "array":
        return isinstance(value, list)
    return isinstance(value, dict)


def format_ok(value: str, fmt: str) -> bool:
    try:
        if fmt == "date":
            return (
                bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}", value))
                and datetime.strptime(value, "%Y-%m-%d") is not None
            )
        if fmt == "date-time":
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            return parsed.tzinfo is not None and parsed.utcoffset() == timedelta(0)
        if fmt == "uri":
            return bool(re.fullmatch(r"[a-z][a-z0-9+.-]*:\S+", value))
    except ValueError:
        return False
    return True


def validate(
    value: Any, schema: dict, schemas: dict[str, dict], doc: str, path: str = "$"
) -> list[str]:
    """Errors as '<path>: <rule>' strings; empty when the value conforms."""
    if "$ref" in schema:
        target, target_doc = resolve(schema["$ref"], doc, schemas)
        return validate(value, target, schemas, target_doc, path)
    errors: list[str] = []
    if "type" in schema:
        names = schema["type"] if isinstance(schema["type"], list) else [schema["type"]]
        if not any(type_ok(value, n) for n in names):
            return [f"{path}: expected type {' or '.join(names)}, got {type(value).__name__}"]
    if "const" in schema and value != schema["const"]:
        errors.append(f"{path}: must equal {schema['const']!r}")
    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{path}: {value!r} is not one of the allowed values")
    if isinstance(value, str):
        if "pattern" in schema and not re.search(schema["pattern"], value):
            errors.append(f"{path}: {value!r} does not match pattern {schema['pattern']}")
        if "format" in schema and not format_ok(value, schema["format"]):
            errors.append(f"{path}: {value!r} is not a valid {schema['format']}")
        # A field a gate refuses as empty, or as a label where a reason belongs, is a field the
        # schema should refuse too: two rules that disagree about the same row are one rule a
        # reader cannot rely on (INVARIANTS §2, §17).
        if "minLength" in schema and len(value) < schema["minLength"]:
            errors.append(
                f"{path}: {len(value)} characters, and this field needs at least "
                f"{schema['minLength']}"
            )
    is_number = isinstance(value, (int, float)) and not isinstance(value, bool)
    if is_number and "minimum" in schema and value < schema["minimum"]:
        errors.append(f"{path}: {value} is below the minimum {schema['minimum']}")
    if isinstance(value, list):
        if "minItems" in schema and len(value) < schema["minItems"]:
            errors.append(f"{path}: needs at least {schema['minItems']} items, has {len(value)}")
        # A list the code reads as holding one is a list the schema should hold to one. Thirteen
        # places read producing_filings[0], and the schema permitted many (the Council's second
        # reading of the built answer, Seat C).
        if "maxItems" in schema and len(value) > schema["maxItems"]:
            errors.append(
                f"{path}: holds {len(value)} items, and this field takes at most "
                f"{schema['maxItems']}"
            )
        if "items" in schema:
            for i, item in enumerate(value):
                errors += validate(item, schema["items"], schemas, doc, f"{path}[{i}]")
    if isinstance(value, dict):
        props = schema.get("properties", {})
        for name in schema.get("required", []):
            if name not in value:
                errors.append(f"{path}.{name}: required field is missing")
        for name, sub in props.items():
            if name in value:
                errors += validate(value[name], sub, schemas, doc, f"{path}.{name}")
        extra = schema.get("additionalProperties", True)
        for name in value:
            if name in props:
                continue
            if extra is False:
                errors.append(f"{path}.{name}: field is not allowed by the schema")
            elif isinstance(extra, dict):
                errors += validate(value[name], extra, schemas, doc, f"{path}.{name}")
    return errors


def check_schema(name: str, schema: dict, schemas: dict[str, dict]) -> list[str]:
    """Meta-check one schema file. Returns problems as strings."""
    problems: list[str] = []
    if schema.get("$schema") != DRAFT:
        problems.append(f"{name}: $schema must be {DRAFT}")
    match = ID_RULE.match(str(schema.get("$id", "")))
    if not match:
        problems.append(
            f"{name}: $id must look like https://oath.jeb2-spec.dev/schemas/<name>/v<n>.json"
        )
    elif match.group(1) != name.split(".")[0]:
        problems.append(
            f"{name}: $id names '{match.group(1)}' but the file is '{name.split('.')[0]}'"
        )

    def walk(node: dict, where: str) -> None:
        for key in node:
            if key not in KEYWORDS:
                problems.append(
                    f"{name} at {where}: keyword '{key}' is not in the validated subset"
                )
        if "type" in node:
            names = node["type"] if isinstance(node["type"], list) else [node["type"]]
            for t in names:
                if t not in TYPES:
                    problems.append(f"{name} at {where}: unknown type '{t}'")
        if "required" in node and "properties" in node:
            for r in node["required"]:
                if r not in node["properties"]:
                    problems.append(f"{name} at {where}: required field '{r}' is not in properties")
        if "pattern" in node:
            try:
                re.compile(node["pattern"])
            except re.error as exc:
                problems.append(f"{name} at {where}: pattern does not compile ({exc})")
        if "format" in node and node["format"] not in FORMATS:
            problems.append(
                f"{name} at {where}: format '{node['format']}' is not one this register checks"
            )
        if "enum" in node and not (isinstance(node["enum"], list) and node["enum"]):
            problems.append(f"{name} at {where}: enum must be a non-empty list")
        if "$ref" in node:
            try:
                resolve(node["$ref"], name, schemas)
            except KeyError as exc:
                problems.append(f"{name} at {where}: {exc}")
        for key in ("properties", "$defs"):
            for sub_name, sub in node.get(key, {}).items():
                walk(sub, f"{where}/{key}/{sub_name}")
        for key in ("items", "additionalProperties"):
            if isinstance(node.get(key), dict):
                walk(node[key], f"{where}/{key}")

    walk(schema, "#")
    for i, example in enumerate(schema.get("examples", [])):
        for err in validate(example, schema, schemas, name):
            problems.append(f"{name}: examples[{i}] does not validate: {err}")
    return problems


def check_rows(root: Path, schemas: dict[str, dict]) -> tuple[list[str], int, int]:
    """Validate every canonical NDJSON row. Returns (problems, rows, files)."""
    problems: list[str] = []
    rows = files = 0
    for path in sorted((root / "data").glob("*.ndjson")):
        schema_name = CANONICAL.get(path.stem)
        if schema_name is None:
            problems.append(f"data/{path.name}: no schema is registered for this file")
            continue
        schema = schemas[f"{schema_name}.schema.json"]
        files += 1
        seen: dict[str, int] = {}
        with path.open("r", encoding="utf-8") as fh:
            for lineno, line in enumerate(fh, 1):
                if not line.strip():
                    continue
                rows += 1
                try:
                    row = json.loads(line)
                except json.JSONDecodeError as exc:
                    problems.append(f"data/{path.name}:{lineno}: not valid JSON ({exc.msg})")
                    continue
                for err in validate(row, schema, schemas, f"{schema_name}.schema.json"):
                    problems.append(f"data/{path.name}:{lineno}: {err}")
                rid = row.get("id") if isinstance(row, dict) else None
                if isinstance(rid, str):
                    if rid in seen:
                        problems.append(
                            f"data/{path.name}:{lineno}: id {rid!r} already appears at line "
                            f"{seen[rid]}; an id is a key"
                        )
                    seen.setdefault(rid, lineno)
    for path in sorted((root / "data" / RUN_RECORDS).glob("*.ndjson")):
        rel = f"data/{RUN_RECORDS}/{path.name}"
        files += 1
        lines = [ln for ln in path.read_text("utf-8").splitlines() if ln.strip()]
        if not lines:
            problems.append(f"{rel}: a run record with no run row says nothing about a run")
            continue
        seen_reports: dict[str, int] = {}
        for lineno, line in enumerate(lines, 1):
            rows += 1
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                problems.append(f"{rel}:{lineno}: not valid JSON ({exc.msg})")
                continue
            name = RUN_ROW if lineno == 1 else OUTCOME_ROW
            schema = schemas[f"{name}.schema.json"]
            for err in validate(row, schema, schemas, f"{name}.schema.json"):
                problems.append(f"{rel}:{lineno}: {err}")
            if lineno == 1 or not isinstance(row, dict):
                continue
            # One outcome per report: two rows for one report are two answers to one question, and
            # every count the pages state would take whichever the loop reached last.
            report = row.get("filing_id")
            if isinstance(report, str):
                if report in seen_reports:
                    problems.append(
                        f"{rel}:{lineno}: {report} already has an outcome at line "
                        f"{seen_reports[report]}; a report has one"
                    )
                seen_reports.setdefault(report, lineno)
        problems += run_agrees_with_itself(rel, lines)
    return problems + joins(root), rows, files


def run_agrees_with_itself(rel: str, lines: list[str]) -> list[str]:
    """Whether a run record's summary row is the sum of its own outcomes.

    The summary is what the landing states and the outcomes are what each page states, so a summary
    that does not add up is two surfaces disagreeing about one run. Nothing derives one from the
    other at render time, which is exactly why it is checked here (Seat G).
    """
    try:
        run = json.loads(lines[0])
        outcomes = [json.loads(ln) for ln in lines[1:]]
    except json.JSONDecodeError:
        return []  # reported above
    if not isinstance(run, dict) or not all(isinstance(o, dict) for o in outcomes):
        return []
    problems = []
    by_state: dict[str, int] = {}
    for o in outcomes:
        state = o.get("state")
        if isinstance(state, str):
            by_state[state] = by_state.get(state, 0) + 1
    totals = {
        "reports": len(outcomes),
        "reports_by_state": by_state,
        "reports_with_a_finding": sum(1 for o in outcomes if o.get("finding_id")),
        "officeholders_with_a_finding": len(
            {o.get("officeholder_id") for o in outcomes if o.get("finding_id")}
        ),
        "rows_evaluated": sum(o.get("evaluated") or 0 for o in outcomes),
        "rows_after": sum(o.get("after") or 0 for o in outcomes),
        "rows_not_evaluated": {},
    }
    for o in outcomes:
        for reason, n in (o.get("not_evaluated") or {}).items():
            totals["rows_not_evaluated"][reason] = totals["rows_not_evaluated"].get(reason, 0) + (
                n or 0
            )
    for field, counted in totals.items():
        said = run.get(field)
        if said != counted:
            problems.append(
                f"{rel}:1: the run says {field} is {canon(said)} and its own outcomes come to "
                f"{canon(counted)}"
            )
    return problems


def canon(value: object) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False)


def joins(root: Path) -> list[str]:
    """Where the rows disagree with one another about who filed what, and at which office."""

    def rows_of(name: str) -> list[dict]:
        path = root / "data" / f"{name}.ndjson"
        if not path.is_file():
            return []
        out = []
        for line in path.read_text("utf-8").splitlines():
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue  # reported above
        return [row for row in out if isinstance(row, dict)]

    holders = {h.get("id"): h for h in rows_of("officeholders")}
    filings = {f.get("id"): f for f in rows_of("filings")}
    problems = []
    for f in filings.values():
        holder = holders.get(f.get("officeholder_id"))
        if holder is None:
            problems.append(
                f"data/filings.ndjson: {f.get('id')} names {f.get('officeholder_id')}, "
                "whom the register does not hold"
            )
        elif f.get("office_id") not in {o.get("id") for o in holder.get("offices", [])}:
            problems.append(
                f"data/filings.ndjson: {f.get('id')} is at {f.get('office_id')}, an "
                f"office {f.get('officeholder_id')} does not hold"
            )
    for tx in rows_of("transactions"):
        filing = filings.get(tx.get("filing_id"))
        if filing is None:
            problems.append(
                f"data/transactions.ndjson: {tx.get('id')} names the filing "
                f"{tx.get('filing_id')}, which the register does not hold"
            )
        elif tx.get("officeholder_id") != filing.get("officeholder_id"):
            problems.append(
                f"data/transactions.ndjson: {tx.get('id')} names "
                f"{tx.get('officeholder_id')}, and its filing names "
                f"{filing.get('officeholder_id')}"
            )
    ids = {
        name: {row.get("id") for row in rows_of(name)}
        for name in ("officeholders", "filings", "transactions")
    }
    for change in rows_of("changes"):
        if change.get("row_id") not in ids.get(change.get("rows"), set()):
            problems.append(
                f"data/changes.ndjson: {change.get('id')} is about "
                f"{change.get('row_id')}, which data/{change.get('rows')}.ndjson "
                "does not hold"
            )
    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate the schemas in schemas/ and every canonical row under data/.",
        epilog=(
            "Gate: INVARIANTS.md §2 (a Signal cites a Standard), §3 (a Finding names its "
            "producing filings), §4 (a Filing carries a source URL and retrieval time), "
            "§6 (a Signal declares what it does not say), all enforced by the schemas. "
            "Catches: a schema outside the validated subset, a required field absent from "
            "properties, a dangling $ref, an example that fails its own schema, and any "
            "row that breaks any rule. Example failing input: a row missing 'source'."
        ),
    )
    parser.add_argument("root", nargs="?", default=".", help="repository root (default: .)")
    args = parser.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    root = Path(args.root).resolve()

    try:
        schemas = load_schemas(root)
    except json.JSONDecodeError as exc:
        print(f"FAIL  a schema is not valid JSON: {exc}")
        return 1
    problems: list[str] = []
    for name, schema in schemas.items():
        problems += check_schema(name, schema, schemas)
    row_problems, rows, files = check_rows(root, schemas)
    problems += row_problems
    for problem in problems:
        print(f"FAIL  {problem}")
    if problems:
        print(f"\n{len(problems)} problems across {len(schemas)} schemas and {rows} rows.")
        return 1
    print(f"OK    {len(schemas)} schemas valid; {rows} rows across {files} NDJSON files validated.")
    if rows == 0:
        print("      The register is empty by design at this build.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
