"""
fund_advisor_paths.py — 全局路径、基础配置与 JSON 数据加载

所有脚本应从此模块导入路径常量，禁止散落硬编码。
支持标准 JSON 和列式压缩 JSON（透明解码）。
v8.0: 增加 LazyDataCache（LRU 缓存）+ sys.dont_write_bytecode 防 .pyc 再生。
"""
from __future__ import annotations

import json
import os
import sys
import time
import threading
from pathlib import Path
from typing import Optional, Any, Dict, List

# 禁止生成 .pyc 缓存文件（所有脚本通过此模块导入，生效范围最广）
sys.dont_write_bytecode = True


def _find_base_dir() -> Path:
    """推断 skill 根目录"""
    env = os.environ.get("FUND_ADVISOR_BASE_DIR")
    if env:
        return Path(env).resolve()

    here = Path(__file__).resolve().parent
    if (here.parent / "SKILL.md").exists():
        return here.parent

    try:
        from importlib.resources import files
        candidate = files("fund_advisor")
        if candidate is not None:
            return Path(str(candidate)).parent
    except (ImportError, ModuleNotFoundError):
        pass

    return Path.cwd()


BASE_DIR: Path = _find_base_dir()
"""skill 根目录（fund-advisor/）"""

DATA_DIR: Path = BASE_DIR / "data"
"""本地 JSON 数据库目录"""

SCRIPTS_DIR: Path = BASE_DIR / "scripts"
"""scripts 目录"""

ASSETS_DIR: Path = BASE_DIR / "assets"
"""图标等资源目录"""

REFERENCES_DIR: Path = BASE_DIR / "references"
"""API 文档目录"""

CLIENTS_DIR: Path = DATA_DIR / "clients"
"""客户持仓仓库目录"""


# ── LRU 缓存（减少重复 JSON 磁盘 I/O） ──────────────────────────────
class LazyDataCache:
    """线程安全 LRU 内存缓存，减少大型 JSON 文件的重复磁盘读取。

    用法:
        cache = LazyDataCache(max_size=5, ttl_seconds=3600)
        data = cache.get('fund_products.json')  # 首次读盘，后续走缓存
        cache.invalidate('fund_products.json')  # 强制下次重新读盘
    """

    def __init__(self, max_size: int = 5, ttl_seconds: int = 3600):
        self._max_size = max_size
        self._ttl = ttl_seconds
        self._cache: Dict[str, tuple] = {}  # key -> (timestamp, mtime, data)
        self._access_order: List[str] = []   # LRU 顺序（最近使用在末尾）
        self._lock = threading.Lock()

    @staticmethod
    def _file_mtime(filename: str) -> Optional[float]:
        """读取文件修改时间；文件不存在时返回 None。"""
        try:
            return os.path.getmtime(filename)
        except OSError:
            return None

    def get(self, filename: str) -> Optional[Dict[str, Any]]:
        """获取缓存数据，若过期或不存在返回 None。"""
        with self._lock:
            if filename in self._cache:
                ts, mtime, data = self._cache[filename]
                current_mtime = self._file_mtime(filename)
                if current_mtime is not None and mtime is not None and current_mtime != mtime:
                    # 文件已被更新，旧缓存立即失效，避免数据刷新后仍返回旧数据
                    del self._cache[filename]
                    self._access_order.remove(filename)
                    return None
                if time.time() - ts < self._ttl:
                    # 更新 LRU 顺序
                    self._access_order.remove(filename)
                    self._access_order.append(filename)
                    return data
                # 过期，移除
                del self._cache[filename]
                self._access_order.remove(filename)
        return None

    def set(self, filename: str, data: Dict[str, Any]) -> None:
        """写入缓存，超过 max_size 时淘汰最久未使用条目。"""
        with self._lock:
            if filename in self._cache:
                self._access_order.remove(filename)
            elif len(self._cache) >= self._max_size:
                oldest = self._access_order.pop(0)
                del self._cache[oldest]
            self._cache[filename] = (time.time(), self._file_mtime(filename), data)
            self._access_order.append(filename)

    def invalidate(self, filename: str) -> None:
        """强制失效指定缓存条目。"""
        with self._lock:
            if filename in self._cache:
                del self._cache[filename]
                self._access_order.remove(filename)

    def clear(self) -> None:
        """清空全部缓存。"""
        with self._lock:
            self._cache.clear()
            self._access_order.clear()

    @property
    def size(self) -> int:
        return len(self._cache)


