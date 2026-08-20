"""test_llm_providers.py — LLM 适配层测试"""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import llm_providers
from llm_providers import LLMClient, LLMError, LLMAuthError, make_client, list_providers


def test_url_build_default():
    """无 custom_path 时走 OpenAI 标准 /chat/completions"""
    c = LLMClient(base_url="https://api.deepseek.com/v1", api_key="x", model="deepseek-chat", provider="deepseek")
    assert c._build_url() == "https://api.deepseek.com/v1/chat/completions"


def test_url_build_custom_path():
    """custom_path 优先"""
    c = LLMClient(base_url="https://api.MiniMax.chat", api_key="x", model="m",
                  provider="MiniMax", custom_path="/v1/text/chatcompletion_v2")
    assert c._build_url() == "https://api.MiniMax.chat/v1/text/chatcompletion_v2"


def test_url_build_strip_slash():
    """base_url 末尾 / 应被去除，避免双斜杠"""
    c = LLMClient(base_url="https://api.deepseek.com/v1/", api_key="x", model="m", provider="p")
    assert c._build_url() == "https://api.deepseek.com/v1/chat/completions"


def test_headers_bearer():
    """默认 openai_bearer 走 Authorization: Bearer"""
    c = LLMClient(base_url="https://x", api_key="my_key", model="m", provider="p")
    h = c._build_headers()
    assert h["Authorization"] == "Bearer my_key"
    assert h["Content-Type"] == "application/json"


def test_headers_x_api_key():
    """x_api_key 风格"""
    c = LLMClient(base_url="https://x", api_key="my_key", model="m", provider="p", auth_style="x_api_key")
    h = c._build_headers()
    assert h["X-Api-Key"] == "my_key"
    assert "Authorization" not in h


def test_headers_stream_accept():
    """流式 Accept 应为 text/event-stream"""
    c = LLMClient(base_url="https://x", api_key="k", model="m", provider="p")
    h = c._build_headers(stream=True)
    assert h["Accept"] == "text/event-stream"


def test_build_messages_prepend_system():
    """没有 system 时自动补"""
    c = LLMClient(base_url="https://x", api_key="k", model="m", provider="p", system_prompt="你是助手")
    msgs = c._build_messages([{"role": "user", "content": "hi"}])
    assert msgs[0]["role"] == "system"
    assert msgs[0]["content"] == "你是助手"
    assert msgs[1]["role"] == "user"


def test_build_messages_keep_existing_system():
    """已有 system 时不重复"""
    c = LLMClient(base_url="https://x", api_key="k", model="m", provider="p", system_prompt="默认")
    msgs = c._build_messages([{"role": "system", "content": "用户指定"}])
    assert len(msgs) == 1
    assert msgs[0]["content"] == "用户指定"


def test_missing_api_key_raises():
    """未配置 API Key 抛 LLMAuthError"""
    c = LLMClient(base_url="https://api.deepseek.com/v1", api_key="", model="m", provider="p")
    with pytest.raises(LLMAuthError):
        c._request({"model": "m", "messages": [], "stream": False})


def test_unconfigured_base_url_raises():
    """base_url 包含占位符应抛 LLMError"""
    c = LLMClient(base_url="https://your-endpoint.com/v1", api_key="k", model="m", provider="p")
    with pytest.raises(llm_providers.LLMError):
        c._request({"model": "m", "messages": [], "stream": False})


def test_make_client_from_config():
    """make_client 工厂函数正常"""
    cfg = {
        "providers": {
            "deepseek": {
                "base_url": "https://api.deepseek.com/v1",
                "api_key": "test_key",
                "model": "deepseek-chat",
            }
        },
        "generation": {"temperature": 0.5, "max_tokens": 1024, "system_prompt": "你是助手"},
    }
    c = make_client("deepseek", cfg)
    assert c.api_key == "test_key"
    assert c.temperature == 0.5
    assert c.max_tokens == 1024
    assert c.system_prompt == "你是助手"


def test_list_providers():
    """list_providers 暴露完整元信息"""
    cfg = {
        "providers": {
            "deepseek": {"base_url": "x", "api_key": "k", "model": "m", "models": ["m"], "name": "DeepSeek", "description": "d", "website": "w"},
            "empty": {"base_url": "y", "api_key": "", "model": "m2"},
        }
    }
    out = list_providers(cfg)
    assert len(out) == 2
    deepseek = next(p for p in out if p["key"] == "deepseek")
    assert deepseek["has_key"] is True
    empty = next(p for p in out if p["key"] == "empty")
    assert empty["has_key"] is False
