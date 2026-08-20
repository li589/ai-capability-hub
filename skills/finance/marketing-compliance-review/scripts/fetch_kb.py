#!/usr/bin/env python3
"""按需从腾讯云 COS 拉取知识库原文。

用法:
  python3 scripts/fetch_kb.py <文件名> [COS_BASE_URL]

环境变量 COS_BASE_URL 也可预设基础地址（如 https://<bucket>.cos.ap-guangzhou.myqcloud.com/kb/）。
输出: 该文件的 Markdown 全文到 stdout。
"""
import os
import sys
import urllib.parse
import urllib.request
import urllib.error


def main():
    if len(sys.argv) < 2:
        sys.stderr.write("用法: fetch_kb.py <文件名> [COS_BASE_URL]\n")
        sys.exit(2)

    fname = sys.argv[1]
    base = sys.argv[2] if len(sys.argv) > 2 else os.environ.get("COS_BASE_URL", "")
    if not base:
        sys.stderr.write("缺少 COS_BASE_URL：请作为参数传入或设置环境变量。\n")
        sys.exit(2)

    base = base.rstrip("/") + "/"
    # 文件名含中文/括号/· 等，必须做 URL 编码（保留 / 以兼容潜在子路径）
    url = base + urllib.parse.quote(fname, safe="/")

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "marketing-compliance-review/1.0.5"})
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = resp.read()
        # 优先按 utf-8 解码，失败回退宽松解码
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            text = data.decode("utf-8", errors="replace")
        sys.stdout.write(text)
    except urllib.error.HTTPError as e:
        sys.stderr.write(f"拉取失败 HTTP {e.code}: {url}\n")
        sys.exit(1)
    except Exception as e:  # noqa: BLE001
        sys.stderr.write(f"拉取失败: {e}\nURL: {url}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
