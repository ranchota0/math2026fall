from __future__ import annotations

import re
import sys
from pathlib import Path

import jsonschema
import yaml
from jinja2 import Environment, FileSystemLoader, StrictUndefined


ROOT = Path(__file__).resolve().parents[1]

CORE_DIRS = [
    "references",
    "config",
    "templates",
    "common",
    "lessons",
    "lessons/_sample",
    "assets/images",
    "assets/tikz",
    "scripts",
    "tests",
    "dist/tex",
    "dist/pdf",
    "build",
    "logs",
    "reports",
]

CORE_FILES = [
    "AGENTS.md",
    "README.md",
    ".gitignore",
    "requirements.txt",
    "references/README.md",
    "references/source_info.md",
    "config/project.yml",
    "config/curriculum_manifest.yml",
    "config/curriculum_manifest.schema.yml",
    "templates/teacher_template.tex.j2",
    "templates/student_template.tex.j2",
    "common/preamble.tex",
    "common/commands.tex",
    "common/tikz_library.tex",
    "lessons/README.md",
    "lessons/_sample/metadata.yml",
    "lessons/_sample/teacher_content.tex",
    "lessons/_sample/student_content.tex",
    "scripts/check_environment.py",
    "scripts/validate_project.py",
    "scripts/render_lesson.py",
    "scripts/compile_all.py",
    "scripts/generate_report.py",
    "tests/smoke_teacher.tex",
    "tests/smoke_student.tex",
    "reports/review_checklist.md",
]

REQUIRED_TEMPLATE_TOKENS = [
    "lesson.lesson_title",
    "lesson.period_minutes",
    "preamble_path",
    "commands_path",
    "tikz_library_path",
    "content_path",
]

ALLOWED_LESSON_TYPES = {
    "new_lesson",
    "practice_lesson",
    "activity_lesson",
    "review_lesson",
    "integrated_practice",
    "optional_extension",
}

