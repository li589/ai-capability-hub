#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
客户行为偏差画像引擎（behavioral_profile.py，v10.0 新增）
==========================================================
在客观画像（年龄/金额/周期，见 user_profile_manager）之上，增加「心理与行为偏差」维度，
帮助客户经理把控客户心理与投资风格：

  6 个偏差维度（0-100）：
    loss_aversion   损失厌恶   —— 对浮亏过度敏感，容易恐慌割肉
    disposition_effect 处置效应 —— 赚钱就跑（落袋为安），亏钱死扛
    overconfidence  过度自信   —— 高估自己的择时/选基能力
    herding         从众追涨   —— 跟风热门、朋友推荐
    overtrading     频繁交易   —— 操作过频，交易成本侵蚀收益
    myopia          短视       —— 只看短期波动，缺乏长期视角

输入（按可得性加权，全部缺失时给出「数据不足」提示）：
  1. 行为问卷（behavioral_questionnaire.json，10 题，每题 0-3）
  2. 情绪记录（emotional_records.json：焦虑/恐惧/贪婪 强度与诱因）
  3. 持仓导入历史（import_history：高频重复导入/频繁更换持仓 → 换手代理）
  4. 画像设置（stop_loss 过紧 → 损失厌恶信号）

输出：
  bias_scores / investor_type（6 类心理类型）/ communication_guide（沟通策略建议）
  / confidence（低/中/高）

