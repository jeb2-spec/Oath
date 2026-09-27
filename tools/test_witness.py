"""Tests for tools/witness.py: an outside copy counts only when its bytes are the sealed ones."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import urllib.parse
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent


def _load():
    tool = HERE / "witness.py"
    spec = importlib.util.spec_from_file_location("witness", tool)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


witness = _load()

URL = "https://disclosures-clerk.house.gov/public_disc/ptr-pdfs/2025/20000001.pdf"
READ = b"%PDF-1.7 the bytes the register read"
OTHER = b"%PDF-1.7 other bytes at the same address"


def sha256(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()


def document(body: bytes = READ, url: str = URL) -> dict:
    return {"filing_id": "fl:us:house:2025:20000001", "url": url, "content_hash": sha256(body)}


class Archive:
    """A fake Internet Archive: an index of captures and the payload each one serves."""

    def __init__(self, held: dict[str, bytes], index_fails: bool = False):
        self.held = held
        self.index_fails = index_fails
        self.asked: list[str] = []

    def __call__(self, url: str) -> tuple[bytes, dict]:
        self.asked.append(url)
        if "/cdx/search/cdx?" in url:
            if self.index_fails:
                raise ConnectionError("the Archive reset the connection")
            query = urllib.parse.parse_qs(url.split("?", 1)[1])
            assert query["filter"] == ["statuscode:200"]
            rows = [["timestamp", "original", "statuscode", "digest"]]
            for timestamp, body in sorted(self.held.items()):
                rows.append([timestamp, query["url"][0], "200", witness.archive_digest(body)])
            return (json.dumps(rows).encode() if len(rows) > 1 else b""), {}
        timestamp = url.split("/web/", 1)[1].split("id_/", 1)[0]
        return self.held[timestamp], {}


def test_a_capture_counts_as_held_only_when_its_bytes_hash_to_the_sealed_hash():
    archive = Archive({"20250615060115": READ})
    row = witness.witness(document(), archive)
    assert row["outcome"] == "held"
    assert row["held_since"] == "2025-06-15T06:01:15Z"
    assert row["replay"] == f"https://web.archive.org/web/20250615060115/{URL}"
    assert row["read"][0]["archive_digest_agrees"] is True


def test_a_capture_of_other_bytes_is_never_a_witness():
    archive = Archive({"20260101000000": OTHER})
    row = witness.witness(document(), archive)
    assert row["outcome"] == "differs"
    assert "held_since" not in row and "replay" not in row
    assert row["read"][0]["sha256"] == sha256(OTHER)
    assert row["read"][0]["matches"] is False


def test_the_earliest_capture_of_the_bytes_read_is_the_one_named():
    archive = Archive({"20250101000000": OTHER, "20250301000000": READ, "20250901000000": READ})
    row = witness.witness(document(), archive)
    assert row["outcome"] == "held"
    assert row["held_since"] == "2025-03-01T00:00:00Z"
    assert row["captures"] == 3 and row["payloads"] == 2
    fetched = [url for url in archive.asked if "id_/" in url]
    assert len(fetched) == 2, "one capture per distinct payload, not one per capture"


def test_no_capture_listed_is_none_and_not_a_claim_about_the_document():
    row = witness.witness(document(), Archive({}))
    assert row["outcome"] == "none"
    assert row["captures"] == 0


def test_an_archive_that_cannot_be_asked_is_unchecked_never_none():
    row = witness.witness(document(), Archive({}, index_fails=True))
    assert row["outcome"] == "unchecked"
    assert "ConnectionError" in row["error"]


def test_it_asks_only_the_internet_archive():
    with pytest.raises(ValueError, match="only the Internet Archive"):
        witness.get(URL)


def test_the_run_fails_loudly_on_other_bytes_and_says_what_it_checked(tmp_path, capsys):
    data = tmp_path / "data"
    data.mkdir()
    (data / "meta.json").write_text(json.dumps({"build": "0005-house-2025", "digest": "ab" * 32}))
    rows = [
        {"id": "fl:us:house:2025:20000001", "source": {"url": URL, "content_hash": sha256(READ)}},
        {
            "id": "fl:us:house:2025:20000002",
            "source": {"url": URL[:-5] + "2.pdf", "content_hash": "0"},
        },
        {
            "id": "fl:us:house:2025:20000003",
            "source": {"url": URL[:-5] + "3.pdf", "content_hash": "0"},
        },
    ]
    (data / "filings.ndjson").write_text("".join(json.dumps(r) + "\n" for r in rows))
    findings = [
        {"producing_filings": ["fl:us:house:2025:20000001"]},
        {"producing_filings": ["fl:us:house:2025:20000001"]},
        {"producing_filings": ["fl:us:house:2025:20000002"]},
    ]
    (data / "findings.ndjson").write_text("".join(json.dumps(f) + "\n" for f in findings))

    class ByAddress(Archive):
        def __call__(self, url):
            self.asked.append(url)
            if "/cdx/search/cdx?" in url:
                address = urllib.parse.parse_qs(url.split("?", 1)[1])["url"][0]
                body = {URL: READ, URL[:-5] + "2.pdf": OTHER}[address]
                header = ["timestamp", "original", "statuscode", "digest"]
                entry = ["20250615060115", address, "200", witness.archive_digest(body)]
                return json.dumps([header, entry]).encode(), {}
            return (READ if url.endswith(URL) else OTHER), {}

    report = tmp_path / "report.json"
    summary = tmp_path / "summary.md"
    code = witness.main(
        ["--root", str(tmp_path), "--report", str(report), "--summary", str(summary)],
        fetch=ByAddress({}),
    )
    assert code == 1
    written = json.loads(report.read_text())
    assert written["totals"] == {"held": 1, "differs": 1, "none": 0, "unchecked": 0}
    assert [row["filing_id"] for row in written["documents"]] == [
        "fl:us:house:2025:20000001",
        "fl:us:house:2025:20000002",
    ], "each document a Finding rests on, once, and none that no Finding rests on"
    out = capsys.readouterr().out
    assert "FAIL" in out and "differs" in out
    assert "20000002.pdf" in summary.read_text()