FORBIDDEN_CURRENT_STATUSES = {"generated", "compiled", "reviewed", "approved"}
INVALID_FILENAME_CHARS = set('\\/:*?"<>|')
PILOT_LESSON_IDS = {"C01-L03", "C05-L05", "C06-L07"}


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def load_yaml(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def has_invalid_filename(value: str) -> bool:
    return any(char in INVALID_FILENAME_CHARS for char in value)


def validate_manifest_business_rules(manifest: dict, errors: list[str]) -> None:
    metadata = manifest.get("metadata") or {}
    chapters = manifest.get("chapters") or []
    lessons = manifest.get("lessons") or []

    if metadata.get("total_chapters") != len(chapters):
        errors.append(
            f"metadata.total_chapters={metadata.get('total_chapters')} does not match chapters count={len(chapters)}"
        )
    if metadata.get("total_lessons") != len(lessons):
        errors.append(
            f"metadata.total_lessons={metadata.get('total_lessons')} does not match lessons count={len(lessons)}"
        )

    lesson_ids = [lesson.get("id") for lesson in lessons]
    duplicate_ids = sorted({lesson_id for lesson_id in lesson_ids if lesson_ids.count(lesson_id) > 1})
    for lesson_id in duplicate_ids:
        errors.append(f"duplicate lesson id: {lesson_id}")

    outputs = []
    for lesson in lessons:
        for key in ["teacher_output", "student_output"]:
            value = lesson.get(key, "")
            if not value:
                errors.append(f"{lesson.get('id')} missing {key}")
                continue
            if has_invalid_filename(value):
                errors.append(f"{lesson.get('id')} {key} contains invalid filename character: {value}")
            if not value.endswith(".tex"):
                errors.append(f"{lesson.get('id')} {key} must end with .tex")
            outputs.append(value)
    duplicate_outputs = sorted({output for output in outputs if outputs.count(output) > 1})
    for output in duplicate_outputs:
        errors.append(f"duplicate output filename: {output}")

    expected_chapter_ids = [f"C{index:02d}" for index in range(1, len(chapters) + 1)]
    actual_chapter_ids = [chapter.get("chapter_id") for chapter in chapters]
    if actual_chapter_ids != expected_chapter_ids:
        errors.append(f"chapter ids must be continuous: expected {expected_chapter_ids}, got {actual_chapter_ids}")

    chapter_map = {chapter.get("chapter_id"): chapter for chapter in chapters}
    for chapter in chapters:
        chapter_id = chapter.get("chapter_id")
        chapter_lessons = [lesson for lesson in lessons if lesson.get("chapter_id") == chapter_id]
        indexes = [lesson.get("lesson_index_in_chapter") for lesson in chapter_lessons]
        expected_indexes = list(range(1, len(chapter_lessons) + 1))
        if indexes != expected_indexes:
            errors.append(f"{chapter_id} lesson indexes must be continuous: expected {expected_indexes}, got {indexes}")
        if chapter.get("proposed_periods") != len(chapter_lessons):
            errors.append(
                f"{chapter_id} proposed_periods={chapter.get('proposed_periods')} does not match lesson count={len(chapter_lessons)}"
            )

    for lesson in lessons:
        lesson_id = lesson.get("id", "")
        chapter_id = lesson.get("chapter_id")

        if lesson.get("sample") is True or lesson_id.startswith("SAMPLE"):
            errors.append(f"sample lesson must not appear in formal lessons list: {lesson_id}")

        if chapter_id not in chapter_map:
            errors.append(f"{lesson_id} references unknown chapter_id: {chapter_id}")
        else:
            expected_title = chapter_map[chapter_id].get("chapter_title")
            if lesson.get("chapter_title") != expected_title:
                errors.append(f"{lesson_id} chapter_title does not match {chapter_id}")

        expected_id = f"{chapter_id}-L{lesson.get('lesson_index_in_chapter', 0):02d}"
        if lesson_id != expected_id:
            errors.append(f"{lesson_id} does not match chapter/index pattern, expected {expected_id}")

        if not lesson.get("source_pages"):
            errors.append(f"{lesson_id} source_pages must not be empty")
        if not 35 <= int(lesson.get("period_minutes", 0)) <= 60:
            errors.append(f"{lesson_id} period_minutes should be between 35 and 60")
        if not lesson.get("key_points"):
            errors.append(f"{lesson_id} key_points must not be empty")
        if not lesson.get("difficulties"):
            errors.append(f"{lesson_id} difficulties must not be empty")
        if "prerequisites" not in lesson:
            errors.append(f"{lesson_id} prerequisites field must exist")
        if lesson.get("lesson_type") not in ALLOWED_LESSON_TYPES:
            errors.append(f"{lesson_id} lesson_type is not allowed: {lesson.get('lesson_type')}")
        if lesson.get("status") in FORBIDDEN_CURRENT_STATUSES:
            errors.append(f"{lesson_id} status must not be {lesson.get('status')} before content generation")

    formal_lesson_files = [
        path
        for path in (ROOT / "lessons").rglob("*")
        if path.is_file()
        and "_sample" not in path.parts
        and path.suffix.lower() in {".tex", ".pdf"}
        and not (
            len(path.parts) >= 2
            and path.parent.name in PILOT_LESSON_IDS
            and path.name in {"teacher.tex", "student.tex"}
        )
        and not (
            len(path.parts) >= 3
            and path.parent.name == "assets"
            and path.parent.parent.name in PILOT_LESSON_IDS
            and path.suffix.lower() == ".tex"
        )
    ]
    for path in formal_lesson_files:
        errors.append(f"formal course file found under lessons/: {rel(path)}")

    dist_course_files = [
        path
        for path in (ROOT / "dist").rglob("*")
        if path.is_file() and path.suffix.lower() in {".tex", ".pdf"}
        and not (
            path.suffix.lower() == ".pdf"
            and path.parent.name in PILOT_LESSON_IDS
            and path.name in {"teacher.pdf", "student.pdf"}
        )
    ]
    for path in dist_course_files:
        errors.append(f"formal course file found under dist/: {rel(path)}")


def main() -> int:
    errors: list[str] = []

    for directory in CORE_DIRS:
        if not (ROOT / directory).is_dir():
            errors.append(f"missing directory: {directory}")

    for filename in CORE_FILES:
        if not (ROOT / filename).is_file():
            errors.append(f"missing file: {filename}")

    try:
        project = load_yaml(ROOT / "config/project.yml")
        manifest = load_yaml(ROOT / "config/curriculum_manifest.yml")
        schema = load_yaml(ROOT / "config/curriculum_manifest.schema.yml")
        jsonschema.validate(instance=manifest, schema=schema)
        print("[OK] YAML parsed and manifest matches schema")
    except Exception as exc:
        errors.append(f"YAML/schema validation failed: {exc}")
        project = {}
        manifest = {}

    for template_name in ["teacher_template.tex.j2", "student_template.tex.j2"]:
        template_path = ROOT / "templates" / template_name
        if template_path.exists():
            text = template_path.read_text(encoding="utf-8")
            for token in REQUIRED_TEMPLATE_TOKENS:
                if token not in text:
                    errors.append(f"template token missing in {template_name}: {token}")

    try:
        env = Environment(
            loader=FileSystemLoader(str(ROOT / "templates")),
            undefined=StrictUndefined,
            autoescape=False,
        )
        lesson = {
            "id": "SAMPLE-L01",
            "lesson_title": "示例课时",
            "chapter_title": "示例章节",
            "source_section": "示例小节",
            "period_minutes": 45,
        }
        for template_name in ["teacher_template.tex.j2", "student_template.tex.j2"]:
            env.get_template(template_name).render(
                lesson=lesson,
                preamble_path="common/preamble.tex",
                commands_path="common/commands.tex",
                tikz_library_path="common/tikz_library.tex",
                content_path="lessons/_sample/teacher_content.tex",
                project=project,
            )
        print("[OK] Jinja templates render with required variables")
    except Exception as exc:
        errors.append(f"template render check failed: {exc}")

    sample_metadata = ROOT / "lessons/_sample/metadata.yml"
    if sample_metadata.exists():
        sample = load_yaml(sample_metadata)
        if sample.get("sample") is not True or sample.get("not_for_teaching") is not True:
            errors.append("lessons/_sample/metadata.yml must be marked sample and not_for_teaching")
        if sample.get("status") != "sample_only":
            errors.append("lessons/_sample/metadata.yml status must be sample_only")

    dist_sample_files = list((ROOT / "dist").rglob("*SAMPLE*")) + list((ROOT / "dist").rglob("*sample*"))
    if dist_sample_files:
        for path in dist_sample_files:
            errors.append(f"sample file found in dist: {rel(path)}")
    else:
        print("[OK] no sample files found in dist")

    if manifest:
        validate_manifest_business_rules(manifest, errors)

    if errors:
        print("[FAIL] project validation failed")
        for error in errors:
            print(f"  - {error}")
        return 1

    print("[OK] project validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
