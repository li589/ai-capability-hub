#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一异常与错误处理 (v6.0.0)
============================
为所有数据获取模块提供标准化的异常类和结果包装。
"""

from typing import Any, Dict, Optional
import ssl


class StockResearcherError(Exception):
    """基础异常类"""
    pass


class DataSourceError(StockResearcherError):
    """数据源错误 — 网络超时、解析失败、API 返回异常等"""
    def __init__(self, message: str, source: str = "", code: str = "",
                 retryable: bool = True):
        super().__init__(message)
        self.source = source
        self.code = code
        self.retryable = retryable


class MarketNotSupportedError(StockResearcherError):
    """不支持的市场"""
    def __init__(self, market: str):
        super().__init__(f"不支持的市场: {market}。支持: cn, hk, us")
        self.market = market


class InvalidCodeError(StockResearcherError):
    """无效的股票/基金代码"""
    def __init__(self, code: str, market: str = ""):
        msg = f"无效代码: {code}"
        if market:
            msg += f" (市场: {market})"
        super().__init__(msg)
        self.code = code


class DataNotAvailableError(StockResearcherError):
    """数据不可用 — 非交易时段或数据源暂无数据"""
    def __init__(self, message: str = "数据暂不可用"):
        super().__init__(message)


def make_result(ok: bool = False, data: Dict = None, error: str = None,
                **kwargs) -> Dict[str, Any]:
    """
    构造标准化的数据获取结果。

    所有数据获取函数应返回此格式，便于调用方统一处理。

    返回格式: {"_ok": bool, "_error": Optional[str], ...data fields...}
    """
    result = {"_ok": ok, "_error": error}
    if data:
        result.update(data)
    result.update(kwargs)
    return result


def handle_request(url: str, timeout: int = 10,
                   retries: int = 3) -> bytes:
    """
    标准化的网络请求，带重试和异常转换。

    Args:
        url: 请求 URL
        timeout: 超时秒数
        retries: 最大重试次数

    Returns:
        bytes: 响应内容

    Raises:
        DataSourceError: 所有网络/解析异常统一转换
    """
    import ssl
    import time
    import urllib.request

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://gu.qq.com/",
    }

    last_err = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
                return resp.read()
        except Exception as e:
            last_err = e
            if attempt < retries - 1:
                wait = 2 ** attempt
                time.sleep(wait)

    raise DataSourceError(
        f"请求失败 [{url[:80]}]: {last_err}",
        source=url,
        retryable=True,
    )


def safe_float(val, default: float = 0.0) -> float:
    """
    统一的安全浮点数转换。
    所有模块应使用此函数，避免在多个文件中重复定义。
    """
    import math
    try:
        f = float(val)
        # v8.0: 上限 1e10→1e15（修复大市值/大营收被清零，如茅台营收 1.5e11）
        return f if math.isfinite(f) and abs(f) < 1e15 else default
    except (TypeError, ValueError):
        return default


def create_ssl_context() -> ssl.SSLContext:
    """创建统一的 TLS/SSL 上下文（跳过国内免费源常见的证书问题）"""
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


def make_headers(referer: str = "https://gu.qq.com/") -> dict:
    """创建统一的 HTTP 请求头"""
    return {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": referer,
    }
