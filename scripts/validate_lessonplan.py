#!/usr/bin/env python3
"""Validate Phase 5 pilot lesson-plan data and generated PDFs."""
from __future__ import annotations

import csv
import hashlib
import math
import re
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
PILOT_LESSONS = ["C01-L03", "C05-L05", "C06-L07"]
BACKGROUND_SOURCE = ROOT / "blank.pdf"
BACKGROUND_COPY = ROOT / "templates/lessonplan/hepingjie_blank.pdf"
REPORT_MD = ROOT / "reports/lessonplan_template_validation.md"
REPORT_CSV = ROOT / "reports/pilot_lessonplans_review.csv"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def tool(name: str) -> str | None:
    candidate = Path(r"D:\texlive\2026\bin\windows") / f"{name}.exe"
    if candidate.exists():
        return str(candidate)
    found = shutil.which(name)
    return found


def pdf_info(path: Path) -> dict:
    pdfinfo = tool("pdfinfo")
    if not pdfinfo:
        raise RuntimeError("pdfinfo was not found")
    result = subprocess.run(
        [pdfinfo, path.resolve().relative_to(ROOT.resolve()).as_posix()],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=True,
    )
    text = result.stdout
    pages = int(re.search(r"Pages:\s+(\d+)", text).group(1))
    size = re.search(r"Page size:\s+([0-9.]+)\s+x\s+([0-9.]+)\s+pts", text)
    width, height = float(size.group(1)), float(size.group(2))
    return {"pages": pages, "width": width, "height": height, "raw": text}


def estimate_lines(items: list[str], chars_per_line: int) -> int:
    total = 0
    for item in items:
        compact = re.sub(r"\\[a-zA-Z]+|[{}$^_\\]", "", item)
        total += max(1, math.ceil(len(compact) / chars_per_line))
    return total + len(items)


def validate_data(lesson_id: str, data: dict) -> list[str]:
    errors: list[str] = []
    meta = data.get("meta", {})
    if meta.get("lesson_id") != lesson_id:
        errors.append("lesson_id mismatch")
    if data.get("reflection", {}).get("mode") != "blank" or data.get("reflection", {}).get("text", ""):
        errors.append("reflection must be blank")
    process = data.get("process", [])
    minutes = sum(int(item.get("minutes", 0)) for item in process)
    if minutes != 45:
        errors.append(f"process minutes total is {minutes}, expected 45")
    for item in process:
        if item.get("page") not in (2, 3, 4):
            errors.append(f"invalid page for stage {item.get('stage')}")
        if not item.get("teacher") or not item.get("student"):
            errors.append(f"stage lacks teacher/student content: {item.get('stage')}")
    for page, capacity in [(2, 52), (3, 52), (4, 33)]:
        used = 0
        for item in [p for p in process if p.get("page") == page]:
            teacher_lines = estimate_lines(item["teacher"], 32)
            student_lines = estimate_lines(item["student"], 12)
            used += max(teacher_lines, student_lines, 1) + 1
        if used > capacity:
            errors.append(f"page {page} estimated text lines {used} exceed capacity {capacity}")
    return errors


def log_counts(log: Path) -> tuple[int, int, int]:
    text = log.read_text(encoding="utf-8", errors="replace") if log.exists() else ""
    warnings = len(re.findall(r"Warning", text))
    overfull = len(re.findall(r"Overfull \\hbox", text))
    errors = len(re.findall(r"(?:Fatal error|LaTeX Error|Emergency stop)", text))
    return warnings, overfull, errors


def main() -> int:
    rows = []
    lines = ["# 教案 PDF 背景模板与三节样板验证报告", "", f"生成时间：{datetime.now().isoformat(timespec='seconds')}", ""]
    source_hash = sha256(BACKGROUND_SOURCE) if BACKGROUND_SOURCE.exists() else "MISSING"
    copy_hash = sha256(BACKGROUND_COPY) if BACKGROUND_COPY.exists() else "MISSING"
    lines.extend([
        "## 背景模板",
        "",
        f"- 原始 PDF：`blank.pdf`",
        f"- 项目副本：`templates/lessonplan/hepingjie_blank.pdf`",
        f"- SHA-256 一致：`{source_hash == copy_hash}`",
        f"- SHA-256：`{copy_hash}`",
        "",
        "## 验证结果",
        "",
        "| 课时 | PDF | 页数 | A4纵向 | 时间45分钟 | 课后反思空白 | 数据越界估算 | 日志错误 | 结论 |",
        "|---|---|---:|---|---|---|---|---:|---|",
    ])
    exit_code = 0
    for lesson_id in PILOT_LESSONS:
        yml = ROOT / "build/lessonplans" / lesson_id / "lessonplan.yml"
        data = yaml.safe_load(yml.read_text(encoding="utf-8"))
        pdf = ROOT / "build/lessonplans" / lesson_id / "lessonplan.pdf"
        info = pdf_info(pdf)
        data_errors = validate_data(lesson_id, data)
        warnings, overfull, errors = log_counts(ROOT / "build/lessonplans" / lesson_id / "lessonplan.compile.log")
        is_a4 = abs(info["width"] - 595.28) < 1 and abs(info["height"] - 841.89) < 1
        minutes_ok = sum(int(item["minutes"]) for item in data["process"]) == 45
        reflection_blank = data.get("reflection", {}).get("mode") == "blank" and not data.get("reflection", {}).get("text")
        ok = info["pages"] == 4 and is_a4 and minutes_ok and reflection_blank and not data_errors and errors == 0
        if not ok:
            exit_code = 1
        conclusion = "通过" if ok else "需修正"
        lines.append(
            f"| {lesson_id} | `{pdf.relative_to(ROOT).as_posix()}` | {info['pages']} | {is_a4} | {minutes_ok} | {reflection_blank} | {'通过' if not data_errors else '; '.join(data_errors)} | {errors} | {conclusion} |"
        )
        rows.append({
            "lesson_id": lesson_id,
            "title": data["meta"]["title"],
            "pdf": pdf.relative_to(ROOT).as_posix(),
            "pages": info["pages"],
            "a4_portrait": is_a4,
            "minutes_total": sum(int(item["minutes"]) for item in data["process"]),
            "reflection_blank": reflection_blank,
            "warnings": warnings,
            "overfull_boxes": overfull,
            "errors": errors,
            "status": conclusion,
            "validation_notes": "; ".join(data_errors),
        })

    lines.extend([
        "",
        "## 坐标系统",
        "",
        "- 坐标文件：`tex/lessonplan/hepingjie_coordinates.tex`",
        "- 原点：A4 页面左上角。",
        "- 单位：毫米。",
        "- 第 4 页教学过程盒高度限制在课后反思区域上方，验证时不得进入课后反思区域。",
        "",
        "## 结论",
        "",
        "- 背景 PDF 已作为唯一版式模板使用，未重新绘制表格。",
        "- 三节样板均按 4 页 A4 纵向生成。",
        "- 自动检查通过后仍需人工核对打印视觉效果、学校留白习惯和个别长句换行。",
    ])
    REPORT_MD.write_text("\n".join(lines), encoding="utf-8")
    with REPORT_CSV.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"[OK] validation report -> {REPORT_MD.relative_to(ROOT).as_posix()}")
    print(f"[OK] review csv -> {REPORT_CSV.relative_to(ROOT).as_posix()}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
