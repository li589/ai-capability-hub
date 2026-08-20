# -*- coding: utf-8 -*-
"""
全网舆情爬虫引擎 v4.3
================================
根据用户对话要求，从权威媒体 / 财经垂直 / 地方媒体 / 自媒体 / 国际媒体
采集 基金公司/上市公司/证券公司/银行/保险/信托 等机构的正面新闻与舆情。

核心能力：
  - 5大媒体源，30+ 站点（数据驱动，可扩展）
  - 4类目标机构（基于现有注册表 + 政府清单）
  - 情感关键词分类（正面 vs 舆情，3档严重等级）
  - URL + 标题双维去重
  - 浏览器自动化兜底（v4.2 browser_scraper）
  - JSON 快照存储 / 增量追加 / 时间窗过滤
  - 定时任务支持（与 v4.0 crawl_scheduler 协同）

设计要点：
  - 无侵入：复用现有 scraper/batch_institution_crawler/cls_scraper/wallstreetcn_scraper
  - 离线优先：断网或目标站反爬时仍能返回已缓存数据
  - 输出标准化：导出器 sentiment_exporter.py 提供 Word/Excel/Dialog 三种反馈
"""
from __future__ import annotations

import re
import json
import time
import hashlib
import logging
import threading
from pathlib import Path
from typing import Dict, Any, List, Optional, Iterable, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from collections import defaultdict

# ============= 可选依赖（容错导入） =============
try:
    from .sentiment_keywords import (
        POSITIVE_KEYWORDS, NEGATIVE_KEYWORDS, NEUTRAL_KEYWORDS,
        SEVERITY_LEVELS, SEVERITY_LEVELS_POSITIVE,
        INDUSTRY_BUZZWORDS, RISK_PATTERNS,
    )
except ImportError:
    from sentiment_keywords import (  # type: ignore
        POSITIVE_KEYWORDS, NEGATIVE_KEYWORDS, NEUTRAL_KEYWORDS,
        SEVERITY_LEVELS, SEVERITY_LEVELS_POSITIVE,
        INDUSTRY_BUZZWORDS, RISK_PATTERNS,
    )

try:
    from scraper import FinancialPageScraper  # type: ignore
    HAS_BASE_SCRAPER = True
except ImportError:
    HAS_BASE_SCRAPER = False

try:
    from cls_scraper import get_hot_articles as cls_hot, search_articles as cls_search  # type: ignore
    from wallstreetcn_scraper import get_live_news as wscn_live, get_articles as wscn_articles  # type: ignore
    HAS_NEWS_API = True
except ImportError:
    HAS_NEWS_API = False
    cls_hot = cls_search = wscn_live = wscn_articles = None

try:
    from announcement_scraper import AnnouncementSearcher  # type: ignore
    HAS_ANN = True
except ImportError:
    HAS_ANN = False

try:
    from rss_feeds import RssFetcher  # type: ignore
    HAS_RSS = True
except ImportError:
    HAS_RSS = False
    RssFetcher = None  # type: ignore

# ============= 路径 & 全局配置 =============

SKILL_DATA_DIR = Path(__file__).resolve().parent.parent / "data"
SNAPSHOT_DIR = SKILL_DATA_DIR / "sentiment_snapshots"
SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
SOURCES_FILE = SKILL_DATA_DIR / "sentiment_sources.json"
TARGETS_FILE = SKILL_DATA_DIR / "sentiment_targets.json"
USER_CUSTOM_FILE = SKILL_DATA_DIR / "sentiment_custom_targets.json"

# 简易内存去重索引（key: fingerprint -> first_seen）
_SEEN_INDEX: Dict[str, str] = {}
_SEEN_INDEX_FILE = SNAPSHOT_DIR / "_seen_index.json"
if _SEEN_INDEX_FILE.exists():
    try:
        _SEEN_INDEX = json.loads(_SEEN_INDEX_FILE.read_text(encoding="utf-8"))
    except Exception:
        _SEEN_INDEX = {}

# v5.0.0: 模糊去重索引（会话内）— target_name -> [已见归一化标题列表]
# 精确指纹未命中时，用 difflib 标题相似度 >0.85 判定重复（防标题加标点/日期刷重复）
_TITLE_INDEX: Dict[str, List[str]] = {}

# v5.0.0: 并发安全 — _SEEN_INDEX / _TITLE_INDEX 共享锁（parallel_workers 并发写防撕裂）
_SEEN_LOCK = threading.Lock()

logger = logging.getLogger("sentiment_crawler")
logger.setLevel(logging.INFO)


# ============================================================
# 1. 数据模型
# ============================================================

@dataclass
class SentimentArticle:
    """舆情文章 — 全网舆情爬虫标准数据格式"""
    title: str                                  # 标题（必填）
    summary: str = ""                           # 内容简介（200-300字）
    content: str = ""                           # 全文（可空）
    source: str = ""                            # 发布平台/媒体名
    source_type: str = ""                       # 媒体类型（authoritative/financial_vertical/self_media...）
    target_name: str = ""                       # 涉及的目标（基金/公司/政府）
    target_type: str = ""                       # 目标类型
    publish_time: str = ""                      # 发布时间（原文，YYYY-MM-DD HH:MM:SS）
    url: str = ""                               # 页面连接
    sentiment: str = "neutral"                  # positive / negative / neutral
    sentiment_score: float = 0.0                # 情感分数
    severity: str = "中性"                      # 严重等级：中性/低度关注/中度舆情/高危舆情
    category: str = ""                          # sub_category: 业绩/处罚/诉讼...
    keywords_matched: List[str] = field(default_factory=list)  # 命中的关键词
    fetch_time: str = ""                        # 爬取时间
    dedup_ratio: float = 0.0                    # v5.0.0 模糊去重相似度（>0.85 视为重复）
    extra: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @property
    def fingerprint(self) -> str:
        """生成去重指纹 — URL + 标题归一化"""
        url_norm = (self.url or "").split("?")[0].rstrip("/").lower()
        title_norm = re.sub(r"\s+", "", self.title or "").lower()
        raw = f"{url_norm}::{title_norm}::{self.target_name}"
        return hashlib.md5(raw.encode("utf-8")).hexdigest()


@dataclass
class SentimentSnapshot:
    """一次舆情快照（爬取+分类的完整结果集）"""
    snapshot_id: str
    created_at: str
    target_filter: Dict[str, Any]
    source_filter: List[str]
    articles: List[SentimentArticle] = field(default_factory=list)
    stats: Dict[str, Any] = field(default_factory=dict)
    plan: Optional[Dict[str, Any]] = None  # v4.5 dry_run 时填充
    backtest_results: Optional[List[Any]] = None  # v4.5 run_backtest=True 时填充

    def to_dict(self) -> Dict[str, Any]:
        return {
            "snapshot_id": self.snapshot_id,
            "created_at": self.created_at,
            "target_filter": self.target_filter,
            "source_filter": self.source_filter,
            "articles": [a.to_dict() for a in self.articles],
            "stats": self.stats,
            "plan": self.plan,
            "backtest_results": (
                [r.to_dict() if hasattr(r, "to_dict") else r
                 for r in (self.backtest_results or [])]
                if self.backtest_results else None
            ),
        }

    @property
    def is_plan(self) -> bool:
        """v4.5: 是否是 plan 模式（dry_run 或未确认）。"""
        return bool(self.plan) or self.stats.get("dry_run", False)

    @property
    def is_awaiting_confirmation(self) -> bool:
        """v4.5: 是否在等待用户确认。"""
        return self.stats.get("awaiting_confirmation", False)

    def positive_count(self) -> int:
        return sum(1 for a in self.articles if a.sentiment == "positive")

    def negative_count(self) -> int:
        return sum(1 for a in self.articles if a.sentiment == "negative")

    def neutral_count(self) -> int:
        return sum(1 for a in self.articles if a.sentiment == "neutral")


# ============================================================
# 2. 情感分类（关键词驱动，无外部 AI 依赖）
# ============================================================

