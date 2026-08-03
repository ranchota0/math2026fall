#!/usr/bin/env python3
"""Validate the complete Phase 7 teacher lesson-plan delivery."""
from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from pathlib import Path

import yaml
import pdfplumber
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "output" / "lesson_plans_final"
REPORT_JSON = OUTPUT / "reports" / "automatic_validation.json"
REPORT_MD = ROOT / "reports" / "phase7_automatic_validation.md"
APPROVED = {"C01-L03", "C05-L05", "C06-L07"}
FROZEN_HASHES = {
    "tex/lessonplan/hepingjie_lessonplan.sty": "1A11888DB7ECA9FF51B0D3691B9EA765AE710B4D35A0090347AC43487D6AA1B4",
    "scripts/build_lessonplans_v2.py": "8D9C2AB5FB0377D2A2A58F0EAE0069CD10F314300B85A54FF623FB84852DC069",
    "config/lessonplan_style.yml": "83943BE1673992DBE546D553A85EE5D3696664E06E524B862B4747B32BC3B29E",
    "reports/phase6_1_template_freeze_report.md": "31708A51A90BFA5A53232C1D0E232913356E69B68CE0EF6A752D6CB871E838EB",
}
APPROVED_PDF_HASHES = {
    "C01-L03": "E081CC01273A9585E337047406C9BFCE4C34AC163A94783A53A1E001F59F0352",
    "C05-L05": "68A435ADFD7B5920C37A44155AA92E43C3438778EE51790CA4F31414A164EAE2",
    "C06-L07": "FCFC4DE162CFD88F25F3B3B468D86AB9AEB5933F4E874EADE09E34A7C84770D5",
}
FORBIDDEN_TEX = {
    "itemize": re.compile(r"\\begin\s*\{itemize\}"),
    "textbullet": re.compile(r"\\textbullet|\\bullet|\\ding\s*\{"),
    "negative_spacing": re.compile(r"\\(?:hspace\*?|vspace\*?)\s*\{\s*-"),
    "zero_width_box": re.compile(r"\\makebox\s*\[\s*0pt\s*\]"),
}
PLACEHOLDERS = ("此处为", "待补充", "TODO", "完成相关练习", "教师适当讲解", "布置相关题目")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def pdf_geometry(path: Path) -> tuple[int, bool]:
    # Use the project Python dependency instead of invoking ``pdfinfo``.
    # On Windows the bundled Poppler launcher can be a .cmd wrapper, which
    # CreateProcess cannot execute directly when shell=False.
    with pdfplumber.open(path) as pdf:
        if not pdf.pages:
            return 0, False
        width = float(pdf.pages[0].width)
        height = float(pdf.pages[0].height)
        return len(pdf.pages), 590 <= width <= 600 and 837 <= height <= 847 and height > width


def process_text(data: dict) -> str:
    return json.dumps(data.get("process", []), ensure_ascii=False)


