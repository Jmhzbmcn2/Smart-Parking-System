"""T-06: write automated pytest results into the test_cases sheet of the requirements workbook.

    uv run --directory backend pytest -q --junitxml=report.xml
    uv run --directory backend python mocks/update_test_cases.py --junit report.xml --executor "<name>"

A TC passes only if every test_tc<NN>_* test passes. TCs without an automated test are not touched
(TC-17 comes from docs/testing/tc17-results.md, TC-18 stays Not Run). Other sheets are not touched.
A hand-written actual_result of a Pass is kept; failures always overwrite.
"""

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from datetime import date
from pathlib import Path

import openpyxl

DEFAULT_WORKBOOK = Path(__file__).resolve().parents[2] / "docs" / "requirements" / "SPMS_requirements.xlsx"
AUTOMATED = "Automated:"


def tc_id(test_name: str) -> str | None:
    match = re.match(r"test_tc(\d{2})_", test_name)
    return f"TC-{match.group(1)}" if match else None


def read_junit(path: Path) -> dict[str, list[str | None]]:
    """TC id -> one entry per test: None if it passed, else the failure message."""
    results: dict[str, list[str | None]] = {}
    for case in ET.parse(path).getroot().iter("testcase"):
        tc = tc_id(case.get("name", ""))
        if tc is None:
            continue
        problem = case.find("failure")
        if problem is None:
            problem = case.find("error")
        message = None if problem is None else (problem.get("message") or "failed")
        results.setdefault(tc, []).append(message)
    return results


def update(workbook: Path, results: dict[str, list[str | None]], executor: str, when: str) -> list[str]:
    wb = openpyxl.load_workbook(workbook)
    sheet = wb["test_cases"]
    col = {cell.value: cell.column for cell in sheet[1]}
    changed = []
    for row in range(2, sheet.max_row + 1):
        tc = sheet.cell(row, col["id"]).value
        if tc not in results:
            continue
        failures = [m for m in results[tc] if m is not None]
        kept = sheet.cell(row, col["actual_result"]).value
        if not failures and kept and not str(kept).startswith(AUTOMATED):
            actual = kept
        elif failures:
            actual = failures[0]
        else:
            actual = f"{AUTOMATED} {len(results[tc])} test(s) passed"
        for name, value in (
            ("status", "Fail" if failures else "Pass"),
            ("actual_result", actual),
            ("executed_by", executor),
            ("executed_date", when),
        ):
            sheet.cell(row, col[name]).value = value
        changed.append(f"{tc}: {'Fail' if failures else 'Pass'}")
    wb.save(workbook)
    return changed


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--junit", type=Path, required=True)
    parser.add_argument("--executor", required=True)
    parser.add_argument("--date", default=date.today().isoformat())
    parser.add_argument("--workbook", type=Path, default=DEFAULT_WORKBOOK)
    args = parser.parse_args()
    changed = update(args.workbook, read_junit(args.junit), args.executor, args.date)
    print("\n".join(changed))
    sys.exit(0)


if __name__ == "__main__":
    main()