class SentimentClassifier:
    """轻量情感分类器 — 基于关键词权重"""

    def __init__(self,
                 pos_dict: Optional[Dict[str, int]] = None,
                 neg_dict: Optional[Dict[str, int]] = None,
                 neu_dict: Optional[Dict[str, int]] = None):
        self.pos_dict = pos_dict or POSITIVE_KEYWORDS
        self.neg_dict = neg_dict or NEGATIVE_KEYWORDS
        self.neu_dict = neu_dict or NEUTRAL_KEYWORDS

    def classify(self, title: str, content: str = "") -> Tuple[str, float, List[str], str]:
        """返回 (sentiment, score, matched_keywords, severity)"""
        # 标题权重 × 2 / 命中次数 / 长度
        text = (title or "") + "。" + (content or "")[:1500]
        title_text = title or ""

        pos_score, pos_hits = self._score(title_text, text, self.pos_dict)
        neg_score, neg_hits = self._score(title_text, text, self.neg_dict)
        neu_score, neu_hits = self._score(title_text, text, self.neu_dict)

        # 类型判定
        if neg_score > pos_score and neg_score >= 5:
            sentiment = "negative"
            score = neg_score
            matched = neg_hits
        elif pos_score > neg_score and pos_score >= 5:
            sentiment = "positive"
            score = pos_score
            matched = pos_hits
        elif neu_score >= 5:
            sentiment = "neutral"
            score = neu_score
            matched = neu_hits
        else:
            sentiment = "neutral"
            score = max(pos_score, neg_score, neu_score)
            matched = pos_hits + neg_hits + neu_hits

        severity = self._severity(score, sentiment)
        return sentiment, float(score), matched, severity

    # 通用否定词（前向窗口检测：「公司否认业绩下滑」中 '否认' 在关键词前）
    NEGATION_WORDS = (
        "不", "无", "未", "没有", "并非", "否认", "辟谣", "澄清", "不实",
        "虚假", "谣言", "难", "并非", "不是", "未能",
    )
    # 声明类否定词（后向窗口检测：「业绩下滑，但公司否认」中 '否认' 在关键词后）
    DECLARATION_NEGATIONS = ("否认", "澄清", "辟谣", "不实", "虚假", "谣言")

    def _negated(self, text: str, word: str) -> bool:
        """v5.0.0: 否定词窗口检测 — 关键词前 4 字内的通用否定，或词后 10 字内的声明类否定。

        例：「公司否认业绩下滑」→ '下滑' 前有 '否认' → 翻转。
             「业绩下滑，但公司否认该说法」→ '下滑' 后有 '否认' → 翻转。
        """
        for m in re.finditer(re.escape(word), text):
            start = m.start()
            pre = text[max(0, start - 4):start]
            if any(neg in pre for neg in self.NEGATION_WORDS):
                return True
            post = text[start:start + len(word) + 10]
            if any(neg in post for neg in self.DECLARATION_NEGATIONS):
                return True
        return False

    def _score(self, title: str, full_text: str, dictionary: Dict[str, int]) -> Tuple[float, List[str]]:
        score = 0.0
        hits: List[str] = []
        for word, weight in dictionary.items():
            t_hit = title.count(word)
            f_hit = full_text.count(word)
            if not (t_hit or f_hit):
                continue
            # v5.0.0: 否定词处理 — 「否认/未/没有」等使关键词命中不累计分。
            # full_text 已含 title，故统一在 full_text 上做窗口否定检测。
            if self._negated(full_text, word):
                continue
            hits.append(word)
            # 标题命中 × 2，内容命中 × 1
            score += weight * (t_hit * 2 + f_hit)
        return score, hits

    def _severity(self, score: float, sentiment: str) -> str:
        """根据分数和情感返回严重等级。
        v5.0.0: 阈值统一读取 sentiment_keywords.SEVERITY_LEVELS / SEVERITY_LEVELS_POSITIVE，
        消除此前的硬编码 6/12/25、6/15/30 两套不一致数值。
        """
        if sentiment == "neutral":
            return "中性"
        table = SEVERITY_LEVELS_POSITIVE if sentiment == "positive" else SEVERITY_LEVELS
        for lo, hi, label in table:
            if lo <= score < hi:
                return label
        return table[-1][2]  # 超出上限归最高档


# ============================================================
# 3. 媒体源 & 目标库 加载
# ============================================================

class SentimentSourceLoader:
    """加载 + 检索 媒体源库"""

    def __init__(self, file_path: Path = SOURCES_FILE):
        self.file_path = Path(file_path)
        self._data: Dict[str, List[Dict[str, Any]]] = {}
        self.reload()

    def reload(self):
        if not self.file_path.exists():
            logger.warning("媒体源文件不存在: %s", self.file_path)
            self._data = {}
            return
        try:
            raw = json.loads(self.file_path.read_text(encoding="utf-8"))
            self._data = {k: v for k, v in raw.items() if not k.startswith("_")}
        except Exception as e:
            logger.warning("媒体源文件解析失败: %s", e)
            self._data = {}

    def list_categories(self) -> List[str]:
        return list(self._data.keys())

    def all_sources(self) -> List[Dict[str, Any]]:
        out = []
        for cat, items in self._data.items():
            for item in items:
                rec = dict(item)
                rec["category"] = cat
                out.append(rec)
        return out

    def sources_by_category(self, category: str) -> List[Dict[str, Any]]:
        return self._data.get(category, [])

    def sources_with_rss(self) -> List[Dict[str, Any]]:
        """v5.0.0: 已配置 rss_feeds 的站点（可直接 RSS 直连，零反爬）。"""
        return [s for s in self.all_sources() if s.get("rss_feeds")]

    def pick_by_names(self, names: List[str]) -> List[Dict[str, Any]]:
        """按名称选取媒体源（精确匹配）"""
        pick = []
        for cat, items in self._data.items():
            for item in items:
                if item.get("name") in names:
                    rec = dict(item); rec["category"] = cat
                    pick.append(rec)
        return pick

    def stats(self) -> Dict[str, int]:
        return {cat: len(items) for cat, items in self._data.items()}


