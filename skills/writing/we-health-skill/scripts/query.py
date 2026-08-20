#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""微医健康技能 — 健康查询脚本。

支持场景：报告解读、医生/医院/科室推荐、健康咨询、用药咨询、药盒识别。

用法:
  python3 query.py "用户的健康问题"                    # 纯文本查询
  python3 query.py "用户问题" --region 北京            # 带地区查询
  python3 query.py "用户问题" --no-followup            # 跳过追问直接解读（报告解读）
  python3 query.py --stdin << 'EOF'                    # stdin JSON 模式
  {"query":"...","region":"北京","file_list":[...],"no_followup":true}
  EOF

API Key 通过 credential.py 管理（macOS Keychain 直存，失败回退 AES-GCM 加密文件）。
配置 API Key：python3 scripts/credential.py set <key>
"""

import importlib
import json
import os
import sys
import urllib.error
import urllib.request
from typing import Any

# 同目录导入 credential 模块
_script_dir = os.path.dirname(os.path.abspath(__file__))
if _script_dir not in sys.path:
    sys.path.insert(0, _script_dir)
get_key = importlib.import_module("credential").get_key

# ── 配置 ──────────────────────────────────────────────

API_URL = "https://aichat.guahao.com/chat/v1/wecare/skills/api/workbuddy/chat"
TIMEOUT_SECONDS = 120

# Windows 下强制 UTF-8 输出
if sys.platform == "win32":
    for _stream in (sys.stdout, sys.stderr):
        _reconfigure = getattr(_stream, "reconfigure", None)
        if _reconfigure is not None:
            _reconfigure(encoding="utf-8", errors="replace")


# ── 参数解析 ──────────────────────────────────────────

def parse_args() -> dict[str, Any]:
    args = sys.argv[1:]
    result: dict[str, Any] = {
        "query": "", "file_list": None, "use_stdin": False,
        "region": "", "no_followup": False,
    }

    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--stdin":
            result["use_stdin"] = True
        elif arg == "--no-followup":
            result["no_followup"] = True
        elif arg == "--region":
            if i + 1 < len(args):
                result["region"] = args[i + 1]
                i += 1
        elif arg.startswith("--region="):
            result["region"] = arg[len("--region="):]
        elif not arg.startswith("--") and not result["query"]:
            result["query"] = arg
        i += 1
    return result


# ── 验证 ──────────────────────────────────────────────

def validate_file_list(file_list: Any) -> tuple[bool, str]:
    if not isinstance(file_list, list):
        return False, "file_list 必须是数组"
    for item in file_list:
        if not isinstance(item, dict):
            return False, "file_list 元素必须是对象"
        if not item.get("file_url") and not item.get("file_base64"):
            return False, "file_list 元素必须包含 file_url 或 file_base64"
        if item.get("file_type") and item["file_type"] not in ("pic", "pdf"):
            return False, "file_type 必须是 pic 或 pdf"
    return True, ""


# ── 主流程 ────────────────────────────────────────────

def main() -> None:
    args = parse_args()
    user_query: str = args["query"]
    file_list = args["file_list"]
    region: str = args["region"]
    no_followup: bool = args["no_followup"]

    # stdin 模式
    if args["use_stdin"]:
        stdin_raw = sys.stdin.read()
        if not stdin_raw.strip():
            print("错误: --stdin 模式需要管道输入 JSON 数据", file=sys.stderr)
            print('示例: echo \'{"query":"..."}\' | python3 query.py --stdin', file=sys.stderr)
            sys.exit(1)

        try:
            stdin_data = json.loads(stdin_raw)
        except json.JSONDecodeError as e:
            print(f"错误: stdin JSON 解析失败 - {e}", file=sys.stderr)
            sys.exit(1)

        query_val = stdin_data.get("query")
        if not isinstance(query_val, str) or not query_val.strip():
            print("错误: stdin JSON 必须包含非空 query 字段", file=sys.stderr)
            sys.exit(1)

        user_query = query_val.strip()

        if "file_list" in stdin_data:
            valid, error = validate_file_list(stdin_data["file_list"])
            if not valid:
                print(f"错误: {error}", file=sys.stderr)
                sys.exit(1)
            file_list = stdin_data["file_list"]

        region_val = stdin_data.get("region")
        if isinstance(region_val, str) and region_val.strip():
            region = region_val.strip()

        # stdin 中也可指定 no_followup
        if stdin_data.get("no_followup"):
            no_followup = True

    # 读取 API Key（Keychain 优先，加密文件兜底）
    cred = get_key()
    api_key = cred["key"]
    if not api_key:
        print(
            "缺少 API Key。请先配置：\n"
            "  python3 scripts/credential.py set <你的key>",
            file=sys.stderr,
        )
        sys.exit(1)

    if not user_query:
        print(
            "缺少查询内容。用法：\n"
            '  python3 query.py "我想咨询皮肤科医生"\n'
            '  或 echo \'{"query":"..."}\' | python3 query.py --stdin',
            file=sys.stderr,
        )
        sys.exit(1)

    # 如果有用户地区信息，附加到查询中以便 API 精准匹配
    if region:
        user_query = f"用户所在地区：{region}。{user_query}"

    # 报告解读场景：跳过追问，直接解读
    # 在 query 末尾追加「直接解读」关键词，触发服务端跳过追问机制
    if no_followup:
        user_query = f"{user_query}（请直接解读报告，无需追问，直接给出解读结果）"

    # 构建请求体
    body: dict[str, Any] = {"query": user_query}
    if isinstance(file_list, list) and len(file_list) > 0:
        body["file_list"] = file_list

    body_bytes = json.dumps(body, ensure_ascii=False).encode("utf-8")

    # 发送请求
    req = urllib.request.Request(
        API_URL,
        data=body_bytes,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as response:
            if response.status != 200:
                print(f"请求失败: HTTP {response.status}", file=sys.stderr)
                sys.exit(1)
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        print(f"请求失败: HTTP {e.code}", file=sys.stderr)
        sys.exit(1)
    except TimeoutError:
        print("请求超时（已等待 2 分钟），请稍后重试。", file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as e:
        reason = str(e.reason)
        if "timed out" in reason:
            print("请求超时（已等待 2 分钟），请稍后重试。", file=sys.stderr)
        else:
            print(f"请求异常: {reason}", file=sys.stderr)
        sys.exit(1)

    # 提取 data.markdown_content 展示给用户
    content = data.get("data", {}).get("markdown_content") if isinstance(data, dict) else None
    if isinstance(content, str) and content:
        print(content)
    else:
        print("未获取到有效回复内容", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
