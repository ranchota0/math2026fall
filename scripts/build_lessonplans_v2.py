#!/usr/bin/env python3
"""Build the three Phase 6 mature-style pilot lesson plans."""
from __future__ import annotations

import argparse
import hashlib
import os
import re
import shutil
import subprocess
import time
from pathlib import Path

import yaml
from PIL import Image, ImageDraw, ImageOps


ROOT = Path(__file__).resolve().parents[1]
LESSON_DIR = ROOT / "lessons"
BUILD_DIR = ROOT / "build" / "lessonplans_v2"
DIST_DIR = ROOT / "dist" / "lessonplans_v2"
STYLE_CONFIG = ROOT / "config" / "lessonplan_style.yml"
BACKGROUND_SOURCE = ROOT / "blank.pdf"
BACKGROUND_COPY = ROOT / "templates" / "lessonplan" / "hepingjie_blank.pdf"
PILOT_IDS = ["C01-L03", "C05-L05", "C06-L07"]


FIGURES = {
    "axis_definition": r"""
\begin{tikzpicture}[x=8mm,y=8mm,baseline=(current bounding box.center)]
  \draw[->] (-3.6,0)--(3.8,0);
  \foreach \x in {-3,-2,...,3}{\draw (\x,.11)--(\x,-.11) node[below]{\scriptsize \x};}
  \node[above] at (0,.12) {\scriptsize 原点};
  \draw[<->] (0,-.72)--(1,-.72) node[midway,below]{\scriptsize 单位长度};
  \node[above] at (3.25,.08) {\scriptsize 正方向};
\end{tikzpicture}
""",
    "axis_errors": r"""
\begin{tikzpicture}[x=4.8mm,y=4.8mm,baseline=(current bounding box.center)]
  \begin{scope}
    \draw (-3,0)--(3,0);
    \foreach \x in {-2,-1,0,1,2}{\draw(\x,.12)--(\x,-.12);}
    \node[below] at (0,-.2){\scriptsize 图1：缺箭头};
  \end{scope}
  \begin{scope}[xshift=38mm]
    \draw[->] (-3,0)--(3,0);
    \foreach \x in {-2,-.7,0,1.6,2.4}{\draw(\x,.12)--(\x,-.12);}
    \node[below] at (0,-.2){\scriptsize 图2：刻度不均};
  \end{scope}
  \begin{scope}[xshift=76mm]
    \draw[->] (-3,0)--(3,0);
    \foreach \x/\t in {-2/{-1},-1/{-2},0/0,1/1,2/2}
      {\draw(\x,.12)--(\x,-.12)node[below]{\scriptsize $\t$};}
    \node[below] at (0,-.8){\scriptsize 图3：负数顺序错};
  \end{scope}
\end{tikzpicture}
""",
    "axis_points": r"""
\begin{tikzpicture}[x=8mm,y=8mm,baseline=(current bounding box.center)]
  \draw[->] (-4.2,0)--(4.4,0);
  \foreach \x in {-4,-3,...,4}{\draw(\x,.11)--(\x,-.11)node[below]{\scriptsize \x};}
  \foreach \x/\t in {-2.5/{-\frac52},-2/{-2},.5/{0.5},3/{3}}
    {\fill(\x,0)circle(1.35pt)node[above]{\scriptsize $\t$};}
\end{tikzpicture}
""",
    "angle_compare": r"""
\begin{tikzpicture}[scale=.62,baseline=(current bounding box.center)]
  \coordinate (O) at (0,0);
  \draw[->] (O)--(3.2,0) node[right]{$A$};
  \draw[->] (O)--(2.7,.55) node[right]{$B$};
  \node[left] at (O) {$O$};
  \draw (.55,0) arc (0:11.5:.55);
  \node[below] at (1.45,-.15) {\scriptsize 边长，张开小};
  \begin{scope}[xshift=5.2cm]
    \coordinate (P) at (0,0);
    \draw[->] (P)--(1.8,0) node[right]{$C$};
    \draw[->] (P)--(.95,1.45) node[above]{$D$};
    \node[left] at (P) {$P$};
    \draw (.48,0) arc (0:56:.48);
    \node[below] at (1.1,-.15) {\scriptsize 边短，张开大};
  \end{scope}
\end{tikzpicture}
""",
    "angle_sum": r"""
\begin{tikzpicture}[scale=.62,baseline=(current bounding box.center)]
  \coordinate(O) at (0,0);
  \draw[->](O)--(3,0) node[right]{$A$};
  \draw[->](O)--(2.35,1.05) node[right]{$B$};
  \draw[->](O)--(1.05,2.25) node[above]{$C$};
  \node[left] at (O) {$O$};
  \draw (.55,0) arc (0:24:.55);
  \draw (24:.7) arc (24:65:.7);
  \node[right] at (3.5,1.1) {$\angle AOC=\angle AOB+\angle BOC$};
\end{tikzpicture}
""",
    "angle_bisector": r"""
\begin{tikzpicture}[scale=.58,baseline=(current bounding box.center)]
  \coordinate(O) at (0,0);
  \draw[->](O)--(3,0) node[right]{$A$};
  \draw[->](O)--(2.35,1.15) node[right]{$B$};
  \draw[->](O)--(1.15,2.35) node[above]{$C$};
  \node[left] at (O) {$O$};
  \draw (.5,0) arc (0:26:.5);
  \draw (.62,0) arc (0:26:.62);
  \draw (26:.5) arc (26:64:.5);
  \draw (26:.62) arc (26:64:.62);
  \node[right] at (3.4,1.0) {$\angle AOB=\angle BOC$};
\end{tikzpicture}
""",
    "angle_composite": r"""
\begin{tikzpicture}[scale=.56,baseline=(current bounding box.center)]
  \coordinate(O) at (0,0);
  \draw[->](O)--(3,0) node[right]{$A$};
  \draw[->](O)--(2.35,1.1) node[right]{$B$};
  \draw[->](O)--(1.75,1.75) node[above right]{$D$};
  \draw[->](O)--(.8,2.55) node[above]{$C$};
  \node[left] at (O) {$O$};
  \draw (.5,0) arc (0:25:.5);
  \draw (.62,0) arc (0:25:.62);
  \draw (25:.5) arc (25:72:.5);
  \draw (25:.62) arc (25:72:.62);
  \draw (25:.95) arc (25:45:.95);
  \node[right] at (3.4,1.35) {\shortstack[l]{射线顺序：$OA,OB,OD,OC$\\$OB$ 平分 $\angle AOC$}};
\end{tikzpicture}
""",
}


