"""DesignKit 请求的公共凭据入口与渠道上下文。"""

from __future__ import annotations

import os
import urllib.parse


# DEFAULT_CHANNEL 是分发包唯一需要修改的渠道标识。
DEFAULT_CHANNEL = "workbuddy"
DEFAULT_ACCOUNT_PORTAL_URL = "https://www.designkit.cn/openClaw"


def channel_value() -> str:
    """返回受运行环境统一管理、不可由用户输入覆盖的渠道值。"""
    return os.environ.get("DESIGNKIT_CHANNEL", DEFAULT_CHANNEL).strip() or DEFAULT_CHANNEL


def account_portal_url() -> str:
    """返回与公共渠道一致的账号注册、充值和权益处理入口。"""
    base_url = (
        os.environ.get("DESIGNKIT_OPENCLAW_AK_URL", DEFAULT_ACCOUNT_PORTAL_URL).strip()
        or DEFAULT_ACCOUNT_PORTAL_URL
    )
    return with_channel(base_url)


def with_channel(url: str) -> str:
    """在服务请求 URL 上强制写入唯一的 channel 查询参数。"""
    parsed = urllib.parse.urlsplit(url)
    query = [
        (key, value)
        for key, value in urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
        if key != "channel"
    ]
    query.append(("channel", channel_value()))
    return urllib.parse.urlunsplit(
        (parsed.scheme, parsed.netloc, parsed.path, urllib.parse.urlencode(query), parsed.fragment)
    )
