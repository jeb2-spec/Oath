"""Tests for scripts/oath-doctor.py.

The checks that read files are exercised on fixtures, red first; the whole doctor
is then run on the repository and must not be red.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def load():
    spec = importlib.util.spec_from_file_location(
        "oath_doctor", ROOT / "scripts" / "oath-doctor.py"
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


doctor = load()


def write(root: Path, rel: str, text: str) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def memory_index(order: list[str]) -> str:
    return "# Index\n\n" + "\n".join(f"- [{n}]({n})" for n in order) + "\n"


def test_memory_chain_whole_and_in_order(tmp_path: Path):
    for name in doctor.ORDERED_MEMORY:
        write(tmp_path, f".claude/memory/{name}", "*Last updated: 2026-09-22*\n")
    write(tmp_path, ".claude/memory/MEMORY.md", memory_index(doctor.ORDERED_MEMORY))
    rep = doctor.Report()
    doctor.check_memory(tmp_path, rep)
    assert rep.red == 0
    assert any(
        "in the order CLAUDE.md gives" in line and line.startswith("[ok]") for line in rep.lines
    )


def test_memory_chain_missing_file_is_red(tmp_path: Path):
    write(tmp_path, ".claude/memory/MEMORY.md", memory_index(doctor.ORDERED_MEMORY))
    rep = doctor.Report()
    doctor.check_memory(tmp_path, rep)
    assert rep.red >= 3


def test_memory_chain_wrong_order_is_red(tmp_path: Path):
    for name in doctor.ORDERED_MEMORY:
        write(tmp_path, f".claude/memory/{name}", "x\n")
    write(tmp_path, ".claude/memory/MEMORY.md", memory_index(list(reversed(doctor.ORDERED_MEMORY))))
    rep = doctor.Report()
    doctor.check_memory(tmp_path, rep)
    assert any("not indexed in the order" in line for line in rep.lines) and rep.red == 1


def test_charter_read_back_needs_exactly_five_vows(tmp_path: Path):
    write(
        tmp_path,
        "CHARTER.md",
        "# Charter\n\n## I. One.\n\n## II. Two.\n\n## III. Three.\n\n## IV. Four.\n\n## V. Five.\n",
    )
    rep = doctor.Report()
    doctor.check_charter(tmp_path, rep)
    assert rep.red == 0 and sum(line.startswith("[ok]   Vow") for line in rep.lines) == 5
    write(tmp_path, "CHARTER.md", "# Charter\n\n## I. One.\n\n## II. Two.\n")
    rep = doctor.Report()
    doctor.check_charter(tmp_path, rep)
    assert rep.red == 1


def test_gates_list_planned_and_run_present(tmp_path: Path):
    write(tmp_path, "tools/verify.py", "import sys\nprint('OK fixture')\nsys.exit(0)\n")
    write(tmp_path, "tools/tamper-test.py", "import sys\nprint('FAIL fixture')\nsys.exit(1)\n")
    rep = doctor.Report()
    doctor.check_gates(tmp_path, rep)
    assert any("verify.py passes" in line for line in rep.lines)
    assert any("tamper-test.py FAILS" in line for line in rep.lines)
    assert sum("planned, not landed" in line for line in rep.lines) == len(doctor.GATES) - 2
    assert rep.red == 1


def test_the_repository_is_not_red(capsys):
    assert doctor.main([str(ROOT)]) == 0
    out = capsys.readouterr().out
    assert "GREEN" in out and "Vow V." in out
