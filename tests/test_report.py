"""Report classifier tests."""
import unittest
from bug_hunter.report import classify_report


class ReportTests(unittest.TestCase):
    def test_type_error(self):
        self.assertEqual(classify_report("TypeError: unsupported operand type(s) for +: 'int' and 'str'")["root_cause"], "WRONG_TYPE_CONVERSION")
    def test_missing(self):
        self.assertEqual(classify_report("ModuleNotFoundError: No module named 'requests'")["root_cause"], "MISSING_DEPENDENCY")
    def test_unknown(self):
        self.assertEqual(classify_report("something unrelated")["root_cause"], "UNKNOWN_ROOT_CAUSE")


if __name__ == "__main__":
    unittest.main()
