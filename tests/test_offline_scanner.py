"""Regression tests for the deterministic read-only bug_hunter scanner."""
import json
from pathlib import Path
from bug_hunter import scan_source, classify_report, to_sarif, scan_path


def rules(source):
    return {f.rule_id for f in scan_source(source)}


def test_shell_alias():
    assert 'BH012' in rules("from subprocess import run as r\nr('x', shell=True)")

def test_local_run_no_false_positive():
    assert 'BH009' not in rules('def run(x): return x\nrun(1)')

def test_yaml_unsafe():
    assert 'BH003' in rules('import yaml\nyaml.load(x, Loader=yaml.Loader)')

def test_yaml_safe():
    assert 'BH003' not in rules('import yaml\nyaml.load(x, Loader=yaml.SafeLoader)')

def test_report_uncertainty():
    assert classify_report('completely unrelated report')['root_cause'] == 'UNKNOWN_ROOT_CAUSE'

def test_scan_does_not_modify_source(tmp_path):
    f = tmp_path / 'test.py'
    f.write_text('eval(input())')
    before = f.read_bytes()
    result = scan_path(str(f))
    assert f.read_bytes() == before
    assert result

def test_sarif_version():
    assert to_sarif(scan_source('eval(x)'), 'test.py')['version'] == '2.1.0'
