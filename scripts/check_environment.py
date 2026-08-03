from __future__ import annotations

import importlib.util
import os
import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REQUIRED_PACKAGES = {
    "jinja2": "jinja2",
    "pyyaml": "yaml",
    "jsonschema": "jsonschema",
}


def ok(label: str, detail: str) -> None:
    print(f"[OK] {label}: {detail}")


def warn(label: str, detail: str) -> None:
    print(f"[WARN] {label}: {detail}")


def check_package(name: str, import_name: str) -> bool:
    found = importlib.util.find_spec(import_name) is not None
    if found:
        ok(f"python package {name}", "available")
    else:
        warn(f"python package {name}", "missing; run pip install -r requirements.txt")
    return found


def check_writable(path: Path) -> bool:
    path.mkdir(parents=True, exist_ok=True)
    test_file = path / ".write_test"
    try:
        test_file.write_text("ok", encoding="utf-8")
        test_file.unlink()
        ok(f"writable {path.relative_to(ROOT)}", "yes")
        return True
    except OSError as exc:
        warn(f"writable {path.relative_to(ROOT)}", str(exc))
        return False


def main() -> int:
    print(f"Project root: {ROOT}")
    print(f"Python: {sys.version.split()[0]} ({sys.executable})")
    if sys.version_info >= (3, 10):
        ok("python version", ">= 3.10")
    else:
        warn("python version", "Python 3.10+ is recommended")

    for package, import_name in REQUIRED_PACKAGES.items():
        check_package(package, import_name)

    xelatex = shutil.which("xelatex")
    latexmk = shutil.which("latexmk")
    if xelatex:
        ok("xelatex", xelatex)
    else:
        warn("xelatex", "not found; compile step will be skipped")
    if latexmk:
        ok("latexmk", latexmk)
    else:
        warn("latexmk", "not found; direct xelatex fallback will be used if available")

    textbook = ROOT / "references" / "textbook.pdf"
    if textbook.exists():
        ok("textbook pdf", str(textbook.relative_to(ROOT)))
    else:
        warn("textbook pdf", "references/textbook.pdf not found")

    for directory in ["build", "logs", "reports", "dist/tex", "dist/pdf"]:
        check_writable(ROOT / directory)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
