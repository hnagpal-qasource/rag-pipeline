import json
import tempfile
import unittest
from pathlib import Path

from ci.gate_validation import main as gate_main


class TestGate(unittest.TestCase):
    def test_gate_passes(self):
        with tempfile.TemporaryDirectory() as td:
            report = Path(td) / "report.json"
            report.write_text(json.dumps({"status": "passed"}), encoding="utf-8")
            code = gate_main_wrapper(report)
            self.assertEqual(code, 0)

    def test_gate_fails(self):
        with tempfile.TemporaryDirectory() as td:
            report = Path(td) / "report.json"
            report.write_text(json.dumps({"status": "failed", "checks": {"groundedness": False}}), encoding="utf-8")
            code = gate_main_wrapper(report)
            self.assertEqual(code, 1)


def gate_main_wrapper(path: Path) -> int:
    import sys

    original = sys.argv
    try:
        sys.argv = ["gate_validation.py", "--report", str(path)]
        return gate_main()
    finally:
        sys.argv = original


if __name__ == "__main__":
    unittest.main()
