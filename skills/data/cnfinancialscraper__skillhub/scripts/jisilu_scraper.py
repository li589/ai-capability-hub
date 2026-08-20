# -*- coding: utf-8 -*-
"""
集思录可转债数据爬虫模块

数据源: jisilu.cn（可转债数据）
提供可转债全量列表查询和单只可转债详细信息获取。

主要函数:
    - get_convertible_bonds()  — 获取全量可转债列表
    - get_bond_detail(bond_code) — 获取单只可转债详细信息

API:
    - 数据接口: https://www.jisilu.cn/data/cbnew/cb_list/
    - 需要设置正确的 User-Agent 和 Referer
    - 返回 JSON 格式
"""

import logging
from typing import Optional, Dict, Any, List

try:
    from .http_utils import http_get_json, http_get, http_post, rate_limit, get_session
except ImportError:
    from http_utils import http_get_json, http_get, http_post, rate_limit, get_session

log = logging.getLogger(__name__)

# ==================== 常量 ====================

JISILU_CB_LIST_URL = "https://www.jisilu.cn/data/cbnew/cb_list/"
JISILU_CB_DETAIL_URL = "https://www.jisilu.cn/data/cbnew/cb_detail_new/"
JISILU_REFERER = "https://www.jisilu.cn/cbnew/"

# 集思录需要特定的请求头来绕过反爬
JISILU_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Referer": JISILU_REFERER,
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "X-Requested-With": "XMLHttpRequest",
}

# 可转债列表 POST 请求的默认参数
DEFAULT_CB_LIST_PARAMS = {
    "btype": "C",       # C=可转债
    "listed": "Y",      # Y=已上市
    "rp": "50",         # 每页条数
    "page": "1",
}

# ==================== 安全类型转换 ====================


def _safe_float(val, default=None):
    """安全转换为浮点数"""
    if val is None or val == "" or val == "-":
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


def _safe_str(val, default=""):
    """安全转换为字符串"""
    if val is None:
        return default
    return str(val)


# ==================== 可转债列表 ====================


def _akshare_bond_fallback(listed_only: bool = True) -> List[Dict[str, Any]]:
    """v5.0.0: 集思录接口被封时降级到 akshare 可转债全量数据（尽力而为）。"""
    try:
        from scripts.akshare_fallback import fallback_akshare
        return fallback_akshare(
            "bond_zh_hs_cov",
            {"symbol": "沪深" if listed_only else "沪深京"},
            {"bond_id": ["代码"], "bond_nm": ["名称"], "price": ["最新价"],
             "convert_price": ["转股价"], "premium_rt": ["溢价率"],
             "ytm_rt": ["到期税前收益"], "rating_cd": ["信用评级"],
             "year_left": ["剩余年限"], "stock_id": ["正股代码"], "stock_nm": ["正股名称"]},
        )
    except Exception:
        return []


