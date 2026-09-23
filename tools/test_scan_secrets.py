"""The secrets gate finds the shapes it names, honours the baseline, and passes this repository.

The fake secrets here are assembled at run time from pieces, so that this test file is
itself clean under the scanner it tests.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def load():
    spec = importlib.util.spec_from_file_location("scan_secrets", HERE / "scan-secrets.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_the_named_shapes_are_found_and_the_match_is_cut_short():
    scan = load()
    text = "\n".join(
        [
            "-----BEGIN " + "RSA PRIVATE KEY-----",
            "aws = " + "AKIA" + "ABCDEFGHIJKLMNOP",
            "gh = " + "ghp_" + "a" * 40,
            "api_key = " + "Z" * 24,
            "path = C:" + "\\Users\\somebody\\Apps",
            "path2 = /" + "Users/somebody/Documents/",
            "mail = somebody" + "@gmail.com",
        ]
    )
    hits = scan.scan_text("fixture.txt", text, set())
    kinds = [h.split(": ")[1] for h in hits]
    assert kinds == [
        "private key",
        "AWS access key",
        "GitHub token",
        "credential assignment",
        "personal path",
        "personal path",
        "e-mail address",
    ], hits
    assert "…" in hits[1] and "ABCDEFGHIJKLMNOP" not in hits[1], "the match is not repeated in full"


def test_the_operators_address_and_an_organisations_contact_pass():
    scan = load()
    text = "\n".join(
        [
            "Oath operator <operator@veraproject.xyz>",
            "Co-Authored-By: Claude <noreply@anthropic.com>",
            "someone@example.com in a schema example",
            "the regulator's API desk, APIinfo@fec.gov, a citation not a person",
            "C:\\Users\\<you>\\Apps\\Oath in a README",
            "https://efdsearch.senate.gov/search/home/ is a door, not a home directory",
        ]
    )
    assert scan.scan_text("docs.md", text, set()) == []


def test_the_baseline_allows_exactly_one_text_in_one_file():
    scan = load()
    line = "contact = someone" + "@hotmail.com"
    assert scan.scan_text("a.md", line, set()) != []
    allowed = {("a.md", "someone" + "@hotmail.com")}
    assert scan.scan_text("a.md", line, allowed) == []
    assert scan.scan_text("b.md", line, allowed) != [], "a baseline entry is per file"


def test_this_repository_is_clean(tmp_path):
    scan = load()
    problems, scanned = scan.scan(ROOT)
    assert scanned > 50
    assert problems == [], problems
    baseline = ROOT / ".secrets.baseline"
    if baseline.is_file():
        entries = json.loads(baseline.read_text(encoding="utf-8"))
        assert all({"path", "match", "reason"} <= set(e) for e in entries)
