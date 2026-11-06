"""Regression tests for the OpenCode review findings (round 2).

#8 (occurrence counter) is documented as an accepted limitation, not fixed here.
"""
import pytest

from bug_hunter import Finding, classify_report, scan_path, scan_source, to_sarif


def rules(src):
    return {f.rule_id for f in scan_source(src)}


# 1 — substring matching produces false root causes


def test_report_ignores_substring_matches():
    assert classify_report("print(x)")["root_cause"] != "WRONG_TYPE_CONVERSION"
    assert classify_report("nonempty list")["root_cause"] != "MISSING_GUARD"
    # real signals must still work
    assert classify_report("TypeError: unsupported operand type(s)")["root_cause"] == "WRONG_TYPE_CONVERSION"


# 2 — **kwargs must not fake a timeout finding

def test_kwargs_unpack_suppresses_timeout_false_positive():
    assert "BH009" not in rules("import subprocess\nsubprocess.run(cmd, **opts)\n")


# 3 — non-constant shell value must still be flagged

def test_shell_variable_is_flagged():
    assert "BH012" in rules("import subprocess\nsubprocess.call(cmd, shell=sh)\n")

def test_shell_false_is_not_flagged():
    assert "BH012" not in rules("import subprocess\nsubprocess.call(cmd, shell=False, timeout=3)\n")


# 5 — augmented assignment target is never scanned

def test_augassign_target_is_visited():
    assert "BH001" in rules("d[eval(k)] += 1\n")


# 7 — SARIF must relativize to base and not claim SRCROOT wrongly

def test_sarif_relativizes_to_base(tmp_path):
    target = tmp_path / "sub" / "a.py"
    target.parent.mkdir()
    target.write_text("x = 1\n")
    finding = Finding("BH001", str(target), 1, 1, "m", "WARNING", "UNSAFE_EVAL", "CWE-95", "fix", "fp1")
    sarif = to_sarif([finding], str(tmp_path))
    loc = sarif["runs"][0]["results"][0]["locations"][0]["physicalLocation"]["artifactLocation"]
    assert loc["uri"] == "sub/a.py"
    assert loc["uriBaseId"] == "%SRCROOT%"


# 9 — skipped symlinked .py must be surfaced, not silently dropped

def test_skipped_symlink_is_surfaced(tmp_path):
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "real.py").write_text("x = 1\n")
    root = tmp_path / "root"
    root.mkdir()
    (root / "link.py").symlink_to(outside / "real.py")
    findings = scan_path(root)
    assert any(f.rule_id == "BH_SKIP" for f in findings)


# 10 — module-level annotation expressions are evaluated at runtime

def test_module_level_annotation_is_visited():
    assert "BH001" in rules("x: eval(u) = 0\n")
