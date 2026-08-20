"""
新浪财经数据 Provider

数据源：hq.sinajs.cn / quotes.sina.cn / stock.finance.sina.com.cn
协议：HTTPS GET，GBK 编码响应（行情接口）/ JSON（财报/期权合约）
封禁风险：极低
覆盖市场：A股/港股/美股/ETF期权
"""

from __future__ import annotations

import json
import re

from core.client import http_get
from core.throttle import throttled_get
from core.ticker import normalize, cn_prefix


# ========== 财务报表 ==========

_FINANCE_API = "https://quotes.sina.cn/cn/api/openapi.php"


def financial_report(code: str, report_type: str = "income") -> list[dict]:
    """获取上市公司财务报表数据

    通过新浪财经 CompanyFinanceService 接口获取三大报表数据。

    Args:
        code: 股票代码，如 "600519"
        report_type: 报表类型，可选：
            - "balance_sheet": 资产负债表
            - "income": 利润表
            - "cashflow": 现金流量表

    Returns:
        报表数据列表，每项为一个报告期的字段字典
    """
    normalized = normalize(code)

    # 新浪接口报表类型映射
    type_map = {
        "balance_sheet": "BalanceSheet",
        "income": "ProfitStatement",
        "cashflow": "CashFlow",
    }
    sina_type = type_map.get(report_type, "ProfitStatement")

    params = {
        "app": "finance",
        "cat": "CompanyFinanceService",
        "exec": f"get{sina_type}",
        "symbol": normalized,
        "page": "1",
        "num": "10",
    }

    query_str = "&".join(f"{k}={v}" for k, v in params.items())
    url = f"{_FINANCE_API}?{query_str}"

    resp = throttled_get(url)
    if resp is None or not resp.ok:
        return []
    try:
        data = json.loads(resp.text)
    except (json.JSONDecodeError, TypeError):
        return []

    # 防御: API 可能返回错误对象
    if not isinstance(data, dict):
        return []

    # 响应结构: {"result": {"data": {"report_date": [...], ...}}}
    result = data.get("result", {})
    if not result:
        return []

    report_data = result.get("data", {})
    if not report_data:
        return []

    # 转置：将列式数据转为行式记录
    dates = report_data.get("report_date", [])
    records = []
    for i, date in enumerate(dates):
        record = {"report_date": date}
        for field, values in report_data.items():
            if field == "report_date":
                continue
            if isinstance(values, list) and i < len(values):
                record[field] = values[i]
        records.append(record)

    return records


# ========== ETF期权 ==========

_OPTION_API = "https://stock.finance.sina.com.cn/futures/api/openapi.php"
_HQ_API = "http://hq.sinajs.cn/list="


def option_contracts(underlying: str, call: bool = True) -> list[dict]:
    """获取期权合约列表

    获取指定标的（如50ETF）的当月期权合约代码清单。

    Args:
        underlying: 标的代码，如 "510050"
        call: True 获取认购合约，False 获取认沽合约

    Returns:
        合约列表，每项包含 contract_code, strike, expire_date 等
    """
    normalized = normalize(underlying)
    direction = "call" if call else "put"

    params = {
        "app": "option",
        "cat": "OptionService",
        "exec": "getContractList",
        "underlying": normalized,
        "direction": direction,
    }

    query_str = "&".join(f"{k}={v}" for k, v in params.items())
    url = f"{_OPTION_API}?{query_str}"

    resp = throttled_get(url)
    if resp is None or not resp.ok:
        return []
    try:
        data = json.loads(resp.text)
    except (json.JSONDecodeError, TypeError):
        return []

    result = data.get("result", {})
    contracts = result.get("data", [])

    parsed = []
    for c in contracts:
        parsed.append({
            "contract_code": c.get("contractCode", ""),
            "contract_symbol": c.get("contractSymbol", ""),
            "strike": float(c["strike"]) if "strike" in c else None,
            "expire_date": c.get("expireDate", ""),
            "direction": direction,
            "underlying": normalized,
        })

    return parsed


