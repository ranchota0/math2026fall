from __future__ import annotations

import ast
import html
from pathlib import Path
from zipfile import ZipFile

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import Paragraph, Table, TableStyle


ROOT = Path(__file__).resolve().parents[1]
DOCX = (
    ROOT
    / "lessons"
    / "第07章_相交线与平行线"
    / "7.1.1_相交线与对顶角"
    / "教学设计"
    / "7.1.1_相交线与对顶角_教学设计_模板调整版.docx"
)
PDF = DOCX.with_suffix(".pdf")


def docx_text(path: Path) -> str:
    with ZipFile(path) as archive:
        xml = archive.read("word/document.xml").decode("utf-8")
    import re

    return "".join(re.findall(r"<w:t[^>]*>(.*?)</w:t>", xml)).replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&")


def process_pages() -> list[list[dict]]:
    tree = ast.parse((ROOT / "scripts" / "adjust_c07_l01_template.py").read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "PROCESS_PAGES" for t in node.targets):
            return ast.literal_eval(node.value)
    raise RuntimeError("PROCESS_PAGES not found")


def register_fonts() -> None:
    pdfmetrics.registerFont(TTFont("FangSong", r"C:\Windows\Fonts\simfang.ttf"))
    pdfmetrics.registerFont(TTFont("SimHei", r"C:\Windows\Fonts\simhei.ttf"))


BODY = ParagraphStyle(
    "body",
    fontName="FangSong",
    fontSize=9.5,
    leading=12.2,
    alignment=TA_LEFT,
    wordWrap="CJK",
    spaceAfter=1,
)
BODY_SMALL = ParagraphStyle(
    "body-small",
    parent=BODY,
    fontSize=8.8,
    leading=11.5,
)
CENTER = ParagraphStyle(
    "center",
    parent=BODY,
    fontSize=10.5,
    leading=13,
    alignment=TA_CENTER,
)
LABEL = ParagraphStyle(
    "label",
    parent=CENTER,
    fontName="FangSong",
    fontSize=10.5,
    leading=14,
)


def esc(value: str) -> str:
    return html.escape(value).replace("\n", "<br/>")


def para(text: str, *, style=BODY, bold: bool = False) -> Paragraph:
    markup = esc(text)
    if bold:
        markup = f'<font name="SimHei">{markup}</font>'
    return Paragraph(markup, style)


def rich(heading: str, items: list[tuple[str, str]], *, size: float = 8.8) -> Paragraph:
    parts = [f'<font name="SimHei">{esc(heading)}</font>']
    for label, text in items:
        parts.append(f'<font name="SimHei">{esc(label)}：</font>{esc(text)}')
    style = ParagraphStyle(
        f"rich-{size}",
        parent=BODY_SMALL,
        fontSize=size,
        leading=size * 1.31,
    )
    return Paragraph("<br/>".join(parts), style)


