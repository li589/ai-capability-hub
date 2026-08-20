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

SKILL_PREFIX = "restapi/guyouquan"

SKILL_ID = "guyouquan-query"

TIMEOUT = 60

API_KEY = os.getenv("PINGAN_SKILL_APIKEY", "").strip()


# ==========================================================
# CLI指令映射
# ==========================================================

API_PATHS = {
    "search_circle": "e-server-transfer-service/dify/retrieval",        # 搜索圈子
    "hot_posts": "e-server-transfer-service/dify/retrieval",            # 热点内容
    "hot_holdings": "follow-svc/option/stockFriendCircle/queryHotStock",   # 热门持仓
}




# ==========================================================
# 选择不同查询库
# ==========================================================

KB_IDS = {
    "search_circle": "1_3_287_v2",
    "hot_posts": "1_3_288_v2",
}

# KB_TOKEN = "0c1aab1c9cfa444b9636d4918f80e389"   # 测试环境

KB_TOKEN = "e4c34022e6a64e0d83dfea24b1540415"  # 生产

KB_OPTIONS = {
    "search_circle",
    "hot_posts",
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

    # 知识库接口header
    if options in KB_OPTIONS:

        headers = {
            "X-API-Key": API_KEY,
            "Content-Type": "application/json",
            "X-Skill-ID": SKILL_ID,
            "X-Request-ID": str(uuid.uuid4()),      
            "Authorization": f"Bearer {KB_TOKEN}",
        }

    # 热门持仓接口header
    else:
        headers = {
            "X-API-Key": API_KEY,
            "Content-Type": "application/json",
            "X-Skill-ID": SKILL_ID,
            "X-Request-ID": str(uuid.uuid4()),
        }

    # print(url)
    # print(json.dumps(payload, ensure_ascii=False, indent=2))
    # print(json.dumps(headers, ensure_ascii=False, indent=2))

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


    if not (body.get("msg") == None or body.get("status") == "1"):
        raise RuntimeError(body.get("msg") or "接口调用失败。")

    if options in KB_OPTIONS:
        return body.get("records", [])
    else:
        return body.get("results", {})

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

    subparsers = parser.add_subparsers(dest="options", required=True)

    # 1. 搜索圈子
    p = subparsers.add_parser(
        "search_circle",
        help="搜索圈子"
    )
    p.add_argument(
        "--question",
        required=True,
        help="用户问题"
    )
    p.add_argument(
        "--top_k",
        type=int,
        required=True,
        help="召回数量"
    )

    # 2. 圈子热点内容
    p = subparsers.add_parser(
        "hot_posts",
        help="查看圈子热点内容"
    )
    p.add_argument(
        "--question",
        required=True,
        help="用户问题"
    )
    p.add_argument(
        "--top_k",
        type=int,
        required=True,
        help="召回数量"
    )

    # 3. 热门持仓
    p = subparsers.add_parser(
        "hot_holdings",
        help="查看圈子热门持仓"
    )
    p.add_argument(
        "--circle_id",
        type=int,
        required=True,
        help="圈子ID"
    )
    # p.add_argument(
    #     "--sort_type",
    #     default="1",
    #     choices=["1"],
    #     help="排序方式，默认1：持仓人数排序"
    # )

    return parser


def build_payload(args):

    # 两个知识库接口
    if args.options in ("search_circle", "hot_posts"):
        return {
            "knowledge_id": KB_IDS[args.options],
            "query": args.question,
            "retrieval_setting":{
                "top_k": args.top_k,
                "score_threshold":0.1
                }
        }

    # 热门持仓接口
    if args.options == "hot_holdings":
        return {
            "channel":"PASkill",
            "requestId":str(uuid.uuid4()),
            "body":{
                "circleId": args.circle_id,
                "sortType": "1"
                }
        }

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