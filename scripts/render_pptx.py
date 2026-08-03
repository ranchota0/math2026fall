from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from pptx_audit_lib import pptx_files, safe_deck_name


ROOT = Path(__file__).resolve().parents[1]


def ps_quote(path: Path) -> str:
    return "'" + str(path).replace("'", "''") + "'"


def export_one(pptx: Path, out_dir: Path) -> None:
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = out_dir / "deck.pdf"
    script = f"""
$ErrorActionPreference = 'Stop'
$ppt = New-Object -ComObject PowerPoint.Application
$ppt.Visible = 1
$pres = $ppt.Presentations.Open({ps_quote(pptx.resolve())}, $true, $false, $false)
$pres.Export({ps_quote(out_dir.resolve())}, 'PNG')
try {{
  $pres.SaveAs({ps_quote(pdf_path.resolve())}, 32)
}} catch {{
  Write-Output ('PDF export failed: ' + $_.Exception.Message)
}}
$pres.Close()
$ppt.Quit()
"""
    with tempfile.NamedTemporaryFile("w", suffix=".ps1", delete=False, encoding="utf-8-sig") as handle:
        handle.write(script)
        ps1 = handle.name
    try:
        completed = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", ps1],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            encoding="utf-8",
            errors="replace",
        )
        if completed.returncode != 0:
            print(completed.stdout)
            raise subprocess.CalledProcessError(completed.returncode, completed.args, completed.stdout)
    finally:
        try:
            os.unlink(ps1)
        except OSError:
            pass
    normalize_slide_names(out_dir)
    create_contact_sheet(out_dir, out_dir / "contact_sheet.png", pptx.name)


def normalize_slide_names(out_dir: Path) -> None:
    for path in list(out_dir.glob("Slide*.PNG")) + list(out_dir.glob("幻灯片*.PNG")):
        match = re.search(r"(?:Slide|幻灯片)(\d+)\.PNG", path.name, re.I)
        if match:
            target = out_dir / f"slide-{int(match.group(1)):03d}.png"
            if target.exists():
                target.unlink()
            path.rename(target)


def create_contact_sheet(image_dir: Path, output: Path, title: str) -> None:
    images = sorted(image_dir.glob("slide-*.png"))
    if not images:
        return
    thumbs = []
    for image_path in images:
        img = Image.open(image_path).convert("RGB")
        img.thumbnail((320, 180))
        canvas = Image.new("RGB", (340, 220), "white")
        canvas.paste(img, ((340 - img.width) // 2, 10))
        draw = ImageDraw.Draw(canvas)
        draw.text((10, 194), image_path.stem, fill=(0, 0, 0))
        thumbs.append(canvas)

    cols = 4
    rows = (len(thumbs) + cols - 1) // cols
    header = 40
    sheet = Image.new("RGB", (cols * 340, rows * 220 + header), "white")
    draw = ImageDraw.Draw(sheet)
    draw.text((12, 12), title, fill=(0, 0, 0))
    for idx, thumb in enumerate(thumbs):
        x = (idx % cols) * 340
        y = header + (idx // cols) * 220
        sheet.paste(thumb, (x, y))
    output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output)


def main() -> int:
    parser = argparse.ArgumentParser(description="Render PPTX files to PNG slides and PDF with PowerPoint COM.")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--skip-existing", action="store_true", help="Skip decks whose contact sheet and 15 slide PNGs already exist.")
    parser.add_argument("--path-contains", default="", help="Render only PPTX paths containing this text.")
    args = parser.parse_args()

    source = Path(args.input)
    files = [source] if source.is_file() else pptx_files(source)
    if args.path_contains:
        files = [path for path in files if args.path_contains in str(path)]
    out_root = Path(args.output)
    for pptx in files:
        base = source.parent if source.is_file() else source
        name = re.sub(r"[^0-9A-Za-z\u4e00-\u9fff_-]+", "_", safe_deck_name(pptx, base)).strip("_")
        out_dir = out_root / name
        if args.skip_existing and (out_dir / "contact_sheet.png").exists() and len(list(out_dir.glob("slide-*.png"))) == 15:
            print(f"[SKIP] {pptx} -> {out_dir}")
            continue
        print(f"[RENDER] {pptx} -> {out_dir}")
        export_one(pptx, out_dir)
    print(f"[OK] rendered {len(files)} pptx files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
