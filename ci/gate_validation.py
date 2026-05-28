from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Deployment quality gate")
    parser.add_argument(
        "--report",
        default="reports/validation_report.json",
        help="Path to validation report",
    )
    args = parser.parse_args()

    report_path = Path(args.report)
    if not report_path.exists():
        print(f"FAIL: validation report not found at {report_path}")
        return 2

    report = json.loads(report_path.read_text(encoding="utf-8"))

    if report.get("status") == "passed":
        print("PASS: AI validation gate satisfied")
        return 0

    print("FAIL: AI validation gate failed")
    checks = report.get("checks", {})
    for name, ok in checks.items():
        print(f"- {name}: {'PASS' if ok else 'FAIL'}")

    for err in report.get("errors", []):
        print(f"- error: {err}")

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
