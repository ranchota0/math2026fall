#!/usr/bin/env python3
"""Build Phase 7 lesson plans without modifying the frozen Phase 6 renderer."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import shutil
import sys
from pathlib import Path

import yaml
from PIL import Image, ImageDraw, ImageOps


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import build_lessonplans_v2 as frozen  # noqa: E402
from phase7_content_bank import CONTENT  # noqa: E402


MANIFEST_PATH = ROOT / "config" / "curriculum_manifest.yml"
STYLE_PATH = ROOT / "config" / "lessonplan_style.yml"
BUILD_ROOT = ROOT / "build" / "lessonplans_final"
OUTPUT_ROOT = ROOT / "output" / "lesson_plans_final"
APPROVED_IDS = {"C01-L03", "C05-L05", "C06-L07"}
FROZEN_HASHES = {
    "tex/lessonplan/hepingjie_lessonplan.sty": "1A11888DB7ECA9FF51B0D3691B9EA765AE710B4D35A0090347AC43487D6AA1B4",
    "scripts/build_lessonplans_v2.py": "8D9C2AB5FB0377D2A2A58F0EAE0069CD10F314300B85A54FF623FB84852DC069",
    "config/lessonplan_style.yml": "83943BE1673992DBE546D553A85EE5D3696664E06E524B862B4747B32BC3B29E",
    "reports/phase6_1_template_freeze_report.md": "31708A51A90BFA5A53232C1D0E232913356E69B68CE0EF6A752D6CB871E838EB",
    "dist/lessonplans_v2/C01-L03_数轴_教案_v2.pdf": "E081CC01273A9585E337047406C9BFCE4C34AC163A94783A53A1E001F59F0352",
    "dist/lessonplans_v2/C05-L05_移项解一元一次方程_教案_v2.pdf": "68A435ADFD7B5920C37A44155AA92E43C3438778EE51790CA4F31414A164EAE2",
    "dist/lessonplans_v2/C06-L07_角的比较与运算_教案_v2.pdf": "FCFC4DE162CFD88F25F3B3B468D86AB9AEB5933F4E874EADE09E34A7C84770D5",
}


EXTRA_FIGURES = {
    "addition_axis": r"""
\begin{tikzpicture}[x=8mm,y=8mm,baseline=(current bounding box.center)]
  \draw[->] (-5.3,0)--(5.5,0);
  \foreach \x in {-5,-4,...,5}{\draw(\x,.11)--(\x,-.11)node[below]{\scriptsize \x};}
  \draw[->,thick] (0,.55)--(3,.55) node[midway,above]{\scriptsize $+3$};
  \draw[->,thick] (3,.9)--(-2,.9) node[midway,above]{\scriptsize $-5$};
  \fill (0,0) circle(1.2pt); \fill (-2,0) circle(1.2pt);
\end{tikzpicture}
""",
    "place_value": r"""
\begin{tikzpicture}[x=15mm,y=8mm,baseline=(current bounding box.center)]
  \foreach \x/\t in {0/个位,1/十位,2/百位,3/千位}{
    \draw (\x,0) rectangle ++(1,1); \node at (\x+.5,.68){\scriptsize \t};
    \node at (\x+.5,.28){\scriptsize $10^{\x}$};
  }
  \node[below] at (2,-.15){\scriptsize 每一位的数字乘相应位值};
\end{tikzpicture}
""",
    "solid_plane": r"""
\begin{tikzpicture}[scale=.75,baseline=(current bounding box.center)]
  \draw (0,0) rectangle (2.6,1.7); \draw (.6,.6) rectangle (3.2,2.3);
  \draw (0,0)--(.6,.6);
  \draw (2.6,0)--(3.2,.6);
  \draw (2.6,1.7)--(3.2,2.3);
  \draw (0,1.7)--(.6,2.3);
  \node[below] at (1.6,-.2){\scriptsize 长方体};
  \draw (5.3,0) ellipse (1.1 and .35); \draw (4.2,0)--(4.2,2); \draw (6.4,0)--(6.4,2);
  \draw (5.3,2) ellipse (1.1 and .35); \node[below] at (5.3,-.45){\scriptsize 圆柱};
  \draw (8.2,.1) rectangle (10,1.9); \draw (11.5,1) circle(.9);
  \node[below] at (9.1,-.15){\scriptsize 正方形}; \node[below] at (11.5,-.15){\scriptsize 圆};
\end{tikzpicture}
""",
    "point_line_surface": r"""
