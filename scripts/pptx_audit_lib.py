from __future__ import annotations

import csv
import re
import zipfile
from dataclasses import dataclass
from pathlib import Path
from xml.etree import ElementTree as ET


NS = {
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
}

EMU_PER_INCH = 914400
FORBIDDEN_PATTERNS = [
    ("Pxx", re.compile(r"\bPxx\b", re.I)),
    ("PXX", re.compile(r"\bPXX\b")),
    ("XXX", re.compile(r"\bXXX\b")),
    ("张老师", re.compile(r"张老师")),
    ("豆包AI生成", re.compile(r"豆包AI生成")),
    ("latex_dollar", re.compile(r"\$")),
    ("latex_frac", re.compile(r"\\frac")),
    ("latex_times", re.compile(r"\\times")),
    ("latex_inline_open", re.compile(r"\\\(")),
    ("latex_inline_close", re.compile(r"\\\)")),
    ("markdown_backtick", re.compile(r"`")),
]


@dataclass
class PptxAudit:
    path: Path
    slide_count: int
    width_in: float
    height_in: float
    notes_slides: int
    text_runs: int
    issue_count: int
    issues: list[dict]


def pptx_files(root: Path) -> list[Path]:
    return sorted(path for path in root.rglob("*.pptx") if path.is_file() and not path.name.startswith("~$"))


def safe_deck_name(path: Path, base: Path) -> str:
    rel = path.relative_to(base).with_suffix("")
    return "__".join(rel.parts).replace(" ", "_")


def read_xml(zf: zipfile.ZipFile, name: str) -> ET.Element | None:
    try:
        return ET.fromstring(zf.read(name))
    except KeyError:
        return None


def all_text(root: ET.Element | None) -> str:
    if root is None:
        return ""
    return "\n".join(node.text or "" for node in root.findall(".//a:t", NS))


def shape_bounds(shape: ET.Element) -> tuple[int, int, int, int] | None:
    xfrm = shape.find(".//p:spPr/a:xfrm", NS)
    if xfrm is None:
        xfrm = shape.find(".//p:pic/p:spPr/a:xfrm", NS)
    if xfrm is None:
        xfrm = shape.find(".//p:graphicFrame/a:xfrm", NS)
    if xfrm is None:
        return None
    off = xfrm.find("a:off", NS)
    ext = xfrm.find("a:ext", NS)
    if off is None or ext is None:
        return None
    return (
        int(off.attrib.get("x", "0")),
        int(off.attrib.get("y", "0")),
        int(ext.attrib.get("cx", "0")),
        int(ext.attrib.get("cy", "0")),
    )


