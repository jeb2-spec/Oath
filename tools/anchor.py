#!/usr/bin/env python3
"""Anchor each sealed build with OpenTimestamps, and keep ANCHORS.md saying what the proofs say.

The seal's digest is the SHA-256 of the build's manifest (`tools/verify.py --manifest`): one
line per sealed file, its hash and its path. So the file this tool stamps is that manifest,
written to `data/anchors/<build>.manifest`, and the proof beside it, `<build>.manifest.ots`,
commits to the build's digest itself: `ots info` prints the digest as the file's hash, and
`sha256sum` of the manifest prints it too. Because every proof sits beside the exact file it
proves, `ots verify` works on any build's proof for as long as the repository exists.

Nothing under `data/anchors/` is sealed (the seal covers the NDJSON rows, the doctrine and
`data/meta.json`), so a proof can be added and later completed without moving the digest it
is over. For the same reason the anchor's state is never written into the sealed meta.json:
it lives in the proofs, and ANCHORS.md is regenerated from them (NEXT.md S.4).

    python tools/anchor.py            # the gate: the table says what the proofs say, every
                                      # proof commits to its manifest, and every manifest
                                      # to its build's digest
    python tools/anchor.py --stamp    # write this build's manifest, and stamp it and every
                                      # earlier build whose stamp is still owed
    python tools/anchor.py --upgrade  # complete pending proofs once Bitcoin holds them
    python tools/anchor.py --ledger   # rewrite the ANCHORS.md table from the proofs
    python tools/anchor.py --status   # each build, its digest, and its state

Stamping and upgrading call the `ots` command (`pip install opentimestamps-client`) and need
the calendar servers. Everything else, the reading of a proof included, is standard library.
A stamp that cannot reach the calendars is owed: the manifest is written, the table says
owed, and the tool exits 3 so a scheduled job fails loudly and tries again. It never writes a
proof of anything but the manifest whose hash is the digest.

Example of a failing input for --check: a proof whose file hash is not the SHA-256 of the
manifest beside it, or a table row that says confirmed for a proof that names no block.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path

ANCHORS = "data/anchors"
LEDGER = "ANCHORS.md"
START = "<!-- anchors:table:start (written by tools/anchor.py --ledger; do not edit by hand) -->"
END = "<!-- anchors:table:end -->"
OWED = 3

MAGIC = b"\x00OpenTimestamps\x00\x00Proof\x00\xbf\x89\xe2\xe8\x84\xe8\x92\x94"
BITCOIN = bytes.fromhex("0588960d73d71901")
PENDING = bytes.fromhex("83dfe30d2ef90c8e")
UNARY = {0x02, 0x03, 0x08, 0x67, 0xF2, 0xF3}  # sha1, ripemd160, sha256, keccak256, reverse, hexlify
BINARY = {0xF0, 0xF1}  # append, prepend


class Refusal(Exception):
    """Why the tool will not do what it was asked."""


# ---- reading a proof, standard library only ----------------------------------------------


class Reader:
    def __init__(self, data: bytes) -> None:
        self.data, self.pos = data, 0

    def take(self, n: int) -> bytes:
        if self.pos + n > len(self.data):
            raise ValueError("the proof ends early")
        out = self.data[self.pos : self.pos + n]
        self.pos += n
        return out

    def byte(self) -> int:
        return self.take(1)[0]

    def varuint(self) -> int:
        value, shift = 0, 0
        while True:
            b = self.byte()
            value |= (b & 0x7F) << shift
            if not b & 0x80:
                return value
            shift += 7

    def varbytes(self) -> bytes:
        return self.take(self.varuint())


def attestations(reader: Reader, depth: int = 0) -> list[tuple[str, object]]:
    """Every attestation in one timestamp tree, as ("bitcoin", height) or ("pending", uri)."""
    if depth > 256:
        raise ValueError("the proof nests deeper than any real one")
    found: list[tuple[str, object]] = []
    tag = reader.byte()
    while True:
        more = tag == 0xFF
        if more:
            tag = reader.byte()
        if tag == 0x00:
            kind, payload = reader.take(8), reader.varbytes()
            if kind == BITCOIN:
                found.append(("bitcoin", Reader(payload).varuint()))
            elif kind == PENDING:
                found.append(("pending", Reader(payload).varbytes().decode("utf-8", "replace")))
            else:
                found.append(("other", kind.hex()))
        elif tag in BINARY:
            reader.varbytes()
            found += attestations(reader, depth + 1)
        elif tag in UNARY:
            found += attestations(reader, depth + 1)
        else:
            raise ValueError(f"unknown operation 0x{tag:02x}")
        if not more:
            return found
        tag = reader.byte()


def read_proof(data: bytes) -> dict:
    """The file hash a detached proof commits to, and its attestations."""
    reader = Reader(data)
    if reader.take(len(MAGIC)) != MAGIC:
        raise ValueError("not an OpenTimestamps proof")
    if reader.varuint() != 1:
        raise ValueError("a proof version this reader does not know")
    if reader.byte() != 0x08:
        raise ValueError("the proof is not over a SHA-256 file hash")
    file_hash = reader.take(32).hex()
    found = attestations(reader)
    if reader.pos != len(data):
        raise ValueError("the proof has bytes after its end")
    return {"file_hash": file_hash, "attestations": found}


def state_of(proof: dict | None) -> tuple[str, int | None]:
    """owed (no proof), pending (the calendars hold it), or confirmed (a Bitcoin block)."""
    if proof is None:
        return "owed", None
    heights = [h for kind, h in proof["attestations"] if kind == "bitcoin"]
    if heights:
        return "confirmed", min(heights)
    return "pending", None


# ---- the builds under data/anchors -------------------------------------------------------


def load_verify(root: Path):
    spec = importlib.util.spec_from_file_location("verify", root / "tools" / "verify.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def builds(root: Path) -> list[dict]:
    """Every anchored or owed build, in build order, with what its files say."""
    out = []
    for manifest in sorted((root / ANCHORS).glob("*.manifest")):
        build = manifest.name[: -len(".manifest")]
        record = json.loads((root / ANCHORS / f"{build}.json").read_text("utf-8"))
        digest = hashlib.sha256(manifest.read_bytes()).hexdigest()
        proof_path = manifest.with_name(manifest.name + ".ots")
        proof = read_proof(proof_path.read_bytes()) if proof_path.is_file() else None
        state, block = state_of(proof)
        out.append(
            {
                "build": build,
                "digest": digest,
                "recorded_digest": record.get("digest"),
                "built_at": record.get("built_at"),
                "proof": proof,
                "state": state,
                "block": block,
            }
        )
    return out


def problems(root: Path) -> list[str]:
    """Every way the files under data/anchors fail to say one consistent thing."""
    found = []
    for b in builds(root):
        if b["recorded_digest"] != b["digest"]:
            found.append(
                f"{b['build']}: the manifest's SHA-256 is {b['digest'][:12]}, and the build's "
                f"record says {str(b['recorded_digest'])[:12]}"
            )
        if b["proof"] and b["proof"]["file_hash"] != b["digest"]:
            found.append(
                f"{b['build']}: the proof commits to {b['proof']['file_hash'][:12]}, not to the "
                f"manifest beside it, {b['digest'][:12]}"
            )
    for proof in sorted((root / ANCHORS).glob("*.ots")):
        if not proof.with_suffix("").is_file():
            found.append(f"{proof.name}: a proof with no manifest beside it")
    return found


NOTES = {
    "owed": "stamp owed; the manifest is written and the calendars have not yet taken it",
    "pending": "the calendars hold it; awaiting a Bitcoin block",
    "confirmed": "",
}


def table(root: Path) -> str:
    rows = [
        "| Build id | Digest (SHA-256, prefix) | Built at (UTC) | Anchor state | Bitcoin block "
        "| Note |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for b in builds(root):
        rows.append(
            f"| `{b['build']}` | `{b['digest'][:16]}…` | {b['built_at']} | {b['state']} | "
            f"{b['block'] if b['block'] is not None else '-'} | {NOTES[b['state']]} |"
        )
    if len(rows) == 2:
        return "*No build has been stamped yet, and no stamp is owed.*"
    return "\n".join(rows)


def ledger_text(root: Path) -> str:
    text = (root / LEDGER).read_text("utf-8")
    if START not in text or END not in text:
        raise Refusal(f"{LEDGER} has no table markers; the table is written between them")
    head, rest = text.split(START, 1)
    _, tail = rest.split(END, 1)
    return f"{head}{START}\n{table(root)}\n{END}{tail}"


# ---- the commands ------------------------------------------------------------------------


def ots(*args: str) -> subprocess.CompletedProcess | None:
    exe = shutil.which("ots")
    if exe is None:
        return None
    return subprocess.run([exe, *args], capture_output=True, text=True, timeout=600)


def stamp(root: Path) -> int:
    verify = load_verify(root)
    meta = json.loads((root / verify.META).read_text("utf-8"))
    build, digest = meta["build"], meta["digest"]
    manifest = verify.manifest(root)
    if hashlib.sha256(manifest).hexdigest() != digest:
        raise Refusal(
            "the tree does not verify against data/meta.json; a stamp of a digest the tree "
            "does not carry would witness nothing. Run python tools/verify.py"
        )
    folder = root / ANCHORS
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{build}.manifest"
    if path.is_file() and path.read_bytes() != manifest:
        raise Refusal(f"{path.name} exists with other bytes; a build's manifest never changes")
    path.write_bytes(manifest)
    record = {"build": build, "built_at": meta["built_at"], "digest": digest}
    (folder / f"{build}.json").write_text(
        json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n"
    )
    owed = [b for b in builds(root) if b["state"] == "owed"]
    if build not in {b["build"] for b in owed}:
        proof = path.with_name(path.name + ".ots")
        print(f"OK    {build} is already stamped: {state_of(read_proof(proof.read_bytes()))[0]}")
    code = 0
    for b in owed:
        path = folder / f"{b['build']}.manifest"
        proof = path.with_name(path.name + ".ots")
        done = ots("stamp", str(path))
        if done is None or done.returncode != 0 or not proof.is_file():
            why = "the ots command is not installed" if done is None else done.stderr.strip()[-300:]
            print(f"OWED  {b['build']}: the manifest is written; the stamp is owed ({why})")
            code = OWED
            continue
        if read_proof(proof.read_bytes())["file_hash"] != b["digest"]:
            proof.unlink()
            raise Refusal(f"{proof.name} did not commit to the digest; it was removed")
        print(
            f"OK    {b['build']} stamped; the calendars hold digest {b['digest'][:16]}…, "
            "awaiting Bitcoin"
        )
    return code


def upgrade(root: Path) -> int:
    waiting = [b for b in builds(root) if b["state"] == "pending"]
    for b in waiting:
        proof = root / ANCHORS / f"{b['build']}.manifest.ots"
        backup = proof.with_name(proof.name + ".bak")
        backup.unlink(missing_ok=True)
        done = ots("upgrade", str(proof))
        backup.unlink(missing_ok=True)
        if done is None:
            print("OWED  the ots command is not installed; nothing was upgraded")
            return OWED
        state, block = state_of(read_proof(proof.read_bytes()))
        shown = f"confirmed in Bitcoin block {block}" if state == "confirmed" else state
        print(f"{'OK  ' if state == 'confirmed' else 'WAIT'}  {b['build']}: {shown}")
    if not waiting:
        print("OK    no proof is waiting for Bitcoin")
    return 0


def check(root: Path) -> int:
    found = problems(root)
    if (root / LEDGER).read_text("utf-8") != ledger_text(root):
        found.append(f"{LEDGER}: the table does not say what the proofs say; run --ledger")
    for line in found:
        print(f"FAIL  {line}")
    if found:
        return 1
    counts: dict[str, int] = {}
    for b in builds(root):
        counts[b["state"]] = counts.get(b["state"], 0) + 1
    said = ", ".join(f"{n} {state}" for state, n in sorted(counts.items())) or "no build yet"
    print(
        f"OK    ANCHORS.md says what the proofs say ({said}); each proof commits to the "
        "manifest beside it, and each manifest to its build's digest."
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("root", nargs="?", default=".", help="repository root (default: .)")
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--stamp", action="store_true", help="write and stamp this build")
    action.add_argument("--upgrade", action="store_true", help="complete pending proofs")
    action.add_argument("--ledger", action="store_true", help="rewrite the ANCHORS.md table")
    action.add_argument("--status", action="store_true", help="each build and its state")
    args = parser.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    root = Path(args.root).resolve()
    try:
        if args.stamp or args.upgrade:
            code = stamp(root) if args.stamp else upgrade(root)
            (root / LEDGER).write_text(ledger_text(root), encoding="utf-8", newline="\n")
            return code
        if args.ledger:
            (root / LEDGER).write_text(ledger_text(root), encoding="utf-8", newline="\n")
            print(f"wrote the table in {LEDGER}")
            return 0
        if args.status:
            for b in builds(root):
                block = f" at block {b['block']}" if b["block"] is not None else ""
                print(f"{b['build']}  {b['digest'][:16]}…  {b['state']}{block}")
            return 0
        return check(root)
    except (Refusal, ValueError) as refusal:
        print(f"REFUSED  {refusal}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