\begin{tikzpicture}[scale=.72,baseline=(current bounding box.center)]
  \coordinate(A)at(0,0);\coordinate(B)at(3,0);\coordinate(C)at(3,2);\coordinate(D)at(0,2);
  \coordinate(E)at(.7,.7);\coordinate(F)at(3.7,.7);\coordinate(G)at(3.7,2.7);\coordinate(H)at(.7,2.7);
  \draw (A)--(B)--(C)--(D)--cycle (E)--(F)--(G)--(H)--cycle;
  \foreach \p/\q in {A/E,B/F,C/G,D/H}{\draw (\p)--(\q);}
  \fill (A)circle(1.6pt) node[below left]{$A$};
  \node[below] at (1.5,0){\scriptsize 线}; \node at (2.6,1.5){\scriptsize 面};
  \node[right] at (4.2,1.4){\scriptsize 体由面围成，面交成线，线交成点};
\end{tikzpicture}
""",
    "line_ray_segment": r"""
\begin{tikzpicture}[x=9mm,y=8mm,baseline=(current bounding box.center)]
  \draw[<->] (-.6,2)--(4.2,2); \fill(1,2)circle(1.2pt)node[above]{$A$};\fill(3,2)circle(1.2pt)node[above]{$B$};
  \node[right] at (4.3,2){\scriptsize 直线 $AB$};
  \draw[->] (0,1)--(4.2,1); \fill(0,1)circle(1.2pt)node[above]{$A$};\fill(2.5,1)circle(1.2pt)node[above]{$B$};
  \node[right] at (4.3,1){\scriptsize 射线 $AB$};
  \draw (0,0)--(3.2,0); \fill(0,0)circle(1.2pt)node[above]{$A$};\fill(3.2,0)circle(1.2pt)node[above]{$B$};
  \node[right] at (4.3,0){\scriptsize 线段 $AB$};
\end{tikzpicture}
""",
    "segment_compare": r"""
\begin{tikzpicture}[x=12mm,y=9mm,baseline=(current bounding box.center)]
  \draw (0,1.2)--(4,1.2); \fill(0,1.2)circle(1.2pt)node[above]{$A$};\fill(4,1.2)circle(1.2pt)node[above]{$B$};
  \draw (.5,0)--(3.2,0); \fill(.5,0)circle(1.2pt)node[above]{$C$};\fill(3.2,0)circle(1.2pt)node[above]{$D$};
  \node[right] at (4.5,.6){\scriptsize 叠合或度量比较};
\end{tikzpicture}
""",
    "segment_midpoint": r"""
\begin{tikzpicture}[x=13mm,y=8mm,baseline=(current bounding box.center)]
  \draw (0,0)--(6,0); \foreach \x/\t in {0/A,3/M,6/B}{\fill(\x,0)circle(1.3pt)node[above]{$\t$};}
  \draw (1.35,.16)--(1.55,-.16); \draw (4.45,.16)--(4.65,-.16);
  \node[below] at (3,-.25){$AM=MB=\frac12AB$};
\end{tikzpicture}
""",
    "angle_measure": r"""
\begin{tikzpicture}[scale=.7,baseline=(current bounding box.center)]
  \coordinate(O)at(0,0); \draw[->](O)--(4,0)node[right]{$A$}; \draw[->](O)--(2.6,2.2)node[above]{$B$};
  \node[left]at(O){$O$}; \draw (.8,0) arc (0:40:.8); \node at (1.25,.45){\scriptsize $\alpha$};
  \draw (6,0)--(9,0); \foreach \a in {0,30,...,180}{\draw (7.5,0)--++(\a:.25);}
  \node[below]at(7.5,-.2){\scriptsize 量角器中心对准顶点};
\end{tikzpicture}
""",
    "complementary_angles": r"""
\begin{tikzpicture}[scale=.72,baseline=(current bounding box.center)]
  \draw[->](0,0)--(3,0)node[right]{$A$};\draw[->](0,0)--(0,2.5)node[above]{$C$};\draw[->](0,0)--(2,1.45)node[right]{$B$};
  \node[below left]at(0,0){$O$}; \draw (.35,0)--(.35,.35)--(0,.35);
  \node[right]at(3.7,1.2){$\angle AOB+\angle BOC=90^\circ$};
  \draw[->](8,0)--(5,0)node[left]{$D$};\draw[->](8,0)--(11,0)node[right]{$F$};\draw[->](8,0)--(9.7,1.7)node[above]{$E$};
  \node[below]at(8,0){$P$}; \node[right]at(8.4,-.55){\scriptsize 两角和为 $180^\circ$};
