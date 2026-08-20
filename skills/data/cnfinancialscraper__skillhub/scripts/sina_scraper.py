# -*- coding: utf-8 -*-
"""
新浪财经数据爬虫 v1.0

提供 A 股实时行情、个股基本资料等数据。
数据源: hq.sinajs.cn（免费实时行情 API）、finance.sina.com.cn

注意：
- 新浪 API 是 JS 变量赋值格式，需自行解析逗号分隔字段
- 建议请求频率不超过 1.5 次/秒（由 http_utils 自动限流）
- 新浪行情 API 为非官方接口，未来可能变更
"""

import re
import json
import logging
from typing import Dict, List, Optional

try:
    from .http_utils import http_get, fetch_text
except ImportError:
    from http_utils import http_get, fetch_text

log = logging.getLogger(__name__)

# ── 新浪实时行情字段映射 ──────────────────────────────
# 来源: hq.sinajs.cn 返回的 var hq_str_{code}="..." 逗号分隔
# 索引  0: 名称  1: 今开  2: 昨收  3: 当前价  4: 最高
#        5: 最低  8: 成交量(手)  9: 成交额(万)
#       30: 日期  31: 时间  32: 停牌状态(00正常)
_SINA_FIELD_MAP = {
    "name": 0, "open": 1, "close_yesterday": 2, "price": 3,
    "high": 4, "low": 5, "bid": 6, "ask": 7,
    "volume": 8, "amount": 9,
    "bid1_vol": 10, "bid1_price": 11, "bid2_vol": 12, "bid2_price": 13,
    "bid3_vol": 14, "bid3_price": 15, "bid4_vol": 16, "bid4_price": 17,
    "bid5_vol": 18, "bid5_price": 19,
    "ask1_vol": 20, "ask1_price": 21, "ask2_vol": 22, "ask2_price": 23,
    "ask3_vol": 24, "ask3_price": 25, "ask4_vol": 26, "ask4_price": 27,
    "ask5_vol": 28, "ask5_price": 29,
    "date": 30, "time": 31,
}


def _to_sina_code(stock_code: str) -> str:
    """将 6 位股票代码转换为新浪格式 (sh600519 / sz000858)"""
    code = stock_code.strip().replace(".SH", "").replace(".SZ", "").replace(" ", "")
    if code.startswith(("6", "9")):
        return f"sh{code}"
    return f"sz{code}"


def _parse_sina_line(line: str) -> Optional[Dict]:
    """解析新浪单行行情数据"""
    try:
        # 格式: var hq_str_sh600519="贵州茅台,1850.00,...";
        match = re.search(r'hq_str_(\w+)="(.+)"', line)
        if not match:
            return None
        code_raw = match.group(1)  # sh600519
        values = match.group(2).split(",")
        if len(values) < 32:
            return None

        data = {
            "code": code_raw[2:],  # 去掉 sh/sz 前缀
            "exchange": "SH" if code_raw.startswith("sh") else "SZ",
        }
        for key, idx in _SINA_FIELD_MAP.items():
            val = values[idx] if idx < len(values) else ""
            if key == "name":
                data[key] = val.strip()
            elif key in ("date", "time"):
                data[key] = val.strip()
            else:
                try:
                    data[key] = float(val) if val else 0.0
                except ValueError:
                    data[key] = 0.0 if key != "name" else val

        # 计算涨跌幅
        if data.get("close_yesterday", 0) > 0:
            data["change_pct"] = round(
                (data["price"] - data["close_yesterday"]) / data["close_yesterday"] * 100, 2
            )
        else:
            data["change_pct"] = 0.0

        return data
    except Exception as e:
        log.debug(f"解析新浪行情失败: {e}")
        return None