def tool(name: str) -> str | None:
    texlive = Path(r"D:\texlive\2026\bin\windows") / f"{name}.exe"
    return str(texlive) if texlive.exists() else shutil.which(name)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def tex_text(value: str) -> str:
    return value.replace("%", r"\%")


def join_paragraphs(entries: list[str]) -> str:
    return "；".join(tex_text(entry) for entry in entries)


def teacher_part(label: str, entries: list[str]) -> str:
    return rf"\LPTeacherPart{{{label}}}{{{join_paragraphs(entries)}}}" if entries else ""


def student_part(label: str, entries: list[str]) -> str:
    return rf"\LPStudentPart{{{label}}}{{{join_paragraphs(entries)}}}" if entries else ""


def teacher_block(stage: dict) -> str:
    teacher = stage["teacher"]
    parts = [
        teacher_part("问题", teacher["questions"]),
        teacher_part("组织", teacher["actions"]),
        teacher_part("说明", teacher["explanation"]),
    ]
    figure_name = stage.get("figure")
    if figure_name:
        if figure_name not in FIGURES:
            raise ValueError(f"未知图形标识：{figure_name}")
        parts.append(rf"\LPFigureBlock{{{FIGURES[figure_name]}}}")
    parts.extend(
        [
            teacher_part("例题", teacher.get("example", [])),
            teacher_part("对应练习", teacher.get("practice", [])),
            teacher_part("纠错", teacher["correction"]),
            teacher_part("归纳", teacher.get("summary", [])),
            teacher_part("意图", stage["design_intent"]),
        ]
    )
    return "".join(parts)


def student_block(stage: dict) -> str:
    student = stage["student"]
    return "".join(
        [
            student_part("活动", student["actions"]),
            student_part("预期", student["expected_response"]),
        ]
    )


