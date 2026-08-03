#!/usr/bin/env python3
"""Build the three approved Phase 5 pilot lesson plans only."""
from __future__ import annotations

import csv
import sys
from datetime import datetime
from pathlib import Path

from build_lessonplan import ROOT, build


PILOT_LESSONS = ["C01-L03", "C05-L05", "C06-L07"]


def main() -> int:
    rows = []
    for lesson_id in PILOT_LESSONS:
        result = build(lesson_id)
        result["status"] = "compiled"
        result["timestamp"] = datetime.now().isoformat(timespec="seconds")
        rows.append(result)
        print(f"[OK] {lesson_id} -> {result['dist_pdf']}")

    report = ROOT / "reports/pilot_lessonplans_build.csv"
    report.parent.mkdir(parents=True, exist_ok=True)
    with report.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["lesson_id", "title", "status", "build_pdf", "dist_pdf", "compile_seconds", "log", "timestamp"],
        )
        writer.writeheader()
        writer.writerows(rows)
    print(f"[OK] build report -> {report.relative_to(ROOT).as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
