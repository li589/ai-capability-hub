#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
持仓历史归档（holdings_history.py，v10.0 新增）
================================================
holdings_database.json 只保留最新一季快照（quarter 仅在 meta）。跟仓/持仓变动对比
需要多季度历史，本模块在每次持仓刷新后把当前快照按季度归档到：

  data/holdings_history/{YYYYQN}.json   （紧凑格式，与 holdings_database 相同）

策略（v10.0「从现在积累」）：
  - 首次归档以当前季报为基线；
  - 之后每季刷新时，若该季度快照不存在则归档，存在则跳过（不覆写历史）；
  - 旧季度缺失是正常的（基线之前无数据），diff 从下一个季度开始可用。

零依赖（stdlib）。

用法:
  python holdings_history.py archive   # 归档当前快照
  python holdings_history.py list      # 列出已有季度
"""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

SCRIPT_DIR = Path(__file__).resolve().parent
BASE_DIR = SCRIPT_DIR.parent.parent
sys.path.insert(0, str(BASE_DIR / "scripts"))

from fund_advisor_paths import DATA_DIR, normalize_holdings  # noqa: E402

HISTORY_DIR_NAME = 'holdings_history'


def _history_dir(data_dir: Optional[Path] = None) -> Path:
    base = Path(data_dir) if data_dir else DATA_DIR
    return base / HISTORY_DIR_NAME


def current_quarter(data_dir: Optional[Path] = None) -> str:
    """读取当前持仓库的季度标识"""
    base = Path(data_dir) if data_dir else DATA_DIR
    path = base / 'holdings_database.json'
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
        meta = data.get('m', {}) if isinstance(data, dict) else {}
        return str(meta.get('quarter', ''))
    except Exception:
        return ''


def archive_current_holdings(data_dir: Optional[Path] = None) -> Optional[str]:
    """把当前持仓库快照归档到 holdings_history/{quarter}.json；已存在则跳过。

    Returns:
        归档文件路径（或 None：无数据/已存在/失败）
    """
    base = Path(data_dir) if data_dir else DATA_DIR
    src = base / 'holdings_database.json'
    if not src.exists():
        return None
    try:
        data = json.loads(src.read_text(encoding='utf-8'))
    except (json.JSONDecodeError, OSError):
        return None
    quarter = current_quarter(data_dir)
    if not quarter:
        quarter = datetime.now().strftime('%YQ%m')  # 兜底：按当前年月
    hdir = _history_dir(data_dir)
    hdir.mkdir(parents=True, exist_ok=True)
    dst = hdir / f'{quarter}.json'
    if dst.exists():
        return None  # 该季度已归档，不覆写历史
    dst.write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')
    return str(dst)


def list_history_quarters(data_dir: Optional[Path] = None) -> List[str]:
    """按时间升序列出已归档季度"""
    hdir = _history_dir(data_dir)
    if not hdir.exists():
        return []
    return sorted(p.stem for p in hdir.glob('*.json') if p.stem)


def load_quarter_snapshot(quarter: str, data_dir: Optional[Path] = None) -> Dict[str, Any]:
    """读取指定季度快照原始内容（不存在返回 {}）"""
    path = _history_dir(data_dir) / f'{quarter}.json'
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except (json.JSONDecodeError, OSError):
        return {}


def load_quarter_rows(quarter: str, data_dir: Optional[Path] = None) -> List[Dict[str, Any]]:
    """读取指定季度快照并归一化为股票级明细行"""
    return normalize_holdings(load_quarter_snapshot(quarter, data_dir))


def latest_two_quarters(data_dir: Optional[Path] = None) -> tuple:
    """返回 (最新季度, 次新季度)；不足两季返回 (最新, None)"""
    quarters = list_history_quarters(data_dir)
    if not quarters:
        return ('', None)
    latest = quarters[-1]
    prev = quarters[-2] if len(quarters) >= 2 else None
    return latest, prev


if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'archive'
    if cmd == 'archive':
        p = archive_current_holdings()
        print(f'归档: {p}' if p else '无新季度可归档（数据缺失或已存在）')
    elif cmd == 'list':
        print('已归档季度:', list_history_quarters() or '（暂无）')
    else:
        print(__doc__)
