#!/usr/bin/env python3
"""TencentOS CVE XML 查询工具.

从 https://mirrors.tencent.com/tlinux/errata/cve.xml 查询 CVE 修复状态。
无外部服务依赖，一个文件即可运行。

提供 CLI 接口：
  - query   单个/批量 CVE 查询
  - extract 从文本提取 CVE 编号
  - status  查看数据源状态
  - clear   清除 XML 缓存

返回结构与原 MCP tool 一致，可直接喂给 LLM。

用法：
  python cve_xml_server.py query CVE-2020-15778
  python cve_xml_server.py query CVE-2024-1234 CVE-2024-5678
  python cve_xml_server.py extract "修复了 CVE-2024-1234 和 CVE-2024-5678"
  python cve_xml_server.py status
  python cve_xml_server.py clear
"""

import json
import os
import re
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set


# ===========================================================================
# 配置
# ===========================================================================

CVE_XML_URL = os.getenv(
    "CVE_XML_URL",
    "https://mirrors.tencent.com/tlinux/errata/cve.xml",
)
CVE_XML_CACHE_DURATION = int(os.getenv("CVE_XML_CACHE_DURATION", "3600"))
TSSA_URL_TEMPLATE = os.getenv(
    "TSSA_URL_TEMPLATE",
    "https://mirrors.tencent.com/tlinux/errata/{tssa_id}.xml",
)


# ===========================================================================
# 响应封装（与原 MCP tool 返回结构一致）
# ===========================================================================


def _success(data, meta=None):
    # type: (Any, Optional[dict]) -> str
    resp = {"status": "success", "data": data}  # type: Dict[str, Any]
    if meta:
        resp["meta"] = meta
    return json.dumps(resp, ensure_ascii=False, default=str)


def _error(msg, meta=None):
    # type: (str, Optional[dict]) -> str
    resp = {"status": "error", "error": {"message": msg}, "data": {}}  # type: Dict[str, Any]
    if meta:
        resp["meta"] = meta
    return json.dumps(resp, ensure_ascii=False)


# ===========================================================================
# CVE ID 工具函数
# ===========================================================================

CVE_PATTERN = re.compile(r"CVE-\d{4}-\d{4,}", re.IGNORECASE)


def validate_cve_id(cve_id: str) -> bool:
    if not cve_id:
        return False
    return bool(CVE_PATTERN.fullmatch(cve_id.upper()))


def extract_cve_ids(text: str) -> List[str]:
    seen = set()  # type: Set[str]
    result = []  # type: List[str]
    for m in CVE_PATTERN.findall(text):
        u = m.upper()
        if u not in seen:
            seen.add(u)
            result.append(u)
    return result


def normalize_cve_id(cve_id: str) -> str:
    cve_id = cve_id.strip().upper()
    if not validate_cve_id(cve_id):
        raise ValueError(f"Invalid CVE ID format: {cve_id}")
    return cve_id


# ===========================================================================
# TSSA URL 构建
# ===========================================================================


def build_tssa_url(tssa_id: str) -> str:
    formatted = tssa_id.lower().replace(":", "")
    return TSSA_URL_TEMPLATE.format(tssa_id=formatted)


# ===========================================================================
# 数据模型（轻量，不依赖 pydantic）
# ===========================================================================


class TSSABlock:
    __slots__ = (
        "tssa_id", "title", "severity", "advisory_type",
        "issued_date", "updated_date", "description",
        "cve_list", "packages", "product_series",
    )

    def __init__(self):
        self.tssa_id = ""
        self.title = ""
        self.severity = ""
        self.advisory_type = ""
        self.issued_date = ""
        self.updated_date = ""
        self.description = ""
        self.cve_list = []  # type: List[str]
        self.packages = []  # type: List[str]
        self.product_series = ""


class CVEXMLCache:
    def __init__(self, tssa_blocks: "List[TSSABlock]", cached_at: datetime):
        self.tssa_blocks = tssa_blocks
        self.cached_at = cached_at

    def is_expired(self) -> bool:
        return datetime.now() - self.cached_at > timedelta(seconds=CVE_XML_CACHE_DURATION)


# ===========================================================================
# XML 获取与解析（带缓存）
# ===========================================================================


class _CacheManager:
    """CVE XML 缓存管理器"""

    def __init__(self):
        self.cache: Optional[CVEXMLCache] = None

    def clear(self) -> None:
        self.cache = None

    def get_status(self) -> dict:
        if self.cache:
            return {
                "cached": True,
                "cached_at": self.cache.cached_at.isoformat(),
                "tssa_count": len(self.cache.tssa_blocks),
                "is_expired": self.cache.is_expired(),
            }
        return {"cached": False}


_cache_manager = _CacheManager()


