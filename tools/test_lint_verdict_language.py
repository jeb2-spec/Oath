"""Tests for tools/lint-verdict-language.py.

A fixture repository is built in a temporary directory to exercise every rule red
first: a plain hit, an inflected hit, the frame sentence, an allowlisted hit, a
stale allowlist entry, a malformed allowlist line, the excluded directories, and a
data row. The repository itself must be green last.
"""

from __future__ import annotations

import importlib.util
import subprocess
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def load():
    spec = importlib.util.spec_from_file_location("lint_verdict", HERE / "lint-verdict-language.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


lint = load()


def write(root: Path, rel: str, text: str) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    write(
        tmp_path,
        "README.md",
        "# Fixture\n\nPresence in the register is not evidence of wrongdoing.\n",
    )
    return tmp_path


def test_clean_fixture_is_green(repo: Path):
    failures, scanned, allowed = lint.lint(repo)
    assert failures == [] and scanned == 1 and allowed == 0


def test_plain_and_inflected_hits_fail_with_line_and_word(repo: Path):
    write(
        repo,
        "docs/signals/late-ptr.md",
        "# Late PTR\n\nThe senator's late filing was dishonest.\n"
        "A corruption of the record.\nCriminally late.\n",
    )
    failures, _, _ = lint.lint(repo)
    assert failures == [
        'docs/signals/late-ptr.md:3: "dishonest" in: The senator\'s late filing was dishonest.',
        'docs/signals/late-ptr.md:4: "corruption" in: A corruption of the record.',
        'docs/signals/late-ptr.md:5: "Criminally" in: Criminally late.',
    ]


def test_frame_sentence_is_always_allowed_but_only_that_word(repo: Path):
    write(
        repo,
        "README.md",
        "Presence in the register is not evidence of wrongdoing, and the filer is not corrupt.\n",
    )
    failures, _, _ = lint.lint(repo)
    assert len(failures) == 1 and '"corrupt"' in failures[0]


def test_allowlist_allows_by_path_and_context(repo: Path):
    write(repo, "STANDARDS.md", "Willful failure to file may constitute a criminal violation.\n")
    write(
        repo,
        lint.ALLOWLIST,
        "STANDARDS.md | may constitute a criminal violation | the statute's own penalty category\n",
    )
    failures, _, allowed = lint.lint(repo)
    assert failures == [] and allowed == 1


def test_allowlist_entry_does_not_leak_to_other_files(repo: Path):
    write(repo, "STANDARDS.md", "may constitute a criminal violation\n")
    write(repo, "docs/x.md", "may constitute a criminal violation\n")
    write(repo, lint.ALLOWLIST, "STANDARDS.md | may constitute a criminal violation | reason\n")
    failures, _, _ = lint.lint(repo)
    assert len(failures) == 1 and failures[0].startswith("docs/x.md:1:")


def test_stale_allowlist_entry_fails(repo: Path):
    write(repo, lint.ALLOWLIST, "README.md | no such context | reason\n")
    failures, _, _ = lint.lint(repo)
    assert failures == [
        "verdict-lint.allowlist:1: stale entry, no line in README.md contains 'no such context'"
    ]


def test_malformed_allowlist_line_is_an_error(repo: Path):
    write(repo, lint.ALLOWLIST, "README.md | missing reason\n")
    assert lint.main([str(repo)]) == 1


def test_excluded_directories_are_not_scanned(repo: Path):
    write(repo, ".claude/memory/x.md", "guilty guilty guilty\n")
    write(repo, "docs/related-work/x.md", "a neighbour says misconduct\n")
    write(repo, "node_modules/x.md", "crook\n")
    failures, scanned, _ = lint.lint(repo)
    assert failures == [] and scanned == 1


def test_data_rows_and_source_are_scanned(repo: Path):
    write(repo, "data/findings.ndjson", '{"description":"The member is a crook."}\n')
    write(repo, "src/signals/x.ts", 'const text = "this is shameful";\n')
    failures, scanned, _ = lint.lint(repo)
    assert scanned == 3
    assert any(f.startswith('data/findings.ndjson:1: "crook"') for f in failures)
    assert any(f.startswith('src/signals/x.ts:1: "shameful"') for f in failures)


def test_the_repository_is_green(capsys):
    assert lint.main([str(ROOT)]) == 0
    out = capsys.readouterr().out
    assert out.startswith("OK") and "no verdict language" in out


def test_rendered_pages_are_read_though_git_ignores_them(repo: Path):
    """The pages a reader is shown are build output, untracked; the gate reads them anyway."""
    write(repo, ".gitignore", "build/\n")
    write(repo, "docs/build/officeholders/x.html", "<p>The report shows the member is dirty.</p>\n")
    git = ["git", "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@example.invalid"]
    subprocess.run([*git, "init", "-q"], check=True)
    subprocess.run([*git, "add", "README.md", ".gitignore"], check=True)
    tracked = subprocess.run([*git, "ls-files"], capture_output=True, text=True, check=True)
    assert "docs/build" not in tracked.stdout
    failures, scanned, _ = lint.lint(repo)
    assert scanned == 2
    assert failures == [
        'docs/build/officeholders/x.html:1: "dirty" in: '
        "<p>The report shows the member is dirty.</p>"
    ]


def test_a_rendered_page_is_read_once_without_git(repo: Path):
    write(
        repo,
        "docs/build/index.html",
        "<p>Presence in the register is not evidence of wrongdoing.</p>\n",
    )
    failures, scanned, _ = lint.lint(repo)
    assert failures == [] and scanned == 2


def test_the_frame_allows_only_itself(repo: Path):
    """Seat C's case: one NDJSON row is one line, and it may carry the frame and a verdict."""
    write(
        repo,
        "data/findings.ndjson",
        '{"notes":"Presence in the register is not evidence of wrongdoing, but this report '
        'shows wrongdoing."}\n',
    )
    failures, _, _ = lint.lint(repo)
    assert len(failures) == 1 and '"wrongdoing"' in failures[0]
    assert lint.hits("Presence in the register is not evidence of wrongdoing.") == []
