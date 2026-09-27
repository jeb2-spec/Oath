"""Tests for scripts/oath-doctor.py.

The checks that read files are exercised on fixtures, red first; the whole doctor
is then run on the repository and must not be red.
"""

from __future__ import annotations

import importlib.util
import subprocess
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


PAGE_LINT = """import argparse, sys
from pathlib import Path
p = argparse.ArgumentParser()
p.add_argument("root")
p.add_argument("--site", default="docs/build")
a = p.parse_args()
site = Path(a.root) / a.site
print("OK read" if (site / "index.html").is_file() else "FAIL nothing to read")
sys.exit(0 if (site / "index.html").is_file() else 1)
"""


def test_the_page_gates_read_a_render_made_for_them(tmp_path: Path):
    """The site is never in git, so a fresh clone has none: the doctor renders the
    register into a temporary folder and points the page gates at it, as CI renders
    before it lints. Found when the page gates learnt to fail on nothing to read and
    the doctor, run before any render, went red."""
    write(
        tmp_path,
        "src/surfaces/render.py",
        "import sys\nfrom pathlib import Path\n"
        "out = Path(sys.argv[sys.argv.index('--out') + 1])\n"
        "out.mkdir(parents=True, exist_ok=True)\n(out / 'index.html').write_text('x')\n",
    )
    write(tmp_path, "tools/lint-frame-presence.py", PAGE_LINT)
    write(tmp_path, "tools/lint-no-ranking.py", PAGE_LINT)
    rep = doctor.Report()
    doctor.check_gates(tmp_path, rep)
    assert rep.red == 0, rep.lines
    assert not (tmp_path / "docs" / "build").exists(), "the render is not left in the tree"
    write(tmp_path, "src/surfaces/render.py", "import sys\nprint('broken')\nsys.exit(1)\n")
    rep = doctor.Report()
    doctor.check_gates(tmp_path, rep)
    assert any("does not render" in line for line in rep.lines)
    assert rep.red == 3, "a register that does not render is red, and so are its page gates"


SEATS = [
    (
        letter,
        f"The {name}",
        f"You read as the {name.lower()}. Watch for:\n\n- one thing;\n- another.",
    )
    for letter, name in zip(
        "ABCDEFG",
        ("Fair", "Subject", "Reviewer", "Partisans", "Constituent", "Neighbour", "Later"),
        strict=True,
    )
]


MODES = [
    f"**Mode {n}.** A failure every seat reads for, the [{n}th](METHODOLOGY.md)."
    for n in range(1, 11)
]


def listed(modes) -> str:
    return "".join(f"{n}. {mode}\n" for n, mode in enumerate(modes, start=1))


def council_md(seats, modes=MODES) -> str:
    body = "".join(f"### Seat {letter}. {title}\n\n{text}\n\n" for letter, title, text in seats)
    return (
        f"# The Council\n\n## 3. The seats\n\nThe seats are a floor.\n\n{body}## 4. Next\n\n"
        f"## 5. Findings a Council session must always try to catch\n\n{listed(modes)}\n"
        "The names of the first four are the errata precedent.\n\n## 6. Acting on findings\n"
    )


def prompt_md(seats, modes=MODES) -> str:
    body = "".join(f"**Seat {letter}. {title}.** {text}\n\n" for letter, title, text in seats)
    return (
        f"# The Council prompt\n\n## The seats\n\n{body}"
        f"## What every seat must try to catch\n\nCOUNCIL.md §5.\n\n{listed(modes)}\n"
        "## The finding\n"
    )


def council_report(root: Path, council, prompt, modes=MODES, carried=None):
    write(root, "COUNCIL.md", council_md(council, modes))
    write(root, doctor.PROMPT, prompt_md(prompt, modes if carried is None else carried))
    rep = doctor.Report()
    doctor.check_council(root, rep)
    return rep


def test_the_seats_read_back_when_the_prompt_sits_each_of_them(tmp_path: Path):
    rep = council_report(tmp_path, SEATS, SEATS)
    assert rep.red == 0, rep.lines
    assert sum(line.startswith("[ok]   Seat") for line in rep.lines) == 7
    assert any("sits COUNCIL.md's 7 seats" in line for line in rep.lines)


def test_a_seat_doctrine_names_and_the_prompt_does_not_sit_is_red(tmp_path: Path):
    """The one thing that actually breaks COUNCIL.md §8: a session records a seat as having read,
    and the prompt at that blob SHA has no such seat, so nobody can reproduce the read."""
    rep = council_report(tmp_path, SEATS, [s for s in SEATS if s[0] != "E"])
    assert rep.red == 1
    assert any("in COUNCIL.md §3, and not in the prompt" in line for line in rep.lines)


