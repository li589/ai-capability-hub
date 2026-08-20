#!/usr/bin/env python3
"""链接搜索 CLI入口"""

COMMAND_NAME = "link_search"
COMMAND_DESC = "链接找同款"

import os
import sys
import argparse

sys.path.insert(0, os.path.normpath(os.path.join(os.path.dirname(__file__), '..', '..')))

from _auth import get_ak_from_env
from _output import print_output, print_error, format_products_table

from capabilities.link_search.service import link_search, link_search_with_image


def main():
    ak_id, _ = get_ak_from_env()
    if not ak_id:
        print_output(False,
                     "❌ AK 未配置，无法进行链接搜索。\n\n如果还没有 API_KEY，请前往 https://clawhub.1688.com/ 获取。\n\n运行: `cli.py configure YOUR_AK`",
                     {"data": {}})
        return

    parser = argparse.ArgumentParser(description="链接搜索 - 通过商品链接找同款")
    parser.add_argument("--url", "-u", required=True, help="商品链接或商品 ID")
    parser.add_argument("--image", "-i", help="商品图片 URL（当自动获取失败时使用）")
    parser.add_argument("--platform", "-p", default="1688", help="目标平台，默认 1688")
    parser.add_argument("--limit", "-l", type=int, default=10, help="返回数量，默认 10")
    args = parser.parse_args()

    try:
        # 如果提供了图片 URL，直接使用图片搜索
        if args.image:
            result = link_search_with_image(
                image_url=args.image,
                limit=args.limit
            )
        else:
            result = link_search(
                url=args.url,
                platform=args.platform,
                limit=args.limit
            )
        
        # 检查是否需要用户输入图片 URL
        if not result.get("success") and result.get("action") == "need_image_url":
            message = f"⚠️ {result.get('message')}\n\n"
            message += "请使用 `--image` 参数提供商品图片 URL：\n"
            message += f"python cmd.py --url \"{args.url}\" --image \"图片URL\""
            print_output(False, message, {"data": result})
            return
        
        # 构建输出消息
        total = result.get("total_results", 0)
        products = result.get("similar_products", [])
        
        if total > 0:
            header = f"✅ 找到 {total} 个同款/匹配商品"
            if result.get("source_image"):
                header += f"\n\n📷 商品主图: {result.get('source_image')}"
            message = format_products_table(products, header)
        else:
            message = "未找到匹配商品"
        
        print_output(True, message, {"data": result})
    except Exception as e:
        print_error(e, {"data": {}})


if __name__ == "__main__":
    main()
