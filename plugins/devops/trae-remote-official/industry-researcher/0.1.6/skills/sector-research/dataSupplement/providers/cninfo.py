"""
巨潮资讯 Provider

数据源：www.cninfo.com.cn / irm.cninfo.com.cn
协议：HTTPS POST（公告）/ HTTPS GET（互动易）
封禁风险：低
覆盖市场：A股

主要提供上市公司公告检索和互动易问答数据。
"""

from __future__ import annotations

from core.client import http_get, http_post
from core.ticker import normalize


# ========== 模块级缓存 ==========

# org_id 缓存，避免重复查询
_ORG_ID_CACHE: dict[str, str] = {}


# ========== 内部工具 ==========

_ORG_SEARCH_URL = "https://www.cninfo.com.cn/new/information/topSearch/detailOfQuery"


def _get_org_id(code: str) -> str:
    """获取巨潮内部 org_id

    巨潮接口使用 orgId 标识上市公司，需先通过股票代码查询映射。
    结果缓存到模块级字典避免重复请求。

    Args:
        code: 归一化后的6位股票代码

    Returns:
        orgId 字符串，查询失败返回空字符串
    """
    if code in _ORG_ID_CACHE:
        return _ORG_ID_CACHE[code]

    # 通过巨潮搜索接口获取 orgId
    payload = {
        "keyWord": code,
        "maxSecNum": 10,
        "maxListNum": 5,
    }

    try:
        resp = http_post(_ORG_SEARCH_URL, data=payload)
        if resp is None or not resp.ok:
            return ""
        data = resp.json()
    except (ValueError, AttributeError):
        return ""

    # 从结果中匹配目标代码
    stock_list = data.get("stockList", [])
    for item in stock_list:
        item_code = item.get("code", "")
        if item_code == code:
            org_id = item.get("orgId", "")
            _ORG_ID_CACHE[code] = org_id
            return org_id

    # 未精确匹配则取第一个
    if stock_list:
        org_id = stock_list[0].get("orgId", "")
        _ORG_ID_CACHE[code] = org_id
        return org_id

    return ""


# ========== 公告检索 ==========

_ANNOUNCEMENT_URL = "https://www.cninfo.com.cn/new/hisAnnouncement/query"

# 公告分类映射
_CATEGORY_MAP = {
    "年报": "category_ndbg_szsh",
    "半年报": "category_bndbg_szsh",
    "一季报": "category_yjdbg_szsh",
    "三季报": "category_sjdbg_szsh",
    "业绩预告": "category_yjyg_szsh",
    "业绩快报": "category_yjkb_szsh",
    "分红": "category_fhsg_szsh",
    "增减持": "category_zjc_szsh",
    "股权质押": "category_gqzr_szsh",
    "定增": "category_zf_szsh",
    "回购": "category_hg_szsh",
    "关联交易": "category_gljy_szsh",
}


def announcements(
    code: str,
    keyword: str | None = None,
    start: str | None = None,
    end: str | None = None,
    category: str | None = None,
) -> list[dict]:
    """搜索上市公司公告

    通过巨潮资讯网公告查询接口检索公告信息，支持关键词、时间范围和分类过滤。

    Args:
        code: 股票代码，如 "600519"
        keyword: 搜索关键词，如 "分红", "回购", "业绩"
        start: 起始日期，格式 "YYYY-MM-DD"
        end: 截止日期，格式 "YYYY-MM-DD"
        category: 公告分类，可选：
            年报, 半年报, 一季报, 三季报, 业绩预告, 业绩快报,
            分红, 增减持, 股权质押, 定增, 回购, 关联交易

    Returns:
        公告列表，每项包含：
        - title: 公告标题
        - date: 发布日期
        - url: 公告PDF链接
        - category: 分类
        - summary: 摘要（如有）
    """
    normalized = normalize(code)

    # 判断交易所前缀（巨潮需要完整代码含交易所）
    if normalized.startswith("6") or normalized.startswith("9"):
        stock_code = f"{normalized},gssh0{normalized}"
        plate = "sh"
    elif normalized.startswith("0") or normalized.startswith("3") or normalized.startswith("2"):
        stock_code = f"{normalized},gssz0{normalized}"
        plate = "sz"
    else:
        stock_code = normalized
        plate = ""

    # 构造请求参数
    payload = {
        "stock": stock_code,
        "tabName": "fulltext",
        "pageSize": 30,
        "pageNum": 1,
        "column": "szse" if plate == "sz" else "sse",
        "isHLtitle": "true",
    }

    if keyword:
        payload["searchkey"] = keyword

    if start:
        payload["seDate"] = f"{start}~{end or ''}"
    elif end:
        payload["seDate"] = f"~{end}"

    if category:
        mapped_cat = _CATEGORY_MAP.get(category, "")
        if mapped_cat:
            payload["category"] = mapped_cat

    resp = http_post(_ANNOUNCEMENT_URL, data=payload)
    if resp is None or not resp.ok:
        return []
    try:
        data = resp.json()
    except (ValueError, AttributeError):
        return []

    announcements_list = data.get("announcements", [])
    if not announcements_list:
        return []

    results = []
    for ann in announcements_list:
        adj_title = ann.get("announcementTitle", "")
        # 去除高亮标签
        adj_title = adj_title.replace("<em>", "").replace("</em>", "")

        pdf_url = ""
        adj_url = ann.get("adjunctUrl", "")
        if adj_url:
            pdf_url = f"http://static.cninfo.com.cn/{adj_url}"

        results.append({
            "title": adj_title,
            "date": ann.get("announcementTime", ""),
            "url": pdf_url,
            "category": ann.get("announcementTypeName", ""),
            "summary": ann.get("adjunctContent", ""),
            "code": ann.get("secCode", normalized),
            "company": ann.get("secName", ""),
        })

    return results


