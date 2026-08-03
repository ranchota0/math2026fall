"""Generate editable Word resources for all Grade 7B lessons except the gold sample."""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

from generate_7b_word import build_teaching_design, build_worksheet


ROOT = Path(__file__).resolve().parents[1]


def grade7b_sources() -> list[Path]:
    result: list[Path] = []
    for path in (ROOT / "lessons").rglob("lesson.yml"):
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        lesson_id = str((data.get("meta") or {}).get("lesson_id", ""))
        if lesson_id.startswith(("C07-", "C08-", "C09-", "C10-", "C11-", "C12-")):
            result.append(path)
    return sorted(result, key=lambda p: yaml.safe_load(p.read_text(encoding="utf-8"))["meta"]["lesson_id"])


def main() -> int:
    generated = 0
    skipped = 0
    for source in grade7b_sources():
        data = yaml.safe_load(source.read_text(encoding="utf-8"))
        if data["meta"]["lesson_id"] == "C07-L01":
            skipped += 1
            continue
        lesson_root = source.parents[1]
        prefix = data["meta"]["file_prefix"]
        teaching = lesson_root / "教学设计" / f"{prefix}_教学设计.docx"
        student = lesson_root / "学案" / f"{prefix}_学生学案.docx"
        teacher = lesson_root / "学案" / f"{prefix}_学案教师版.docx"
        existing = [path for path in (teaching, student, teacher) if path.exists()]
        if existing:
            raise FileExistsError(f"Refusing to overwrite existing Word files: {existing}")
        build_teaching_design(data, teaching)
        build_worksheet(data, student, teacher=False)
        build_worksheet(data, teacher, teacher=True)
        generated += 3
        print(f"[WORD] {data['meta']['lesson_id']} {prefix}")
    print(f"[OK] generated_docx={generated} skipped_gold_lessons={skipped}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
