from __future__ import annotations

import json
import re
import shutil
import subprocess
import time
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = ROOT / "logs"
BUILD_DIR = ROOT / "build" / "compiled"
RESULTS_JSON = LOG_DIR / "compile_results.json"


def discover_tex_files() -> list[Path]:
    files = sorted((ROOT / "tests").glob("*.tex"))
    sample_dir = ROOT / "build" / "sample"
    if sample_dir.exists():
        files.extend(sorted(sample_dir.glob("*.tex")))
    return files


def classify(path: Path) -> str:
    if "tests" in path.parts:
        return "smoke_test"
    if "sample" in path.parts:
        return "sample"
    return "unknown"


def parse_log(text: str) -> dict:
    warnings = len(re.findall(r"(?:LaTeX|Package [^ ]+) Warning", text))
    overfull = len(re.findall(r"Overfull \\\\hbox", text))
    pages = 0
    match = re.search(r"Output written on .+? \((\d+) pages?", text)
    if match:
        pages = int(match.group(1))
    error_message = ""
    for line in text.splitlines():
        if line.startswith("!") or "Fatal error" in line or "Emergency stop" in line:
            error_message = line.strip()
            break
    return {
        "warnings": warnings,
        "overfull_boxes": overfull,
        "pdf_pages": pages,
        "error_message": error_message,
    }


def run_command(command: list[str], cwd: Path, log_path: Path) -> tuple[int, str, float]:
    start = time.perf_counter()
    completed = subprocess.run(
        command,
        cwd=str(cwd),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        encoding="utf-8",
        errors="replace",
    )
    seconds = time.perf_counter() - start
    log_path.write_text(completed.stdout, encoding="utf-8")
    return completed.returncode, completed.stdout, seconds


def compile_file(path: Path, latexmk: str | None, xelatex: str | None) -> dict:
    rel = path.relative_to(ROOT)
    out_dir = BUILD_DIR / path.parent.relative_to(ROOT) / path.stem
    out_dir.mkdir(parents=True, exist_ok=True)
    log_path = LOG_DIR / f"{path.stem}.compile.log"

    if latexmk:
        command = [
            latexmk,
            "-xelatex",
            "-interaction=nonstopmode",
            "-halt-on-error",
            "-file-line-error",
            f"-outdir={out_dir}",
            str(path),
        ]
        code, output, seconds = run_command(command, ROOT, log_path)
    else:
        combined = []
        seconds = 0.0
        code = 0
        for _ in range(2):
            command = [
                xelatex or "xelatex",
                "-interaction=nonstopmode",
                "-halt-on-error",
                "-file-line-error",
                f"-output-directory={out_dir}",
                str(path),
            ]
            run_code, output, run_seconds = run_command(command, ROOT, log_path)
            combined.append(output)
            seconds += run_seconds
            code = run_code
            if run_code != 0:
                break
        output = "\n".join(combined)
        log_path.write_text(output, encoding="utf-8")

    tex_log = out_dir / f"{path.stem}.log"
    log_text = tex_log.read_text(encoding="utf-8", errors="replace") if tex_log.exists() else output
    parsed = parse_log(log_text)
    status = "success" if code == 0 else "failed"
    if status == "success" and parsed["pdf_pages"] == 0 and (out_dir / f"{path.stem}.pdf").exists():
        parsed["pdf_pages"] = 1

    return {
        "file": rel.as_posix(),
        "type": classify(path),
        "status": status,
        "compile_seconds": round(seconds, 3),
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        **parsed,
    }


def main() -> int:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    BUILD_DIR.mkdir(parents=True, exist_ok=True)

    files = discover_tex_files()
    latexmk = shutil.which("latexmk")
    xelatex = shutil.which("xelatex")
    results = []

    if not xelatex:
        for path in files:
            results.append(
                {
                    "file": path.relative_to(ROOT).as_posix(),
                    "type": classify(path),
                    "status": "skipped_environment_missing",
                    "pdf_pages": 0,
                    "compile_seconds": 0,
                    "warnings": 0,
                    "overfull_boxes": 0,
                    "error_message": "xelatex not found",
                    "timestamp": datetime.now().isoformat(timespec="seconds"),
                }
            )
            print(f"[SKIP] {path.relative_to(ROOT)}: xelatex not found")
        RESULTS_JSON.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
        return 0

    for path in files:
        result = compile_file(path, latexmk, xelatex)
        results.append(result)
        print(
            f"[{result['status'].upper()}] {result['file']} "
            f"{result['compile_seconds']}s warnings={result['warnings']} overfull={result['overfull_boxes']}"
        )

    RESULTS_JSON.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    return 1 if any(item["status"] == "failed" for item in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
