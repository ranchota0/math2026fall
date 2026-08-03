#!/usr/bin/env python3
"""Validate Phase 6 pilot outputs and write the v1/v2 comparison CSV."""
from __future__ import annotations

import csv
import hashlib
import re
import shutil
import subprocess
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
PILOT_IDS = ["C01-L03", "C05-L05", "C06-L07"]
BACKGROUND_SOURCE = ROOT / "blank.pdf"
BACKGROUND_COPY = ROOT / "templates" / "lessonplan" / "hepingjie_blank.pdf"
STYLE_CONFIG = ROOT / "config" / "lessonplan_style.yml"
REPORT_CSV = ROOT / "reports" / "pilot_lessonplan_v1_v2_comparison.csv"


def tool(name: str) -> str | None:
    texlive = Path(r"D:\texlive\2026\bin\windows") / f"{name}.exe"
    return str(texlive) if texlive.exists() else shutil.which(name)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def pdf_info(path: Path) -> tuple[int, bool]:
    pdfinfo = tool("pdfinfo")
    if not pdfinfo:
        raise RuntimeError("pdfinfo 不可用")
    result = subprocess.run(
        [pdfinfo, path.relative_to(ROOT).as_posix()],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=True,
    )
    pages_match = re.search(r"Pages:\s+(\d+)", result.stdout)
    size_match = re.search(r"Page size:\s+([0-9.]+)\s+x\s+([0-9.]+)\s+pts", result.stdout)
    pages = int(pages_match.group(1)) if pages_match else 0
    width = float(size_match.group(1)) if size_match else 0.0
    height = float(size_match.group(2)) if size_match else 0.0
    a4_portrait = abs(width - 595.28) < 1.0 and abs(height - 841.89) < 1.0
    return pages, a4_portrait


def count_items(process: list[dict], parent: str, child: str) -> int:
    return sum(len(stage.get(parent, {}).get(child, [])) for stage in process)


def log_counts(path: Path) -> tuple[int, int, int]:
    text = path.read_text(encoding="utf-8", errors="replace")
    warnings = len(re.findall(r"Warning", text))
    overfull = len(re.findall(r"Overfull \\hbox", text))
    errors = len(re.findall(r"(?:LaTeX Error|Fatal error|Emergency stop|Undefined control sequence)", text))
    return warnings, overfull, errors


def main() -> int:
    style = yaml.safe_load(STYLE_CONFIG.read_text(encoding="utf-8"))
    expected_pages = int(style["page_count"])
    expected_minutes = int(style["lesson_duration"])
    background_match = sha256(BACKGROUND_SOURCE) == sha256(BACKGROUND_COPY)
    rows = []
    failed = not background_match

    for lesson_id in PILOT_IDS:
        v1_dir = ROOT / "build" / "lessonplans" / lesson_id
        v2_dir = ROOT / "build" / "lessonplans_v2" / lesson_id
        v1 = yaml.safe_load((v1_dir / "lessonplan.yml").read_text(encoding="utf-8"))
        v2 = yaml.safe_load((v2_dir / "lessonplan.yml").read_text(encoding="utf-8"))
        v1_pages, v1_a4 = pdf_info(v1_dir / "lessonplan.pdf")
        v2_pages, v2_a4 = pdf_info(v2_dir / "lessonplan.pdf")
        warnings, overfull, errors = log_counts(v2_dir / "lessonplan.compile.log")
        v2_process = v2["process"]
        v2_minutes = sum(int(stage["minutes"]) for stage in v2_process)
        png_count = len(list(v2_dir.glob("page-*.png")))
        reflection_blank = v2["reflection"]["mode"] == "blank" and not v2["reflection"]["text"]
        dist_pdf = (
            ROOT
            / "dist"
            / "lessonplans_v2"
            / f"{lesson_id}_{v2['meta']['title']}_教案_v2.pdf"
        )
        status_ok = (
            background_match
            and v2_pages == expected_pages
            and v2_a4
            and v2_minutes == expected_minutes
            and png_count == expected_pages
            and reflection_blank
            and errors == 0
            and overfull == 0
            and dist_pdf.exists()
        )
        failed = failed or not status_ok
        rows.append(
            {
                "lesson_id": lesson_id,
                "title": v2["meta"]["title"],
                "v1_pages": v1_pages,
                "v2_pages": v2_pages,
                "v1_a4_portrait": v1_a4,
                "v2_a4_portrait": v2_a4,
                "v1_stages": len(v1["process"]),
                "v2_stages": len(v2_process),
                "v2_teacher_questions": count_items(v2_process, "teacher", "questions"),
                "v2_student_actions": count_items(v2_process, "student", "actions"),
                "v2_expected_responses": count_items(v2_process, "student", "expected_response"),
                "v2_design_intents": sum(len(stage["design_intent"]) for stage in v2_process),
                "v2_minutes": v2_minutes,
                "v2_png_pages": png_count,
                "reflection_blank": reflection_blank,
                "compile_warnings": warnings,
                "overfull_boxes": overfull,
                "compile_errors": errors,
                "background_sha256_match": background_match,
                "status": "通过" if status_ok else "需修正",
            }
        )
        print(
            f"[{'OK' if status_ok else 'FAIL'}] {lesson_id} "
            f"v1={v1_pages}p v2={v2_pages}p minutes={v2_minutes} png={png_count} "
            f"warnings={warnings} overfull={overfull} errors={errors}"
        )

    REPORT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with REPORT_CSV.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"[OK] comparison csv -> {REPORT_CSV.relative_to(ROOT)}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
