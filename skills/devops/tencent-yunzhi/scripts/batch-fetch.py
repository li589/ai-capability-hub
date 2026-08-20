#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
batch-fetch.py — 批量获取乐享 v1 团队文档 parsed-content

用法：
  # 拉取一个 v1 团队某目录下所有文档（用 parsed-content 接口）
  python3 batch-fetch.py --v1 --team-id <UUID> --node-id <folder_id> --out ./out/

Token 来源优先级（与 docs-v1.py / assets-v1.py 一致）：
  1. LEXIANG_TOKEN 环境变量
  2. ~/.workbuddy/mcp.json 或 ~/.mcporter/mcporter.json 的 lexiang Authorization

环境变量：
  COMPANY_FROM   选填，默认 CSIG（永久默认值）

设计目标：
  - 一次脚本完成 v1「列目录 → 拉取 parsed-content → 落盘」
  - v2 批量读取请用 MCP 工具组合：entry_list_children + entry_describe_ai_parse_content
  - 失败容错：单条失败不中断，统计后输出报告

依赖：仅标准库（urllib），Python 3.9+（使用了 list[dict] 等内置泛型注解）。
"""
import argparse
import json
import os
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path

API_HOST = "https://lxapi.lexiangla.com"
DEFAULT_COMPANY_FROM = "CSIG"  # 永久默认值，禁止改动


def redact(text: str) -> str:
    """脱敏：抹掉日志/异常中可能出现的 token，避免泄露。"""
    import re
    s = str(text)
    s = re.sub(r"lxmcp_[A-Za-z0-9._\-]+", "lxmcp_***", s)
    s = re.sub(r"(Bearer\s+)\S+", r"\1***", s)
    return s


def resolve_token() -> str:
    """Resolve token: 环境变量 → 本地 mcp.json，不在 shell 历史中留痕。"""
    token = os.environ.get("LEXIANG_TOKEN", "").strip()
    if token:
        return token.replace("Bearer ", "", 1).strip()

    for config_path in (
        Path.home() / ".workbuddy" / "mcp.json",
        Path.home() / ".mcporter" / "mcporter.json",
    ):
        try:
            data = json.loads(config_path.read_text(encoding="utf-8"))
            auth = (
                data.get("mcpServers", {})
                .get("lexiang", {})
                .get("headers", {})
                .get("Authorization", "")
            )
            token = auth.replace("Bearer ", "", 1).strip()
            if token:
                return token
        except (OSError, json.JSONDecodeError):
            continue

    sys.exit("❌ 未找到 LEXIANG_TOKEN。请设置环境变量，或在本地 mcp.json 中配置 lexiang Authorization。")


def http_get(url: str, token: str, timeout: int = 30, retries: int = 2) -> dict:
    """带超时与简单重试的 GET；4xx 不重试，网络错误/5xx 重试。"""
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        },
    )
    last_err = None
    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if 400 <= e.code < 500:
                raise  # 客户端错误（401/404 等）重试无意义
            last_err = e
        except (urllib.error.URLError, TimeoutError) as e:
            last_err = e
        if attempt < retries:
            time.sleep(1.5 * (attempt + 1))
    raise last_err


def fetch_v1_doc_parsed(doc_id: str, token: str) -> str:
    """v1 文档 → parsed_content（已解析 Markdown）"""
    url = f"{API_HOST}/cgi-bin/v1/docs/{doc_id}/parsed-content"
    data = http_get(url, token)
    return data.get("data", {}).get("attributes", {}).get("parsed_content", "")


def fetch_v1_team_docs(team_id: str, node_id: str, token: str) -> list[dict]:
    """列出 v1 团队某目录下的文档"""
    url = (
        f"{API_HOST}/cgi-bin/v1/staffs/x/app-data"
        f"?module_type=doc&team_id={team_id}&directory_id={node_id}"
    )
    data = http_get(url, token)
    return data.get("data", [])


def safe_filename(name: str, doc_id: str) -> str:
    """文件名安全化：去掉特殊字符，保留可读性"""
    safe = "".join(c if c.isalnum() or c in "-_." else "_" for c in name)[:80]
    return f"{safe}-{doc_id[:8]}.md"


def main():
    parser = argparse.ArgumentParser(description="批量获取乐享文档内容")
    parser.add_argument("--v1", action="store_true", help="走 1.0 REST API（当前脚本仅支持 v1）")
    parser.add_argument("--team-id", help="v1 团队 UUID")
    parser.add_argument("--node-id", help="v1 目录 node_id")
    parser.add_argument("--out", default="./out", help="输出目录")
    parser.add_argument("--limit", type=int, default=100, help="最多处理多少篇")
    args = parser.parse_args()

    token = resolve_token()
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    success, failed = [], []

    if not args.v1:
        sys.exit("❌ 当前脚本仅支持 v1 REST 批量读取。v2 请使用 MCP 工具组合。")
    if not (args.team_id and args.node_id):
        sys.exit("❌ --v1 模式需要 --team-id 和 --node-id")

    print(f"[v1] 获取团队 {args.team_id} 目录 {args.node_id} 下文档列表...")
    docs = fetch_v1_team_docs(args.team_id, args.node_id, token)[: args.limit]
    print(f"[v1] 共 {len(docs)} 篇文档，开始拉取正文...")
    for i, doc in enumerate(docs, 1):
        doc_id = doc.get("id") or doc.get("attributes", {}).get("doc_id")
        name = doc.get("attributes", {}).get("name", "untitled")
        try:
            content = fetch_v1_doc_parsed(doc_id, token)
            fname = safe_filename(name, doc_id)
            (out_dir / fname).write_text(content, encoding="utf-8")
            print(f"  [{i}/{len(docs)}] ✅ {fname}")
            success.append(fname)
        except urllib.error.HTTPError as e:
            print(f"  [{i}/{len(docs)}] ❌ {name}: HTTP {e.code}")
            failed.append({"name": name, "doc_id": doc_id, "error": f"HTTP {e.code}"})
        except Exception as e:
            print(f"  [{i}/{len(docs)}] ❌ {name}: {redact(e)}")
            failed.append({"name": name, "doc_id": doc_id, "error": redact(e)})
        time.sleep(0.2)  # 简单限速

    print("\n=== 报告 ===")
    print(f"✅ 成功：{len(success)} 篇 → {out_dir.resolve()}")
    print(f"❌ 失败：{len(failed)} 篇")
    if failed:
        report_path = out_dir / "_failed.json"
        report_path.write_text(json.dumps(failed, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"   失败详情已写入：{report_path}")


if __name__ == "__main__":
    main()
