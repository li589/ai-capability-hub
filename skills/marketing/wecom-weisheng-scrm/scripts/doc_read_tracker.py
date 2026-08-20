#!/usr/bin/env python3
"""文档已读缓存管理模块。

将 AI 已读文档的状态持久化到本地文件系统，供后续命令（如 call-api）校验
"AI 是否已读过该文档"。缓存文件以 ``md5(doc_url).json`` 命名，
存放在 ``.cache/doc_reads/`` 目录下。

@author jzc
@date 2026-05-24 18:36
"""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any, Optional

from utils import SKILL_ROOT, ensure_dir

# 缓存目录
CACHE_DIR: Path = SKILL_ROOT / ".cache" / "doc_reads"

# 默认缓存有效期（秒），2 小时
DEFAULT_TTL: int = 7200


def _cache_path(doc_url: str) -> Path:
    """根据 doc_url 的 MD5 生成缓存文件路径。

    Args:
        doc_url: 文档的原始 URL。

    Returns:
        对应的缓存文件 Path。
    """
    url_hash = hashlib.md5(doc_url.encode("utf-8")).hexdigest()
    return CACHE_DIR / f"{url_hash}.json"


def save(
    doc_url: str,
    field_input_spec: Optional[dict],
    warnings: Optional[list[dict]] = None,
) -> dict[str, Any]:
    """将文档已读状态写入缓存。

    Args:
        doc_url: 文档的原始 URL。
        field_input_spec: 从文档中解析出的 FIELD_INPUT_SPEC，可能为 None。
        warnings: 解析过程中的告警列表。

    Returns:
        写入的完整缓存记录字典。
    """
    ensure_dir(CACHE_DIR)

    now = time.time()
    record: dict[str, Any] = {
        "doc_url": doc_url,
        "field_input_spec": field_input_spec,
        "read_at": now,
        "expire_at": now + DEFAULT_TTL,
        "warnings": warnings or [],
    }

    cache_file = _cache_path(doc_url)
    cache_file.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")

    return record


def load(doc_url: str) -> Optional[dict[str, Any]]:
    """读取指定文档的缓存记录。

    Args:
        doc_url: 文档的原始 URL。

    Returns:
        缓存记录字典，不存在时返回 None。
    """
    cache_file = _cache_path(doc_url)
    if not cache_file.exists():
        return None

    try:
        return json.loads(cache_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def check_valid(doc_url: str) -> str:
    """检查指定文档的缓存状态。

    Args:
        doc_url: 文档的原始 URL。

    Returns:
        ``"valid"`` — 缓存存在且未过期；
        ``"not_found"`` — 缓存不存在；
        ``"expired"`` — 缓存已过期。
    """
    record = load(doc_url)
    if record is None:
        return "not_found"

    if time.time() > record.get("expire_at", 0):
        return "expired"

    return "valid"


def get_spec(doc_url: str) -> Optional[dict]:
    """获取指定文档缓存的 field_input_spec 字段。

    Args:
        doc_url: 文档的原始 URL。

    Returns:
        field_input_spec 字典，缓存不存在或已过期时返回 None。
    """
    if check_valid(doc_url) != "valid":
        return None

    record = load(doc_url)
    return record.get("field_input_spec") if record else None
