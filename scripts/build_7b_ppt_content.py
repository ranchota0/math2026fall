"""Build compact 15-slide content plans from structured lesson sources."""

from __future__ import annotations

import json
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "build" / "7b_batch" / "ppt_content.json"


def short(text: str, limit: int) -> str:
    text = " ".join(str(text).split())
    return text if len(text) <= limit else text[: limit - 1] + "…"


def lesson_sources() -> list[tuple[Path, dict]]:
    found: list[tuple[Path, dict]] = []
    for source in (ROOT / "lessons").rglob("lesson.yml"):
        try:
            data = yaml.safe_load(source.read_text(encoding="utf-8"))
        except Exception:
            continue
        lid = str((data.get("meta") or {}).get("lesson_id", ""))
        if lid.startswith(("C07-", "C08-", "C09-", "C10-", "C11-", "C12-")):
            found.append((source, data))
    return sorted(found, key=lambda item: item[1]["meta"]["lesson_id"])


def content_for(source: Path, data: dict) -> dict:
    meta = data["meta"]
    q = data["questions"]
    concepts = data["worksheet"]["concept_teacher"] if "worksheet" in data else [
        "邻补角：有公共边，另两边互为反向延长线，和为180°。",
        "对顶角：有公共顶点，两边分别互为反向延长线；对顶角相等。",
    ]
    core = [line.split("：", 1)[0] for line in concepts]
    while len(core) < 3:
        core.append("关键方法")
    objectives = data["objectives"]
    while len(objectives) < 4:
        objectives.append("完成课堂任务并根据评分点自评。")
    misconceptions = data["student_analysis"]["misconceptions"]
    while len(misconceptions) < 4:
        misconceptions.append("只写结果，没有写过程、依据或检验。")
    chapter_id = meta["lesson_id"].split("-", 1)[0]
    chapter_number = chapter_id[1:]
    lesson_root = source.parents[1]
    pages = meta["printed_pages"]
    title = meta["title"]
    section = meta["section"]
    example_label = q[3]["prompt"].split("：", 1)[0]

    slides = [
        [f"{section} {title}", meta["chapter"], f"七年级数学下册 · 教材印刷页{pages} · {meta['lesson_type']}"],
        [
            "本节课，我们要解决什么？",
            "01 认识对象：提取与表达", short(objectives[0], 63),
            "02 探究规律：观察与验证", short(objectives[1], 63),
            "03 规范应用：方法与检验", short(objectives[2], 63),
            "04 反思评价：表达与订正", short(objectives[3], 63),
        ],
        [
            "问题从哪里来？",
            f"教材情境\n对应印刷页{pages}。先读图、读表或读题，圈出已知和所求。",
            f"已有基础\n调用{short(data['student_analysis']['foundation'], 48)}",
            f"核心任务\n聚焦{short('、'.join(core), 45)}，不急于抄结论。",
            "课堂路径\n观察/阅读 → 自主记录 → 合作验证 → 例练检测。",
        ],
        [
            f"旧知回顾：{short(q[0]['prompt'].split('：', 1)[0], 18)}",
            "01 回忆规则", short(q[0]["prompt"], 72),
            "02 独立作答", "先写定义、性质、式子、图形或数据关系，再与同桌核对。",
            "03 连接新知", short(q[0]["answer"], 78),
        ],
        [
            "自主探究：观察、猜想与验证",
            f"01 阅读与标记\n{short(q[1]['prompt'], 78)}",
            f"02 小组探究\n{short(q[2]['prompt'], 78)}",
            "03 记录证据\n写清现象、猜想、验证方法和结论；暂不看参考答案。",
            "图示：把条件、对象和关系组织在同一视图中",
            f"🔍 交流要求\n围绕“{short(data['key_point'], 38)}”说明理由；同伴只追问条件和依据。",
        ],
        [
            f"概念一：{core[0]}",
            "01 教材表述", short(concepts[0], 105),
            "02 成立条件", "把定义中的对象、条件、表示和结论分开记录；缺少条件时不能直接使用。",
            "03 规范表达", "用数学符号、图形、式子、表格或完整语句表达，并标注单位和依据。",
        ],
        [
            f"概念二：{core[1]}",
            "01 核心含义", short(concepts[1] if len(concepts) > 1 else data["key_point"], 105),
            "02 与概念一的联系", "先辨对象和条件，再比较两者的作用、方向或适用范围。",
            "03 易错提醒", short(data["worksheet"].get("notice", data["difficulty"]), 95),
        ],
        [
            "为什么这样做？",
            "01 条件先行", short(q[2]["prompt"], 96),
            "已知与对象\n逐项核对题目条件",
            "方法与依据\n选择定义、性质或步骤",
            "结论与检验\n回到题意复核",
            "02 完成验证", short(q[2]["answer"], 125),
            f"💡 方法归纳\n{short(data['worksheet'].get('method', ''), 125)}",
        ],
        [
            "这些“陷阱”要避开！",
            "01 条件不完整", f"❌ {short(misconceptions[0], 54)}\n✅ 回到定义逐项核对对象和条件。",
            "02 相近概念混淆", f"❌ {short(misconceptions[1], 54)}\n✅ 比较条件、结论和使用方向。",
            "03 只写结果", f"❌ {short(misconceptions[2], 54)}\n✅ 补全过程、依据和必要单位。",
            "04 不作检验", f"❌ {short(misconceptions[3], 54)}\n✅ 代回、逆算、看图或用数据复核。",
        ],
        [
            f"教材例题：{short(example_label, 22)}",
            f"01 题目\n{short(q[3]['prompt'], 80)}",
            "02 先独立完成\n圈出条件和所求；选择方法；暂不显示完整答案。",
            f"03 思考顺序\n1. 提取条件；2. 选用{short(data['key_point'], 22)}；3. 写依据并检验。",
            f"教材印刷页{pages}：先思考，再对照规范解答",
            "🔍 课堂约定\n先写自己的第一步；同桌只检查条件和方法，不直接报答案。",
        ],
        [
            "例题：规范解答",
            "01 第一步：审条件", short(q[3]["steps"][0] if q[3]["steps"] else "提取已知和所求", 80),
            f"关系/规则\n{short(q[3]['steps'][1] if len(q[3]['steps']) > 1 else data['key_point'], 44)}",
            f"过程/表达\n{short(q[3]['steps'][2] if len(q[3]['steps']) > 2 else '规范完成', 44)}",
            "结论/检验\n结果必须满足全部条件并回到问题。",
            "02 完整解答", short(q[3]["answer"], 165),
            f"💡 易错纠正\n{short(q[3]['error'], 125)}",
        ],
        [
            "分层练习：基础与变式",
            "01 Q5 · 基础辨析", short(q[4]["prompt"], 90),
            "02 Q6 · 变式练习", short(q[5]["prompt"], 90),
            "03 同桌互查 · 说清依据", "① 条件是否完整；② 方法是否匹配；③ 过程是否规范；④ 是否检验。",
        ],
        [
            "变式提升：迁移方法",
            f"01 改变条件\n{short(q[5]['prompt'], 82)}",
            "02 保持方法\n说明改变后为什么仍能使用原方法，不能只照抄原结果。",
            f"03 评价标准\n{short(q[5]['answer'], 82)}",
            "图示：把新条件与原方法逐项对应",
            f"🔍 方法迁移\n{short(data['worksheet'].get('method', ''), 125)}",
        ],
        [
            "当堂检测：独立完成",
            "01 Q7 · 纠错", short(q[6]["prompt"], 95),
            "02 Q8 · 检测", short(q[7]["prompt"], 95),
            "03 自我检查", "① 条件对象是否找全？\n② 方法与依据是否匹配？\n③ 结果是否检验？\n④ 书写和单位是否规范？",
        ],
        [
            "课堂小结与分层作业",
            "01 课堂小结", short(data["worksheet"].get("summary", ""), 165),
            "02 分层作业", short(f"基础：{data['homework']['basic'][0]}\n提升：{data['homework']['advanced'][0]}\n自拟：围绕本课编一道题并交换解答。", 175),
            f"💡 课后自评\n我能否：①准确表达{core[0]}；②运用{short(data['key_point'], 28)}；③写清依据并检验？选择“会 / 需复习 / 需帮助”。",
        ],
    ]
    notes = [
        f"从教材印刷页{pages}进入《{title}》。说明本课在{meta['chapter']}中的位置。\n[Sources]\n- 人教版《义务教育教科书·数学七年级下册》，印刷页{pages}。",
        "请学生默读目标，圈出“说出、说明、解决、检验”等可观察动词；课末按同一目标自评。",
        "先让学生读图、读表或读题，不提前给结论。追问：对象是什么，条件是什么，要解决什么？",
        "组织Q1独立作答。旧知只回顾本课真正需要的部分，出现条件缺失时用反例纠正。",
        "布置Q2、Q3。教师巡视时只问现象、猜想和证据，给学生保留形成结论的过程。",
        f"形成第一个核心概念：{core[0]}。要求学生标出对象、条件、表示和作用。",
        f"形成第二个核心概念或方法：{core[1]}。与前一概念对比，避免相近知识混淆。",
        "把探究记录整理为完整的条件—方法—结论链，强调结论来自证据而不是直觉。",
        "逐条辨析易错点。要求学生说出错误发生在哪个条件、步骤或使用方向。",
        f"呈现Q4，保留独立思考时间。题型对应教材印刷页{pages}的例题或典型任务。\n[Sources]\n- 人教版《义务教育教科书·数学七年级下册》，印刷页{pages}。",
        "按审条件—选方法—规范表达—检验的顺序讲评Q4，评分时过程与依据同样计分。",
        "完成Q5、Q6。Q5用于基础辨析，Q6要求改变条件后仍能解释方法为何适用。",
        "展示一份变式答案，依据评价标准互评；重点检查是否照抄原结果。",
        "Q7、Q8独立完成，不在本页呈现答案。教师记录共性错误，作为下节课反馈依据。",
        "回扣学习目标，布置基础、提升和自拟任务；请学生填写学案自评并写一条仍需帮助的问题。",
    ]
    return {
        "lessonId": meta["lesson_id"],
        "lessonRoot": str(lesson_root),
        "outputPptx": str(lesson_root / "PPT" / f"{meta['file_prefix']}_课堂教学.pptx"),
        "chapterId": chapter_id,
        "slides": slides,
        "notes": notes,
    }


def main() -> int:
    lessons = [content_for(source, data) for source, data in lesson_sources() if data["meta"]["lesson_id"] != "C07-L01"]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"lessons": lessons}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[OK] ppt_content_lessons={len(lessons)} out={OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
