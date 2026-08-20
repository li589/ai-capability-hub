#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基金经理人设卡构建器（manager_persona.py，v10.0 新增）
=====================================================
把分散的数据源蒸馏为「基金经理人设卡」，供经理对话（manager_dialogue）、
定制报告（manager_views 模块）与 MCP 工具使用：

  profile  → fund_managers_distilled.json   履历/风格/股票池/风险提示
  scope    → fund_products.json（v10 档案列）投资目标/投资范围/业绩比较基准
  views    → manager_views.json              最新季报观点（schema 兼容 fc/fund_code、v/views）
  news     → manager_news.json               新闻/采访/公告
  speeches → fund_managers_speech_by_company.json（存在时）人设话术

零依赖（stdlib）。数据缺失时逐节降级，persona 永远可用。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR.parent))
sys.path.insert(0, str(SCRIPT_DIR.parent.parent / "scripts"))

from fund_advisor_paths import DATA_DIR, load_json_data  # noqa: E402


def _normalize_view(view: Dict[str, Any]) -> Dict[str, Any]:
    """manager_views.json 新旧 schema 键归一化（fc/fund_code、v/views）"""
    return {
        'fund_code': str(view.get('fund_code') or view.get('fc') or ''),
        'fund_name': view.get('fund_name', ''),
        'report_date': view.get('report_date', view.get('date', '')),
        'report_title': view.get('report_title', ''),
        'views': view.get('views', view.get('v', '')),
        'outlook': view.get('outlook', ''),
        'performance': view.get('performance', ''),
        'quarter': view.get('quarter', ''),
        'source': view.get('source', ''),
    }


