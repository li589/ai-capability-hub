#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ETF 筛选执行脚本
"""
import argparse
import json
import os
import sys
import uuid
import requests

# ==========================================================
# 基础配置（每个 Skill 修改）
# ==========================================================

# BASE_URL = "https://ai.stg.pingan.com" # 测试

BASE_URL = "https://ai.stock.pingan.com" #生产

SKILL_PREFIX = "restapi/jinku"

API_PATH = "omm/v2/http/mop/vault/query"

SKILL_ID = "etf-filter"

TIMEOUT = 60

API_KEY = os.getenv("PINGAN_SKILL_APIKEY", "").strip()

# 固定值参数

FIXED_PARAMS = {
    "key": "ETF_FILTER",
}



# ==========================================================
# HTTP 请求
# ==========================================================

def call_api(payload: dict):

    if not API_KEY:
        raise RuntimeError("缺少环境变量 PINGAN_SKILL_APIKEY")

    url = f"{BASE_URL}/{SKILL_PREFIX}/{API_PATH}"

    headers = {
        "X-API-Key": API_KEY,
        "Content-Type": "application/json",
        "X-Skill-ID": SKILL_ID,
        "X-Request-ID": str(uuid.uuid4()),
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

    return body.get("rows", []) or body


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
    parser = JSONArgumentParser(
        description="ETF 筛选 Skill"
    )
    parser.add_argument(
        "--payload",
        required=True,
        help=(
            "完整请求体 JSON 字符串，包含 wheres/fields/orderBy/orderType/pageSize，"
            "字段与取值说明见 SKILL.md。示例："
            '\'{"wheres":[{"field":"pe","type":2,"value":20}],'
            '"orderBy":"pe","orderType":"A","pageSize":20}\''
        ),
    )
    return parser

def build_body(args):
    try:
        payload = json.loads(args.payload)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"--payload 不是合法 JSON：{e}")


    # key 始终固定为 ETF_FILTER
    payload.update(FIXED_PARAMS)

    return payload


def main():

    parser = build_parser()

    args = parser.parse_args()

    body = build_body(args)

    # 调用接口
    result = call_api(body)

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
