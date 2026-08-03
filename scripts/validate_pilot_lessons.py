from __future__ import annotations

import csv
import re
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
PILOT_IDS = ["C01-L03", "C05-L05", "C06-L07"]
REQUIRED_META_FIELDS = [
    "lesson_id",
    "chapter",
    "section",
    "lesson_title",
    "lesson_type",
    "textbook_page_start",
    "textbook_page_end",
    "prerequisite",
    "learning_objectives",
    "teacher_output",
    "student_output",
]
ANSWER_LEAK_PATTERNS = [
    r"参考答案",
    r"答案[:：]",
    r"解[:：]",
    r"所以\s*[A-Za-z0-9\\]+=",
]


def load_yaml(path: Path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def formal_manifest_lessons() -> dict:
    manifest = load_yaml(ROOT / "config" / "curriculum_manifest.yml")
    return {lesson["id"]: lesson for lesson in manifest["lessons"]}


def extract_ids(tex: str, command: str) -> list[str]:
    return re.findall(r"\\" + command + r"\{([^}]+)\}", tex)


def flow_minutes(tex: str) -> int:
    pattern = r"\\flowrow\{[^{}]*\}\{[^{}]*\}\{[^{}]*\}\{[^{}]*\}\{(\d+)\}"
    return sum(int(value) for value in re.findall(pattern, tex, flags=re.S))


def validate_lesson(lesson_id: str, manifest_lesson: dict, errors: list[str]) -> None:
    lesson_dir = ROOT / "lessons" / lesson_id
    meta_path = lesson_dir / "lesson.yml"
    teacher_path = lesson_dir / "teacher.tex"
    student_path = lesson_dir / "student.tex"

    if not meta_path.exists():
        errors.append(f"{lesson_id}: missing lesson.yml")
        return
    if not teacher_path.exists():
        errors.append(f"{lesson_id}: missing teacher.tex")
    if not student_path.exists():
        errors.append(f"{lesson_id}: missing student.tex")

    meta = load_yaml(meta_path)
    for field in REQUIRED_META_FIELDS:
        if field not in meta:
            errors.append(f"{lesson_id}: lesson.yml missing {field}")

    if meta.get("lesson_id") != lesson_id:
        errors.append(f"{lesson_id}: lesson.yml lesson_id mismatch")
    if meta.get("lesson_title") != manifest_lesson.get("lesson_title"):
        errors.append(f"{lesson_id}: lesson title differs from manifest")
    if meta.get("lesson_type") != manifest_lesson.get("lesson_type"):
        errors.append(f"{lesson_id}: lesson_type differs from manifest")
    if meta.get("textbook_page_start") != min(manifest_lesson.get("source_pages", [])):
        errors.append(f"{lesson_id}: textbook_page_start differs from manifest")
    if meta.get("textbook_page_end") != max(manifest_lesson.get("source_pages", [])):
        errors.append(f"{lesson_id}: textbook_page_end differs from manifest")

    if teacher_path.exists() and student_path.exists():
        teacher = teacher_path.read_text(encoding="utf-8")
        student = student_path.read_text(encoding="utf-8")
        student_ids = extract_ids(student, "qitem")
        answer_ids = extract_ids(teacher, "answer")
        if student_ids != answer_ids:
            errors.append(f"{lesson_id}: student question ids do not match teacher answer ids")
        for pattern in ANSWER_LEAK_PATTERNS:
            if re.search(pattern, student):
                errors.append(f"{lesson_id}: possible answer leak in student.tex: {pattern}")
        minutes = flow_minutes(teacher)
        expected_minutes = int(meta.get("period_minutes", manifest_lesson.get("period_minutes", 0)))
        if minutes != expected_minutes:
            errors.append(f"{lesson_id}: teaching flow minutes={minutes} does not match period")

        input_paths = re.findall(r"\\input\{([^}]+)\}", teacher + "\n" + student)
        for input_path in input_paths:
            path = ROOT / input_path
            if not path.exists():
                errors.append(f"{lesson_id}: missing input asset {input_path}")


def validate_dist(errors: list[str]) -> None:
    allowed = {ROOT / "dist" / lesson_id / name for lesson_id in PILOT_IDS for name in ["teacher.pdf", "student.pdf"]}
    for path in (ROOT / "dist").rglob("*.pdf"):
        if path not in allowed:
            errors.append(f"unexpected PDF in dist: {path.relative_to(ROOT).as_posix()}")


def validate_build_report(errors: list[str]) -> None:
    report = ROOT / "reports" / "pilot_build_report.csv"
    if not report.exists():
        errors.append("missing reports/pilot_build_report.csv")
        return
    with report.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != len(PILOT_IDS):
        errors.append(f"pilot_build_report row count should be {len(PILOT_IDS)}, got {len(rows)}")
    for row in rows:
        if row.get("lesson_id") not in PILOT_IDS:
            errors.append(f"unexpected lesson in pilot_build_report: {row.get('lesson_id')}")
        if row.get("compile_status") != "success":
            errors.append(f"{row.get('lesson_id')}: compile_status is {row.get('compile_status')}")
        if int(row.get("warning_count") or 0) != 0:
            errors.append(f"{row.get('lesson_id')}: warning_count is not 0")
        if int(row.get("overfull_hbox_count") or 0) != 0:
            errors.append(f"{row.get('lesson_id')}: overfull_hbox_count is not 0")


def main() -> int:
    errors: list[str] = []
    manifest = formal_manifest_lessons()
    for lesson_id in PILOT_IDS:
        if lesson_id not in manifest:
            errors.append(f"{lesson_id}: not found in formal manifest")
            continue
        validate_lesson(lesson_id, manifest[lesson_id], errors)
    validate_dist(errors)
    validate_build_report(errors)

    if errors:
        print("[FAIL] pilot lesson validation failed")
        for error in errors:
            print(f"  - {error}")
        return 1
    print("[OK] pilot lesson validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
