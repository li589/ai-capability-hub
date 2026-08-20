# -*- coding: utf-8 -*-
"""akshare 数据源适配器（akshare_fallback.py，v4.9.0 新增）

设计目标：
- 当 cls_scraper / wallstreetcn_scraper / sina_scraper / jisilu_scraper 等
  自有接口被封时，自动降级到 akshare 开源数据源
- 统一异常处理（akshare 不可用/超时/异常 → 透明降级）
- 不强制依赖 akshare（未装时降级到 mock/None）

数据源对照表（v4.9）：

| 原爬虫               | 被封数据源          | akshare 替代函数              |
|---------------------|--------------------|--------------------------------|
| cls_scraper         | cls.cn/api/sw      | stock_info_global_cls / news_...|
| wallstreetcn_scraper| wallstreetcn.com   | 暂无（fallback 失败时返回 []） |
| sina_scraper        | hq.sinajs.cn       | stock_zh_a_spot() 实时行情    |
| jisilu_scraper      | jisilu.cn/data     | bond_zh_hs_cov, bond_zh_cov     |
| eastmoney_scraper  | 各种 JSONP         | stock_zh_a_hist_pre_min_em      |
| cninfo_scraper     | cninfo.com.cn      | stock_notice_report             |

调用方式：
    from scripts.akshare_fallback import fetch_with_fallback

    # 自动尝试原数据源，失败则降级到 akshare
    data = fetch_with_fallback(
        primary=("cls_scraper", "get_hot_articles", {"limit": 10}),
        fallback=("akshare", "news_economic_baidu"),
        mock=[{"title": "降级mock", "id": "fallback"}],
    )
"""
from __future__ import annotations

import logging
from typing import Any, Callable, Dict, List, Optional, Tuple

log = logging.getLogger(__name__)


# 检测 akshare 是否安装
def _has_akshare() -> bool:
    try:
        import akshare  # noqa: F401
        return True
    except ImportError:
        return False


HAS_AKSHARE = _has_akshare()


def _call_primary(module_path: str, func_name: str, kwargs: Dict[str, Any]) -> Any:
    """尝试调用原爬虫模块。

    Args:
        module_path: 形如 "scripts.cls_scraper" 或 "cls_scraper"
        func_name: 函数名
        kwargs: 关键字参数

    Returns:
        原函数返回值；调用失败时返回 None。
    """
    import importlib
    try:
        if module_path.startswith("scripts."):
            mod = importlib.import_module(module_path)
        else:
            # 兼容 "cls_scraper" 这种形式
            try:
                mod = importlib.import_module(f"scripts.{module_path}")
            except ImportError:
                mod = importlib.import_module(module_path)
        func = getattr(mod, func_name)
        return func(**kwargs)
    except Exception as e:
        log.debug(f"primary 调用失败 {module_path}.{func_name}: {e}")
        return None


def _call_akshare(func_name: str, kwargs: Optional[Dict[str, Any]] = None) -> Any:
    """调用 akshare 函数。

    Args:
        func_name: akshare 函数名（如 "news_economic_baidu"）
        kwargs: 关键字参数

    Returns:
        akshare 函数返回值；未装 akshare 或调用失败时返回 None。
    """
    if not HAS_AKSHARE:
        log.debug("akshare 未安装，跳过 fallback")
        return None
    kwargs = kwargs or {}
    try:
        import akshare as ak
        func = getattr(ak, func_name)
        return func(**kwargs)
    except Exception as e:
        log.debug(f"akshare.{func_name} 调用失败: {e}")
        return None


def fetch_with_fallback(primary: Tuple[str, str, Dict[str, Any]],
                         fallback: Optional[Tuple[str, str, Dict[str, Any]]] = None,
                         mock: Optional[List[Dict[str, Any]]] = None,
                         data_validator: Optional[Callable[[Any], bool]] = None) -> Any:
    """统一数据源路由：primary → fallback → mock。

    Args:
        primary: (模块名, 函数名, kwargs) 首选原爬虫
        fallback: (类型, 函数名, kwargs) 可选 akshare 替代
            类型: "akshare" 或 "http" 或 "module_path"
        mock: 最终降级返回的 mock 数据（避免 None 阻塞下游）
        data_validator: 验证 primary 返回值是否合理的回调
            返回 True = primary 成功，使用 primary 结果；返回 False = 触发 fallback

    Returns:
        primary 有效结果 OR fallback 结果 OR mock（按优先级回退）
    """
    module_path, func_name, kwargs = primary
    primary_result = _call_primary(module_path, func_name, kwargs)

    # 验证 primary 是否合理
    # 修复 BUG：data_validator=None 时不应跳过 primary 直接走 fallback。
    # 当 data_validator=None 且 primary_result 非 None，直接返回。
    if data_validator:
        try:
            if data_validator(primary_result):
                return primary_result
        except Exception as e:
            log.debug(f"data_validator 异常: {e}")
    elif primary_result is not None:
        # 无 validator：primary 成功则直接返回
        return primary_result

    # primary 不可用 → fallback
    if fallback is not None:
        ftype, fname, fkwargs = fallback
        if ftype == "akshare":
            fallback_result = _call_akshare(fname, fkwargs)
        elif ftype == "module":
            fallback_result = _call_primary(fname.split(".")[0], fname.split(".")[1], fkwargs)
        else:
            log.warning(f"未知 fallback 类型: {ftype}")
            fallback_result = None
        if fallback_result is not None:
            log.info(f"fallback 成功: {ftype}.{fname}")
            return fallback_result

    # 最终降级
    if mock is not None:
        log.info("返回 mock 数据")
        return mock

    return None


