"""Generate Grade 7B lesson-list reports and workbook-ready audit data."""

from __future__ import annotations

import csv
import json
import re
from collections import Counter
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "config" / "curriculum_manifest_7b.yml"
TEXTBOOK = ROOT / "build" / "7b_audit" / "textbook" / "textbook_pages.json"
MD_OUT = ROOT / "reports" / "人教版七年级下册课时清单.md"
CSV_OUT = ROOT / "reports" / "人教版七年级下册课时清单.csv"
JSON_OUT = ROOT / "build" / "7b_artifacts" / "curriculum_workbook_data.json"

COLUMN_NAMES = [
    "观察与猜想",
    "探究与发现",
    "阅读与思考",
    "信息技术应用",
    "图说数学史",
    "数学活动",
    "小结",
    "综合与实践",
]


def join(values: list[object]) -> str:
    return "；".join(str(value) for value in values)


def lesson_rows(data: dict) -> list[dict]:
    chapters = {row["chapter_id"]: row for row in data["chapters"]}
    rows = []
    for lesson in data["lessons"]:
        chapter = chapters[lesson["chapter_id"]]
        pages = lesson["source_pages"]
        rows.append(
            {
                "课时编号": lesson["id"],
                "章": f"第{chapter['chapter_number']}章 {chapter['chapter_title']}",
                "节/小节": lesson["source_section"],
                "课题名称": lesson["lesson_title"],
                "课型": lesson["lesson_type"],
                "教材印刷页": f"{min(pages)}—{max(pages)}" if len(pages) > 1 else str(pages[0]),
                "PDF物理页": f"{min(pages)+7}—{max(pages)+7}" if len(pages) > 1 else str(pages[0] + 7),
                "建议课时数": 1,
                "课时分钟": data["metadata"]["period_minutes"],
                "核心知识": join(lesson["core_knowledge"]),
                "前置知识": join(lesson["prerequisites"]),
                "教学重点": join(lesson["key_points"]),
                "教学难点": join(lesson["difficulties"]),
                "对应例题/栏目": join(lesson["examples"]),
                "对应练习": join(lesson["exercises"]),
                "对应作业范围": join(lesson["homework_scope"]),
                "需图形/图表": "是" if lesson["needs_figure"] else "否",
                "适合探究": "是" if lesson["suitable_for_inquiry"] else "否",
            }
        )
    return rows


def clean_line(line: str) -> str:
    return " ".join(line.split()).strip()


def content_items(text: str) -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for raw in text.splitlines():
        line = clean_line(raw)
        if not line or "仅供个人学习使用" in line:
            continue
        item: tuple[str, str] | None = None
        section = re.match(r"^(\d+\.\d+(?:\.\d+)?)\s+(.+)", line)
        example = re.search(r"例\s*(\d*)\s+(.+)", line)
        exercise = re.match(r"^(练习|习题\s*\d*|复习题\s*\d*)", line)
        if section:
            item = ("节/小节", f"{section.group(1)} {section.group(2)[:100]}")
        elif example:
            number = example.group(1) or "（无编号）"
            item = ("例题", f"例{number} {example.group(2)[:100]}")
        elif exercise:
            item = ("练习/习题", line[:110])
        else:
            for name in COLUMN_NAMES:
                if name in line:
                    item = ("教材栏目", line[:110])
                    break
        if item and item not in seen:
            seen.add(item)
            rows.append(item)
    return rows


def coverage_rows(manifest: dict, textbook: dict) -> list[dict]:
    page_to_lesson: dict[int, dict] = {}
    for lesson in manifest["lessons"]:
        for page in lesson["source_pages"]:
            page_to_lesson[page] = lesson
    chapter_names = {row["chapter_id"]: row["chapter_title"] for row in manifest["chapters"]}
    output = []
    for page in textbook["pages"]:
        printed = page["printed_page"]
        if printed is None or not 1 <= printed <= 192:
            continue
        lesson = page_to_lesson[printed]
        items = content_items(page["text"])
        if not items:
            items = [("正文/题目", "本页全部正文、图表与题目")]
        else:
            items.insert(0, ("整页覆盖", "本页全部正文、图表与题目"))
        for kind, label in items:
            output.append(
                {
                    "教材印刷页": printed,
                    "PDF物理页": page["physical_page"],
                    "内容类型": kind,
                    "教材内容/标记": label,
                    "课时编号": lesson["id"],
                    "章": chapter_names[lesson["chapter_id"]],
                    "节/小节": lesson["source_section"],
                    "课题名称": lesson["lesson_title"],
                    "安排状态": "已安排",
                    "复核说明": "以当前教材PDF为准；后续逐课引用时复核题号、图号与数据",
                }
            )
    return output


