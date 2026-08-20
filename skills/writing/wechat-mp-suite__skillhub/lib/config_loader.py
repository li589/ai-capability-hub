#!/usr/bin/env python3
"""
统一配置加载器 — 读取 config.yaml + .env
所有 Python 脚本通过此模块获取配置，不再硬编码常量。
"""
import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional

# 项目根目录 (lib/ 的父目录)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = PROJECT_ROOT / "config.yaml"
DOT_ENV_PATH = PROJECT_ROOT / ".env"

# 缓存
_config_cache: Optional[Dict[str, Any]] = None

def load_env(path: Path = DOT_ENV_PATH) -> Dict[str, str]:
    """加载 .env 文件为字典"""
    env_vars = {}
    if not path.exists():
        return env_vars
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            key, _, value = line.partition('=')
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key:
                env_vars[key] = value
                os.environ.setdefault(key, value)
    return env_vars

def load_config(path: Path = CONFIG_PATH) -> Dict[str, Any]:
    """加载 YAML 配置文件"""
    global _config_cache
    if _config_cache is not None:
        return _config_cache
    if not path.exists():
        _config_cache = {}
        return _config_cache
    with open(path, 'r', encoding='utf-8') as f:
        _config_cache = yaml.safe_load(f) or {}
    return _config_cache

def get(key_path: str, default: Any = None) -> Any:
    """
    通过点号路径获取配置值
    例: get('spider.parallel_downloads') -> 5
         get('spider.parallel_downloads', 3) -> 5
         get('nonexistent.key', 'fallback') -> 'fallback'
    """
    config = load_config()
    parts = key_path.split('.')
    current = config
    for part in parts:
        if isinstance(current, dict):
            current = current.get(part)
            if current is None:
                return default
        else:
            return default
    return current if current is not None else default

def get_env(key: str, default: str = "") -> str:
    """获取环境变量（优先 .env 文件，其次系统环境变量）"""
    load_env()
    return os.environ.get(key, default)

def reload():
    """重新加载配置（调试用）"""
    global _config_cache
    _config_cache = None
    load_config()

# ═══════════════════════════════════════════════════════════════
# 统一凭证加载
# ═══════════════════════════════════════════════════════════════

ENV_FILE_PATHS = [
    PROJECT_ROOT / "wechat.env",
    PROJECT_ROOT / ".env",
    PROJECT_ROOT.parent / "wechat.env",
    PROJECT_ROOT.parent / ".env",
]

def find_env_file() -> Optional[Path]:
    """搜索所有可能的 .env 路径，返回第一个存在的"""
    for path in ENV_FILE_PATHS:
        if path.exists():
            return path
    return None

def load_credentials() -> Dict[str, str]:
    """统一凭证加载：.env > 环境变量

    返回 dict，包含 WECHAT_APP_ID, WECHAT_APP_SECRET, SOGOU_COOKIE, MCP_SERVER_URL, SEARCH_PROXY 等。
    """
    env_path = find_env_file()
    if env_path:
        load_env(env_path)
    result = {}
    for key in ['WECHAT_APP_ID', 'WECHAT_APP_SECRET', 'SOGOU_COOKIE',
                'MCP_SERVER_URL', 'SEARCH_PROXY']:
        val = os.environ.get(key)
        if val:
            result[key] = val
    return result

# 启动时自动加载
load_env()
