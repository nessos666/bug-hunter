"""Scanner unit tests (python -m unittest discover -s tests)."""
import unittest
from bug_hunter.scanner import scan_source


class ScannerTests(unittest.TestCase):
    def assertFinds(self, source, required, forbidden=frozenset()):
        actual = {f.rule_id for f in scan_source(source)}
        self.assertTrue(required <= actual, "%s not in %s" % (required, actual))
        self.assertFalse(forbidden & actual, "forbidden %s" % (forbidden & actual))

    def test_eval(self): self.assertFinds("eval(input())", {"BH001"})
    def test_shell(self): self.assertFinds("import subprocess as sp\nsp.run('x', shell=True)", {"BH012", "BH009"})
    def test_alias_shell(self): self.assertFinds("from subprocess import run as r\nr('x', shell=True)", {"BH012"})
    def test_local_run(self): self.assertFinds("def run(x): return x\nrun(1)", set(), {"BH009", "BH012"})
    def test_yaml_unsafe(self): self.assertFinds("import yaml\nyaml.load('x', Loader=yaml.Loader)", {"BH003"})
    def test_yaml_safe(self): self.assertFinds("import yaml\nyaml.load('x', Loader=yaml.SafeLoader)", set(), {"BH003", "BH014"})
    def test_pickle_alias(self): self.assertFinds("import pickle as p\np.loads(b'x')", {"BH002"})
    def test_bare_except(self): self.assertFinds("try: pass\nexcept: pass", {"BH005", "BH011"})
    def test_none(self): self.assertFinds("if None == x: pass", {"BH006"})
    def test_mutable_kw(self): self.assertFinds("def f(*, x={}): pass", {"BH007"})
    def test_with_open(self): self.assertFinds("with open('x') as f: pass", set(), {"BH008"})
    def test_async_with(self): self.assertFinds("async def f():\n    async with open('x') as h: pass", set(), {"BH008"})
    def test_open(self): self.assertFinds("f = open('x')", {"BH008"})
    def test_shadow_eval(self): self.assertFinds("def f(eval):\n    return eval('x')", set(), {"BH001"})
    def test_check_output(self): self.assertFinds("from subprocess import check_output\ncheck_output(['x'])", {"BH009"})
    def test_safe_call(self): self.assertFinds("import subprocess\nsubprocess.run(['x'], timeout=3)", set(), {"BH009", "BH012"})
    def test_syntax(self): self.assertFinds("def :", {"BH_PARSE"})
    def test_compile(self): self.assertFinds("compile('x', '<x>', 'exec')", {"BH013"})


if __name__ == "__main__":
    unittest.main()
