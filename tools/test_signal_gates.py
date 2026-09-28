"""The gates that keep Findings and Signal definitions honest, each proven red before green.

INVARIANTS.md §5 (check-aggregator-sole), §11 (check-signal-versions), §12
(check-supersessions), and RUBRIC.md gate 4 (rebuild). Each test makes the change a gate
exists to refuse and requires the refusal; the published side is a real git ref in a
throwaway repository, because that is what the gates read in CI.
"""

from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def load(name: str):
    path = ROOT / "tools" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name.replace("-", "_"), path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


supersessions = load("check-supersessions")
versions = load("check-signal-versions")
aggregator = load("check-aggregator-sole")
rebuild = load("rebuild")


def row(fid: str, **extra) -> dict:
    base = {"id": fid, "signal_id": "sg:x:v1", "description": "d", "superseded_by": None}
    base.update(extra)
    return base


# ---- §12 ------------------------------------------------------------------------------


def test_a_published_finding_that_disappears_is_refused():
    assert supersessions.problems([], [row("fn:1")])


def test_a_published_finding_changed_in_place_is_refused():
    found = supersessions.problems([row("fn:1", description="edited")], [row("fn:1")])
    assert found and "changed in place" in found[0]


def test_a_supersession_to_a_correction_of_the_same_report_passes():
    tree = [row("fn:1", superseded_by="fn:1:c1"), row("fn:1:c1")]
    assert supersessions.problems(tree, [row("fn:1")]) == []


def test_a_supersession_to_a_missing_or_foreign_row_is_refused():
    assert supersessions.problems([row("fn:1", superseded_by="fn:1:c1")], [])
    assert supersessions.problems([row("fn:1", superseded_by="fn:2"), row("fn:2")], [])


def test_a_chain_with_two_current_rows_or_a_loop_is_refused():
    assert supersessions.problems([row("fn:1"), row("fn:1:c1")], [])
    loop = [row("fn:1", superseded_by="fn:1:c1"), row("fn:1:c1", superseded_by="fn:1")]
    assert supersessions.problems(loop, [])


def repo_with(tmp_path: Path, files: dict[str, str]) -> Path:
    """A throwaway repository whose branch `published` holds `files`."""
    for rel, text in files.items():
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / rel).write_text(text, encoding="utf-8")
    for args in (
        ["init", "-q", "-b", "published"],
        ["add", "-A"],
        ["-c", "user.email=t@example.com", "-c", "user.name=t", "commit", "-q", "-m", "p"],
    ):
        subprocess.run(["git", "-C", str(tmp_path), *args], check=True, capture_output=True)
    return tmp_path


def test_the_gate_reads_the_published_ref_and_refuses_an_edit(tmp_path, monkeypatch):
    line = json.dumps(row("fn:1"), sort_keys=True) + "\n"
    repo = repo_with(tmp_path, {"data/findings.ndjson": line})
    monkeypatch.setenv("OATH_PUBLISHED_REF", "published")
    assert supersessions.main([str(repo)]) == 0
    edited = json.dumps(row("fn:1", description="edited"), sort_keys=True) + "\n"
    (repo / "data/findings.ndjson").write_text(edited, encoding="utf-8")
    assert supersessions.main([str(repo)]) == 1


def test_a_gate_that_cannot_read_the_published_ref_fails(tmp_path, monkeypatch):
    repo = repo_with(tmp_path, {"data/findings.ndjson": ""})
    monkeypatch.setenv("OATH_PUBLISHED_REF", "no-such-ref")
    assert supersessions.main([str(repo)]) == 1
    assert versions.main([str(repo)]) == 1


# ---- §11 ------------------------------------------------------------------------------


def signal(version: int, **extra) -> dict:
    base = {"id": f"sg:x:v{version}", "slug": "x", "version": version, "supersedes": None}
    base.update(extra)
    return base


def definitions(tmp_path: Path, *names_and_versions: tuple[str, int]) -> Path:
    for name, version in names_and_versions:
        (tmp_path / "docs/signals").mkdir(parents=True, exist_ok=True)
        (tmp_path / "docs/signals" / name).write_text(f"---\nversion: {version}\n---\n", "utf-8")
    return tmp_path


