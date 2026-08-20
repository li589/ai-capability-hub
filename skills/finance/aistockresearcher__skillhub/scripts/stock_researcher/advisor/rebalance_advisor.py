#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""调仓建议引擎 (v4.0.0 新增)

输入：用户画像 + 持仓组合分析 + 融合信号
输出：具体调仓动作（减持/增持/新增/清仓），每项附带画像 gap 理由与信号理由。

设计原则（半自动）：仅出建议，不自动执行。每项建议可追溯画像约束与信号来源。
"""
from __future__ import annotations
import sys
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime

SKILL_DIR = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(SKILL_DIR / "scripts"))

from stock_researcher.advisor.user_profile import UserProfile, load_profile
from stock_researcher.advisor.portfolio_analyzer import PortfolioAnalyzer, PortfolioSnapshot


@dataclass
class RebalanceAction:
    action: str             # 减持/增持/新增/清仓/持有
    target: str             # 股票/基金代码
    target_name: str
    amount_pct: float       # 建议调整金额占比(%)
    urgency: str            # 高/中/低
    reasons: List[str]      # 理由列表
    source: str             # 理由来源(profile_gap/signal/constraint/risk)


class RebalanceAdvisor:
    """调仓顾问"""

    def __init__(self):
        self._analyzer = PortfolioAnalyzer()

    def suggest(
        self, client_id: str, top_n: int = 8
    ) -> List[RebalanceAction]:
        actions = []

        # 1. 加载画像 + 持仓分析
        profile = load_profile(client_id)
        ps = self._analyzer.analyze(client_id)
        if ps is None:
            return [RebalanceAction("error", "no_holdings", "",
                                    0, "低", ["无法加载持仓数据"], "system")]

        pm = ps.profile_match or {}

        # 2. 画像 gap → 调仓建议
        gaps = pm.get("gaps", {})
        for asset_type, gap in sorted(gaps.items(), key=lambda x: abs(x[1]), reverse=True):
            if abs(gap) < 5:
                continue
            if gap < -10:  # 实际权重远低于目标
                actions.append(RebalanceAction(
                    action="增配", target=asset_type, target_name=f"{asset_type}类资产",
                    amount_pct=abs(gap), urgency="高" if abs(gap) > 20 else "中",
                    reasons=[f"当前{asset_type}配置{gaps.get(asset_type,0):+.1f}%偏差(目标{pm['target'].get(asset_type,0)}%)",
                             f"风险偏好: {profile.risk_preference if profile else '未知'}"],
                    source="profile_gap",
                ))
            elif gap > 10:  # 实际权重远超目标
                actions.append(RebalanceAction(
                    action="减持", target=asset_type, target_name=f"{asset_type}类资产",
                    amount_pct=abs(gap), urgency="高" if abs(gap) > 20 else "中",
                    reasons=[f"当前{asset_type}配置{gaps.get(asset_type,0):+.1f}%偏高(目标{pm['target'].get(asset_type,0)}%)",
                             f"风险偏好: {profile.risk_preference if profile else '未知'}"],
                    source="profile_gap",
                ))

        # 3. 集中度风险
        conc = ps.concentration or {}
        if conc.get("hhi", 0) > 2500:
            actions.append(RebalanceAction(
                action="分散", target="portfolio", target_name="整体组合",
                amount_pct=0, urgency="中",
                reasons=[f"组合HHI={conc.get('hhi',0):.0f}(高度集中), Top1权重{conc.get('top1_weight_pct',0)}%",
                         "建议分散至不同行业/资产类别"],
                source="risk",
            ))

        # 4. 时长不匹配
        dur = pm.get("duration_match", "")
        if dur and "偏短" in str(dur):
            actions.append(RebalanceAction(
                action="调整", target="duration", target_name="投资时长",
                amount_pct=0, urgency="中",
                reasons=["实际投资时长偏短于风险偏好建议，可考虑降风险或延长持有期"],
                source="profile_gap",
            ))

        # 5. 对持仓个股获取信号（尝试）
        try:
            from stock_researcher.fusion.multi_horizon_forecaster import MultiHorizonForecaster
            fc = MultiHorizonForecaster()
            # 从持仓读取股票代码
            hfile = Path(SKILL_DIR / "data" / "clients" / client_id / "holdings.json")
            if hfile.exists():
                import json as _json
                holdings = _json.load(open(hfile, "r", encoding="utf-8"))
                for h in holdings[:10]:
                    code = str(h.get("code", "")).zfill(6)
                    if not code or len(code) < 6:
                        continue
                    try:
                        result = fc.forecast_stock(code, horizons=["5d", "1M"])
                        fr = result.horizons.get("5d") or result.horizons.get("1M")
                        if fr and fr.direction in ("看空", "分歧偏空") and fr.composite_score < -15:
                            actions.append(RebalanceAction(
                                action="减持", target=code, target_name=h.get("name", code),
                                amount_pct=10, urgency="中",
                                reasons=[f"信号{fr.direction}(得分{fr.composite_score:+.0f},"
                                         f"涨跌幅预测{fr.predicted_pct:+.2f}%)",
                                         f"置信{fr.confidence:.0%}"],
                                source="signal",
                            ))
                        elif fr and fr.direction in ("看多",) and fr.composite_score > 20:
                            actions.append(RebalanceAction(
                                action="增持", target=code, target_name=h.get("name", code),
                                amount_pct=5, urgency="低",
                                reasons=[f"信号{fr.direction}(得分{fr.composite_score:+.0f})"],
                                source="signal",
                            ))
                    except Exception:
                        pass
        except Exception:
            pass  # 信号层面非必需

        return self._prioritize(actions, top_n)

    def _prioritize(self, actions: List[RebalanceAction], top_n: int) -> List[RebalanceAction]:
        priority = {"高": 0, "中": 1, "低": 2}
        actions.sort(key=lambda a: (priority.get(a.urgency, 99), -abs(a.amount_pct)))
        return actions[:top_n]


def format_rebalance_actions(actions: List[RebalanceAction], client_id: str = "") -> str:
    lines = [f"📐 调仓建议  |  {client_id}  |  {datetime.now().strftime('%Y-%m-%d %H:%M')}",
             "=" * 65]
    if not actions:
        lines.append("  ✅ 当前持仓与画像基本匹配，暂无紧急调仓建议。")
        lines.append("=" * 65)
        return "\n".join(lines)
    for i, a in enumerate(actions, 1):
        urg_icon = {"高": "🔴", "中": "🟡", "低": "🟢"}.get(a.urgency, "")
        lines.append(f"  {urg_icon} #{i} [{a.urgency}优] {a.action} {a.target_name}({a.target})"
                     f"  {a.amount_pct:+.0f}%  [{a.source}]")
        for r in a.reasons:
            lines.append(f"       → {r}")
        lines.append("")
    lines.append("⚠️ 以上为基于画像与信号的参考建议，不构成投资指令。调仓决策请自行判断。")
    lines.append("=" * 65)
    return "\n".join(lines)