def get_convertible_bonds(listed_only: bool = True,
                          page: int = 1,
                          page_size: int = 50) -> List[Dict[str, Any]]:
    """
    获取集思录全量可转债列表。

    通过集思录 cb_list 接口获取可转债数据，每只包含:
    代码、名称、现价、转股价、溢价率、到期收益率、评级、剩余年限等字段。

    Args:
        listed_only: 是否仅获取已上市可转债（默认 True）
        page: 页码（默认 1）
        page_size: 每页条数（默认 50）

    Returns:
        可转债信息列表，每个元素为 dict，主要字段包括:
        - bond_id: 可转债代码
        - bond_nm: 可转债名称
        - price: 现价
        - convert_price: 转股价
        - premium_rt: 溢价率(%)
        - ytm_rt: 到期收益率(%)
        - rating_cd: 评级
        - year_left: 剩余年限
        - stock_id: 正股代码
        - stock_nm: 正股名称
        - put_convert_price: 回售价
        失败返回空列表
    """
    # 先 GET 首页获取 Cookie/Token（集思录需要 Cookie 才能访问数据接口）
    log.info("正在访问集思录首页以获取 Cookie...")
    session = get_session(headers=JISILU_HEADERS)
    home_resp = http_get(
        "https://www.jisilu.cn/cbnew/",
        headers=JISILU_HEADERS,
        session=session,
        use_cache=False,
    )
    if home_resp is None:
        log.warning("访问集思录首页失败，尝试直接请求数据接口")

    # 构造请求参数
    params = dict(DEFAULT_CB_LIST_PARAMS)
    params["rp"] = str(page_size)
    params["page"] = str(page)
    if not listed_only:
        params["listed"] = "N"

    # 限流
    rate_limit(url=JISILU_CB_LIST_URL)

    # POST 请求数据接口（集思录 cb_list 使用 POST）
    log.info(f"正在请求可转债列表: page={page}, page_size={page_size}")
    try:
        resp = http_post(
            JISILU_CB_LIST_URL,
            data=params,
            headers=JISILU_HEADERS,
            session=session,
            timeout=30,
        )
        if resp is None:
            log.error("集思录可转债列表请求失败")
            return _akshare_bond_fallback(listed_only)

        data = resp.json()
    except Exception as e:
        log.error(f"集思录可转债列表解析失败: {e}")
        return _akshare_bond_fallback(listed_only)

    # 解析返回数据
    # 集思录返回格式: {"rows": [...], "total": N, "page": 1}
    rows = data.get("rows", [])
    if not rows:
        # 某些情况下数据可能在 data 字段下
        rows = data.get("data", {}).get("rows", [])
        if not rows:
            log.warning("集思录返回数据为空")
            return []

    bonds = []
    for row in rows:
        cell = row.get("cell", row)  # 兼容不同返回格式
        bond = {
            "bond_id": _safe_str(cell.get("bond_id", "")),
            "bond_nm": _safe_str(cell.get("bond_nm", "")),
            "price": _safe_float(cell.get("price")),
            "convert_price": _safe_float(cell.get("convert_price")),
            "premium_rt": _safe_float(cell.get("premium_rt")),
            "ytm_rt": _safe_float(cell.get("ytm_rt")),
            "rating_cd": _safe_str(cell.get("rating_cd", "")),
            "year_left": _safe_float(cell.get("year_left")),
            "stock_id": _safe_str(cell.get("stock_id", "")),
            "stock_nm": _safe_str(cell.get("stock_nm", "")),
            "convert_value": _safe_float(cell.get("convert_value")),
            "volume": _safe_float(cell.get("volume")),
            "svolume": _safe_float(cell.get("svolume")),
            "put_convert_price": _safe_float(cell.get("put_convert_price")),
            "force_redeem_price": _safe_float(cell.get("force_redeem_price")),
            "maturity_dt": _safe_str(cell.get("maturity_dt", "")),
            "list_dt": _safe_str(cell.get("list_dt", "")),
            "issuer_rating_cd": _safe_str(cell.get("issuer_rating_cd", "")),
            "guarantor": _safe_str(cell.get("guarantor", "")),
            "coupon_rate": _safe_str(cell.get("coupon_rate", "")),
            "issue_size": _safe_float(cell.get("issue_size")),
            "remain_size": _safe_float(cell.get("remain_size")),
            "adj_scnt": _safe_float(cell.get("adj_scnt")),       # 已下调转股价次数
            "adj_cnt": _safe_float(cell.get("adj_cnt")),         # 总下调转股价次数
            "ration_rt": _safe_float(cell.get("ration_rt")),     # 股东配售率
            "syl_rt": _safe_float(cell.get("syl_rt")),           # 收益率
            "cb_type": _safe_str(cell.get("cb_type", "")),       # 可转债类型
        }
        bonds.append(bond)

    log.info(f"成功获取 {len(bonds)} 只可转债数据")
    return bonds


def get_all_convertible_bonds(listed_only: bool = True) -> List[Dict[str, Any]]:
    """
    分页获取全量可转债列表（自动遍历所有页码）。

    Args:
        listed_only: 是否仅获取已上市可转债

    Returns:
        全量可转债信息列表
    """
    all_bonds = []
    page = 1

    while True:
        bonds = get_convertible_bonds(
            listed_only=listed_only,
            page=page,
            page_size=100,  # 集思录单页最大约100条
        )

        if not bonds:
            break

        all_bonds.extend(bonds)

        # 如果返回数量不足一页，说明已到末尾
        if len(bonds) < 100:
            break

        page += 1

    log.info(f"全量获取完成，共 {len(all_bonds)} 只可转债")
    return all_bonds


# ==================== 单只可转债详情 ====================


def get_bond_detail(bond_code: str) -> Optional[Dict[str, Any]]:
    """
    获取单只可转债的详细信息。

    通过集思录 cb_detail_new 接口获取单只可转债的详细数据，
    包含历史价格、回售条款、强赎条款、下修条款等。

    Args:
        bond_code: 可转债代码（如 "110059"）

    Returns:
        可转债详情字典，包含:
        - 基本信息: 代码、名称、现价、转股价
        - 条款信息: 回售价、强赎触发价、下修触发条件
        - 历史数据: 价格走势关键节点
        失败返回 None
    """
    log.info(f"正在获取可转债详情: {bond_code}")

    session = get_session(headers=JISILU_HEADERS)

    # 请求详情接口
    params = {"bond_id": bond_code}
    rate_limit(url=JISILU_CB_DETAIL_URL)

    try:
        resp = http_post(
            JISILU_CB_DETAIL_URL,
            data=params,
            headers=JISILU_HEADERS,
            session=session,
            timeout=30,
        )
        if resp is None:
            log.error(f"可转债 {bond_code} 详情请求失败")
            return None

        data = resp.json()
    except Exception as e:
        log.error(f"可转债 {bond_code} 详情解析失败: {e}")
        return None

    # 解析详情数据
    if not data:
        return None

    # 集思录详情可能嵌套在多层结构下
    detail = data.get("data", data)

    return {
        "bond_id": bond_code,
        "bond_nm": _safe_str(detail.get("bond_nm", "")),
        "price": _safe_float(detail.get("price")),
        "convert_price": _safe_float(detail.get("convert_price")),
        "premium_rt": _safe_float(detail.get("premium_rt")),
        "ytm_rt": _safe_float(detail.get("ytm_rt")),
        "rating_cd": _safe_str(detail.get("rating_cd", "")),
        "stock_id": _safe_str(detail.get("stock_id", "")),
        "stock_nm": _safe_str(detail.get("stock_nm", "")),
        "put_convert_price": _safe_float(detail.get("put_convert_price")),
        "force_redeem_price": _safe_float(detail.get("force_redeem_price")),
        "convert_low_price": _safe_float(detail.get("convert_low_price")),
        "maturity_dt": _safe_str(detail.get("maturity_dt", "")),
        "year_left": _safe_float(detail.get("year_left")),
        "issue_size": _safe_float(detail.get("issue_size")),
        "remain_size": _safe_float(detail.get("remain_size")),
        "coupon_rate": _safe_str(detail.get("coupon_rate", "")),
        "guarantor": _safe_str(detail.get("guarantor", "")),
        "issuer_rating_cd": _safe_str(detail.get("issuer_rating_cd", "")),
        "raw_data": detail,  # 保留原始数据以备扩展
    }