def option_tquote(contract_code: str) -> dict:
    """获取期权合约T型报价

    解析新浪 hq.sinajs.cn 的期权实时行情数据。

    Args:
        contract_code: 期权合约代码，如 "10007306"

    Returns:
        T型报价字典，包含：
        - bid_price: 买价
        - ask_price: 卖价
        - latest_price: 最新价
        - position: 持仓量
        - volume: 成交量
        - strike: 行权价
        - underlying_price: 标的价格
    """
    url = f"{_HQ_API}CON_OP_{contract_code}"

    resp = throttled_get(url, encoding="gbk")
    if resp is None or not resp.ok:
        return {}
    text = resp.text

    # 格式: var hq_str_CON_OP_10007306="...,字段1,字段2,...";
    match = re.search(r'"([^"]*)"', text)
    if not match:
        return {}

    fields = match.group(1).split(",")
    if len(fields) < 42:
        return {}

    def _safe_float(idx: int) -> float | None:
        try:
            val = fields[idx].strip()
            return float(val) if val else None
        except (IndexError, ValueError):
            return None

    def _safe_int(idx: int) -> int | None:
        try:
            val = fields[idx].strip()
            return int(float(val)) if val else None
        except (IndexError, ValueError):
            return None

    return {
        "contract_code": contract_code,
        "buy_price": _safe_float(0),      # 买价
        "sell_price": _safe_float(1),      # 卖价
        "latest_price": _safe_float(2),    # 最新价
        "position": _safe_int(5),          # 持仓量
        "volume": _safe_int(41),           # 成交量
        "bid1_price": _safe_float(6),      # 买一价
        "bid1_vol": _safe_int(7),          # 买一量
        "bid2_price": _safe_float(8),      # 买二价
        "bid2_vol": _safe_int(9),          # 买二量
        "bid3_price": _safe_float(10),     # 买三价
        "bid3_vol": _safe_int(11),         # 买三量
        "bid4_price": _safe_float(12),     # 买四价
        "bid4_vol": _safe_int(13),         # 买四量
        "bid5_price": _safe_float(14),     # 买五价
        "bid5_vol": _safe_int(15),         # 买五量
        "ask1_price": _safe_float(16),     # 卖一价
        "ask1_vol": _safe_int(17),         # 卖一量
        "ask2_price": _safe_float(18),     # 卖二价
        "ask2_vol": _safe_int(19),         # 卖二量
        "ask3_price": _safe_float(20),     # 卖三价
        "ask3_vol": _safe_int(21),         # 卖三量
        "ask4_price": _safe_float(22),     # 卖四价
        "ask4_vol": _safe_int(23),         # 卖四量
        "ask5_price": _safe_float(24),     # 卖五价
        "ask5_vol": _safe_int(25),         # 卖五量
        "strike": _safe_float(37),         # 行权价
        "settle_price": _safe_float(38),   # 结算价
        "expire_date": fields[36].strip() if len(fields) > 36 else None,
    }


def option_greeks(contract_code: str) -> dict:
    """获取期权合约希腊字母

    通过新浪 CON_OP_GREEKS 接口获取期权的 Greeks 和隐含波动率。

    Args:
        contract_code: 期权合约代码

    Returns:
        Greeks 字典：
        - delta: Delta 值
        - gamma: Gamma 值
        - theta: Theta 值
        - vega: Vega 值
        - iv: 隐含波动率
        - theoretical_price: 理论价格
    """
    url = f"{_HQ_API}CON_OP_GREEKS_{contract_code}"

    resp = throttled_get(url, encoding="gbk")
    if resp is None or not resp.ok:
        return {}
    text = resp.text

    match = re.search(r'"([^"]*)"', text)
    if not match:
        return {}

    fields = match.group(1).split(",")
    if len(fields) < 7:
        return {}

    def _safe_float(idx: int) -> float | None:
        try:
            val = fields[idx].strip()
            return float(val) if val else None
        except (IndexError, ValueError):
            return None

    return {
        "contract_code": contract_code,
        "delta": _safe_float(0),
        "gamma": _safe_float(1),
        "theta": _safe_float(2),
        "vega": _safe_float(3),
        "iv": _safe_float(4),              # 隐含波动率
        "theoretical_price": _safe_float(5),  # 理论价格
        "underlying_price": _safe_float(6),   # 标的现价
    }


# ========== 资金流 ==========

_FUND_FLOW_API = "https://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/MoneyFlow/GetMoneyFlow"


