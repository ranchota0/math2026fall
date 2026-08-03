"""Create a concise, page-by-page content inventory from the Grade 7B PDF audit."""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "build" / "7b_audit" / "textbook" / "textbook_pages.json"
OUTPUT = ROOT / "build" / "7b_audit" / "textbook" / "page_inventory.md"

KEY_RE = re.compile(
    r"(?:^\d+\.\d+(?:\.\d+)?\s|^第[七八九十百]+章|^例\s*\d*\b|"
    r"练习|习题\s*\d*|数学活动|小结|复习题|观察与猜想|阅读与思考|"
    r"探究与发现|信息技术应用|图说数学史|综合与实践)"
)
HEADER_RE = re.compile(r"^(?:\d+\s*)?第[七八九十百]+章|仅供个人学习使用")


def cleaned_lines(text: str) -> list[str]:
    rows = []
    for line in text.splitlines():
        value = " ".join(line.split())
        if not value or HEADER_RE.search(value) or value.startswith("版权"):
            continue
        rows.append(value)
    return rows


def main() -> int:
    data = json.loads(SOURCE.read_text(encoding="utf-8"))
    lines = ["# 七下教材逐页内容索引", ""]
    for page in data["pages"]:
        printed = page["printed_page"]
        if printed is None or printed < 1:
            continue
        rows = cleaned_lines(page["text"])
        hits = [row for row in rows if KEY_RE.search(row)]
        lead = " / ".join(rows[:4])
        lines.append(f"## 教材第 {printed} 页（PDF 第 {page['physical_page']} 页）")
        lines.append("")
        lines.append(f"- 页首摘要：{lead[:360]}")
        if hits:
            lines.append("- 栏目标记：")
            for hit in hits[:20]:
                lines.append(f"  - {hit[:360]}")
        lines.append("")
    OUTPUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"[OK] output={OUTPUT} pages={sum(p['printed_page'] is not None for p in data['pages'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