def test_a_published_signal_redefined_in_place_is_refused(tmp_path):
    root = definitions(tmp_path, ("x.md", 1))
    found = versions.problems(root, [signal(1, name="new words")], [signal(1, name="old words")])
    assert found and "redefined in place" in found[0]


def test_a_new_version_must_name_the_one_it_supersedes(tmp_path):
    root = definitions(tmp_path, ("x.md", 2), ("x.v1.md", 1))
    assert versions.problems(root, [signal(1), signal(2)], [signal(1)])
    assert versions.problems(root, [signal(1), signal(2, supersedes="sg:x:v1")], [signal(1)]) == []


def test_a_superseded_definition_must_stay_readable(tmp_path):
    root = definitions(tmp_path, ("x.md", 2))
    found = versions.problems(root, [signal(1), signal(2, supersedes="sg:x:v1")], [signal(1)])
    assert found and "x.v1.md" in found[0]


# ---- §5 -------------------------------------------------------------------------------

SOURCES = (
    "# Sources\n## Federal. primary\n### F.1\n- <https://disclosures-clerk.house.gov/a>\n"
    "- <https://clerk.house.gov/xml>\n## Federal. corroborating (aggregators, cited never sole)\n"
    "- **OpenSecrets**. <https://www.opensecrets.org>\n"
)


def register(tmp_path: Path, filing_url: str) -> Path:
    (tmp_path / "data").mkdir()
    (tmp_path / "SOURCES.md").write_text(SOURCES, encoding="utf-8")
    holder = {"id": "oh:us:example:example", "source": {"url": "https://clerk.house.gov/xml"}}
    filing = {"id": "fl:example:P:1", "source": {"url": filing_url}}
    found = {"id": "fn:1", "officeholder_id": holder["id"], "producing_filings": [filing["id"]]}
    for name, obj in (("officeholders", holder), ("filings", filing), ("findings", found)):
        (tmp_path / "data" / f"{name}.ndjson").write_text(json.dumps(obj) + "\n", "utf-8")
    return tmp_path


def test_the_registry_is_read_from_sources_md():
    primary, aggregators = aggregator.registry(SOURCES)
    assert primary == {"disclosures-clerk.house.gov", "clerk.house.gov"}
    assert aggregators == {"www.opensecrets.org"}


def test_a_finding_on_a_primary_source_passes(tmp_path):
    root = register(tmp_path, "https://disclosures-clerk.house.gov/a.pdf")
    assert aggregator.main([str(root)]) == 0


def test_a_finding_resting_on_an_aggregator_alone_is_refused(tmp_path):
    assert aggregator.main([str(register(tmp_path, "https://www.opensecrets.org/x"))]) == 1


def test_a_finding_resting_on_an_unregistered_source_is_refused(tmp_path):
    assert aggregator.main([str(register(tmp_path, "https://example.com/x"))]) == 1


# ---- RUBRIC gate 4 ------------------------------------------------------------------------


def test_a_finding_regenerates_from_the_rows_it_names():
    first = json.loads((ROOT / "data" / "findings.ndjson").read_text("utf-8").splitlines()[0])
    assert rebuild.main([str(ROOT), first["id"]]) == 0


@pytest.mark.parametrize("signal", ["stock-act-ptr-after-deadline", "annual-report-after"])
def test_a_tampered_finding_does_not_regenerate(tmp_path, signal):
    for rel in ("data", "docs/signals", "src/signals", "fixtures"):
        shutil.copytree(ROOT / rel, tmp_path / rel)
    ledger = tmp_path / "data" / "findings.ndjson"
    lines = ledger.read_text("utf-8").splitlines()
    at = next(n for n, line in enumerate(lines) if signal in json.loads(line)["signal_id"])
    first = json.loads(lines[at])
    if "rows" in first["evidence"]:
        first["evidence"]["rows"][0]["days_after"] += 1
    else:
        first["evidence"]["days_after_latest"] += 1
    lines[at] = json.dumps(first, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    ledger.write_text("\n".join(lines) + "\n", encoding="utf-8")
    assert rebuild.main([str(tmp_path), first["id"]]) == 1
    assert rebuild.main([str(tmp_path)]) == 1