class ManagerPersona:
    """基金经理人设卡"""

    def __init__(self, data_dir: Optional[Path] = None):
        self.data_dir = Path(data_dir) if data_dir else DATA_DIR
        self._managers: List[dict] = []
        self._views: List[dict] = []
        self._news: List[dict] = []
        self._products: List[dict] = []
        self._speeches: dict = {}
        self._loaded = False

    # ── 数据加载 ───────────────────────────────────────────────

    def _read_json(self, fname: str, key: str) -> list:
        """从 self.data_dir 读取并解码（列式透明；文件缺失返回空列表）"""
        path = self.data_dir / fname
        if not path.exists():
            return []
        try:
            data = load_json_data(str(path))
            return data.get(key, data.get('items', []))
        except Exception:
            return []

    def _ensure_loaded(self):
        if self._loaded:
            return
        self._managers = self._read_json('fund_managers_distilled.json', 'managers')
        self._views = [_normalize_view(v) for v in
                       self._read_json('manager_views.json', 'views')
                       if isinstance(v, dict)]
        self._news = [n for n in self._read_json('manager_news.json', 'news')
                      if isinstance(n, dict)]
        self._products = self._read_json('fund_products.json', 'products')
        try:
            sdata = load_json_data(str(self.data_dir / 'fund_managers_speech_by_company.json'))
            if isinstance(sdata, dict):
                self._speeches = sdata
        except Exception:
            self._speeches = {}
        self._loaded = True

    # ── 经理定位 ───────────────────────────────────────────────

    def find_manager(self, manager_name: Optional[str] = None,
                     manager_id: Optional[str] = None,
                     fund_code: Optional[str] = None) -> Optional[dict]:
        """按 姓名/ID/现任基金代码 定位经理（姓名支持模糊）"""
        self._ensure_loaded()
        if not any([manager_name, manager_id, fund_code]):
            return None
        code = str(fund_code or '').zfill(6)
        for m in self._managers:
            if manager_id and str(m.get('manager_id') or '') == str(manager_id):
                return m
        for m in self._managers:
            if code and str(m.get('current_fund_code') or '').zfill(6) == code:
                return m
        if manager_name:
            name = str(manager_name).strip()
            for m in self._managers:
                if str(m.get('name', '')) == name:
                    return m
            for m in self._managers:
                if name and name in str(m.get('name', '')):
                    return m
        return None

    # ── 人设构建 ───────────────────────────────────────────────

    def build(self, manager_name: Optional[str] = None,
              manager_id: Optional[str] = None,
              fund_code: Optional[str] = None) -> Optional[dict]:
        """构建人设卡；找不到经理返回 None"""
        mgr = self.find_manager(manager_name, manager_id, fund_code)
        if not mgr:
            return None
        self._ensure_loaded()
        name = str(mgr.get('name', ''))
        mid = str(mgr.get('manager_id') or mgr.get('code') or '')
        fcode = str(mgr.get('current_fund_code') or '').zfill(6)
        fname = str(mgr.get('current_fund_name') or '')

        # 投资范围/目标（来自产品档案 v10 列）
        scope: Dict[str, Any] = {}
        for p in self._products:
            if str(p.get('code') or '').zfill(6) == fcode:
                for k in ('investment_goal', 'investment_scope', 'investment_strategy',
                          'benchmark', 'risk_level', 'inception_date', 'scale'):
                    if p.get(k):
                        scope[k] = p[k]
                break

        # 最新观点（按报告日期倒序取前 3）
        views = [v for v in self._views
                 if v['fund_code'] == fcode or v.get('fund_name') == fname]
        views.sort(key=lambda v: v['report_date'], reverse=True)

        # 新闻/采访（按经理 ID 或姓名匹配）
        news = [n for n in self._news
                if n.get('manager_id') == mid or n.get('manager_name') == name]

        # 话术（speech DB，存在时）
        speech: Dict[str, Any] = {}
        if self._speeches:
            for company, blob in self._speeches.items():
                if not isinstance(blob, dict):
                    continue
                for key, item in (blob.items() if isinstance(blob, dict) else []):
                    if isinstance(item, dict) and item.get('name') == name:
                        speech = item
                        break
                if speech:
                    break

        tenure_days = mgr.get('tenure_days') or 0
        try:
            tenure_years = round(float(tenure_days) / 365, 1)
        except (TypeError, ValueError):
            tenure_years = mgr.get('tenure_years', 0)

        return {
            'manager_id': mid,
            'name': name,
            'company': mgr.get('company_name', ''),
            'fund': {'code': fcode, 'name': fname},
            'profile': {
                'tenure_years': tenure_years,
                'total_scale': mgr.get('total_scale', ''),
                'best_return': mgr.get('best_return', ''),
                'work_years': mgr.get('work_years', ''),
                'education': mgr.get('education', ''),
                'fund_stage': mgr.get('fund_stage', ''),
                'stage_description': mgr.get('stage_description', ''),
                'star_rating': mgr.get('star_rating', ''),
            },
            'style': {
                'investment_style': mgr.get('investment_style', ''),
                'sector_description': mgr.get('sector_description', ''),
                'sectors': mgr.get('sectors') or [],
                'stock_pool': mgr.get('stock_pool') or [],
                'investment_advice': mgr.get('investment_advice', ''),
                'risk_warning': mgr.get('risk_warning', ''),
                'suitable_investors': mgr.get('suitable_investors', ''),
                'investment_period': mgr.get('investment_period', ''),
            },
            'scope': scope,
            'views': views[:3],
            'news': news[:6],
            'speech': speech,
            'data_availability': {
                'has_scope': bool(scope),
                'has_views': bool(views),
                'has_news': bool(news),
                'has_speech': bool(speech),
            },
        }

    # ── 渲染 ───────────────────────────────────────────────────

    def format_persona(self, persona: dict) -> str:
        """渲染为人设卡文本"""
        L: List[str] = []
        L.append(f"【{persona['name']}】人设卡")
        L.append(f"  公司: {persona['company']} | 现任基金: {persona['fund']['name']}({persona['fund']['code']})")
        p = persona['profile']
        bits = []
        if p.get('tenure_years'):
            bits.append(f"从业 {p['tenure_years']} 年")
        if p.get('total_scale'):
            bits.append(f"管理规模 {p['total_scale']}")
        if p.get('best_return'):
            bits.append(f"最佳回报 {p['best_return']}")
        if bits:
            L.append("  履历: " + ' | '.join(bits))
        s = persona['style']
        if s.get('investment_style'):
            L.append(f"  风格: {s['investment_style']}")
        if s.get('sector_description'):
            L.append(f"  行业: {s['sector_description']}")
        if s.get('stock_pool'):
            L.append(f"  股票池: {', '.join(map(str, s['stock_pool'][:8]))}")
        sc = persona['scope']
        if sc.get('investment_goal'):
            L.append(f"  投资目标: {sc['investment_goal'][:120]}")
        if sc.get('investment_scope'):
            L.append(f"  投资范围: {sc['investment_scope'][:200]}")
        if sc.get('benchmark'):
            L.append(f"  业绩比较基准: {sc['benchmark'][:80]}")
        if persona['views']:
            v = persona['views'][0]
            L.append(f"  最新观点({v['report_title'] or v['report_date'] or '定期报告'}):")
            text = (v.get('views') or v.get('outlook') or '').strip()
            L.append(f"    {text[:200]}")
        if persona['news']:
            L.append("  近期新闻/采访:")
            for n in persona['news'][:3]:
                L.append(f"    [{n['type']}] {n['title']} ({n['date'] or n['source']})")
        L.append("  ── 风险提示 ──")
        L.append(f"  {s.get('risk_warning', '市场有风险，投资需谨慎。')}")
        return '\n'.join(L)


if __name__ == '__main__':
    import sys as _s
    name = _s.argv[1] if len(_s.argv) > 1 else ''
    p = ManagerPersona()
    persona = p.build(manager_name=name) if name else p.build(fund_code=_s.argv[2] if len(_s.argv) > 2 else None)
    if not persona:
        print(f"未找到经理: {name or _s.argv[2] if len(_s.argv) > 2 else ''}")
    else:
        print(p.format_persona(persona))
