#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基本面数据获取
Fundamental Data Fetching
东方财富财务API
"""

import re
import time
import json
from typing import Dict, List, Optional, Tuple

try:
    from crawl_utils import safe_request
    HAS_CRAWL_UTILS = True
except ImportError:
    HAS_CRAWL_UTILS = False


class FundamentalData:
    """
    基本面数据获取

    数据来源：东方财富
    - 财务指标: https://emweb.securities.eastmoney.com/PC_HSF10/NewFinanceAnalysis/ZYZBAjaxNew
    """

    def __init__(self):
        pass

    def safe_float(self, v, default=0.0):
        try:
            f = float(v)
            # v8.0: 上限 1e10→1e15（修复大市值/大营收被清零）
            return f if abs(f) < 1e15 else default
        except Exception:
            return default

    def fetch_financial_indicators(self, code: str) -> Dict:
        """
        获取财务指标

        Args:
            code: 股票代码，如 "600519"

        Returns:
            Dict: 财务指标
        """
        # 自动判断前缀
        if code.startswith(("6", "5", "9")):
            prefix = "SH"
        else:
            prefix = "SZ"

        url = f"https://emweb.securities.eastmoney.com/PC_HSF10/NewFinanceAnalysis/ZYZBAjaxNew?type=0&code={prefix}{code}"

        headers = {
            "User-Agent": "Mozilla/5.0",
            "Referer": "https://emweb.securities.eastmoney.com/"
        }

        try:
            if HAS_CRAWL_UTILS:
                raw = safe_request(url, headers=headers, timeout=8)
                if isinstance(raw, tuple):
                    raw = raw[0]
            else:
                import urllib.request
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, timeout=8) as resp:
                    raw = resp.read().decode("utf-8", errors="ignore")

            if isinstance(raw, bytes):
                raw = raw.decode("utf-8", errors="ignore")

            data = json.loads(raw)
            return data
        except Exception as e:
            print(f"[FundamentalData] 获取财务指标失败: {e}")
            return {}

    def parse_financial_data(self, raw: Dict) -> Dict:
        """
        解析财务数据

        Args:
            raw: 原始财务数据

        Returns:
            Dict: 解析后的数据
        """
        result = {
            "roe": 0,
            "eps": 0,
            "bvps": 0,  # 每股净资产
            "pe": 0,    # 市盈率
            "pb": 0,    # 市净率
            "revenue": 0,
            "net_profit": 0,
            "total_assets": 0,
            "total_liabilities": 0,
            "current_assets": 0,
            "gross_margin": 0,
            "operating_margin": 0,
            "net_margin": 0,
        }

        try:
            # 解析最新季度数据
            data_list = raw.get("result", {}).get("data", [])
            if data_list and len(data_list) > 0:
                latest = data_list[0]

                # v8.0: 财务报告期 + 资产负债字段（激活 analyzer 的 data_freshness 时效校验）
                result["report_date"] = str(latest.get("REPORTDATE", ""))[:10]
                result["total_assets"] = self.safe_float(latest.get("TOTAL_ASSETS"))
                result["total_liabilities"] = self.safe_float(latest.get("TOTAL_LIABILITIES"))
                result["current_assets"] = self.safe_float(latest.get("TOTAL_CURRENT_ASSETS"))

                # ROE
                roe_str = latest.get("ROE", "")
                if roe_str and roe_str not in ("-", "", "N/A"):
                    result["roe"] = self.safe_float(roe_str.replace("%", ""))

                # EPS
                eps_str = latest.get("BASIC_EPS", "")
                if eps_str and eps_str not in ("-", "", "N/A"):
                    result["eps"] = self.safe_float(eps_str)

                # 每股净资产
                bvps_str = latest.get("BPS", "")
                if bvps_str and bvps_str not in ("-", "", "N/A"):
                    result["bvps"] = self.safe_float(bvps_str)

                # 营业收入
                revenue_str = latest.get("TOTAL_OPERATE_INCOME", "")
                if revenue_str and revenue_str not in ("-", "", "N/A"):
                    result["revenue"] = self.safe_float(revenue_str)

                # 净利润
                profit_str = latest.get("PARENT_NETPROFIT", "")
                if profit_str and profit_str not in ("-", "", "N/A"):
                    result["net_profit"] = self.safe_float(profit_str)

                # 资产负债率
                debt_str = latest.get("DEBT_ASSET_RATIO", "")
                if debt_str and debt_str not in ("-", "", "N/A"):
                    result["debt_ratio"] = self.safe_float(debt_str.replace("%", ""))

        except Exception as e:
            print(f"[FundamentalData] 解析财务数据失败: {e}")

        return result

    def get_valuation(self, code: str, history_len: int = 250) -> Dict:
        """
        获取估值指标（PE/PB/PS等）+ PE/PB 历史序列（v8.0 激活真实历史分位）。

        Args:
            code: 股票代码
            history_len: 拉取历史估值条数（默认 250，供分位计算；旧行为 pageSize=1 无历史）

        Returns:
            Dict: 估值指标（含 pe_history/pb_history/history_dates，时间升序）
        """
        # 使用东方财富估值API（RPT_VALUEANALYSIS_DET 按证券代码过滤，沪深通用）
        # v8.0: pageSize=1→history_len，拉取历史 PE_TTM/PB_MRQ 序列 → 激活 analyzer 真实分位
        url = f"https://datacenter-web.eastmoney.com/api/data/v1/get?reportName=RPT_VALUEANALYSIS_DET&columns=ALL&filter=(SECURITY_CODE%3D%22{code}%22)&pageSize={history_len}&sortColumns=TRADE_DATE&sortTypes=-1"

        headers = {
            "User-Agent": "Mozilla/5.0",
            "Referer": "https://data.eastmoney.com/"
        }

        try:
            if HAS_CRAWL_UTILS:
                raw = safe_request(url, headers=headers, timeout=8)
                if isinstance(raw, tuple):
                    raw = raw[0]
            else:
                import urllib.request
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, timeout=8) as resp:
                    raw = resp.read().decode("utf-8", errors="ignore")

            if isinstance(raw, bytes):
                raw = raw.decode("utf-8", errors="ignore")
            data = json.loads(raw)
            result = (data.get("result") or {}).get("data") or []
            if not result:
                return {}
            # 接口按 TRADE_DATE 降序返回 → 转升序供分位计算
            rows = sorted(result, key=lambda r: str(r.get("TRADE_DATE", "")))
            latest = rows[-1]
            pe_hist = [self.safe_float(r.get("PE_TTM")) for r in rows]
            pb_hist = [self.safe_float(r.get("PB_MRQ")) for r in rows]
            return {
                "pe": self.safe_float(latest.get("PE_TTM")),
                "pb": self.safe_float(latest.get("PB_MRQ")),
                "ps": self.safe_float(latest.get("PS_TTM")),
                "pcf": self.safe_float(latest.get("PCF_OCF_TTM")),
                "pe_history": pe_hist,
                "pb_history": pb_hist,
                "history_dates": [str(r.get("TRADE_DATE", ""))[:10] for r in rows],
                "history_len": len(rows),
            }
        except Exception as e:
            print(f"[FundamentalData] 获取估值失败: {e}")

        return {}

    def get_financial_summary(self, code: str) -> Dict:
        """
        获取财务摘要（综合）

        Args:
            code: 股票代码

        Returns:
            Dict: 财务摘要
        """
        fin_data = self.fetch_financial_indicators(code)
        parsed = self.parse_financial_data(fin_data)
        valuation = self.get_valuation(code)

        result = {**parsed, **valuation}
        return result