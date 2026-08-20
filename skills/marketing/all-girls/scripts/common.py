"""
Mini App Order - 公共常量与异常
"""

import os
from pathlib import Path

# =====================================================
# ENVIRONMENT CONFIGURATION（环境配置）
# =====================================================

_ENVIRONMENTS = {
    "prod": {
        "base_url": "https://7.wawo.cc",
        "api_prefix": "/api",
        "label": "正式环境",
    },
}

_env_name = os.environ.get("MINI_APP_ENV", "prod").lower()
if _env_name not in _ENVIRONMENTS:
    _env_name = "prod"

_env_cfg = _ENVIRONMENTS[_env_name]

# 允许完全自定义（如有 MINI_APP_API_BASE 则覆盖 env 配置）
_custom_base = os.environ.get("MINI_APP_API_BASE", "")
if _custom_base:
    BASE_URL = _custom_base.rstrip("/")
    API_PREFIX = ""
else:
    BASE_URL = _env_cfg["base_url"]
    API_PREFIX = _env_cfg["api_prefix"]

ENV_LABEL = _env_cfg["label"] if not _custom_base else "自定义环境"

WX_APP_ID = os.environ.get("WX_APP_ID", "your-wechat-appid")
TIMEOUT = 15  # seconds

# 搜索接口固定请求头（与认证无关的部分）
SEARCH_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 "
        "Safari/604.1 wechatdevtools/2.01.2510260 MicroMessenger/8.0.5 "
        "Language/zh_CN webview/ hash/1968450271"
    ),
    "os": "devtools",
    "content-type": "application/json",
    "Accept": "*/*",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Referer": "https://servicewechat.com/wx7d1403fe84339669/devtools/page-frame.html",
}

# =====================================================
# 环境检测（PC 端 / 云沙箱）
# =====================================================

def get_client_type() -> str:
    """
    检测当前运行环境。

    Returns:
        "pc"            — PC 端（macOS / Windows），本地文件系统持久化
        "miniprogram"   — 云沙箱（Linux），文件可能临时，需持久化目录

    检测优先级：
        1. 环境变量 WORKBUDDY_CLIENT_TYPE（显式指定）
        2. 操作系统推断（Darwin/Windows → pc，Linux → miniprogram）
    """
    # 优先级 1：显式环境变量
    _type = os.environ.get("WORKBUDDY_CLIENT_TYPE", "").lower()
    if _type in ("pc", "miniprogram"):
        return _type

    # 优先级 2：操作系统推断
    import platform
    system = platform.system()
    if system in ("Darwin", "Windows"):
        return "pc"
    if system == "Linux":
        # Linux 环境视为云沙箱（miniprogram）
        return "miniprogram"

    return "pc"  # 未知系统默认按 PC 端处理


def get_os() -> str:
    """
    返回当前操作系统名称。

    Returns:
        "darwin"   — macOS
        "windows"  — Windows
        "linux"    — Linux / 云沙箱
        "unknown"  — 未知系统
    """
    import platform
    system = platform.system()
    mapping = {
        "Darwin": "darwin",
        "Windows": "windows",
        "Linux": "linux",
    }
    return mapping.get(system, system.lower())


_CLIENT_TYPE = get_client_type()

# Token 缓存文件（存在 skill 目录下，不进 git）
_SKILL_DIR = Path(__file__).parent.parent


def _get_persist_dir() -> Path:
    """
    获取持久化存储目录。

    - PC 端：直接使用 skill 目录（本地文件系统已持久化）
    - 云沙箱：优先使用 WORKBUDDY_PERSIST_DIR 环境变量，
      未设置时回退到 skill 目录（可能是临时的）
    """
    if _CLIENT_TYPE == "pc":
        return _SKILL_DIR
    # 云沙箱：尝试使用平台提供的持久化目录
    persist = os.environ.get("WORKBUDDY_PERSIST_DIR", "")
    if persist:
        p = Path(persist)
        p.mkdir(parents=True, exist_ok=True)
        return p
    return _SKILL_DIR


TOKEN_CACHE_FILE = _get_persist_dir() / ".token_cache.json"


# =====================================================
# Custom Exceptions
# =====================================================

class AuthRequiredError(RuntimeError):
    """需要扫码登录的特殊异常。WorkBuddy 捕获此异常后应触发两阶段扫码登录流程。"""
    pass


class NoAddressError(RuntimeError):
    """用户没有收货地址。需引导用户先去小程序中补充收货地址。"""
    pass