def validate_row(row: dict) -> dict:
    lesson_id = row["lesson_id"]
    errors: list[str] = []
    warnings: list[str] = []
    yaml_path = ROOT / row["source_yaml"]
    tex_path = ROOT / row["source_tex"]
    pdf_path = ROOT / row["output_pdf"]
    contact = OUTPUT / "contact_sheets" / f"{lesson_id}_contact-sheet.png"
    png_dir = OUTPUT / "png" / lesson_id
    for label, path in (("YAML", yaml_path), ("TeX", tex_path), ("PDF", pdf_path), ("contact sheet", contact)):
        if not path.exists():
            errors.append(f"missing {label}: {path.relative_to(ROOT)}")
    if errors:
        return {"lesson_id": lesson_id, "status": "failed", "errors": errors, "warnings": warnings}

    data = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    tex = tex_path.read_text(encoding="utf-8")
    stages = [item.get("stage", "") for item in data.get("process", [])]
    minutes = sum(int(item.get("minutes", 0)) for item in data.get("process", []))
    if minutes != 45:
        errors.append(f"total minutes is {minutes}, expected 45")
    if not data.get("objectives") or not data.get("key_points") or not data.get("difficulties"):
        errors.append("missing first-page teaching fields")
    if data.get("reflection") != {"mode": "blank", "text": ""}:
        errors.append("reflection is not blank")
    body = process_text(data)
    if lesson_id not in APPROVED:
        if len(stages) != 8:
            errors.append(f"process stage count is {len(stages)}, expected 8")
        functional_groups = (
            ("导入", "复习", "依据", "情境", "问题", "任务", "观察", "诊断"),
            ("错误", "错解", "易错", "辨析", "纠错", "修正"),
            ("检测", "评价"),
            ("总结", "回顾", "作业"),
        )
        for group in functional_groups:
            if not any(any(token in stage for token in group) for stage in stages):
                errors.append(f"missing functional stage: {'/'.join(group)}")
        if "例题" not in body or "练习" not in body:
            errors.append("concrete example or exercise marker missing")
        if "10 分" not in body or "参考答案" not in body or "达标标准" not in body:
            errors.append("feedback test details missing")
        if not all(token in body for token in ("A 组", "B 组", "C 组")):
            errors.append("layered homework missing")
    if "如图" in body and not any(item.get("figure") for item in data["process"]):
        errors.append("text says 如图 but no figure is configured")
    for token in PLACEHOLDERS:
        if token in body or token in tex:
            errors.append(f"placeholder text found: {token}")
    for token in ("•", "●", "· "):
        if token in body or token in tex:
            errors.append(f"bullet character found: {token.strip()}")
    for name, pattern in FORBIDDEN_TEX.items():
        if pattern.search(tex):
            errors.append(f"forbidden TeX structure found: {name}")

    pages, a4_portrait = pdf_geometry(pdf_path)
    if pages != 4:
        errors.append(f"PDF has {pages} pages, expected 4")
    if not a4_portrait:
        errors.append("PDF is not A4 portrait")
    pngs = sorted(png_dir.glob("*.png"))
    if len(pngs) != pages:
        errors.append(f"PNG count is {len(pngs)}, expected {pages}")
    for png in pngs:
        with Image.open(png) as image:
            gray = image.convert("L")
            dark_ratio = sum(1 for value in gray.resize((124, 175)).getdata() if value < 245) / (124 * 175)
            if dark_ratio < 0.01:
                errors.append(f"possible blank page: {png.name}")

    if lesson_id not in APPROVED:
        log = ROOT / "build" / "lessonplans_final" / lesson_id / "lessonplan.compile.log"
        if not log.exists():
            errors.append("compile log missing")
        else:
            log_text = log.read_text(encoding="utf-8", errors="replace")
            checks = {
                "LaTeX Error": r"LaTeX Error",
                "Undefined control sequence": r"Undefined control sequence",
                "Fatal error": r"Fatal error|Emergency stop",
                "Overfull hbox": r"Overfull \\hbox",
            }
            for label, pattern in checks.items():
                count = len(re.findall(pattern, log_text, re.IGNORECASE))
                if count:
                    errors.append(f"{label}={count}")

    if lesson_id in APPROVED and sha256(pdf_path) != APPROVED_PDF_HASHES[lesson_id]:
        errors.append("approved PDF SHA-256 changed")
    return {
        "lesson_id": lesson_id,
        "status": "passed" if not errors else "failed",
        "pages": pages,
        "minutes": minutes,
        "errors": errors,
        "warnings": warnings,
    }


def main() -> int:
    manifest_path = OUTPUT / "manifests" / "lessonplan_manifest.json"
    rows = json.loads(manifest_path.read_text(encoding="utf-8"))
    global_errors: list[str] = []
    ids = [row["lesson_id"] for row in rows]
    if len(rows) != 53:
        global_errors.append(f"manifest rows={len(rows)}, expected 53")
    if len(ids) != len(set(ids)):
        global_errors.append("duplicate lesson IDs in manifest")
    for relative, expected in FROZEN_HASHES.items():
        actual = sha256(ROOT / relative)
        if actual != expected:
            global_errors.append(f"frozen file changed: {relative}")

    results = [validate_row(row) for row in rows]
    status_counts = Counter(item["status"] for item in results)
    batch_sheets = sorted((OUTPUT / "contact_sheets" / "batches").glob("batch-*.png"))
    if len(batch_sheets) != 6:
        global_errors.append(f"batch contact sheets={len(batch_sheets)}, expected 6")
    passed = not global_errors and status_counts["failed"] == 0
    payload = {
        "status": "passed" if passed else "failed",
        "lesson_count": len(rows),
        "status_counts": dict(status_counts),
        "global_errors": global_errors,
        "results": results,
    }
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Phase 7 自动验收报告",
        "",
        f"- 总体状态：`{payload['status']}`",
        f"- manifest 课时数：{len(rows)}",
        f"- 通过：{status_counts['passed']}",
        f"- 失败：{status_counts['failed']}",
        f"- 批次 contact sheet：{len(batch_sheets)}",
        "- 检查范围：冻结哈希、文件完整性、A4 纵向四页、45 分钟、结构化内容、反馈测试、分层作业、空白反思、禁用排版结构、编译日志、逐页 PNG。",
        "",
        "## 全局错误",
        "",
    ]
    lines.extend([f"- {item}" for item in global_errors] or ["- 无。"])
    lines.extend(["", "## 逐课结果", "", "| 课时 ID | 状态 | 页数 | 分钟 | 错误 |", "|---|---:|---:|---:|---|"])
    for item in results:
        lines.append(
            f"| {item['lesson_id']} | {item['status']} | {item.get('pages', '')} | "
            f"{item.get('minutes', '')} | {'；'.join(item['errors']) or '无'} |"
        )
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"status={payload['status']} lessons={len(rows)} passed={status_counts['passed']} failed={status_counts['failed']}")
    for error in global_errors:
        print(f"[GLOBAL] {error}")
    for item in results:
        for error in item["errors"]:
            print(f"[{item['lesson_id']}] {error}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