def write_md(manifest: dict, rows: list[dict]) -> None:
    chapter_counts = Counter(row["chapter_id"] for row in manifest["lessons"])
    lines = [
        "# 人教版七年级下册课时清单",
        "",
        f"教材：{manifest['metadata']['textbook']}（{manifest['metadata']['publisher']}）  ",
        f"权威来源：`{manifest['metadata']['source_pdf']}`  ",
        f"课时总数：{len(rows)}；每课时 {manifest['metadata']['period_minutes']} 分钟。  ",
        "教材印刷页 1 对应 PDF 物理页 8，页码偏移为 +7。",
        "",
        "## 章节统计",
        "",
        "| 章 | 教材页码 | 课时数 |",
        "|---|---:|---:|",
    ]
    for chapter in manifest["chapters"]:
        start, end = chapter["printed_pages"]
        lines.append(
            f"| 第{chapter['chapter_number']}章 {chapter['chapter_title']} | {start}—{end} | {chapter_counts[chapter['chapter_id']]} |"
        )
    lines.extend(
        [
            "",
            "## 全册课时表",
            "",
            "| 编号 | 章 | 节/小节 | 课题 | 页码 | 课型 | 核心知识 | 重点 | 难点 | 图形/图表 | 探究 |",
            "|---|---|---|---|---:|---|---|---|---|:---:|:---:|",
        ]
    )
    for row in rows:
        lines.append(
            f"| {row['课时编号']} | {row['章']} | {row['节/小节']} | {row['课题名称']} | {row['教材印刷页']} | "
            f"{row['课型']} | {row['核心知识']} | {row['教学重点']} | {row['教学难点']} | {row['需图形/图表']} | {row['适合探究']} |"
        )
    lines.extend(["", "## 逐课详细信息", ""])
    for row in rows:
        lines.extend(
            [
                f"### {row['课时编号']} {row['课题名称']}",
                "",
                f"- 章节：{row['章']} / {row['节/小节']}",
                f"- 教材页码：印刷页 {row['教材印刷页']}；PDF物理页 {row['PDF物理页']}",
                f"- 建议课时：{row['建议课时数']} 课时（{row['课时分钟']} 分钟）",
                f"- 核心知识：{row['核心知识']}",
                f"- 前置知识：{row['前置知识']}",
                f"- 教学重点：{row['教学重点']}",
                f"- 教学难点：{row['教学难点']}",
                f"- 对应例题/栏目：{row['对应例题/栏目']}",
                f"- 对应练习：{row['对应练习']}",
                f"- 对应作业范围：{row['对应作业范围']}",
                f"- 图形或统计图表：{row['需图形/图表']}；适合探究活动：{row['适合探究']}",
                "",
            ]
        )
    MD_OUT.write_text("\n".join(lines), encoding="utf-8")


def write_csv(rows: list[dict]) -> None:
    with CSV_OUT.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    manifest = yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))
    textbook = json.loads(TEXTBOOK.read_text(encoding="utf-8"))
    rows = lesson_rows(manifest)
    coverage = coverage_rows(manifest, textbook)
    write_md(manifest, rows)
    write_csv(rows)
    chapter_stats = []
    for chapter in manifest["chapters"]:
        chapter_lessons = [row for row in manifest["lessons"] if row["chapter_id"] == chapter["chapter_id"]]
        chapter_stats.append(
            {
                "章编号": chapter["chapter_id"],
                "章": f"第{chapter['chapter_number']}章 {chapter['chapter_title']}",
                "教材页码": f"{chapter['printed_pages'][0]}—{chapter['printed_pages'][1]}",
                "课时数": len(chapter_lessons),
                "需图形/图表课时": sum(bool(row["needs_figure"]) for row in chapter_lessons),
                "探究课时": sum(bool(row["suitable_for_inquiry"]) for row in chapter_lessons),
                "活动/复习/综合课": sum(row["lesson_type"] != "new_lesson" for row in chapter_lessons),
            }
        )
    JSON_OUT.parent.mkdir(parents=True, exist_ok=True)
    JSON_OUT.write_text(
        json.dumps(
            {
                "metadata": manifest["metadata"],
                "lesson_rows": rows,
                "coverage_rows": coverage,
                "chapter_stats": chapter_stats,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"[OK] lessons={len(rows)} coverage_rows={len(coverage)} md={MD_OUT.name} csv={CSV_OUT.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