# 模块级全局缓存实例
_data_cache = LazyDataCache(max_size=5, ttl_seconds=3600)


def ensure_dirs() -> None:
    """确保关键目录存在"""
    for d in (DATA_DIR, CLIENTS_DIR, DATA_DIR / "uploads"):
        d.mkdir(parents=True, exist_ok=True)


def relative_to_skill(path: Path) -> Optional[Path]:
    """把绝对路径转成相对 skill 根目录的路径"""
    try:
        return path.relative_to(BASE_DIR)
    except ValueError:
        return None


def is_columnar(data: Any) -> bool:
    """判断是否为列式压缩格式（新旧两种变体）"""
    if not isinstance(data, dict):
        return False
    f = data.get("_f")
    if f == "c":  # 旧版: {"_f":"c","c":[列名],"d":[行...],"m":{}}
        return True
    # 新版: {"_f":[列名...],"c":[列数组...],"m":{}}
    return isinstance(f, list) and isinstance(data.get("c"), list)


def _decode_columnar(data: dict, known_list_key: str = "items") -> dict:
    """解码列式压缩格式，兼容两种变体：

    旧版: {"_f":"c","c":[列名...],"d":[[行]...],"m":{...}}
    新版: {"_f":[列名...],"c":[[列数组]...],"m":{...}}（真列存，v6.1 起 fund_managers/fund_products 使用）
    """
    f = data.get("_f")
    meta = data.get("m", {})

    if isinstance(f, list):  # 新版列存
        columns = f
        col_arrays = data.get("c", [])
        n = len(col_arrays[0]) if col_arrays else 0
        items = [
            {columns[j]: col_arrays[j][i] for j in range(len(columns)) if j < len(col_arrays) and i < len(col_arrays[j])}
            for i in range(n)
        ]
        return {known_list_key: items, "meta": meta}

    # 旧版行式
    columns = data.get("c", [])
    rows = data.get("d", [])
    items = []
    for row in rows:
        item = {}
        for i, col_name in enumerate(columns):
            if i < len(row):
                item[col_name] = row[i]
        items.append(item)

    return {known_list_key: items, "meta": meta}


def normalize_holdings(data: Any) -> List[Dict[str, Any]]:
    """把 holdings_database.json 的各种历史格式统一为股票级明细行。

    返回: [{fund_code, fund_name, manager_name, company_name,
            stock_code, stock_name, weight}, ...]

    支持的输入格式:
      - v7.2+ 紧凑格式: {"h":[{"fc","fn","mg","co","ss":[[code,name,weight],...]}],"m":{}}
      - f/m 数组并行格式: {"f":[[code,name,manager,company,[codes],[weights]],...],"m":{}}
      - 全量刷新格式: {"holdings":[股票级dict...]} 或 {"by_manager":[基金级dict...]}
      - 股票级 dict 组成的裸列表
    """
    rows: List[Dict[str, Any]] = []
    if isinstance(data, list):
        entries = data
        for e in entries:
            if isinstance(e, dict) and ('stock_code' in e or 'fund_code' in e):
                rows.append(e)
        return rows

    if not isinstance(data, dict):
        return rows

    # v7.2+ 紧凑格式
    if isinstance(data.get('h'), list):
        for entry in data['h']:
            if not isinstance(entry, dict):
                continue
            fc, fn = entry.get('fc', ''), entry.get('fn', '')
            mg, co = entry.get('mg', ''), entry.get('co', '')
            for s in entry.get('ss', []):
                if isinstance(s, dict):  # 兼容 v5.5 的 dict 形式 {c,n,w}
                    rows.append({'fund_code': fc, 'fund_name': fn, 'manager_name': mg,
                                 'company_name': co, 'stock_code': s.get('c', ''),
                                 'stock_name': s.get('n', ''), 'weight': s.get('w', 0.0)})
                elif isinstance(s, (list, tuple)) and len(s) >= 2:
                    rows.append({'fund_code': fc, 'fund_name': fn, 'manager_name': mg,
                                 'company_name': co, 'stock_code': s[0], 'stock_name': s[1],
                                 'weight': s[2] if len(s) > 2 else 0.0})
        return rows

    # f/m 数组并行格式
    if isinstance(data.get('f'), list):
        for item in data['f']:
            if not isinstance(item, (list, tuple)) or len(item) < 5:
                continue
            fc, fn, mg, co = item[0], item[1], item[2], item[3]
            codes = item[4] or []
            weights = item[5] if len(item) > 5 and item[5] else []
            for i, sc in enumerate(codes):
                w = weights[i] if i < len(weights) else 0.0
                rows.append({'fund_code': str(fc).zfill(6), 'fund_name': fn,
                             'manager_name': mg, 'company_name': co,
                             'stock_code': sc, 'stock_name': '', 'weight': w})
        return rows

    # 全量刷新格式：股票级
    if isinstance(data.get('holdings'), list):
        return [e for e in data['holdings'] if isinstance(e, dict)]

    # 全量刷新格式：基金级（stocks 为 dict 列表）
    if isinstance(data.get('by_manager'), list):
        for entry in data['by_manager']:
            if not isinstance(entry, dict):
                continue
            for s in entry.get('stocks', []):
                if isinstance(s, dict):
                    rows.append({'fund_code': entry.get('fund_code', ''),
                                 'fund_name': entry.get('fund_name', ''),
                                 'manager_name': entry.get('manager_name', ''),
                                 'company_name': entry.get('company_name', ''),
                                 'stock_code': s.get('stock_code', ''),
                                 'stock_name': s.get('stock_name', ''),
                                 'weight': s.get('weight', 0.0)})
        return rows

    return rows


