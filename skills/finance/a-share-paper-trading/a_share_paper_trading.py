#!/usr/bin/env python3
import os
import sys
import json
import argparse
from pathlib import Path
from typing import Literal, Optional

import requests


# --- 配置 ---

def _load_config_file() -> dict:
    config_path = Path.home() / ".htsc-skills" / "config"
    if not config_path.exists():
        return {}
    result = {}
    for line in config_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        result[key.strip()] = value.strip()
    return result


class Config:
    def __init__(self) -> None:
        _file_cfg = _load_config_file()
        self.api_url = os.environ.get("PAPER_TRADING_API_URL", "https://ai.zhangle.com")
        self.api_key = os.environ.get("HT_APIKEY") or _file_cfg.get("HT_APIKEY", "")
        self.base_url = os.environ.get("PAPER_TRADING_BASE_URL", "/edge/entry/gate")
        self.timeout_ms = int(os.environ.get("PAPER_TRADING_TIMEOUT_MS", "5000"))

    @property
    def timeout_seconds(self) -> float:
        return self.timeout_ms / 1000.0


_config: Optional[Config] = None


def _get_config() -> Config:
    global _config
    if _config is None:
        _config = Config()
    return _config


# --- HTTP 客户端 ---

def _network_error(message: str, hint: str = "") -> dict:
    return {
        "ok": False,
        "data": None,
        "error": {
            "code": 5000,
            "message": message,
            "category": "network",
            "retriable": True,
            "hint": hint or "网络抖动或后端临时不可用，请稍后再试。",
        },
    }


def _post(path: str, body: Optional[dict] = None) -> dict:
    cfg = _get_config()
    url = cfg.api_url.rstrip("/") + cfg.base_url + path
    headers = {"apiKey": cfg.api_key, "Content-Type": "application/json", "skillCode": "mx_1778741794549"}
    try:
        resp = requests.post(url, json=body or {}, headers=headers, timeout=cfg.timeout_seconds)
        if resp.status_code != 200:
            return _network_error(
                f"后端返回异常状态码 {resp.status_code}",
                hint="可能后端服务故障，请稍后再试或检查后端日志。",
            )
        return resp.json()
    except requests.exceptions.Timeout:
        return _network_error("请求超时")
    except requests.exceptions.ConnectionError:
        return _network_error(
            "无法连接到后端服务",
            hint=f"请检查 PAPER_TRADING_API_URL（当前 {cfg.api_url}）是否正确，以及后端服务是否启动。",
        )
    except json.JSONDecodeError:
        return _network_error("后端返回内容无法解析", hint="请检查后端版本是否匹配契约。")
    except Exception as e:
        return _network_error(f"未知网络错误：{e}")


# --- 工具函数 ---

def searchStock(query: str, limit: int = 30) -> dict:
    """按名称、代码、拼音首字母搜索股票。

    用于将用户提到的股票名称（"茅台"、"宁德"）解析为标准 stockCode。
    返回的 results 已按相关度倒序。模型按返回数量判断：1 条直接用，
    多条需向用户确认，0 条告知用户找不到。

    Args:
        query: 股票名称、代码、或拼音首字母（如"茅台"、"600519"、"GZMT"）
        limit: 最大返回数（默认 10，最多 20）

    Returns:
        results[]（每条含 stockCode, stockName, exchange），totalCount, query
    """
    return _post("/api/simSkills/searchStock", {"query": query, "limit": limit})


def getQuote(stockCode: str, exchange: Literal["SH", "SZ", "BJ"]) -> dict:
    """查股票实时行情。

    A 股不同市场可能存在相同代码（如 SH 000001 是上证指数, SZ 000001 是平安银行），
    所以 exchange 必填。一般通过 searchStock 获取正确的 (stockCode, exchange) 组合。

    Args:
        stockCode: 6 位股票代码
        exchange: 交易所标识 SH / SZ / BJ

    Returns:
        含 currentPrice, prevClose, limitUp, limitDown, bidPrice1, askPrice1,
        change, isSuspended 等字段
    """
    return _post("/api/simSkills/getQuote", {"stockCode": stockCode, "exchange": exchange})


def getAccountBalance() -> dict:
    """查账户资金总览。"""
    return _post("/api/simSkills/getAccountBalance")


def getPositions() -> dict:
    """查所有持仓明细。"""
    return _post("/api/simSkills/getPositions")


def submitOrder(
    direction: Literal["buy", "sell"],
    stockCode: str,
    exchange: Literal["SH", "SZ", "BJ"],
    quantity: int,
    orderType: Literal["limit", "market"] = "limit",
    price: Optional[float] = None,
) -> dict:
    """提交买卖委托。

    Args:
        direction: 买入 buy / 卖出 sell
        stockCode: 6 位代码
        exchange: 交易所标识 SH / SZ / BJ（必填，避免同代码不同市场歧义）
        quantity: 股数（最小申报数量与递增单位由后端按品种校验）
        orderType: limit（限价，默认）/ exchange（市价）
        price: 委托价。limit 必填，market 时忽略
    """
    body: dict = {
        "direction": direction,
        "stockCode": stockCode,
        "exchange": exchange,
        "quantity": quantity,
        "orderType": orderType,
    }
    if price is not None:
        body["price"] = price
    return _post("/api/simSkills/submitOrder", body)


def cancelOrder(orderId: str) -> dict:
    """按单号撤销单笔未成交（或部分成交）委托。"""
    return _post("/api/simSkills/cancelOrder", {"orderId": orderId})