def overview_page(data: dict) -> str:
    meta = data["meta"]
    objectives = "".join(rf"\LPPlainLine{{{tex_text(item)}}}" for item in data["objectives"])
    blackboard = "".join(
        rf"\LPBoardLine{{{index}}}{{{tex_text(item)}}}"
        for index, item in enumerate(data["blackboard"]["lines"], 1)
    )
    date = meta["teaching_date"]
    return rf"""
\LPBackgroundPage{{1}}{{
  \LPCenterBox{{\LPDateYearX}}{{\LPDateY}}{{12mm}}{{5mm}}{{{date.get("year", "")}}}
  \LPCenterBox{{\LPDateMonthX}}{{\LPDateY}}{{10mm}}{{5mm}}{{{date.get("month", "")}}}
  \LPCenterBox{{\LPDateDayX}}{{\LPDateY}}{{10mm}}{{5mm}}{{{date.get("day", "")}}}
  \LPCenterBox{{\LPRecordPageX}}{{\LPRecordPageY}}{{10mm}}{{5mm}}{{1}}
  \LPHeaderCell{{\LPTopicX}}{{\LPTopicY}}{{\LPTopicW}}{{8mm}}{{{meta["title"]}}}
  \LPHeaderCell{{\LPTypeX}}{{\LPTypeY}}{{\LPTypeW}}{{8mm}}{{{meta["lesson_type"]}}}
  \LPCenterBox{{\LPUnitTotalX}}{{\LPUnitTotalY}}{{12mm}}{{5mm}}{{{meta["unit_total_periods"]}}}
  \LPCenterBox{{\LPTopicTotalX}}{{\LPTopicTotalY}}{{12mm}}{{5mm}}{{{meta["topic_total_periods"]}}}
  \LPCenterBox{{\LPCurrentPeriodX}}{{\LPCurrentPeriodY}}{{12mm}}{{5mm}}{{{meta["current_period"]}}}
  \LPTextBox{{\LPBodyX}}{{\LPObjectiveY}}{{\LPBodyW}}{{\LPObjectiveH}}{{{objectives}}}
  \LPTextBox{{\LPBodyX}}{{\LPKeyPointY}}{{\LPBodyW}}{{\LPKeyPointH}}{{{tex_text("；".join(data["key_points"]))}}}
  \LPTextBox{{\LPBodyX}}{{\LPDifficultyY}}{{\LPBodyW}}{{\LPDifficultyH}}{{{tex_text("；".join(data["difficulties"]))}}}
  \LPTextBox{{\LPBodyX}}{{\LPMethodY}}{{\LPBodyW}}{{\LPMethodH}}{{{tex_text("；".join(data["methods"]))}}}
  \LPTextBox{{\LPBodyX}}{{\LPMediaY}}{{\LPBodyW}}{{\LPMediaH}}{{{tex_text("；".join(data["media"]))}}}
  \LPTextBox{{\LPBodyX}}{{\LPBlackboardY}}{{\LPBodyW}}{{\LPBlackboardH}}{{\LPBoardTitle{{{tex_text(data["blackboard"]["title"])}}}{blackboard}}}
}}
"""


def process_page(page_number: int, stages: list[dict]) -> str:
    height = r"\LPProcessPageFourH" if page_number == 4 else r"\LPProcessFullH"
    rows = "\n".join(
        rf"\LPProcessRow{{{tex_text(stage['stage'])}}}{{{teacher_block(stage)}}}{{{student_block(stage)}}}{{{stage['minutes']}}}"
        for stage in stages
    )
    return rf"""
\LPBackgroundPage{{{page_number}}}{{
  \LPProcessBox{{\LPProcessX}}{{\LPProcessY}}{{\LPProcessW}}{{{height}}}{{{rows}}}
}}
"""


def document(data: dict) -> str:
    pages = [overview_page(data)]
    for page_number in (2, 3, 4):
        pages.append(
            process_page(
                page_number,
                [stage for stage in data["process"] if stage["page"] == page_number],
            )
        )
    return (
        "% !TeX program = xelatex\n"
        r"\documentclass[UTF8,a4paper,zihao=-4,fontset=none]{ctexart}" "\n"
        r"\setCJKmainfont[BoldFont={LXGW Neo XiHei}]{LXGW Neo ZhiSong}" "\n"
        r"\setCJKsansfont[AutoFakeBold=2]{LXGW Neo XiHei}" "\n"
        r"\setCJKmonofont{LXGW Neo XiHei}" "\n"
        r"\setCJKfamilyfont{zhhei}[AutoFakeBold=2]{LXGW Neo XiHei}" "\n"
        r"\providecommand{\heiti}{\CJKfamily{zhhei}}" "\n"
        r"\input{tex/lessonplan/hepingjie_render.tex}" "\n"
        r"\usetikzlibrary{calc}" "\n"
        r"\begin{document}" "\n"
        + "".join(pages)
        + r"\end{document}" "\n"
    )


