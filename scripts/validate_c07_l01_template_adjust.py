from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from zipfile import ZipFile

from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[1]
LESSON_DIR = ROOT / "lessons" / "第07章_相交线与平行线" / "7.1.1_相交线与对顶角" / "教学设计"
DOCX = LESSON_DIR / "7.1.1_相交线与对顶角_教学设计_模板调整版.docx"
PDF = DOCX.with_suffix(".pdf")
OUT = ROOT / "build" / "7b_template_adjust" / "qa.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def main() -> None:
    with ZipFile(DOCX) as archive:
        xml = archive.read("word/document.xml").decode("utf-8")
    docx_text = "".join(re.findall(r"<w:t[^>]*>(.*?)</w:t>", xml))
    docx_text = docx_text.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&")
    table_count = xml.count("<w:tbl>")
    section_count = xml.count("<w:sectPr")
    a4_sections = len(re.findall(r'<w:pgSz[^>]*w:w="1190[67]"[^>]*w:h="1683[78]"', xml))

    reader = PdfReader(str(PDF))
    pdf_texts = [(page.extract_text() or "") for page in reader.pages]
    pdf_text = "\n".join(pdf_texts)
    boxes = [[round(float(page.mediabox.width), 2), round(float(page.mediabox.height), 2)] for page in reader.pages]
    required = [
        "北京市和平街第一中学课时教学设计",
        "两条直线相交",
        "邻补角",
        "对顶角",
        "对顶角相等",
        "∠1+∠2=180°",
        "课标依据",
        "教材地位",
        "学情基础",
        "旧知回顾",
        "操作探究",
        "概念形成",
        "性质推导",
        "教材例1",
        "分层练习与检测",
        "基础巩固",
        "提升思考",
        "评价设计",
        "资源对应",
        "印刷页1—3",
        "当堂检测",
        "课后反思",
    ]
    forbidden = ["正数和负数", "反比例函数", "[["]
    required_docx = {item: item in docx_text for item in required}
    normalized_pdf_text = re.sub(r"\s+", "", pdf_text)
    required_pdf = {item: item in normalized_pdf_text for item in required}
    forbidden_docx = {item: item not in docx_text for item in forbidden}
    forbidden_pdf = {item: item not in pdf_text for item in forbidden}

    result = {
        "docx": {
            "path": str(DOCX),
            "sha256": sha256(DOCX),
            "size": DOCX.stat().st_size,
            "tables": table_count,
            "sections": section_count,
            "a4_sections": a4_sections,
            "required": required_docx,
            "forbidden_absent": forbidden_docx,
        },
        "pdf": {
            "path": str(PDF),
            "sha256": sha256(PDF),
            "size": PDF.stat().st_size,
            "pages": len(reader.pages),
            "page_boxes_points": boxes,
            "text_chars_per_page": [len(text) for text in pdf_texts],
            "searchable_all_pages": all(len(text.strip()) > 20 for text in pdf_texts),
            "producer": (reader.metadata.producer if reader.metadata else None),
            "required": required_pdf,
            "forbidden_absent": forbidden_pdf,
        },
        "checks": {
            "docx_editable_structure": table_count == 4 and section_count == 4,
            "docx_a4_all_sections": a4_sections == 4,
            "pdf_four_pages": len(reader.pages) == 4,
            "pdf_a4_all_pages": all(abs(w - 595.28) < 1 and abs(h - 841.89) < 1 for w, h in boxes),
            "content_required_docx": all(required_docx.values()),
            "content_required_pdf": all(required_pdf.values()),
            "forbidden_absent_docx": all(forbidden_docx.values()),
            "forbidden_absent_pdf": all(forbidden_pdf.values()),
            "pdf_searchable": all(len(text.strip()) > 20 for text in pdf_texts),
        },
    }
    result["checks"]["all_pass"] = all(result["checks"].values())
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