\end{tikzpicture}
""",
    "geometry_activity": r"""
\begin{tikzpicture}[scale=.68,baseline=(current bounding box.center)]
  \draw (0,0)--(5,0); \foreach \x/\t in {0/A,2.5/M,5/B}{\fill(\x,0)circle(1.2pt)node[above]{$\t$};}
  \draw (1.15,.15)--(1.35,-.15);\draw (3.65,.15)--(3.85,-.15);
  \begin{scope}[xshift=7cm]
    \draw[->](0,0)--(3,0)node[right]{$C$};\draw[->](0,0)--(2.2,1.2)node[right]{$D$};\draw[->](0,0)--(.8,2.5)node[above]{$E$};
    \node[left]at(0,0){$O$};\draw (.55,0)arc(0:29:.55);\draw (29:.55)arc(29:72:.55);
  \end{scope}
\end{tikzpicture}
""",
    "geometry_review": r"""
\begin{tikzpicture}[scale=.68,baseline=(current bounding box.center)]
  \draw (0,0)--(5,0); \foreach \x/\t in {0/A,2.5/M,4/C,5/B}{\fill(\x,0)circle(1.2pt)node[above]{$\t$};}
  \node[below]at(2.5,-.25){\scriptsize 线段和差与中点};
  \begin{scope}[xshift=7cm]
    \draw[->](0,0)--(3,0)node[right]{$A$};\draw[->](0,0)--(2.2,1.1)node[right]{$B$};\draw[->](0,0)--(.7,2.5)node[above]{$C$};
    \node[left]at(0,0){$O$};\draw (.5,0)arc(0:27:.5);\draw (27:.5)arc(27:74:.5);
  \end{scope}
\end{tikzpicture}
""",
    "track_layout": r"""
\begin{tikzpicture}[x=.8mm,y=.8mm,baseline=(current bounding box.center)]
  \draw (0,0) rectangle (92,38); \draw[dashed] (5,5) rectangle (87,33);
  \draw (23,9)--(69,9) arc (-90:90:12)--(23,33) arc (90:270:12)--cycle;
  \draw (25,12)--(67,12) arc (-90:90:9)--(25,30) arc (90:270:9)--cycle;
  \node at (46,19){\scriptsize 比赛区域}; \node[below]at(46,-2){\scriptsize 标比例尺、尺寸与安全带};
