#!/usr/bin/env python3
"""
Запускает diag_connectivity.py, парсит JSON-строки и формирует краткий отчёт.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, List


def run_diag() -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "diag_connectivity.py"],
        capture_output=True,
        text=True,
        check=False,
    )


def parse_lines(output: str) -> List[Dict]:
    items: List[Dict] = []
    for line in output.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            items.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return items


def format_report(entries: List[Dict]) -> str:
    rows = ["| Component | Status | Message |", "| --- | --- | --- |"]
    for entry in entries:
        rows.append(
            f"| {entry.get('component')} | {entry.get('status')} | {entry.get('message')} |"
        )
    return "\n".join(rows)


def main() -> None:
    result = run_diag()
    entries = parse_lines(result.stdout)
    report = format_report(entries)
    Path("diag_report.md").write_text(report + "\n", encoding="utf-8")
    print(report)
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
