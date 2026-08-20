# -*- coding: utf-8 -*-
"""Tushare 数据源适配器 (v8.0 新增)
===================================
Tushare (https://tushare.pro) 作为可选增强数据源。
需自行申请 token 并设置环境变量 TUSHARE_TOKEN。

能力:
  - macro: 宏观经济数据（GDP/CPI/PMI/M2等）
  - fund_nav: 基金日净值历史
  - index: 指数日线行情
  - fund_holdings: 基金持仓明细（如有权限）

优雅降级:
  - token 未配置 → 自动跳过，SourceResponse.fail()
  - tushare 库未安装 → 自动跳过
  - 网络/API 错误 → 捕获后返回 SourceResponse.fail()
"""
from __future__ import annotations

import os
import sys
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

_SCRIPTS = Path(__file__).resolve().parents[2]
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from .base import DataSource, SourceResponse  # noqa: E402


class TushareProvider(DataSource):
    """Tushare 数据源 — 可选增强，token 未配置时静默跳过。"""

    name = "tushare"
    capabilities = ["macro", "fund_nav", "index"]

    def __init__(self):
        self._token = os.environ.get("TUSHARE_TOKEN", "")
        self._pro = None
        self._available = bool(self._token)
        if self._available:
            self._init_pro()

    def _init_pro(self) -> None:
        """初始化 Tushare Pro 客户端。"""
        try:
            import tushare as ts
            ts.set_token(self._token)
            self._pro = ts.pro_api()
            self._available = True
        except ImportError:
            self._available = False
        except Exception:
            self._available = False

    # ── 宏观数据 ─────────────────────────────────────────────
    def fetch_macro(self) -> SourceResponse:
        if not self._available or self._pro is None:
            return SourceResponse.fail(self.name, "Tushare token 未配置或库未安装")

        indicators = {}
        try:
            # GDP
            gdp = self._pro.cn_gdp()
            if gdp is not None and not gdp.empty:
                latest = gdp.iloc[0]
                indicators["gdp_yoy"] = float(latest.get("gdp_yoy", 0))

            # CPI
            cpi = self._pro.cn_cpi()
            if cpi is not None and not cpi.empty:
                latest = cpi.iloc[0]
                indicators["cpi_yoy"] = float(latest.get("cpi_yoy", 0))

            # PPI
            ppi = self._pro.cn_ppi()
            if ppi is not None and not ppi.empty:
                latest = ppi.iloc[0]
                indicators["ppi_yoy"] = float(latest.get("ppi_yoy", 0))

            # PMI
            pmi = self._pro.cn_pmi()
            if pmi is not None and not pmi.empty:
                latest = pmi.iloc[0]
                indicators["pmi"] = float(latest.get("pmi", 50))

            # M2
            m2 = self._pro.cn_m()
            if m2 is not None and not m2.empty:
                latest = m2.iloc[0]
                indicators["m2_yoy"] = float(latest.get("m2_yoy", 0))

            return SourceResponse.ok(self.name, indicators)
        except Exception as e:
            return SourceResponse.fail(self.name, f"宏观数据获取失败: {e}")

    # ── 基金净值 ─────────────────────────────────────────────
    def fetch_fund_nav(self, code: str) -> SourceResponse:
        if not self._available or self._pro is None:
            return SourceResponse.fail(self.name, "Tushare token 未配置")

        try:
            # 获取最近一年净值
            end_date = datetime.now().strftime("%Y%m%d")
            start_date = (datetime.now() - timedelta(days=365)).strftime("%Y%m%d")

            df = self._pro.fund_nav(ts_code=f"{code}.OF", start_date=start_date, end_date=end_date)
            if df is None or df.empty:
                return SourceResponse.fail(self.name, f"未找到基金 {code} 的净值数据")

            records = []
            for _, row in df.iterrows():
                records.append({
                    "date": str(row.get("nav_date", row.get("end_date", ""))),
                    "nav": float(row.get("unit_nav", row.get("nav", 0))),
                    "acc_nav": float(row.get("accum_nav", row.get("accumulated_nav", 0))),
                })

            return SourceResponse.ok(self.name, {
                "code": code,
                "count": len(records),
                "records": records,
                "latest_nav": records[-1]["nav"] if records else None,
            })
        except Exception as e:
            return SourceResponse.fail(self.name, f"净值获取失败: {e}")

    # ── 指数数据 ─────────────────────────────────────────────
    def fetch_index(self, index_code: str) -> SourceResponse:
        if not self._available or self._pro is None:
            return SourceResponse.fail(self.name, "Tushare token 未配置")

        try:
            end_date = datetime.now().strftime("%Y%m%d")
            start_date = (datetime.now() - timedelta(days=365)).strftime("%Y%m%d")

            df = self._pro.index_daily(ts_code=index_code, start_date=start_date, end_date=end_date)
            if df is None or df.empty:
                return SourceResponse.fail(self.name, f"未找到指数 {index_code}")

            records = []
            for _, row in df.iterrows():
                records.append({
                    "date": str(row.get("trade_date", "")),
                    "close": float(row.get("close", 0)),
                    "open": float(row.get("open", 0)),
                    "high": float(row.get("high", 0)),
                    "low": float(row.get("low", 0)),
                    "volume": float(row.get("vol", 0)),
                })

            return SourceResponse.ok(self.name, {
                "code": index_code,
                "count": len(records),
                "records": records,
                "latest_close": records[-1]["close"] if records else None,
            })
        except Exception as e:
            return SourceResponse.fail(self.name, f"指数数据获取失败: {e}")

    # ── 基金持仓 ─────────────────────────────────────────────
    def fetch_fund_holdings(self, code: str) -> SourceResponse:
        """基金持仓（需高级权限）。"""
        if not self._available or self._pro is None:
            return SourceResponse.fail(self.name, "Tushare token 未配置")

        try:
            df = self._pro.fund_portfolio(ts_code=f"{code}.OF")
            if df is None or df.empty:
                return SourceResponse.fail(self.name, f"未找到基金 {code} 的持仓数据（可能需高级权限）")

            records = []
            for _, row in df.iterrows():
                records.append({
                    "stock_code": str(row.get("stk_code", "")),
                    "stock_name": str(row.get("stk_name", "")),
                    "weight": float(row.get("weight", 0)),
                    "market_value": float(row.get("mkt_val", 0)),
                    "report_date": str(row.get("report_date", "")),
                })

            return SourceResponse.ok(self.name, {
                "code": code,
                "count": len(records),
                "records": records,
            })
        except Exception as e:
            return SourceResponse.fail(self.name, f"持仓数据获取失败: {e}")
