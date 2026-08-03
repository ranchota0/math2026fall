"""Download and verify the four official PEP mathematics textbooks.

The source records and PDF URLs are taken directly from the public textbook
catalogue of the National Smart Education Platform for Primary and Secondary
Education.  No authentication, scraping workaround, or third-party mirror is
used.
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
import shutil
import sys
import tempfile
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[1]
TEXTBOOK_ROOT = ROOT / "references" / "textbooks"
REPORTS = ROOT / "reports"
API = (
    "https://bdcs-file-2.ykt.cbern.com.cn/zxx_secondary/ndrv2/"
    "resources/tch_material/details/{resource_id}.json"
)

BOOKS = [
    {
        "key": "八年级上册",
        "grade": "八年级",
        "term": "上册",
        "resource_id": "81264e9e-22bc-4289-8389-13b40433b5ba",
        "expected_md5": "c3faba41eada7029aca267961dba5cb3",
        "expected_size": 11211129,
    },
    {
        "key": "八年级下册",
        "grade": "八年级",
        "term": "下册",
        "resource_id": "e91a6f80-2a9a-4452-a47e-b9ec164156ff",
        "expected_md5": "035a0c9715fe33bb5a604f463787cba0",
        "expected_size": 11120380,
    },
    {
        "key": "九年级上册",
        "grade": "九年级",
        "term": "上册",
        "resource_id": "937a48c1-de81-4cc6-91b2-617cd859de4b",
        "expected_md5": "f1180bcbb1fe2f219594e0bbf1768ac8",
        "expected_size": 9191547,
    },
    {
        "key": "九年级下册",
        "grade": "九年级",
        "term": "下册",
        "resource_id": "ab188631-292c-455e-8082-e09a0ab4001c",
        "expected_md5": "68ab485c1541306185ca9d0f80567426",
        "expected_size": 8863167,
    },
]


def fetch_bytes(url: str) -> bytes:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 Chrome/140 Safari/537.36"
        },
    )
    with urllib.request.urlopen(req, timeout=120) as response:
        return response.read()


def encoded_url(url: str) -> str:
    """Percent-encode non-ASCII characters and spaces in an official URL."""
    parts = urllib.parse.urlsplit(url)
    return urllib.parse.urlunsplit(
        (
            parts.scheme,
            parts.netloc,
            urllib.parse.quote(urllib.parse.unquote(parts.path), safe="/%:@"),
            parts.query,
            parts.fragment,
        )
    )


def digest_file(path: Path) -> tuple[str, str, int]:
    md5 = hashlib.md5()
    sha256 = hashlib.sha256()
    size = 0
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            md5.update(chunk)
            sha256.update(chunk)
            size += len(chunk)
    return md5.hexdigest(), sha256.hexdigest(), size


def download_atomic(url: str, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=target.stem + "_", suffix=".part", dir=target.parent)
    os.close(fd)
    temp = Path(temp_name)
    try:
        req = urllib.request.Request(
            encoded_url(url),
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 Chrome/140 Safari/537.36"
            },
        )
        with urllib.request.urlopen(req, timeout=180) as response, temp.open("wb") as out:
            shutil.copyfileobj(response, out, length=1024 * 1024)
        temp.replace(target)
    finally:
        if temp.exists():
            temp.unlink()


def analyse_pdf(path: Path) -> tuple[int, bool, int]:
    reader = PdfReader(str(path))
    page_count = len(reader.pages)
    text_chars = 0
    # Sampling enough pages reliably distinguishes searchable source PDFs from
    # image-only scans while avoiding an expensive full-text pass here.
    sample_indices = sorted(set([0, 1, 2, 3, 4, page_count // 2, page_count - 1]))
    for index in sample_indices:
        if 0 <= index < page_count:
            text_chars += len((reader.pages[index].extract_text() or "").strip())
    return page_count, text_chars >= 100, text_chars


def main() -> int:
    TEXTBOOK_ROOT.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    now = datetime.now(ZoneInfo("Asia/Shanghai"))
    rows: list[dict[str, object]] = []

    for book in BOOKS:
        key = str(book["key"])
        resource_id = str(book["resource_id"])
        detail_url = API.format(resource_id=resource_id)
        detail = json.loads(fetch_bytes(detail_url).decode("utf-8"))
        sources = [
            item
            for item in detail.get("ti_items", [])
            if item.get("ti_file_flag") == "source"
            and item.get("ti_is_source_file") is True
            and item.get("ti_format") == "pdf"
        ]
        if len(sources) != 1:
            raise RuntimeError(f"{key}: expected one official source PDF, found {len(sources)}")
        source = sources[0]
        urls = source.get("ti_storages") or []
        if not urls:
            raise RuntimeError(f"{key}: official detail record has no source storage URL")
        source_url = str(urls[0])

        book_dir = TEXTBOOK_ROOT / f"人教版{key}"
        pdf_path = book_dir / f"人教版_数学{key}_官方教材.pdf"
        raw_detail_path = book_dir / "官方资源详情.json"
        book_dir.mkdir(parents=True, exist_ok=True)
        raw_detail_path.write_text(
            json.dumps(detail, ensure_ascii=False, indent=2), encoding="utf-8"
        )

        download_status = "已下载并校验"
        block_reason = ""
        if not pdf_path.exists():
            print(f"[DOWNLOAD] {key}: {source_url}", flush=True)
            try:
                download_atomic(source_url, pdf_path)
            except urllib.error.HTTPError as exc:
                download_status = "阻断"
                block_reason = (
                    f"官方源文件地址返回 HTTP {exc.code}；官方详情页同时要求登录。"
                    "未尝试绕过登录，也未使用第三方镜像或截图拼接。"
                )
                print(f"[BLOCKED] {key}: {block_reason}", flush=True)

        expected_md5 = str(book["expected_md5"])
        expected_size = int(book["expected_size"])
        if pdf_path.exists():
            md5, sha256, size = digest_file(pdf_path)
            if md5.lower() != expected_md5.lower() or size != expected_size:
                raise RuntimeError(
                    f"{key}: verification failed; md5={md5}, size={size}, "
                    f"expected md5={expected_md5}, size={expected_size}"
                )
            page_count, searchable, sample_text_chars = analyse_pdf(pdf_path)
        else:
            md5, sha256, size = "", "", 0
            requirements = {
                item.get("name"): item.get("value")
                for item in source.get("custom_properties", {}).get("requirements", [])
            }
            page_count = int(requirements.get("pagesize") or 0)
            searchable = False
            sample_text_chars = 0
        title = detail.get("title") or detail.get("global_title", {}).get("zh-CN") or ""
        page_url = (
            "https://basic.smartedu.cn/tchMaterial/detail?"
            f"contentType=assets_document&contentId={resource_id}&"
            "catalogType=tchMaterial&subCatalog=tchMaterial"
        )
        metadata = {
            "书名": title,
            "学科": "数学",
            "年级": book["grade"],
            "册次": book["term"],
            "版本": "人教版（由平台标签确认，版权页复核另见版本报告）",
            "来源平台": "国家中小学智慧教育平台",
            "官方详情页": page_url,
            "官方详情接口": detail_url,
            "resourceId": resource_id,
            "containerId": detail.get("container_id"),
            "providerId": detail.get("provider"),
            "资源更新时间": detail.get("update_time"),
            "资源上线时间": detail.get("online_time"),
            "官方源文件名": Path(str(source.get("ti_storage", ""))).name,
            "本地文件": str(pdf_path) if pdf_path.exists() else "",
            "下载状态": download_status,
            "阻断原因": block_reason,
            "官方标注文件大小": expected_size,
            "本地文件大小": size,
            "官方MD5": expected_md5,
            "实测MD5": md5,
            "SHA256": sha256,
            "PDF页数": page_count,
            "抽样文本字符数": sample_text_chars,
            "具有可检索文本层": searchable,
            "下载时间": now.isoformat(timespec="seconds"),
            "版权页核验": "待逐页复核",
            "封面目录一致性": "待逐页复核",
        }
        metadata_path = book_dir / "教材信息.json"
        metadata_path.write_text(
            json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        rows.append(metadata)
        if pdf_path.exists():
            print(
                f"[VERIFIED] {key}: {page_count} pages, {size} bytes, "
                f"MD5={md5}, searchable={searchable}",
                flush=True,
            )

    csv_path = REPORTS / "四册教材下载清单.csv"
    fields = list(rows[0].keys())
    with csv_path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    print(f"[REPORT] {csv_path}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
