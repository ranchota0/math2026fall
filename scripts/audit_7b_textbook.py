"""Extract the authoritative Grade 7B textbook into page-indexed audit files.

This utility is read-only with respect to the source PDF.  It deliberately uses
pdfplumber because the supplied textbook contains a malformed font object that
causes pypdf text extraction to fail.
"""

from __future__ import annotations

import argparse
import json
import re
import unicodedata
from contextlib import redirect_stderr
from io import StringIO
from pathlib import Path

import pdfplumber


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PDF = ROOT / "义务教育教科书_数学七年级下册_标准PDF.pdf"
DEFAULT_OUTPUT = ROOT / "build" / "7b_audit" / "textbook"

MARKER_RE = re.compile(
    r"(?:第[七八九十百]+章|\d+\.\d+(?:\.\d+)?|"
    r"观察与猜想|阅读与思考|探究与发现|信息技术应用|"
    r"图说数学史|综合与实践|数学活动|小结|复习题|习题\s*\d*|练习)"
)


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    text = text.replace("\u3000", " ").replace("\xa0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    return "\n".join(line.rstrip() for line in text.splitlines()).strip()


def extract(pdf_path: Path, output_dir: Path) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    pages: list[dict] = []
    marker_rows: list[dict] = []
    stderr_buffer = StringIO()

    with redirect_stderr(stderr_buffer), pdfplumber.open(pdf_path) as pdf:
        metadata = dict(pdf.metadata or {})
        for physical_page, page in enumerate(pdf.pages, start=1):
            text = normalize(page.extract_text(layout=True) or "")
            printed_page = physical_page - 7 if physical_page >= 8 else None
            row = {
                "physical_page": physical_page,
                "printed_page": printed_page,
                "width_pt": round(float(page.width), 3),
                "height_pt": round(float(page.height), 3),
                "text": text,
            }
            pages.append(row)
            for line in text.splitlines():
                clean = line.strip()
                if clean and MARKER_RE.search(clean):
                    marker_rows.append(
                        {
                            "physical_page": physical_page,
                            "printed_page": printed_page,
                            "line": clean,
                        }
                    )

    text_blocks = []
    for row in pages:
        text_blocks.extend(
            [
                f"===== PDF_PAGE {row['physical_page']} | PRINTED_PAGE {row['printed_page']} =====",
                row["text"],
                "",
            ]
        )

    payload = {
        "source": str(pdf_path),
        "page_count": len(pages),
        "printed_page_offset": 7,
        "metadata": metadata,
        "pages": pages,
        "markers": marker_rows,
        "extractor_warnings": stderr_buffer.getvalue().splitlines(),
    }
    (output_dir / "textbook_pages.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (output_dir / "textbook_pages.txt").write_text("\n".join(text_blocks), encoding="utf-8")
    (output_dir / "textbook_markers.json").write_text(
        json.dumps(marker_rows, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdf", type=Path, default=DEFAULT_PDF)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    payload = extract(args.pdf.resolve(), args.output.resolve())
    print(
        f"[OK] pages={payload['page_count']} markers={len(payload['markers'])} "
        f"offset={payload['printed_page_offset']} output={args.output.resolve()}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
