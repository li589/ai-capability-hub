"""
财联社快讯 Provider

数据源：cls.cn
协议：HTTPS GET，JSON 响应
封禁风险：低
覆盖市场：A股/宏观

特点：无需 API Key，通过本地签名计算（md5(sha1(sorted_params))）认证。
"""

from __future__ import annotations

import hashlib
import time
import datetime

from core.client import http_get


# ========== 签名计算 ==========


def _compute_sign(params: dict) -> str:
    """计算财联社接口签名

    签名算法：将请求参数按 key 排序拼接为 query string，
    先 SHA1 哈希，再 MD5 哈希，得到最终签名。

    算法流程：
        1. 按参数 key 字母排序
        2. 拼接为 "key1=val1&key2=val2&..." 格式
        3. SHA1(query_string) -> hex_digest
        4. MD5(sha1_hex) -> hex_digest（最终签名）

    Args:
        params: 请求参数字典（不含 sign 字段本身）

    Returns:
        32位小写十六进制签名字符串
    """
    # 按 key 字母序排列
    sorted_keys = sorted(params.keys())
    query_parts = []
    for key in sorted_keys:
        val = params[key]
        if val is not None and val != "":
            query_parts.append(f"{key}={val}")

    query_string = "&".join(query_parts)

    # SHA1 -> MD5
    sha1_hash = hashlib.sha1(query_string.encode("utf-8")).hexdigest()
    md5_hash = hashlib.md5(sha1_hash.encode("utf-8")).hexdigest()

    return md5_hash


# ========== 7x24 快讯 ==========

_TELEGRAPH_API = "https://www.cls.cn/v1/roll/get_roll_list"

# 快讯分类映射
_CATEGORY_MAP = {
    "全部": None,
    "重要": "1",
    "A股": "5",
    "美股": "6",
    "港股": "7",
    "外汇": "8",
    "商品": "9",
    "宏观": "10",
    "公司": "11",
    "科技": "12",
}


def telegraph(category: str | None = None, count: int = 50) -> list[dict]:
    """获取财联社 7x24 实时快讯

    通过财联社电报接口获取实时财经资讯流，支持按分类筛选。
    接口使用本地签名认证，无需 API Key。

    Args:
        category: 分类筛选，可选：
            全部, 重要, A股, 美股, 港股, 外汇, 商品, 宏观, 公司, 科技
            默认为全部
        count: 获取条数，默认50，最大100

    Returns:
        快讯列表，每项包含：
        - id: 快讯ID
        - title: 标题（如有）
        - content: 快讯正文
        - time: 发布时间（Unix 时间戳）
        - datetime: 格式化时间字符串
        - level: 重要性级别
        - tags: 关联标签列表
        - stocks: 关联股票代码列表
    """
    count = min(count, 100)
    now_ts = str(int(time.time()))

    # 构造基础参数
    params = {
        "app": "CailianpressWeb",
        "os": "web",
        "sv": "8.4.6",
        "rn": str(count),
        "last_time": now_ts,
    }

    # 分类过滤
    if category and category in _CATEGORY_MAP:
        cat_id = _CATEGORY_MAP[category]
        if cat_id:
            params["category"] = cat_id

    # 计算签名
    sign = _compute_sign(params)
    params["sign"] = sign

    # 拼接请求 URL
    query_str = "&".join(f"{k}={v}" for k, v in params.items())
    url = f"{_TELEGRAPH_API}?{query_str}"

    resp = http_get(url)
    if resp is None or not resp.ok:
        return []
    try:
        data = resp.json()
    except (ValueError, AttributeError):
        return []

    # 解析响应
    roll_data = data.get("data", {})
    roll_list = roll_data.get("roll_data", roll_data.get("roll_list", roll_data.get("data", [])))
    if not isinstance(roll_list, list):
        return []

    results = []
    for item in roll_list:
        # 提取关联股票
        stocks = []
        stock_list = item.get("stocks", item.get("associated_stocks", []))
        if isinstance(stock_list, list):
            for s in stock_list:
                if isinstance(s, dict):
                    stocks.append(s.get("code", s.get("symbol", "")))
                elif isinstance(s, str):
                    stocks.append(s)

        # 提取标签
        tags = []
        tag_list = item.get("tags", item.get("subjects", []))
        if isinstance(tag_list, list):
            for t in tag_list:
                if isinstance(t, dict):
                    tags.append(t.get("name", t.get("subject_name", "")))
                elif isinstance(t, str):
                    tags.append(t)

        # 时间处理
        ctime = item.get("ctime", item.get("time", 0))
        dt_str = ""
        if ctime:
            try:
                dt_str = datetime.datetime.fromtimestamp(
                    int(ctime)
                ).strftime("%Y-%m-%d %H:%M:%S")
            except (ValueError, OSError):
                dt_str = str(ctime)

        results.append({
            "id": item.get("id", ""),
            "title": item.get("title", ""),
            "content": item.get("content", item.get("brief", "")),
            "time": ctime,
            "datetime": dt_str,
            "level": item.get("level", item.get("importance", 0)),
            "tags": tags,
            "stocks": stocks,
        })

    return results
