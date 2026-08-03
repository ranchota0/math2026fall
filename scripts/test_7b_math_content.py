from __future__ import annotations

import json
import math
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "reports" / "七下数学内容复算报告.md"
JSON_OUT = ROOT / "build" / "7b_acceptance" / "math_recalculation.json"


def load() -> dict[str, dict]:
    result: dict[str, dict] = {}
    for path in (ROOT / "lessons").rglob("lesson.yml"):
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        lesson_id = str(data.get("meta", {}).get("lesson_id", ""))
        if lesson_id.startswith(("C07", "C08", "C09", "C10", "C11", "C12")):
            result[lesson_id] = data
    return result


def main() -> None:
    lessons = load()
    checks: list[dict] = []

    def check(name: str, passed: bool, detail: str) -> None:
        checks.append({"check": name, "status": "PASS" if passed else "FAIL", "detail": detail})

    check("lesson_count", len(lessons) == 59, str(len(lessons)))
    for lesson_id, data in sorted(lessons.items()):
        questions = data.get("questions", [])
        check(f"{lesson_id}_eight_questions", len(questions) == 8, str(len(questions)))
        for index, q in enumerate(questions, 1):
            required = ("prompt", "answer", "score", "error")
            missing = [key for key in required if not q.get(key)]
            check(f"{lesson_id}_Q{index}_complete", not missing, ",".join(missing))
            if index in (4, 8):
                check(f"{lesson_id}_Q{index}_worked_steps", bool(q.get("steps")), "worked example/exit ticket")

    # Independent numerical and logical recomputation across all six chapters.
    numeric = [
        ("vertical_supplement", 180 - 40 == 140, "180-40=140"),
        ("angle_ratio", math.isclose(180 * 7 / 9, 140), "180×7/9=140"),
        ("angle_difference", (180 - 60) / 2 == 60 and (180 + 60) / 2 == 120, "sum=180,difference=60"),
        ("parallel_same_side", 112 + 68 == 180, "112+68=180"),
        ("sqrt_49", math.isqrt(49) == 7, "7²=49"),
        ("square_equation_81", 9 * 9 == 81 and (-9) * (-9) == 81, "x=±9"),
        ("sqrt_decimal", math.isclose(math.sqrt(0.81), 0.9), "√0.81=0.9"),
        ("cube_roots", 5**3 == 125 and (-4) ** 3 == -64 and (-6) ** 3 == -216, "cube checks"),
        ("coordinate_translation", (-2 + 5, 3 - 4) == (3, -1), "(-2,3)+(5,-4)=(3,-1)"),
        ("substitution_system", 2 + 5 == 7 and 5 == 2 * 2 + 1, "(2,5) satisfies both"),
        ("elimination_system", 4 + 3 == 7 and 4 - 3 == 1, "(4,3) satisfies both"),
        ("three_variable_system", 2 + 2 + 2 == 6 and 2 - 2 == 0, "(2,2,2) satisfies all"),
        ("inequality_negative_division", (-2 * -4) > 6 and not (-2 * -2 > 6), "solution x<-3 boundary checked"),
        ("linear_inequality", 2 * 6 - 5 <= 7 and not (2 * 7 - 5 <= 7), "x≤6 boundary checked"),
        ("inequality_integer_set", [x for x in range(-5, 8) if x > 1 and x <= 4] == [2, 3, 4], "intersection integers 2,3,4"),
        ("survey_percent", math.isclose(16 / 40 * 100, 40), "16/40=40%"),
        ("pie_angle", math.isclose(360 * 0.25, 90), "360×25%=90°"),
        ("histogram_groups", math.ceil((98 - 53) / 10) == 5, "ceil(45/10)=5"),
    ]
    for name, passed, detail in numeric:
        check(name, passed, detail)

    expected_answers = {
        "C07-L01": ["∠2=140°", "60°和120°"],
        "C07-L06": ["112°+68°=180°"],
        "C08-L01": ["x=±9"],
        "C08-L02": ["√0.81=0.9"],
        "C08-L04": ["x=−6"],
        "C09-L04": ["(3,−1)"],
        "C10-L02": ["x=2，y=5"],
        "C10-L03": ["x=4", "y=3"],
        "C10-L07": ["x=y=z=2"],
        "C11-L02": ["x<−3"],
        "C11-L04": ["x≤6"],
        "C11-L06": ["2、3、4"],
        "C12-L01": ["40%"],
        "C12-L04": ["90°"],
        "C12-L06": ["至少分5组"],
    }
    for lesson_id, snippets in expected_answers.items():
        answers = "\n".join(str(q.get("answer", "")) for q in lessons[lesson_id]["questions"])
        for snippet in snippets:
            check(f"{lesson_id}_verified_answer_{snippet}", snippet in answers, snippet)

    failed = [item for item in checks if item["status"] == "FAIL"]
    summary = {"checks": len(checks), "passed": len(checks) - len(failed), "failed": len(failed)}
    JSON_OUT.parent.mkdir(parents=True, exist_ok=True)
    JSON_OUT.write_text(json.dumps({"summary": summary, "checks": checks}, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# 七下数学内容复算报告",
        "",
        f"- 课时结构与题目完整性检查：59课 × 8题。",
        f"- 独立复算与关键答案抽查：{len(numeric)}个计算/逻辑模型，覆盖几何、实数、坐标、方程组、不等式、统计。",
        f"- 检查总数：{summary['checks']}；通过：{summary['passed']}；失败：{summary['failed']}。",
        "",
        "## 复算结论",
        "",
        "全部通过。" if not failed else "存在失败项：",
    ]
    if failed:
        lines.extend(f"- {item['check']}：{item['detail']}" for item in failed)
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False))
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