def fund_flow_daily(code: str, days: int = 5) -> list[dict]:
    """获取个股每日资金流向

    通过新浪资金流接口获取大单/中单/小单净流入数据。

    Args:
        code: 股票代码，如 "600519"
        days: 获取天数，默认5天

    Returns:
        资金流列表，每天一条记录，包含：
        - date: 日期
        - main_net_inflow: 主力净流入（万元）
        - big_net_inflow: 大单净流入（万元）
        - mid_net_inflow: 中单净流入（万元）
        - small_net_inflow: 小单净流入（万元）
        - main_net_pct: 主力净流入占比(%)
    """
    normalized = normalize(code)
    prefix = cn_prefix(normalized)

    params = {
        "page": "1",
        "num": str(days),
        "sort": "date",
        "asc": "0",
        "fenlei": "1",
        "symbol": f"{prefix}{normalized}",
    }
    query_str = "&".join(f"{k}={v}" for k, v in params.items())
    url = f"{_FUND_FLOW_API}?{query_str}"

    resp = throttled_get(url)
    if resp is None or not resp.ok:
        return []
    text = resp.text

    # 新浪资金流接口返回 JSONP 格式或裸 JSON 数组
    # 去除可能的 JSONP 包裹
    if text and not text.strip().startswith("["):
        match = re.search(r'\[.*\]', text, re.DOTALL)
        if match:
            text = match.group(0)

    try:
        data = json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return []

    # 防御性检查：API 可能返回错误对象而非数组
    if not isinstance(data, list):
        return []

    results = []
    for item in data:
        if not isinstance(item, dict):
            continue
        results.append({
            "date": item.get("r_date", ""),
            "main_net_inflow": _to_float(item.get("r0_net", "")),
            "big_net_inflow": _to_float(item.get("r1_net", "")),
            "mid_net_inflow": _to_float(item.get("r2_net", "")),
            "small_net_inflow": _to_float(item.get("r3_net", "")),
            "main_net_pct": _to_float(item.get("r0_ratio", "")),
            "close_price": _to_float(item.get("close", "")),
            "change_pct": _to_float(item.get("changeratio", "")),
        })

    return results


def _to_float(val) -> float | None:
    """安全转换为浮点数"""
    if val is None or val == "":
        return None
    try:
        return float(str(val).replace(",", "").replace("%", ""))
    except (ValueError, TypeError):
        return None


# ========== 港股行情 ==========

def hk_quote(code: str) -> dict:
    """获取港股实时行情

    通过新浪 hq.sinajs.cn 的港股行情接口获取数据。

    Args:
        code: 港股代码，如 "00700" 或 "00700.HK"

    Returns:
        行情字典，包含 name, price, change, change_pct, volume 等
    """
    # 提取纯数字代码
    clean_code = normalize(code).replace(".HK", "").replace(".hk", "")
    # 补齐5位
    clean_code = clean_code.zfill(5)

    url = f"{_HQ_API}rt_hk{clean_code}"

    resp = throttled_get(url, encoding="gbk")
    if resp is None or not resp.ok:
        return {}
    text = resp.text

    match = re.search(r'"([^"]*)"', text)
    if not match:
        return {}

    fields = match.group(1).split(",")
    if len(fields) < 18:
        return {}

    def _sf(idx: int) -> float | None:
        try:
            val = fields[idx].strip()
            return float(val) if val else None
        except (IndexError, ValueError):
            return None

    return {
        "code": clean_code,
        "name_en": fields[0].strip() if len(fields) > 0 else "",
        "name": fields[1].strip() if len(fields) > 1 else "",
        "open": _sf(2),
        "prev_close": _sf(3),
        "high": _sf(4),
        "low": _sf(5),
        "price": _sf(6),
        "change": _sf(7),
        "change_pct": _sf(8),
        "bid_price": _sf(9),
        "ask_price": _sf(10),
        "volume": _sf(11),          # 成交量（股）
        "amount": _sf(12),          # 成交额
        "pe": _sf(14),
        "week52_high": _sf(15),
        "week52_low": _sf(16),
        "date": fields[17].strip() if len(fields) > 17 else None,
    }


# ========== 美股行情 ==========

