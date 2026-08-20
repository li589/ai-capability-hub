"""
腾讯财经实时行情 Provider

数据源：qt.gtimg.cn
协议：HTTPS GET，GBK 编码响应
封禁风险：极低（不封IP）
覆盖市场：A股/港股/美股

字段解析基于腾讯财经行情接口返回的 50+ 字段格式。
"""

from __future__ import annotations

from core.client import http_get
from core.throttle import throttled_get
from core.ticker import normalize, to_tencent_code, detect_market, cn_prefix


# 腾讯行情接口字段索引映射（从0开始）
# 格式: v_sz000001="1~平安银行~000001~10.50~10.45~10.48~..."
_FIELD_MAP = {
    "market": 0,       # 市场标识
    "name": 1,         # 股票名称
    "code": 2,         # 股票代码
    "price": 3,        # 当前价格
    "prev_close": 4,   # 昨收价
    "open": 5,         # 开盘价
    "volume": 6,       # 成交量（手）
    "buy_volume": 7,   # 外盘（主动买）
    "sell_volume": 8,  # 内盘（主动卖）
    "bid1_price": 9,   # 买一价
    "bid1_vol": 10,    # 买一量
    "bid2_price": 11,  # 买二价
    "bid2_vol": 12,    # 买二量
    "bid3_price": 13,  # 买三价
    "bid3_vol": 14,    # 买三量
    "bid4_price": 15,  # 买四价
    "bid4_vol": 16,    # 买四量
    "bid5_price": 17,  # 买五价
    "bid5_vol": 18,    # 买五量
    "ask1_price": 19,  # 卖一价
    "ask1_vol": 20,    # 卖一量
    "ask2_price": 21,  # 卖二价
    "ask2_vol": 22,    # 卖二量
    "ask3_price": 23,  # 卖三价
    "ask3_vol": 24,    # 卖三量
    "ask4_price": 25,  # 卖四价
    "ask4_vol": 26,    # 卖四量
    "ask5_price": 27,  # 卖五价
    "ask5_vol": 28,    # 卖五量
    "recent_trades": 29,  # 最近成交
    "datetime": 30,    # 日期时间
    "change": 31,      # 涨跌额
    "change_pct": 32,  # 涨跌幅(%)
    "high": 33,        # 最高价
    "low": 34,         # 最低价
    "price_vol_amount": 35,  # 价格/成交量/成交额
    "amount": 36,      # 成交额（万元）
    "turnover_rate": 38,  # 换手率(%)
    "pe": 39,          # 市盈率(动态)
    "amplitude": 43,   # 振幅(%)
    "circulation_cap": 44,  # 流通市值
    "market_cap": 45,  # 总市值
    "pb": 46,          # 市净率
    "limit_up": 47,    # 涨停价
    "limit_down": 48,  # 跌停价
    "quantity_ratio": 49,  # 量比
    "委差": 50,        # 委差
    "avg_price": 51,   # 均价
    "pe_dynamic": 52,  # 动态市盈率
    "pe_static": 53,   # 静态市盈率
}

_BASE_URL = "http://qt.gtimg.cn/q="


def _parse_line(line: str) -> dict | None:
    """解析单行腾讯行情数据为字典

    Args:
        line: 形如 v_sz000001="1~平安银行~000001~10.50~..." 的原始数据行

    Returns:
        解析后的标准字段字典，解析失败返回 None
    """
    if "=" not in line:
        return None

    # 提取引号内的数据部分
    try:
        raw = line.split('"')[1]
    except IndexError:
        return None

    if not raw or raw.strip() == "":
        return None

    fields = raw.split("~")
    if len(fields) < 49:
        return None

    def _float(idx: int) -> float | None:
        """安全提取浮点数"""
        try:
            val = fields[idx].strip()
            return float(val) if val else None
        except (IndexError, ValueError):
            return None

    def _int(idx: int) -> int | None:
        """安全提取整数"""
        try:
            val = fields[idx].strip()
            return int(float(val)) if val else None
        except (IndexError, ValueError):
            return None

    code = fields[2].strip()
    price = _float(3)
    prev_close = _float(4)

    # 计算涨跌额和涨跌幅
    change = _float(31)
    change_pct = _float(32)
    if change is None and price is not None and prev_close is not None and prev_close != 0:
        change = round(price - prev_close, 4)
        change_pct = round(change / prev_close * 100, 2)

    result = {
        "code": code,
        "name": fields[1].strip(),
        "price": price,
        "change": change,
        "change_pct": change_pct,
        "open": _float(5),
        "high": _float(33),
        "low": _float(34),
        "prev_close": prev_close,
        "volume": _int(6),           # 成交量（手）
        "amount": _float(36),        # 成交额（万元）
        "pe": _float(39),            # 市盈率
        "pb": _float(46),            # 市净率
        "market_cap": _float(45),    # 总市值
        "turnover_rate": _float(38), # 换手率
        "limit_up": _float(47),      # 涨停价
        "limit_down": _float(48),    # 跌停价
    }

    # 补充额外字段（可选）
    extra = {
        "buy_volume": _int(7),
        "sell_volume": _int(8),
        "amplitude": _float(43),
        "circulation_cap": _float(44),
        "quantity_ratio": _float(49),
        "avg_price": _float(51),
        "pe_dynamic": _float(52),
        "pe_static": _float(53),
        "bid1_price": _float(9),
        "bid1_vol": _int(10),
        "ask1_price": _float(19),
        "ask1_vol": _int(20),
        "datetime": fields[30].strip() if len(fields) > 30 else None,
    }

    # 只保留非 None 的额外字段
    for k, v in extra.items():
        if v is not None:
            result[k] = v

    return result


def quote(codes: list) -> list[dict]:
    """批量获取腾讯财经实时行情

    通过腾讯 qt.gtimg.cn 接口获取实时行情数据，支持 A股/港股/美股。
    支持批量请求，多个代码用逗号拼接一次请求。

    Args:
        codes: 股票代码列表，如 ["600519", "000858", "00700.HK"]
               自动添加市场前缀（sz/sh/hk/us）

    Returns:
        行情字典列表，每个字典包含：
        - code: 代码
        - name: 名称
        - price: 当前价
        - change: 涨跌额
        - change_pct: 涨跌幅(%)
        - open: 开盘价
        - high: 最高价
        - low: 最低价
        - prev_close: 昨收价
        - volume: 成交量（手）
        - amount: 成交额（万元）
        - pe: 市盈率
        - pb: 市净率
        - market_cap: 总市值
        - turnover_rate: 换手率(%)
        - limit_up: 涨停价
        - limit_down: 跌停价

    Raises:
        ValueError: 当 codes 为空列表时
    """
    if not codes:
        raise ValueError("codes 不能为空列表")

    # 归一化代码并添加腾讯前缀
    prefixed = []
    for code in codes:
        prefixed.append(to_tencent_code(code))

    codes_str = ",".join(prefixed)
    url = f"{_BASE_URL}{codes_str}"

    # 请求并解码 GBK 响应
    resp = throttled_get(url, encoding="gbk")
    if resp is None or not resp.ok:
        return []
    text = resp.text

    # 逐行解析
    results = []
    for line in text.strip().split("\n"):
        line = line.strip()
        if not line:
            continue
        parsed = _parse_line(line)
        if parsed is not None:
            results.append(parsed)

    return results
