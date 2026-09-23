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
     filings, holdings, transactions, findings, signals) validates against its schema.
     An invalid row is reported with its file, line, field path, and the rule it broke,
     as METHODOLOGY.md §2.1 requires. Rows under data/rejected/ are not validated; they
     are the rejects.

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
    "minimum",
    "default",
    "examples",
}
TYPES = {"string", "integer", "number", "boolean", "null", "array", "object"}
FORMATS = {"date", "date-time", "uri"}
DRAFT = "https://json-schema.org/draft/2020-12/schema"
ID_RULE = re.compile(r"^https://oath\.jeb2-spec\.dev/schemas/([a-z]+)/v(\d+)\.json$")
CANONICAL = {
    "officeholders": "officeholder",
    "offices": "office",
    "filings": "filing",
    "holdings": "holding",
    "transactions": "transaction",
    "findings": "finding",
    "signals": "signal",
}


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
    is_number = isinstance(value, (int, float)) and not isinstance(value, bool)
    if is_number and "minimum" in schema and value < schema["minimum"]:
        errors.append(f"{path}: {value} is below the minimum {schema['minimum']}")
    if isinstance(value, list):
        if "minItems" in schema and len(value) < schema["minItems"]:
            errors.append(f"{path}: needs at least {schema['minItems']} items, has {len(value)}")
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
    return problems, rows, files


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
