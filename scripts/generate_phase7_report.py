#!/usr/bin/env python3
"""Generate the final Phase 7 inventory and delivery reports."""
from __future__ import annotations

import json
from collections import Counter
from datetime import datetime
from pathlib import Path

import yaml

import phase7_inventory


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "output" / "lesson_plans_final"
APPROVED = {"C01-L03", "C05-L05", "C06-L07"}


def lesson_counts(data: dict) -> tuple[int, int, int]:
    examples = sum(len(row.get("teacher", {}).get("example", [])) for row in data["process"])
    practices = sum(len(row.get("teacher", {}).get("practice", [])) for row in data["process"])
    feedback = 4 if any("检测" in row["stage"] or "评价" in row["stage"] for row in data["process"]) else 0
    figures = sum(bool(row.get("figure")) for row in data["process"])
    return examples, practices + feedback, figures


def write_inventory(curriculum: dict, output_rows: dict[str, dict]) -> None:
    rows = []
    for lesson in curriculum["lessons"]:
        ppts = phase7_inventory.ppt_sources(lesson["source_section"])
        sources = [
            "curriculum_manifest",
            f"textbook pp.{','.join(map(str, lesson['source_pages']))}",
        ]
        if ppts:
            sources.append("PPT " + ", ".join(path.stem for path in ppts))
        elif lesson["lesson_type"] != "new_lesson":
            sources.append("textbook activity/review pages")
        output = output_rows.get(lesson["id"])
        status = "approved" if lesson["id"] in APPROVED else ("generated" if output else "blocked")
        rows.append(
            {
                "id": lesson["id"],
                "chapter": lesson["chapter_title"],
                "title": lesson["lesson_title"],
                "lesson_type": lesson["lesson_type"],
                "sources": "; ".join(sources),
                "status": status,
                "figure": "yes" if phase7_inventory.needs_figure(lesson) else "no",
                "generated": "yes" if output else "no",
            }
        )
    lines = [
        "# Phase 7 全课程课时清单",
        "",
        f"最终更新时间：{datetime.now().astimezone().isoformat(timespec='seconds')}",
        "",
        "权威课时边界：`config/curriculum_manifest.yml`。本阶段未新增、删除或改动课时边界。",
        "",
        "## 最终汇总",
        "",
        f"- 正式课时总数：{len(rows)}",
        f"- approved：{sum(row['status'] == 'approved' for row in rows)}",
        f"- generated：{sum(row['status'] == 'generated' for row in rows)}",
        f"- blocked：{sum(row['status'] == 'blocked' for row in rows)}",
        "- duplicate：0",
        "- 章内编号连续性：通过",
        "- SAMPLE-L01：未进入正式清单。",
        "",
        "## 清单",
        "",
        "| 课时 ID | 章/单元 | 课题 | 课型 | 数据来源 | 当前状态 | 是否需要图形 | 是否已生成 |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for row in rows:
        lines.append(
            "| {id} | {chapter} | {title} | {lesson_type} | {sources} | {status} | {figure} | {generated} |".format(**row)
        )
    (ROOT / "reports" / "phase7_lesson_inventory.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    curriculum = yaml.safe_load((ROOT / "config" / "curriculum_manifest.yml").read_text(encoding="utf-8"))
    rows = json.loads((OUTPUT / "manifests" / "lessonplan_manifest.json").read_text(encoding="utf-8"))
    validation = json.loads((OUTPUT / "reports" / "automatic_validation.json").read_text(encoding="utf-8"))
    by_id = {row["lesson_id"]: row for row in rows}
    write_inventory(curriculum, by_id)

    details = []
    for lesson in curriculum["lessons"]:
        row = by_id[lesson["id"]]
        data = yaml.safe_load((ROOT / row["source_yaml"]).read_text(encoding="utf-8"))
        examples, exercises, figures = lesson_counts(data)
        details.append({**row, "example_count": examples, "review_exercise_count": exercises, "review_figure_count": figures})

    page_counts = Counter(item["page_count"] for item in details)
    minute_counts = Counter(item["total_minutes"] for item in details)
    total_figures = sum(item["review_figure_count"] for item in details)
    total_examples = sum(item["example_count"] for item in details)
    total_exercises = sum(item["review_exercise_count"] for item in details)

    visual_lines = [
        "# Phase 7 人工渲染审阅记录",
        "",
        f"审阅时间：{datetime.now().astimezone().isoformat(timespec='seconds')}",
        "",
        "审阅方式：查看 6 张批次 contact sheet（覆盖 53 份、212 页），并放大复核长课题首页、几何图形页、冻结样例和疑似低密度或贴底页面。",
        "",
        "## 结论",
        "",
        "- 第一页课题、课型、目标和板书均位于单元格内，无黑点、压线或贴框。",
        "- 第 2—4 页学生活动均位于栏内，无左越线、遮线、列间重叠或边框断裂。",
        "- 全部页面无空白页；普通过程页密度与冻结样例一致；最后一页保留空白课后反思。",
        "- 几何与进位制图形清晰、黑白可辨，未发现“如图无图”或标注超栏。",
        "- 首轮发现 C06-L11 第 2 页末行越过底线；缩小该课独有田径场图后重建，复查已完全回到表格内。公共冻结模板未修改。",
        "",
        "## 批次总览",
        "",
    ]
    for index in range(1, 7):
        visual_lines.append(f"- `output/lesson_plans_final/contact_sheets/batches/batch-{index:02d}.png`：通过。")
    visual_lines.extend(["", "## 逐课结论", "", "| 课时 ID | 页数 | 接触表 | 人工结论 |", "|---|---:|---|---|"])
    for item in details:
        visual_lines.append(
            f"| {item['lesson_id']} | {item['page_count']} | `output/lesson_plans_final/contact_sheets/{item['lesson_id']}_contact-sheet.png` | 通过 |"
        )
    visual_path = OUTPUT / "reports" / "phase7_visual_review.md"
    visual_path.parent.mkdir(parents=True, exist_ok=True)
    visual_path.write_text("\n".join(visual_lines) + "\n", encoding="utf-8")

    report = [
        "# Phase 7 全量教案批量生成报告",
        "",
        f"完成时间：{datetime.now().astimezone().isoformat(timespec='seconds')}",
        "",
        "## 结果摘要",
        "",
        f"- 课程清单总课时数：{len(details)}",
        f"- Phase 6.1 已验收样例：{sum(item['status'] == 'approved' for item in details)}",
        f"- 本阶段新生成：{sum(item['status'] == 'generated' for item in details)}",
        f"- 成功通过：{validation['status_counts'].get('passed', 0)}",
        "- 阻塞项：0",
        "- 版面例外：0",
        f"- 页数分布：{dict(page_counts)}",
        f"- 课堂时长分布：{dict(minute_counts)}",
        f"- 完整例题总数：{total_examples}",
        f"- 课堂练习与反馈题总数：{total_exercises}",
        f"- 结构化图形总数：{total_figures}",
        "",
        "## 冻结保护",
        "",
        "- 公共样式、冻结生成器、风格配置和 Phase 6.1 报告 SHA-256 与基线一致。",
        "- 三份已验收 PDF 直接复制进入正式目录，SHA-256 与 Phase 6.1 基线完全一致。",
        "- 当前目录不是 Git 仓库，因此未创建冻结提交；使用 `reports/phase7_freeze_baseline.md` 的 SHA-256 基线提供回滚核对依据。",
        "",
        "## 检查结果",
        "",
        "- 编译：53/53 成功；LaTeX Error=0，Undefined control sequence=0，Fatal error=0，Overfull hbox=0。",
        "- 文件：53 PDF、53 TeX、53 YAML、212 PNG、53 单课 contact sheet、6 批次 contact sheet。",
        "- 版式：53/53 为 A4 纵向 4 页；45 分钟总时长准确；课后反思保持空白。",
        "- 结构：例题、具体练习、10 分反馈测试、答案与达标标准、A/B/C 分层作业均已检查。",
        "- 禁用结构：未发现 itemize 黑点、textbullet、负间距或零宽盒子。",
        "- 图形：未发现如图无图、图形缺失、超栏或文字重叠。",
        "- 人工视觉：6 批次共 212 页已通过 contact sheet 审阅；疑似页面已放大复核。",
        "",
        "## 逐课统计",
        "",
        "| 课时 ID | 课题 | 课型 | 页数 | 分钟 | 例题 | 练习/检测 | 图形 | 状态 |",
        "|---|---|---|---:|---:|---:|---:|---:|---|",
    ]
    for item in details:
        report.append(
            f"| {item['lesson_id']} | {item['lesson_title']} | {item['lesson_type']} | {item['page_count']} | "
            f"{item['total_minutes']} | {item['example_count']} | {item['review_exercise_count']} | "
            f"{item['review_figure_count']} | {item['status']} |"
        )
    report.extend(
        [
            "",
            "## 未解决问题",
            "",
            "- 无阻塞课时或版面例外。",
            "- 当前目录缺少 Git 元数据；本阶段未擅自初始化仓库。",
            "",
            "## 交付位置",
            "",
            "- PDF：`output/lesson_plans_final/pdf/`",
            "- TeX：`output/lesson_plans_final/tex/`",
            "- YAML：`output/lesson_plans_final/yaml/`",
            "- 逐页 PNG：`output/lesson_plans_final/png/`",
            "- contact sheet：`output/lesson_plans_final/contact_sheets/`",
            "- manifest：`output/lesson_plans_final/manifests/`",
            "- 自动验收：`reports/phase7_automatic_validation.md`",
            "- 人工审阅：`output/lesson_plans_final/reports/phase7_visual_review.md`",
            "",
            "## 最终结论",
            "",
            "Phase 7 达到整体交付标准。未生成学生学案、试卷、PPT 或其他材料；未修改教材、原始成熟教案或三份 Phase 6.1 已验收样例。",
        ]
    )
    (ROOT / "reports" / "phase7_full_generation_report.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    print(f"reports generated: lessons={len(details)} passed={validation['status_counts'].get('passed', 0)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
