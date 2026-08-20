#!/usr/bin/env python3
"""文本搜索 CLI入口"""

COMMAND_NAME = "text_search"
COMMAND_DESC = "文本搜索商品"

import os
import sys
import argparse

sys.path.insert(0, os.path.normpath(os.path.join(os.path.dirname(__file__), '..', '..')))

from _auth import get_ak_from_env
from _output import print_output, print_error, format_products_table

from capabilities.text_search.service import text_search


def main():
    ak_id, _ = get_ak_from_env()
    if not ak_id:
        print_output(False,
                     "❌ AK 未配置，无法进行文本搜索。\n\n如果还没有 API_KEY，请前往 https://clawhub.1688.com/ 获取。\n\n运行: `cli.py configure YOUR_AK`",
                     {"data": {}})
        return

    parser = argparse.ArgumentParser(description="文本搜索 - 通过关键词搜索商品")
    parser.add_argument("--query", "-q", required=True, help="搜索关键词")
    parser.add_argument("--platform", "-p", default="1688", help="目标平台，默认 1688")
    parser.add_argument("--limit", "-l", type=int, default=10, help="返回数量，默认 10")
    args = parser.parse_args()

    try:
        result = text_search(
            query=args.query,
            platform=args.platform,
            limit=args.limit
        )
        
        # 构建输出消息
        total = result.get("total_results", 0)
        products = result.get("similar_products", [])
        
        if total > 0:
            header = f"✅ 搜索「{args.query}」找到 {total} 个商品"
            message = format_products_table(products, header)
        else:
            message = f"未找到与「{args.query}」相关的商品"
        
        print_output(True, message, {"data": result})
    except Exception as e:
        print_error(e, {"data": {}})


if __name__ == "__main__":
    main()
