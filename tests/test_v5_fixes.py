"""Regression tests for the three v5 fixes (from the 10-agent research).

1. Deeply nested source must return a diagnostic, never crash with RecursionError.
2. Shadowing in one function must not disable a rule for the whole file.
3. Finding fingerprints must be content-based (stable when a line is inserted above).
"""
import pytest

from bug_hunter import scan_source, to_sarif


# --- 1. RecursionError ------------------------------------------------------


def test_deep_expression_returns_diagnostic_instead_of_crashing():
    src = "x = " + " + ".join(["1"] * 5000)
    findings = scan_source(src)          # must not raise
    assert isinstance(findings, list)
    assert any(f.rule_id in {"BH_PARSE", "BH_LIMIT"} for f in findings)

def test_deep_attribute_chain_returns_diagnostic():
    src = "x = a" + ".b" * 3000
    findings = scan_source(src)          # must not raise
    assert any(f.rule_id in {"BH_PARSE", "BH_LIMIT"} for f in findings)


# --- 2. Scope shadowing -----------------------------------------------------

def test_shadowing_in_one_function_does_not_disable_file():
    src = "def helper(eval):\n    return eval('x')\neval('y')\n"
    assert [f.rule_id for f in scan_source(src)].count("BH001") == 1


# --- 3. Content-based fingerprint -------------------------------------------

def test_fingerprint_stable_when_line_inserted_above():
    a = scan_source("eval('x')\n")
    b = scan_source("# inserted comment\n\neval('x')\n")
    assert a[0].fingerprint == b[0].fingerprint

def test_fingerprint_unique_for_distinct_lines():
    src = "eval('x')\neval('y')\n"
    fps = [f.fingerprint for f in scan_source(src)]
    assert len(fps) == 2 and fps[0] != fps[1]

def test_fingerprint_unique_for_identical_lines():
    src = "eval('x')\neval('x')\n"
    fps = [f.fingerprint for f in scan_source(src)]
    assert len(fps) == 2 and fps[0] != fps[1]

def test_sarif_fingerprints_stable_under_insertion():
    a = to_sarif(scan_source("eval('x')\n"))
    b = to_sarif(scan_source("# c\n\neval('x')\n"))
    fa = a["runs"][0]["results"][0]["partialFingerprints"]["primaryLocationLineHash"]
    fb = b["runs"][0]["results"][0]["partialFingerprints"]["primaryLocationLineHash"]
    assert fa == fb
