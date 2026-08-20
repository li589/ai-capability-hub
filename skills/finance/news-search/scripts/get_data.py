#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import argparse
import json
import os
import sys
import uuid
import requests

# ==========================================================
# 基础配置（每个 Skill 修改）
# ==========================================================

BASE_URL = "https://ai.stock.pingan.com" #生产

SKILL_PREFIX = "restapi/zixun"

API_PATHS = "e-server-transfer-service/dify/retrieval"

SKILL_ID = "news-search"

TIMEOUT = 60

API_KEY = os.getenv("PINGAN_SKILL_APIKEY", "").strip()

KB_IDS = "1_3_237_v2"

KB_TOKEN = "e4c34022e6a64e0d83dfea24b1540415"  


# ==========================================================
# HTTP 请求
# ==========================================================

def call_api(payload: dict):

    if not API_KEY:
        raise RuntimeError("缺少环境变量 PINGAN_SKILL_APIKEY")

    url = f"{BASE_URL}/{SKILL_PREFIX}/{API_PATHS}"

    headers = {
        "X-API-Key": API_KEY,
        "Content-Type": "application/json",
        "X-Skill-ID": SKILL_ID,
        "X-Request-ID": str(uuid.uuid4()),
        "Authorization": f"Bearer {KB_TOKEN}",
    }

    response = requests.post(
        url,
        json=payload,
        headers=headers,
        timeout=TIMEOUT,
    )

    # ----------------------------
    # HTTP 错误处理
    # ----------------------------

    if response.status_code == 401:
        raise RuntimeError("缺少 API Key。")

    if response.status_code == 403:
        raise RuntimeError("API Key 无效或没有权限。")

    if response.status_code == 429:

        body = response.json()

        error_code = body.get("error_code")

        if error_code == "RATE_LIMIT_EXCEEDED":
            raise RuntimeError("接口调用频率超限。")

        if error_code == "DAILY_QUOTA_EXCEEDED":
            raise RuntimeError("今日调用次数已达上限。")

        raise RuntimeError("请求超过限制。")

    if response.status_code == 503:
        raise RuntimeError("服务暂时不可用，请稍后重试。")

    response.raise_for_status()

    body = response.json()

    return body.get("records", []) or body

# ==========================================================
# CLI
# ==========================================================

class JSONArgumentParser(argparse.ArgumentParser):
    """
    命令行解析出错提示，统一处理错误信息
    """
    def error(self, message):
        raise RuntimeError(message)


def build_parser():

    parser = JSONArgumentParser(description="平安证券股友圈 Skill")

    parser.add_argument(
        "--question",
        required=True,
        help="用户问题",
    )
    parser.add_argument(
        "--top_k",
        type=int,
        default=5,
        help="召回数量",
    )

    return parser


def main():

    parser = build_parser()

    args = parser.parse_args()

    payload = {
        "knowledge_id": KB_IDS,
        "query": args.question,
        "retrieval_setting": {
            "top_k": args.top_k,
            "score_threshold": 0.1,
        },
    }

    # 调用接口
    result = call_api(payload)

    print(
        json.dumps(
            result,
            ensure_ascii=False,
        )
    )

# ==========================================================
# 主程序入口
# ==========================================================

if __name__ == "__main__":

    try:
        main()
    except Exception as e:
        # 错误处理
        print(
            json.dumps(
                {
                    "error": str(e)
                },
                ensure_ascii=False,
            ),
            file=sys.stderr,
        )

        sys.exit(1)