# ========== 互动易问答 ==========

# 旧接口 https://irm.cninfo.com.cn/ssgs/questionListByPage 已下线。
# 现行接口(2024+):
#   1) 查 orgId(secid): POST newircs/index/queryKeyboardInfo (data: keyWord=代码)
#   2) 查问答明细:      POST newircs/company/question (query: stockcode + orgId)
# 注意: 该平台仅覆盖深市股票; 沪市股票(6开头)在此接口通常无数据。
_IRM_KEYBOARD_URL = "https://irm.cninfo.com.cn/newircs/index/queryKeyboardInfo"
_IRM_QUESTION_URL = "https://irm.cninfo.com.cn/newircs/company/question"

_IRM_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Referer": "https://irm.cninfo.com.cn/",
    "Accept": "application/json, text/plain, */*",
}


def _irm_secid(code: str) -> str:
    """通过互动易键盘搜索接口取 secid(orgId)。"""
    cache_key = f"irm:{code}"
    if cache_key in _ORG_ID_CACHE:
        return _ORG_ID_CACHE[cache_key]
    try:
        resp = http_post(
            f"{_IRM_KEYBOARD_URL}?_t=1",
            data={"keyWord": code},
            headers=_IRM_HEADERS,
        )
        if resp is None or not resp.ok:
            return ""
        arr = resp.json().get("data", [])
        for item in arr:
            if item.get("stockCode") == code:
                secid = item.get("secid", "")
                _ORG_ID_CACHE[cache_key] = secid
                return secid
        if arr:
            secid = arr[0].get("secid", "")
            _ORG_ID_CACHE[cache_key] = secid
            return secid
    except (ValueError, AttributeError, KeyError, TypeError):
        return ""
    return ""


def _irm_ms_to_date(val) -> str:
    """毫秒时间戳 -> YYYY-MM-DD HH:MM:SS 字符串。"""
    if not val:
        return ""
    try:
        from datetime import datetime, timezone, timedelta
        ts = int(val) / 1000.0
        dt = datetime.fromtimestamp(ts, tz=timezone(timedelta(hours=8)))
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except (ValueError, TypeError, OSError):
        return str(val)


def investor_qa(code: str, page: int = 1) -> list[dict]:
    """获取互动易投资者问答

    从巨潮互动易平台获取投资者与上市公司的问答记录。
    （沪市 6 开头股票该平台通常无数据，属正常现象。）

    Args:
        code: 股票代码，如 "002594"
        page: 页码，从1开始

    Returns:
        问答列表，每项包含：
        - question: 投资者提问内容
        - answer: 公司回复内容
        - question_date: 提问日期
        - answer_date: 回复日期
        - questioner: 提问者（如有）
    """
    normalized = normalize(code)
    secid = _irm_secid(normalized)
    if not secid:
        return []

    query = (
        f"_t=1&stockcode={normalized}&orgId={secid}"
        f"&pageSize=20&pageNum={page}&keyWord=&startDay=&endDay="
    )
    url = f"{_IRM_QUESTION_URL}?{query}"

    resp = http_post(url, headers=_IRM_HEADERS)
    if resp is None or not resp.ok:
        return []
    try:
        data = resp.json()
    except (ValueError, AttributeError):
        return []

    records = data.get("rows", [])
    if not isinstance(records, list):
        return []

    results = []
    for item in records:
        results.append({
            "question": item.get("mainContent", ""),
            "answer": item.get("attachedContent", "") or "",
            "question_date": _irm_ms_to_date(item.get("pubDate")),
            "answer_date": _irm_ms_to_date(item.get("attachedPubDate")),
            "questioner": item.get("authorName", ""),
        })

    return results