def validate_data(lesson_id: str, data: dict, style: dict) -> list[str]:
    errors: list[str] = []
    if data.get("meta", {}).get("lesson_id") != lesson_id:
        errors.append("meta.lesson_id 与目录不一致")
    objective_count = len(data.get("objectives", []))
    if not style["objectives"]["min_items"] <= objective_count <= style["objectives"]["max_items"]:
        errors.append(f"教学目标数量为 {objective_count}")
    process = data.get("process", [])
    if not style["process"]["min_stages"] <= len(process) <= style["process"]["max_stages"]:
        errors.append(f"教学阶段数量为 {len(process)}")
    minutes = sum(int(stage.get("minutes", 0)) for stage in process)
    if minutes != style["lesson_duration"]:
        errors.append(f"总估时为 {minutes} 分钟")
    for stage in process:
        name = stage.get("stage", "未命名")
        if stage.get("page") not in (2, 3, 4):
            errors.append(f"{name} 的页码无效")
        teacher = stage.get("teacher", {})
        student = stage.get("student", {})
        for key in ("questions", "actions", "explanation", "correction"):
            if not teacher.get(key):
                errors.append(f"{name} 的 teacher.{key} 为空")
        for key in ("actions", "expected_response"):
            if not student.get(key):
                errors.append(f"{name} 的 student.{key} 为空")
        intent = stage.get("design_intent", [])
        if not intent or len(intent) > style["process"]["design_intent_max_items"]:
            errors.append(f"{name} 的设计意图数量不合规")
    for page_number in (2, 3, 4):
        if not any(stage.get("page") == page_number for stage in process):
            errors.append(f"第 {page_number} 页没有教学阶段")
    reflection = data.get("reflection", {})
    if reflection.get("mode") != "blank" or reflection.get("text"):
        errors.append("课后反思必须保持空白")
    return errors


