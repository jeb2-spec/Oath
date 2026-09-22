#!/usr/bin/env python3
"""Prove the verifier is not decorative.

Three checks, in the order RUBRIC.md gate 4 and METHODOLOGY.md §7.3 name them:

  1. Copy the sealed files to a throwaway directory, change one character of a
     disclosure in data/meta.json, run tools/verify.py there, and require FAIL.
  2. Run tools/verify.py on the real tree and require OK, because a checker that
     rejects everything is not a checker.
  3. Recompute the digest from the sealed files with the code below, which imports
     nothing from the verifier or the sealer and re-implements the manifest rule
     from its written description, and require it to equal the recorded digest.

Standard-library Python 3.11+. Exits 0 when all three pass, 1 otherwise.

    python3 tools/tamper-test.py
    python3 tools/tamper-test.py <root>
"""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

DOCTRINE = [
    "CHARTER.md",
    "RUBRIC.md",
    "INVARIANTS.md",
    "BYLAWS.md",
    "COUNCIL.md",
    "METHODOLOGY.md",
    "STANDARDS.md",
    "SOURCES.md",
    "LIMITATIONS.md",
    "SPEC.md",
    "ECOSYSTEM.md",
]


def independent_digest(root: Path) -> str:
    """The manifest rule, written again from its description, sharing no code."""
    lines: list[bytes] = []
    for path in sorted(root.glob("data/**/*.ndjson")):
        rel = path.relative_to(root).as_posix()
        lines.append(f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {rel}\n".encode())
    for name in DOCTRINE:
        lines.append(f"{hashlib.sha256((root / name).read_bytes()).hexdigest()}  {name}\n".encode())
    meta = json.loads((root / "data" / "meta.json").read_text(encoding="utf-8"))
    meta.pop("digest", None)
    canon = (
        json.dumps(meta, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n"
    ).encode("utf-8")
    lines.append(f"{hashlib.sha256(canon).hexdigest()}  data/meta.json\n".encode())
    return hashlib.sha256(b"".join(sorted(lines))).hexdigest()


def run_verify(verify: Path, root: Path) -> tuple[int, str]:
    proc = subprocess.run(
        [sys.executable, str(verify), str(root)], capture_output=True, text=True, encoding="utf-8"
    )
    return proc.returncode, proc.stdout


def copy_sealed(root: Path, dest: Path) -> None:
    for path in root.glob("data/**/*.ndjson"):
        target = dest / path.relative_to(root)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, target)
    for name in DOCTRINE:
        shutil.copyfile(root / name, dest / name)
    (dest / "data").mkdir(exist_ok=True)
    shutil.copyfile(root / "data" / "meta.json", dest / "data" / "meta.json")


def main(argv: list[str] | None = None) -> int:
    root = Path(argv[0] if argv else ".").resolve()
    verify = Path(__file__).resolve().parent / "verify.py"
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ok = True

    with tempfile.TemporaryDirectory() as tmp:
        altered = Path(tmp) / "altered"
        altered.mkdir()
        copy_sealed(root, altered)
        meta_path = altered / "data" / "meta.json"
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        key = sorted(meta["disclosures"])[0]
        meta["disclosures"][key] = str(meta["disclosures"][key]) + "."
        meta_path.write_text(json.dumps(meta, indent=2, sort_keys=True), encoding="utf-8")
        code, out = run_verify(verify, altered)
        passed = code != 0 and "FAIL" in out
        ok &= passed
        verdict = "rejected it" if passed else "ACCEPTED IT"
        mark = "pass" if passed else "FAIL"
        print(
            f"[{mark}] 1. one character added to disclosure '{key}' in a copy: verifier {verdict}"
        )

    code, out = run_verify(verify, root)
    passed = code == 0 and "OK" in out
    ok &= passed
    verdict = "accepted it" if passed else "REJECTED IT"
    mark = "pass" if passed else "FAIL"
    print(f"[{mark}] 2. the real tree: verifier {verdict}")

    recorded = str(
        json.loads((root / "data" / "meta.json").read_text(encoding="utf-8")).get("digest", "")
    )
    independent = independent_digest(root)
    passed = bool(recorded) and independent == recorded
    ok &= passed
    verdict = "equals" if passed else "DIFFERS FROM"
    mark = "pass" if passed else "FAIL"
    print(f"[{mark}] 3. independent recomputation, no shared code: {independent[:16]}...")
    print(f"       {verdict} the recorded digest {recorded[:16] or '(none)'}...")

    print(
        "\n"
        + (
            "All three checks pass. The seal can be trusted to detect change."
            if ok
            else "A check failed. The seal cannot be trusted until this is fixed."
        )
    )
    print("Integrity is not accuracy.")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
