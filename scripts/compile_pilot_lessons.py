from __future__ import annotations

import csv
import json
import re
import shutil
import subprocess
import time
from datetime import datetime
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
PILOT_IDS = ["C01-L03", "C05-L05", "C06-L07"]
LOG_DIR = ROOT / "logs" / "pilot"
BUILD_DIR = ROOT / "build" / "pilot"
REPORT = ROOT / "reports" / "pilot_build_report.csv"
RESULTS_JSON = LOG_DIR / "pilot_compile_results.json"


def load_yaml(path: Path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def parse_log(text: str) -> dict:
    warnings = len(re.findall(r"(?:LaTeX|Package [^ ]+) Warning", text))
    overfull = len(re.findall(r"Overfull \\\\hbox", text))
    pages = 0
    match = re.search(r"Output written on .+? \((\d+) pages?", text)
    if match:
        pages = int(match.group(1))
    error_message = ""
    for line in text.splitlines():
        if line.startswith("!") or "Fatal error" in line or "Emergency stop" in line:
            error_message = line.strip()
            break
    return {
        "warnings": warnings,
        "overfull_boxes": overfull,
        "pdf_pages": pages,
        "error_message": error_message,
    }


def run_command(command: list[str], cwd: Path, log_path: Path) -> tuple[int, str, float]:
    start = time.perf_counter()
    completed = subprocess.run(
        command,
        cwd=str(cwd),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        encoding="utf-8",
        errors="replace",
    )
    seconds = time.perf_counter() - start
    log_path.write_text(completed.stdout, encoding="utf-8")
    return completed.returncode, completed.stdout, seconds


def compile_tex(tex_path: Path, lesson_id: str, role: str, latexmk: str | None, xelatex: str | None) -> dict:
    out_dir = BUILD_DIR / lesson_id / role
    out_dir.mkdir(parents=True, exist_ok=True)
    log_path = LOG_DIR / f"{lesson_id}_{role}.compile.log"

    if latexmk:
        command = [
            latexmk,
            "-xelatex",
            "-interaction=nonstopmode",
            "-halt-on-error",
            "-file-line-error",
            f"-outdir={out_dir}",
            str(tex_path),
        ]
        code, output, seconds = run_command(command, ROOT, log_path)
    else:
        output_parts = []
        seconds = 0.0
        code = 0
        for _ in range(2):
            command = [
                xelatex or "xelatex",
                "-interaction=nonstopmode",
                "-halt-on-error",
                "-file-line-error",
                f"-output-directory={out_dir}",
                str(tex_path),
            ]
            run_code, output, run_seconds = run_command(command, ROOT, log_path)
            output_parts.append(output)
            seconds += run_seconds
            code = run_code
            if run_code != 0:
                break
        output = "\n".join(output_parts)
        log_path.write_text(output, encoding="utf-8")

    tex_log = out_dir / f"{tex_path.stem}.log"
    log_text = tex_log.read_text(encoding="utf-8", errors="replace") if tex_log.exists() else output
    parsed = parse_log(log_text)
    status = "success" if code == 0 else "failed"
    source_pdf = out_dir / f"{tex_path.stem}.pdf"
    dist_pdf = ROOT / "dist" / lesson_id / f"{role}.pdf"
    dist_pdf.parent.mkdir(parents=True, exist_ok=True)
    if status == "success" and source_pdf.exists():
        shutil.copy2(source_pdf, dist_pdf)
    if status == "success" and parsed["pdf_pages"] == 0 and dist_pdf.exists():
        parsed["pdf_pages"] = 1

    return {
        "lesson_id": lesson_id,
        "role": role,
        "tex": tex_path.relative_to(ROOT).as_posix(),
        "pdf": dist_pdf.relative_to(ROOT).as_posix() if dist_pdf.exists() else "",
        "status": status,
        "compile_seconds": round(seconds, 3),
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        **parsed,
    }


def main() -> int:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    REPORT.parent.mkdir(parents=True, exist_ok=True)

    latexmk = shutil.which("latexmk")
    xelatex = shutil.which("xelatex")

    rows = []
    if not xelatex:
        for lesson_id in PILOT_IDS:
            meta = load_yaml(ROOT / "lessons" / lesson_id / "lesson.yml")
            rows.append(
                {
                    "lesson_id": lesson_id,
                    "chapter": meta.get("chapter", ""),
                    "lesson_title": meta.get("lesson_title", ""),
                    "lesson_type": meta.get("lesson_type", ""),
                    "teacher_tex": f"lessons/{lesson_id}/teacher.tex",
                    "student_tex": f"lessons/{lesson_id}/student.tex",
                    "teacher_pdf": "",
                    "student_pdf": "",
                    "teacher_pages": 0,
                    "student_pages": 0,
                    "compile_status": "skipped_environment_missing",
                    "warning_count": 0,
                    "overfull_hbox_count": 0,
                    "manual_review_status": "pending",
                }
            )
        write_reports(rows, [])
        return 0

    raw_results = []
    for lesson_id in PILOT_IDS:
        lesson_dir = ROOT / "lessons" / lesson_id
        meta = load_yaml(lesson_dir / "lesson.yml")
        teacher = compile_tex(lesson_dir / "teacher.tex", lesson_id, "teacher", latexmk, xelatex)
        student = compile_tex(lesson_dir / "student.tex", lesson_id, "student", latexmk, xelatex)
        raw_results.extend([teacher, student])

        compile_status = "success" if teacher["status"] == "success" and student["status"] == "success" else "failed"
        rows.append(
            {
                "lesson_id": lesson_id,
                "chapter": meta.get("chapter", ""),
                "lesson_title": meta.get("lesson_title", ""),
                "lesson_type": meta.get("lesson_type", ""),
                "teacher_tex": teacher["tex"],
                "student_tex": student["tex"],
                "teacher_pdf": teacher["pdf"],
                "student_pdf": student["pdf"],
                "teacher_pages": teacher["pdf_pages"],
                "student_pages": student["pdf_pages"],
                "compile_status": compile_status,
                "warning_count": teacher["warnings"] + student["warnings"],
                "overfull_hbox_count": teacher["overfull_boxes"] + student["overfull_boxes"],
                "manual_review_status": "pending",
            }
        )
        print(
            f"[{compile_status.upper()}] {lesson_id} "
            f"teacher_pages={teacher['pdf_pages']} student_pages={student['pdf_pages']} "
            f"warnings={teacher['warnings'] + student['warnings']} "
            f"overfull={teacher['overfull_boxes'] + student['overfull_boxes']}"
        )

    write_reports(rows, raw_results)
    return 1 if any(row["compile_status"] != "success" for row in rows) else 0


def write_reports(rows: list[dict], raw_results: list[dict]) -> None:
    fields = [
        "lesson_id",
        "chapter",
        "lesson_title",
        "lesson_type",
        "teacher_tex",
        "student_tex",
        "teacher_pdf",
        "student_pdf",
        "teacher_pages",
        "student_pages",
        "compile_status",
        "warning_count",
        "overfull_hbox_count",
        "manual_review_status",
    ]
    with REPORT.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    RESULTS_JSON.write_text(json.dumps(raw_results, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