def compile_tex(tex_path: Path, output_dir: Path) -> tuple[bool, float, str]:
    xelatex = tool("xelatex")
    if not xelatex:
        raise RuntimeError("未找到 xelatex")
    env = os.environ.copy()
    env["TEXINPUTS"] = ".//" + os.pathsep + "tex//" + os.pathsep + env.get("TEXINPUTS", "")
    command = [
        xelatex,
        "-interaction=nonstopmode",
        "-halt-on-error",
        f"-output-directory={output_dir.relative_to(ROOT).as_posix()}",
        tex_path.relative_to(ROOT).as_posix(),
    ]
    started = time.perf_counter()
    outputs = []
    return_code = 0
    for _ in range(2):
        result = subprocess.run(
            command,
            cwd=ROOT,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        outputs.append(result.stdout)
        return_code = result.returncode
        if return_code:
            break
    elapsed = time.perf_counter() - started
    output = "\n".join(outputs)
    (output_dir / "lessonplan.compile.log").write_text(output, encoding="utf-8")
    return return_code == 0, elapsed, output


def pdf_info(pdf_path: Path) -> dict:
    pdfinfo = tool("pdfinfo")
    if not pdfinfo:
        raise RuntimeError("未找到 pdfinfo")
    result = subprocess.run(
        [pdfinfo, pdf_path.relative_to(ROOT).as_posix()],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=True,
    )
    pages_match = re.search(r"Pages:\s+(\d+)", result.stdout)
    size_match = re.search(r"Page size:\s+([0-9.]+)\s+x\s+([0-9.]+)\s+pts", result.stdout)
    return {
        "pages": int(pages_match.group(1)) if pages_match else 0,
        "width": float(size_match.group(1)) if size_match else 0.0,
        "height": float(size_match.group(2)) if size_match else 0.0,
    }


def render_pdf(pdf_path: Path, output_dir: Path) -> None:
    pdftoppm = tool("pdftoppm")
    if not pdftoppm:
        raise RuntimeError("未找到 pdftoppm")
    for stale in output_dir.glob("page-*.png"):
        stale.unlink()
    contact_sheet = output_dir / "contact-sheet.png"
    if contact_sheet.exists():
        contact_sheet.unlink()
    prefix = output_dir / "page"
    subprocess.run(
        [
            pdftoppm,
            "-png",
            "-r",
            "150",
            pdf_path.relative_to(ROOT).as_posix(),
            prefix.relative_to(ROOT).as_posix(),
        ],
        cwd=ROOT,
        check=True,
    )
    images = []
    for page_number, path in enumerate(sorted(output_dir.glob("page-*.png")), 1):
        image = Image.open(path).convert("RGB")
        image.thumbnail((360, 510))
        framed = ImageOps.expand(image, border=7, fill="white")
        canvas = Image.new("RGB", (framed.width, framed.height + 24), "white")
        canvas.paste(framed, (0, 0))
        ImageDraw.Draw(canvas).text((9, framed.height + 5), f"page {page_number}", fill="black")
        images.append(canvas)
    if images:
        cell_width = max(image.width for image in images)
        cell_height = max(image.height for image in images)
        sheet = Image.new("RGB", (len(images) * cell_width, cell_height), "#d8d8d8")
        for index, image in enumerate(images):
            sheet.paste(image, (index * cell_width, 0))
        sheet.save(contact_sheet)


def difference_note(data: dict, output_dir: Path, v1_path: Path, v2_path: Path) -> None:
    stage_names = " → ".join(stage["stage"] for stage in data["process"])
    lines = [
        f"# {data['meta']['lesson_id']} v1/v2 差异说明",
        "",
        f"- v1：`{v1_path.relative_to(ROOT).as_posix()}`",
        f"- v2：`{v2_path.relative_to(ROOT).as_posix()}`",
        "- v2 使用结构化的教师问题、教师动作、知识说明、纠错、学生活动、预期回答和设计意图。",
        f"- v2 教学链条：{stage_names}。",
        "- v2 采用“一例一练一归纳”，学生栏与估时栏均填写，合计 45 分钟。",
        "- v2 保留四页背景模板和空白课后反思，不迁移成熟教案中的初三题目。",
    ]
    (output_dir / "v1_v2_difference.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ids", nargs="*", choices=PILOT_IDS, default=PILOT_IDS)
    args = parser.parse_args()
    selected = args.ids or PILOT_IDS

    style = yaml.safe_load(STYLE_CONFIG.read_text(encoding="utf-8"))
    if not BACKGROUND_SOURCE.exists() or not BACKGROUND_COPY.exists():
        raise FileNotFoundError("blank.pdf 或项目背景副本不存在")
    if sha256(BACKGROUND_SOURCE) != sha256(BACKGROUND_COPY):
        raise RuntimeError("blank.pdf 与冻结背景副本 SHA-256 不一致")

    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    DIST_DIR.mkdir(parents=True, exist_ok=True)
    failed = False
    for lesson_id in selected:
        source_yml = LESSON_DIR / lesson_id / "lessonplan.yml"
        data = yaml.safe_load(source_yml.read_text(encoding="utf-8"))
        data_errors = validate_data(lesson_id, data, style)
        if data_errors:
            failed = True
            print(f"[FAIL] {lesson_id} data: {'; '.join(data_errors)}")
            continue

        output_dir = BUILD_DIR / lesson_id
        output_dir.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source_yml, output_dir / "lessonplan.yml")
        tex_path = output_dir / "lessonplan.tex"
        tex_path.write_text(document(data), encoding="utf-8")
        ok, elapsed, log = compile_tex(tex_path, output_dir)
        pdf_path = output_dir / "lessonplan.pdf"
        if not ok or not pdf_path.exists():
            failed = True
            print(f"[FAIL] {lesson_id} compile ({elapsed:.1f}s)")
            continue

        info = pdf_info(pdf_path)
        warning_count = len(re.findall(r"(?:LaTeX|Package) Warning", log))
        overfull_count = len(re.findall(r"Overfull \\hbox", log))
        latex_error_count = len(re.findall(r"(?:LaTeX Error|Fatal error|Emergency stop)", log))
        a4_portrait = abs(info["width"] - 595.28) < 1.0 and abs(info["height"] - 841.89) < 1.0
        if info["pages"] != style["page_count"] or not a4_portrait or overfull_count or latex_error_count:
            failed = True
            print(
                f"[FAIL] {lesson_id} pages={info['pages']} a4={a4_portrait} "
                f"overfull={overfull_count} errors={latex_error_count}"
            )
            continue

        render_pdf(pdf_path, output_dir)
        rendered_pages = len(list(output_dir.glob("page-*.png")))
        if rendered_pages != style["page_count"]:
            failed = True
            print(f"[FAIL] {lesson_id} rendered_pages={rendered_pages}")
            continue

        title = data["meta"]["title"]
        dist_path = DIST_DIR / f"{lesson_id}_{title}_教案_v2.pdf"
        shutil.copyfile(pdf_path, dist_path)
        v1_path = ROOT / "dist" / "lessonplans" / f"{lesson_id}_{title}_教案.pdf"
        difference_note(data, output_dir, v1_path, dist_path)
        print(
            f"[OK] {lesson_id} pages={info['pages']} minutes=45 "
            f"warnings={warning_count} overfull={overfull_count} seconds={elapsed:.1f}"
        )
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
