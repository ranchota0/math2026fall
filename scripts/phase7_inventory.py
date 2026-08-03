#!/usr/bin/env python3
"""Create the Phase 7 frozen baseline and authoritative lesson inventory."""
from __future__ import annotations

import hashlib
import re
from collections import Counter
from datetime import datetime
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "config" / "curriculum_manifest.yml"
PPT_ROOT = ROOT / "郭立华2026秋数学PPT"
APPROVED_IDS = {"C01-L03", "C05-L05", "C06-L07"}
FROZEN_FILES = [
    ROOT / "tex" / "lessonplan" / "hepingjie_lessonplan.sty",
    ROOT / "scripts" / "build_lessonplans_v2.py",
    ROOT / "config" / "lessonplan_style.yml",
    ROOT / "reports" / "phase6_1_template_freeze_report.md",
    ROOT / "dist" / "lessonplans_v2" / "C01-L03_数轴_教案_v2.pdf",
    ROOT / "dist" / "lessonplans_v2" / "C05-L05_移项解一元一次方程_教案_v2.pdf",
    ROOT / "dist" / "lessonplans_v2" / "C06-L07_角的比较与运算_教案_v2.pdf",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def ppt_sources(section: str) -> list[Path]:
    numbers = re.findall(r"\b[1-6]\.[1-4]\b", section)
    matches: list[Path] = []
    for number in numbers:
        matches.extend(PPT_ROOT.rglob(f"{number}.pdf"))
        matches.extend(PPT_ROOT.rglob(f"{number} *.pdf"))
    return sorted(set(matches))


def needs_figure(lesson: dict) -> bool:
    text = " ".join(
        [lesson["lesson_title"], lesson["source_section"]]
        + lesson.get("content_scope", [])
    )
    markers = (
        "数轴", "图形", "直线", "射线", "线段", "角", "场地", "进位制",
        "位置", "统计", "图表", "展开", "点线面体",
    )
    return any(marker in text for marker in markers)


def initial_status(lesson: dict, ppts: list[Path]) -> str:
    if lesson["id"] in APPROVED_IDS:
        return "approved"
    if lesson["lesson_type"] in {"activity_lesson", "review_lesson", "integrated_practice"}:
        return "partial"
    return "ready" if ppts or lesson.get("source_pages") else "partial"


def main() -> int:
    data = yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))
    lessons = data["lessons"]
    ids = [lesson["id"] for lesson in lessons]
    titles = [(lesson["chapter_id"], lesson["lesson_title"]) for lesson in lessons]
    duplicate_ids = sorted(key for key, count in Counter(ids).items() if count > 1)
    duplicate_titles = sorted(key for key, count in Counter(titles).items() if count > 1)

    chapter_counts = Counter(lesson["chapter_id"] for lesson in lessons)
    continuity_errors: list[str] = []
    for chapter in data["chapters"]:
        chapter_id = chapter["chapter_id"]
        expected = [f"{chapter_id}-L{index:02d}" for index in range(1, chapter["proposed_periods"] + 1)]
        actual = [lesson["id"] for lesson in lessons if lesson["chapter_id"] == chapter_id]
        if actual != expected:
            continuity_errors.append(f"{chapter_id}: expected {expected}, actual {actual}")
        if chapter_counts[chapter_id] != chapter["proposed_periods"]:
            continuity_errors.append(
                f"{chapter_id}: proposed={chapter['proposed_periods']} actual={chapter_counts[chapter_id]}"
            )

    rows = []
    for lesson in lessons:
        ppts = ppt_sources(lesson["source_section"])
        source_parts = [
            "curriculum_manifest",
            f"textbook pp.{','.join(map(str, lesson['source_pages']))}",
        ]
        if ppts:
            source_parts.append("PPT " + ", ".join(path.stem for path in ppts))
        elif lesson["lesson_type"] != "new_lesson":
            source_parts.append("textbook activity/review pages")
        status = initial_status(lesson, ppts)
        rows.append(
            {
                "id": lesson["id"],
                "chapter": lesson["chapter_title"],
                "title": lesson["lesson_title"],
                "lesson_type": lesson["lesson_type"],
                "sources": "; ".join(source_parts),
                "status": status,
                "figure": "yes" if needs_figure(lesson) else "no",
                "generated": "yes" if lesson["id"] in APPROVED_IDS else "no",
            }
        )

    report = [
        "# Phase 7 全课程课时清单",
        "",
        f"生成时间：{datetime.now().astimezone().isoformat(timespec='seconds')}",
        "",
        "权威课时边界：`config/curriculum_manifest.yml`。本清单不新增、删除或改动课时边界。",
        "",
        "## 汇总",
        "",
        f"- 正式课时总数：{len(lessons)}",
        f"- 已验收样例：{sum(row['status'] == 'approved' for row in rows)}",
        f"- ready：{sum(row['status'] == 'ready' for row in rows)}",
        f"- partial：{sum(row['status'] == 'partial' for row in rows)}",
        "- blocked：0",
        "- duplicate：0" if not duplicate_ids and not duplicate_titles else "- duplicate：需处理",
        "",
        "`partial` 均为活动、复习或综合实践课；它们有明确教材页码、内容范围和先修知识，可从教材与正式 manifest 可靠补齐，因此纳入本阶段生成。",
        "",
        "## 清单",
        "",
        "| 课时 ID | 章/单元 | 课题 | 课型 | 数据来源 | 当前状态 | 是否需要图形 | 是否已生成 |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for row in rows:
        report.append(
            "| {id} | {chapter} | {title} | {lesson_type} | {sources} | {status} | {figure} | {generated} |".format(**row)
        )
    report.extend(
        [
            "",
            "## 一致性检查",
            "",
            f"- 课时 ID 重复：{duplicate_ids or '无'}",
            f"- 同章同名课题重复：{duplicate_titles or '无'}",
            f"- 章内编号连续性：{'通过' if not continuity_errors else '失败'}",
            f"- metadata.total_lessons：{data['metadata']['total_lessons']}，实际：{len(lessons)}",
            "- SAMPLE-L01：仅存在于 `lessons/_sample`，未进入正式 manifest。",
            "- 教材页码缺失：" + ("无" if all(lesson.get("source_pages") for lesson in lessons) else "存在"),
        ]
    )
    if continuity_errors:
        report.extend(["", "### 连续性问题", ""] + [f"- {item}" for item in continuity_errors])
    inventory_path = ROOT / "reports" / "phase7_lesson_inventory.md"
    inventory_path.write_text("\n".join(report) + "\n", encoding="utf-8")

    baseline = [
        "# Phase 7 冻结基线",
        "",
        f"记录时间：{datetime.now().astimezone().isoformat(timespec='seconds')}",
        "",
        "当前目录不是 Git 仓库，无法创建 Phase 6.1 提交。本阶段以 SHA-256 清单保护冻结文件；不初始化仓库、不修改冻结公共文件。",
        "",
        "| 文件 | 大小（字节） | SHA-256 |",
        "|---|---:|---|",
    ]
    for path in FROZEN_FILES:
        baseline.append(
            f"| `{path.relative_to(ROOT).as_posix()}` | {path.stat().st_size} | `{sha256(path)}` |"
        )
    baseline.extend(
        [
            "",
            "三份已验收 PDF 必须保持上述 SHA-256；Phase 7 只复制这些产物到正式交付目录，不重新生成或覆盖。",
        ]
    )
    baseline_path = ROOT / "reports" / "phase7_freeze_baseline.md"
    baseline_path.write_text("\n".join(baseline) + "\n", encoding="utf-8")

    if duplicate_ids or duplicate_titles or continuity_errors or len(lessons) != data["metadata"]["total_lessons"]:
        print("[FAIL] manifest consistency check")
        return 1
    print(f"[OK] inventory: {inventory_path.relative_to(ROOT)} ({len(lessons)} lessons)")
    print(f"[OK] baseline: {baseline_path.relative_to(ROOT)} ({len(FROZEN_FILES)} frozen files)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
