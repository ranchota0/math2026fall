from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "build" / "7b_rendered_word"
OUTPUT = ROOT / "build" / "7b_acceptance" / "visual_overviews"


def build(kind: str, output_name: str) -> None:
    chosen: list[tuple[str, Path]] = []
    for chapter in range(7, 13):
        chapter_token = f"第{chapter:02d}章"
        candidates = sorted(
            path
            for path in SOURCE.rglob("contact_sheet.png")
            if chapter_token in path.parent.name and kind in path.parent.name
        )
        if not candidates:
            raise RuntimeError(f"missing {chapter_token} {kind}")
        chosen.append((chapter_token, candidates[0]))

    canvas = Image.new("RGB", (1800, 2100), "#eeeeee")
    draw = ImageDraw.Draw(canvas)
    font = ImageFont.load_default()
    for index, (chapter, path) in enumerate(chosen):
        image = Image.open(path).convert("RGB")
        image.thumbnail((860, 980), Image.Resampling.LANCZOS)
        cell_x = (index % 2) * 900
        cell_y = (index // 2) * 700
        x = cell_x + (900 - image.width) // 2
        y = cell_y + 28
        canvas.paste(image, (x, y))
        draw.text((cell_x + 12, cell_y + 8), chapter, fill="#111111", font=font)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    canvas.save(OUTPUT / output_name, quality=92)


def main() -> None:
    build("_教学设计", "teaching_overview.jpg")
    build("_学生学案", "student_overview.jpg")
    build("_学案教师版", "teacher_overview.jpg")
    print(OUTPUT)


if __name__ == "__main__":
    main()
