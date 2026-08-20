#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基金经理跟仓引擎（manager_follower.py，v10.0 新增）
====================================================
围绕「跟仓」场景的四类能力：

  1. diff_fund_holdings      — 同一只基金两个季度的十大重仓变动（新增/剔除/加仓/减仓）
  2. build_mirror_portfolio  — 按最新季报十大重仓构建「镜像组合」（加权/等权）
  3. track_mirror_performance— 镜像组合跟踪（基金净值近似 + 当日行情估算）
  4. get_follow_signals      — 跟仓信号（持仓变动 + 经理变动监控结果 + 置信度）

数据依赖：holdings_database.json（最新季）+ holdings_history/ 季度历史（v10.0 起积累）。
所有输出自带合规风险提示（披露滞后/集中度/申赎成本），不构成投资建议。

零依赖（stdlib；联网行情 best effort，失败自动降级）。
"""
from __future__ import annotations

import json
import re
import sys
import time
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR.parent))
sys.path.insert(0, str(SCRIPT_DIR.parent.parent / "scripts"))

from fund_advisor_paths import (DATA_DIR, load_holdings, load_holdings_history,  # noqa: E402
                                load_json_data)
import data_collection.holdings_history as hh  # noqa: E402

COMPLIANCE_DISCLAIMER = (
    '⚠️ 跟仓风险提示：① 季报披露滞后（通常滞后 1-2 个季度），经理实际持仓可能已变动；'
    '② 十大重仓仅覆盖组合一部分（其余为债券/现金/其他），镜像≠基金本身；'
    '③ 跟仓涉及申赎成本与个股集中度风险，请结合客户风险承受能力评估；'
    '④ 以上仅为投顾参考，不构成投资建议。')

_QUOTE_API = ('https://push2.eastmoney.com/api/qt/ulist.np/get?fltt=2&fields=f2,f3,f12,f14'
              '&secids={secids}')
_UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
       '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')


def _http_get(url: str, timeout: int = 8) -> str:
    try:
        req = urllib.request.Request(url, headers={'User-Agent': _UA, 'Referer': 'https://quote.eastmoney.com/'})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode('utf-8', errors='replace')
    except Exception:
        return ''


def _zfill6(code: Any) -> str:
    return str(code or '').strip().zfill(6)


def _rows_by_fund(rows: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """股票级明细行 → {fund_code: [行...]}"""
    out: Dict[str, List[Dict[str, Any]]] = {}
    for r in rows:
        fc = _zfill6(r.get('fund_code'))
        if fc:
            out.setdefault(fc, []).append(r)
    return out


class ManagerFollower:
    """基金经理跟仓引擎"""

    def __init__(self, data_dir: Optional[Path] = None):
        self.data_dir = Path(data_dir) if data_dir else DATA_DIR
        self._nav_cache = None

    def _load_current_rows(self) -> List[Dict[str, Any]]:
        """读取当前持仓库（尊重 data_dir）"""
        return load_holdings(str(self.data_dir / 'holdings_database.json'))

    def _load_managers(self) -> List[dict]:
        """读取经理蒸馏库（尊重 data_dir）"""
        try:
            path = self.data_dir / 'fund_managers_distilled.json'
            if not path.exists():
                return []
            data = load_json_data(str(path))
            return data.get('items') or data.get('managers') or []
        except Exception:
            return []

    def _get_nav_cache(self):
        """净值缓存（尊重 data_dir，避免测试/多实例污染默认路径）"""
        if self._nav_cache is None:
            try:
                from data_collection.nav_cache import NavCache
                self._nav_cache = NavCache(self.data_dir / 'nav_cache.db')
            except Exception:
                self._nav_cache = None
        return self._nav_cache

    # ── 1. 持仓变动对比 ─────────────────────────────────────────

    @staticmethod
    def diff_holdings(prev_rows: List[Dict[str, Any]],
                      curr_rows: List[Dict[str, Any]]) -> Dict[str, Any]:
        """同一只基金两个季度十大重仓的变动 diff。

        Args:
            prev_rows/curr_rows: 该基金的股票级明细行（含 stock_code/stock_name/weight）

        Returns:
            {added:[...], removed:[...], increased:[...], decreased:[...], kept:[...],
             summary, moves: topN 变动}
        """
        prev = {_zfill6(r.get('stock_code')): r for r in prev_rows}
        curr = {_zfill6(r.get('stock_code')): r for r in curr_rows}
        added, removed, increased, decreased, kept = [], [], [], [], []
        for code, r in curr.items():
            name = r.get('stock_name') or code
            w = float(r.get('weight') or 0)
            if code not in prev:
                added.append({'stock_code': code, 'stock_name': name, 'weight': w})
            else:
                pw = float(prev[code].get('weight') or 0)
                item = {'stock_code': code, 'stock_name': name,
                        'prev_weight': pw, 'weight': w,
                        'change': round(w - pw, 2)}
                if w > pw + 0.01:
                    increased.append(item)
                elif w < pw - 0.01:
                    decreased.append(item)
                else:
                    kept.append(item)
        for code, r in prev.items():
            if code not in curr:
                removed.append({'stock_code': code,
                                'stock_name': r.get('stock_name') or code,
                                'prev_weight': float(r.get('weight') or 0)})
        for lst in (added, removed, increased, decreased):
            lst.sort(key=lambda x: -abs(x.get('change', x.get('weight', 0)) or
                                        x.get('prev_weight', 0)))
        return {
            'added': added, 'removed': removed,
            'increased': increased, 'decreased': decreased, 'kept': kept,
            'summary': {
                'added_count': len(added), 'removed_count': len(removed),
                'increased_count': len(increased), 'decreased_count': len(decreased),
                'kept_count': len(kept),
                'turnover': round((len(added) + len(removed)) /
                                  max(len(prev) + len(curr), 1), 3),
            },
            'moves': (added + removed + increased + decreased)[:10],
        }

    def diff_fund_holdings(self, fund_code: str,
                           q1: Optional[str] = None,
                           q2: Optional[str] = None) -> Dict[str, Any]:
        """对比基金在 q1→q2 两个季度的重仓变化（缺省用历史最新两季）"""
        code = _zfill6(fund_code)
        if not q2:
            q2 = hh.current_quarter(self.data_dir) or (
                hh.list_history_quarters(self.data_dir) or [''])[-1]
        if not q1:
            quarters = hh.list_history_quarters(self.data_dir)
            q1 = quarters[-2] if len(quarters) >= 2 else None
        if not q1:
            return {'fund_code': code, 'error': 'no_history',
                    'message': '暂无历史季度快照，已建立基线（从现在积累，下一季起可对比）',
                    'quarters': [q2] if q2 else []}
        prev_rows = [r for r in hh.load_quarter_rows(q1, self.data_dir)
                     if _zfill6(r.get('fund_code')) == code]
        curr_rows = [r for r in hh.load_quarter_rows(q2, self.data_dir)
                     if _zfill6(r.get('fund_code')) == code]
        diff = self.diff_holdings(prev_rows, curr_rows)
        diff.update({'fund_code': code, 'quarters': [q1, q2], 'quarter': q2})
        return diff

    # ── 2. 镜像组合 ─────────────────────────────────────────────

    def build_mirror_portfolio(self, fund_code: str, mode: str = 'weighted',
                               max_holdings: int = 10,
                               total_amount: float = 100000.0) -> Dict[str, Any]:
        """按最新季报十大重仓构建镜像组合。

        mode: 'weighted' 按披露权重（未披露部分记为现金/其他），
              'equal' 等权分摊（股票部分均分，其余为现金/其他）。
        """
        code = _zfill6(fund_code)
        rows = [r for r in self._load_current_rows()
                if _zfill6(r.get('fund_code')) == code][:max_holdings]
        if not rows:
            return {'fund_code': code, 'error': 'no_holdings',
                    'message': f'基金 {code} 暂无最新季报重仓数据（请先 update_data.py full）'}
        quarter = hh.current_quarter(self.data_dir)
        if mode == 'equal':
            n = len(rows)
            positions = [{'stock_code': _zfill6(r.get('stock_code')),
                          'stock_name': r.get('stock_name') or '',
                          'mirror_weight': round(100.0 / n, 2)} for r in rows]
            stock_sum = 100.0
        else:
            positions = [{'stock_code': _zfill6(r.get('stock_code')),
                          'stock_name': r.get('stock_name') or '',
                          'mirror_weight': round(float(r.get('weight') or 0), 2)}
                         for r in rows]
            stock_sum = round(sum(p['mirror_weight'] for p in positions), 2)
        weights = [p['mirror_weight'] for p in positions]
        top1 = max(weights) if weights else 0
        top3 = round(sum(sorted(weights, reverse=True)[:3]), 2)
        top5 = round(sum(sorted(weights, reverse=True)[:5]), 2)
        herfindahl = round(sum((w / 100) ** 2 for w in weights), 4) if weights else 0.0
        cash_ratio = round(max(100.0 - stock_sum, 0.0), 2)

        amount = max(float(total_amount or 0), 0.0)
        for p in positions:
            p['amount_breakdown'] = round(amount * p['mirror_weight'] / 100.0, 2)

        warnings = []
        if top1 >= 30:
            warnings.append(f'第一大重仓占比 {top1:.1f}%，个股集中度高')
        if top3 >= 60:
            warnings.append(f'前三大重仓合计 {top3:.1f}%，组合集中度偏高')
        if herfindahl >= 0.25:
            warnings.append(f'持仓分散度不足（HHI={herfindahl:.3f}）')
        if cash_ratio > 20:
            warnings.append(f'十大重仓未覆盖 {cash_ratio:.1f}%（债券/现金/其他），镜像误差大')

        return {
            'fund_code': code,
            'fund_name': rows[0].get('fund_name', ''),
            'manager_name': rows[0].get('manager_name', ''),
            'mode': mode,
            'quarter': quarter,
            'positions': positions,
            'stock_weight_sum': stock_sum,
            'cash_ratio': cash_ratio,
            'concentration': {'top1': top1, 'top3': top3, 'top5': top5,
                              'herfindahl': herfindahl},
            'total_amount': amount,
            'warnings': warnings,
            'disclaimer': COMPLIANCE_DISCLAIMER,
        }

    # ── 3. 镜像组合跟踪 ─────────────────────────────────────────

    def track_mirror_performance(self, fund_code: str, portfolio: Optional[dict] = None,
                                 days: int = 30) -> Dict[str, Any]:
        """跟踪镜像组合表现：基金净值周期收益（近似）+ 当日行情估算（best effort）。

        净值可用时标注 approximated=True（镜像与基金非一一对应）；
        净值不可用时以基金当日估算/行情代替并标注 degraded。
        """
        code = _zfill6(fund_code)
        portfolio = portfolio or self.build_mirror_portfolio(code)
        if portfolio.get('error'):
            return portfolio
        end = datetime.now()
        start = end - timedelta(days=days)

        fund_return: Optional[float] = None
        nav_series: List[float] = []
        try:
            cache = self._get_nav_cache()
            if cache is not None:
                nav_series = cache.get_nav_series(code, start.strftime('%Y-%m-%d'),
                                                  end.strftime('%Y-%m-%d')) or []
                if len(nav_series) >= 2:
                    fund_return = round((nav_series[-1] / nav_series[0] - 1) * 100, 2)
        except Exception:
            pass

        # 当日行情估算（best effort）
        stock_quotes: List[Dict[str, Any]] = []
        codes = [p['stock_code'] for p in portfolio.get('positions', [])]
        if codes:
            secids = ','.join(f'1.{c}' for c in codes[:15])
            text = _http_get(_QUOTE_API.format(secids=secids))
            try:
                data = json.loads(text)
                for item in ((data.get('data') or {}).get('diff') or []):
                    stock_quotes.append({
                        'stock_code': str(item.get('f12', '')),
                        'stock_name': item.get('f14', ''),
                        'price': item.get('f2'),
                        'day_change_pct': item.get('f3'),
                    })
            except (json.JSONDecodeError, ValueError):
                pass
        if stock_quotes:
            by_code = {_zfill6(q['stock_code']): q for q in stock_quotes}
            total_day = 0.0
            used = 0
            for p in portfolio.get('positions', []):
                q = by_code.get(p['stock_code'])
                if q and isinstance(q.get('day_change_pct'), (int, float)):
                    total_day += p['mirror_weight'] / 100.0 * q['day_change_pct']
                    used += 1
            if used:
                portfolio = dict(portfolio)
                portfolio['day_change_estimate_pct'] = round(total_day, 2)
                portfolio['day_change_quotes_used'] = used

        return {
            'fund_code': code,
            'fund_name': portfolio.get('fund_name', ''),
            'period_days': days,
            'period': f'{start:%Y-%m-%d} ~ {end:%Y-%m-%d}',
            'fund_nav_return_pct': fund_return,
            'approximated': fund_return is not None,
            'degraded': fund_return is None and not stock_quotes,
            'day_change_estimate_pct': portfolio.get('day_change_estimate_pct'),
            'stock_quotes': stock_quotes[:15],
            'note': ('镜像组合表现以基金净值为近似（十大重仓≠全部持仓）；'
                     '当日估算基于重仓股行情，仅供参考。'),
        }

    # ── 4. 跟仓信号 ─────────────────────────────────────────────

    def get_follow_signals(self, fund_codes: Optional[List[str]] = None,
                           include_manager_change: bool = True) -> Dict[str, Any]:
        """生成跟仓信号列表。

        fund_codes: 关注的基金代码列表（缺省=全部有持仓数据的基金）
        每只基金一条信号：持仓变动摘要 + 置信度 + （可选）经理变动告警。
        """
        # 可用季度
        quarters = hh.list_history_quarters(self.data_dir)
        curr_q = hh.current_quarter(self.data_dir) or (quarters[-1] if quarters else '')

        # 全量持仓 → 基金集合
        all_rows = self._load_current_rows()
        by_fund = _rows_by_fund(all_rows)
        if fund_codes:
            targets = [_zfill6(c) for c in fund_codes]
        else:
            targets = sorted(by_fund.keys())

        # 经理变更监控结果（manager_change_monitor.py 产物，存在时并入）
        manager_changes: List[dict] = []
        try:
            mc_path = self.data_dir / 'manager_changes.json'
            if mc_path.exists():
                mc = json.loads(mc_path.read_text(encoding='utf-8'))
                manager_changes = mc.get('changes', [])
        except Exception:
            pass

        signals: List[Dict[str, Any]] = []
        for code in targets:
            rows = by_fund.get(code, [])
            if not rows:
                continue
            fund_name = rows[0].get('fund_name', '')
            manager_name = rows[0].get('manager_name', '')

            # 季度对比
            diff = self.diff_fund_holdings(code)
            if diff.get('error'):
                sig: Dict[str, Any] = {
                    'fund_code': code, 'fund_name': fund_name,
                    'manager_name': manager_name,
                    'level': 'info',
                    'signal': 'baseline',
                    'message': '已建立持仓基线，下一季度起可对比变动',
                    'confidence': 'low',
                    'quarter': curr_q,
                }
            else:
                s = diff['summary']
                moves = diff['moves'][:5]
                move_text = '；'.join(
                    f"{m['stock_name']}{'+' if m.get('change', 0) > 0 else '-'}"
                    f"{abs(m.get('change', m.get('weight', 0))):.1f}%"
                    if 'change' in m else
                    f"新增{m['stock_name']}({m.get('weight', 0):.1f}%)"
                    for m in moves)
                level = 'high' if s['turnover'] >= 0.3 or s['added_count'] >= 3 else \
                    ('medium' if s['turnover'] >= 0.1 else 'low')
                sig = {
                    'fund_code': code, 'fund_name': fund_name,
                    'manager_name': manager_name,
                    'level': level,
                    'signal': 'holdings_change',
                    'quarter': diff.get('quarters', ['', ''])[1],
                    'prev_quarter': diff.get('quarters', ['', ''])[0],
                    'summary': s,
                    'top_moves': moves,
                    'message': (f'{fund_name} 十大重仓变动：新增{s["added_count"]}只、'
                                f'剔除{s["removed_count"]}只、加仓{s["increased_count"]}只、'
                                f'减仓{s["decreased_count"]}只'
                                + (f'。主要变动：{move_text}' if move_text else '')),
                    'confidence': 'high' if level == 'high' else
                                  ('medium' if level == 'medium' else 'low'),
                }

            # 经理变动告警
            if include_manager_change and manager_name:
                change = next((c for c in manager_changes
                               if _zfill6(c.get('fund_code')) == code), None)
                if change:
                    sig = dict(sig)
                    sig['manager_change'] = change
                    sig['level'] = 'high'
                    sig['signal'] = 'manager_change'
                    sig['message'] = (f'{fund_name} 经理变动：{change.get("detail", "")} '
                                      f'（原经理 {change.get("old_manager", "")} → '
                                      f'{change.get("new_manager", manager_name)}）')
            signals.append(sig)

        signals.sort(key=lambda x: {'high': 0, 'medium': 1, 'low': 2, 'info': 3}
                     .get(x.get('level'), 3))
        return {
            'signals': signals,
            'meta': {
                'quarter': curr_q,
                'history_quarters': quarters,
                'generated_at': datetime.now().isoformat(),
                'count': len(signals),
            },
            'disclaimer': COMPLIANCE_DISCLAIMER,
        }


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='基金经理跟仓引擎')
    parser.add_argument('cmd', choices=['diff', 'mirror', 'track', 'signals'],
                        help='diff=持仓变动 | mirror=镜像组合 | track=跟踪 | signals=信号')
    parser.add_argument('--fund', type=str, default='', help='基金代码')
    parser.add_argument('--mode', type=str, default='weighted', help='镜像模式 weighted/equal')
    parser.add_argument('--amount', type=float, default=100000, help='跟仓金额')
    args = parser.parse_args()
    f = ManagerFollower()
    if args.cmd == 'diff':
        print(json.dumps(f.diff_fund_holdings(args.fund), ensure_ascii=False, indent=2))
    elif args.cmd == 'mirror':
        print(json.dumps(f.build_mirror_portfolio(args.fund, mode=args.mode,
                                                  total_amount=args.amount),
                         ensure_ascii=False, indent=2))
    elif args.cmd == 'track':
        print(json.dumps(f.track_mirror_performance(args.fund), ensure_ascii=False, indent=2))
    else:
        print(json.dumps(f.get_follow_signals(), ensure_ascii=False, indent=2))
