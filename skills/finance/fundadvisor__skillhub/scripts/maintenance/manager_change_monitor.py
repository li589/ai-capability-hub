#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基金经理变动监控（manager_change_monitor.py，v10.0 新增）
=========================================================
检测基金「基金经理变更」信号（持有人/跟仓客户重点关注）：

  1. 本地对比（离线，零依赖）：
     持仓库（holdings_database.json 的 mg，即披露季报时的经理）
     vs 经理蒸馏库（fund_managers_distilled.json 的 current_fund_code → name）
     不一致 → 经理已变更。
  2. 公告扫描（在线 best effort）：
     天天基金公告接口（JJGG）中标题含「基金经理」的 变更/离任/增聘/任职 公告。

输出 data/manager_changes.json：
  {"changes": [{fund_code, fund_name, old_manager, new_manager, source, date, detail}],
   "meta": {...}}
被 manager_follower.get_follow_signals 并入跟仓信号。

用法:
  python manager_change_monitor.py              # 本地对比
  python manager_change_monitor.py --online     # 本地对比 + 公告扫描
"""
from __future__ import annotations

import json
import sys
import time
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

SCRIPT_DIR = Path(__file__).resolve().parent
BASE_DIR = SCRIPT_DIR.parent.parent
sys.path.insert(0, str(BASE_DIR / "scripts"))

from fund_advisor_paths import DATA_DIR, load_json_data, load_holdings  # noqa: E402

_UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
       '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')


def _http_get(url: str, timeout: int = 12) -> str:
    try:
        req = urllib.request.Request(url, headers={'User-Agent': _UA,
                                                   'Referer': 'https://fundf10.eastmoney.com/'})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode('utf-8', errors='replace')
    except Exception:
        return ''


class ManagerChangeMonitor:
    """基金经理变动监控"""

    def __init__(self, data_dir: Optional[Path] = None):
        self.data_dir = Path(data_dir) if data_dir else DATA_DIR

    # ── 1. 本地对比 ─────────────────────────────────────────────

    def _load_managers(self) -> list:
        """读取经理蒸馏库（尊重 data_dir）"""
        try:
            path = self.data_dir / 'fund_managers_distilled.json'
            if not path.exists():
                return []
            data = load_json_data(str(path))
            return data.get('items') or data.get('managers') or []
        except Exception:
            return []

    def detect_local_changes(self) -> List[dict]:
        """持仓库披露经理 vs 经理库现任经理，不一致即视为变更信号"""
        changes: List[dict] = []
        # 现任经理：current_fund_code → name
        current: Dict[str, str] = {}
        try:
            for m in self._load_managers():
                fc = str(m.get('current_fund_code') or '').zfill(6)
                if fc.isdigit() and m.get('name'):
                    current.setdefault(fc, str(m['name']))
        except Exception:
            pass

        # 持仓库（披露季报时的经理）
        seen: set = set()
        for r in load_holdings(str(self.data_dir / 'holdings_database.json')):
            fc = str(r.get('fund_code') or '').zfill(6)
            if not fc or fc in seen:
                continue
            seen.add(fc)
            disclosed = r.get('manager_name', '')
            now = current.get(fc, '')
            if disclosed and now and disclosed != now:
                changes.append({
                    'fund_code': fc,
                    'fund_name': r.get('fund_name', ''),
                    'old_manager': disclosed,
                    'new_manager': now,
                    'source': '本地档案对比',
                    'date': '',
                    'detail': f'基金经理由 {disclosed} 变更为 {now}',
                })
        return changes

    # ── 2. 公告扫描（在线 best effort） ─────────────────────────

    def detect_announcements(self, fund_codes: Optional[List[str]] = None,
                             limit: int = 200) -> List[dict]:
        """扫描基金公告中的经理变更/增聘/离任标题"""
        codes = fund_codes or []
        if not codes:
            try:
                data = load_json_data('fund_managers_distilled.json')
                codes = sorted({str(m.get('current_fund_code', '')).zfill(6)
                                for m in (data.get('items') or data.get('managers') or [])
                                if str(m.get('current_fund_code', '')).isdigit()})[:limit]
            except Exception:
                return []
        changes: List[dict] = []
        for code in codes:
            url = ('http://api.fund.eastmoney.com/f10/JJGG'
                   f'?fundcode={code}&pageIndex=1&pageSize=20&type=1&_={int(time.time()*1000)}')
            text = _http_get(url)
            try:
                data = json.loads(text)
            except (json.JSONDecodeError, ValueError):
                continue
            for row in (data.get('Data') or []):
                title = str(row.get('TITLE', ''))
                if '基金经理' not in title:
                    continue
                if not any(kw in title for kw in ('变更', '离任', '增聘', '任职', '更换')):
                    continue
                date = str(row.get('PUBLISHDATEDesc') or row.get('PUBLISHDATE', ''))[:10]
                changes.append({
                    'fund_code': code,
                    'fund_name': '',
                    'old_manager': '',
                    'new_manager': '',
                    'source': '天天基金公告',
                    'date': date,
                    'detail': title,
                })
                break  # 每只基金一条最新公告即可
            time.sleep(0.05)
        return changes

    # ── 汇总与保存 ─────────────────────────────────────────────

    def run(self, online: bool = False, save: bool = True) -> Dict[str, Any]:
        changes = self.detect_local_changes()
        if online:
            changes += self.detect_announcements()
        result = {
            'changes': changes,
            'meta': {
                'count': len(changes),
                'mode': 'local+online' if online else 'local',
                'checked_at': datetime.now().isoformat(),
            },
        }
        if save:
            path = self.data_dir / 'manager_changes.json'
            path.write_text(json.dumps(result, ensure_ascii=False, indent=2),
                            encoding='utf-8')
            result['meta']['saved_to'] = str(path)
        return result


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='基金经理变动监控')
    parser.add_argument('--online', action='store_true', help='额外扫描公告（联网）')
    args = parser.parse_args()
    mon = ManagerChangeMonitor()
    out = mon.run(online=args.online)
    print(f"经理变动信号: {len(out['changes'])} 条（模式: {out['meta']['mode']}）")
    for c in out['changes'][:20]:
        print(f"  [{c['source']}] {c.get('fund_name') or c.get('fund_code')}: {c['detail']}")