def _get_text(elem: ET.Element, tag: str) -> str:
    child = elem.find(tag)
    if child is not None and child.text:
        return child.text.strip()
    return ""


def _extract_product_series(title: str, desc: str) -> str:
    text = f"{title} {desc}"
    for pat in [r"TencentOS\s+Server\s+(\d+)", r"\bTS(\d+)\b"]:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            return f"TS{m.group(1)}"
    return ""


def _parse_tssa_update(update: ET.Element) -> Optional[TSSABlock]:
    block = TSSABlock()
    block.tssa_id = _get_text(update, "id")
    if not block.tssa_id:
        return None
    block.title = _get_text(update, "title")
    block.severity = _get_text(update, "severity")
    block.advisory_type = update.get("type", "")
    issued = update.find("issued")
    if issued is not None:
        block.issued_date = issued.get("date", "")
    updated = update.find("updated")
    if updated is not None:
        block.updated_date = updated.get("date", "")
    block.description = _get_text(update, "description")
    block.product_series = _extract_product_series(block.title, block.description)
    refs = update.find("references")
    if refs is not None:
        for ref in refs.findall("reference"):
            if ref.get("type") == "cve":
                cve_id = ref.get("id", "")
                if cve_id and cve_id not in block.cve_list:
                    block.cve_list.append(cve_id)
    pkglist = update.find("pkglist")
    if pkglist is not None:
        for coll in pkglist.findall("collection"):
            for pkg in coll.findall("package"):
                if pkg.get("arch") == "src":
                    fn = pkg.find("filename")
                    if fn is not None and fn.text:
                        src = fn.text.strip()
                        if src.endswith(".src.rpm"):
                            v = src[:-8]
                            if v not in block.packages:
                                block.packages.append(v)
    return block


def parse_cve_xml(xml_content: str) -> "List[TSSABlock]":
    root = ET.fromstring(xml_content)
    blocks = []  # type: List[TSSABlock]
    for update in root.findall(".//update"):
        try:
            b = _parse_tssa_update(update)
            if b and b.cve_list:
                blocks.append(b)
        except (ET.ParseError, ValueError, KeyError, AttributeError):
            pass
    return blocks


def _fetch_xml_sync() -> str:
    """同步获取 XML 内容（使用 urllib，避免 httpx 依赖）"""
    import urllib.request
    import ssl

    ctx = ssl.create_default_context()
    req = urllib.request.Request(CVE_XML_URL, headers={"User-Agent": "cve-query/1.0"})
    with urllib.request.urlopen(req, timeout=60, context=ctx) as resp:
        return resp.read().decode("utf-8")


def fetch_cve_xml() -> "List[TSSABlock]":
    """获取并解析 CVE XML（带缓存）"""
    cache = _cache_manager.cache
    if cache and not cache.is_expired():
        return cache.tssa_blocks
    xml_content = _fetch_xml_sync()
    blocks = parse_cve_xml(xml_content)
    _cache_manager.cache = CVEXMLCache(tssa_blocks=blocks, cached_at=datetime.now())
    return blocks


def clear_xml_cache() -> None:
    _cache_manager.clear()


def get_cache_status() -> dict:
    return _cache_manager.get_status()


# ===========================================================================
# CVE 查询逻辑
# ===========================================================================


def _group_latest_by_version(blocks: "List[TSSABlock]") -> "Dict[str, TSSABlock]":
    groups = defaultdict(list)  # type: Dict[str, List[TSSABlock]]
    for b in blocks:
        ver = b.product_series or _extract_product_series(b.title, b.description)
        if ver:
            groups[ver].append(b)
    result = {}  # type: Dict[str, TSSABlock]
    for ver, vblocks in groups.items():
        result[ver] = sorted(vblocks, key=lambda x: x.updated_date or x.issued_date or "", reverse=True)[0]
    return result


def _build_cve_result(cve_id: str, version_blocks: "Dict[str, TSSABlock]") -> dict:
    if not version_blocks:
        return None
    sorted_items = sorted(
        version_blocks.items(),
        key=lambda x: x[1].updated_date or x[1].issued_date or "",
        reverse=True,
    )
    _, base = sorted_items[0]
    products = []
    for ver in sorted(version_blocks.keys()):
        b = version_blocks[ver]
        fix_ver = ", ".join(b.packages) if b.packages else ""
        p = {
            "product_id": "TencentOS-{}".format(ver),
            "product_series": ver,
            "package_name": ", ".join(b.packages[:5]) if b.packages else "",
            "fix_version": fix_ver,
            "status": "fixed" if b.packages else "investigating",
            "conclusion": f"Fixed in {b.tssa_id}" if b.packages else "Under investigation",
        }
        if b.tssa_id:
            p["security_advisory"] = {
                "id": b.tssa_id,
                "url": build_tssa_url(b.tssa_id),
                "publish_date": b.issued_date,
            }
        if b.title:
            p["comments"] = f"{ver}: {b.title}"
        products.append(p)
    return {
        "cve_id": cve_id,
        "severity": base.severity.lower() if base.severity else "unknown",
        "status": "fixed" if any(b.packages for b in version_blocks.values()) else "investigating",
        "description": base.description,
        "dates": {"publish_date": base.issued_date, "update_date": base.updated_date},
        "affected_products": products,
    }


