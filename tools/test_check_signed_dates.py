"""Tests for tools/check-signed-dates.py: the date a report's own signature line gives."""

from __future__ import annotations

import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _load():
    tool = HERE / "check-signed-dates.py"
    spec = importlib.util.spec_from_file_location("check_signed_dates", tool)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


signed = _load()


def test_the_signature_line_gives_the_date_the_filer_signed():
    text = "I CERTIFY that the statements ...\nDigitally Signed: Hon. A. Example , 02/13/2025\n"
    assert signed.signed_on(text) == "2025-02-13"


def test_a_report_with_no_signature_line_gives_no_date_rather_than_a_guess():
    assert signed.signed_on("Filing ID #20024346\nS 01/13/2025 01/13/2025 $1,001 - $15,000") is None


def test_the_last_signature_line_is_the_one_read():
    text = "Digitally Signed: A , 01/02/2025\n...\nDigitally Signed: A , 03/04/2025\n"
    assert signed.signed_on(text) == "2025-03-04"
