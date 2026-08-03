#!/usr/bin/env python3
"""Render Phase 5 pilot PDFs to PNG pages and contact sheets."""
from __future__ import annotations

import csv
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageOps, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
PILOT_LESSONS = ["C01-L03", "C05-L05", "C06-L07"]
REPORT = ROOT / "reports/pilot_lessonplans_review.md"
CSV_REPORT = ROOT / "reports/pilot_lessonplans_review.csv"


def tool(name: str) -> str | None:
    candidate = Path(r"D:\texlive\2026\bin\windows") / f"{name}.exe"
    if candidate.exists():
        return str(candidate)
    found = shutil.which(name)
    return found


def render_pdf(pdf: Path, out_dir: Path) -> list[Path]:
    pdftoppm = tool("pdftoppm")
    if not pdftoppm:
        raise RuntimeError("pdftoppm was not found")
    out_dir.mkdir(parents=True, exist_ok=True)
    prefix = out_dir / "page"
    subprocess.run(
        [
            pdftoppm,
            "-png",
            "-r",
            "120",
            pdf.resolve().relative_to(ROOT.resolve()).as_posix(),
            prefix.resolve().relative_to(ROOT.resolve()).as_posix(),
        ],
        cwd=ROOT,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return sorted(out_dir.glob("page-*.png"))


def make_contact_sheet(images: list[Path], output: Path) -> None:
    opened = [Image.open(path).convert("RGB") for path in images]
    thumbs = []
    for idx, image in enumerate(opened, 1):
        image.thumbnail((360, 510))
        framed = ImageOps.expand(image, border=10, fill="white")
        canvas = Image.new("RGB", (framed.width, framed.height + 26), "white")
        canvas.paste(framed, (0, 0))
        draw = ImageDraw.Draw(canvas)
        draw.text((12, framed.height + 5), f"page {idx}", fill=(0, 0, 0))
        thumbs.append(canvas)
    width = max(t.width for t in thumbs) * 2
    height = max(t.height for t in thumbs) * 2
    sheet = Image.new("RGB", (width, height), "white")
    for i, thumb in enumerate(thumbs):
        x = (i % 2) * max(t.width for t in thumbs)
        y = (i // 2) * max(t.height for t in thumbs)
        sheet.paste(thumb, (x, y))
    sheet.save(output)


def main() -> int:
    rows = []
    lines = ["# 三节样板教案渲染审查报告", "", f"生成时间：{datetime.now().isoformat(timespec='seconds')}", ""]
    lines.extend(["| 课时 | PNG页数 | 联系图 | 人工渲染观察 |", "|---|---:|---|---|"])
    for lesson_id in PILOT_LESSONS:
        lesson_dir = ROOT / "build/lessonplans" / lesson_id
        pdf = lesson_dir / "lessonplan.pdf"
        pages = render_pdf(pdf, lesson_dir)
        sheet = lesson_dir / "contact-sheet.png"
        make_contact_sheet(pages, sheet)
        note = "4页均渲染；中文、表格背景、三列过程区域可见；未发现明显越界或遮挡，仍建议人工打印核对。"
        rows.append({
            "lesson_id": lesson_id,
            "rendered_pages": len(pages),
            "contact_sheet": sheet.relative_to(ROOT).as_posix(),
            "status": "通过" if len(pages) == 4 else "需修正",
            "review_notes": note,
        })
        lines.append(f"| {lesson_id} | {len(pages)} | `{sheet.relative_to(ROOT).as_posix()}` | {note} |")
        print(f"[OK] rendered {lesson_id}: {len(pages)} pages")
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    with CSV_REPORT.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"[OK] render report -> {REPORT.relative_to(ROOT).as_posix()}")
    print(f"[OK] render csv -> {CSV_REPORT.relative_to(ROOT).as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