# ===========================================================================
# 公开查询接口（供 CLI 和外部调用使用）
# ===========================================================================


def query_cve(cve_id: str) -> str:
    """查询单个 CVE 修复状态，返回 JSON 字符串（结构与原 MCP tool 一致）."""
    meta = {"tool": "query_cve", "cve_id": cve_id}
    try:
        actual = normalize_cve_id(cve_id)
        blocks = fetch_cve_xml()
        matching = [b for b in blocks if actual in [c.upper() for c in b.cve_list]]
        if not matching:
            return _error(f"CVE {actual} not found", meta)
        vb = _group_latest_by_version(matching)
        result = _build_cve_result(actual, vb)
        if result is None:
            return _error(f"CVE {actual} not found", meta)
        return _success(result, meta)
    except (ValueError, ET.ParseError, OSError) as e:
        return _error(str(e), meta)


def query_cve_batch(cve_ids_str: str) -> str:
    """批量查询多个 CVE 修复状态，返回 JSON 字符串（结构与原 MCP tool 一致）."""
    meta = {"tool": "query_cve_batch", "input": cve_ids_str}
    try:
        ids = extract_cve_ids(cve_ids_str)
        if not ids:
            return _error("No valid CVE IDs found", meta)
        blocks = fetch_cve_xml()
        results = {}  # type: Dict[str, Any]
        for cve_id in ids:
            matching = [b for b in blocks if cve_id in [c.upper() for c in b.cve_list]]
            if not matching:
                results[cve_id] = None
            else:
                vb = _group_latest_by_version(matching)
                results[cve_id] = _build_cve_result(cve_id, vb)
        found = sum(1 for v in results.values() if v is not None)
        not_found = [k for k, v in results.items() if v is None]
        meta.update({"total": len(ids), "found": found, "not_found_list": not_found})
        return _success(results, meta)
    except (ValueError, ET.ParseError, OSError) as e:
        return _error(str(e), meta)


def extract_cve_from_text(text: str) -> str:
    """从文本提取 CVE 编号，返回 JSON 字符串."""
    ids = extract_cve_ids(text)
    return _success({"total": len(ids), "cve_ids": ids}, {"tool": "extract_cve_from_text"})


def get_data_source_status() -> str:
    """获取数据源状态，返回 JSON 字符串."""
    return _success({
        "xml_source": {
            "url": CVE_XML_URL,
            "cache_duration_seconds": CVE_XML_CACHE_DURATION,
            "cache_status": get_cache_status(),
        },
    }, {"tool": "get_data_source_status"})


# ===========================================================================
# CLI 入口
# ===========================================================================


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="TencentOS CVE 漏洞查询工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
示例:
  # 查询单个 CVE
  python cve_xml_server.py query CVE-2020-15778

  # 批量查询多个 CVE
  python cve_xml_server.py query CVE-2024-1234 CVE-2024-5678

  # 从文本提取 CVE 编号
  python cve_xml_server.py extract "修复了 CVE-2024-1234 和 CVE-2024-5678"

  # 查看数据源状态
  python cve_xml_server.py status

  # 清除缓存
  python cve_xml_server.py clear
""",
    )
    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # query 子命令
    query_parser = subparsers.add_parser("query", help="查询 CVE 修复状态")
    query_parser.add_argument("cve_ids", nargs="+", help="CVE 编号（支持多个）")

    # extract 子命令
    extract_parser = subparsers.add_parser("extract", help="从文本提取 CVE 编号")
    extract_parser.add_argument("text", help="包含 CVE 编号的文本")

    # status 子命令
    subparsers.add_parser("status", help="查看数据源和缓存状态")

    # clear 子命令
    subparsers.add_parser("clear", help="清除 XML 缓存")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == "query":
        if len(args.cve_ids) == 1:
            print(query_cve(args.cve_ids[0]))
        else:
            print(query_cve_batch(" ".join(args.cve_ids)))

    elif args.command == "extract":
        print(extract_cve_from_text(args.text))

    elif args.command == "status":
        print(get_data_source_status())

    elif args.command == "clear":
        clear_xml_cache()
        print(_success({"message": "CVE XML cache cleared"}, {"tool": "clear_cache"}))


if __name__ == "__main__":
    main()
