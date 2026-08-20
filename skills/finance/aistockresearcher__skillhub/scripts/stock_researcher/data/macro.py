#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
宏观数据获取
Macro Data Fetching
"""

import re
import json
import time
from typing import Dict, List, Optional

try:
    from crawl_utils import safe_request
    HAS_CRAWL_UTILS = True
except ImportError:
    HAS_CRAWL_UTILS = False


class MacroData:
    """
    宏观数据获取

    数据来源：东方财富数据中心
    指标：GDP、CPI、PPI、PMI、M2、利率等
    """

    # v8.0: 指标 → (reportName, 过滤名)。此前全部映射 RPT_ECONOMIC_GDP，
    # 导致 CPI/PPI/PMI/M2 取不到（接口无对应 INDICATOR_NAME）。
    MACRO_REPORT = {
        "gdp": ("RPT_ECONOMIC_GDP", "GDP同比"),
        "cpi": ("RPT_ECONOMIC_CPI", "CPI同比"),
        "ppi": ("RPT_ECONOMIC_PPI", "PPI同比"),
        "pmi": ("RPT_ECONOMIC_PMI", "PMI"),
        "m2": ("RPT_ECONOMIC_GJZB", "M2同比"),
        "lpr": ("RPT_LPR", ""),
    }

    # 兼容旧键（analyze_macro_impact 等按中文名判断）
    MACRO_INDICATORS = {
        "gdp": "GDP同比",
        "cpi": "CPI同比",
        "ppi": "PPI同比",
        "pmi": "PMI",
        "社融": "社会融资规模",
        "m2": "M2同比",
        "lpr": "LPR1年期",
    }

    def __init__(self):
        pass

    def fetch_macro_indicator(self, indicator_name: str) -> Dict:
        """
        获取单个宏观指标

        Args:
            indicator_name: 指标名称，如 "cpi"

        Returns:
            Dict: 指标数据
        """
        report_cfg = self.MACRO_REPORT.get(indicator_name)
        if report_cfg:
            report_name, cn_name = report_cfg
        else:
            report_name, cn_name = "RPT_ECONOMIC_GDP", self.MACRO_INDICATORS.get(indicator_name, indicator_name)

        filter_part = f"filter=(INDICATOR_NAME%3D%22{cn_name}%22)" if cn_name else ""
        url = (
            f"https://datacenter-web.eastmoney.com/api/data/v1/get?"
            f"reportName={report_name}&columns=ALL&{filter_part}"
            f"pageSize=10&pageIndex=1&sortColumns=REPORT_DATE&sortTypes=-1"
        )

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
            items = data.get("result", {}).get("data", [])

            if items:
                latest = items[0]
                return {
                    "indicator": cn_name,
                    "value": latest.get("INDICATOR_VALUE", ""),
                    "unit": latest.get("UNIT", ""),
                    "date": latest.get("REPORT_DATE", ""),
                    "previous": latest.get("PREV_INDICATOR_VALUE", ""),
                }

        except Exception as e:
            print(f"[MacroData] 获取宏观指标失败: {e}")

        # v8.0: akshare 宏观兜底（可选依赖，未装自动跳过）
        try:
            from stock_researcher.data.akshare_provider import ak_macro
            fallback = ak_macro(indicator_name)
            if fallback and fallback.get("value") is not None:
                return fallback
        except Exception:
            pass
        return {}

    def fetch_all_macro(self) -> List[Dict]:
        """
        获取所有主要宏观指标

        Returns:
            List[Dict]: 宏观指标列表
        """
        result = []

        for indicator in self.MACRO_INDICATORS.keys():
            data = self.fetch_macro_indicator(indicator)
            if data:
                result.append(data)
            time.sleep(0.3)  # 避免请求过快

        return result

    def analyze_macro_impact(self, macro_data: List[Dict]) -> Dict:
        """
        分析宏观环境影响

        Args:
            macro_data: 宏观数据列表

        Returns:
            Dict: 分析结果
        """
        score = 0
        factors = []

        for m in macro_data:
            name = m.get("indicator", "")
            value_str = m.get("value", "")
            try:
                value = float(str(value_str).replace("%", ""))

                # CPI分析
                if "CPI" in name:
                    if value < 3:
                        score += 10
                        factors.append("CPI温和，通胀可控")
                    elif value > 5:
                        score -= 10
                        factors.append("CPI偏高，通胀压力")

                # PMI分析
                elif "PMI" in name:
                    if value > 50:
                        score += 10
                        factors.append("PMI扩张，经济回暖")
                    else:
                        score -= 10
                        factors.append("PMI收缩，经济放缓")

                # GDP分析
                elif "GDP" in name:
                    if value > 5:
                        score += 5
                        factors.append("GDP增长稳健")
                    else:
                        score -= 5
                        factors.append("GDP增速放缓")

            except Exception:
                pass

        # 信号判断
        if score > 15:
            signal = "积极"
        elif score < -15:
            signal = "谨慎"
        else:
            signal = "中性"

        return {
            "score": score,
            "signal": signal,
            "factors": factors[:5],
            "data": macro_data
        }

    def get_economic_calendar(self) -> List[Dict]:
        """
        获取经济数据日历（未来重要经济数据发布时间）

        Returns:
            List[Dict]: 经济日历
        """
        # 简化版，实际应该爬取财经日历网站
        return [
            {"date": "每月10日", "event": "CPI/PPI公布"},
            {"date": "每月末", "event": "PMI公布"},
            {"date": "每月15日", "event": "GDP数据"},
            {"date": "每周", "event": "央行公开市场操作"},
        ]