def us_quote(code: str) -> dict:
    """获取美股实时行情

    通过新浪 hq.sinajs.cn 的美股行情接口（gb_前缀）获取数据。

    Args:
        code: 美股代码，如 "AAPL", "MSFT", "TSLA"

    Returns:
        行情字典，包含 name, price, change, change_pct, volume 等
    """
    symbol = code.upper().strip()
    url = f"{_HQ_API}gb_{symbol.lower()}"

    resp = throttled_get(url, encoding="gbk")
    if resp is None or not resp.ok:
        return {}
    text = resp.text

    match = re.search(r'"([^"]*)"', text)
    if not match:
        return {}

    fields = match.group(1).split(",")
    if len(fields) < 26:
        return {}

    def _sf(idx: int) -> float | None:
        try:
            val = fields[idx].strip()
            return float(val) if val else None
        except (IndexError, ValueError):
            return None

    return {
        "code": symbol,
        "name": fields[0].strip() if len(fields) > 0 else "",
        "price": _sf(1),
        "change": _sf(2),
        "change_pct": _sf(3),
        "datetime": fields[4].strip() if len(fields) > 4 else None,
        "open": _sf(5),
        "high": _sf(6),
        "low": _sf(7),
        "week52_high": _sf(8),
        "week52_low": _sf(9),
        "volume": _sf(10),
        "market_cap": _sf(12),       # 总市值
        "eps": _sf(13),              # 每股收益
        "pe": _sf(14),               # 市盈率
        "prev_close": _sf(26),       # 昨收价
    }


# ========== 美股K线 ==========

_US_KLINE_API = "https://stock.finance.sina.com.cn/usstock/api/jsonp_v2.php"


def us_kline(code: str, period: str = "day") -> list[dict]:
    """获取美股K线数据

    通过新浪美股K线接口获取历史价格数据。

    Args:
        code: 美股代码，如 "AAPL"
        period: K线周期，可选 "day", "week", "month"

    Returns:
        K线数据列表，每条包含：
        - date: 日期
        - open: 开盘价
        - high: 最高价
        - low: 最低价
        - close: 收盘价
        - volume: 成交量
    """
    symbol = code.upper().strip()

    # 新浪美股K线 JSONP 接口
    period_map = {"day": "d", "week": "w", "month": "m"}
    p = period_map.get(period, "d")

    callback = "var_kline"
    url = (
        f"{_US_KLINE_API}/{callback}/US_MinKService.getUS_MinK?"
        f"symbol={symbol}&type={p}&num=120"
    )

    resp = throttled_get(url)
    if resp is None or not resp.ok:
        return []
    text = resp.text

    # 去除 JSONP 包裹: var_kline([...])
    if text:
        match = re.search(r'\((\[.*?\])\)', text, re.DOTALL)
        if match:
            text = match.group(1)
        else:
            # 尝试直接匹配 JSON 数组
            match = re.search(r'\[.*\]', text, re.DOTALL)
            if match:
                text = match.group(0)

    try:
        data = json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return []

    results = []
    for item in data:
        results.append({
            "date": item.get("d", ""),
            "open": _to_float(item.get("o")),
            "high": _to_float(item.get("h")),
            "low": _to_float(item.get("l")),
            "close": _to_float(item.get("c")),
            "volume": _to_float(item.get("v")),
        })

    return results


# ========== 板块排行（东财被封后的降级源） ==========

_SINA_INDUSTRY_API = "https://vip.stock.finance.sina.com.cn/q/view/newSinaHy.php"


def sector_ranking(board_type: str = "industry") -> list[dict]:
    """新浪行业板块排行。

    作为 domains.signals.sector_ranking 的降级源（akshare 底层走东财
    push2，已被 IP 级封禁）。新浪仅提供行业板块，概念板块返回空由上层处理。

    单板块字段（逗号分隔）：
      [1]板块名 [2]家数 [4]涨跌幅% [6]成交量 [7]成交额
      [8]领涨股代码 [12]领涨股名

    Returns:
        板块排行列表，按涨跌幅降序，字段与 domain 层对齐。
    """
    if board_type == "concept":
        return []  # 新浪此接口不含概念板块
    resp = throttled_get(_SINA_INDUSTRY_API, encoding="gbk")
    if resp is None or not resp.ok:
        return []
    try:
        m = re.search(r"=\s*(\{.*\})", resp.text, re.S)
        if not m:
            return []
        raw = json.loads(m.group(1))
    except Exception:
        return []

    results = []
    for _, line in raw.items():
        parts = str(line).split(",")
        if len(parts) < 13:
            continue
        results.append({
            "name": parts[1],
            "change_pct": _to_float(parts[4]),
            "stock_count": int(_to_float(parts[2]) or 0),
            "volume": _to_float(parts[6]),
            "turnover": _to_float(parts[7]),
            "leader_code": parts[8],
            "leader_stock": parts[12],
        })
    results.sort(key=lambda x: (x["change_pct"] is None, -(x["change_pct"] or 0)))
    return results
