"""akshare 补缺桥接模块

对 akshare 库的涨停池、板块数据、资金流等接口进行薄封装，
作为主数据源（东财/通达信）的补充。优雅处理 akshare 未安装的情况。
"""

_akshare_available = True
try:
    import akshare
except ImportError:
    _akshare_available = False


def _check_available(func_name: str) -> bool:
    """检查 akshare 库是否可用。"""
    if not _akshare_available:
        return False
    return True


def _safe_to_list(df) -> list:
    """安全将 DataFrame 转换为字典列表。"""
    if df is None:
        return []
    try:
        if hasattr(df, "to_dict"):
            return df.to_dict("records")
        return list(df) if df is not None else []
    except (TypeError, ValueError, AttributeError):
        return []


def zt_pool(date: str) -> list:
    """涨停板池（当日涨停股票列表）。

    Args:
        date: 交易日期，格式 'YYYYMMDD'

    Returns:
        涨停股列表，含 code/name/涨停时间/连板天数 等
    """
    if not _check_available("zt_pool"):
        return []
    try:
        df = akshare.stock_zt_pool_em(date=date)
        return _safe_to_list(df)
    except Exception:
        return []


def zb_pool(date: str) -> list:
    """炸板池（当日曾涨停后打开的股票）。

    Args:
        date: 交易日期，格式 'YYYYMMDD'

    Returns:
        炸板股列表
    """
    if not _check_available("zb_pool"):
        return []
    try:
        df = akshare.stock_zt_pool_zbgc_em(date=date)
        return _safe_to_list(df)
    except Exception:
        return []


def dt_pool(date: str) -> list:
    """跌停池（当日跌停股票列表）。

    Args:
        date: 交易日期，格式 'YYYYMMDD'

    Returns:
        跌停股列表
    """
    if not _check_available("dt_pool"):
        return []
    try:
        df = akshare.stock_zt_pool_dtgc_em(date=date)
        return _safe_to_list(df)
    except Exception:
        return []


def yesterday_zt(date: str) -> list:
    """昨日涨停今日表现。

    Args:
        date: 交易日期，格式 'YYYYMMDD'

    Returns:
        昨日涨停股今日表现列表
    """
    if not _check_available("yesterday_zt"):
        return []
    try:
        df = akshare.stock_zt_pool_previous_em(date=date)
        return _safe_to_list(df)
    except Exception:
        return []


def concept_board() -> list:
    """概念板块列表。

    Returns:
        概念板块名称及涨跌幅列表
    """
    if not _check_available("concept_board"):
        return []
    try:
        df = akshare.stock_board_concept_name_em()
        return _safe_to_list(df)
    except Exception:
        return []


def industry_board() -> list:
    """行业板块列表。

    Returns:
        行业板块名称及涨跌幅列表
    """
    if not _check_available("industry_board"):
        return []
    try:
        df = akshare.stock_board_industry_name_em()
        return _safe_to_list(df)
    except Exception:
        return []


def individual_fund_flow(code: str) -> list:
    """个股资金流向。

    Args:
        code: 股票代码，如 '600519'

    Returns:
        资金流向数据列表，含主力/超大单/大单/中单/小单净流入等
    """
    if not _check_available("individual_fund_flow"):
        return []
    try:
        df = akshare.stock_individual_fund_flow(
            stock=code,
            market="sh" if code.startswith(("6", "5", "9")) else "sz",
        )
        return _safe_to_list(df)
    except Exception:
        return []


# ========== 财报（新浪接口下线后的降级源） ==========

# domain 报表类型 -> akshare stock_financial_report_sina 的 symbol 参数
_SINA_REPORT_SYMBOL = {
    "income": "利润表",
    "balance_sheet": "资产负债表",
    "cashflow": "现金流量表",
}


def financial_report_cn(code: str, report_type: str = "income") -> list:
    """A股财报三表（东财新浪接口 via akshare）。

    作为 providers.sina.financial_report 的降级源：
    新浪 CompanyFinanceService 接口已下线，改用 akshare 封装的
    stock_financial_report_sina（按报告期返回完整字段）。

    Args:
        code: 股票代码，如 '600519' / 'sh600519' / '600519.SH'
        report_type: 'income' / 'balance_sheet' / 'cashflow'

    Returns:
        按报告期的记录列表，每项含 '报告日' 及各科目字段
    """
    if not _check_available("financial_report_cn"):
        return []
    symbol = _SINA_REPORT_SYMBOL.get(report_type, "利润表")
    # 规范成 akshare 需要的 shXXXXXX / szXXXXXX 形式
    digits = "".join(ch for ch in str(code) if ch.isdigit())
    if not digits:
        return []
    prefix = "sh" if digits.startswith(("6", "5", "9")) else "sz"
    ak_symbol = f"{prefix}{digits}"
    try:
        df = akshare.stock_financial_report_sina(stock=ak_symbol, symbol=symbol)
        records = _safe_to_list(df)
        # 统一把 '报告日' 暴露为 report_date，兼容上层字段习惯
        for r in records:
            if "报告日" in r and "report_date" not in r:
                r["report_date"] = r["报告日"]
        return records
    except Exception:
        return []


# ========== ETF期权合约清单（新浪 OptionService 下线后的降级源） ==========


def option_contracts_cn(underlying: str = "510050", call: bool = True) -> list:
    """A股 ETF 期权当月合约清单（上交所 via akshare）。

    作为 domains.options 中新浪 OptionService 接口的降级源。
    先取该标的当前有效到期月，再拉当月认购/认沽合约代码。

    Args:
        underlying: ETF 标的代码，如 '510050'(50ETF)/'510300'(300ETF)
        call: True 认购，False 认沽

    Returns:
        合约列表，每项含 contract_code / direction / underlying / month
    """
    if not _check_available("option_contracts_cn"):
        return []
    # 标的代码 -> option_sse_list_sina 的 symbol 名
    underlying_symbol = {
        "510050": "50ETF", "510300": "300ETF", "510500": "500ETF",
        "588000": "科创50ETF", "159919": "300ETF", "159901": "深100ETF",
    }.get(str(underlying), "50ETF")
    direction_symbol = "看涨期权" if call else "看跌期权"
    try:
        months = akshare.option_sse_list_sina(symbol=underlying_symbol, exchange="null")
        if not months:
            return []
        month = str(months[0])  # 最近到期月
        df = akshare.option_sse_codes_sina(
            symbol=direction_symbol, trade_date=month, underlying=str(underlying)
        )
        records = _safe_to_list(df)
        parsed = []
        for r in records:
            ccode = r.get("期权代码") or r.get("contract_code") or ""
            if not ccode:
                continue
            parsed.append({
                "contract_code": str(ccode),
                "direction": "call" if call else "put",
                "underlying": str(underlying),
                "month": month,
            })
        return parsed
    except Exception:
        return []