def audit_pptx(path: Path) -> PptxAudit:
    issues: list[dict] = []
    with zipfile.ZipFile(path) as zf:
        pres = read_xml(zf, "ppt/presentation.xml")
        width = height = 0
        if pres is not None:
            sld_sz = pres.find("p:sldSz", NS)
            if sld_sz is not None:
                width = int(sld_sz.attrib.get("cx", "0"))
                height = int(sld_sz.attrib.get("cy", "0"))

        slide_names = sorted(
            [name for name in zf.namelist() if re.fullmatch(r"ppt/slides/slide\d+\.xml", name)],
            key=lambda n: int(re.search(r"slide(\d+)\.xml", n).group(1)),
        )
        notes_names = sorted(
            [name for name in zf.namelist() if re.fullmatch(r"ppt/notesSlides/notesSlide\d+\.xml", name)],
            key=lambda n: int(re.search(r"notesSlide(\d+)\.xml", n).group(1)),
        )

        text_runs = 0
        notes_with_text = 0
        for slide_index, name in enumerate(slide_names, start=1):
            root = read_xml(zf, name)
            text = all_text(root)
            if root is not None:
                text_runs += len(root.findall(".//a:t", NS))
                checked_objects = []
                for shape in root.findall(".//p:sp", NS):
                    shape_text = all_text(shape).strip()
                    if shape_text:
                        checked_objects.append(("text_box", shape))
                checked_objects.extend(("picture", shape) for shape in root.findall(".//p:pic", NS))
                checked_objects.extend(("graphic_frame", shape) for shape in root.findall(".//p:graphicFrame", NS))
                for object_kind, shape in checked_objects:
                    bounds = shape_bounds(shape)
                    if bounds and width and height:
                        x, y, cx, cy = bounds
                        if x < -1000 or y < -1000 or x + cx > width + 1000 or y + cy > height + 1000:
                            issues.append(
                                {
                                    "file": str(path),
                                    "slide": slide_index,
                                    "issue_type": "object_out_of_bounds",
                                    "detail": f"{object_kind}: x={x}, y={y}, cx={cx}, cy={cy}",
                                }
                            )
                for key, pattern in FORBIDDEN_PATTERNS:
                    if pattern.search(text):
                        issues.append(
                            {
                                "file": str(path),
                                "slide": slide_index,
                                "issue_type": f"forbidden_{key}",
                                "detail": snippet(text, pattern),
                            }
                        )
                for rpr in root.findall(".//a:rPr", NS):
                    size = rpr.attrib.get("sz")
                    if size and int(size) < 1200:
                        issues.append(
                            {
                                "file": str(path),
                                "slide": slide_index,
                                "issue_type": "font_too_small",
                                "detail": f"{int(size) / 100:.1f} pt",
                            }
                        )

        for notes_index, name in enumerate(notes_names, start=1):
            text = all_text(read_xml(zf, name))
            if text.strip():
                notes_with_text += 1
            for key, pattern in FORBIDDEN_PATTERNS:
                if pattern.search(text):
                    issues.append(
                        {
                            "file": str(path),
                            "slide": notes_index,
                            "issue_type": f"notes_forbidden_{key}",
                            "detail": snippet(text, pattern),
                        }
                    )

    return PptxAudit(
        path=path,
        slide_count=len(slide_names),
        width_in=round(width / EMU_PER_INCH, 2) if width else 0.0,
        height_in=round(height / EMU_PER_INCH, 2) if height else 0.0,
        notes_slides=notes_with_text,
        text_runs=text_runs,
        issue_count=len(issues),
        issues=issues,
    )


def snippet(text: str, pattern: re.Pattern, radius: int = 40) -> str:
    match = pattern.search(text)
    if not match:
        return ""
    start = max(match.start() - radius, 0)
    end = min(match.end() + radius, len(text))
    return text[start:end].replace("\n", " ")


def write_audit_reports(audits: list[PptxAudit], csv_path: Path, md_path: Path, title: str) -> None:
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", encoding="utf-8-sig", newline="") as handle:
        fields = ["file", "slide_count", "width_in", "height_in", "notes_slides", "text_runs", "issue_count"]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for audit in audits:
            writer.writerow(
                {
                    "file": str(audit.path),
                    "slide_count": audit.slide_count,
                    "width_in": audit.width_in,
                    "height_in": audit.height_in,
                    "notes_slides": audit.notes_slides,
                    "text_runs": audit.text_runs,
                    "issue_count": audit.issue_count,
                }
            )

    issue_csv = csv_path.with_name(csv_path.stem + "_issues.csv")
    with issue_csv.open("w", encoding="utf-8-sig", newline="") as handle:
        fields = ["file", "slide", "issue_type", "detail"]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for audit in audits:
            for issue in audit.issues:
                writer.writerow(issue)

    lines = [f"# {title}", "", f"文件数：{len(audits)}", ""]
    lines.append("| 文件 | 页数 | 尺寸 | 备注页 | 问题数 |")
    lines.append("|---|---:|---|---:|---:|")
    for audit in audits:
        lines.append(
            f"| `{audit.path}` | {audit.slide_count} | {audit.width_in} x {audit.height_in} in | {audit.notes_slides} | {audit.issue_count} |"
        )
    lines.append("")
    lines.append("## 主要问题")
    for audit in audits:
        if not audit.issues:
            continue
        lines.append("")
        lines.append(f"### {audit.path.name}")
        for issue in audit.issues[:30]:
            lines.append(f"- 第 {issue['slide']} 页：{issue['issue_type']}，{issue['detail']}")
        if len(audit.issues) > 30:
            lines.append(f"- 其余 {len(audit.issues) - 30} 条见 `{issue_csv.name}`。")
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