零依赖（stdlib）。
"""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR.parent))
sys.path.insert(0, str(SCRIPT_DIR.parent.parent / "scripts"))

from fund_advisor_paths import DATA_DIR  # noqa: E402

BIAS_LABELS = {
    'loss_aversion': '损失厌恶',
    'disposition_effect': '处置效应',
    'overconfidence': '过度自信',
    'herding': '从众追涨',
    'overtrading': '频繁交易',
    'myopia': '短视',
}

# 投资者心理类型 → 描述 + 沟通策略
TYPE_GUIDES = {
    '割肉敏感型': {
        'desc': '对浮亏高度敏感，市场波动容易引发恐慌性赎回，往往卖在低点。',
        'tone': '多安抚、多肯定长期逻辑，少用刺激性的涨跌表述；沟通以「陪伴+解释」为主。',
        'risk_warning_frequency': '每次沟通都温和提示波动属正常，亏损时第一时间主动联系。',
        'alert_thresholds': '建议把情绪告警阈值调低（浮亏 -8% 即预警），并配置「冷静 24 小时」缓冲建议。',
        'do_dont': ['建议：设置更宽的止损线并事先约定，避免临时决策',
                    '避免：在下跌行情中反复强调亏损金额，或用「再等等就回本」诱导持有'],
    },
    '落袋为安型': {
        'desc': '盈利拿不住，涨一点就跑，容易错失主升浪；同时对盈利过早兑现的遗憾会诱发追高。',
        'tone': '用「分批止盈」替代「一次卖光」的沟通框架，肯定其锁定收益的合理性。',
        'risk_warning_frequency': '达到止盈线时主动沟通，给出分批止盈节奏建议。',
        'alert_thresholds': '止盈信号触发即提醒，建议默认 20% 分两批执行。',
        'do_dont': ['建议：约定止盈后再买入的冷静期，避免卖完立刻追高',
                    '避免：嘲笑客户「卖飞了」，这反而强化追涨行为'],
    },
    '自信激进型': {
        'desc': '高估自身择时与选基能力，倾向集中持仓、频繁加仓摊薄，回撤风险大。',
        'tone': '用数据说话（回测/胜率/最大回撤），避免正面否定其判断；以「补充视角」方式提示风险。',
        'risk_warning_frequency': '每次给出买入/加仓建议前先提示集中度与回撤风险。',
        'alert_thresholds': '组合集中度（前三大 >60%）与单日估算跌幅预警。',
        'do_dont': ['建议：用历史最大回撤数据校准其预期收益',
                    '避免：与客户争论观点对错，会激发对抗心态'],
    },
    '追涨从众型': {
        'desc': '跟随热点/朋友/大V 操作，容易买在情绪高点，缺乏独立判断。',
        'tone': '先接住「热点叙事」再引导看估值与拥挤度，多用「你了解它为什么涨吗」提问式沟通。',
        'risk_warning_frequency': '热门板块异动时主动提示「高位买入成本」，定期提醒分散配置。',
        'alert_thresholds': '客户提及热门词（AI/半导体/新发爆款）时触发冷静提示。',
        'do_dont': ['建议：帮客户梳理追高买入的历史案例，建立「热度-估值」对照表',
                    '避免：在客户跟风买入后附和「大家都买」'],
    },
    '高频交易型': {
        'desc': '操作频繁，交易成本与择时损耗显著，收益被摩擦成本侵蚀。',
        'tone': '用费用测算（申赎费×次数）量化其交易成本，把「少动」讲成「省到就是赚到」。',
        'risk_warning_frequency': '每次操作前提示成本；月度复盘时给出交易次数统计。',
        'alert_thresholds': '月交易次数 >8 次触发提示。',
        'do_dont': ['建议：推荐定投替代手动择时，降低操作频率',
                    '避免：鼓励短线波段建议（如「今天可以低吸」）'],
    },
    '短视波动型': {
        'desc': '只看短期涨跌，容易在大波动中做出逆向操作，缺乏长期目标锚点。',
        'tone': '把对话锚定到其投资目标与周期（教育金/养老/购房），弱化短期数字。',
        'risk_warning_frequency': '市场单日大幅波动时主动解释波动原因与历史规律。',
        'alert_thresholds': '持有期 <1 年即频繁查看账户的行为提示。',
        'do_dont': ['建议：定期回顾「长期持有收益 vs 频繁操作收益」对比',
                    '避免：用每日涨跌数字开场（如「今天涨了 2% 呢」）'],
    },
    '稳健配置型': {
        'desc': '偏差水平整体较低，心态稳定，能按计划执行，适合作为服务样板客户。',
        'tone': '正常专业沟通即可，定期报告保持交付节奏。',
        'risk_warning_frequency': '常规频率（周报/月报），无需额外干预。',
        'alert_thresholds': '常规告警阈值即可。',
        'do_dont': ['建议：保持例行检视与再平衡提醒',
                    '避免：过度打扰'],
    },
    '综合平衡型': {
        'desc': '存在多个中等水平的偏差，需要组合式引导。',
        'tone': '结合其最突出的 1-2 个偏差，套用对应类型的沟通策略组合。',
        'risk_warning_frequency': '中等频率（周报+关键节点提醒）。',
        'alert_thresholds': '按最显著偏差对应的阈值执行。',
        'do_dont': ['建议：季度做一次行为画像复评，观察偏差变化',
                    '避免：一次给太多建议，抓主要矛盾'],
    },
}


def load_questionnaire(path: Optional[Path] = None) -> Dict[str, Any]:
    """加载行为问卷（不存在返回空结构）"""
    p = path or (SCRIPT_DIR / 'behavioral_questionnaire.json')
    try:
        return json.loads(p.read_text(encoding='utf-8'))
    except Exception:
        return {'questions': []}


class BehavioralBiasEngine:
    """客户行为偏差画像引擎"""

    BIAS_KEYS = ('loss_aversion', 'disposition_effect', 'overconfidence',
                 'herding', 'overtrading', 'myopia')

    def __init__(self, data_dir: Optional[Path] = None):
        self.data_dir = Path(data_dir) if data_dir else DATA_DIR
        self.questionnaire = load_questionnaire()

    # ── 问卷计分 ─────────────────────────────────────────────────

    def score_questionnaire(self, answers: Dict[str, Any]) -> Dict[str, float]:
        """问卷答案 {q1: 0-3 选项下标 或 {"q1": 1}} → 各偏差原始分"""
        raw = {k: 0.0 for k in self.BIAS_KEYS}
        counts = {k: 0 for k in self.BIAS_KEYS}
        qs = self.questionnaire.get('questions', [])
        for q in qs:
            qid = q.get('id', '')
            if qid not in answers:
                continue
            idx = answers[qid]
            try:
                idx = int(idx)
            except (TypeError, ValueError):
                continue
            opts = q.get('options', [])
            if not (0 <= idx < len(opts)):
                continue
            opt = opts[idx]
            bias = opt.get('bias', '')
            if bias in raw:
                raw[bias] += float(opt.get('score', 0))
                counts[bias] += 1
        # 归一化到 0-100（每题满分 3 分）
        out = {}
        for k in self.BIAS_KEYS:
            max_possible = counts[k] * 3.0
            out[k] = round(raw[k] / max_possible * 100, 1) if max_possible else 0.0
        return out

    # ── 行为信号调整 ────────────────────────────────────────────

    @staticmethod
    def adjust_from_behavior(scores: Dict[str, float],
                             emotional_records: Optional[List[dict]] = None,
                             import_history: Optional[list] = None,
                             profile: Optional[dict] = None) -> Dict[str, float]:
        """用行为信号微调偏差分（情绪记录/导入历史/画像设置）"""
        s = dict(scores)
        recs = emotional_records or []
        neg = [r for r in recs if r.get('emotion') in ('焦虑', '恐惧', '崩溃')]
        if neg:
            intense = sum(1 for r in neg if float(r.get('intensity', 0) or 0) >= 7)
            if intense >= 2 or (neg and any('亏' in str(r.get('cause', '')) for r in neg)):
                s['loss_aversion'] = min(100, s['loss_aversion'] + 15)
        if any(r.get('emotion') == '贪婪' for r in recs):
            s['herding'] = min(100, s['herding'] + 10)
        if import_history:
            # 近 90 天内的导入记录作为换手代理
            cutoff = (datetime.now().timestamp() - 90 * 86400)
            recent = []
            for h in import_history:
                if not isinstance(h, dict):
                    continue
                ts = h.get('timestamp', '')
                try:
                    if datetime.fromisoformat(ts).timestamp() >= cutoff:
                        recent.append(h)
                except (ValueError, TypeError):
                    recent.append(h)
            if len(recent) >= 3:
                s['overtrading'] = min(100, s['overtrading'] + 12)
        if profile:
            stop_loss = profile.get('stop_loss')
            if stop_loss is not None and abs(float(stop_loss)) < 5:
                s['loss_aversion'] = min(100, s['loss_aversion'] + 8)
        return {k: round(v, 1) for k, v in s.items()}

    # ── 心理类型与沟通策略 ──────────────────────────────────────

    @staticmethod
    def classify_type(scores: Dict[str, float]) -> str:
        """按主导偏差映射心理类型"""
        dom = max(scores, key=lambda k: scores[k])
        top = scores[dom]
        if top >= 60:
            mapping = {
                'loss_aversion': '割肉敏感型',
                'disposition_effect': '落袋为安型',
                'overconfidence': '自信激进型',
                'herding': '追涨从众型',
                'overtrading': '高频交易型',
                'myopia': '短视波动型',
            }
            return mapping[dom]
        if all(v < 50 for v in scores.values()):
            return '稳健配置型'
        return '综合平衡型'

    # ── 主评估 ──────────────────────────────────────────────────

    def assess(self, client_id: Optional[str] = None,
               answers: Optional[Dict[str, Any]] = None,
               emotional_records: Optional[List[dict]] = None,
               import_history: Optional[list] = None,
               profile: Optional[dict] = None) -> Dict[str, Any]:
        """综合评估：问卷 + 行为信号 → 偏差分/心理类型/沟通策略。

        client_id 提供且 answers 为空时，自动从数据目录读取情绪记录与画像。
        """
        if answers is None and client_id:
            answers = self._load_answers(client_id)
        if emotional_records is None and client_id:
            emotional_records = self._load_emotions(client_id)
        if profile is None and client_id:
            profile = self._load_profile(client_id)

        has_answers = bool(answers)
        base = self.score_questionnaire(answers or {})
        scores = self.adjust_from_behavior(base, emotional_records, import_history, profile)

        sources = []
        if has_answers:
            sources.append('问卷')
        if emotional_records:
            sources.append('情绪记录')
        if import_history:
            sources.append('导入历史')
        if profile:
            sources.append('画像设置')
        confidence = 'high' if has_answers and len(sources) >= 2 else \
                     ('medium' if has_answers or len(sources) >= 2 else 'low')

        itype = self.classify_type(scores)
        guide = TYPE_GUIDES.get(itype, TYPE_GUIDES['综合平衡型'])

        return {
            'client_id': client_id,
            'assessed_at': datetime.now().isoformat(),
            'bias_scores': scores,
            'bias_labels': BIAS_LABELS,
            'dominant_biases': sorted(scores, key=lambda k: -scores[k])[:2],
            'investor_type': itype,
            'type_description': guide['desc'],
            'communication_guide': {
                'tone': guide['tone'],
                'risk_warning_frequency': guide['risk_warning_frequency'],
                'alert_thresholds': guide['alert_thresholds'],
                'do_dont': guide['do_dont'],
            },
            'data_sources': sources,
            'confidence': confidence,
            'note': ('行为偏差画像基于问卷与行为记录推断，仅供客户经理沟通参考，'
                     '不构成对客户风险承受能力的唯一判断依据。'),
        }

    # ── 数据读取（client_id 模式） ──────────────────────────────

    def _load_answers(self, client_id: str) -> dict:
        try:
            p = self.data_dir / 'behavioral_answers.json'
            if p.exists():
                data = json.loads(p.read_text(encoding='utf-8'))
                return data.get(client_id, {})
        except Exception:
            pass
        return {}

    def _load_emotions(self, client_id: str) -> list:
        try:
            p = self.data_dir / 'emotional_records.json'
            if p.exists():
                data = json.loads(p.read_text(encoding='utf-8'))
                return data.get(client_id, [])
        except Exception:
            pass
        return []

    def _load_profile(self, client_id: str) -> dict:
        try:
            p = self.data_dir / 'user_profiles.json'
            if p.exists():
                data = json.loads(p.read_text(encoding='utf-8'))
                return data.get(client_id, {})
        except Exception:
            pass
        return {}

    def save_answers(self, client_id: str, answers: Dict[str, Any]) -> None:
        """保存问卷答案（供下次复评）"""
        p = self.data_dir / 'behavioral_answers.json'
        data = {}
        try:
            if p.exists():
                data = json.loads(p.read_text(encoding='utf-8'))
        except Exception:
            pass
        data[client_id] = answers
        p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')

    # ── 渲染 ────────────────────────────────────────────────────

    def format_report(self, assessment: Dict[str, Any]) -> str:
        L: List[str] = []
        L.append(f"【客户行为画像】{assessment.get('client_id') or ''}")
        L.append(f"  心理类型: {assessment['investor_type']}")
        L.append(f"  类型说明: {assessment['type_description']}")
        L.append("  偏差维度:")
        for k, v in assessment['bias_scores'].items():
            bar = '█' * int(v / 10) + '░' * (10 - int(v / 10))
            L.append(f"    {assessment['bias_labels'].get(k, k):<8} {v:>5.1f}  {bar}")
        L.append(f"  数据来源: {'、'.join(assessment['data_sources']) or '无'} "
                 f"| 置信度: {assessment['confidence']}")
        g = assessment['communication_guide']
        L.append("  沟通策略:")
        L.append(f"    语气: {g['tone']}")
        L.append(f"    风险提示频率: {g['risk_warning_frequency']}")
        L.append(f"    预警阈值: {g['alert_thresholds']}")
        for d in g['do_dont']:
            L.append(f"    · {d}")
        L.append(f"  {assessment['note']}")
        return '\n'.join(L)


if __name__ == '__main__':
    eng = BehavioralBiasEngine()
    demo = {'q1': 0, 'q2': 1, 'q3': 2, 'q4': 1, 'q5': 2, 'q6': 1,
            'q7': 0, 'q8': 2, 'q9': 1, 'q10': 2}
    r = eng.assess(answers=demo)
    print(eng.format_report(r))
