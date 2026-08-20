#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基金经理对话引擎（manager_dialogue.py，v10.0 新增）
==================================================
让客户经理「对话」基金经理：基于蒸馏的人设卡（履历/风格/投资范围/季报观点/新闻采访），
以基金经理口吻回答客户经理的问题。

回答优先级（逐级降级）：
  1. LLM 蒸馏 —— 配置 DEEPSEEK_API_KEY（.env）时，把季报观点/新闻改写为经理口吻；
  2. 规则组装 —— 从人设卡按意图抽取真实数据拼接回答；
  3. 模板兜底 —— 复用 invitation_engine / fund_advisor_speech 现有话术引擎。

所有回答自带免责声明：观点来自公开定期报告与新闻整理，非经理本人实时言论。

用法:
  from manager_dialogue import ManagerDialogue
  dlg = ManagerDialogue()
  print(dlg.chat(manager_name="张坤", question="你对后市怎么看？"))
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR.parent))  # scripts/（fund_advisor_paths / llm_providers）
sys.path.insert(0, str(SCRIPT_DIR))         # scripts/analysis/（manager_persona 同级）

from manager_persona import ManagerPersona  # noqa: E402

DISCLAIMER = ('（注：以上观点来源于该基金经理管理的基金定期报告及公开新闻/采访整理，'
              '非经理本人实时言论，仅供投顾参考，不构成投资建议。）')

# 意图 → 关键词
_INTENT_KEYWORDS: Dict[str, List[str]] = {
    'profile': ['自我介绍', '介绍', '是谁', '背景', '履历', '经历', '资历', '毕业', '学历', '从业'],
    'style': ['风格', '特点', '擅长', '偏好', '打法', '策略', '怎么投', '理念', '选股'],
    'holdings': ['持仓', '重仓', '买了什么', '仓位', '股票', '标的', '调仓', '前十', '十大'],
    'views': ['观点', '展望', '怎么看', '后市', '判断', '想法', '预期', '机会', '风险', '市场', '行情', '乐观', '谨慎'],
    'scope': ['范围', '目标', '能投', '投向', '限制', '基准', '合同'],
    'news': ['新闻', '采访', '访谈', '动态', '近况', '最近', '报道', '专访'],
    'perf': ['业绩', '表现', '收益', '回报', '回撤', '涨', '跌', '赚', '亏', '排名'],
    'comfort': ['安抚', '安慰', '套牢', '亏损', '怎么办', '割肉', '赎回'],
}


def detect_intent(question: str) -> str:
    """关键词意图识别"""
    q = question or ''
    for intent, kws in _INTENT_KEYWORDS.items():
        if any(kw in q for kw in kws):
            return intent
    return 'general'


def _load_llm_client():
    """读取 .env 的 DEEPSEEK_API_KEY，构造 LLMClient；无 key 返回 None"""
    try:
        key = os.environ.get('DEEPSEEK_API_KEY', '')
        if not key:
            env_path = Path(__file__).resolve().parent.parent.parent / '.env'
            if env_path.exists():
                for line in env_path.read_text(encoding='utf-8').splitlines():
                    line = line.strip()
                    if line.startswith('DEEPSEEK_API_KEY'):
                        key = line.split('=', 1)[1].strip().strip('"').strip("'")
                        break
        if not key:
            return None
        sys.path.insert(0, str(SCRIPT_DIR.parent))
        from llm_providers import LLMClient
        return LLMClient(
            base_url='https://api.deepseek.com',
            api_key=key,
            model=os.environ.get('DEEPSEEK_MODEL', 'deepseek-chat'),
            provider='deepseek',
            temperature=0.7,
            max_tokens=600,
            timeout=45,
        )
    except Exception:
        return None