def test_the_prompt_may_word_a_seat_differently_from_doctrine(tmp_path: Path):
    """The check used to require the two to agree word for word, and that requirement is gone.
    COUNCIL.md describes a seat in the third person and a prompt addresses whoever sits it, so
    agreement was reachable only by rewriting sealed doctrine into the prompt's voice: an amendment
    row, a Council reading and a re-seal, for a guarantee §8 never asked for. §8 wants a reading to
    be reproducible, and the prompt's committed blob SHA gives that. What the letters still catch is
    the seat that cannot be reproduced at all."""
    third_person = [(s[0], s[1], f"Reads as the {s[1]}, watching for one thing.") for s in SEATS]
    rep = council_report(tmp_path, third_person, SEATS)
    assert rep.red == 0, rep.lines
    assert sum(line.startswith("[ok]   Seat") for line in rep.lines) == 7


def test_a_seat_renamed_is_red_and_a_seat_only_the_prompt_sits_is_not(tmp_path: Path):
    renamed = [(s[0], "The Reader", s[2]) if s[0] == "F" else s for s in SEATS]
    assert council_report(tmp_path, SEATS, renamed).red == 1, "a seat named two ways"

    # Changed deliberately: the prompt sitting a seat doctrine has not entrenched is the ordinary
    # case now, not an error. Writing a seat into COUNCIL.md costs an amendment and buys a reader
    # nothing; sitting it costs a paragraph in the prompt.
    extra = SEATS + [("H", "The Extra", "You read as an extra seat.")]
    practice = council_report(tmp_path, SEATS, extra)
    assert practice.red == 0, practice.lines
    assert any("sat in practice, not in COUNCIL.md §3" in line for line in practice.lines)

    out_of_order = [SEATS[1], SEATS[0], *SEATS[2:]]
    assert council_report(tmp_path, out_of_order, out_of_order).red == 1, "doctrine's own letters"


def test_the_prompt_carries_at_least_the_failure_modes_doctrine_names(tmp_path: Path):
    here = council_report(tmp_path, SEATS, SEATS)
    assert here.red == 0 and any("all 10 failure modes" in line for line in here.lines)

    dropped = council_report(tmp_path, SEATS, SEATS, carried=MODES[:9])
    assert dropped.red == 1 and any("carries 9 failure modes" in line for line in dropped.lines)

    # Changed with the seats, and for the same reason: the prompt may say a mode in its own words.
    reworded = [m.replace("A failure", "Something") for m in MODES]
    assert council_report(tmp_path, SEATS, SEATS, carried=reworded).red == 0

    added = [*MODES, "**Mode 11.** One more, sat in practice."]
    assert council_report(tmp_path, SEATS, SEATS, carried=added).red == 0, "a mode may be added"


def test_a_gate_that_announces_a_change_and_passes_is_read_back_and_not_red(
    tmp_path: Path, monkeypatch
):
    """A legitimate amendment of the antidrift core makes the §17 gate loud and passing at once:
    it prints the diff under a highlighted notice and exits zero because the row is there. The
    doctor follows the exit code, so a loud pass is read back and never counted red. An earlier
    version of this test also asserted that the doctor stripped GITHUB_EVENT_NAME and
    GITHUB_EVENT_PATH before running the gate, for a pull-request-reading workflow that was
    drafted and never landed; the gate reads neither variable, so that assertion measured a
    no-op and went with the code."""
    write(tmp_path, "tools/highlight-charter-change.py", "")

    def run(args, **kwargs):
        return subprocess.CompletedProcess(args, 0, "HIGHLIGHT  1 of the core changed\n", "")

    monkeypatch.setattr(doctor.subprocess, "run", run)
    rep = doctor.Report()
    doctor.run_gate(tmp_path, rep, "§17", "tools/highlight-charter-change.py", None)
    assert rep.red == 0 and "HIGHLIGHT" in rep.lines[-1]


def test_the_doctor_asks_what_a_reader_will_see_and_counts_it_as_neither(capsys):
    """The doctor answers what it can measure. This is the part it cannot, so printing it is the
    only way to make it unskippable, and it must not be a pass (which reads as done) or a problem
    (which reads as broken). 2026-09-27 is the day it exists for: a session spent on the register's
    own bookkeeping while believing it was building, when rendering the site would have said so."""
    rep = doctor.Report()
    before = (rep.red, rep.warn)
    rep.ask("Name the change a reader will see.")
    assert (rep.red, rep.warn) == before, "a question is neither a pass nor a problem"
    assert rep.lines[-1].startswith("[ask]  ")

    doctor.main([str(ROOT)])
    said = capsys.readouterr().out
    assert "Before you start" in said
    assert "Name the change a reader will see" in said
    assert "story-the-product-was-fine.md" in said
    assert "what-is-already-checked.md" in said