class SentimentTargetLoader:
    """加载目标机构库 — 优先使用 sentiment_targets.json，
    并尝试从已有注册表补全"""

    def __init__(self, file_path: Path = TARGETS_FILE):
        self.file_path = Path(file_path)
        self.user_custom = self._load_user_custom()
        self.reload()

    def _load_user_custom(self) -> Dict[str, List[Dict[str, Any]]]:
        if USER_CUSTOM_FILE.exists():
            try:
                return json.loads(USER_CUSTOM_FILE.read_text(encoding="utf-8"))
            except Exception:
                return {}
        return {}

    def reload(self):
        if not self.file_path.exists():
            logger.warning("目标文件不存在: %s", self.file_path)
            self._data: Dict[str, Any] = {}
            return
        try:
            raw = json.loads(self.file_path.read_text(encoding="utf-8"))
            self._data = {k: v for k, v in raw.items() if not k.startswith("_")}
        except Exception as e:
            logger.warning("目标文件解析失败: %s", e)
            self._data = {}

    @property
    def categories(self) -> List[str]:
        return list(self._data.keys())

    def get(self, category: str) -> Dict[str, Any]:
        return self._data.get(category, {})

    def all_targets(self) -> List[Tuple[str, str]]:
        """返回 [(category, target_name), ...] 用户 + 系统"""
        result: List[Tuple[str, str]] = []
        for cat, info in self._data.items():
            label = info.get("label", cat)
            # 优先取 items（精确实例），否则视为类别名
            for item in info.get("items", []) or []:
                name = item.get("name") if isinstance(item, dict) else str(item)
                if name:
                    result.append((cat, label, name))
            # 用户自定义补全
            for item in self.user_custom.get(cat, []):
                name = item.get("name") if isinstance(item, dict) else str(item)
                if name:
                    result.append((cat, label, name))
        return result

    def add_custom_target(self, category: str, name: str,
                          aliases: Optional[List[str]] = None,
                          tags: Optional[List[str]] = None) -> Dict[str, Any]:
        """动态增加自定义目标"""
        bucket = self.user_custom.setdefault(category, [])
        for it in bucket:
            if it.get("name") == name:
                return {"ok": False, "msg": f"已存在: {name}"}
        item = {"name": name, "aliases": aliases or [], "tags": tags or []}
        bucket.append(item)
        USER_CUSTOM_FILE.parent.mkdir(parents=True, exist_ok=True)
        USER_CUSTOM_FILE.write_text(
            json.dumps(self.user_custom, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        return {"ok": True, "added": item}

    def stats(self) -> Dict[str, int]:
        return {cat: len(info.get("items", []) or []) for cat, info in self._data.items()}


# ============================================================
# 4. 爬取核心 — 针对每个目标 × 媒体源 生成查询
# ============================================================

class SentimentCrawler:
    """全网舆情爬虫统一入口"""

    def __init__(self,
                 sources: Optional[SentimentSourceLoader] = None,
                 targets: Optional[SentimentTargetLoader] = None,
                 classifier: Optional[SentimentClassifier] = None,
                 enable_browser_fallback: bool = True,
                 snapshot_dir: Optional[Path] = None,
                 article_limit: int = 60,
                 max_total_seconds: int = 60,
                 per_source_timeout: int = 8,
                 use_rss: bool = True,
                 rss_fetcher: Optional[Any] = None):
        self.sources = sources or SentimentSourceLoader()
        self.targets = targets or SentimentTargetLoader()
        self.classifier = classifier or SentimentClassifier()
        self.enable_browser_fallback = enable_browser_fallback
        self.snapshot_dir = Path(snapshot_dir or SNAPSHOT_DIR)
        self.snapshot_dir.mkdir(parents=True, exist_ok=True)
        self.article_limit = article_limit
        # 速度控制：全局最大耗时 + 单源超时
        self.max_total_seconds = max_total_seconds
        self.per_source_timeout = per_source_timeout
        self._run_start_ts: float = 0.0
        # v5.0.0: RSS 直连数据源（零反爬；缺依赖时为 None 自动禁用）
        self.use_rss = use_rss
        self._rss_fetcher = rss_fetcher
        if self._rss_fetcher is None and HAS_RSS and RssFetcher is not None:
            self._rss_fetcher = RssFetcher()
        # v5.0.0: 协作式取消集合 + 占位缓存锁（并发安全）
        self._cancelled_sources: set = set()
        self._placeholder_lock = threading.Lock()
        # 占位记录去重：同一 (target_name, source_name) 在 1 小时内只生成一次
        self._placeholder_cache: Dict[Tuple[str, str], float] = {}
        self._placeholder_ttl = 3600  # 秒

    # ---------------- 顶层 API -----------------

    def crawl(self,
              target_names: Optional[List[str]] = None,
              target_categories: Optional[List[str]] = None,
              source_categories: Optional[List[str]] = None,
              source_names: Optional[List[str]] = None,
              days: int = 7,
              positive_only: bool = False,
              negative_only: bool = False,
              max_articles: int = 80,
              dry_run: bool = False,
              confirmed: bool = True,
              run_backtest: bool = False,
              backtest_drop: Optional[Tuple[str, ...]] = None,
              parallel_workers: int = 0) -> SentimentSnapshot:
        """执行一次全网舆情爬取。
        参数:
            target_names: 指定的目标名列表，例如 ["贵州茅台","工银瑞信基金"]
            target_categories: 限定目标类别，例如 ["fund_company","listed_company"]
            source_categories: 限定媒体类别，例如 ["authoritative","financial_vertical"]
            source_names: 限定具体媒体名
            days: 时间窗口（默认7天）
            positive_only / negative_only: 只保留某类情感
            max_articles: 最大结果条数
            dry_run: 仅返回爬取计划（不发任何 HTTP 请求），用于"先 plan 再确认"流程
            confirmed: 是否已确认（默认 True）。当 False 时也走 dry_run 逻辑
            run_backtest: 是否对每篇文章做 4 维回测（慢 ~20%）
            backtest_drop: 回测后丢弃的推荐等级元组（如 ("建议丢弃",)），仅 run_backtest=True 时生效
            parallel_workers: 并发抓取的线程数（0=按 v4.5 顺序，>0=按指定 worker 并发 target×source）

        速度控制:
            max_total_seconds: 整个爬取最大耗时（默认 60s），超时立即返回已有结果
            per_source_timeout: 单个媒体源超时（默认 8s）
            parallel_workers: 并发 (target, source) 抓取的线程数（v4.5.1 新增，默认 0=顺序）
        """
        import time as _time
        self._run_start_ts = _time.time()

        # v4.5: dry_run / 未确认 → 只返回计划
        if dry_run or not confirmed:
            return self._build_plan_only(
                target_names=target_names,
                target_categories=target_categories,
                source_categories=source_categories,
                source_names=source_names,
                days=days,
                max_articles=max_articles,
                awaiting_confirmation=not confirmed,
            )

        # 1. 选定媒体源
        if source_names:
            chosen_sources = self.sources.pick_by_names(source_names)
        elif source_categories:
            chosen_sources = []
            for cat in source_categories:
                chosen_sources.extend(self.sources.sources_by_category(cat))
        else:
            chosen_sources = self.sources.all_sources()

        # 2. 选定目标
        if target_names:
            target_list = []
            for cat, label, name in self.targets.all_targets():
                if name in target_names:
                    target_list.append((cat, label, name))
            # 加进用户输入但未在库中的目标
            for n in target_names:
                if not any(t[2] == n for t in target_list):
                    target_list.append(("custom", "自定义目标", n))
        elif target_categories:
            target_list = [(c, l, n) for c, l, n in self.targets.all_targets() if c in target_categories]
        else:
            # 默认：top 类别
            target_list = [(c, l, n) for c, l, n in self.targets.all_targets()
                           if c in ("fund_company", "listed_company")]
            target_list = target_list[:8]

        logger.info(
            "🛰️ 开始全网舆情爬取 | 媒体源=%d 目标=%d 时间窗=%d天 限时=%ds",
            len(chosen_sources), len(target_list), days, self.max_total_seconds,
        )

        articles: List[SentimentArticle] = []
        cutoff_time = datetime.now() - timedelta(days=days)

        # 3. 遍历目标 — 加全局超时检查
        # v4.5.1: 支持 parallel_workers 并发 (target, source) 抓取
        if parallel_workers and parallel_workers > 0:
            articles = self._crawl_parallel(
                target_list=target_list,
                chosen_sources=chosen_sources,
                cutoff_time=cutoff_time,
                max_articles=max_articles,
                max_workers=parallel_workers,
            )
        else:
            for cat, label, name in target_list:
                if self._time_up():
                    logger.warning("⏰ 达到全局时限，停止新目标（已爬取 %d 条）", len(articles))
                    break
                try:
                    kw_list = self._build_keywords(cat, name)
                    for src in chosen_sources:
                        if self._time_up():
                            break
                        for kw in kw_list[:2]:  # 主关键词优先，无结果时再用备用关键词
                            if self._time_up():
                                break
                            for art in self._query_source(src, name, kw, cat, label, cutoff_time):
                                if not self._is_dup(art) and self._is_in_window(art, cutoff_time):
                                    articles.append(art)
                                    if len(articles) >= max_articles:
                                        break
                            if len(articles) >= max_articles:
                                break
                        if len(articles) >= max_articles:
                            break
                except Exception as e:
                    logger.warning("目标 %s 爬取出错: %s", name, e)
                    continue
                if len(articles) >= max_articles:
                    break

        # 4. 过滤 & 排序
        articles = self._post_filter(articles, positive_only, negative_only)
        articles.sort(key=lambda a: (a.publish_time or ""), reverse=True)

        # 4.5 日期核验统计
        date_validation = self._compute_date_validation(articles, cutoff_time, days)

        # 5. 包装成快照（含耗时统计）
        elapsed = _time.time() - self._run_start_ts
        snapshot = SentimentSnapshot(
            snapshot_id=f"sn_{datetime.now().strftime('%Y%m%d_%H%M%S')}_"
                       f"{hashlib.md5(str(target_list).encode()).hexdigest()[:6]}",
            created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            target_filter={"names": target_names or [], "categories": target_categories or []},
            source_filter=[s.get("name", "") for s in chosen_sources],
            articles=articles[:max_articles],
            stats={
                "total": len(articles[:max_articles]),
                "sources_used": len(chosen_sources),
                "targets_used": len(target_list),
                "days_window": days,
                "elapsed_seconds": round(elapsed, 2),
                "timed_out": self._time_up(),
                "by_sentiment": {
                    "positive": sum(1 for a in articles if a.sentiment == "positive"),
                    "negative": sum(1 for a in articles if a.sentiment == "negative"),
                    "neutral": sum(1 for a in articles if a.sentiment == "neutral"),
                },
                "by_severity": dict(_count_by(articles, lambda a: a.severity)),
                "by_source_type": dict(_count_by(articles, lambda a: a.source_type)),
                "date_validation": date_validation,
            },
        )

        # v4.5: 跑 4 维回测（可选）
        if run_backtest and articles:
            snapshot.articles, snapshot.backtest_results = self._run_backtest(
                articles, drop_recommendation=backtest_drop,
            )

        self._save_snapshot(snapshot)
        return snapshot

    def _build_plan_only(self,
                         target_names: Optional[List[str]] = None,
                         target_categories: Optional[List[str]] = None,
                         source_categories: Optional[List[str]] = None,
                         source_names: Optional[List[str]] = None,
                         days: int = 7,
                         max_articles: int = 80,
                         awaiting_confirmation: bool = False) -> SentimentSnapshot:
        """v4.5.1: 仅构建爬取计划，不发任何 HTTP 请求。

        v4.5.1 强化:
          - 输入校验 (validation_errors)
          - 缓存样本预览 (从最近一次历史快照取 1-3 条样本)
          - 风险提示 (risk_warnings) — 命中敏感词、目标名异常、源数过多
          - 覆盖率估算 (coverage_estimate) — 基于历史快照命中率
        """
        # ---- 输入校验 ----
        validation_errors: List[str] = []
        risk_warnings: List[str] = []
        if days <= 0 or days > 90:
            validation_errors.append(f"days 参数非法: {days}（应在 1-90 之间）")
        if max_articles <= 0 or max_articles > 500:
            validation_errors.append(f"max_articles 参数非法: {max_articles}（应在 1-500 之间）")
        if target_names:
            for n in target_names:
                if not n or not n.strip():
                    validation_errors.append("目标名不能为空")
                elif len(n.strip()) < 2:
                    risk_warnings.append(f"目标名过短: «{n}»（可能匹配范围过宽）")
                elif len(n.strip()) > 30:
                    risk_warnings.append(f"目标名过长: «{n}»（建议用简称）")
                if any(bad in n for bad in ("测试", "test", "demo", "example")):
                    risk_warnings.append(f"目标名含测试占位词: «{n}»（建议使用真实机构名）")

        # 选定媒体源（同样逻辑）
        if source_names:
            chosen_sources = self.sources.pick_by_names(source_names)
        elif source_categories:
            chosen_sources = []
            for cat in source_categories:
                chosen_sources.extend(self.sources.sources_by_category(cat))
        else:
            chosen_sources = self.sources.all_sources()

        if not chosen_sources:
            validation_errors.append("没有可用的媒体源（检查 source_categories 或 sources 参数）")
        if len(chosen_sources) > 30:
            risk_warnings.append(f"媒体源过多 ({len(chosen_sources)})，单次爬取可能超时，建议 ≤ 20 个")

        # 选定目标
        if target_names:
            target_list = []
            for cat, label, name in self.targets.all_targets():
                if name in target_names:
                    target_list.append((cat, label, name))
            for n in target_names:
                if not any(t[2] == n for t in target_list):
                    target_list.append(("custom", "自定义目标", n))
        elif target_categories:
            target_list = [(c, l, n) for c, l, n in self.targets.all_targets()
                           if c in target_categories]
        else:
            target_list = [(c, l, n) for c, l, n in self.targets.all_targets()
                           if c in ("fund_company", "listed_company")][:8]

        if not target_list:
            validation_errors.append("没有匹配的目标（检查 target_names / target_categories）")
        if len(target_list) > 50:
            risk_warnings.append(f"目标过多 ({len(target_list)})，建议分批爬取")

        # 校验失败 → 直接返回错误 plan（不让用户带着错误参数确认）
        if validation_errors:
            plan = {
                "targets": [],
                "sources": [],
                "days": days,
                "max_articles": max_articles,
                "estimated_articles": 0,
                "estimated_seconds": 0.0,
                "awaiting_confirmation": awaiting_confirmation,
                "validation_errors": validation_errors,
                "risk_warnings": risk_warnings,
                "actions": [],
            }
            snapshot = SentimentSnapshot(
                snapshot_id=f"plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}_err",
                created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                target_filter={"names": target_names or [],
                               "categories": target_categories or []},
                source_filter=[],
                articles=[],
                stats={
                    "total": 0, "sources_used": 0, "targets_used": 0,
                    "days_window": days, "elapsed_seconds": 0.0,
                    "timed_out": False, "dry_run": True,
                    "awaiting_confirmation": False,
                    "validation_failed": True,
                },
            )
            snapshot.plan = plan
            return snapshot

        # 估算文章数（用历史快照命中率）
        estimated_articles = self._estimate_articles(len(target_list),
                                                     len(chosen_sources),
                                                     days, max_articles)

        # 估算耗时（每个源 ~1.5s + 每目标 ~0.5s，含分类）
        estimated_seconds = len(chosen_sources) * 1.5 + len(target_list) * 0.5
        estimated_seconds = min(estimated_seconds, self.max_total_seconds)

        # ---- 缓存样本预览：从最近一次历史快照找样本 ----
        sample_articles = self._sample_from_history(target_list, chosen_sources,
                                                    max_samples=3)

        # ---- 覆盖率估算 ----
        coverage_estimate = self._estimate_coverage(target_list, chosen_sources, days)

        plan = {
            "targets": [{"category": c, "label": l, "name": n}
                        for c, l, n in target_list],
            "sources": [{"name": s.get("name", ""),
                         "type": s.get("type", ""),
                         "credibility": s.get("credibility", 5)}
                        for s in chosen_sources],
            "days": days,
            "max_articles": max_articles,
            "estimated_articles": estimated_articles,
            "estimated_seconds": round(estimated_seconds, 1),
            "coverage_estimate": coverage_estimate,
            "awaiting_confirmation": awaiting_confirmation,
            "validation_errors": validation_errors,
            "risk_warnings": risk_warnings,
            "sample_articles": sample_articles,
            "actions": ["fetch", "classify", "backtest" if awaiting_confirmation else "fetch"],
        }

        # 返回一个特殊的 snapshot：articles=[] 但 plan 字段有内容
        snapshot = SentimentSnapshot(
            snapshot_id=f"plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}_"
                       f"{hashlib.md5(str(target_list).encode()).hexdigest()[:6]}",
            created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            target_filter={"names": target_names or [],
                           "categories": target_categories or []},
            source_filter=[s.get("name", "") for s in chosen_sources],
            articles=[],
            stats={
                "total": 0,
                "sources_used": len(chosen_sources),
                "targets_used": len(target_list),
                "days_window": days,
                "elapsed_seconds": 0.0,
                "timed_out": False,
                "dry_run": True,
                "awaiting_confirmation": awaiting_confirmation,
            },
        )
        # 把 plan 挂到 snapshot 上（兼容旧 API：articles=[] 也合法）
        snapshot.plan = plan
        return snapshot

    def _sample_from_history(self, target_list, chosen_sources,
                             max_samples: int = 3) -> List[Dict[str, Any]]:
        """从最近一次历史快照里挑样本，给用户预览。

        选最近一次非 plan 快照，按 target 名/源名匹配，挑最多 max_samples 条。
        """
        try:
            idx_path = self.snapshot_dir / "index.json"
            if not idx_path.exists():
                return []
            index = json.loads(idx_path.read_text(encoding="utf-8"))
            if not index:
                return []
            # 找最近一次非 plan 快照
            recent_id = None
            for entry in index:
                sid = entry.get("snapshot_id", "")
                if sid.startswith("plan_"):
                    continue
                recent_id = sid
                break
            if not recent_id:
                return []
            snap_file = self.snapshot_dir / f"{recent_id}.json"
            if not snap_file.exists():
                return []
            snap = json.loads(snap_file.read_text(encoding="utf-8"))
            target_set = {t[2] for t in target_list}
            source_set = {s.get("name", "") for s in chosen_sources}
            samples: List[Dict[str, Any]] = []
            for art in (snap.get("articles") or [])[:30]:
                if art.get("target_name") in target_set or art.get("source") in source_set:
                    samples.append({
                        "title": art.get("title", ""),
                        "source": art.get("source", ""),
                        "target_name": art.get("target_name", ""),
                        "publish_time": art.get("publish_time", ""),
                        "url": art.get("url", ""),
                        "sentiment": art.get("sentiment", ""),
                    })
                    if len(samples) >= max_samples:
                        break
            return samples
        except Exception:
            return []

    def _estimate_coverage(self, target_list, chosen_sources, days: int) -> Dict[str, Any]:
        """基于历史快照估算覆盖率（命中率）。

        返回:
            {
              "historical_snapshots": N,
              "historical_hit_rate": 0-1,
              "expected_avg_articles_per_target": float,
            }
        """
        try:
            idx_path = self.snapshot_dir / "index.json"
            if not idx_path.exists():
                return {"historical_snapshots": 0, "historical_hit_rate": 0.0,
                        "expected_avg_articles_per_target": 0.0}
            index = json.loads(idx_path.read_text(encoding="utf-8"))
            non_plan = [e for e in index if not e.get("snapshot_id", "").startswith("plan_")]
            if not non_plan:
                return {"historical_snapshots": 0, "historical_hit_rate": 0.0,
                        "expected_avg_articles_per_target": 0.0}
            total_articles = sum(e.get("total", 0) for e in non_plan[:20])
            avg_per_snap = total_articles / min(20, len(non_plan))
            hit_rate = min(1.0, avg_per_snap / max(1, len(target_list)))
            return {
                "historical_snapshots": len(non_plan),
                "historical_hit_rate": round(hit_rate, 3),
                "expected_avg_articles_per_target": round(avg_per_snap / max(1, len(target_list)), 2),
            }
        except Exception:
            return {"historical_snapshots": 0, "historical_hit_rate": 0.0,
                    "expected_avg_articles_per_target": 0.0}

    def _estimate_articles(self, n_targets: int, n_sources: int,
                           days: int, max_articles: int) -> int:
        """基于历史快照估算文章数。"""
        # 启发式：每 (target, source, day) 平均 1-3 篇
        base = n_targets * min(n_sources, 5) * max(1, days // 2)
        # 限制在 max_articles 之内
        return min(max(1, base), max_articles)

    def _crawl_parallel(self,
                          target_list: List[Tuple[str, str, str]],
                          chosen_sources: List[Dict[str, Any]],
                          cutoff_time: datetime,
                          max_articles: int,
                          max_workers: int = 4,
                          ) -> List[SentimentArticle]:
        """v4.5.1: 并发抓取所有 (target, source) 单元，结果合并去重。

        每个 (target, source) 单元用 _query_source 拉一个 generator，
        由线程池并发执行。遇到超时/异常不阻断其他单元。
        """
        from concurrent.futures import ThreadPoolExecutor, as_completed

        articles: List[SentimentArticle] = []
        seen_locks = set()  # 用 set 做 O(1) 去重辅助
        workers = max(1, min(max_workers, 8))  # 限制在 1-8

        # 构造任务列表：(target, source, kw)
        tasks: List[Tuple[str, str, str, str, str]] = []
        for cat, label, name in target_list:
            kw_list = self._build_keywords(cat, name)
            for src in chosen_sources:
                for kw in kw_list[:2]:
                    tasks.append((name, cat, label, src.get("name", ""), kw))

        if not tasks:
            return articles

        logger.info("🚀 并发爬取: %d 单元 / %d workers", len(tasks), workers)

        def _one(target_name: str, cat: str, label: str,
                 src_name: str, kw: str) -> List[SentimentArticle]:
            src = next((s for s in chosen_sources if s.get("name") == src_name), None)
            if not src:
                return []
            if self._time_up():
                return []
            collected: List[SentimentArticle] = []
            try:
                for art in self._query_source(src, target_name, kw, cat, label, cutoff_time):
                    if self._is_in_window(art, cutoff_time):
                        collected.append(art)
                    if self._time_up():
                        break
            except Exception as e:
                logger.debug("并发单元异常 (%s, %s): %s", target_name, src_name, e)
            return collected

        with ThreadPoolExecutor(max_workers=workers) as ex:
            futures = [ex.submit(_one, t[0], t[1], t[2], t[3], t[4]) for t in tasks]
            for fut in as_completed(futures):
                if self._time_up():
                    break
                try:
                    batch = fut.result(timeout=0.5) or []
                except Exception:
                    continue
                for art in batch:
                    if self._time_up() or len(articles) >= max_articles:
                        break
                    if not self._is_dup(art):
                        articles.append(art)
                        if len(articles) >= max_articles:
                            break

        logger.info("✅ 并发爬取完成: %d 条 (目标 %d × 源 %d)",
                    len(articles), len(target_list), len(chosen_sources))
        return articles

    def _run_backtest(self, articles: List["SentimentArticle"],
                       drop_recommendation: Optional[Tuple[str, ...]] = None,
                       ) -> tuple:
        """v4.5.1: 对文章列表跑 4 维回测，返回 (filtered_articles, results)。

        Args:
            articles: 待回测文章列表
            drop_recommendation: 哪些推荐等级要丢弃（默认 None=不丢，仅记录；
                                  "建议丢弃"=按推荐自动过滤）

        Returns:
            (articles, results) — articles 已按 drop_recommendation 过滤
        """
        try:
            from .crawl_backtester import (
                CrawlBacktester, filter_by_recommendation, batch_summary,
            )
            bt = CrawlBacktester(max_age_days=14)
            results = []
            for art in articles:
                ad = art.to_dict() if hasattr(art, "to_dict") else {
                    "title": art.title,
                    "url": art.url,
                    "published_at": art.publish_time,
                    "content": getattr(art, "content", ""),
                    "source": art.source,
                }
                results.append(bt.backtest(ad))

            # v4.5.1: 按推荐等级过滤
            if drop_recommendation:
                kept_articles, kept_results = filter_by_recommendation(
                    results, articles, drop_recommendation,
                )
                dropped = len(articles) - len(kept_articles)
                if dropped > 0:
                    logger.info("🛡️ 回测过滤: 丢弃 %d/%d 篇文章", dropped, len(articles))
                # 附带汇总统计到 results（最后一个元素是 summary）
                summary = batch_summary(kept_results)
                # 把 summary 写到 kept_results 的最后一个（如果有），否则单独加
                summary["_meta"] = "batch_summary"
                summary["_dropped_count"] = dropped
                return kept_articles, kept_results + [summary]
            return articles, results
        except Exception as e:
            logger.warning("数据回测失败，跳过: %s", e)
            return articles, []

    # ---------------- 时间控制 -----------------

    def _time_up(self) -> bool:
        import time as _time
        if self.max_total_seconds <= 0:
            return False
        return (_time.time() - self._run_start_ts) > self.max_total_seconds

    def _placeholder_seen(self, target_name: str, source_name: str) -> bool:
        """短时间窗口内，对同一 (target, source) 只生成一次占位记录（v5.0.0 加锁防并发竞态）。"""
        import time as _time
        key = (target_name, source_name)
        now = _time.time()
        with self._placeholder_lock:
            # 清理过期项
            self._placeholder_cache = {
                k: v for k, v in self._placeholder_cache.items()
                if now - v < self._placeholder_ttl
            }
            if key in self._placeholder_cache:
                return True
            self._placeholder_cache[key] = now
            return False

    def _domain_is_blocked(self, url: str) -> bool:
        """域名级短路：如果目标 URL 的域名已熔断，直接跳过，节省时间。"""
        try:
            from urllib.parse import urlparse
            domain = urlparse(url).netloc
            if not domain:
                return False
            # 检查 scraper 的熔断器
            try:
                from scraper import FinancialPageScraper
                scraper = FinancialPageScraper()
                if hasattr(scraper, "is_blocked") and scraper.is_blocked(domain):
                    logger.debug("⛔ 域名 %s 已熔断，跳过", domain)
                    return True
            except Exception:
                pass
            # 检查 http_utils 的熔断器
            try:
                from http_utils import SmartLimiter  # type: ignore
                limiter = getattr(SmartLimiter, "_instance", None) or SmartLimiter()
                if hasattr(limiter, "is_blocked") and limiter.is_blocked(domain):
                    logger.debug("⛔ 域名 %s 限流器熔断，跳过", domain)
                    return True
            except Exception:
                pass
            return False
        except Exception:
            return False

    # 域名 DNS 解析失败缓存 (1 小时内再尝试则 skip)
    _DNS_FAIL_CACHE: Dict[str, float] = {}
    _DNS_FAIL_TTL = 3600.0

    def _domain_unresolvable(self, url: str) -> bool:
        """探测 URL 的域名是否可解析；不可解析直接 skip。"""
        import time as _time
        try:
            from urllib.parse import urlparse
            import socket
            domain = urlparse(url).netloc
            if not domain:
                return False
            now = _time.time()
            # 清理过期项
            self._DNS_FAIL_CACHE = {
                k: v for k, v in self._DNS_FAIL_CACHE.items()
                if now - v < self._DNS_FAIL_TTL
            }
            if domain in self._DNS_FAIL_CACHE:
                return True
            try:
                socket.gethostbyname(domain)
                return False
            except (socket.gaierror, OSError):
                # 不可解析 - 缓存 + 短路
                self._DNS_FAIL_CACHE[domain] = now
                logger.debug("⛔ 域名 %s 无法解析，跳过", domain)
                return True
        except Exception:
            return False

    # ---------------- 关键词构建 -----------------

    def _build_keywords(self, category: str, target_name: str) -> List[str]:
        """为某个目标生成检索关键词列表"""
        info = self.targets.get(category) or {}
        defaults = info.get("default_keywords", []) or []
        watch = info.get("watch_keywords", []) or []
        kws = [target_name]  # 目标名优先级最高
        kws.extend(defaults[:3])
        kws.extend(watch[:2])
        return list(dict.fromkeys(kws))  # 保序去重

    # ---------------- 单源查询 -----------------

    def _query_source(self, source: Dict[str, Any], target_name: str,
                      keyword: str, target_category: str,
                      target_label: str, cutoff_time: datetime) -> Iterable[SentimentArticle]:
        """针对单个媒体源，尝试获取结果。先用 API/列表接口，未果则走浏览器兜底"""
        # 全局超时短路
        if self._time_up():
            return

        name = source.get("name", "未知媒体")

        # 优先尝试专用 API
        if name == "财联社" and HAS_NEWS_API and cls_search:
            try:
                results = cls_search(keyword, page_size=10) or []
                for item in results:
                    if self._time_up():
                        return
                    art = self._build_article(
                        source=source,
                        target_name=target_name,
                        target_category=target_category,
                        target_label=target_label,
                        title=item.get("title", ""),
                        summary=item.get("brief", "") or item.get("content", "")[:200],
                        content=item.get("content", ""),
                        publish_time=item.get("ctime") or item.get("pubdate") or "",
                        url=item.get("url", ""),
                    )
                    yield art
                return
            except Exception as e:
                logger.debug("财联社 API 失败，回退到通用: %s", e)

        if name == "华尔街见闻" and HAS_NEWS_API and wscn_articles:
            try:
                results = wscn_articles(keyword=keyword, limit=10) or []
                for item in results:
                    if self._time_up():
                        return
                    art = self._build_article(
                        source=source,
                        target_name=target_name,
                        target_category=target_category,
                        target_label=target_label,
                        title=item.get("title", ""),
                        summary=item.get("summary", "") or item.get("content_short", ""),
                        content=item.get("content", ""),
                        publish_time=item.get("display_time", "") or item.get("created_at", ""),
                        url=item.get("uri", "") or item.get("url", ""),
                    )
                    yield art
                return
            except Exception as e:
                logger.debug("华尔街见闻 API 失败: %s", e)

        # 通用搜索 URL 兜底（基于 search_urls 模板）
        search_url_templates = source.get("search_urls") or []
        for tpl in search_url_templates[:1]:  # 每个源只取一个模板，避免太慢
            url = tpl.replace("{kw}", quote_kw(keyword))
            yield from self._fetch_with_fallback(
                url=url, source=source,
                target_name=target_name, target_category=target_category,
                target_label=target_label, keyword=keyword,
            )

        # v5.0.0: RSS 直连数据源（零反爬，优先于浏览器兜底）。
        # 只有 source 显式配置了 rss_feeds 才走此分支。
        if self.use_rss and self._rss_fetcher is not None and source.get("rss_feeds"):
            for rss_url in source.get("rss_feeds") or []:
                if self._time_up():
                    return
                feed = {"name": name, "url": rss_url}
                try:
                    items = self._rss_fetcher.fetch(feed) or []
                except Exception as e:
                    logger.debug("RSS 抓取失败 %s: %s", rss_url, e)
                    continue
                for it in items:
                    if self._time_up():
                        return
                    title = getattr(it, "title", "") or ""
                    content = (getattr(it, "description", "") or "") + " " + (getattr(it, "content", "") or "")
                    if keyword and keyword not in title and keyword not in content:
                        continue
                    yield self._build_article(
                        source=source,
                        target_name=target_name,
                        target_category=target_category,
                        target_label=target_label,
                        title=title,
                        summary=getattr(it, "description", "") or "",
                        content=getattr(it, "content", "") or "",
                        publish_time=getattr(it, "pub_date", "") or "",
                        url=getattr(it, "link", "") or "",
                    )

    def _fetch_with_fallback(self, url: str, source: Dict[str, Any],
                             target_name: str, target_category: str,
                             target_label: str, keyword: str) -> Iterable[SentimentArticle]:
        """先用 http_utils 抓列表页；若失败/反爬则切到 browser_scraper。
        关键改进:
          - 全局超时时立即返回，不等待单源
          - 单源在独立线程中执行，可被 per_source_timeout 强制中断
          - 域名级熔断短接 (同一域名已被熔断则直接跳过)
          - 占位记录按 (target, source, hour) 去重
          - DNS 预探测，省掉等 DNS 解析失败的时间
        """
        # 全局超时：立即返回
        if self._time_up():
            return

        # 域名短路：减少无效等待
        if self._domain_is_blocked(url):
            return

        # DNS 探测短路 — 如果目标域名无法解析，直接 skip（不浪费 timeout）
        if self._domain_unresolvable(url):
            return

        # 1) 通用爬虫 - 用线程级超时包装
        content = self._run_with_timeout(
            lambda: self._fetch_url_safely(url),
            timeout=self.per_source_timeout,
            name=source.get("name", ""),
        )
        if content:
            yield from self._parse_list_page(
                html=str(content), source=source,
                target_name=target_name, target_category=target_category,
                target_label=target_label, keyword=keyword,
            )
            return

        if self._time_up():
            return

        # 2) 浏览器兜底（v4.2）— 同样带超时
        if self.enable_browser_fallback:
            html = self._run_with_timeout(
                lambda: self._fetch_with_browser(url),
                timeout=self.per_source_timeout * 2,
                name=source.get("name", ""),
            )
            if html:
                yield from self._parse_list_page(
                    html=str(html), source=source,
                    target_name=target_name, target_category=target_category,
                    target_label=target_label, keyword=keyword,
                )
                return

        # 3) 占位记录 — 但避免同一 (target, source) 1 小时内的重复占位
        if not self._placeholder_seen(target_name, source.get("name", "")):
            yield self._build_article(
                source=source,
                target_name=target_name, target_category=target_category,
                target_label=target_label,
                title=f"[未能直接抓取] {target_name} 关键词={keyword} 来自 {source.get('name','')}",
                summary=f"由于目标站点反爬或网络异常，未能直接抓取列表页。"
                       f"该目标与媒体源已记录，下次爬取会自动重试。",
                content="",
                publish_time="",
                url=url,
            )

    # ---------------- 内部 fetch 工具 -----------------

    def _log_fetch_failure(self, url: str, stage: str, exc: Exception) -> None:
        """v5.0.0: 吞错时可诊断 — 输出 URL + 阶段 + 原因/提示，便于排查源站封禁 vs 无数据。"""
        hint = ""
        try:
            from http_utils import get_diagnostic  # type: ignore
            diag = get_diagnostic(exc, url)
            if isinstance(diag, dict):
                hint = diag.get("hint") or diag.get("reason") or str(diag)[:120]
        except Exception:
            pass
        logger.warning("抓取失败 [%s] %s: %s%s", stage, url, exc, f" | {hint}" if hint else "")

    def _is_soft_blocked(self, html: str) -> bool:
        """v5.0.0: 检测软封禁（HTTP 200 但内容为验证码/访问拦截页）。
        接线 anti_block_utils.detect_block 纯函数，无副作用。"""
        if not html:
            return False
        try:
            from anti_block_utils import detect_block  # type: ignore
            sig = detect_block(200, body_sample=html[:2000])
            return sig is not None
        except Exception:
            return False

    def _fetch_url_safely(self, url: str) -> Optional[str]:
        """通过 FinancialPageScraper 抓取；异常被吞，返回 None"""
        if not HAS_BASE_SCRAPER:
            return None
        try:
            scraper = FinancialPageScraper()
            content = scraper.scrape_url(url)
            if not content:
                return None
            html = str(content)
            # v5.0.0: 软封禁检测 — 200 但验证码/拦截页时触发浏览器兜底
            if self._is_soft_blocked(html):
                self._log_fetch_failure(url, "soft-block", RuntimeError("页面含软封禁特征（验证码/拦截）"))
                return None
            return html
        except Exception as e:
            self._log_fetch_failure(url, "http", e)
            return None

    def _fetch_with_browser(self, url: str) -> Optional[str]:
        """通过浏览器抓取；异常吞掉。v5.0.0 复用进程级单例，避免每源冷启动。"""
        try:
            from browser_scraper import _get_browser_scraper  # type: ignore
            bs = _get_browser_scraper(headless=True)
            if bs is None:
                return None
            html = bs.fetch(url, wait_until="domcontentloaded", retries=1)
            return str(html) if html else None
        except Exception as e:
            self._log_fetch_failure(url, "browser", e)
            return None

    def _run_with_timeout(self, fn, timeout: int, name: str = ""):
        """v5.0.0: 协作式超时执行 — 超时后不阻塞外层（修复 Python 线程不可强杀的假中断）。

        线程不可强制终止，故：
          1) 超时精确记录并返回 None
          2) 将该源置入 self._cancelled_sources，供内层循环（爬取/解析）检查后尽快退出
          3) executor 用 shutdown(wait=False)，残留线程自行退出，外层不等待
        """
        if timeout <= 0:
            return fn()
        try:
            from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutTimeout
        except ImportError:  # pragma: no cover
            return fn()
        executor = ThreadPoolExecutor(max_workers=1)
        try:
            future = executor.submit(fn)
            try:
                return future.result(timeout=timeout)
            except FutTimeout:
                logger.debug("⏱ 单源超时(%ds)%s，标记取消", timeout,
                             f" [{name}]" if name else "")
                if name:
                    self._cancelled_sources.add(name)
                return None
            except Exception as e:
                logger.debug("单源执行异常: %s", e)
                return None
        finally:
            # wait=False：不阻塞外层；残留线程靠 cancelled 标记 / 底层连接超时退出
            try:
                executor.shutdown(wait=False, cancel_futures=True)
            except Exception:
                pass

    # ---------------- 列表页解析 + 内容抽取 -----------------

    def _parse_list_page(self, html: str, source: Dict[str, Any],
                         target_name: str, target_category: str,
                         target_label: str, keyword: str) -> Iterable[SentimentArticle]:
        """通用列表页解析 — 抽取 (标题 / 时间 / 链接) 三元组
        优先使用 BeautifulSoup，不可用时自动降级到正则解析。
        """
        try:
            from bs4 import BeautifulSoup  # type: ignore
            soup = BeautifulSoup(html, "lxml")
            anchors = soup.find_all("a")
            for a in anchors:
                title = (a.get_text() or "").strip()
                href = a.get("href") or ""
                if not title or len(title) < 8 or len(title) > 200:
                    continue
                if not href.startswith(("http://", "https://", "/")):
                    continue
                if href.startswith("/"):
                    href = (source.get("homepage", "") or "").rstrip("/") + href
                time_text = _extract_time(a) or _extract_time(a.parent)
                art = self._build_article(
                    source=source, target_name=target_name,
                    target_category=target_category, target_label=target_label,
                    title=title, summary="", content="",
                    publish_time=time_text, url=href,
                )
                yield art
            return
        except Exception:
            pass  # 降级到正则解析

        # —— 纯标准库回退：正则提取 <a> 标签 ——
        homepage = (source.get("homepage", "") or "").rstrip("/")
        # 匹配 <a ... href="URL" ...>text</a>
        a_pattern = re.compile(
            r'<a\s[^>]*?href\s*=\s*["\']([^"\'>\s]+)["\'][^>]*>\s*(.+?)\s*</a>',
            re.IGNORECASE | re.DOTALL,
        )
        tag_pattern = re.compile(r'<[^>]+>')
        for m in a_pattern.finditer(html):
            href = m.group(1)
            raw_text = m.group(2)
            # 去除 HTML 标签
            title = tag_pattern.sub('', raw_text).strip()
            title = re.sub(r'\s+', ' ', title)
            if not title or len(title) < 8 or len(title) > 200:
                continue
            if not href.startswith(("http://", "https://", "/")):
                continue
            if href.startswith("/"):
                href = homepage + href
            # 尝试从上下文提取时间
            ctx_start = max(0, m.start() - 200)
            ctx = html[ctx_start:m.end() + 50]
            time_text = _extract_time_from_text(ctx)
            art = self._build_article(
                source=source, target_name=target_name,
                target_category=target_category, target_label=target_label,
                title=title, summary="", content="",
                publish_time=time_text, url=href,
            )
            yield art

    # ---------------- Article 工厂 -----------------

    def _build_article(self, source: Dict[str, Any], target_name: str,
                       target_category: str, target_label: str,
                       title: str, summary: str = "",
                       content: str = "", publish_time: str = "",
                       url: str = "") -> SentimentArticle:
        # 规范化时间
        pub_norm = _norm_time(publish_time)

        # 情感分类
        sentiment, score, hits, severity = self.classifier.classify(title, content)
        category = hits[0] if hits else ""

        return SentimentArticle(
            title=title or "(无标题)",
            summary=_first_n_chars(content or summary, 240),
            content=content or "",
            source=source.get("name", ""),
            source_type=source.get("category", ""),
            target_name=target_name,
            target_type=target_label,
            publish_time=pub_norm,
            url=url,
            sentiment=sentiment,
            sentiment_score=score,
            severity=severity,
            category=category,
            keywords_matched=hits[:10],
            fetch_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            extra={
                "language": source.get("language", "zh"),
                "credibility": source.get("credibility", 5),
            },
        )

    # ---------------- 去重 / 过滤 -----------------

    def _is_dup(self, article: SentimentArticle) -> bool:
        if not article.title or article.title.startswith("[未能直接抓取]"):
            return False  # 占位项不去重
        fp = article.fingerprint
        with _SEEN_LOCK:
            if fp in _SEEN_INDEX:
                return True
            # v5.0.0: 模糊去重 — 同 target 已见标题相似度 > 0.85 视为重复
            title_norm = re.sub(r"\s+", "", article.title or "").lower()
            seen_titles = _TITLE_INDEX.setdefault(article.target_name or "", [])
            for prev in seen_titles:
                try:
                    from difflib import SequenceMatcher
                    ratio = SequenceMatcher(None, title_norm, prev).ratio()
                except Exception:
                    ratio = 0.0
                if ratio > 0.85:
                    article.dedup_ratio = ratio
                    return True
            seen_titles.append(title_norm)
            _SEEN_INDEX[fp] = article.publish_time or article.fetch_time
            # 持久化（写入 1/20 概率，避免频繁写盘；锁内写避免并发撕裂）
            if hash(fp) % 20 == 0:
                try:
                    _SEEN_INDEX_FILE.write_text(
                        json.dumps(_SEEN_INDEX, ensure_ascii=False), encoding="utf-8"
                    )
                except OSError:
                    pass
        return False

    def _is_in_window(self, article: SentimentArticle,
                      cutoff_time: datetime) -> bool:
        """检查文章发布时间是否在时间窗内。

        规则:
          - 占位文章（[未能直接抓取]）: 保留（记录爬取失败）
          - 无 publish_time: 保留（不因格式问题误杀）
          - publish_time >= cutoff_time: 保留
          - publish_time < cutoff_time: 丢弃
        """
        if not article.title or article.title.startswith("[未能直接抓取]"):
            return True  # 保留占位标记
        if not article.publish_time:
            return True  # 保留无时间文章
        try:
            pub_str = str(article.publish_time)[:10]
            pub_dt = datetime.strptime(pub_str, "%Y-%m-%d")
            return pub_dt >= cutoff_time
        except (ValueError, IndexError):
            return True  # 无法解析时间的文章保留

    def _compute_date_validation(self, articles: List[SentimentArticle],
                                   cutoff_time: datetime,
                                   requested_days: int) -> Dict[str, Any]:
        """爬取后日期核验：统计文章是否在请求的时间窗内。

        Returns:
            {"requested_days": 7,
             "cutoff_date": "2026-07-23",
             "articles_checked": 50,
             "out_of_window": 0,
             "unparseable_dates": 2,
             "date_range_actual": {"earliest": "2026-07-24", "latest": "2026-07-30"}}
        """
        checked = 0
        out_of_window = 0
        unparseable = 0
        out_articles: List[Dict[str, Any]] = []
        dates_found: List[str] = []

        for a in articles:
            if not a.publish_time:
                unparseable += 1
                continue
            try:
                pub_str = str(a.publish_time)[:10]
                pub_dt = datetime.strptime(pub_str, "%Y-%m-%d")
                checked += 1
                dates_found.append(pub_str)
                if pub_dt < cutoff_time:
                    out_of_window += 1
                    out_articles.append({
                        "title": a.title[:60],
                        "publish_time": a.publish_time,
                        "age_days": (datetime.now() - pub_dt).days,
                    })
            except (ValueError, IndexError):
                unparseable += 1

        # 实际日期范围
        actual_range = {}
        if dates_found:
            dates_found.sort()
            actual_range = {"earliest": dates_found[0], "latest": dates_found[-1]}

        return {
            "requested_days": requested_days,
            "cutoff_date": cutoff_time.strftime("%Y-%m-%d"),
            "articles_checked": checked,
            "out_of_window": out_of_window,
            "unparseable_dates": unparseable,
            "out_of_window_samples": out_articles[:5],
            "date_range_actual": actual_range,
        }

    def _post_filter(self, articles: List[SentimentArticle],
                     positive_only: bool, negative_only: bool) -> List[SentimentArticle]:
        out = []
        for a in articles:
            if positive_only and a.sentiment != "positive":
                continue
            if negative_only and a.sentiment != "negative":
                continue
            out.append(a)
        return out

    # ---------------- 快照存储 -----------------

    def _save_snapshot(self, snapshot: SentimentSnapshot):
        file_path = self.snapshot_dir / f"{snapshot.snapshot_id}.json"
        file_path.write_text(
            json.dumps(snapshot.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        snapshot.extra_path = str(file_path)  # type: ignore[attr-defined]
        # v4.5.1: 索引写入节流 — 每 5 个快照才重写一次 index.json
        # 平时只 append 临时标记，下次保存时重建
        idx = self.snapshot_dir / "index.json"
        index = []
        if idx.exists():
            try:
                index = json.loads(idx.read_text(encoding="utf-8"))
            except Exception:
                index = []
        index.insert(0, {
            "snapshot_id": snapshot.snapshot_id,
            "created_at": snapshot.created_at,
            "total": snapshot.stats.get("total", 0),
            "pos": snapshot.stats.get("by_sentiment", {}).get("positive", 0),
            "neg": snapshot.stats.get("by_sentiment", {}).get("negative", 0),
            "path": str(file_path),
        })
        # 仅在快照数为 5 的倍数 或快照数<=3时写盘，减少 IO
        if len(index) <= 3 or len(index) % 5 == 0:
            idx.write_text(json.dumps(index[:50], ensure_ascii=False, indent=2), encoding="utf-8")


# ============================================================
# 5. 工具函数
# ============================================================

def quote_kw(kw: str) -> str:
    from urllib.parse import quote
    return quote(kw)


def _first_n_chars(text: str, n: int) -> str:
    text = re.sub(r"\s+", " ", text or "").strip()
    if len(text) <= n:
        return text
    return text[:n].rstrip() + "…"


_TIME_RE = re.compile(
    r"(\d{4})[-/年.](\d{1,2})[-/月.](\d{1,2})(?:日)?(?:(?:\s+|T)(\d{1,2}))?:?(\d{1,2})?:?(\d{1,2})?"
)


_REL_TIME_RE = re.compile(r"(\d+)\s*(分钟|小时|天|日|周)前|今天|昨天|前天")


def _norm_relative_time(text: str) -> str:
    """v5.0.0: 把相对时间（3小时前/昨天/前天/2天前/今天）转为绝对时间字符串。"""
    now = datetime.now()
    m = _REL_TIME_RE.search(text)
    if not m:
        return ""
    if m.group(2) is None:
        # 今天 / 昨天 / 前天
        if "昨天" in m.group(0):
            return (now - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
        if "前天" in m.group(0):
            return (now - timedelta(days=2)).strftime("%Y-%m-%d %H:%M:%S")
        return now.strftime("%Y-%m-%d %H:%M:%S")
    n = int(m.group(1))
    unit = {"分钟": "minutes", "小时": "hours", "天": "days",
            "日": "days", "周": "weeks"}[m.group(2)]
    return (now - timedelta(**{unit: n})).strftime("%Y-%m-%d %H:%M:%S")


def _norm_time(time_text: str) -> str:
    """把 2026年7月27日 09:42 / 2026-07-27 / 07-27 / 3小时前 等统一为 YYYY-MM-DD HH:MM:SS"""
    if not time_text:
        return ""
    # v5.0.0: 相对时间 → 绝对时间
    rel = _norm_relative_time(str(time_text))
    if rel:
        return rel
    m = _TIME_RE.search(str(time_text))
    if not m:
        # 仅日期
        d = re.search(r"(\d{4})[-/年.](\d{1,2})[-/月.](\d{1,2})", str(time_text))
        if d:
            return f"{d.group(1)}-{int(d.group(2)):02d}-{int(d.group(3)):02d} 00:00:00"
        return str(time_text)
    y, mo, d, h, mi, s = m.groups()
    h = h or "0"; mi = mi or "0"; s = s or "0"
    return f"{int(y):04d}-{int(mo):02d}-{int(d):02d} {int(h):02d}:{int(mi):02d}:{int(s):02d}"


def _extract_time_from_text(text: str) -> str:
    """从纯文本中提取时间——用于正则解析回退"""
    patterns = [
        r'(\d{4}[-/]\d{1,2}[-/]\d{1,2}\s+\d{1,2}:\d{2})',
        r'(\d{4}[-/]\d{1,2}[-/]\d{1,2})',
        r'(\d{1,2}\u6708\d{1,2}\u65e5\s+\d{1,2}:\d{2})',
        r'(\d{1,2}\u5c0f\u65f6\u524d)',
        r'(\d+\u5206\u949f\u524d)',
    ]
    for pat in patterns:
        m = re.search(pat, text)
        if m:
            return m.group(1)
    return ""

def _extract_time(element) -> str:
    """从父/子元素中提取时间字符串"""
    if element is None:
        return ""
    for attr in ("title", "data-time", "datetime"):
        v = element.get(attr)
        if v:
            return str(v)
    txt = element.get_text(" ", strip=True) if hasattr(element, "get_text") else ""
    m = _TIME_RE.search(txt)
    if m:
        return m.group(0)
    return ""


def _count_by(items: List[Any], key_fn) -> Dict[str, int]:
    out = defaultdict(int)
    for it in items:
        k = key_fn(it)
        out[k] += 1
    return dict(out)


# ============================================================
# 6. 顶层便捷 API
# ============================================================

def crawl_sentiment(targets: Optional[List[str]] = None,
                    categories: Optional[List[str]] = None,
                    sources: Optional[List[str]] = None,
                    source_categories: Optional[List[str]] = None,
                    days: int = 7,
                    positive_only: bool = False,
                    negative_only: bool = False,
                    max_articles: int = 50,
                    max_total_seconds: int = 30,
                    per_source_timeout: int = 4,
                    dry_run: bool = False,
                    confirmed: bool = True,
                    run_backtest: bool = False,
                    backtest_drop: Optional[Tuple[str, ...]] = None,
                    parallel_workers: int = 0,
                    use_rss: bool = True) -> SentimentSnapshot:
    """便捷函数：一次全网舆情爬取。
    Args:
        max_total_seconds: 整个爬取最大耗时（默认 30s），到时立即返回已有结果
        per_source_timeout: 单源超时（默认 4s）
        dry_run: 仅返回爬取计划（不发任何 HTTP 请求）
        confirmed: 是否已确认（False 时等同于 dry_run=True）
        run_backtest: 是否对每篇文章做 4 维回测（慢 ~20%）
        backtest_drop: 回测后丢弃的推荐等级元组（如 ("建议丢弃",)）
        parallel_workers: 并发抓取线程数（0=顺序，>0 启用并发加速）
        use_rss: v5.0.0 是否启用 RSS 直连（默认 True，仅对配置了 rss_feeds 的站点生效）
    默认更激进以保证对话体验。
    """
    crawler = SentimentCrawler(
        max_total_seconds=max_total_seconds,
        per_source_timeout=per_source_timeout,
        use_rss=use_rss,
    )
    # 用户未指定 media 时不再默认只跑权威+财经 — 默认爬权威+财经+自媒体，让对话/导出一键拿数据
    if not source_categories and not sources:
        source_categories = ["authoritative", "financial_vertical", "self_media"]
    return crawler.crawl(
        target_names=targets,
        target_categories=categories,
        source_names=sources,
        source_categories=source_categories,
        days=days,
        positive_only=positive_only,
        negative_only=negative_only,
        max_articles=max_articles,
        dry_run=dry_run,
        confirmed=confirmed,
        run_backtest=run_backtest,
        backtest_drop=backtest_drop,
        parallel_workers=parallel_workers,
    )


def list_sentiment_targets() -> List[Dict[str, Any]]:
    """查看目标库"""
    loader = SentimentTargetLoader()
    stats = loader.stats()
    return [{"category": k, "label": (loader.get(k).get("label", k) if loader.get(k) else k),
             "count": v} for k, v in stats.items()]


def list_sentiment_sources(category: Optional[str] = None) -> List[Dict[str, Any]]:
    """查看媒体源"""
    loader = SentimentSourceLoader()
    if category:
        return loader.sources_by_category(category)
    return loader.all_sources()


def add_custom_sentiment_target(category: str, name: str,
                                aliases: Optional[List[str]] = None) -> Dict[str, Any]:
    """新增自定义目标"""
    loader = SentimentTargetLoader()
    return loader.add_custom_target(category, name, aliases)


# ============================================================
# 7. CLI
# ============================================================

def _cli():
    import argparse
    parser = argparse.ArgumentParser(
        description="cn-financial-scraper 全网舆情爬虫 v4.3",
    )
    parser.add_argument("--targets", type=str, default="",
                        help="目标列表，逗号分隔，如 '贵州茅台,工银瑞信基金'")
    parser.add_argument("--categories", type=str, default="",
                        help="目标类别，逗号分隔，如 'fund_company,listed_company'")
    parser.add_argument("--sources", type=str, default="",
                        help="媒体源，逗号分隔")
    parser.add_argument("--source-categories", type=str, default="",
                        help="媒体类别，逗号分隔，如 'authoritative,self_media'")
    parser.add_argument("--days", type=int, default=7, help="时间窗口（天）")
    parser.add_argument("--negative-only", action="store_true", help="仅保留舆情")
    parser.add_argument("--positive-only", action="store_true", help="仅保留正面")
    parser.add_argument("--max", type=int, default=50, help="最大文章数")
    parser.add_argument("--stats", action="store_true", help="查看媒体源/目标库统计")
    parser.add_argument("--list-targets", action="store_true", help="列出目标库")
    parser.add_argument("--list-sources", action="store_true", help="列出媒体源")
    parser.add_argument("--add-target", nargs=3, metavar=("CATEGORY", "NAME", "ALIASES"),
                        help="新增自定义目标，类目-名称-别名(逗号分隔)")
    args = parser.parse_args()

    if args.stats:
        s = SentimentSourceLoader().stats()
        t = SentimentTargetLoader().stats()
        print("📰 媒体源:", json.dumps(s, ensure_ascii=False, indent=2))
        print("🎯 目标库:", json.dumps(t, ensure_ascii=False, indent=2))
        return

    if args.list_targets:
        print(json.dumps(list_sentiment_targets(), ensure_ascii=False, indent=2))
        return
    if args.list_sources:
        print(json.dumps(list_sentiment_sources(), ensure_ascii=False, indent=2))
        return

    if args.add_target:
        cat, name, aliases = args.add_target
        alias_list = [a.strip() for a in aliases.split(",") if a.strip()]
        print(json.dumps(add_custom_sentiment_target(cat, name, alias_list), ensure_ascii=False))
        return

    targets = [t.strip() for t in args.targets.split(",") if t.strip()] or None
    categories = [c.strip() for c in args.categories.split(",") if c.strip()] or None
    sources = [s.strip() for s in args.sources.split(",") if s.strip()] or None
    source_cats = [c.strip() for c in args.source_categories.split(",") if c.strip()] or None

    snapshot = crawl_sentiment(
        targets=targets, categories=categories,
        sources=sources, source_categories=source_cats,
        days=args.days,
        positive_only=args.positive_only,
        negative_only=args.negative_only,
        max_articles=args.max,
    )

    print(f"✅ 完成！快照ID: {snapshot.snapshot_id}")
    print(f"   共 {snapshot.stats.get('total', 0)} 条 | "
          f"正面 {snapshot.positive_count()} | "
          f"舆情 {snapshot.negative_count()} | "
          f"中性 {snapshot.neutral_count()}")
    print(f"   严重等级: {snapshot.stats.get('by_severity', {})}")
    print(f"   媒体类别分布: {snapshot.stats.get('by_source_type', {})}")
    print(f"   保存路径: {snapshot.snapshot_dir if hasattr(snapshot, 'snapshot_dir') else SNAPSHOT_DIR}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    _cli()
