from __future__ import annotations

import argparse
from pathlib import Path

from pptx_audit_lib import audit_pptx, pptx_files, write_audit_reports


ALLOWED_AFTER_ISSUES = {"font_too_small"}


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate revised PPTX files.")
    parser.add_argument("--input", default="dist/ppt_revised")
    parser.add_argument("--csv", default="reports/ppt_audit_after.csv")
    parser.add_argument("--md", default="reports/ppt_audit_after.md")
    args = parser.parse_args()

    files = pptx_files(Path(args.input))
    audits = [audit_pptx(path) for path in files]
    write_audit_reports(audits, Path(args.csv), Path(args.md), "PPT 修订后审计报告")

    blocking = []
    for audit in audits:
        for issue in audit.issues:
            if issue["issue_type"] not in ALLOWED_AFTER_ISSUES:
                blocking.append(issue)

    if len(files) != 16:
        print(f"[FAIL] expected 16 revised PPTX files, got {len(files)}")
        return 1
    if blocking:
        print(f"[FAIL] revised PPTX validation found {len(blocking)} blocking issues")
        for issue in blocking[:20]:
            print(f"  - {issue['file']} slide {issue['slide']}: {issue['issue_type']} {issue['detail']}")
        return 1
    print("[OK] revised PPTX validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
