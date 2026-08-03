#!/usr/bin/env python3
"""Rasterize Word-exported mature lesson-plan PDFs and build contact sheets."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageOps


ROOT = Path(__file__).resolve().parents[1]
RENDER_ROOT = ROOT / "build" / "mature_lessonplan_analysis" / "rendered"
PDFTOPPM = Path(r"D:\texlive\2026\bin\windows\pdftoppm.exe")


def render(pdf: Path) -> list[Path]:
    out_dir = pdf.parent / "pages"
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)
    subprocess.run(
        [str(PDFTOPPM), "-png", "-r", "110", str(pdf), str(out_dir / "page")],
        check=True,
    )
    return sorted(out_dir.glob("page-*.png"))


def contact_sheet(images: list[Path], output: Path) -> None:
    thumbs: list[Image.Image] = []
    for index, path in enumerate(images, start=1):
        image = Image.open(path).convert("RGB")
        image.thumbnail((330, 467))
        image = ImageOps.expand(image, border=8, fill="white")
        tile = Image.new("RGB", (image.width, image.height + 24), "white")
        tile.paste(image, (0, 0))
        ImageDraw.Draw(tile).text((8, image.height + 4), f"page {index}", fill="black")
        thumbs.append(tile)
    columns = 2
    tile_width = max(image.width for image in thumbs)
    tile_height = max(image.height for image in thumbs)
    rows = (len(thumbs) + columns - 1) // columns
    sheet = Image.new("RGB", (tile_width * columns, tile_height * rows), "#dddddd")
    for index, image in enumerate(thumbs):
        sheet.paste(image, ((index % columns) * tile_width, (index // columns) * tile_height))
    sheet.save(output)


def main() -> None:
    if not PDFTOPPM.exists():
        raise FileNotFoundError(PDFTOPPM)
    for pdf in sorted(RENDER_ROOT.glob("doc*/source.pdf")):
        pages = render(pdf)
        contact_sheet(pages, pdf.parent / "contact-sheet.png")
        print(f"{pdf.parent.name}: {len(pages)} pages")


if __name__ == "__main__":
    main()
