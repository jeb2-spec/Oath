"""Tests for tools/anchor.py: every build anchored, and a ledger that cannot drift from its proofs.

The reader of a proof is pinned against a proof the OpenTimestamps library itself serialised,
so it runs without the library; where the library is installed, it is also checked against
the library on proofs made fresh. The stamping path runs against a stand-in `ots` that writes
the bytes a calendar would, because the calendars are a network the tests do not touch.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import shutil
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


anchor = _load(HERE / "anchor.py", "anchor")

# Made by opentimestamps 0.4.5 (DetachedTimestampFile over SHA-256 of b"a manifest\n"): two
# branches, one pending at a calendar, one naming Bitcoin block 915123 and pending at another.
LIBRARY_DIGEST = "62ee4f8aa61d15d01a79450143b68b20e67a57a45c627c6b4d8fd2a7bec33c1c"
LIBRARY_PROOF = bytes.fromhex(
    "004f70656e54696d657374616d7073000050726f6f6600bf89e2e884e89294010862ee4f8aa61d15d01a79"
    "450143b68b20e67a57a45c627c6b4d8fd2a7bec33c1cfff010000102030405060708090a0b0c0d0e0f0800"
    "83dfe30d2ef90c8e222168747470733a2f2f612e706f6f6c2e6f70656e74696d657374616d70732e6f7267"
    "f108070707070707070708ff000588960d73d7190103b3ed370083dfe30d2ef90c8e222168747470733a2f"
    "2f622e706f6f6c2e6f70656e74696d657374616d70732e6f7267"
)


def varuint(n: int) -> bytes:
    out = bytearray()
    while True:
        b = n & 0x7F
        n >>= 7
        out.append(b | (0x80 if n else 0))
        if not n:
            return bytes(out)


def proof(file_hash: str, height: int | None = None) -> bytes:
    """A detached proof: one pending attestation, and a Bitcoin one when a height is given."""
    uri = b"https://a.pool.opentimestamps.org"
    pending = b"\x00" + anchor.PENDING + varuint(len(uri) + 1) + varuint(len(uri)) + uri
    tree = pending
    if height is not None:
        payload = varuint(height)
        tree = b"\xff" + pending + b"\x00" + anchor.BITCOIN + varuint(len(payload)) + payload
    return anchor.MAGIC + b"\x01\x08" + bytes.fromhex(file_hash) + tree


def test_the_reader_agrees_with_the_library_on_the_librarys_own_bytes():
    read = anchor.read_proof(LIBRARY_PROOF)
    assert read["file_hash"] == LIBRARY_DIGEST == hashlib.sha256(b"a manifest\n").hexdigest()
    assert sorted(read["attestations"], key=str) == [
        ("bitcoin", 915123),
        ("pending", "https://a.pool.opentimestamps.org"),
        ("pending", "https://b.pool.opentimestamps.org"),
    ]
    assert anchor.state_of(read) == ("confirmed", 915123)


def test_the_reader_agrees_with_the_library_on_fresh_proofs():
    library = pytest.importorskip("opentimestamps.core.timestamp")
    from opentimestamps.core.notary import BitcoinBlockHeaderAttestation, PendingAttestation
    from opentimestamps.core.op import OpSHA256
    from opentimestamps.core.serialize import BytesDeserializationContext

    for height in (None, 1, 127, 128, 915123):
        data = proof(LIBRARY_DIGEST, height)
        parsed = library.DetachedTimestampFile.deserialize(BytesDeserializationContext(data))
        assert isinstance(parsed.file_hash_op, OpSHA256)
        assert parsed.file_digest.hex() == anchor.read_proof(data)["file_hash"]
        ours = anchor.read_proof(data)["attestations"]
        theirs = []
        for _msg, att in parsed.timestamp.all_attestations():
            if isinstance(att, BitcoinBlockHeaderAttestation):
                theirs.append(("bitcoin", att.height))
            elif isinstance(att, PendingAttestation):
                theirs.append(("pending", att.uri))
        assert sorted(ours, key=str) == sorted(theirs, key=str)


def test_what_is_not_a_proof_is_refused():
    for bad in (b"", b"not a proof", LIBRARY_PROOF[:-3], LIBRARY_PROOF + b"\x00"):
        with pytest.raises(ValueError):
            anchor.read_proof(bad)


def test_the_three_states():
    assert anchor.state_of(None) == ("owed", None)
    assert anchor.state_of(anchor.read_proof(proof(LIBRARY_DIGEST))) == ("pending", None)
    assert anchor.state_of(anchor.read_proof(proof(LIBRARY_DIGEST, 900001))) == (
        "confirmed",
        900001,
    )


# ---- a small register, sealed, to anchor --------------------------------------------------


@pytest.fixture
def register(tmp_path: Path) -> Path:
    verify = _load(HERE / "verify.py", "verify_for_anchor")
    (tmp_path / "tools").mkdir()
    shutil.copy(HERE / "verify.py", tmp_path / "tools" / "verify.py")
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "rows.ndjson").write_text('{"id":"x"}\n', encoding="utf-8")
    for name in verify.DOCTRINE:
        (tmp_path / name).write_text(f"# {name}\n", encoding="utf-8")
    meta = {"build": "0009-test", "built_at": "2026-01-02T03:04:05Z", "digest": ""}
    (tmp_path / "data" / "meta.json").write_text(json.dumps(meta), encoding="utf-8")
    meta["digest"] = verify.compute_digest(tmp_path)
    (tmp_path / "data" / "meta.json").write_text(json.dumps(meta), encoding="utf-8")
    (tmp_path / "ANCHORS.md").write_text(
        f"# Anchors\n\n{anchor.START}\n{anchor.END}\n\nAfter the table.\n", encoding="utf-8"
    )
    return tmp_path


def stand_in_ots(folder: Path, height: int | None) -> None:
    """An `ots` that does what a calendar would: stamp writes a pending proof of the file's
    hash; upgrade adds the Bitcoin block when one is given."""
    script = folder / "ots"
    script.write_text(
        f"""#!{sys.executable}
