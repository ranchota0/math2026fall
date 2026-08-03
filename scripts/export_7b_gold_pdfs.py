"""Export final Grade 7B teaching-design PDFs directly from the migrated DOCX files."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import yaml
from pypdf import PdfReader

from apply_7b_gold_lessonplan_template import lesson_sources


ROOT = Path(__file__).resolve().parents[1]
SOFFICE = Path(r"C:\Program Files\LibreOffice\program\soffice.exe")
BASE = ROOT / "build" / "7b_gold_template_migration"
EXPORT = BASE / "lo_export"
PROFILES = BASE / "lo_profiles"


def normalize(value: str) -> str:
    return "".join(value.replace("\u00a0", " ").split())


def validate_pdf(path: Path, data: dict) -> dict:
    reader = PdfReader(path)
    page_info = []
    text = ""
    for page in reader.pages:
        page_text = page.extract_text() or ""
        text += page_text
        page_info.append(
            {
                "width": float(page.mediabox.width),
                "height": float(page.mediabox.height),
                "characters": len(page_text.strip()),
            }
        )
    compact = normalize(text)
    required = [
        "北京市和平街第一中学课时教学设计",
        data["meta"]["title"],
        data["key_point"],
        data["difficulty"],
        "课后反思",
        *[stage["stage"] for stage in data["flow"]],
    ]
    missing = [value for value in required if normalize(value) not in compact]
    geometry_ok = all(
        abs(item["width"] - 595.28) < 1.0
        and abs(item["height"] - 841.89) < 1.0
        and item["characters"] > 120
        for item in page_info
    )
    return {
        "pages": len(reader.pages),
        "page_info": page_info,
        "producer": str((reader.metadata or {}).get("/Producer", "")),
        "missing": missing,
        "pass": len(reader.pages) == 4 and geometry_ok and not missing,
    }


def export_one(source: Path) -> dict:
    data = yaml.safe_load(source.read_text(encoding="utf-8"))
    lesson_id = data["meta"]["lesson_id"]
    lesson_root = source.parents[1]
    prefix = data["meta"]["file_prefix"]
    docx = lesson_root / "教学设计" / f"{prefix}_教学设计.docx"
    final_pdf = docx.with_suffix(".pdf")
    outdir = EXPORT / lesson_id
    profile = PROFILES / lesson_id
    outdir.mkdir(parents=True, exist_ok=True)
    profile.mkdir(parents=True, exist_ok=True)
    exported_pdf = outdir / f"{docx.stem}.pdf"
    if exported_pdf.exists():
        exported_pdf.unlink()
    profile_uri = "file:///" + str(profile.resolve()).replace("\\", "/")
    result = subprocess.run(
        [
            str(SOFFICE), "--headless", f"-env:UserInstallation={profile_uri}",
            "--convert-to", "pdf:writer_pdf_Export", "--outdir", str(outdir), str(docx),
        ],
        capture_output=True,
        text=True,
        timeout=120,
        encoding="utf-8",
        errors="replace",
    )
    record = {
        "lesson_id": lesson_id,
        "docx": str(docx),
        "exported_pdf": str(exported_pdf),
        "final_pdf": str(final_pdf),
        "returncode": result.returncode,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
    }
    if result.returncode != 0 or not exported_pdf.exists():
        record["pass"] = False
        record["error"] = "LibreOffice export failed"
        return record
    validation = validate_pdf(exported_pdf, data)
    record["validation"] = validation
    record["pass"] = validation["pass"]
    if validation["pass"]:
        shutil.copy2(exported_pdf, final_pdf)
    return record


def main() -> int:
    if not SOFFICE.exists():
        raise FileNotFoundError(SOFFICE)
    records = []
    for source in lesson_sources():
        data = yaml.safe_load(source.read_text(encoding="utf-8"))
        if data["meta"]["lesson_id"] == "C07-L01":
            continue
        record = export_one(source)
        records.append(record)
        status = "PASS" if record["pass"] else "FAIL"
        print(f"[{status}] {record['lesson_id']} {record['final_pdf']}")
    (BASE / "pdf_export_validation.json").write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    summary = {
        "lessons": len(records),
        "passed": sum(bool(item["pass"]) for item in records),
        "failed": sum(not item["pass"] for item in records),
    }
    print(json.dumps(summary, ensure_ascii=False))
    return 1 if summary["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