def get_realtime_quote(stock_codes: List[str]) -> Dict[str, Dict]:
    """获取 A 股实时行情

    Args:
        stock_codes: 股票代码列表，如 ["600519", "000858", "300750"]

    Returns:
        {code: {name, price, open, high, low, volume, amount, change_pct, date, time}, ...}
    """
    sina_codes = [_to_sina_code(c) for c in stock_codes]
    url = f"https://hq.sinajs.cn/list={','.join(sina_codes)}"

    # 新浪 API 需要特定的 Referer
    headers = {
        "Referer": "https://finance.sina.com.cn",
        "Accept": "*/*",
    }
    text = fetch_text(url, headers=headers, timeout=15)
    if not text:
        log.warning(f"新浪行情请求失败: {url}")
        # v5.0.0: 降级到 akshare 全市场 A 股行情（接口被封/超时时兜底）
        try:
            from scripts.akshare_fallback import fallback_akshare
            records = fallback_akshare("stock_zh_a_spot", {}, None)
            results = {}
            wanted = {c[-6:] for c in stock_codes}
            for r in records:
                code = str(r.get("代码", r.get("code", "")))
                if code[-6:] not in wanted:
                    continue
                results[code[-6:]] = {
                    "name": r.get("名称", r.get("name", "")),
                    "price": r.get("最新价", r.get("price", "")),
                    "change_pct": r.get("涨跌幅", r.get("change_pct", "")),
                    "open": r.get("今开", r.get("open", "")),
                    "high": r.get("最高", r.get("high", "")),
                    "low": r.get("最低", r.get("low", "")),
                    "pre_close": r.get("昨收", r.get("pre_close", "")),
                    "volume": r.get("成交量", r.get("volume", "")),
                    "amount": r.get("成交额", r.get("amount", "")),
                    "date": r.get("日期", ""),
                    "time": r.get("更新时间", ""),
                }
            return results
        except Exception:
            return {}

    results = {}
    for line in text.strip().split("\n"):
        if not line.strip():
            continue
        parsed = _parse_sina_line(line.strip())
        if parsed:
            results[parsed["code"]] = parsed

    return results


def get_stock_brief(stock_code: str) -> Dict:
    """获取股票简要资料（F10 公司概况）

    Args:
        stock_code: 6 位股票代码

    Returns:
        {code, name, industry, area, market_cap, listed_date, ...}
    """
    sina_code = _to_sina_code(stock_code)
    # 新浪 F10 页面
    url = f"https://vip.stock.finance.sina.com.cn/corp/go.php/vCI_CorpInfo/stockid/{sina_code[2:]}.phtml"
    headers = {"Referer": "https://finance.sina.com.cn"}

    text = fetch_text(url, headers=headers, timeout=15)
    if not text:
        return {}

    result = {"code": stock_code}

    # 公司名称
    name_m = re.search(r'<th[^>]*>公司名称[：:]\s*</th>\s*<td[^>]*>([^<]+)', text)
    if name_m:
        result["name"] = name_m.group(1).strip()

    # 所属行业
    ind_m = re.search(r'<th[^>]*>所属行业[：:]\s*</th>\s*<td[^>]*>([^<]+)', text, re.IGNORECASE)
    if ind_m:
        result["industry"] = ind_m.group(1).strip()

    # 所属地域
    area_m = re.search(r'<th[^>]*>所属地域[：:]\s*</th>\s*<td[^>]*>([^<]+)', text)
    if area_m:
        result["area"] = area_m.group(1).strip()

    # 上市日期
    date_m = re.search(r'<th[^>]*>上市日期[：:]\s*</th>\s*<td[^>]*>([^<]+)', text)
    if date_m:
        result["listed_date"] = date_m.group(1).strip()

    return result


# ── CLI 测试入口 ──────────────────────────────────────

if __name__ == "__main__":
    import sys
    codes = sys.argv[1:] if len(sys.argv) > 1 else ["600519", "000858"]
    print(f"查询实时行情: {codes}")

    quotes = get_realtime_quote(codes)
    for code, data in quotes.items():
        print(f"\n{data.get('name', '?')} ({code})")
        print(f"  当前价: {data.get('price', '?')}")
        print(f"  涨跌幅: {data.get('change_pct', '?')}%")
        print(f"  今开: {data.get('open', '?')}  最高: {data.get('high', '?')}  最低: {data.get('low', '?')}")
        print(f"  成交量: {data.get('volume', '?')}手  成交额: {data.get('amount', '?')}万")

    # 测试F10
    print(f"\n\n获取 {codes[0]} 公司概况...")
    brief = get_stock_brief(codes[0])
    print(json.dumps(brief, ensure_ascii=False, indent=2))
