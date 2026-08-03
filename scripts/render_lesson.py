from __future__ import annotations

from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader, StrictUndefined


ROOT = Path(__file__).resolve().parents[1]
SAMPLE_DIR = ROOT / "lessons" / "_sample"
BUILD_SAMPLE = ROOT / "build" / "sample"


def load_yaml(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def render(template_name: str, output_name: str, content_file: str, lesson: dict, project: dict) -> Path:
    env = Environment(
        loader=FileSystemLoader(str(ROOT / "templates")),
        undefined=StrictUndefined,
        autoescape=False,
        keep_trailing_newline=True,
    )
    template = env.get_template(template_name)
    rendered = template.render(
        project=project,
        lesson=lesson,
        preamble_path="common/preamble.tex",
        commands_path="common/commands.tex",
        tikz_library_path="common/tikz_library.tex",
        content_path=f"lessons/_sample/{content_file}",
    )
    BUILD_SAMPLE.mkdir(parents=True, exist_ok=True)
    output = BUILD_SAMPLE / output_name
    output.write_text(rendered, encoding="utf-8")
    return output


def main() -> int:
    lesson = load_yaml(SAMPLE_DIR / "metadata.yml")
    project = load_yaml(ROOT / "config" / "project.yml")

    if lesson.get("id") != "SAMPLE-L01":
        raise ValueError("render_lesson.py currently supports SAMPLE-L01 only")
    if lesson.get("sample") is not True or lesson.get("not_for_teaching") is not True:
        raise ValueError("sample lesson metadata must be marked sample and not_for_teaching")

    teacher = render(
        "teacher_template.tex.j2",
        "SAMPLE-L01_teacher.tex",
        "teacher_content.tex",
        lesson,
        project,
    )
    student = render(
        "student_template.tex.j2",
        "SAMPLE-L01_student.tex",
        "student_content.tex",
        lesson,
        project,
    )
    print(f"[OK] rendered {teacher.relative_to(ROOT)}")
    print(f"[OK] rendered {student.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
