#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fund-advisor 统一大模型适配层
==============================
所有国产大模型都走 OpenAI 兼容协议（/v1/chat/completions），所以一个 LLMClient 就够用。
本模块负责：参数组装 → HTTP 请求 → 流式/非流式解析 → 错误归一化。

支持：DeepSeek / MiniMax / 小米 / 通义千问 / 智谱 GLM / Kimi / 豆包 / 混元 / 星火 / 自定义 OpenAI 兼容端点
"""
from __future__ import annotations

import json
import time
from typing import Iterator
from urllib import request
from urllib.error import HTTPError, URLError

# ── 错误类 ─────────────────────────────────────────────────────────────
class LLMError(Exception):
    """统一的 LLM 错误基类"""
    def __init__(self, message, provider="", status_code=0, raw=None):
        super().__init__(message)
        self.provider = provider
        self.status_code = status_code
        self.raw = raw


class LLMAuthError(LLMError):  # 401/403
    pass


class LLMRateLimitError(LLMError):  # 429
    pass


class LLMServerError(LLMError):  # 5xx
    pass


# ── 主客户端 ───────────────────────────────────────────────────────────
class LLMClient:
    """OpenAI 兼容协议的通用 LLM 客户端
    用法：
        client = LLMClient(base_url=..., api_key=..., model=..., provider="deepseek")
        reply = client.chat([{"role": "user", "content": "你好"}])
        for chunk in client.stream(messages):
            print(chunk, end="")
    """

    def __init__(self, base_url: str, api_key: str, model: str,
                 provider: str = "unknown",
                 temperature: float = 0.7, max_tokens: int = 2048,
                 system_prompt: str = "", timeout: int = 60,
                 custom_path: str = "", custom_headers: dict = None,
                 auth_style: str = "openai_bearer"):
        """
        auth_style:
          - openai_bearer: Authorization: Bearer <key>  (DeepSeek/通义/智谱/Kimi/豆包/MiniMax OpenAI兼容)
          - MiniMax_v2:    Authorization: Bearer <key> + 专用路径 /v1/text/chatcompletion_v2
          - x_api_key:     X-Api-Key: <key>             (部分旧平台)
        """
        self.base_url = (base_url or "").rstrip("/")
        self.api_key = api_key or ""
        self.model = model
        self.provider = provider
        self.temperature = float(temperature)
        self.max_tokens = int(max_tokens)
        self.system_prompt = system_prompt
        self.timeout = timeout
        self.custom_path = custom_path  # e.g. "/v1/text/chatcompletion_v2" (MiniMax)
        self.custom_headers = custom_headers or {}
        self.auth_style = auth_style

    # ── 公共：补 system message ───────────────────────────────────────
    def _build_messages(self, messages: list, system_prompt: str = "") -> list:
        sys_p = system_prompt or self.system_prompt
        if sys_p:
            has_system = any(m.get("role") == "system" for m in messages)
            if not has_system:
                messages = [{"role": "system", "content": sys_p}] + list(messages)
        return messages

    # ── 公共：发起 HTTP 请求 ──────────────────────────────────────────
    def _build_url(self) -> str:
        """根据 custom_path 或默认 OpenAI 路径拼装"""
        if self.custom_path:
            # 确保 base_url 不带尾部斜杠，custom_path 必须以 / 开头
            base = self.base_url.rstrip("/")
            path = self.custom_path if self.custom_path.startswith("/") else "/" + self.custom_path
            return f"{base}{path}"
        return f"{self.base_url}/chat/completions"

    def _build_headers(self, stream: bool = False) -> dict:
        """根据 auth_style 构造鉴权头"""
        h = {
            "Content-Type": "application/json",
            "Accept": "text/event-stream" if stream else "application/json",
        }
        if self.auth_style == "openai_bearer":
            h["Authorization"] = f"Bearer {self.api_key}"
        elif self.auth_style == "MiniMax_v2":
            # MiniMax 专用端点：Bearer + 特殊路径
            h["Authorization"] = f"Bearer {self.api_key}"
        elif self.auth_style == "x_api_key":
            h["X-Api-Key"] = self.api_key
        else:
            h["Authorization"] = f"Bearer {self.api_key}"
        h.update(self.custom_headers)
        return h

    def _request(self, payload: dict, stream: bool = False) -> dict:
        if not self.api_key:
            raise LLMAuthError(
                f"[{self.provider}] 未配置 API Key，请到「模型设置」里填写。",
                provider=self.provider, status_code=0,
            )
        if not self.base_url or "your-endpoint" in self.base_url:
            raise LLMError(
                f"[{self.provider}] base_url 未配置：{self.base_url}",
                provider=self.provider,
            )

        url = self._build_url()
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")

        req = request.Request(
            url, data=body, method="POST", headers=self._build_headers(stream),
        )
        try:
            with request.urlopen(req, timeout=self.timeout) as resp:
                data = resp.read()
                if stream:
                    # 流式：返回原始字节，调用方自行解析 SSE
                    return {"_stream": resp, "_raw": data}
                return json.loads(data.decode("utf-8"))
        except HTTPError as e:
            raw = e.read().decode("utf-8", errors="replace")
            msg = self._parse_error(raw, e.code)
            if e.code in (401, 403):
                raise LLMAuthError(msg, provider=self.provider, status_code=e.code, raw=raw)
            if e.code == 429:
                raise LLMRateLimitError(msg, provider=self.provider, status_code=e.code, raw=raw)
            if e.code >= 500:
                raise LLMServerError(msg, provider=self.provider, status_code=e.code, raw=raw)
            raise LLMError(msg, provider=self.provider, status_code=e.code, raw=raw)
        except URLError as e:
            raise LLMError(f"[{self.provider}] 网络错误：{e.reason}", provider=self.provider)
        except (TimeoutError, OSError) as e:
            raise LLMError(f"[{self.provider}] 请求超时：{e}", provider=self.provider)

    def _parse_error(self, raw: str, code: int) -> str:
        """从错误响应里挑出可读 message"""
        try:
            j = json.loads(raw)
            err = j.get("error", {}) or {}
            msg = err.get("message") or j.get("message") or raw[:200]
        except Exception:
            msg = raw[:200] or f"HTTP {code}"
        return f"[{self.provider}] {msg}"

    # ── 非流式 ────────────────────────────────────────────────────────
    def chat(self, messages: list, **overrides) -> str:
        """非流式对话，返回完整回复文本"""
        payload = {
            "model": overrides.get("model", self.model),
            "messages": self._build_messages(messages),
            "temperature": overrides.get("temperature", self.temperature),
            "max_tokens": overrides.get("max_tokens", self.max_tokens),
            "stream": False,
        }
        resp = self._request(payload)
        try:
            return resp["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as e:
            raise LLMError(
                f"[{self.provider}] 响应格式异常：{resp}",
                provider=self.provider, raw=resp,
            ) from e

    # ── 流式（SSE） ──────────────────────────────────────────────────
    def stream(self, messages: list, **overrides) -> Iterator[str]:
        """流式对话，逐 chunk yield 文本"""
        payload = {
            "model": overrides.get("model", self.model),
            "messages": self._build_messages(messages),
            "temperature": overrides.get("temperature", self.temperature),
            "max_tokens": overrides.get("max_tokens", self.max_tokens),
            "stream": True,
        }
        if not self.api_key:
            raise LLMAuthError(f"[{self.provider}] 未配置 API Key", provider=self.provider)

        url = self._build_url()
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        req = request.Request(
            url, data=body, method="POST",
            headers=self._build_headers(stream=True),
        )
        try:
            resp = request.urlopen(req, timeout=self.timeout)
        except HTTPError as e:
            raw = e.read().decode("utf-8", errors="replace")
            raise LLMError(self._parse_error(raw, e.code), provider=self.provider, status_code=e.code)
        except (URLError, TimeoutError, OSError) as e:
            raise LLMError(f"[{self.provider}] 网络/超时错误：{e}", provider=self.provider)

        for raw_line in resp:
            line = raw_line.decode("utf-8", errors="replace").strip()
            if not line or not line.startswith("data:"):
                continue
            data_str = line[5:].strip()
            if data_str == "[DONE]":
                break
            try:
                j = json.loads(data_str)
                delta = j["choices"][0].get("delta", {})
                content = delta.get("content", "")
                if content:
                    yield content
            except (KeyError, IndexError, json.JSONDecodeError):
                continue

    # ── 连通性测试 ───────────────────────────────────────────────────
    def ping(self) -> dict:
        """发送最小请求验证 API Key + 网络是否通"""
        start = time.time()
        try:
            reply = self.chat([{"role": "user", "content": "ping"}], max_tokens=8)
            return {
                "ok": True,
                "latency_ms": int((time.time() - start) * 1000),
                "reply": reply[:80],
                "provider": self.provider,
                "model": self.model,
            }
        except LLMError as e:
            return {
                "ok": False,
                "error": str(e),
                "provider": self.provider,
                "model": self.model,
            }


# ── Provider 注册表 ───────────────────────────────────────────────────
# 简单工厂：传入 provider key + 完整配置 → 返回 LLMClient
def make_client(provider_key: str, llm_config: dict) -> LLMClient:
    providers = llm_config.get("providers", {})
    p = providers.get(provider_key, {})
    gen = llm_config.get("generation", {})
    return LLMClient(
        base_url=p.get("base_url", ""),
        api_key=p.get("api_key", ""),
        model=p.get("model", ""),
        provider=provider_key,
        temperature=gen.get("temperature", 0.7),
        max_tokens=gen.get("max_tokens", 2048),
        system_prompt=gen.get("system_prompt", ""),
        custom_path=p.get("custom_path", ""),
        custom_headers=p.get("custom_headers", {}),
        auth_style=p.get("auth_style", "openai_bearer"),
    )


def list_providers(llm_config: dict) -> list:
    """返回可读的 provider 列表（含元信息）"""
    out = []
    for k, v in llm_config.get("providers", {}).items():
        out.append({
            "key": k,
            "name": v.get("name", k),
            "description": v.get("description", ""),
            "model": v.get("model", ""),
            "models": v.get("models", []),
            "has_key": bool(v.get("api_key")),
            "base_url": v.get("base_url", ""),
            "website": v.get("website", ""),
        })
    return out
