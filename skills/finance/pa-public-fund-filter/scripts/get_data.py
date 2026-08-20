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

SKILL_PREFIX = "restapi/jinku"

API_PATH = "omm/v2/http/shelf/inside/queryFundRankList"

SKILL_ID = "public-fund-filter"

TIMEOUT = 60

API_KEY = os.getenv("PINGAN_SKILL_APIKEY", "").strip()

# 固定值参数：这些字段业务上不需要用户/Skill 指定，直接写死，不在 SKILL.md 中暴露
FIXED_PARAMS = {
    "channel": "10038",   # 固定渠道号
    "curPage": 1,         # 只取第一页
    "isSales": "0",       # 仅代销
    "isBuy": "0",         # 仅可购买
}

# 排序字段的默认排序方向：D-降序 A-升序
# 依据接口文档：收益、夏普、卡玛、盈利概率通常降序；回撤、波动率、最长套牢天数通常升序
DEFAULT_SORT_TYPE = {
    "avgreturn": "D",
    "yearlyroe": "D",
    "maxWithdraw": "A",
    "volatilityRatio": "A",
    "sharpRatio": "D",
    "kamaRatio": "D",
    "maxEntangleDay": "A",
    "profitability": "D",
}

# 特色榜单：榜单类型 -> rankKey（rankNo 排序字段只在特色榜单场景下使用）
SPECIAL_RANK_KEYS = {
    "hot": "rank3881",        # 热销榜
    "popularity": "rank3882",  # 人气榜
    "dingtou": "rank3863",     # 定投榜
}

PERIOD_CHOICES = [
    "day", "week", "month", "quarter", "halfyear", "year",
    "twoyear", "threeyear", "fiveyear", "thisyear", "sincefound",
]


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

    data = body.get("data", [])
    
    if isinstance(data, list):
        for fund in data:
            if isinstance(fund, dict):
                fund.pop("rankExpandList", None)
    
    return data


# ==========================================================
# CLI
# ==========================================================

class JSONArgumentParser(argparse.ArgumentParser):
    """
    命令行解析出错提示，统一处理错误信息
    """
    def error(self, message):
        raise RuntimeError(message)


def add_common_filters(subparser):
    """rank / special 两个子命令共用的筛选参数"""
    subparser.add_argument(
        "--firstITypes",
        help="基金类型，多个用逗号隔开，如 股票型,混合型,债券型",
    )
    subparser.add_argument(
        "--fundKyp",
        help="标签，最多3个，逗号隔开，如 FT3001,FT562",
    )
    subparser.add_argument(
        "--specifiRisk",
        choices=["1", "2", "3", "4", "5"],
        help="风险等级：1低风险 2中低风险 3中等风险 4中高风险 5高风险",
    )
    subparser.add_argument(
        "--scaleType",
        choices=["1", "2", "3", "4", "5"],
        help="基金规模(亿元)：1<=2 2:2~10 3:10~50 4:50~100 5:>100",
    )
    subparser.add_argument(
        "--setupTimeType",
        choices=["1", "2", "3", "4", "5", "6"],
        help="成立年限：1<=1 2:1~2 3:2~3 4:3~4 5:4~5 6:>5",
    )
    subparser.add_argument(
        "--rateDiscountType",
        choices=["1", "2"],
        help="申购费率：1零费率 2一折",
    )
    subparser.add_argument(
        "--pageSize",
        type=int,
        default=5,
        help="返回数量，默认5，建议10~50",
    )


def build_parser():
    parser = JSONArgumentParser(
        description="场外基金排行榜 Skill"
    )

    sub = parser.add_subparsers(dest="command", required=True)

    # ---- rank：按单一指标排序的通用榜单 ----
    p_rank = sub.add_parser(
        "rank",
        help="按指标排序查询基金榜单（收益/回撤/夏普/卡玛/波动率/盈利概率等）",
    )
    p_rank.add_argument(
        "--field",
        required=True,
        choices=list(DEFAULT_SORT_TYPE.keys()),
        help=(
            "排序字段：avgreturn阶段收益 yearlyroe七日年化 maxWithdraw最大回撤 "
            "volatilityRatio波动率 sharpRatio夏普比率 kamaRatio卡玛比率 "
            "maxEntangleDay最长套牢天数 profitability持有期盈利概率"
        ),
    )
    p_rank.add_argument(
        "--period",
        default="week",
        choices=PERIOD_CHOICES,
        help="统计周期，默认week（近一周）",
    )
    p_rank.add_argument(
        "--sortType",
        choices=["A", "D"],
        help="排序方向：A升序 D降序。不传则按 --field 自动选择合理方向",
    )
    add_common_filters(p_rank)

    # ---- special：热销榜/人气榜/定投榜等特色榜单 ----
    p_special = sub.add_parser(
        "special",
        help="查询热销榜/人气榜/定投榜等平台特色榜单",
    )
    p_special.add_argument(
        "--type",
        required=True,
        choices=list(SPECIAL_RANK_KEYS.keys()),
        help="榜单类型：hot热销榜 popularity人气榜 dingtou定投榜",
    )
    p_special.add_argument(
        "--period",
        default="quarter",
        choices=PERIOD_CHOICES,
        help="统计周期，默认近3月",
    )
    add_common_filters(p_special)

    return parser


def build_payload(args):

    if args.command == "rank":
        payload = {
            "ordeField": args.field,
            "stageType": args.period,
            "sortType": args.sortType or DEFAULT_SORT_TYPE[args.field],
        }
    else:  # special
        payload = {
            "ordeField": "rankNo",
            "stageType": args.period,
            "sortType": "A",
            "rankKey": SPECIAL_RANK_KEYS[args.type],
        }

    payload.update({
        "firstITypes": args.firstITypes,
        "fundKyp": args.fundKyp,
        "specifiRisk": args.specifiRisk,
        "scaleType": args.scaleType,
        "setupTimeType": args.setupTimeType,
        "rateDiscountType": args.rateDiscountType,
        "pageSize": args.pageSize,
    })

    payload.update(FIXED_PARAMS)

    return {
        k: v
        for k, v in payload.items()
        if v is not None
    }


def main():

    parser = build_parser()

    args = parser.parse_args()

    payload = build_payload(args)

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