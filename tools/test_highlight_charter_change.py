"""The gate for the meta-invariant, measured. INVARIANTS.md §17.

§17 is the rule that holds every other rule, and until now it was the only invariant whose gate did
not exist: the file said *(planned)* and nothing checked it. A gate that protects the antidrift core
and can itself be fooled protects nothing, so each test below is one way a change to the core could
have reached `main` looking ordinary.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load():
    spec = importlib.util.spec_from_file_location(
        "highlight_charter_change", ROOT / "tools/highlight-charter-change.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gate = load()

CORE_TEXT = {
    "CHARTER.md": "# Charter\n\n## Vow I. We describe.\n\nWe do not condemn.\n",
    "RUBRIC.md": "# Rubric\n\n## Gate 1. It regenerates.\n\nFrom the rows.\n",
    "INVARIANTS.md": "# Invariants\n\n## §1. No verdict language.\n\nA list, and its gate.\n",
    "BYLAWS.md": "# Bylaws\n\n## 1. Who decides.\n\nThe maintainer.\n",
    "COUNCIL.md": "# Council\n\n## 3. The seats\n\n### Seat A. The Reader Who Wants to Be Fair\n",
}
PROMPT_TEXT = (
    "# The Council prompt\n\n"
    "**Seat A. The Reader Who Wants to Be Fair.** Watch for verdicts.\n"
    "**Seat B. The Subject in a Room.** Read it back as the officeholder.\n"
    "**Seat C. The Reviewer's Reviewer.** Watch for what the definition does not disclose.\n"
)
ROW = {
    "file": "COUNCIL.md",
    "sections": ["3"],
    "direction": "adds",
    "because": (
        "Seven seats have read every pass since the fourth reading and only three are written "
        "down, so four of the seven readings cannot be reproduced by a later reader holding the "
        "prompt's blob SHA, which COUNCIL section 8 makes the reproducibility guarantee."
    ),
    "council": {
        "prompt_sha": "0" * 40,
        "read_at": "2026-09-27T05:00:00Z",
        "seats": ["A", "B", "C"],
        "findings": "docs/design/pages-a-reader-can-use.md section 9",
    },
    "approved_by": "the maintainer",
    "decided_at": "2026-09-27T05:30:00Z",
}


def git(root: Path, *args: str) -> None:
    done = subprocess.run(
        ["git", "-C", str(root), *args], capture_output=True, text=True, encoding="utf-8"
    )
    assert done.returncode == 0, done.stderr


def repo(tmp_path: Path) -> Path:
    """A repository whose `origin/main` holds the core as published."""
    root = tmp_path / "repo"
    root.mkdir()
    git(root, "init", "--quiet", "--initial-branch=main")
    git(root, "config", "user.email", "operator@veraproject.xyz")
    git(root, "config", "user.name", "jeb2-spec")
    for name, text in CORE_TEXT.items():
        (root / name).write_text(text, encoding="utf-8")
    prompt = root / gate.PROMPT
    prompt.parent.mkdir(parents=True, exist_ok=True)
    prompt.write_text(PROMPT_TEXT, encoding="utf-8")
    (root / "data").mkdir()
    git(root, "add", ".")
    git(root, "commit", "--quiet", "-m", "the core as published")
    # The gate reads origin/main, so give the clone one that points at this commit.
    git(root, "update-ref", "refs/remotes/origin/main", "HEAD")
    return root


def prompt_sha(root: Path) -> str:
    """The blob SHA of the fixture's prompt, the way COUNCIL §8 asks a reading to record it."""
    done = subprocess.run(
        ["git", "-C", str(root), "hash-object", gate.PROMPT],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert done.returncode == 0, done.stderr
    return done.stdout.strip()


def row(root: Path, **over) -> dict:
    """A whole justification row against the fixture's own prompt."""
    made = dict(ROW, council=dict(ROW["council"], prompt_sha=prompt_sha(root)))
    council = over.pop("council", None)
    if council is not None:
        made["council"] = council
    made.update(over)
    return made


def ledger(root: Path, *rows: dict) -> None:
    (root / "data").mkdir(exist_ok=True)
    (root / gate.LEDGER).write_text(
        "".join(json.dumps(r, sort_keys=True) + "\n" for r in rows), encoding="utf-8"
    )


def test_an_unchanged_core_passes_and_says_so_rather_than_saying_nothing(tmp_path, capsys):
    """Silence reads the same whether a gate checked or crashed, so the passing run prints each
    file's digest and its section count: a reader sees the claim, not the absence of an alarm."""
    root = repo(tmp_path)
    assert gate.check(root, "origin/main") == 0
    said = capsys.readouterr().out
    assert "the antidrift core is unchanged" in said
    for name in gate.CORE:
        assert name in said, name
        assert gate.digest(CORE_TEXT[name])[:16] in said


def test_a_changed_core_file_with_no_justification_fails(tmp_path, capsys):
    """The whole point. A softening that reaches main inside an ordinary pull request is the
    failure §17 exists to prevent."""
    root = repo(tmp_path)
    (root / "INVARIANTS.md").write_text(
        "# Invariants\n\n## §1. No verdict language, mostly.\n\nA shorter list.\n", encoding="utf-8"
    )
    assert gate.check(root, "origin/main") == 1
    said = capsys.readouterr().out
    assert "The antidrift core changed" in said
    assert "INVARIANTS.md" in said and gate.LEDGER in said
    assert "-## §1. No verdict language." in said, "the diff is printed, not just named"
    assert "+## §1. No verdict language, mostly." in said


def test_a_section_removed_from_the_core_is_called_out_by_name(tmp_path, capsys):
    """A gate that prints a diff and nothing else makes a reviewer find the deletion. §17's own
    subject is removal, so the removal is named."""
    root = repo(tmp_path)
    (root / "INVARIANTS.md").write_text("# Invariants\n\nNothing here now.\n", encoding="utf-8")
    assert gate.check(root, "origin/main") == 1
    assert "sections gone: §1" in capsys.readouterr().out


def test_a_change_with_a_whole_justification_passes_and_prints_who_weighed_it(tmp_path, capsys):
    """Loud softening is allowed. The gate's job is that it cannot be quiet."""
    root = repo(tmp_path)
    (root / "COUNCIL.md").write_text(
        CORE_TEXT["COUNCIL.md"] + "\n### Seat D. The Reader Who Sees One Piece\n", encoding="utf-8"
    )
    ledger(root, row(root))
    assert gate.check(root, "origin/main") == 0
    said = capsys.readouterr().out
    assert "justified: adds 3" in said
    assert "read by seats A, B, C" in said and "approved by the maintainer" in said
    assert "The antidrift core changed" in said, "it passes loudly, never quietly"


def test_a_widening_says_that_it_softens_the_core(tmp_path, capsys):
    """§17's subject is removal, softening and weakening. A row that admits it is printed as such,
    so a reviewer skimming the log sees the word."""
    root = repo(tmp_path)
    (root / "COUNCIL.md").write_text(CORE_TEXT["COUNCIL.md"] + "\nMore.\n", encoding="utf-8")
    ledger(root, row(root, direction="widens"))
    assert gate.check(root, "origin/main") == 0
    assert "this SOFTENS the core" in capsys.readouterr().out


def test_a_justification_missing_any_part_fails_and_names_the_part(tmp_path, capsys):
    """A row that names the file and nothing else reads, to a later reader, as an amendment that
    was weighed. Each field is one thing the diff cannot supply."""
    root = repo(tmp_path)
    (root / "COUNCIL.md").write_text(CORE_TEXT["COUNCIL.md"] + "\nMore.\n", encoding="utf-8")
    for field in gate.REQUIRED:
        ledger(root, {k: v for k, v in ROW.items() if k != field})
        assert gate.check(root, "origin/main") == 1, field
        assert field in capsys.readouterr().out, field
    # And the Council reading's own parts, because COUNCIL §8 makes the prompt SHA the guarantee.
    for field in ("prompt_sha", "read_at", "seats"):
        ledger(root, dict(ROW, council={k: v for k, v in ROW["council"].items() if k != field}))
        assert gate.check(root, "origin/main") == 1, field
        assert f"council.{field}" in capsys.readouterr().out, field


def test_a_reason_that_is_a_label_rather_than_a_reason_fails(tmp_path, capsys):
    """§17 asks the reason to say what problem the current text causes and what the change is
    expected to fix. "Cleanup" is not that, and a gate that accepts it accepts anything."""
    root = repo(tmp_path)
    (root / "BYLAWS.md").write_text(CORE_TEXT["BYLAWS.md"] + "\nMore.\n", encoding="utf-8")
    ledger(root, dict(ROW, file="BYLAWS.md", because="Cleanup."))
    assert gate.check(root, "origin/main") == 1
    assert "a reason, not a label" in capsys.readouterr().out


def test_a_direction_the_ledger_does_not_define_fails(tmp_path, capsys):
    root = repo(tmp_path)
    (root / "BYLAWS.md").write_text(CORE_TEXT["BYLAWS.md"] + "\nMore.\n", encoding="utf-8")
    ledger(root, dict(ROW, file="BYLAWS.md", direction="tidies"))
    assert gate.check(root, "origin/main") == 1
    assert "direction (one of" in capsys.readouterr().out


def test_a_justification_for_a_change_nobody_made_fails(tmp_path, capsys):
    """The rot this project has now found four times. A row standing in the record claiming a
    decision was weighed, with nothing behind it, is believed by the next reader."""
    root = repo(tmp_path)
    ledger(root, ROW)
    assert gate.check(root, "origin/main") == 1
    said = capsys.readouterr().out
    assert "is unchanged from origin/main" in said
    assert "a justification for a change nobody made" in said
    # And the same row alongside a real change to a different file still fails for its own file.
    (root / "BYLAWS.md").write_text(CORE_TEXT["BYLAWS.md"] + "\nMore.\n", encoding="utf-8")
    ledger(root, ROW, dict(ROW, file="BYLAWS.md"))
    assert gate.check(root, "origin/main") == 1
    assert "COUNCIL.md is unchanged" in capsys.readouterr().out


def test_a_core_file_that_is_gone_fails(tmp_path, capsys):
    """Deleting the file is the loudest softening of all, and the cheapest to miss."""
    root = repo(tmp_path)
    (root / "CHARTER.md").unlink()
    assert gate.check(root, "origin/main") == 1
    assert "CHARTER.md is part of the antidrift core and is missing" in capsys.readouterr().out


def test_a_gate_that_cannot_read_the_published_core_fails_rather_than_passes(
    tmp_path, capsys, monkeypatch
):
    """Every comparing gate here holds this rule: a gate that cannot read the record fails. A pass
    on an unreadable ref is a green tick that measured nothing.

    `main` takes the ref from the environment, so both halves of this test say which ref they mean.
    The half below sets an unreadable one. The line above it used to take whatever the machine
    held, and on a push to main that is CI's own `OATH_PUBLISHED_REF`, a commit this temporary
    repository has never heard of: the gate refused it, correctly, and the assertion that a
    well-formed tree passes failed on main and nowhere else. `conftest.py` clears it now."""
    root = repo(tmp_path)
    assert gate.main([str(root)]) == 0
    assert gate.readable(root, "refs/remotes/origin/nothing-here") is False
    monkeypatch.setenv("OATH_PUBLISHED_REF", "refs/remotes/origin/nothing-here")
    assert gate.main([str(root)]) == 1
    assert "Nothing was checked" in capsys.readouterr().out


def test_a_ledger_line_that_does_not_parse_fails_loudly(tmp_path):
    import pytest

    root = repo(tmp_path)
    (root / gate.LEDGER).write_text("{not json}\n", encoding="utf-8")
    with pytest.raises(SystemExit) as refused:
        gate.rows(root)
    assert gate.LEDGER in str(refused.value) and ":1" in str(refused.value)


def test_the_notice_is_the_runners_own_highlight_when_there_is_a_runner(monkeypatch):
    """§17 asks for a highlighted notice. Highlighted means the runner highlights it, not that the
    text is in capitals."""
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    assert gate.notice("error", "a\nb") == "a\nb"
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    assert gate.notice("error", "a\nb") == "::error::a%0Ab"


def test_this_repositorys_own_core_is_unchanged_and_the_gate_reads_it():
    """The gate against the real files, so a rename or a new core file is caught here rather than
    in CI. It does not assert the core is unchanged: a branch amending it should still pass its
    own tests, and the amendment's own justification is what the gate then requires."""
    for name in gate.CORE:
        assert (ROOT / name).is_file(), name
        assert gate.sections((ROOT / name).read_text("utf-8")), f"{name} holds no section"
    assert gate.sections((ROOT / "INVARIANTS.md").read_text("utf-8")).count("§17") == 1
    assert "§17" in gate.sections((ROOT / "INVARIANTS.md").read_text("utf-8"))


def test_a_reading_that_names_a_seat_the_prompt_does_not_define_fails(tmp_path, capsys):
    """COUNCIL §8 makes the prompt's blob SHA the reproducibility guarantee, and a guarantee is only
    worth the thing it points at. Seven seats have read every pass since the fourth reading and the
    committed prompt defines three, so four of those readings cannot be reproduced by anyone,
    however carefully the SHA was recorded. That is the defect the amendment this gate protects
    exists to fix, so the gate holds the amendment itself to it.
    """
    root = repo(tmp_path)
    prompt = root / gate.PROMPT
    prompt.parent.mkdir(parents=True, exist_ok=True)
    prompt.write_text(
        "# The Council prompt\n\n**Seat A. The Reader Who Wants to Be Fair.** Watch for verdicts.\n"
        "**Seat B. The Subject in a Room.** Read it back as the officeholder.\n",
        encoding="utf-8",
    )
    git(root, "add", gate.PROMPT)
    sha = subprocess.run(
        ["git", "-C", str(root), "hash-object", gate.PROMPT],
        capture_output=True,
        text=True,
    ).stdout.strip()

    (root / "COUNCIL.md").write_text(CORE_TEXT["COUNCIL.md"] + "\nMore.\n", encoding="utf-8")
    # A reading by the seats the prompt defines passes.
    ledger(root, dict(ROW, council=dict(ROW["council"], prompt_sha=sha, seats=["A", "B"])))
    assert gate.check(root, "origin/main") == 0
    assert "read by seats A, B" in capsys.readouterr().out

    # A reading that names a seat the prompt does not define is refused, by name.
    ledger(root, dict(ROW, council=dict(ROW["council"], prompt_sha=sha, seats=["A", "B", "D"])))
    assert gate.check(root, "origin/main") == 1
    said = capsys.readouterr().out
    assert "Seat D is not defined in .claude/prompts/council.md at that SHA" in said
    assert "Seat A is not defined" not in said, "it names the seat that is missing, not all of them"

    # And a SHA this repository does not hold is the same failure, louder: the instrument is gone.
    ledger(root, dict(ROW, council=dict(ROW["council"], prompt_sha="0" * 40, seats=["A"])))
    assert gate.check(root, "origin/main") == 1
    assert "is not in this repository" in capsys.readouterr().out


def test_this_repositorys_own_prompt_defines_the_seats_it_names():
    """The gap, as it stands today, asserted here so it cannot be forgotten: the committed prompt
    defines A, B and C, and seven seats have read every pass. This test passes on the three and is
    the test that must be extended when the prompt gains D to G, in the same commit."""
    sha = subprocess.run(
        ["git", "-C", str(ROOT), "hash-object", gate.PROMPT], capture_output=True, text=True
    ).stdout.strip()
    assert len(sha) == 40, "the prompt is in the tree and hashable"
    defined = [s for s in "ABCDEFG" if not gate.undefined_seats(ROOT, sha, [s])]
    assert "A" in defined and "B" in defined and "C" in defined
    assert gate.undefined_seats(ROOT, sha, defined) == []
