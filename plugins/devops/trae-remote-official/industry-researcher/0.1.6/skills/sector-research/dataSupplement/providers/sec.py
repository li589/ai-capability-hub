"""SEC EDGAR 数据源模块

提供美国证券交易委员会（SEC）EDGAR 系统的公司文件与 XBRL 财务数据接口。
所有请求须携带规范 User-Agent，遵守 SEC 访问政策（10 req/sec 限制）。
"""

import re
from core.client import http_get

# ─── 基础配置 ─────────────────────────────────────────────────
_SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik}.json"
_XBRL_FACTS_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
_TICKER_LOOKUP_URL = "https://www.sec.gov/cgi-bin/browse-edgar"

# SEC 要求所有自动化请求携带规范的 User-Agent
_SEC_HEADERS = {
    "User-Agent": "DataSupplement/7.1 (dataSupplement@example.com)",
    "Accept-Encoding": "gzip, deflate",
    "Accept": "application/json",
}

# ─── CIK 缓存 ────────────────────────────────────────────────
_cik_cache: dict = {}


def _ticker_to_cik(ticker: str) -> str:
    """将股票代码转换为 SEC CIK 编号（10 位零填充）。

    通过 SEC 的 browse-edgar 接口查询 ticker 对应的 CIK 号，
    结果缓存于内存中避免重复请求。

    Args:
        ticker: 股票代码，如 'AAPL'

    Returns:
        10 位零填充 CIK 字符串，查询失败返回空字符串
    """
    ticker_upper = ticker.upper().strip()
    if ticker_upper in _cik_cache:
        return _cik_cache[ticker_upper]

    params = {
        "action": "getcompany",
        "company": ticker_upper,
        "CIK": ticker_upper,
        "type": "10-K",
        "dateb": "",
        "owner": "include",
        "count": "1",
        "search_text": "",
        "output": "atom",
    }
    resp = http_get(_TICKER_LOOKUP_URL, params=params, headers=_SEC_HEADERS)
    if resp is None:
        return ""

    try:
        text = resp.text
        # 从 atom feed 中提取 CIK
        # 格式: <CIK>0001234567</CIK> 或 cik=0001234567
        cik_match = re.search(r"CIK=(\d{10})", text, re.IGNORECASE)
        if not cik_match:
            cik_match = re.search(r"<cik[^>]*>(\d+)</cik", text, re.IGNORECASE)
        if not cik_match:
            cik_match = re.search(r"cik=(\d+)", text, re.IGNORECASE)
        if not cik_match:
            return ""

        cik = cik_match.group(1).zfill(10)
        _cik_cache[ticker_upper] = cik
        return cik
    except (AttributeError, IndexError):
        return ""


def filings(ticker: str, form_type: str = None, count: int = 10) -> list:
    """查询公司 SEC 文件提交记录。

    Args:
        ticker: 股票代码，如 'AAPL'
        form_type: 文件类型筛选，如 '10-K'、'10-Q'、'8-K'，可选
        count: 返回条数，默认 10

    Returns:
        文件列表，每条含 form / filingDate / primaryDocument / accessionNumber 等
    """
    cik = _ticker_to_cik(ticker)
    if not cik:
        return []

    url = _SUBMISSIONS_URL.format(cik=cik)
    resp = http_get(url, headers=_SEC_HEADERS)
    if resp is None:
        return []

    try:
        data = resp.json()
    except (ValueError, AttributeError):
        return []

    recent = data.get("filings", {}).get("recent", {})
    if not recent:
        return []

    # 提取各字段数组
    forms = recent.get("form", [])
    dates = recent.get("filingDate", [])
    documents = recent.get("primaryDocument", [])
    accessions = recent.get("accessionNumber", [])
    descriptions = recent.get("primaryDocDescription", [])

    results = []
    for i in range(min(len(forms), len(dates))):
        record = {
            "form": forms[i] if i < len(forms) else "",
            "filingDate": dates[i] if i < len(dates) else "",
            "primaryDocument": documents[i] if i < len(documents) else "",
            "accessionNumber": accessions[i] if i < len(accessions) else "",
            "description": descriptions[i] if i < len(descriptions) else "",
        }
        # 按 form_type 过滤
        if form_type and record["form"] != form_type:
            continue
        results.append(record)
        if len(results) >= count:
            break

    return results


def xbrl_facts(ticker: str, taxonomy: str = "us-gaap") -> dict:
    """获取公司 XBRL 财务事实数据。

    通过 SEC companyfacts API 获取结构化财务数据，
    包含所有已提交的 XBRL 标签值。

    Args:
        ticker: 股票代码
        taxonomy: 会计准则分类，默认 'us-gaap'，可选 'ifrs-full'

    Returns:
        XBRL facts 字典，按概念名索引，含 units / label / description 等
    """
    cik = _ticker_to_cik(ticker)
    if not cik:
        return {}

    url = _XBRL_FACTS_URL.format(cik=cik)
    resp = http_get(url, headers=_SEC_HEADERS)
    if resp is None:
        return {}

    try:
        data = resp.json()
    except (ValueError, AttributeError):
        return {}

    facts = data.get("facts", {})
    taxonomy_data = facts.get(taxonomy, {})
    return taxonomy_data if isinstance(taxonomy_data, dict) else {}
