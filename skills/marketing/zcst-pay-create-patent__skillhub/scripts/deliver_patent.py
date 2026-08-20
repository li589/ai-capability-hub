#!/usr/bin/env python3
"""Save paid patent Markdown and download its official DOCX artifact."""

from __future__ import annotations

import argparse
import json
import os
import re
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


MAX_RESPONSE_BYTES = 32 * 1024 * 1024
MAX_DOCX_BYTES = 100 * 1024 * 1024


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="交付付费专利 Markdown 和官方 DOCX。")
    parser.add_argument("--response-file", type=Path, required=True)
    parser.add_argument("--expected-out-trade-no", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args()


def load_response(path: Path, expected_order: str) -> dict[str, Any]:
    if path.stat().st_size > MAX_RESPONSE_BYTES:
        raise ValueError("响应文件超过大小限制")
    body = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(body, dict) or body.get("code") != "SUCCESS":
        raise ValueError("响应文件不是成功的专利交付结果")
    if body.get("out_trade_no") != expected_order:
        raise ValueError("响应文件订单号与预期订单不一致")
    if not isinstance(body.get("content"), str) or not body["content"].strip():
        raise ValueError("成功响应缺少 Markdown 正文")
    return body


def docx_url(body: dict[str, Any]) -> str:
    artifacts = body.get("artifacts")
    if not isinstance(artifacts, list):
        raise ValueError("成功响应缺少附件列表")
    matches = [item.get("download_url") for item in artifacts
               if isinstance(item, dict) and item.get("type") == "docx"]
    if len(matches) != 1 or not isinstance(matches[0], str):
        raise ValueError("成功响应必须包含一个 DOCX 下载地址")
    validate_download_url(matches[0])
    return matches[0]


def validate_download_url(value: str) -> None:
    parsed = urllib.parse.urlparse(value)
    if (parsed.scheme != "https"
            or parsed.hostname != "patent.ecoaitech.com"
            or parsed.port is not None
            or parsed.username is not None
            or not parsed.path.startswith("/api/download/")
            or not parsed.path.endswith("/docx")):
        raise ValueError("服务返回了不受信任的 DOCX 下载地址")


def safe_stem(title: str, out_trade_no: str) -> str:
    cleaned = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "-", title).strip(" .-")
    cleaned = re.sub(r"\s+", " ", cleaned) or "专利文档"
    return f"{cleaned[:80]}-{out_trade_no}"


def atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    temporary = Path(name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(content.rstrip() + "\n")
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def download_docx(url: str, path: Path) -> None:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "User-Agent": "zcst-pay-create-patent/1.0",
        },
        method="GET",
    )
    with urllib.request.urlopen(request, timeout=120) as response:
        content = response.read(MAX_DOCX_BYTES + 1)
    if len(content) > MAX_DOCX_BYTES:
        raise ValueError("DOCX 文件超过大小限制")
    if len(content) < 4 or not content.startswith(b"PK"):
        raise ValueError("下载结果不是有效的 DOCX 文件")
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    temporary = Path(name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(content)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def main() -> int:
    args = parse_args()
    try:
        body = load_response(args.response_file, args.expected_out_trade_no)
        title = body.get("title") if isinstance(body.get("title"), str) else "专利文档"
        stem = safe_stem(title, args.expected_out_trade_no)
        output_dir = args.output_dir.resolve()
        markdown_path = output_dir / f"{stem}.md"
        docx_path = output_dir / f"{stem}.docx"
        atomic_write_text(markdown_path, body["content"])
        download_docx(docx_url(body), docx_path)
        print(json.dumps({
            "status": "succeeded",
            "out_trade_no": args.expected_out_trade_no,
            "title": title,
            "markdown_path": str(markdown_path),
            "docx_path": str(docx_path),
            "response_file": str(args.response_file.resolve()),
        }, ensure_ascii=False, indent=2))
        return 0
    except (OSError, urllib.error.URLError, json.JSONDecodeError, ValueError) as exception:
        print(json.dumps({"status": "failed", "error": str(exception)}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
