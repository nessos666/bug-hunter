"""Regression tests for the defects found by the Codex reviews (A + B).

Each test reproduces one confirmed defect; all must fail before the fix and
pass after it.
"""
import json
import os

import pytest

from bug_hunter import main, scan_path, scan_source


def rules(src):
    return {f.rule_id for f in scan_source(src)}


# --------------------------------------------------------------------------
# A#1 FIFO named *.py must never be read (blocks forever)
# --------------------------------------------------------------------------


@pytest.mark.timeout(20)

def test_fifo_is_not_read_and_reports_bh_io(tmp_path):
    fifo = tmp_path / "blocked.py"
    os.mkfifo(fifo)
    findings = scan_path(tmp_path)
    assert any(f.rule_id == "BH_IO" for f in findings)


# --------------------------------------------------------------------------
# A#2 / B#3 unreadable subtree must emit BH_IO (os.walk onerror)
# --------------------------------------------------------------------------

def test_unreadable_directory_emits_bh_io(tmp_path):
    locked = tmp_path / "locked"
    locked.mkdir()
    (locked / "a.py").write_text("x = 1\n")
    locked.chmod(0o000)
    try:
        findings = scan_path(tmp_path)
    finally:
        locked.chmod(0o755)
    assert any(f.rule_id == "BH_IO" for f in findings)


# --------------------------------------------------------------------------
# A#3 / B#4 baseline must not hide operational failures (exit stays 2)
# --------------------------------------------------------------------------

def test_baseline_does_not_hide_parse_failure(tmp_path):
    bad = tmp_path / "bad.py"
    bad.write_text("def :\n")
    findings = scan_source("def :\n", path=str(bad))
    assert findings and findings[0].rule_id == "BH_PARSE"
    baseline = tmp_path / "baseline.json"
    baseline.write_text(json.dumps([findings[0].fingerprint]))
    rc = main(["scan", str(bad), "--baseline", str(baseline)])
    assert rc == 2


# --------------------------------------------------------------------------
# B#6 class attribute must not shadow a builtin inside a method
# --------------------------------------------------------------------------

def test_class_attribute_does_not_shadow_builtin_in_method():
    src = "class C:\n    eval = staticmethod(str)\n    def m(self):\n        return eval('x')\n"
    assert "BH001" in rules(src)


# --------------------------------------------------------------------------
# B#7 import after function definition must still resolve
# --------------------------------------------------------------------------

def test_import_after_function_is_resolved():
    src = "def f():\n    return pickle.loads(d)\nimport pickle\n"
    assert "BH002" in rules(src)


# --------------------------------------------------------------------------
# A#6 branches must not poison each other
# --------------------------------------------------------------------------

def test_if_else_branches_are_independent():
    src = "import pickle\nif flag:\n    pickle = None\nelse:\n    pickle.loads(d)\n"
    assert "BH002" in rules(src)


# --------------------------------------------------------------------------
# A#7 annotated assignment keeps the alias origin
# --------------------------------------------------------------------------

def test_annassign_keeps_alias():
    src = "import pickle\np: object = pickle\np.loads(d)\n"
    assert "BH002" in rules(src)


# --------------------------------------------------------------------------
# A#8 annotations and class keyword expressions are executed -> must be visited
# --------------------------------------------------------------------------

def test_function_annotation_is_visited():
    assert "BH001" in rules("def f(x: eval(p)):\n    pass\n")

def test_class_keyword_expression_is_visited():
    assert "BH001" in rules("class C(metaclass=eval(p)):\n    pass\n")


# --------------------------------------------------------------------------
# A#9 lambda keyword-only defaults visited, vararg binds
# --------------------------------------------------------------------------

def test_lambda_keyword_default_is_visited():
    assert "BH001" in rules("f = lambda *, x=eval(p): x\n")

def test_lambda_vararg_shadows_builtin():
    assert "BH001" not in rules("f = lambda *eval: eval('x')\n")


# --------------------------------------------------------------------------
# A#10 positional shell argument for Popen
# --------------------------------------------------------------------------

def test_popen_positional_shell():
    # Popen signature: args, bufsize, executable, stdin, stdout, stderr,
    # preexec_fn, close_fds, shell  -> shell is index 8 (9 positional args).
    src = "import subprocess\nsubprocess.Popen('cmd', -1, None, None, None, None, None, True, True)\n"
    assert "BH012" in rules(src)


# --------------------------------------------------------------------------
# A#11 mutable constructor defaults
# --------------------------------------------------------------------------

@pytest.mark.parametrize("ctor", ["list", "dict", "set"])

def test_mutable_constructor_default(ctor):
    assert "BH007" in rules("def f(a=%s()):\n    pass\n" % ctor)


# --------------------------------------------------------------------------
# A#12 symlink cycle must terminate
# --------------------------------------------------------------------------

@pytest.mark.timeout(20)

def test_symlink_cycle_terminates(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    (root / "a.py").write_text("x = 1\n")
    (root / "loop").symlink_to(root, target_is_directory=True)
    scan_path(root, follow_symlinks=True)   # must return


# --------------------------------------------------------------------------
# B#1 unknown severity must block, not slip through
# --------------------------------------------------------------------------
