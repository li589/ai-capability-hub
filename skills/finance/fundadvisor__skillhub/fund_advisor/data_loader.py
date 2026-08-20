"""
data_loader.py — 统一数据加载器 v3.1

支持三种 JSON 格式：
1. 标准格式：{"key": [{...}, ...], "meta": {...}}
2. 旧列式格式：{"_f": "c", "c": [列名], "d": [[行], ...], "m": {...}}
3. 新列式格式：{"_f": [列名], "c": [[列数组], ...], "m": {...}}（v6.1 起）
   自动还原为标准格式，体积减少 30-50%。
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

# 复用 fund_advisor_paths 的列式解码逻辑，避免重复实现
import sys, os
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from fund_advisor_paths import (  # noqa: E402
    _data_cache,
    _decode_columnar,
    is_columnar,
    load_json_data,
)


def load_json_cached(file_path, encoding="utf-8", max_cache_mb=50):
    """带 LRU 内存缓存的 JSON 加载（统一委托 fund_advisor_paths 的线程安全 LRU）。"""
    if max_cache_mb <= 0:
        return load_json_data(str(file_path), use_cache=False)
    return load_json_data(str(file_path), use_cache=True)


def clear_cache():
    """清空全局 LRU 缓存"""
    return _data_cache.clear()


def load_json(file_path: str | Path, encoding: str = "utf-8") -> Any:
    """
    加载 JSON 文件，自动识别并解码列式格式（新旧两种变体）。

    自动还原为 {"key":[{...},...],"meta":{...}}
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"数据文件不存在: {path}")

    with open(path, "r", encoding=encoding) as f:
        data = json.load(f)

    # 检测列式格式并解码
    if is_columnar(data):
        return _decode_columnar(data)

    return data


def get_data_path(data_dir: str | Path, filename: str) -> Path:
    """
    获取数据文件的完整路径。
    """
    base = Path(data_dir)
    return base / filename


def compress_json_file(file_path: str | Path, remove_original: bool = False) -> Path:
    """
    将 JSON 文件压缩为列式格式（节省 30-50% 体积）。

    Returns:
        压缩后的文件路径
    """
    path = Path(file_path)

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 查找列表键
    list_key = None
    for k, v in data.items():
        if isinstance(v, list) and len(v) > 0 and isinstance(v[0], dict):
            list_key = k
            break

    if list_key is None:
        raise ValueError(f"未找到可压缩的列表数据: {path}")

    records = data[list_key]
    columns = list(records[0].keys())
    rows = [[rec.get(col) for col in columns] for rec in records]

    result = {
        "_f": "c",
        "c": columns,
        "d": rows,
        "m": data.get("meta", data.get("_meta", {})),
    }

    with open(path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, separators=(",", ":"))

    return path


def compress_all_data(data_dir: str | Path) -> dict:
    """
    列式压缩数据目录中的所有 JSON 文件。

    Returns:
        压缩结果 {filename: {"original": size, "compressed": size, "ratio": percent}}
    """
    base = Path(data_dir)
    results = {}

    for json_file in base.glob("*.json"):
        original_size = json_file.stat().st_size
        compress_json_file(json_file)
        compressed_size = json_file.stat().st_size

        results[json_file.name] = {
            "original": original_size,
            "compressed": compressed_size,
            "ratio": f"{compressed_size * 100 // original_size}%"
        }

    return results
