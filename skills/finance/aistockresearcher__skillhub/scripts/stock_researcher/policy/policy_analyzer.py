#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
政策解读分析引擎 (v7.0.0)
===========================
独立的政策解读分析模块，从多源采集政策新闻，进行：
  - 政策分类（货币/财政/产业/监管/贸易/地缘政治）
  - 影响力评分（方向×力度×确定性）
  - 板块映射（政策→受益/受损板块）
  - 市场级政策影响评估

纯 Python 标准库，零依赖。数据源：东方财富+财联社+新浪财经（免费、无 Key）。

用法:
    from stock_researcher.policy.policy_analyzer import PolicyAnalyzer
    pa = PolicyAnalyzer()
    impact = pa.analyze_market_impact("cn")      # A股政策面评估
    sector_imp = pa.analyze_sector_impact("新能源", "cn")
"""

import json
import re
import ssl
import urllib.request
import urllib.error
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta


@dataclass
class PolicyImpact:
    """政策影响评估结果"""
    direction: str = "中性"        # "利好" | "偏利好" | "中性" | "偏利空" | "利空"
    score: float = 0               # -100 ~ +100（正=利好）
    strength: int = 1              # 力度 1-5
    confidence: float = 0.5        # 确定性 0-1
    category: str = ""             # 政策分类
    title: str = ""                # 代表性政策标题
    affected_sectors: List[str] = field(default_factory=list)  # 受影响的板块
    summary: str = ""              # 一句话摘要


@dataclass
class PolicyBundle:
    """一组政策影响评估"""
    market: str
    timestamp: str
    impacts: List[PolicyImpact] = field(default_factory=list)
    composite_score: float = 0     # 综合评分
    composite_direction: str = "中性"
    top_policies: List[str] = field(default_factory=list)
    affected_sectors: List[str] = field(default_factory=list)


# ── 政策关键词库 ──────────────────────────────

# 政策分类 → 关键词
POLICY_CATEGORIES = {
    "货币政策": {
        "keywords": ["降准", "降息", "加息", "利率", "存款准备金", "逆回购", "MLF",
                   "LPR", "公开市场操作", "货币政策", "央行", "人民银行",
                   "rate cut", "rate hike", "fed", "fomc", "ECB", "BOJ", "PBOC"],
        "weight": 1.2,  # 货币政策影响广泛
    },
    "财政政策": {
        "keywords": ["财政", "赤字", "国债", "地方债", "减税", "税收", "专项债",
                   "财政刺激", "fiscal", "stimulus", "基础设施投资"],
        "weight": 1.1,
    },
    "产业政策": {
        "keywords": ["产业规划", "十四五", "补贴", "扶持", "振兴", "发展规划",
                   "新能源", "半导体", "芯片", "人工智能", "数字经济",
                   "高端制造", "碳中和", "碳达峰", "绿色金融", "ESG",
                   "subsidy", "industrial policy", "CHIPS act"],
        "weight": 1.0,
    },
    "监管政策": {
        "keywords": ["监管", "处罚", "反垄断", "合规", "整改", "约谈",
                   "暂停", "限制", "禁止", "牌照", "数据安全",
                   "个人信息保护", "网络安全审查",
                   "regulation", "antitrust", "SEC", "CFTC"],
        "weight": 1.0,
    },
    "贸易政策": {
        "keywords": ["关税", "贸易战", "出口管制", "进口限制", "反倾销",
                   "反补贴", "WTO", "RCEP", "CPTPP", "贸易摩擦",
                   "实体清单", "制裁", "脱钩",
                   "tariff", "trade war", "export control", "sanctions"],
        "weight": 0.9,
    },
    "地缘政治": {
        "keywords": ["地缘", "冲突", "制裁", "军事", "台海", "南海",
                   "中东", "俄乌", "朝鲜", "外交",
                   "geopolitical", "conflict", "sanctions"],
        "weight": 0.8,
    },
}


# 政策 → 板块映射规则
POLICY_SECTOR_MAP = {
    "降准": ["银行", "房地产", "非银金融"],
    "降息": ["房地产", "汽车", "银行"],
    "新能源": ["新能源", "汽车", "有色金属"],
    "半导体": ["电子", "计算机"],
    "芯片": ["电子"],
    "碳中和": ["新能源", "化工", "钢铁"],
    "反垄断": ["科技", "互联网", "传媒"],
    "房地产调控": ["房地产", "银行", "建材"],
    "药品集采": ["医药生物"],
    "关税": ["电子", "汽车", "机械设备"],
    "出口管制": ["电子", "通信", "军工"],
    "消费刺激": ["消费", "食品饮料", "汽车"],
    "基建": ["建筑材料", "机械设备", "钢铁"],
    "数字经济": ["计算机", "通信", "传媒"],
    "绿色金融": ["新能源", "银行"],
    "军事": ["军工"],
    "制裁": ["科技", "电子", "能源", "军工"],
}


class PolicyAnalyzer:
    """
    政策解读分析引擎。

    功能：
      1. 多源政策新闻采集
      2. 政策分类与影响力评分
      3. 政策→板块映射
      4. 市场级政策影响评估
    """

    NEWS_SOURCES = [
        # 东方财富政策新闻
        ("https://np-listapi.eastmoney.com/comm/web/getNewsByColumns?"
         "columns=102&pageIndex=1&pageSize=15&sort=default",
         "东方财富"),
        # 财联社电报（政策相关）
        ("https://np-listapi.eastmoney.com/comm/web/getNewsByColumns?"
         "columns=266&pageIndex=1&pageSize=15&sort=default",
         "财联社"),
    ]

    def __init__(self, cache_ttl: int = 600):
        """
        Args:
            cache_ttl: 缓存有效期（秒），默认10分钟
        """
        self._ctx = ssl.create_default_context()
        self._ctx.check_hostname = False
        self._ctx.verify_mode = ssl.CERT_NONE
        self._cache_ttl = cache_ttl
        self._cache = {}  # market → (timestamp, PolicyBundle)

    def fetch_policy_news(self, limit: int = 20) -> List[dict]:
        """
        多源采集政策相关新闻。

        Returns:
            [{"title": str, "source": str, "time": str, "category": str}, ...]
        """
        all_news = []

        for url, source_name in self.NEWS_SOURCES:
            try:
                req = urllib.request.Request(url, headers={
                    "User-Agent": "Mozilla/5.0",
                    "Referer": "https://www.eastmoney.com/",
                })
                with urllib.request.urlopen(req, timeout=10, context=self._ctx) as resp:
                    data = json.loads(resp.read().decode("utf-8", errors="replace"))

                items = data.get("data", {}).get("list", [])
                for item in items[:limit]:
                    title = item.get("title", "")
                    # 分类
                    category = self._classify_policy(title)
                    if category:
                        all_news.append({
                            "title": title,
                            "source": source_name,
                            "time": item.get("showTime", ""),
                            "category": category,
                        })
            except Exception:
                continue

        return sorted(all_news, key=lambda n: n.get("time", ""), reverse=True)[:limit]

    def _classify_policy(self, text: str) -> str:
        """将新闻标题归类到政策类别"""
        text_lower = text.lower()
        for category, info in POLICY_CATEGORIES.items():
            for kw in info["keywords"]:
                if kw.lower() in text_lower:
                    return category
        return ""

    def _analyze_impact(self, title: str, category: str) -> PolicyImpact:
        """
        分析单条政策的行业影响。

        判断逻辑：
          1. 方向：利好/利空（关键词极性）
          2. 力度：1-5（关键词密度+类别权重大）
          3. 确定性：0-1（官方 vs 传闻）
        """
        # 关键词极性判断
        positive_kw = ["利好", "支持", "促进", "推动", "鼓励", "补贴", "降准", "降息",
                      "振兴", "减税", "放宽", "放开", "批准", "获批", "试点",
                      "stimulus", "support", "boost", "approval", "positive"]
        negative_kw = ["利空", "限制", "禁止", "处罚", "监管", "约谈", "调查",
                      "制裁", "加税", "罚款", "收紧", "暂停",
                      "crackdown", "fine", "investigation", "sanctions",
                      "restriction", "tighten"]

        pos_count = sum(1 for kw in positive_kw if kw in title)
        neg_count = sum(1 for kw in negative_kw if kw in title)

        if pos_count > neg_count:
            direction = "利好" if pos_count >= 3 else "偏利好"
            polar_sign = 1
        elif neg_count > pos_count:
            direction = "利空" if neg_count >= 3 else "偏利空"
            polar_sign = -1
        else:
            direction = "中性"
            polar_sign = 0

        # 力度：关键词密度 + 类别权重
        total_hits = pos_count + neg_count
        base_strength = min(5, max(1, total_hits))
        category_weight = POLICY_CATEGORIES.get(category, {}).get("weight", 1.0)
        strength = min(5, max(1, int(base_strength * category_weight)))

        # 确定性：官方 > 媒体解读 > 传闻
        official_kw = ["国务院", "央行", "发改委", "财政部", "工信部", "证监会",
                      "银保监会", "国常会",
                      "fed", "european central bank", "sec"]
        rumor_kw = ["传闻", "或", "可能", "拟", "消息称", "据称",
                   "rumor", "reportedly", "sources say"]
        if any(kw.lower() in title.lower() for kw in official_kw):
            confidence = 0.85
        elif any(kw.lower() in title.lower() for kw in rumor_kw):
            confidence = 0.4
        else:
            confidence = 0.6

        # 板块映射
        affected = []
        for policy_topic, sectors in POLICY_SECTOR_MAP.items():
            if policy_topic in title:
                affected.extend(sectors)

        # 评分
        score = polar_sign * strength * confidence * 20  # -100 ~ +100

        return PolicyImpact(
            direction=direction,
            score=round(score, 1),
            strength=strength,
            confidence=round(confidence, 2),
            category=category,
            title=title[:80],
            affected_sectors=list(set(affected))[:5],
            summary=f"[{category}] {'+' if score > 0 else ''}{score:.0f}分: {title[:60]}",
        )

    def analyze_market_impact(self, market: str = "cn") -> dict:
        """
        评估政策对该市场的综合影响。

        Args:
            market: 市场代码（cn/hk/us/jp 等）

        Returns:
            {"score": float, "direction": str, "top_policies": [...],
             "affected_sectors": [...], "impacts": [...]}
        """
        # 检查缓存
        now = time.time()
        if market in self._cache:
            ts, bundle = self._cache[market]
            if now - ts < self._cache_ttl:
                return {
                    "score": bundle.composite_score,
                    "direction": bundle.composite_direction,
                    "top_policies": bundle.top_policies,
                    "affected_sectors": bundle.affected_sectors,
                    "impacts": [{
                        "title": i.title, "direction": i.direction,
                        "score": i.score, "category": i.category,
                        "sectors": i.affected_sectors,
                    } for i in bundle.impacts],
                }

        # 采集+分析
        news_list = self.fetch_policy_news(limit=20)
        impacts = []
        for news in news_list:
            if news["category"]:
                impact = self._analyze_impact(news["title"], news["category"])
                if impact.score != 0:
                    impacts.append(impact)

        # 综合评分（时间衰减：24h内权重1.0，72h内权重0.7，更早0.4）
        total_score = 0.0
        total_weight = 0.0
        affected_sectors = []
        top_policies = []

        for impact in impacts:
            # 时间衰减（简化为按出现顺序）
            pos = impacts.index(impact)
            if pos < 3:
                tw = 1.0
            elif pos < 8:
                tw = 0.7
            else:
                tw = 0.4
            total_score += impact.score * tw
            total_weight += tw
            affected_sectors.extend(impact.affected_sectors)
            top_policies.append(impact.title[:60])

        if total_weight > 0:
            composite = round(total_score / total_weight, 1)
        else:
            composite = 0

        # 方向标签
        if composite > 20:
            direction = "政策偏暖"
        elif composite > 5:
            direction = "温和偏多"
        elif composite > -5:
            direction = "中性"
        elif composite > -20:
            direction = "温和偏空"
        else:
            direction = "政策偏冷"

        # 缓存
        bundle = PolicyBundle(
            market=market,
            timestamp=datetime.now().isoformat(),
            impacts=impacts,
            composite_score=composite,
            composite_direction=direction,
            top_policies=top_policies[:5],
            affected_sectors=list(set(affected_sectors))[:10],
        )
        self._cache[market] = (now, bundle)

        return {
            "score": composite,
            "direction": direction,
            "top_policies": top_policies[:5],
            "affected_sectors": bundle.affected_sectors,
            "impacts": [{
                "title": i.title, "direction": i.direction,
                "score": i.score, "category": i.category,
                "sectors": i.affected_sectors,
            } for i in impacts[:8]],
        }

    def analyze_sector_impact(self, sector: str, market: str = "cn") -> dict:
        """
        评估政策对该板块的影响。

        Args:
            sector: 板块名称
            market: 市场代码

        Returns:
            {"score": float, "direction": str, "summary": str}
        """
        market_result = self.analyze_market_impact(market)
        impacts = market_result.get("impacts", [])

        # 筛选对该板块有影响的政策
        sector_impacts = [
            i for i in impacts
            if sector in i.get("sectors", [])
        ]
        # 也检查板块关键词
        for i in impacts:
            if any(kw in i.get("title", "") for kw in
                  ["新能源", "半导体", "芯片", "医药", "房地产", "银行",
                   "消费", "汽车", "军工", "科技"]):
                if sector in POLICY_SECTOR_MAP.get(
                    next((kw for kw in ["新能源", "半导体", "芯片", "医药",
                     "房地产", "银行", "消费", "汽车", "军工", "科技"]
                     if kw in i.get("title", "")), ""), []):
                    if i not in sector_impacts:
                        sector_impacts.append(i)

        if not sector_impacts:
            return {
                "score": market_result.get("score", 0) * 0.5,  # 跟随市场但减弱
                "direction": market_result.get("direction", "中性"),
                "summary": f"暂无{sector}板块专项政策，跟随市场政策面",
                "top_policies": market_result.get("top_policies", [])[:3],
            }

        # 加权评分
        total = sum(i.get("score", 0) for i in sector_impacts)
        avg_score = total / len(sector_impacts) if sector_impacts else 0

        if avg_score > 15:
            direction = "政策利好"
        elif avg_score > 5:
            direction = "偏利好"
        elif avg_score > -5:
            direction = "中性"
        elif avg_score > -15:
            direction = "偏利空"
        else:
            direction = "政策利空"

        return {
            "score": round(avg_score, 1),
            "direction": direction,
            "summary": f"共{len(sector_impacts)}条相关，"
                      f"{'利好' if avg_score > 0 else '承压'}: "
                      + "; ".join(i.get("title", "")[:40]
                                  for i in sector_impacts[:3]),
            "top_policies": [i.get("title", "")[:60] for i in sector_impacts[:3]],
        }


# ── 便捷函数 ──

def analyze_market_policy(market: str = "cn") -> dict:
    """便捷函数：评估市场政策面"""
    return PolicyAnalyzer().analyze_market_impact(market)


def analyze_sector_policy(sector: str, market: str = "cn") -> dict:
    """便捷函数：评估板块政策面"""
    return PolicyAnalyzer().analyze_sector_impact(sector, market)
