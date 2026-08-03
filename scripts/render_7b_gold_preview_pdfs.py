"""Create temporary searchable PDF previews for visual QA of gold-template DOCX files.

These PDFs live only under build/ and are not final deliverables.  Final lesson
PDFs must still be exported from Word after the DOCX passes this preview gate.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import yaml
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import Paragraph, Table, TableStyle

from apply_7b_gold_lessonplan_template import chapter_periods, lesson_sources, teacher_pairs
from render_c07_l01_adjusted_pdf import BODY, BODY_SMALL, CENTER, LABEL, esc, para, register_fonts, rich


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "build" / "7b_gold_template_migration" / "preview_pdf"


def draw_page_one(canvas: Canvas, data: dict) -> None:
    width, height = A4
    meta = data["meta"]
    canvas.setFont("SimHei", 18)
    canvas.drawCentredString(width / 2, height - 2.45 * cm, "北京市和平街第一中学课时教学设计")
    canvas.setFont("FangSong", 10.5)
    canvas.drawCentredString(width / 2, height - 4.15 * cm, "授课时间　　　　年　　月　　日　　　　　　　　　　　　第　1　页")

    rows = [["" for _ in range(9)] for _ in range(8)]
    rows[0][0] = para("课题", style=CENTER)
    rows[0][3] = para(f"{meta['section']} {meta['title']}")
    rows[0][6] = para("课型", style=CENTER)
    rows[0][7] = para(meta["lesson_type"])
    rows[1][0] = para("章（单元）总课时", style=CENTER)
    rows[1][3] = para(str(chapter_periods()[meta["lesson_id"].split("-")[0]]), style=CENTER)
    rows[1][4] = para("本课题课时", style=CENTER)
    rows[1][5] = para("1", style=CENTER)
    rows[1][6] = para("本节课是第　1　课时", style=CENTER)

    labels = ["教\n学\n目\n标", "教学\n重点", "教学\n难点", "教学\n方法", "教学\n手段", "板\n书\n设\n计"]
    contents = [
        [f"{index + 1}. {value}" for index, value in enumerate(data["objectives"])],
        [data["key_point"]],
        [data["difficulty"]],
        ["；".join(data["methods"]) + "。"],
        [
            "教师：" + "、".join(data["preparation"]["teacher"]) + "；学生：" + "、".join(data["preparation"]["student"]) + "。",
            f"教材：{meta['textbook']}，印刷页{meta['printed_pages']}（PDF {meta['pdf_pages']}）。",
        ],
        list(data["blackboard"]),
    ]
    for row, (label, lines) in enumerate(zip(labels, contents), start=2):
        rows[row][0] = para(label, style=LABEL)
        body_style = BODY_SMALL if row in (2, 7) else BODY
        markup = "<br/>".join(
            (f'<font name="SimHei">{esc(line)}</font>' if row == 7 and index == 0 else esc(line))
            for index, line in enumerate(lines)
        )
        rows[row][2] = Paragraph(markup, body_style)

    col_widths = [1.52, 0.60, 0.90, 4.35, 3.54, 1.68, 1.54, 2.47, 1.40]
    row_heights = [0.95, 0.95, 4.2, 1.55, 1.55, 1.55, 2.05, 8.65]
    table = Table(rows, colWidths=[value * cm for value in col_widths], rowHeights=[value * cm for value in row_heights])
    spans = [
        ("SPAN", (0, 0), (2, 0)), ("SPAN", (3, 0), (5, 0)), ("SPAN", (7, 0), (8, 0)),
        ("SPAN", (0, 1), (2, 1)), ("SPAN", (6, 1), (8, 1)),
    ]
    for row in range(2, 8):
        spans.extend([("SPAN", (0, row), (1, row)), ("SPAN", (2, row), (8, row))])
    table.setStyle(TableStyle([
        *spans,
        ("GRID", (0, 0), (-1, -1), 0.65, colors.black),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("VALIGN", (2, 2), (8, 7), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4), ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    tw, th = table.wrapOn(canvas, 18 * cm, 22 * cm)
    table.drawOn(canvas, (width - tw) / 2, height - 4.75 * cm - th)


def draw_process_page(canvas: Canvas, data: dict, stages: list[dict], page_index: int) -> None:
    width, height = A4
    final_page = page_index == 3
    rows_count = 1 + len(stages) + (1 if final_page else 0)
    rows = [["" for _ in range(4)] for _ in range(rows_count)]
    rows[0] = [para("", style=CENTER), para("教师教学活动设计", style=CENTER), para("学生活动", style=CENTER), para("估时", style=CENTER)]
    offsets = [0, 3, 6]
    heights = [[10.20, 6.40, 9.50], [7.80, 7.80, 9.75], [7.35, 8.35]][page_index - 1]
    chinese_nums = ["一", "二", "三", "四", "五", "六", "七", "八"]
    for row_index, stage in enumerate(stages, start=1):
        global_index = offsets[page_index - 1] + row_index - 1
        font_size = 8.0 if page_index == 1 and row_index == 1 else 9.0
        rows[row_index][0] = para("教\n学\n过\n程", style=LABEL) if row_index == 1 else ""
        rows[row_index][1] = rich(
            f"（{chinese_nums[global_index]}）{stage['stage']}",
            teacher_pairs(stage, first_stage=(global_index == 0), data=data),
            size=font_size,
        )
        student_items = [("活动", value) for value in stage.get("student", [])] + [("预期", stage["expected"])]
        rows[row_index][2] = rich("", student_items, size=max(font_size, 8.7))
        rows[row_index][3] = para(f"{stage['minutes']}分钟", style=CENTER)
    if final_page:
        rows[-1][0] = para("课\n后\n反\n思", style=LABEL)

    row_heights = [0.75, *heights]
    if final_page:
        row_heights.append(9.10)
    table = Table(rows, colWidths=[1.50 * cm, 11.20 * cm, 3.50 * cm, 1.80 * cm], rowHeights=[value * cm for value in row_heights])
    commands = [
        ("BOX", (0, 0), (-1, -1), 0.65, colors.black),
        ("LINEBELOW", (0, 0), (-1, 0), 0.65, colors.black),
        ("LINEAFTER", (0, 0), (0, -1), 0.65, colors.black),
        ("LINEAFTER", (1, 0), (1, -1), 0.65, colors.black),
        ("LINEAFTER", (2, 0), (2, -1), 0.65, colors.black),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("VALIGN", (1, 1), (2, len(stages)), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4), ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("SPAN", (0, 1), (0, len(stages))),
    ]
    if final_page:
        commands.extend([
            ("SPAN", (1, rows_count - 1), (3, rows_count - 1)),
            ("LINEABOVE", (0, rows_count - 1), (3, rows_count - 1), 0.65, colors.black),
        ])
    table.setStyle(TableStyle(commands))
    tw, th = table.wrapOn(canvas, 18 * cm, 27 * cm)
    table.drawOn(canvas, (width - tw) / 2, height - 1.15 * cm - th)


def render_one(data: dict) -> Path:
    lesson_id = data["meta"]["lesson_id"]
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"{lesson_id}.pdf"
    canvas = Canvas(str(path), pagesize=A4, pageCompression=1)
    canvas.setTitle(f"{data['meta']['section']} {data['meta']['title']} 教学设计预览")
    canvas.setAuthor("北京市和平街第一中学")
    draw_page_one(canvas, data)
    groups = [data["flow"][0:3], data["flow"][3:6], data["flow"][6:8]]
    for page_index, stages in enumerate(groups, start=1):
        canvas.showPage()
        draw_process_page(canvas, data, stages, page_index)
    canvas.save()
    return path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lesson-id", action="append")
    args = parser.parse_args()
    selected = set(args.lesson_id or [])
    register_fonts()
    count = 0
    for source in lesson_sources():
        data = yaml.safe_load(source.read_text(encoding="utf-8"))
        lesson_id = data["meta"]["lesson_id"]
        if lesson_id == "C07-L01" or (selected and lesson_id not in selected):
            continue
        print(render_one(data))
        count += 1
    print(f"[SUMMARY] previews={count} output={OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
