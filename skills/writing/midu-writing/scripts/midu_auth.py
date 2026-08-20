#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Midu Skill 短信验证码登录/注册授权工具。

两步授权：
  --action send    下发短信验证码
  --action verify  提交验证码，返回 appSecret / userId，并写入 ~/.midu_keys

用 requests 直连蜜度授权接口。verify 接口登录/注册一体（未注册自动注册）。
禁止只依赖 export：子进程改不了父 shell 环境变量，命令结束后丢失。
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import requests


BASE_URL = "https://api.midu.com"
SEND_SMS_URL = f"{BASE_URL}/ability/auth/send/sms"
VERIFY_URL = f"{BASE_URL}/ability/auth/mobile/verify"
PRODUCT_TYPE = 40   # 垂直 AI 平台
SMS_TYPE = "1"      # 1=登录（verify 接口登录/注册一体）
DEFAULT_TIMEOUT = 30
KEYS_FILE = Path.home() / ".midu_keys"


class MiduAuthError(RuntimeError):
    pass


def load_keys_file(path: Path = KEYS_FILE) -> Dict[str, str]:
    if not path.is_file():
        return {}
    result: Dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        result[key.strip()] = value.strip()
    return result


def save_credentials(app_secret: str, user_id: Any, path: Path = KEYS_FILE) -> str:
    """将凭证持久化到 ~/.midu_keys（跨会话复用）。禁止只依赖 export。"""
    data = load_keys_file(path)
    data["MIDU_APP_SECRET"] = str(app_secret)
    data["MIDU_USER_ID"] = str(user_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    content = "".join(f"{k}={v}\n" for k, v in data.items())
    path.write_text(content, encoding="utf-8")
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass
    return str(path)


def _post_form(url: str, data: Dict[str, Any], timeout: int) -> Dict[str, Any]:
    try:
        r = requests.post(
            url,
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=timeout,
        )
    except requests.RequestException as exc:
        raise MiduAuthError(f"网络请求失败：{exc}") from exc

    if not r.ok:
        raise MiduAuthError(f"接口 HTTP 错误: {r.status_code} {r.text}".strip())

    try:
        parsed = r.json()
    except ValueError as exc:
        raise MiduAuthError(f"响应不是合法 JSON：{r.text}") from exc
    if not isinstance(parsed, dict):
        raise MiduAuthError(f"响应 JSON 不是对象：{parsed!r}")

    code = str(parsed.get("code", ""))
    success = parsed.get("success")
    if code not in ("0000", "0", "200") and success is not True:
        raise MiduAuthError(parsed.get("message") or parsed.get("msg") or f"授权失败：{parsed}")
    return parsed


def send_sms(mobile: str, timeout: int = DEFAULT_TIMEOUT) -> Dict[str, Any]:
    """下发短信验证码。"""
    return _post_form(
        SEND_SMS_URL,
        {"productType": PRODUCT_TYPE, "mobile": mobile, "smsType": SMS_TYPE},
        timeout,
    )


def verify_sms(mobile: str, sms_code: str, timeout: int = DEFAULT_TIMEOUT) -> Dict[str, Any]:
    """校验短信验证码并登录/注册，返回含 userVo 的响应。"""
    return _post_form(
        VERIFY_URL,
        {"productType": PRODUCT_TYPE, "mobile": mobile, "smsCode": sms_code},
        timeout,
    )


def extract_credentials(result: Dict[str, Any]) -> Tuple[str, Any, str]:
    """从 verify 响应提取 (appSecret, userId, appId)。返回结构为 data.userVo.*。"""
    user_vo = (result.get("data") or {}).get("userVo") or {}
    app_secret = (user_vo.get("appSecret") or "").strip()
    user_id = user_vo.get("id")
    app_id = user_vo.get("appId") or ""
    return app_secret, user_id, app_id


def _build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Midu Skill 短信验证码登录/注册授权")
    p.add_argument(
        "--action",
        required=True,
        choices=["send", "verify"],
        help="send=下发验证码；verify=校验验证码并返回 appSecret/userId",
    )
    p.add_argument("--mobile", required=True, help="用户手机号")
    p.add_argument("--sms_code", default="", help="短信验证码（--action verify 时必填）")
    p.add_argument(
        "--timeout",
        type=int,
        default=DEFAULT_TIMEOUT,
        help=f"HTTP 超时秒数（默认 {DEFAULT_TIMEOUT}）",
    )
    p.add_argument("--pretty", action="store_true", help="美化输出 JSON")
    return p


def _print_json(payload: Dict[str, Any], pretty: bool) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2 if pretty else None))


def main(argv: Optional[Tuple[str, ...]] = None) -> int:
    args = _build_arg_parser().parse_args(list(argv) if argv is not None else None)
    mobile = args.mobile.strip()
    if not mobile:
        print("❌ mobile 不能为空", file=sys.stderr)
        return 2

    try:
        if args.action == "send":
            result = send_sms(mobile, args.timeout)
            _print_json(
                {
                    "code": result.get("code", "0000"),
                    "success": True,
                    "message": result.get("message") or result.get("msg") or "验证码已发送",
                    "mobile": mobile,
                },
                args.pretty,
            )
            return 0

        sms_code = args.sms_code.strip()
        if not sms_code:
            print("❌ --action verify 时必须传 --sms_code", file=sys.stderr)
            return 2

        result = verify_sms(mobile, sms_code, args.timeout)
        app_secret, user_id, app_id = extract_credentials(result)
        if not app_secret or user_id is None:
            raise MiduAuthError(f"授权成功但响应缺少 appSecret/userId：{result}")

        keys_path = save_credentials(app_secret, user_id)
        _print_json(
            {
                "code": result.get("code", "0000"),
                "success": True,
                "message": result.get("message") or result.get("msg") or "授权成功",
                "appSecret": app_secret,
                "userId": user_id,
                "appId": app_id,
                "transactionId": result.get("transactionId", ""),
                "keysFile": keys_path,
                "hint": (
                    f"凭证已写入 {keys_path}。"
                    "业务脚本优先读环境变量，其次读该文件；不要只依赖 shell export。"
                    "后续请求头自动带 Authorization / X-User-Id / X-Skill-Code。"
                ),
            },
            args.pretty,
        )
        return 0
    except MiduAuthError as e:
        print(f"❌ {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
