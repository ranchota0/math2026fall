from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULTS_JSON = ROOT / "logs" / "compile_results.json"
REPORT = ROOT / "reports" / "build_report.csv"
FIELDS = [
    "file",
    "type",
    "status",
    "pdf_pages",
    "compile_seconds",
    "warnings",
    "overfull_boxes",
    "error_message",
    "timestamp",
]


def main() -> int:
    if RESULTS_JSON.exists():
        rows = json.loads(RESULTS_JSON.read_text(encoding="utf-8"))
    else:
        rows = []

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    with REPORT.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in FIELDS})

    print(f"[OK] wrote {REPORT.relative_to(ROOT)} with {len(rows)} rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
