"""Regression tests for the GGCoder + Claude Code reviews (round 3)."""
import pytest

from bug_hunter import _coerce_finding, scan_file, scan_source


def rules(src):
    return {f.rule_id for f in scan_source(src)}


# --- GGCoder ---


def test_import_in_if_branch_keeps_later_binding():
    src = "if flag:\n    import subprocess\nsubprocess.run(cmd, shell=True)\n"
    assert "BH012" in rules(src)

def test_yaml_loader_from_submodule_is_safe():
    src = "from yaml.loader import SafeLoader\nimport yaml\nyaml.load(x, Loader=SafeLoader)\n"
    assert "BH003" not in rules(src)

def test_yaml_fullloader_is_safe():
    assert "BH003" not in rules("import yaml\nyaml.load(x, Loader=yaml.FullLoader)\n")

def test_yaml_loader_bare_is_unsafe():
    assert "BH003" in rules("import yaml\nyaml.load(x, Loader=yaml.Loader)\n")

def test_relative_import_binds_name():
    src = "from . import subprocess\nsubprocess.run(cmd, shell=True)\n"
    assert "BH012" in rules(src)

def test_builtins_alias_is_detected():
    assert "BH001" in rules("import builtins as b\nb.eval(x)\n")

def test_unknown_encoding_is_skip_not_io(tmp_path):
    target = tmp_path / "weird.py"
    target.write_bytes(b"# coding: nonsense-enc\nx = 1\n")
    findings = scan_file(target)
    assert findings and findings[0].rule_id == "BH_SKIP"

def test_coerce_finding_raises_value_error():
    with pytest.raises(ValueError):
        _coerce_finding({"rule_id": "X"})


# --- Claude Code ---

def test_shell_true_with_kwargs_still_flags():
    src = "import subprocess\nsubprocess.run(cmd, shell=True, **kw)\n"
    assert "BH012" in rules(src)

def test_loop_body_assignment_does_not_erase_import():
    src = "import subprocess as sp\nfor item in items:\n    sp = item\nsp.run(cmd, shell=True)\n"
    assert "BH012" in rules(src)

def test_timeout_none_does_not_suppress():
    src = "import subprocess\nsubprocess.run(cmd, timeout=None)\n"
    assert "BH009" in rules(src)

def test_pathlib_path_open_detected():
    src = "from pathlib import Path\nPath(x).open()\n"
    assert "BH008" in rules(src)

def test_lambda_mutable_default():
    assert "BH007" in rules("f = lambda x=[]: x\n")

def test_class_annotation_inside_function_is_visited():
    src = "def f():\n    class C:\n        x: eval(u) = 0\n"
    assert "BH001" in rules(src)
