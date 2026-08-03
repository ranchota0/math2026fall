"""Validate and montage every temporary gold-template teaching-design preview."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "build" / "7b_gold_template_migration"
PDF_DIR = BASE / "preview_pdf"
PNG_DIR = BASE / "preview_png"
MONTAGE_DIR = BASE / "chapter_montages"


def image_metrics(path: Path) -> dict:
    image = Image.open(path).convert("L")
    width, height = image.size
    pixels = image.load()
    dark = []
    for y in range(height):
        for x in range(width):
            if pixels[x, y] < 245:
                dark.append((x, y))
    if dark:
        xs = [item[0] for item in dark]
        ys = [item[1] for item in dark]
        bbox = [min(xs), min(ys), max(xs), max(ys)]
    else:
        bbox = None
    border_dark = 0
    border_total = 0
    margin = 8
    for y in range(height):
        for x in range(width):
            if x < margin or y < margin or x >= width - margin or y >= height - margin:
                border_total += 1
                if pixels[x, y] < 245:
                    border_dark += 1
    return {
        "size": [width, height],
        "dark_fraction": len(dark) / (width * height),
        "bbox": bbox,
        "border_dark_fraction": border_dark / border_total,
    }


def create_montage(chapter: str, lesson_dirs: list[Path]) -> Path:
    thumb_w, thumb_h = 238, 337
    gap, label_h = 14, 26
    columns = 8
    items = []
    for lesson_dir in lesson_dirs:
        for page in sorted(lesson_dir.glob("page-*.png")):
            items.append((lesson_dir.name, page))
    rows = (len(items) + columns - 1) // columns
    canvas = Image.new("RGB", (columns * (thumb_w + gap) + gap, rows * (thumb_h + label_h + gap) + gap), "white")
    draw = ImageDraw.Draw(canvas)
    font = ImageFont.truetype(r"C:\Windows\Fonts\arial.ttf", 14)
    for index, (lesson_id, page) in enumerate(items):
        col, row = index % columns, index // columns
        x = gap + col * (thumb_w + gap)
        y = gap + row * (thumb_h + label_h + gap)
        image = Image.open(page).convert("RGB")
        image.thumbnail((thumb_w, thumb_h))
        canvas.paste(image, (x, y))
        draw.text((x, y + thumb_h + 3), f"{lesson_id}-{page.stem}", fill="black", font=font)
    MONTAGE_DIR.mkdir(parents=True, exist_ok=True)
    output = MONTAGE_DIR / f"{chapter}.png"
    canvas.save(output)
    return output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--final", action="store_true", help="Validate actual DOCX-exported final PDFs")
    args = parser.parse_args()
    png_dir = BASE / "final_pdf_png" if args.final else PNG_DIR
    montage_dir = BASE / "final_chapter_montages" if args.final else MONTAGE_DIR
    if args.final:
        export_records = json.loads((BASE / "pdf_export_validation.json").read_text(encoding="utf-8"))
        pdf_records = [(item["lesson_id"], Path(item["final_pdf"])) for item in export_records]
    else:
        pdf_records = [(pdf.stem, pdf) for pdf in sorted(PDF_DIR.glob("C??-L??.pdf"))]
    results = []
    failures = []
    for lesson_id, pdf in pdf_records:
        reader = PdfReader(pdf)
        lesson = {"lesson_id": lesson_id, "pdf": str(pdf), "pages": len(reader.pages), "page_checks": []}
        if len(reader.pages) != 4:
            failures.append(f"{lesson_id}: pdf_pages={len(reader.pages)}")
        lesson_dir = png_dir / lesson_id
        images = sorted(lesson_dir.glob("page-*.png"))
        if len(images) != 4:
            failures.append(f"{lesson_id}: png_pages={len(images)}")
        for index, page in enumerate(reader.pages, start=1):
            width = float(page.mediabox.width)
            height = float(page.mediabox.height)
            text = page.extract_text() or ""
            pdf_ok = abs(width - 595.28) < 1.0 and abs(height - 841.89) < 1.0 and len(text.strip()) > 120
            if not pdf_ok:
                failures.append(f"{lesson_id}: page{index} pdf geometry/text")
        for image in images:
            metrics = image_metrics(image)
            bbox = metrics["bbox"] or [0, 0, 0, 0]
            image_ok = (
                metrics["size"][0] > 700 and metrics["size"][1] > 1000
                and 0.015 < metrics["dark_fraction"] < 0.35
                and metrics["border_dark_fraction"] == 0
                and bbox[0] >= 45 and bbox[1] >= 35
                and bbox[2] <= metrics["size"][0] - 45 and bbox[3] <= metrics["size"][1] - 35
            )
            if not image_ok:
                failures.append(f"{lesson_id}: {image.name} {metrics}")
            lesson["page_checks"].append({"image": str(image), "ok": image_ok, **metrics})
        results.append(lesson)

    montages = []
    for chapter in ("C07", "C08", "C09", "C10", "C11", "C12"):
        dirs = sorted(path for path in png_dir.glob(f"{chapter}-L??") if path.is_dir())
        original_montage_dir = MONTAGE_DIR
        globals()["MONTAGE_DIR"] = montage_dir
        montages.append(str(create_montage(chapter, dirs)))
        globals()["MONTAGE_DIR"] = original_montage_dir
    report = {
        "lessons": len(results),
        "pdf_pages": sum(item["pages"] for item in results),
        "png_pages": sum(len(item["page_checks"]) for item in results),
        "failures": failures,
        "montages": montages,
        "results": results,
    }
    report_name = "final_pdf_validation.json" if args.final else "preview_validation.json"
    (BASE / report_name).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({key: report[key] for key in ("lessons", "pdf_pages", "png_pages", "failures", "montages")}, ensure_ascii=False))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
