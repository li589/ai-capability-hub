"""Search and fetch the bundled Jiandaoyun official API documentation catalog."""

import json
import re
import urllib.error
import urllib.request
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

from .errors import JiandaoyunError


SKILL_ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = SKILL_ROOT / "references" / "official-api-index.json"
TOOL_MAP_PATH = SKILL_ROOT / "references" / "tool-doc-map.json"
OFFICIAL_HOST = "hc.jiandaoyun.com"


def load_catalog():
    return json.loads(CATALOG_PATH.read_text(encoding="utf-8"))


def load_tool_map():
    return json.loads(TOOL_MAP_PATH.read_text(encoding="utf-8"))


def search_docs(query):
    value = query.strip().casefold()
    if not value:
        raise JiandaoyunError("invalid_input", "文档搜索词不能为空。")
    return [
        entry
        for entry in load_catalog()["entries"]
        if value in entry["title"].casefold() or value == entry["id"]
    ]


def docs_for_tool(tool_name):
    mapping = load_tool_map()
    doc_ids = mapping.get(tool_name)
    if not doc_ids:
        raise JiandaoyunError("unknown_operation", f"没有找到工具对应的官方文档：{tool_name}")
    by_id = {entry["id"]: entry for entry in load_catalog()["entries"]}
    return [by_id[doc_id] for doc_id in doc_ids]


def resolve_doc(reference):
    value = reference.strip()
    catalog = load_catalog()["entries"]
    exact = [
        entry
        for entry in catalog
        if value in {entry["id"], entry["url"], entry["title"]}
    ]
    if len(exact) == 1:
        return exact[0]
    matches = search_docs(value)
    if len(matches) == 1:
        return matches[0]
    if not matches:
        raise JiandaoyunError("not_found", f"没有找到官方文档：{reference}")
    raise JiandaoyunError(
        "ambiguous_document",
        f"文档名称不唯一，请改用文档ID：{reference}",
        details=[{"id": item["id"], "title": item["title"]} for item in matches],
    )


def fetch_doc(reference, *, opener=None, timeout=30):
    entry = resolve_doc(reference)
    parsed = urlparse(entry["url"])
    if parsed.scheme != "https" or parsed.hostname != OFFICIAL_HOST:
        raise JiandaoyunError("unsafe_document_url", "只允许读取简道云官方帮助中心文档。")
    request = urllib.request.Request(
        entry["url"],
        method="GET",
        headers={"User-Agent": "jiandaoyun-api-skill/0.2.0"},
    )
    try:
        response = (opener or urllib.request.urlopen)(request, timeout=timeout)
        body = response.read().decode("utf-8", errors="replace")
    except (urllib.error.HTTPError, urllib.error.URLError, OSError) as exc:
        raise JiandaoyunError(
            "document_fetch_failed",
            f"无法读取简道云官方文档：{entry['url']}",
            retryable=True,
            details=str(exc),
        ) from exc
    parser = OfficialContentParser()
    parser.feed(body)
    content = parser.text()
    if not content:
        raise JiandaoyunError(
            "document_parse_failed",
            "官方文档页面结构可能已变化，未能提取正文；请直接打开返回的URL。",
            details={"url": entry["url"]},
        )
    return {**entry, "content": content}


class OfficialContentParser(HTMLParser):
    """Extract readable text from the official page's x-page-content container."""

    BLOCK_TAGS = {"h1", "h2", "h3", "h4", "p", "li", "tr", "pre", "div"}
    SKIP_TAGS = {"script", "style", "noscript"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self._capture_depth = 0
        self._skip_depth = 0
        self._parts = []

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        classes = set(attrs_dict.get("class", "").split())
        if not self._capture_depth and "x-page-content" in classes:
            self._capture_depth = 1
            return
        if self._capture_depth:
            self._capture_depth += 1
            if tag in self.SKIP_TAGS:
                self._skip_depth += 1
            if tag in self.BLOCK_TAGS:
                self._parts.append("\n")

    def handle_endtag(self, tag):
        if not self._capture_depth:
            return
        if tag in self.SKIP_TAGS and self._skip_depth:
            self._skip_depth -= 1
        if tag in self.BLOCK_TAGS:
            self._parts.append("\n")
        self._capture_depth -= 1

    def handle_data(self, data):
        if self._capture_depth and not self._skip_depth:
            self._parts.append(data)

    def text(self):
        value = "".join(self._parts).replace("\u00a0", " ")
        value = re.sub(r"[ \t\r\f\v]+", " ", value)
        value = re.sub(r" *\n+ *", "\n", value)
        value = re.sub(r"\n{3,}", "\n\n", value)
        return value.strip()
