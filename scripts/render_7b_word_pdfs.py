from __future__ import annotations

import argparse
import re
from pathlib import Path

import pypdfium2 as pdfium
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]


def safe_name(path: Path) -> str:
    text = "__".join(path.parts[-4:]).replace(".pdf", "")
    return re.sub(r'[<>:"/\\|?*]', "_", text)


def make_contact_sheet(images: list[Path], output: Path, label: str) -> None:
    thumbs: list[Image.Image] = []
    for image_path in images:
        image = Image.open(image_path).convert("RGB")
        image.thumbnail((360, 510), Image.Resampling.LANCZOS)
        thumbs.append(image.copy())
    cols = min(4, max(1, len(thumbs)))
    rows = (len(thumbs) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * 380, rows * 540 + 44), "white")
    draw = ImageDraw.Draw(sheet)
    draw.text((12, 12), label, fill="#222222", font=ImageFont.load_default())
    for index, image in enumerate(thumbs):
        x = (index % cols) * 380 + (380 - image.width) // 2
        y = (index // cols) * 540 + 44
        sheet.paste(image, (x, y))
        draw.rectangle((x, y, x + image.width - 1, y + image.height - 1), outline="#999999")
    output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output, quality=92)


def render_pdf(pdf_path: Path, out_root: Path, scale: float) -> tuple[int, Path]:
    out_dir = out_root / safe_name(pdf_path)
    out_dir.mkdir(parents=True, exist_ok=True)
    document = pdfium.PdfDocument(str(pdf_path))
    pages: list[Path] = []
    for page_index in range(len(document)):
        target = out_dir / f"page-{page_index + 1:02d}.png"
        if not target.exists():
            page = document[page_index]
            bitmap = page.render(scale=scale)
            bitmap.to_pil().convert("RGB").save(target, optimize=True)
        pages.append(target)
    contact = out_dir / "contact_sheet.png"
    make_contact_sheet(pages, contact, str(pdf_path.relative_to(ROOT)))
    return len(pages), contact


def main() -> None:
    parser = argparse.ArgumentParser(description="Render all Grade 7B Word-exported PDFs.")
    parser.add_argument("--output", default="build/7b_rendered_word")
    parser.add_argument("--scale", type=float, default=1.25)
    parser.add_argument("--skip-existing", action="store_true")
    args = parser.parse_args()

    output = ROOT / args.output
    pdfs = sorted(
        p
        for p in (ROOT / "lessons").rglob("*.pdf")
        if any(token in p.name for token in ("_教学设计", "_学生学案", "_学案教师版"))
    )
    total_pages = 0
    for index, pdf in enumerate(pdfs, 1):
        total_pages += render_pdf(pdf, output, args.scale)[0]
        if index % 10 == 0 or index == len(pdfs):
            print(f"rendered {index}/{len(pdfs)} PDFs")
    print(f"files={len(pdfs)} pages={total_pages} output={output}")


if __name__ == "__main__":
    main()
