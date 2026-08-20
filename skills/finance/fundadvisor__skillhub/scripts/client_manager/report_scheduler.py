#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
客户报告订阅与批量生成（report_scheduler.py，v10.0 新增）
==========================================================
按客户要求「定制定期报告」：
  - 每个客户可订阅：报告频率 × 内容模块 × 模板；
  - 一键批量生成名下全部客户的报告（客户经理场景）；
  - 订阅配置存 data/report_subscriptions.json，批量产物存 data/reports/。

用法:
  from report_scheduler import ReportScheduler
  sched = ReportScheduler()
  sched.add_subscription("张先生", report_type="weekly",
                         modules=["news", "holdings", "manager_views", "risk"])
  summary = sched.generate_all()          # 批量生成
  report = sched.generate_one("张先生")    # 单个客户

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

from fund_advisor_paths import DATA_DIR  # noqa: E402


class ReportScheduler:
    """客户报告订阅与批量生成器"""

    def __init__(self, data_dir: Optional[Path] = None):
        self.data_dir = Path(data_dir) if data_dir else DATA_DIR
        self.subscriptions_path = self.data_dir / 'report_subscriptions.json'

    # ── 订阅管理 ───────────────────────────────────────────────

    def _load(self) -> dict:
        try:
            if self.subscriptions_path.exists():
                return json.loads(self.subscriptions_path.read_text(encoding='utf-8'))
        except Exception:
            pass
        return {'subscriptions': []}

    def _save(self, data: dict) -> None:
        self.subscriptions_path.parent.mkdir(parents=True, exist_ok=True)
        self.subscriptions_path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')

    def list_subscriptions(self) -> List[dict]:
        return self._load().get('subscriptions', [])

    def add_subscription(self, client_id: str, report_type: str = 'weekly',
                         modules: Optional[List[str]] = None,
                         template: str = 'standard', active: bool = True) -> dict:
        """新增/更新客户报告订阅"""
        subs = self.list_subscriptions()
        entry = {
            'client_id': client_id,
            'report_type': report_type,
            'modules': modules,          # None=用报告类型默认模块
            'template': template,
            'active': active,
            'updated_at': datetime.now().isoformat(),
        }
        for i, s in enumerate(subs):
            if s.get('client_id') == client_id:
                subs[i] = entry
                break
        else:
            subs.append(entry)
        self._save({'subscriptions': subs, 'updated_at': datetime.now().isoformat()})
        return entry

    def remove_subscription(self, client_id: str) -> bool:
        """删除客户订阅，返回是否确有删除"""
        before = self.list_subscriptions()
        subs = [s for s in before if s.get('client_id') != client_id]
        self._save({'subscriptions': subs, 'updated_at': datetime.now().isoformat()})
        return len(subs) < len(before)

    # ── 生成 ───────────────────────────────────────────────────

    def generate_one(self, client_id: str, report_type: str = None,
                     modules: Optional[List[str]] = None,
                     template: str = None) -> Dict[str, Any]:
        """按订阅配置生成单个客户报告；返回 {client_id, path, ok, error?}"""
        sub = next((s for s in self.list_subscriptions()
                    if s.get('client_id') == client_id), None)
        rtype = report_type or (sub or {}).get('report_type', 'weekly')
        mods = modules if modules is not None else (sub or {}).get('modules')
        tpl = template or (sub or {}).get('template', 'standard')
        try:
            from report_generator import ReportGenerator
            gen = ReportGenerator(data_dir=self.data_dir)
            content = gen.generate_report(user_id=client_id, report_type=rtype,
                                          modules=mods, template=tpl)
            path = gen.save_report(client_id, rtype, content=content,
                                   modules=mods, template=tpl)
            return {'client_id': client_id, 'report_type': rtype, 'ok': True,
                    'path': path, 'generated_at': datetime.now().isoformat()}
        except Exception as e:
            return {'client_id': client_id, 'report_type': rtype, 'ok': False,
                    'error': f'{type(e).__name__}: {e}'}

    def generate_all(self, active_only: bool = True) -> Dict[str, Any]:
        """批量生成所有订阅客户报告（客户经理一键周报）"""
        subs = self.list_subscriptions()
        if active_only:
            subs = [s for s in subs if s.get('active', True)]
        results = [self.generate_one(s['client_id']) for s in subs]
        ok = [r for r in results if r.get('ok')]
        return {
            'total': len(results),
            'success': len(ok),
            'failed': len(results) - len(ok),
            'results': results,
            'generated_at': datetime.now().isoformat(),
        }


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='客户报告订阅与批量生成')
    parser.add_argument('cmd', choices=['list', 'add', 'generate', 'generate-all'],
                        help='list=订阅列表 | add=新增订阅 | generate=生成单个 | generate-all=批量')
    parser.add_argument('--client', type=str, default='', help='客户ID')
    parser.add_argument('--type', type=str, default='weekly', help='报告频率')
    parser.add_argument('--modules', type=str, default='',
                        help='模块逗号分隔（news,holdings,manager_views,psychology,follow,allocation,outlook,risk）')
    parser.add_argument('--template', type=str, default='standard', help='standard/concise/professional')
    args = parser.parse_args()

    sched = ReportScheduler()
    if args.cmd == 'list':
        for s in sched.list_subscriptions():
            print(s)
    elif args.cmd == 'add':
        if not args.client:
            print('请用 --client 指定客户ID')
            sys.exit(1)
        mods = [m.strip() for m in args.modules.split(',') if m.strip()] or None
        print(sched.add_subscription(args.client, args.type, mods, args.template))
    elif args.cmd == 'generate':
        if not args.client:
            print('请用 --client 指定客户ID')
            sys.exit(1)
        print(sched.generate_one(args.client))
    else:
        print(sched.generate_all())