def cancelAllPendingOrders(
    stockCode: Optional[str] = None,
    exchange: Optional[Literal["SH", "SZ", "BJ"]] = None,
    direction: Optional[Literal["buy", "sell"]] = None,
) -> dict:
    """一键撤销所有未成交委托，可按股票或方向过滤。

    stockCode 和 exchange 必须同时提供或同时省略。"""
    body: dict = {}
    if stockCode is not None:
        body["stockCode"] = stockCode
    if exchange is not None:
        body["exchange"] = exchange
    if direction is not None:
        body["direction"] = direction
    return _post("/api/simSkills/cancelAllPendingOrders", body)


def listPendingOrders(
    stockCode: Optional[str] = None,
    exchange: Optional[Literal["SH", "SZ", "BJ"]] = None,
    direction: Optional[Literal["buy", "sell"]] = None,
) -> dict:
    """查当日未成交/部分成交委托，按提交时间倒序。

    stockCode 和 exchange 必须同时提供或同时省略。"""
    body: dict = {}
    if stockCode is not None:
        body["stockCode"] = stockCode
    if exchange is not None:
        body["exchange"] = exchange
    if direction is not None:
        body["direction"] = direction
    return _post("/api/simSkills/listPendingOrders", body)


def listTradeHistory(
    startDate: str,
    endDate: str,
    stockCode: Optional[str] = None,
    exchange: Optional[Literal["SH", "SZ", "BJ"]] = None,
    direction: Optional[Literal["buy", "sell"]] = None,
) -> dict:
    """查历史成交记录。

    stockCode 和 exchange 必须同时提供或同时省略。

    Args:
        startDate: YYYY-MM-DD
        endDate: YYYY-MM-DD（跨度 ≤ 90 天）
    """
    body: dict = {"startDate": startDate, "endDate": endDate}
    if stockCode is not None:
        body["stockCode"] = stockCode
    if exchange is not None:
        body["exchange"] = exchange
    if direction is not None:
        body["direction"] = direction
    return _post("/api/simSkills/listTradeHistory", body)


# --- CLI ---

def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="a_share_paper_trading", description="A 股模拟交易工具调度入口")
    sub = p.add_subparsers(dest="tool", required=True, metavar="<tool>")

    s = sub.add_parser("searchStock", help="按名称/代码/拼音搜索股票")
    s.add_argument("--query", required=True)
    s.add_argument("--limit", type=int, default=30)

    s = sub.add_parser("getQuote", help="查股票实时行情")
    s.add_argument("--stock-code", required=True)
    s.add_argument("--exchange", required=True, choices=["SH", "SZ", "BJ"])

    sub.add_parser("getAccountBalance", help="查账户资金总览")
    sub.add_parser("getPositions", help="查所有持仓明细")

    s = sub.add_parser("submitOrder", help="提交买卖委托")
    s.add_argument("--direction", required=True, choices=["buy", "sell"])
    s.add_argument("--stock-code", required=True)
    s.add_argument("--exchange", required=True, choices=["SH", "SZ", "BJ"])
    s.add_argument("--quantity", required=True, type=int)
    s.add_argument("--order-type", default="limit", choices=["limit", "market"])
    s.add_argument("--price", type=float)

    s = sub.add_parser("cancelOrder", help="按单号撤单")
    s.add_argument("--order-id", required=True)

    for name, help_ in [
        ("cancelAllPendingOrders", "一键撤销所有未成交委托"),
        ("listPendingOrders", "查当日未成交/部分成交委托"),
    ]:
        s = sub.add_parser(name, help=help_)
        s.add_argument("--stock-code")
        s.add_argument("--exchange", choices=["SH", "SZ", "BJ"])
        s.add_argument("--direction", choices=["buy", "sell"])

    s = sub.add_parser("listTradeHistory", help="查历史成交记录")
    s.add_argument("--start-date", required=True)
    s.add_argument("--end-date", required=True)
    s.add_argument("--stock-code")
    s.add_argument("--exchange", choices=["SH", "SZ", "BJ"])
    s.add_argument("--direction", choices=["buy", "sell"])

    return p


def main() -> None:
    args = _build_parser().parse_args()
    tool = args.tool

    if tool == "searchStock":
        result = searchStock(query=args.query, limit=args.limit)
    elif tool == "getQuote":
        result = getQuote(stockCode=args.stock_code, exchange=args.exchange)
    elif tool == "getAccountBalance":
        result = getAccountBalance()
    elif tool == "getPositions":
        result = getPositions()
    elif tool == "submitOrder":
        result = submitOrder(
            direction=args.direction,
            stockCode=args.stock_code,
            exchange=args.exchange,
            quantity=args.quantity,
            orderType=args.order_type,
            price=args.price,
        )
    elif tool == "cancelOrder":
        result = cancelOrder(orderId=args.order_id)
    elif tool == "cancelAllPendingOrders":
        result = cancelAllPendingOrders(
            stockCode=args.stock_code,
            exchange=args.exchange,
            direction=args.direction,
        )
    elif tool == "listPendingOrders":
        result = listPendingOrders(
            stockCode=args.stock_code,
            exchange=args.exchange,
            direction=args.direction,
        )
    elif tool == "listTradeHistory":
        result = listTradeHistory(
            startDate=args.start_date,
            endDate=args.end_date,
            stockCode=args.stock_code,
            exchange=args.exchange,
            direction=args.direction,
        )
    else:
        raise SystemExit(f"unknown tool: {tool}")

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
