"""Tests for tools/verify.py, tools/seal.py, and tools/tamper-test.py.

A fixture register is built in a temporary directory: eleven one-line doctrine
documents, two NDJSON files with three rows between them, and a meta.json with
disclosures. It is sealed, verified, altered, verified again, and recomputed with
the tamper-test's independent code. The repository itself is verified last.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def load(name: str):
    spec = importlib.util.spec_from_file_location(name.replace("-", "_"), HERE / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


verify = load("verify")
seal = load("seal")
tamper = load("tamper-test")


@pytest.fixture
def register(tmp_path: Path) -> Path:
    for name in verify.DOCTRINE:
        (tmp_path / name).write_text(f"# {name}\n\nfixture only\n", encoding="utf-8", newline="\n")
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "officeholders.ndjson").write_text(
        '{"id":"oh:fixture:1"}\n{"id":"oh:fixture:2"}\n', encoding="utf-8", newline="\n"
    )
    (tmp_path / "data" / "filings.ndjson").write_text(
        '{"id":"fl:fixture:1"}\n\n', encoding="utf-8", newline="\n"
    )
    meta = {
        "state": "A fixture register: 2 officeholders and 1 filing, sealed for the tests.",
        "register": "fixture",
        "disclosures": {"assistant": "disclosed", "non_public_data": "none"},
        "digest": "",
    }
    (tmp_path / "data" / "meta.json").write_text(
        json.dumps(meta, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    seal.seal(tmp_path, "fixture-0001", "2026-09-22T00:00:00Z")
    return tmp_path


def test_sealed_register_verifies_and_counts_rows(register: Path, capsys):
    assert verify.main([str(register)]) == 0
    out = capsys.readouterr().out
    assert (
        "OK" in out
        and "3 rows across 2 NDJSON files" in out
        and "Integrity is not accuracy." in out
    )
    meta = json.loads((register / "data" / "meta.json").read_text(encoding="utf-8"))
    assert meta["rows"] == {"data/filings.ndjson": 1, "data/officeholders.ndjson": 2}
    assert meta["build"] == "fixture-0001" and len(meta["digest"]) == 64


def test_sealing_twice_is_byte_identical(register: Path):
    first = (register / "data" / "meta.json").read_bytes()
    seal.seal(register, "fixture-0001", "2026-09-22T00:00:00Z")
    assert (register / "data" / "meta.json").read_bytes() == first


def test_changed_row_fails(register: Path, capsys):
    path = register / "data" / "officeholders.ndjson"
    path.write_bytes(path.read_bytes().replace(b"oh:fixture:2", b"oh:fixture:3"))
    assert verify.main([str(register)]) == 1
    assert "FAIL" in capsys.readouterr().out


def test_changed_disclosure_fails(register: Path, capsys):
    meta_path = register / "data" / "meta.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    meta["disclosures"]["assistant"] = "not disclosed"
    meta_path.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8", newline="\n")
    assert verify.main([str(register)]) == 1
    assert "FAIL" in capsys.readouterr().out


def test_changed_doctrine_fails(register: Path, capsys):
    (register / "CHARTER.md").write_text(
        "# CHARTER.md\n\nsoftened\n", encoding="utf-8", newline="\n"
    )
    assert verify.main([str(register)]) == 1
    assert "FAIL" in capsys.readouterr().out


def test_meta_formatting_does_not_change_the_seal(register: Path):
    """The seal covers meta's content, not its whitespace."""
    before = verify.compute_digest(register)
    meta_path = register / "data" / "meta.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    meta_path.write_text(
        json.dumps(meta, indent=4, sort_keys=False), encoding="utf-8", newline="\n"
    )
    assert verify.compute_digest(register) == before


def test_independent_recomputation_matches(register: Path):
    meta = json.loads((register / "data" / "meta.json").read_text(encoding="utf-8"))
    assert tamper.independent_digest(register) == meta["digest"] == verify.compute_digest(register)


def test_manifest_has_one_line_per_sealed_file(register: Path, capsys):
    assert verify.main([str(register), "--manifest"]) == 0
    lines = capsys.readouterr().out.splitlines()
    assert len(lines) == 2 + len(verify.DOCTRINE) + 1
    assert lines == sorted(lines)
    assert all(len(line.split("  ")[0]) == 64 for line in lines)


def test_missing_meta_fails_closed(register: Path, capsys):
    (register / "data" / "meta.json").unlink()
    assert verify.main([str(register)]) == 1
    assert "cannot verify" in capsys.readouterr().out


def test_tamper_test_passes_on_fixture(register: Path):
    proc = subprocess.run(
        [sys.executable, str(HERE / "tamper-test.py"), str(register)],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert proc.returncode == 0, proc.stdout
    assert proc.stdout.count("[pass]") == 3


def test_the_repository_verifies():
    proc = subprocess.run(
        [sys.executable, str(HERE / "verify.py"), str(ROOT)],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert proc.returncode == 0, proc.stdout