# ============================================================================
# 公共降级 helper（v5.0.0）
# 供各站点 scraper 在 except 分支直接调用，避免经 fetch_with_fallback 回调
# primary 造成循环。
# ============================================================================


def akshare_to_records(result: Any, record_map: Optional[Dict[str, List[str]]] = None) -> List[Dict[str, Any]]:
    """把 akshare 返回结果（DataFrame/list）归一化为 list[dict]，并按字段映射重命名。

    Args:
        result: akshare 函数返回值（pandas.DataFrame / list[dict] / None）
        record_map: {目标字段: [候选源字段...]}，从结果行中取第一个存在的源字段

    Returns:
        list[dict]；无数据时返回 []。
    """
    if result is None:
        return []
    if hasattr(result, "to_dict"):  # pandas.DataFrame
        try:
            result = result.to_dict("records")
        except Exception:
            return []
    if not isinstance(result, list):
        return []
    if not record_map:
        return [dict(r) for r in result if isinstance(r, dict)]
    out = []
    for row in result:
        if not isinstance(row, dict):
            continue
        rec = {}
        for key, sources in record_map.items():
            rec[key] = next((row[s] for s in sources if s in row), "")
        out.append(rec)
    return out


def fallback_akshare(func_name: str,
                     kwargs: Optional[Dict[str, Any]] = None,
                     record_map: Optional[Dict[str, List[str]]] = None) -> List[Dict[str, Any]]:
    """站点 scraper 的兜底入口：直接调用 akshare 函数并归一化为 list[dict]。

    Args:
        func_name: akshare 函数名
        kwargs: 传给 akshare 的参数
        record_map: 字段映射（见 akshare_to_records）

    Returns:
        list[dict]；akshare 未装 / 调用失败 → []。
    """
    result = _call_akshare(func_name, kwargs or {})
    return akshare_to_records(result, record_map)


# ============================================================================
# 便捷适配器（按原爬虫一对一映射）
# ============================================================================


def fetch_cls_hot_articles(limit: int = 10):
    """财联社热门文章（primary: cls_scraper → fallback: akshare → mock）。"""
    from scripts.cls_scraper import get_hot_articles as _primary

    def _validate(data):
        return isinstance(data, list) and len(data) > 0

    return fetch_with_fallback(
        primary=("cls_scraper", "get_hot_articles", {"limit": limit}),
        fallback=("akshare", "news_economic_cls", {"limit": limit}),
        mock=[],
        data_validator=_validate,
    )


def fetch_sina_realtime(stock_codes: List[str]):
    """新浪实时行情（primary: sina_scraper → fallback: akshare → mock）。"""
    from scripts.sina_scraper import get_realtime_quote as _primary

    def _validate(data):
        return isinstance(data, dict) and len(data) > 0

    return fetch_with_fallback(
        primary=("sina_scraper", "get_realtime_quote", {"stock_codes": stock_codes}),
        fallback=("akshare", "stock_zh_a_spot", {}),
        mock={},
        data_validator=_validate,
    )


def fetch_jisilu_convertible_bonds(page: int = 1, page_size: int = 50):
    """集思录可转债列表（primary → fallback akshare → mock）。"""
    from scripts.jisilu_scraper import get_convertible_bonds as _primary

    def _validate(data):
        return isinstance(data, list) and len(data) > 0

    return fetch_with_fallback(
        primary=("jisilu_scraper", "get_convertible_bonds",
                 {"page": page, "page_size": page_size}),
        fallback=("akshare", "bond_zh_hs_cov", {}),
        mock=[],
        data_validator=_validate,
    )


def fetch_wallstreetcn_live():
    """华尔街见闻直播（primary → fallback akshare → mock）。"""
    from scripts.wallstreetcn_scraper import get_live_news as _primary

    def _validate(data):
        return isinstance(data, list) and len(data) > 0

    return fetch_with_fallback(
        primary=("wallstreetcn_scraper", "get_live_news", {}),
        fallback=("akshare", "news_economic_baidu", {}),
        mock=[],
        data_validator=_validate,
    )


# ============================================================================
# 自检（仅在 CLI 调用时执行）
# ============================================================================


def self_check() -> Dict[str, Any]:
    """返回数据源健康度自检报告。"""
    return {
        "akshare_installed": HAS_AKSHARE,
        "primary_modules": [
            "cls_scraper", "sina_scraper", "jisilu_scraper",
            "wallstreetcn_scraper", "eastmoney_scraper", "cninfo_scraper",
        ],
        "fallback_strategy": "akshare (zero-token, free, A股最全)",
    }


if __name__ == "__main__":
    import json
    print(json.dumps(self_check(), ensure_ascii=False, indent=2))
    if HAS_AKSHARE:
        print("\n✅ akshare 已安装，可作为 fallback 数据源")
    else:
        print("\n⚠️ akshare 未安装，建议 `pip install akshare` 以启用 fallback")
        print("   pip install akshare --upgrade  # ≥1.12.0")