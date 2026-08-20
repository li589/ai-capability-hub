#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""多源数据采集基类与聚合器 (v6.0 新增)

设计：
- DataSource 基类：每个源子类化，按能力实现 fetch_* 方法（未实现的返回 unavailable）。
- SourceResponse：统一返回结构，带 source/available/data/error/fetched_at。
- MultiSourceProvider：聚合多源，按数据类型分发到支持它的源，合并+去重+provenance。
- 逐源 try/except，任一源失败不影响其余，source_status 标注可用性。

数据类型：
  macro      - 宏观经济数据
  fund_ratings - 基金评级（多源聚合）
  fund_nav   - 基金净值
  fund_holdings - 基金持仓
  fund_holder_structure - 持有人结构
  manager_attribution - 经理能力归因
  news       - 新闻电报
  index      - 指数成分/收益
"""
from __future__ import annotations

import sys
import json
import time
import threading
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

# 接入 fund_advisor_paths
_SCRIPTS = Path(__file__).resolve().parents[2]  # scripts/
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))
try:
    from fund_advisor_paths import DATA_DIR  # noqa: E402
except Exception:
    DATA_DIR = Path(__file__).resolve().parents[4] / "data"


@dataclass
class SourceResponse:
    """单源响应"""
    source: str             # 源名（如 "akshare"/"晨星中国"）
    available: bool         # 是否成功获取
    data: Any = None        # 数据载荷
    error: str = ""         # 失败原因
    fetched_at: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    @classmethod
    def ok(cls, source: str, data: Any) -> "SourceResponse":
        return cls(source=source, available=True, data=data)

    @classmethod
    def fail(cls, source: str, error: str) -> "SourceResponse":
        return cls(source=source, available=False, error=error)


class DataSource:
    """数据源基类。子类按能力覆盖 fetch_* 方法。"""

    name: str = "base"
    capabilities: List[str] = []  # ["macro","fund_ratings","fund_nav",...]

    def fetch_macro(self) -> SourceResponse:
        return SourceResponse.fail(self.name, "不支持宏观数据")

    def fetch_fund_ratings(self, code: str) -> SourceResponse:
        return SourceResponse.fail(self.name, "不支持基金评级")

    def fetch_fund_nav(self, code: str) -> SourceResponse:
        return SourceResponse.fail(self.name, "不支持基金净值")

    def fetch_fund_holdings(self, code: str) -> SourceResponse:
        return SourceResponse.fail(self.name, "不支持基金持仓")

    def fetch_fund_holder_structure(self, code: str) -> SourceResponse:
        return SourceResponse.fail(self.name, "不支持持有人结构")

    def fetch_manager_attribution(self, manager_name: str) -> SourceResponse:
        return SourceResponse.fail(self.name, "不支持经理归因")

    def fetch_news(self, limit: int = 20) -> SourceResponse:
        return SourceResponse.fail(self.name, "不支持新闻")

    def fetch_index(self, index_code: str) -> SourceResponse:
        return SourceResponse.fail(self.name, "不支持指数")


class MultiSourceProvider:
    """多源聚合器"""

    def __init__(self):
        self._sources: List[DataSource] = []
        self._cache: Dict[str, tuple] = {}  # (key, (ts, value))
        self._cache_ttl = 300  # 5 分钟
        self._lock = threading.Lock()
        self._register_defaults()

    def _register_defaults(self):
        """注册默认数据源（按优先级）。每个源独立 try，缺失依赖不阻断。"""
        # akshare 是核心源（宏观数据/净值/持仓/指数）
        try:
            from .akshare_provider import AkshareProvider
            self._sources.append(AkshareProvider())
        except Exception:
            pass
        # 财联社电报
        try:
            from .cls_provider import ClsProvider
            self._sources.append(ClsProvider())
        except Exception:
            pass
        # 华尔街见闻
        try:
            from .wallstreetcn_provider import WallstreetcnProvider
            self._sources.append(WallstreetcnProvider())
        except Exception:
            pass
        # Phase 2 源（显式导入，缺失/解析失败不阻断）
        try:
            from .csindex_provider import CsindexProvider
            self._sources.append(CsindexProvider())
        except Exception:
            pass
        try:
            from .morningstar_provider import MorningstarProvider
            self._sources.append(MorningstarProvider())
        except Exception:
            pass
        try:
            from .howbuy_provider import HowbuyProvider
            self._sources.append(HowbuyProvider())
        except Exception:
            pass
        try:
            from .jiucaiban_provider import JiucaibanProvider
            self._sources.append(JiucaibanProvider())
        except Exception:
            pass
        try:
            from .danjuan_provider import DanjuanProvider
            self._sources.append(DanjuanProvider())
        except Exception:
            pass
        try:
            from .eastmoney_v2_provider import EastmoneyV2Provider
            self._sources.append(EastmoneyV2Provider())
        except Exception:
            pass
        # v8.0: Tushare 可选增强源
        try:
            from .tushare_provider import TushareProvider
            self._sources.append(TushareProvider())
        except Exception:
            pass

    def list_sources(self) -> List[Dict]:
        """列出已注册源及其能力"""
        return [{"name": s.name, "capabilities": s.capabilities} for s in self._sources]

    def _cached(self, key: str):
        with self._lock:
            if key in self._cache:
                ts, val = self._cache[key]
                if time.time() - ts < self._cache_ttl:
                    return val
        return None

    def _set_cache(self, key: str, val):
        with self._lock:
            self._cache[key] = (time.time(), val)

    # ─── 聚合接口 ──────────────────────────────────────────
    def get_macro(self) -> Dict:
        """聚合宏观数据（多源互补）"""
        cache_key = "macro"
        cached = self._cached(cache_key)
        if cached:
            return cached
        responses = []
        for s in self._sources:
            if "macro" in s.capabilities:
                try:
                    r = s.fetch_macro()
                    responses.append(r)
                except Exception as e:
                    responses.append(SourceResponse.fail(s.name, str(e)))
        result = self._merge_macro(responses)
        self._set_cache(cache_key, result)
        return result

    def get_fund_ratings(self, code: str) -> Dict:
        """聚合多源基金评级"""
        cache_key = f"ratings:{code}"
        cached = self._cached(cache_key)
        if cached:
            return cached
        responses = []
        for s in self._sources:
            if "fund_ratings" in s.capabilities:
                try:
                    responses.append(s.fetch_fund_ratings(code))
                except Exception as e:
                    responses.append(SourceResponse.fail(s.name, str(e)))
        result = self._merge_ratings(code, responses)
        self._set_cache(cache_key, result)
        return result

    def get_fund_nav(self, code: str) -> Dict:
        """获取基金净值（首个可用源）"""
        for s in self._sources:
            if "fund_nav" in s.capabilities:
                try:
                    r = s.fetch_fund_nav(code)
                    if r.available:
                        return {"code": code, "source": r.source, "nav": r.data,
                                "fetched_at": r.fetched_at}
                except Exception:
                    continue
        return {"code": code, "error": "所有净值源不可用", "source": "none"}

    def get_news(self, limit: int = 20) -> Dict:
        """聚合多源新闻"""
        cache_key = f"news:{limit}"
        cached = self._cached(cache_key)
        if cached:
            return cached
        all_news = []
        source_status = {}
        for s in self._sources:
            if "news" in s.capabilities:
                try:
                    r = s.fetch_news(limit=limit)
                    source_status[s.name] = "ok" if r.available else "fail"
                    if r.available and isinstance(r.data, list):
                        for item in r.data:
                            item.setdefault("source", s.name)
                            all_news.append(item)
                except Exception:
                    source_status[s.name] = "error"
        # 去重（按标题）
        seen = set()
        deduped = []
        for n in all_news:
            t = n.get("title", "")
            if t and t not in seen:
                seen.add(t)
                deduped.append(n)
        deduped.sort(key=lambda x: x.get("time", ""), reverse=True)
        result = {"news": deduped[:limit], "source_status": source_status,
                  "fetched_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        self._set_cache(cache_key, result)
        return result

    def get_fund_detail(self, code: str) -> Dict:
        """聚合基金全维度数据（评级+净值+持仓+持有人结构）"""
        detail = {"code": code, "fetched_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        detail["ratings"] = self.get_fund_ratings(code)
        detail["nav"] = self.get_fund_nav(code)
        # 持仓/持有人结构：找首个可用源
        for cap, key in [("fund_holdings", "holdings"),
                         ("fund_holder_structure", "holder_structure")]:
            for s in self._sources:
                if cap in s.capabilities:
                    try:
                        method = getattr(s, f"fetch_{cap}")
                        r = method(code)
                        if r.available:
                            detail[key] = {"source": r.source, "data": r.data}
                            break
                    except Exception:
                        continue
            if key not in detail:
                detail[key] = {"source": "none", "data": None}
        return detail

    # ─── 合并逻辑 ──────────────────────────────────────────
    def _merge_macro(self, responses: List[SourceResponse]) -> Dict:
        """合并宏观数据：多源互补，每指标取首个可用"""
        merged = {}
        source_status = {}
        for r in responses:
            source_status[r.source] = "ok" if r.available else "fail"
            if r.available and isinstance(r.data, dict):
                for k, v in r.data.items():
                    if k not in merged and v is not None:
                        merged[k] = {"value": v, "source": r.source}
        return {"indicators": merged, "source_status": source_status,
                "fetched_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

    def _merge_ratings(self, code: str, responses: List[SourceResponse]) -> Dict:
        """合并多源评级：每源评级+加权一致评级"""
        ratings = {}
        source_status = {}
        for r in responses:
            source_status[r.source] = "ok" if r.available else "fail"
            if r.available and r.data:
                ratings[r.source] = r.data
        # 计算加权一致评级（星级归一到 1-5）
        scores = []
        for src, data in ratings.items():
            star = self._extract_star(data)
            if star:
                scores.append(star)
        consensus = round(sum(scores) / len(scores), 2) if scores else None
        return {"code": code, "ratings": ratings, "consensus_star": consensus,
                "source_count": len(scores), "source_status": source_status,
                "fetched_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

    @staticmethod
    def _extract_star(data: Any) -> Optional[float]:
        """从评级数据提取星级(1-5)"""
        if isinstance(data, dict):
            for key in ("star", "stars", "rating", "morningstar_star", "howbuy_rating"):
                v = data.get(key)
                if isinstance(v, (int, float)) and 0 < v <= 5:
                    return float(v)
        return None


# 模块级单例
_provider_instance: Optional[MultiSourceProvider] = None
_provider_lock = threading.Lock()


def get_provider() -> MultiSourceProvider:
    """获取多源聚合器单例"""
    global _provider_instance
    if _provider_instance is None:
        with _provider_lock:
            if _provider_instance is None:
                _provider_instance = MultiSourceProvider()
    return _provider_instance