# ==================== 便捷查询 ====================


def search_bonds(keyword: str) -> List[Dict[str, Any]]:
    """
    根据关键词搜索可转债（从全量列表中按代码或名称筛选）。

    Args:
        keyword: 搜索关键词（可转债代码或名称关键字）

    Returns:
        匹配的可转债列表
    """
    all_bonds = get_convertible_bonds(listed_only=False, page_size=100)
    keyword_lower = keyword.lower()

    results = []
    for bond in all_bonds:
        bond_id = str(bond.get("bond_id", "")).lower()
        bond_nm = str(bond.get("bond_nm", "")).lower()
        stock_nm = str(bond.get("stock_nm", "")).lower()

        if (keyword_lower in bond_id
                or keyword_lower in bond_nm
                or keyword_lower in stock_nm):
            results.append(bond)

    log.info(f"搜索 '{keyword}' 找到 {len(results)} 只可转债")
    return results


def get_low_premium_bonds(top_n: int = 20,
                          max_premium: float = 30.0) -> List[Dict[str, Any]]:
    """
    获取低溢价率可转债排行。

    Args:
        top_n: 返回前 N 只
        max_premium: 溢价率上限（%），超过此值不纳入

    Returns:
        低溢价率可转债列表，按溢价率升序排列
    """
    all_bonds = get_convertible_bonds(listed_only=True, page_size=100)

    # 筛选有效溢价率数据
    valid_bonds = []
    for bond in all_bonds:
        premium = bond.get("premium_rt")
        price = bond.get("price")
        if premium is not None and price is not None and price > 0:
            if premium <= max_premium:
                valid_bonds.append(bond)

    # 按溢价率升序排列
    valid_bonds.sort(key=lambda x: x.get("premium_rt", 999))

    result = valid_bonds[:top_n]
    log.info(f"低溢价率可转债: 找到 {len(result)} 只（溢价率 <= {max_premium}%）")
    return result


# ==================== 测试入口 ====================

if __name__ == "__main__":
    import json

    print("=" * 60)
    print("集思录可转债爬虫 - 功能测试")
    print("=" * 60)

    # 测试1: 获取可转债列表（第一页）
    print("\n[测试1] 获取可转债列表（前20条）...")
    bonds = get_convertible_bonds(page_size=20)
    if bonds:
        print(f"成功获取 {len(bonds)} 只可转债")
        print(f"\n前3只示例:")
        for bond in bonds[:3]:
            print(f"  {bond.get('bond_id')} {bond.get('bond_nm')} "
                  f"现价:{bond.get('price')} "
                  f"溢价率:{bond.get('premium_rt')}% "
                  f"评级:{bond.get('rating_cd')}")
    else:
        print("获取失败（可能需要有效的集思录 Cookie）")

    # 测试2: 搜索可转债
    print("\n[测试2] 搜索含'银行'的可转债...")
    results = search_bonds("银行")
    for bond in results[:5]:
        print(f"  {bond.get('bond_id')} {bond.get('bond_nm')} "
              f"正股:{bond.get('stock_nm')}")

    # 测试3: 低溢价率排行
    print("\n[测试3] 低溢价率可转债 Top 10...")
    low_p = get_low_premium_bonds(top_n=10, max_premium=20)
    for i, bond in enumerate(low_p[:10], 1):
        print(f"  {i}. {bond.get('bond_id')} {bond.get('bond_nm')} "
              f"溢价率:{bond.get('premium_rt')}% "
              f"现价:{bond.get('price')}")

    # 测试4: 单只可转债详情
    if bonds:
        test_code = bonds[0].get("bond_id", "")
        if test_code:
            print(f"\n[测试4] 获取可转债详情: {test_code}")
            detail = get_bond_detail(test_code)
            if detail:
                print(json.dumps(detail, ensure_ascii=False, indent=2, default=str))
            else:
                print("获取详情失败")

    print("\n" + "=" * 60)
    print("测试完成")
