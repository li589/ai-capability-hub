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

# BASE_URL = "https://ai.stg.pingan.com" # 测试

BASE_URL = "https://ai.stock.pingan.com" #生产

SKILL_PREFIX = "restapi/hangqing"

SKILL_ID = "market-query"

TIMEOUT = 60

API_KEY = os.getenv("PINGAN_SKILL_APIKEY", "").strip()

REQUEST_ID = str(uuid.uuid4())



# ==========================================================
# CLI指令映射
# ==========================================================

API_PATHS = {
    "quote": "adapter/hangQing/stockDynamic",              # 1. 股票/股指/ETF 实时行情查询
    "sector": "adapter/hangQing/blockDynamic",             # 2. 板块实时行情
    "sector_stocks": "adapter/hangQing/constituentDynamic",  # 3. 板块成分股实时变动
    "fundflow": "adapter/hangQing/capitalFlow",           # 4. 主力资金流向数据
    "kline": "adapter/hangQing/klineData",                 # 5. 历史K线数据
}
# ==========================================================
# HTTP 请求
# ==========================================================

def call_api(options: str, payload: dict):

    if not API_KEY:
        raise RuntimeError("缺少环境变量 PINGAN_SKILL_APIKEY")

    path = API_PATHS.get(options)

    if path is None:
        raise RuntimeError(f"未知指令：{options}")

    url = f"{BASE_URL}/{SKILL_PREFIX}/{path}"

    headers = {
        "X-API-Key": API_KEY,
        "Content-Type": "application/json",
        "X-Skill-ID": SKILL_ID,
        "X-Request-ID": REQUEST_ID,
        "channelId":"c_lite_adapgaty_a_skill",
        "requestId":REQUEST_ID
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

    if body.get("code") != 0:
        raise RuntimeError(
            body.get("error_message", "接口调用失败。")
        )

    return body.get("data", {})

# ==========================================================
# CLI
# ==========================================================

class JSONArgumentParser(argparse.ArgumentParser):
    """
    命令行解析出错提示，统一处理错误信息
    """
    def error(self, message):
        raise RuntimeError(message)

def codes_list():
    """
    把逗号分隔的代码字符串解析成列表，例如 "SH600519,SZ000001" -> ["SH600519", "SZ000001"]。
    """

    def _parse(value: str):
        return [item.strip() for item in value.split(",") if item.strip()]

    return _parse


def _compact(payload: dict) -> dict:
    """去掉值为 None 的字段后返回，供 build_payload 组装请求体使用。"""
    return {k: v for k, v in payload.items() if v is not None}


def build_parser() -> argparse.ArgumentParser:

    parser = JSONArgumentParser(description="平安证券行情 Skill")

    subparsers = parser.add_subparsers(dest="options", required=True)

    # 1. 股票/股指/ETF 实时行情查询
    p = subparsers.add_parser("quote", help="股票/股指/ETF 实时行情查询")
    p.add_argument(
        "--codes", type=codes_list(),
        help="代码列表，逗号分隔，如 SH600519,SZ000001",
    )

    # 2. 板块实时行情
    p = subparsers.add_parser("sector", help="板块实时行情")
    p.add_argument("--sector_code", help="板块代码")

    # 3. 板块成分股查询
    p = subparsers.add_parser("sector_stocks", help="板块成分股查询")
    p.add_argument("--sector_code", help="板块代码")
    p.add_argument(
        "--limit", type=int, default=None,
        help="返回条数，不传则使用默认值",
    )

    # 4. 主力资金流向数据
    p = subparsers.add_parser("fundflow", help="主力资金流向数据")
    p.add_argument(
        "--codes", type=codes_list(),
        help="代码列表，逗号分隔",
    )

    # 5. 历史K线数据
    p = subparsers.add_parser("kline", help="历史K线数据")
    p.add_argument("--code", help="股票代码")
    p.add_argument(
        "--last_n", type=int, default=None,
        help="最近 N 个交易日，不传默认取最近 5 个交易日",
    )

    return parser


def build_payload(args: argparse.Namespace) -> dict:

    if args.options == "quote":
        return _compact({"codes": args.codes})

    if args.options == "sector":
        return _compact({"sector_code": args.sector_code})

    if args.options == "sector_stocks":
        return _compact({
            "sector_code": args.sector_code,
            "limit": args.limit,
        })

    if args.options == "fundflow":
        return _compact({"codes": args.codes})

    if args.options == "kline":
        return _compact({
            "code": args.code,
            "last_n": args.last_n,
        })

    raise RuntimeError(f"未知指令：{args.options}")


def main():

    parser = build_parser()

    args = parser.parse_args()

    payload = build_payload(args)

    # 调用接口
    result = call_api(
        args.options,
        payload,
    )

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