def load_holdings(filename: str = 'holdings_database.json') -> List[Dict[str, Any]]:
    """加载持仓数据库并统一为股票级明细行（见 normalize_holdings）。"""
    base = Path(filename)
    path = base if base.parent.parts else DATA_DIR / base
    if not path.exists():
        return []
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError, ValueError):
        return []
    return normalize_holdings(data)


# ── v10.0: 持仓历史（跟仓/持仓变动对比） ──────────────────────────
def list_holdings_history_quarters(data_dir: Optional[Path] = None) -> List[str]:
    """列出已归档的持仓季度快照（升序），如 ['2026Q1','2026Q2']。"""
    hdir = (Path(data_dir) if data_dir else DATA_DIR) / 'holdings_history'
    if not hdir.exists():
        return []
    return sorted(p.stem for p in hdir.glob('*.json') if p.stem)


def load_holdings_history(quarter: Optional[str] = None,
                          data_dir: Optional[Path] = None) -> List[Dict[str, Any]]:
    """加载持仓历史并统一为股票级明细行。

    quarter 指定时只返回该季度；否则返回全部季度（每行带 quarter 字段）。
    """
    hdir = (Path(data_dir) if data_dir else DATA_DIR) / 'holdings_history'
    quarters = [quarter] if quarter else list_holdings_history_quarters(data_dir)
    rows: List[Dict[str, Any]] = []
    for q in quarters:
        path = hdir / f'{q}.json'
        if not path.exists():
            continue
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError, ValueError):
            continue
        for r in normalize_holdings(data):
            r = dict(r)
            r['quarter'] = q
            rows.append(r)
    return rows


def load_json_data(filename: str, use_cache: bool = True) -> Dict[str, Any]:
    """
    加载 JSON 数据文件，透明支持标准格式和列式压缩格式。
    v8.0: 增加 LRU 缓存（use_cache=False 可跳过缓存强制重新读盘）。

    用法: load_json_data('fund_managers_distilled.json')
    """
    base = Path(filename)
    if base.parent == Path('.') or not base.parent.parts:
        path = DATA_DIR / base
    else:
        path = base

    if not path.exists():
        raise FileNotFoundError(f"数据文件不存在: {path}")

    # 尝试从缓存读取
    cache_key = str(path)
    if use_cache:
        cached = _data_cache.get(cache_key)
        if cached is not None:
            return cached

    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 检测并解码列式格式（新旧两种变体）
    if is_columnar(data):
        data = _decode_columnar(data)

    # 写入缓存
    if use_cache:
        _data_cache.set(cache_key, data)

    return data
