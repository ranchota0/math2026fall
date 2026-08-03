#!/usr/bin/env python3
"""Compile Hepingjie lesson-plan templates or lesson-plan .tex files."""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path


def rel_arg(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return str(path.resolve())


def compile_tex(root: Path, tex_file: Path, output_dir: Path) -> dict:
    xelatex = shutil.which("xelatex")
    if not xelatex:
        raise RuntimeError("xelatex was not found. Install TeX Live or MiKTeX first.")

    tex_file = tex_file.resolve()
    if not tex_file.is_file():
        raise FileNotFoundError(f"missing tex file: {tex_file}")

    output_dir.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env["TEXINPUTS"] = "tex//" + os.pathsep + env.get("TEXINPUTS", "")

    cmd = [
        xelatex,
        "-interaction=nonstopmode",
        "-halt-on-error",
        f"-output-directory={rel_arg(output_dir, root)}",
        rel_arg(tex_file, root),
    ]

    outputs = []
    code = 0
    for _ in range(2):
        result = subprocess.run(
            cmd,
            cwd=root,
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            encoding="utf-8",
            errors="replace",
        )
        outputs.append(result.stdout)
        code = result.returncode
        if code != 0:
            break

    log_path = output_dir / f"{tex_file.stem}.compile.log"
    log_path.write_text("\n".join(outputs), encoding="utf-8")

    pdf = output_dir / f"{tex_file.stem}.pdf"
    if code != 0:
        raise RuntimeError(f"compile failed: {tex_file}; see {log_path}")
    if not pdf.exists():
        raise RuntimeError(f"PDF was not generated: {pdf}")

    return {"tex": tex_file, "pdf": pdf, "log": log_path}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("tex", nargs="*", help=".tex files to compile")
    parser.add_argument("--output-dir", default="dist/templates", help="PDF output directory")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    files = [Path(p) for p in args.tex] if args.tex else [
        root / "templates/hepingjie_lessonplan/blank.tex",
        root / "templates/hepingjie_lessonplan/example.tex",
    ]
    output_dir = root / args.output_dir

    try:
        for file in files:
            file = file if file.is_absolute() else root / file
            result = compile_tex(root, file, output_dir)
            print(f"[OK] {result['tex'].relative_to(root).as_posix()} -> {result['pdf'].relative_to(root).as_posix()}")
    except (RuntimeError, FileNotFoundError) as exc:
        print(f"[FAIL] {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