class ManagerDialogue:
    """基金经理对话引擎"""

    def __init__(self, data_dir: Optional[Path] = None,
                 llm_client: Any = None, use_llm: bool = True):
        self.data_dir = Path(data_dir) if data_dir else None
        self.persona_engine = ManagerPersona(data_dir=self.data_dir)
        self.llm_client = llm_client if llm_client is not None else (_load_llm_client() if use_llm else None)

    # ── 主入口 ─────────────────────────────────────────────────

    def chat(self, manager_name: Optional[str] = None,
             manager_id: Optional[str] = None,
             fund_code: Optional[str] = None,
             question: str = '') -> str:
        """以经理口吻回答问题（找不到经理返回提示）"""
        persona = self.persona_engine.build(manager_name, manager_id, fund_code)
        if not persona:
            return (f'未找到基金经理「{manager_name or manager_id or fund_code}」。'
                    f'请确认姓名/代码，或先运行 update_data.py full 重建经理库。')
        intent = detect_intent(question)
        # 1) LLM 蒸馏（可选：有 key 且人设有观点/新闻时启用）
        has_source = (persona['data_availability'].get('has_views')
                      or persona['data_availability'].get('has_news'))
        if self.llm_client and has_source:
            text = self._llm_distill(persona, question, intent)
            if text:
                return text + '\n' + DISCLAIMER
        # 2) 规则组装
        answer = self._assemble_answer(persona, question, intent)
        return answer + '\n' + DISCLAIMER

    # ── LLM 蒸馏 ───────────────────────────────────────────────

    def _llm_distill(self, persona: dict, question: str, intent: str) -> str:
        """把人设卡内容蒸馏为经理口吻的回答"""
        try:
            v = persona['views'][0] if persona['views'] else {}
            news_lines = '\n'.join(f"- {n['title']}" for n in persona['news'][:4])
            system = ('你是一位公募基金经理。请以第一人称、口语化但专业克制的口吻，'
                      '基于【公开信息】回答理财经理的问题。不得编造公开信息之外的事实；'
                      '若信息不足，明说并给出一般性看法。结尾不要加免责声明。')
            prompt = (
                f"你的公开档案：{persona['name']}，{persona['company']}，"
                f"风格 {persona['style'].get('investment_style')}，"
                f"行业 {persona['style'].get('sector_description')}。\n"
                f"投资范围：{persona['scope'].get('investment_scope', '（无档案）')}\n"
                f"定期报告观点：{v.get('views', '')[:500]}\n"
                f"展望：{v.get('outlook', '')[:300]}\n"
                f"近期新闻：{news_lines or '（无）'}\n"
                f"客户经理问：{question}"
            )
            reply = self.llm_client.chat(
                [{"role": "user", "content": prompt}], system_prompt=system)
            reply = (reply or '').strip()
            return reply[:800] if reply else ''
        except Exception:
            return ''

    # ── 规则组装 ───────────────────────────────────────────────

    def _assemble_answer(self, persona: dict, question: str, intent: str) -> str:
        """按意图从人设卡抽取真实数据组装回答"""
        name = persona['name']
        if intent == 'profile':
            return self._answer_profile(persona)
        if intent == 'style':
            return self._answer_style(persona)
        if intent == 'holdings':
            return self._answer_holdings(persona)
        if intent == 'scope':
            return self._answer_scope(persona)
        if intent == 'news':
            return self._answer_news(persona)
        if intent == 'perf':
            return self._answer_perf(persona)
        if intent == 'views':
            return self._answer_views(persona)
        if intent == 'comfort':
            return self._answer_comfort(persona)
        return self._answer_general(persona, question)

    def _answer_profile(self, p: dict) -> str:
        prof = p['profile']
        L = [f"我是{p['name']}，目前在{p['company']}管理{p['fund']['name']}（{p['fund']['code']}）。"]
        bits = []
        if prof.get('tenure_years'):
            bits.append(f"从业约{prof['tenure_years']}年")
        if prof.get('total_scale'):
            bits.append(f"管理规模约{prof['total_scale']}")
        if prof.get('best_return'):
            bits.append(f"任职最佳回报{prof['best_return']}")
        if bits:
            L.append("背景上，" + '，'.join(bits) + "。")
        if prof.get('stage_description'):
            L.append(prof['stage_description'])
        if prof.get('education'):
            L.append(f"教育背景：{prof['education']}")
        return ' '.join(L)

    def _answer_style(self, p: dict) -> str:
        s = p['style']
        L = []
        if s.get('investment_style'):
            L.append(f"我的风格是{s['investment_style']}。")
        if s.get('sector_description'):
            L.append(s['sector_description'] + "。")
        if s.get('stock_pool'):
            pool = '、'.join(map(str, s['stock_pool'][:8]))
            L.append(f"股票池里主要关注：{pool}。")
        if s.get('investment_advice'):
            L.append(s['investment_advice'])
        if s.get('suitable_investors'):
            L.append(f"适合的投资者：{s['suitable_investors']}。")
        if not L:
            L.append("我的风格资料暂缺，等我更新档案后再细聊。")
        return ' '.join(L)

    def _answer_holdings(self, p: dict) -> str:
        code = p['fund']['code']
        try:
            from fund_advisor_paths import load_holdings
            rows = [r for r in load_holdings()
                    if str(r.get('fund_code', '')).zfill(6) == code][:10]
        except Exception:
            rows = []
        if not rows:
            return (f"我目前管理{p['fund']['name']}，最新季报重仓数据暂未入库。"
                    f"（提示：可先运行 update_data.py full 重建持仓数据）")
        L = [f"我管理的{p['fund']['name']}最新季报十大重仓："]
        for r in rows:
            L.append(f"  {r.get('stock_code', '')} {r.get('stock_name', '')} "
                     f"{r.get('weight', 0)}%")
        return '\n'.join(L)

    def _answer_scope(self, p: dict) -> str:
        sc = p['scope']
        if not sc.get('investment_scope') and not sc.get('investment_goal'):
            return (f"我管理的{p['fund']['name']}的合同投资范围档案暂缺。"
                    f"（提示：运行 fund_profile_collector.py 可补充投资目标/范围）")
        L = []
        if sc.get('investment_goal'):
            L.append(f"投资目标：{sc['investment_goal'][:150]}")
        if sc.get('investment_scope'):
            L.append(f"投资范围：{sc['investment_scope'][:250]}")
        if sc.get('benchmark'):
            L.append(f"业绩比较基准：{sc['benchmark'][:80]}")
        if sc.get('risk_level'):
            L.append(f"风险等级：{sc['risk_level'][:60]}")
        return '\n'.join(L)

    def _answer_views(self, p: dict) -> str:
        if not p['views']:
            return (f"我最新一期的定期报告观点暂未入库。"
                    f"（提示：运行 view_collector.py 可采集真实季报观点）")
        v = p['views'][0]
        title = v['report_title'] or v['report_date'] or '定期报告'
        L = [f"我在{title}中的看法："]
        if v.get('views'):
            L.append(f"【运作分析】{v['views'][:300]}")
        if v.get('outlook'):
            L.append(f"【后市展望】{v['outlook'][:300]}")
        return '\n'.join(L)

    def _answer_news(self, p: dict) -> str:
        if not p['news']:
            return (f"我最近的公开新闻/采访暂未入库。"
                    f"（提示：运行 manager_news_collector.py 可采集新闻采访）")
        L = [f"我近期的一些公开动态："]
        for n in p['news'][:5]:
            L.append(f"  [{n['type']}] {n['title']}（{n['date'] or n['source']}）")
        return '\n'.join(L)

    def _answer_perf(self, p: dict) -> str:
        prof = p['profile']
        L = []
        if prof.get('best_return'):
            L.append(f"我任职期间的最佳回报是{prof['best_return']}。")
        if prof.get('total_scale'):
            L.append(f"目前管理规模约{prof['total_scale']}。")
        if p['fund']['name']:
            L.append(f"具体到{p['fund']['name']}的区间业绩，可以参考最新净值与定期报告数据。")
        if not L:
            L.append("我的业绩数据暂缺。")
        return ' '.join(L)

    def _answer_comfort(self, p: dict) -> str:
        s = p['style']
        L = [f"理解大家持有{p['fund']['name']}过程中的波动感受。"]
        if s.get('risk_warning'):
            L.append(s['risk_warning'])
        L.append("市场短期波动是常态，我更关注组合的中长期回报与回撤控制。"
                 "建议结合自身风险承受能力与投资周期做决策，不必在恐慌中做操作。")
        return ' '.join(L)

    def _answer_general(self, p: dict, question: str) -> str:
        L = [f"关于「{question}」，我从公开信息能分享的是："]
        if p['views']:
            v = p['views'][0]
            text = (v.get('outlook') or v.get('views') or '').strip()
            L.append(text[:200] if text else '（该期报告暂未披露具体展望）')
        else:
            s = p['style']
            L.append(f"我整体是{s.get('investment_style', '均衡')}风格，"
                     f"{s.get('sector_description', '关注行业景气与估值匹配')}。")
        return ' '.join(L)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='基金经理对话')
    parser.add_argument('--name', type=str, default='', help='经理姓名')
    parser.add_argument('--fund', type=str, default='', help='基金代码')
    parser.add_argument('--question', type=str, default='你对后市怎么看？', help='问题')
    args = parser.parse_args()
    dlg = ManagerDialogue()
    print(dlg.chat(manager_name=args.name or None, fund_code=args.fund or None,
                   question=args.question))