\end{tikzpicture}
""",
}
frozen.FIGURES.update(EXTRA_FIGURES)


ARCHETYPE = {
    "concept": {
        "type": "概念形成课",
        "stages": ["情境引入", "比较与抽象", "正例示范", "表示与应用", "易错辨析", "归纳迁移", "当堂检测", "回顾总结与作业"],
        "times": [5, 7, 7, 6, 5, 5, 6, 4],
        "methods": ["问题引导", "比较归纳", "正反例辨析"],
    },
    "skill": {
        "type": "运算技能课",
        "stages": ["依据复习", "尝试与归纳", "规范示范", "变式训练", "错解诊断", "综合练习", "当堂检测", "回顾总结与作业"],
        "times": [5, 7, 8, 6, 5, 4, 6, 4],
        "methods": ["复习迁移", "规范板演", "错例纠正"],
    },
    "geometry": {
        "type": "几何探究课",
        "stages": ["观察与操作", "概念形成", "图形表示", "关系应用", "条件辨析", "综合探究", "当堂检测", "回顾总结与作业"],
        "times": [5, 7, 7, 6, 5, 5, 6, 4],
        "methods": ["观察操作", "画图标注", "图形说理"],
    },
    "application": {
        "type": "应用建模课",
        "stages": ["问题情境", "数量关系", "模型求解", "变式解释", "错误诊断", "方案迁移", "当堂检测", "回顾总结与作业"],
        "times": [5, 7, 8, 6, 5, 4, 6, 4],
        "methods": ["情境分析", "数量关系建模", "检验解释"],
    },
    "activity": {
        "type": "数学活动课",
        "stages": ["任务说明", "独立尝试", "小组探究", "展示交流", "错误修正", "迁移应用", "反馈评价", "回顾总结与作业"],
        "times": [5, 7, 8, 7, 5, 4, 5, 4],
        "methods": ["操作探究", "合作交流", "成果互评"],
    },
    "review": {
        "type": "章末复习课",
        "stages": ["知识诊断", "结构梳理", "典型题组", "方法迁移", "易错诊断", "综合训练", "当堂检测", "分层作业"],
        "times": [5, 7, 8, 6, 5, 4, 6, 4],
        "methods": ["结构梳理", "题组训练", "错因诊断"],
    },
    "project": {
        "type": "综合实践课",
        "stages": ["任务理解", "信息整理", "方案形成", "计算验证", "错误修正", "展示评价", "成果检测", "回顾总结与作业"],
        "times": [5, 7, 8, 7, 5, 4, 5, 4],
        "methods": ["任务驱动", "合作建模", "方案评价"],
    },
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def ensure_frozen() -> None:
    mismatches = []
    for relative, expected in FROZEN_HASHES.items():
        path = ROOT / relative
        actual = sha256(path) if path.exists() else "MISSING"
        if actual != expected:
            mismatches.append(f"{relative}: expected {expected}, got {actual}")
    if mismatches:
        raise RuntimeError("Phase 6.1 frozen baseline changed:\n" + "\n".join(mismatches))


def clean_filename(value: str) -> str:
    cleaned = re.sub(r'[<>:"/\\|?*]', "_", value).strip().rstrip(".")
    return re.sub(r"\s+", "", cleaned)


def infer_archetype(lesson: dict) -> str:
    title = lesson["lesson_title"]
    if lesson["lesson_type"] == "review_lesson":
        return "review"
    if lesson["lesson_type"] == "activity_lesson":
        return "activity"
    if lesson["lesson_type"] == "integrated_practice":
        return "project"
    if lesson["chapter_id"] == "C06" or "数轴" in title:
        return "geometry"
    if "实际问题" in title or "应用" in title:
        return "application"
    skill_markers = ("运算", "法则", "乘方", "记数法", "近似数", "值", "合并", "去括号", "解一元一次方程")
    if any(marker in title for marker in skill_markers):
        return "skill"
    return "concept"


def topic_period(lesson: dict, all_lessons: list[dict]) -> tuple[int, int]:
    same = [item for item in all_lessons if item["source_section"] == lesson["source_section"]]
    return len(same), same.index(lesson) + 1


def stage(
    name: str,
    page: int,
    minutes: int,
    *,
    question: str,
    action: str,
    explanation: str,
    correction: str,
    student_action: str,
    expected: str,
    intent: str,
    example: str | None = None,
    practice: str | None = None,
    summary: str | None = None,
    figure: str | None = None,
) -> dict:
    result = {
        "stage": name,
        "page": page,
        "teacher": {
            "questions": [question],
            "actions": [action],
            "explanation": [explanation],
            "correction": [correction],
            "example": [example] if example else [],
            "practice": [practice] if practice else [],
            "summary": [summary] if summary else [],
        },
        "student": {
            "actions": [student_action],
            "expected_response": [expected],
        },
        "design_intent": [intent],
        "minutes": minutes,
    }
    if figure:
        result["figure"] = figure
    return result


def make_process(lesson: dict, content: dict, archetype: str) -> list[dict]:
    recipe = ARCHETYPE[archetype]
    names = recipe["stages"]
    times = recipe["times"]
    pages = [2, 2, 2, 3, 3, 3, 4, 4]
    hook_q, hook_a = content["hook"]
    core_q, core_a = content["core"]
    ex1_q, ex1_a = content["examples"][0]
    ex2_q, ex2_a = content["examples"][1]
    d1_q, d1_a = content["drills"][0]
    d2_q, d2_a = content["drills"][1]
    d3_q, d3_a = content["drills"][2]
    error_q, error_a = content["error"]
    app_q, app_a = content["application"]
    method = content["method"]
    rows = [
        stage(
            names[0], pages[0], times[0], question=hook_q,
            action="出示题目或情境，先让学生独立判断，再请两名学生说明依据。",
            explanation=hook_a,
            correction="若学生只报结论，追问基准、条件或运算依据，要求补成完整句。",
            student_action="独立观察或计算，圈出关键信息后口头说明。",
            expected=hook_a,
            intent="用具体问题激活先修经验，并明确本节需要解决的核心矛盾。",
            summary="把情境中的信息转化为数学对象和关系。",
        ),
        stage(
            names[1], pages[1], times[1], question=core_q,
            action="组织观察、比较或试算，板书学生给出的共同点，并逐项核对术语。",
            explanation=core_a,
            correction=f"用反例检查是否真正满足条件，提醒按“{method}”说明。",
            student_action="在图形、算式或表格中标注条件，与同桌归纳共同特征。",
            expected=core_a,
            intent="让核心结论由可检验的观察或运算形成，而不是直接记忆。",
            example=f"基础例题：{ex1_q} 规范解答：{ex1_a}",
            practice=f"即时练习：{d1_q} 答案：{d1_a}",
            summary=method,
            figure=content.get("figure"),
        ),
        stage(
            names[2], pages[2], times[2], question=f"解答“{ex2_q}”前应先确定什么？",
            action="教师按题意、依据、步骤和结论顺序板演；学生在每一步旁标注作用。",
            explanation=f"规范解答：{ex2_a}",
            correction="若一步跳到结论，要求补写关键关系或中间步骤，并用原题条件检验。",
            student_action="先独立完成，再与板演对照步骤、符号、单位或图形标记。",
            expected=f"能得到 {ex2_a}，并说出关键依据。",
            intent="用完整例题建立可模仿的书写顺序和检查方法。",
            example=f"变式例题：{ex2_q} 解答：{ex2_a}",
            practice=f"对应练习：{d2_q} 答案：{d2_a}",
            summary=f"解题流程：{method}。",
        ),
        stage(
            names[3], pages[3], times[3], question=app_q,
            action="要求学生先写条件关系或示意，再完成计算并解释结果；抽取两种方法比较。",
            explanation=app_a,
            correction="若答案脱离条件或单位，要求回到题干逐项对应并作合理性检查。",
            student_action="独立列式或作图，小组内互查条件、步骤和答语。",
            expected=app_a,
            intent="把核心方法迁移到不同表示方式或实际情境中。",
            example=f"应用例题：{app_q} 解答：{app_a}",
            practice=f"即时变式：{d3_q} 答案：{d3_a}",
            summary="先识别结构，再选择方法，最后解释结果。",
        ),
        stage(
            names[4], pages[4], times[4], question=error_q,
            action="展示错解，要求学生只圈第一处错误，写出依据后再完整订正。",
            explanation=error_a,
            correction="不接受只写“错”或只改答案；必须指出错误对象、正确规则和订正过程。",
            student_action="独立找错、写依据、完成订正，再与同桌互评理由是否完整。",
            expected=error_a,
            intent="利用典型错误暴露概念边界、符号习惯或条件遗漏。",
            example=f"易错辨析：{error_q}",
            practice=f"纠错要求：写出第一处错误，并按“{method}”重做。参考：{error_a}",
            summary="纠错顺序：定位错误、说明依据、规范订正、回题检验。",
        ),
        stage(
            names[5], pages[5], times[5], question="三道练习分别考查哪个要点，先做哪一道能最快暴露问题？",
            action=f"组织限时题组：①{d1_q} ②{d2_q} ③{d3_q}；完成后按答案自查。",
            explanation=f"答案：①{d1_a} ②{d2_a} ③{d3_a}",
            correction="正确率低于 70% 时暂停机动题，按核心方法示范一道，再让学生订正同类错题。",
            student_action="限时完成三题，按概念、步骤或应用给错因分类，并订正一题。",
            expected=f"能够依据“{method}”完成题组并说清错因。",
            intent="集中检查方法稳定性，并为反馈测试前的即时补救提供依据。",
            practice=f"机动题：{ex1_q} 学有余力者换一种方法说明；答案要点：{ex1_a}",
            summary=method,
        ),
        stage(
            names[6], pages[6], times[6], question="四道反馈题中，哪一题最能检验本节核心方法？",
            action=f"投放 10 分反馈卡：①2 分，{core_q} ②2 分，{d2_q} ③2 分，{error_q} ④4 分，{app_q}",
            explanation=f"参考答案：①{core_a} ②{d2_a} ③{error_a} ④{app_a}",
            correction="公布答案后学生自评并举牌统计：9 分及以上完成提高任务；7—8 分订正；7 分以下接受针对性补练。",
            student_action="独立完成，按答案自评；把错误标为概念、步骤、条件或表达问题。",
            expected="能完成四类题并用核心术语说明至少一道题的依据。",
            intent="用概念、技能、纠错和综合四类任务覆盖本节目标。",
            summary="达标标准：10 分制 9 分及以上完全达标，7—8 分基本达标，7 分以下补练。",
        ),
        stage(
            names[7], pages[7], times[7], question="本节研究了什么、关键步骤是什么、最容易错在哪里？",
            action="请学生各用一句话回答三个问题，教师据此补全板书并布置分层作业。",
            explanation=(
                f"A 组：①{d1_q} ②{d2_q} ③{d3_q} ④{error_q}；答案：①{d1_a} ②{d2_a} ③{d3_a} ④{error_a}。"
                f"B 组：①{ex2_q} ②{app_q}；答案要点：①{ex2_a} ②{app_a}。"
                f"C 组选做：围绕“{lesson['lesson_title']}”自编一道含易错条件的题并给出解答与检查方法。"
            ),
            correction="作业答案必须包含必要步骤或依据；只写结果的题次日先口述方法再补写。",
            student_action="说出一个结论、一个步骤和一个易错点，记录 A、B、C 三组作业。",
            expected=f"能用“{method}”概括本节方法，并知道如何自查。",
            intent="由学生完成结构化回顾，把课堂方法迁移到分层课后任务。",
            summary=f"核心方法：{method}。课后反思区域由任课教师课后填写。",
        ),
    ]
    return rows


def make_data(lesson: dict, all_lessons: list[dict], chapter_periods: dict[str, int]) -> dict:
    content = CONTENT[lesson["id"]]
    archetype = infer_archetype(lesson)
    recipe = ARCHETYPE[archetype]
    total_topic, current_topic = topic_period(lesson, all_lessons)
    scopes = lesson.get("content_scope", [])
    key = lesson["key_points"][0]
    difficulty = lesson["difficulties"][0]
    difficulty_display = {
        "-a^n 与 (-a)^n 的区别": r"$-a^n$ 与 $(-a)^n$ 的区别",
        "确定 a x 10^n 中 n 的值": r"确定 $a\times10^n$ 中 $n$ 的值",
    }.get(difficulty, difficulty)
    objectives = [
        f"说出并解释{scopes[0] if scopes else key}，使用本节规范术语表达。",
        f"按规范步骤完成{key}，并说明关键依据。",
        f"判断并订正与“{difficulty_display}”有关的常见错误。",
        f"在变式或实际情境中运用本节方法，完整写出过程和结论。",
    ]
    board_lines = [
        f"核心：{content['core'][1]}",
        f"方法：{content['method']}。",
        f"例题：{content['examples'][0][0]} 答：{content['examples'][0][1]}",
        f"易错：{content['error'][0]} 纠正：{content['error'][1]}",
        "检查：条件、依据、步骤、符号或单位逐项核对。",
    ]
    media = ["PPT", "黑板", "反馈卡"]
    if archetype == "geometry":
        media.extend(["直尺", "量角器或透明纸"])
    elif archetype in {"activity", "project"}:
        media.extend(["任务单", "小组记录表"])
    else:
        media.append("步骤卡")
    return {
        "meta": {
            "lesson_id": lesson["id"],
            "title": lesson["lesson_title"],
            "lesson_type": recipe["type"],
            "source_pages": lesson["source_pages"],
            "teaching_date": {"year": "", "month": "", "day": ""},
            "unit_total_periods": chapter_periods[lesson["chapter_id"]],
            "topic_total_periods": total_topic,
            "current_period": current_topic,
        },
        "objectives": objectives,
        "key_points": lesson["key_points"],
        "difficulties": [difficulty_display, *lesson["difficulties"][1:]],
        "methods": recipe["methods"],
        "media": media,
        "blackboard": {"title": lesson["lesson_title"], "lines": board_lines},
        "process": make_process(lesson, content, archetype),
        "reflection": {"mode": "blank", "text": ""},
    }


def write_data_files(manifest: dict) -> None:
    lessons = manifest["lessons"]
    chapters = {item["chapter_id"]: item["proposed_periods"] for item in manifest["chapters"]}
    expected = {lesson["id"] for lesson in lessons} - APPROVED_IDS
    if set(CONTENT) != expected:
        raise RuntimeError(f"content bank mismatch: missing={sorted(expected-set(CONTENT))} extra={sorted(set(CONTENT)-expected)}")
    for lesson in lessons:
        if lesson["id"] in APPROVED_IDS:
            continue
        data = make_data(lesson, lessons, chapters)
        source = ROOT / "lessons" / lesson["id"] / "lessonplan.yml"
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_text(
            yaml.safe_dump(data, allow_unicode=True, sort_keys=False, width=120),
            encoding="utf-8",
        )


def output_paths(lesson_id: str, title: str) -> dict[str, Path]:
    stem = f"{lesson_id}_{clean_filename(title)}_教案_v2"
    return {
        "pdf": OUTPUT_ROOT / "pdf" / f"{stem}.pdf",
        "tex": OUTPUT_ROOT / "tex" / f"{stem}.tex",
        "yaml": OUTPUT_ROOT / "yaml" / f"{lesson_id}_{clean_filename(title)}.yml",
        "png": OUTPUT_ROOT / "png" / lesson_id,
        "contact": OUTPUT_ROOT / "contact_sheets" / f"{lesson_id}_contact-sheet.png",
    }


def copy_approved(lesson: dict) -> None:
    lesson_id = lesson["id"]
    title = lesson["lesson_title"]
    paths = output_paths(lesson_id, title)
    source_pdf = ROOT / "dist" / "lessonplans_v2" / f"{lesson_id}_{title}_教案_v2.pdf"
    source_tex = ROOT / "build" / "lessonplans_v2" / lesson_id / "lessonplan.tex"
    source_yaml = ROOT / "lessons" / lesson_id / "lessonplan.yml"
    source_render = ROOT / "build" / "lessonplans_v2" / lesson_id
    for path in paths.values():
        path.parent.mkdir(parents=True, exist_ok=True)
    paths["png"].mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source_pdf, paths["pdf"])
    shutil.copyfile(source_tex, paths["tex"])
    shutil.copyfile(source_yaml, paths["yaml"])
    for page in source_render.glob("page-*.png"):
        shutil.copyfile(page, paths["png"] / page.name)
    shutil.copyfile(source_render / "contact-sheet.png", paths["contact"])


def build_one(lesson: dict, style: dict) -> dict:
    lesson_id = lesson["id"]
    title = lesson["lesson_title"]
    source_yml = ROOT / "lessons" / lesson_id / "lessonplan.yml"
    data = yaml.safe_load(source_yml.read_text(encoding="utf-8"))
    errors = frozen.validate_data(lesson_id, data, style)
    if errors:
        raise RuntimeError("; ".join(errors))
    output_dir = BUILD_ROOT / lesson_id
    output_dir.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source_yml, output_dir / "lessonplan.yml")
    tex_path = output_dir / "lessonplan.tex"
    tex_path.write_text(frozen.document(data), encoding="utf-8")
    ok, elapsed, log = frozen.compile_tex(tex_path, output_dir)
    pdf_path = output_dir / "lessonplan.pdf"
    if not ok or not pdf_path.exists():
        raise RuntimeError(f"compile failed; see {output_dir / 'lessonplan.compile.log'}")
    info = frozen.pdf_info(pdf_path)
    warnings = len(re.findall(r"Warning", log))
    overfull = len(re.findall(r"Overfull \\hbox", log))
    errors_count = len(re.findall(r"LaTeX Error|Fatal error|Emergency stop|Undefined control sequence", log))
    a4 = abs(info["width"] - 595.28) < 1.0 and abs(info["height"] - 841.89) < 1.0
    if info["pages"] != 4 or not a4 or overfull or errors_count:
        raise RuntimeError(
            f"layout/log failure pages={info['pages']} a4={a4} overfull={overfull} errors={errors_count}"
        )
    frozen.render_pdf(pdf_path, output_dir)
    paths = output_paths(lesson_id, title)
    for path in paths.values():
        path.parent.mkdir(parents=True, exist_ok=True)
    paths["png"].mkdir(parents=True, exist_ok=True)
    shutil.copyfile(pdf_path, paths["pdf"])
    shutil.copyfile(tex_path, paths["tex"])
    shutil.copyfile(source_yml, paths["yaml"])
    for page in output_dir.glob("page-*.png"):
        shutil.copyfile(page, paths["png"] / page.name)
    shutil.copyfile(output_dir / "contact-sheet.png", paths["contact"])
    return {
        "lesson_id": lesson_id,
        "pages": info["pages"],
        "seconds": round(elapsed, 2),
        "warnings": warnings,
        "overfull": overfull,
        "errors": errors_count,
    }


def make_batch_sheets(lessons: list[dict], batch_size: int = 10) -> None:
    target = OUTPUT_ROOT / "contact_sheets" / "batches"
    target.mkdir(parents=True, exist_ok=True)
    for stale in target.glob("batch-*.png"):
        stale.unlink()
    for batch_index, start in enumerate(range(0, len(lessons), batch_size), 1):
        subset = lessons[start : start + batch_size]
        panels = []
        for lesson in subset:
            source = output_paths(lesson["id"], lesson["lesson_title"])["contact"]
            image = Image.open(source).convert("RGB")
            image.thumbnail((860, 330))
            canvas = Image.new("RGB", (880, 370), "white")
            canvas.paste(image, ((880 - image.width) // 2, 28))
            ImageDraw.Draw(canvas).text((12, 7), f"{lesson['id']} {lesson['lesson_title']}", fill="black")
            panels.append(ImageOps.expand(canvas, border=2, fill="#777777"))
        sheet = Image.new("RGB", (1764, ((len(panels) + 1) // 2) * 374), "#d0d0d0")
        for index, panel in enumerate(panels):
            sheet.paste(panel, ((index % 2) * 882, (index // 2) * 374))
        sheet.save(target / f"batch-{batch_index:02d}.png")


def count_exercises(data: dict) -> int:
    count = 0
    for item in data["process"]:
        count += len(item["teacher"].get("example", []))
        count += len(item["teacher"].get("practice", []))
        if item["stage"] in {"当堂检测", "反馈评价", "成果检测"}:
            count += 4
    return count


def assemble_manifest(manifest: dict) -> None:
    rows = []
    for lesson in manifest["lessons"]:
        paths = output_paths(lesson["id"], lesson["lesson_title"])
        if not all(paths[key].exists() for key in ("pdf", "tex", "yaml", "contact")):
            continue
        data = yaml.safe_load(paths["yaml"].read_text(encoding="utf-8"))
        info = frozen.pdf_info(paths["pdf"])
        rows.append(
            {
                "lesson_id": lesson["id"],
                "chapter": lesson["chapter_title"],
                "lesson_title": lesson["lesson_title"],
                "lesson_type": data["meta"]["lesson_type"],
                "source_yaml": paths["yaml"].relative_to(ROOT).as_posix(),
                "source_tex": paths["tex"].relative_to(ROOT).as_posix(),
                "output_pdf": paths["pdf"].relative_to(ROOT).as_posix(),
                "page_count": info["pages"],
                "total_minutes": sum(item["minutes"] for item in data["process"]),
                "figure_count": sum(bool(item.get("figure")) for item in data["process"]),
                "exercise_count": count_exercises(data),
                "status": "approved" if lesson["id"] in APPROVED_IDS else "generated",
                "sha256": sha256(paths["pdf"]),
            }
        )
    manifest_dir = OUTPUT_ROOT / "manifests"
    manifest_dir.mkdir(parents=True, exist_ok=True)
    csv_path = manifest_dir / "lessonplan_manifest.csv"
    if rows:
        with csv_path.open("w", encoding="utf-8-sig", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
    (manifest_dir / "lessonplan_manifest.json").write_text(
        json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    sums = [f"{row['sha256']}  {row['output_pdf']}" for row in rows]
    (manifest_dir / "sha256sums.txt").write_text("\n".join(sums) + "\n", encoding="utf-8")
    make_batch_sheets(manifest["lessons"])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prepare-only", action="store_true")
    parser.add_argument("--ids", nargs="*")
    parser.add_argument("--copy-approved", action="store_true")
    parser.add_argument("--assemble", action="store_true")
    args = parser.parse_args()

    ensure_frozen()
    manifest = yaml.safe_load(MANIFEST_PATH.read_text(encoding="utf-8"))
    style = yaml.safe_load(STYLE_PATH.read_text(encoding="utf-8"))
    write_data_files(manifest)
    if args.prepare_only:
        print(f"[OK] prepared {len(CONTENT)} lesson YAML files")
        return 0

    selected = set(args.ids or [])
    failed = False
    for lesson in manifest["lessons"]:
        lesson_id = lesson["id"]
        if lesson_id in APPROVED_IDS:
            if args.copy_approved:
                copy_approved(lesson)
                print(f"[OK] {lesson_id} approved copy preserved")
            continue
        if selected and lesson_id not in selected:
            continue
        try:
            result = build_one(lesson, style)
            print(
                f"[OK] {lesson_id} pages={result['pages']} seconds={result['seconds']} "
                f"warnings={result['warnings']} overfull={result['overfull']} errors={result['errors']}"
            )
        except Exception as exc:
            failed = True
            print(f"[FAIL] {lesson_id}: {exc}")
    if args.assemble:
        assemble_manifest(manifest)
        print("[OK] manifests and batch contact sheets assembled")
    ensure_frozen()
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