def draw_page_one(canvas: Canvas) -> None:
    width, height = A4
    canvas.setFont("SimHei", 18)
    canvas.drawCentredString(width / 2, height - 2.45 * cm, "北京市和平街第一中学课时教学设计")
    canvas.setFont("FangSong", 10.5)
    canvas.drawCentredString(width / 2, height - 4.15 * cm, "授课时间　　　　年　　月　　日　　　　　　　　　　　　第　1　页")

    data = [["" for _ in range(9)] for _ in range(8)]
    data[0][0] = para("课题", style=CENTER)
    data[0][3] = para("7.1.1 两条直线相交（邻补角与对顶角）")
    data[0][6] = para("课型", style=CENTER)
    data[0][7] = para("概念形成课")
    data[1][0] = para("章（单元）总课时", style=CENTER)
    data[1][3] = para("13", style=CENTER)
    data[1][4] = para("本课题课时", style=CENTER)
    data[1][5] = para("1", style=CENTER)
    data[1][6] = para("本节课是第　1　课时", style=CENTER)

    labels = ["教\n学\n目\n标", "教学\n重点", "教学\n难点", "教学\n方法", "教学\n手段", "板\n书\n设\n计"]
    contents = [
        [
            "1. 通过观察和标注相交线所成的四个角，说出邻补角、对顶角的定义，并能按位置关系正确识别。",
            "2. 借助补角的性质说明“对顶角相等”，能写出两步以内的推理依据。",
            "3. 已知相交线中一个角或相邻两角的数量关系，能计算其余角的度数并检验结果。",
            "4. 在转动木条、比较和交流中形成“先看位置、再用数量”的几何研究习惯。",
        ],
        ["识别邻补角和对顶角；运用对顶角相等解决简单角度问题。"],
        ["从角的两边关系准确说明对顶角，并把补角性质组织成规范推理。"],
        ["问题驱动；操作探究；例练结合；同伴互评。"],
        [
            "教师：两根可转动硬纸条、PPT、直尺、实物投影；学生：直尺、量角器、学案。",
            "教材：人教版《义务教育教科书·数学七年级下册》，印刷页1—3（PDF 8—10）。",
        ],
        [
            "7.1.1 相交线与对顶角",
            "1. 邻补角：公共边；另外两边互为反向延长线；和为180°。",
            "2. 对顶角：公共顶点；两边分别互为反向延长线。",
            "3. 性质：对顶角相等。推理：∠1+∠2=180°，∠3+∠2=180°，所以∠1=∠3。",
            "4. 方法：先看位置 → 选关系 → 列式 → 写依据 → 检验。",
            "5. 易错：相等的角不一定是对顶角。",
        ],
    ]
    for row, (label, lines) in enumerate(zip(labels, contents), start=2):
        data[row][0] = para(label, style=LABEL)
        body_style = BODY_SMALL if row in (2, 7) else BODY
        markup = "<br/>".join(
            (f'<font name="SimHei">{esc(line)}</font>' if row == 7 and i == 0 else esc(line))
            for i, line in enumerate(lines)
        )
        data[row][2] = Paragraph(markup, body_style)

    col_widths = [1.52, 0.60, 0.90, 4.35, 3.54, 1.68, 1.54, 2.47, 1.40]
    row_heights = [0.95, 0.95, 4.2, 1.55, 1.55, 1.55, 2.05, 8.65]
    table = Table(data, colWidths=[v * cm for v in col_widths], rowHeights=[v * cm for v in row_heights])
    spans = [
        ("SPAN", (0, 0), (2, 0)),
        ("SPAN", (3, 0), (5, 0)),
        ("SPAN", (7, 0), (8, 0)),
        ("SPAN", (0, 1), (2, 1)),
        ("SPAN", (6, 1), (8, 1)),
    ]
    for row in range(2, 8):
        spans.extend([("SPAN", (0, row), (1, row)), ("SPAN", (2, row), (8, row))])
    table.setStyle(
        TableStyle(
            [
                *spans,
                ("GRID", (0, 0), (-1, -1), 0.65, colors.black),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("VALIGN", (2, 2), (8, 7), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    tw, th = table.wrapOn(canvas, 18 * cm, 22 * cm)
    table.drawOn(canvas, (width - tw) / 2, height - 4.75 * cm - th)


def draw_process_page(canvas: Canvas, stages: list[dict], *, final_page: bool) -> None:
    width, height = A4
    rows = 1 + len(stages) + (1 if final_page else 0)
    data = [["" for _ in range(4)] for _ in range(rows)]
    data[0] = [para("", style=CENTER), para("教师教学活动设计", style=CENTER), para("学生活动", style=CENTER), para("估时", style=CENTER)]
    for idx, stage in enumerate(stages, start=1):
        stage_size = stage.get("font_size", 8.8)
        data[idx][0] = para("教\n学\n过\n程", style=LABEL) if idx == 1 else ""
        data[idx][1] = rich(stage["stage"], stage["teacher"], size=stage_size)
        data[idx][2] = rich("", stage["student"], size=max(stage_size, 8.8))
        data[idx][3] = para(stage["time"], style=CENTER)
    if final_page:
        row = rows - 1
        data[row][0] = para("课\n后\n反\n思", style=LABEL)
        data[row][1] = ""

    col_widths = [1.50, 11.20, 3.50, 1.80]
    row_heights = [0.75] + [stage.get("height", 7.85 if final_page else 8.20) for stage in stages]
    if final_page:
        row_heights.append(9.10)
    table = Table(data, colWidths=[v * cm for v in col_widths], rowHeights=[v * cm for v in row_heights])
    commands = [
        ("BOX", (0, 0), (-1, -1), 0.65, colors.black),
        ("LINEBELOW", (0, 0), (-1, 0), 0.65, colors.black),
        ("LINEAFTER", (0, 0), (0, -1), 0.65, colors.black),
        ("LINEAFTER", (1, 0), (1, -1), 0.65, colors.black),
        ("LINEAFTER", (2, 0), (2, -1), 0.65, colors.black),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("VALIGN", (1, 1), (2, len(stages)), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("SPAN", (0, 1), (0, len(stages))),
    ]
    if final_page:
        commands.append(("SPAN", (1, rows - 1), (3, rows - 1)))
        commands.append(("VALIGN", (1, rows - 1), (3, rows - 1), "TOP"))
        commands.append(("LINEABOVE", (0, rows - 1), (3, rows - 1), 0.65, colors.black))
    table.setStyle(TableStyle(commands))
    tw, th = table.wrapOn(canvas, 18 * cm, 27 * cm)
    table.drawOn(canvas, (width - tw) / 2, height - 1.15 * cm - th)


def main() -> None:
    if not DOCX.exists():
        raise FileNotFoundError(DOCX)
    text = docx_text(DOCX)
    required = ["北京市和平街第一中学课时教学设计", "邻补角", "对顶角", "对顶角相等", "当堂检测", "课后反思"]
    missing = [item for item in required if item not in text]
    if missing:
        raise RuntimeError(f"final DOCX is missing required content: {missing}")

    register_fonts()
    canvas = Canvas(str(PDF), pagesize=A4, pageCompression=1)
    canvas.setTitle("7.1.1 两条直线相交（邻补角与对顶角）教学设计")
    canvas.setAuthor("北京市和平街第一中学")
    draw_page_one(canvas)
    canvas.showPage()
    pages = process_pages()
    draw_process_page(canvas, pages[0], final_page=False)
    canvas.showPage()
    draw_process_page(canvas, pages[1], final_page=False)
    canvas.showPage()
    draw_process_page(canvas, pages[2], final_page=True)
    canvas.save()
    print(PDF)


if __name__ == "__main__":
    main()
