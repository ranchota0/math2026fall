from __future__ import annotations

import argparse
from pathlib import Path

from pptx_audit_lib import audit_pptx, pptx_files, write_audit_reports


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit PPTX files without modifying them.")
    parser.add_argument("--input", default="郭立华2026秋数学PPT", help="PPTX file or directory")
    parser.add_argument("--csv", default="reports/ppt_audit_before.csv")
    parser.add_argument("--md", default="reports/ppt_audit_before.md")
    parser.add_argument("--title", default="PPT 修订前审计报告")
    args = parser.parse_args()

    root = Path(args.input)
    files = [root] if root.is_file() else pptx_files(root)
    audits = [audit_pptx(path) for path in files]
    write_audit_reports(audits, Path(args.csv), Path(args.md), args.title)
    print(f"[OK] audited {len(audits)} pptx files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