import hashlib, sys
sys.path.insert(0, {str(HERE)!r})
import importlib.util
spec = importlib.util.spec_from_file_location("t", {str(Path(__file__).resolve())!r})
t = importlib.util.module_from_spec(spec); spec.loader.exec_module(t)
command, path = sys.argv[1], sys.argv[2]
if command == "stamp":
    digest = hashlib.sha256(open(path, "rb").read()).hexdigest()
    open(path + ".ots", "wb").write(t.proof(digest))
elif command == "upgrade":
    read = t.anchor.read_proof(open(path, "rb").read())
    if {height!r} is None:
        sys.exit(1)
    open(path + ".bak", "wb").write(open(path, "rb").read())
    open(path, "wb").write(t.proof(read["file_hash"], {height!r}))
""",
        encoding="utf-8",
    )
    script.chmod(0o755)


def test_an_unreachable_calendar_leaves_the_stamp_owed_and_says_so(register, monkeypatch, capsys):
    monkeypatch.setenv("PATH", str(register / "no-ots-here"))
    assert anchor.main([str(register), "--stamp"]) == anchor.OWED
    manifest = (register / "data" / "anchors" / "0009-test.manifest").read_bytes()
    meta = json.loads((register / "data" / "meta.json").read_text("utf-8"))
    assert hashlib.sha256(manifest).hexdigest() == meta["digest"], "the manifest is the digest"
    ledger = (register / "ANCHORS.md").read_text("utf-8")
    assert "| `0009-test` |" in ledger and "| owed |" in ledger
    assert ledger.endswith("\n\nAfter the table.\n")
    assert "OWED" in capsys.readouterr().out
    assert anchor.main([str(register)]) == 0


def test_a_stamp_then_an_upgrade_carries_the_build_to_a_bitcoin_block(register, monkeypatch):
    bin_dir = register / "bin"
    bin_dir.mkdir()
    stand_in_ots(bin_dir, height=None)
    monkeypatch.setenv("PATH", f"{bin_dir}{os.pathsep}{os.environ['PATH']}")
    assert anchor.main([str(register), "--stamp"]) == 0
    assert "| pending |" in (register / "ANCHORS.md").read_text("utf-8")
    assert anchor.main([str(register), "--upgrade"]) == 0, "still waiting is not a failure"
    assert "| pending |" in (register / "ANCHORS.md").read_text("utf-8")
    stand_in_ots(bin_dir, height=915123)
    assert anchor.main([str(register), "--upgrade"]) == 0
    ledger = (register / "ANCHORS.md").read_text("utf-8")
    assert "| confirmed | 915123 |" in ledger
    assert not list((register / "data" / "anchors").glob("*.bak")), "the backup is not kept"
    assert anchor.main([str(register)]) == 0


def test_a_tree_that_does_not_verify_is_not_stamped(register):
    (register / "data" / "rows.ndjson").write_text('{"id":"y"}\n', encoding="utf-8")
    assert anchor.main([str(register), "--stamp"]) == 1
    assert not (register / "data" / "anchors").exists()


def test_the_check_sees_a_proof_of_something_else_and_a_hand_edited_table(register, monkeypatch):
    monkeypatch.setenv("PATH", str(register / "no-ots-here"))
    anchor.main([str(register), "--stamp"])
    ledger = register / "ANCHORS.md"
    ledger.write_text(ledger.read_text("utf-8").replace("| owed |", "| confirmed |"), "utf-8")
    assert anchor.main([str(register)]) == 1
    anchor.main([str(register), "--ledger"])
    assert anchor.main([str(register)]) == 0
    other = hashlib.sha256(b"another file").hexdigest()
    (register / "data" / "anchors" / "0009-test.manifest.ots").write_bytes(proof(other))
    anchor.main([str(register), "--ledger"])
    assert anchor.main([str(register)]) == 1


def test_a_builds_manifest_is_never_rewritten(register, monkeypatch):
    monkeypatch.setenv("PATH", str(register / "no-ots-here"))
    anchor.main([str(register), "--stamp"])
    path = register / "data" / "anchors" / "0009-test.manifest"
    path.write_bytes(path.read_bytes() + b"x")
    assert anchor.main([str(register), "--stamp"]) == 1


def test_the_repository_ledger_says_what_its_proofs_say():
    assert anchor.main([str(ROOT)]) == 0


def test_a_stamp_owed_by_an_earlier_build_is_retried_with_the_next(register, monkeypatch):
    """ANCHORS.md promises every owed stamp is retried. A build sealed while the calendars
    were unreachable stays owed until a stamp succeeds, whatever build has come since."""
    monkeypatch.setenv("PATH", str(register / "no-ots-here"))
    assert anchor.main([str(register), "--stamp"]) == anchor.OWED
    verify = _load(HERE / "verify.py", "verify_for_the_next_build")
    (register / "data" / "rows.ndjson").write_text('{"id":"x"}\n{"id":"y"}\n', "utf-8")
    meta = {"build": "0010-test", "built_at": "2026-01-09T03:04:05Z", "digest": ""}
    (register / "data" / "meta.json").write_text(json.dumps(meta), encoding="utf-8")
    meta["digest"] = verify.compute_digest(register)
    (register / "data" / "meta.json").write_text(json.dumps(meta), encoding="utf-8")
    bin_dir = register / "bin"
    bin_dir.mkdir()
    stand_in_ots(bin_dir, height=None)
    monkeypatch.setenv("PATH", f"{bin_dir}{os.pathsep}{os.environ['PATH']}")
    assert anchor.main([str(register), "--stamp"]) == 0
    states = {b["build"]: b["state"] for b in anchor.builds(register)}
    assert states == {"0009-test": "pending", "0010-test": "pending"}
    assert anchor.main([str(register), "--stamp"]) == 0, "nothing owed, nothing to do"
    assert anchor.main([str(register)]) == 0
