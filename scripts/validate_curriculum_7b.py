"""Validate the Grade 7B authoritative curriculum manifest."""

from __future__ import annotations

from collections import Counter
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "config" / "curriculum_manifest_7b.yml"
REQUIRED = {
    "id",
    "chapter_id",
    "lesson_index_in_chapter",
    "source_section",
    "lesson_title",
    "lesson_type",
    "source_pages",
    "core_knowledge",
    "prerequisites",
    "key_points",
    "difficulties",
    "examples",
    "exercises",
    "homework_scope",
    "needs_figure",
    "suitable_for_inquiry",
}


def main() -> int:
    data = yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))
    lessons = data["lessons"]
    errors: list[str] = []
    if len(lessons) != data["metadata"]["total_lessons"]:
        errors.append("metadata.total_lessons mismatch")
    ids = [row["id"] for row in lessons]
    if len(ids) != len(set(ids)):
        errors.append("duplicate lesson id")
    all_pages = [page for row in lessons for page in row["source_pages"]]
    missing_pages = [page for page in range(1, 193) if page not in all_pages]
    duplicate_pages = sorted(page for page, count in Counter(all_pages).items() if count > 1)
    if missing_pages:
        errors.append(f"missing printed pages: {missing_pages}")
    if duplicate_pages:
        errors.append(f"duplicate printed pages: {duplicate_pages}")
    chapter_counts = Counter(row["chapter_id"] for row in lessons)
    for chapter in data["chapters"]:
        actual = chapter_counts[chapter["chapter_id"]]
        if actual != chapter["proposed_periods"]:
            errors.append(
                f"{chapter['chapter_id']} proposed_periods={chapter['proposed_periods']} actual={actual}"
            )
    by_chapter: dict[str, list[dict]] = {}
    for row in lessons:
        missing = sorted(REQUIRED - set(row))
        if missing:
            errors.append(f"{row.get('id', '?')} missing fields {missing}")
        expected = f"{row['chapter_id']}-L{row['lesson_index_in_chapter']:02d}"
        if row["id"] != expected:
            errors.append(f"{row['id']} expected {expected}")
        by_chapter.setdefault(row["chapter_id"], []).append(row)
    for chapter_id, rows in by_chapter.items():
        indexes = [row["lesson_index_in_chapter"] for row in rows]
        expected = list(range(1, len(rows) + 1))
        if indexes != expected:
            errors.append(f"{chapter_id} non-contiguous indexes: {indexes}")
    if errors:
        print("[FAIL] Grade 7B curriculum manifest")
        for error in errors:
            print(f"- {error}")
        return 1
    print(
        f"[OK] lessons={len(lessons)} chapters={len(data['chapters'])} "
        f"printed_pages=1-192 page_coverage=100%"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
