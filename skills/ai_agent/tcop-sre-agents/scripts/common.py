from __future__ import annotations

import datetime
import json
import os
import sys
from typing import Any

from credential_refresh import refresh_credential_file, CREDENTIAL_PATH

try:
    from tencentcloud.common import credential
    from tencentcloud.common.common_client import CommonClient
    from tencentcloud.common.exception.tencent_cloud_sdk_exception import (
        TencentCloudSDKException,
    )
    from tencentcloud.common.profile.client_profile import ClientProfile
    from tencentcloud.common.profile.http_profile import HttpProfile
except ImportError:
    print(
        json.dumps(
            {"success": False, "error": "tencentcloud-sdk-python 未安装，请运行: pip3 install tencentcloud-sdk-python"},
            ensure_ascii=False,
        )
    )
    sys.exit(1)

def success(data: dict) -> None:
    result = {"success": True}
    result.update(data)
    print(json.dumps(result, ensure_ascii=True, indent=2))

def fail(message: str) -> None:
    print(json.dumps({"success": False, "error": message}, ensure_ascii=True, indent=2))
    sys.exit(1)

def run(func) -> None:
    try:
        func()
    except SystemExit:
        raise
    except TencentCloudSDKException as e:
        fail(f"云 API 错误: [{e.code}] {e.message}")
    except Exception as e:
        fail(f"未知错误: {e}")

_CRED_EXPIRY_BUFFER_SECONDS = 300

def _load_dotenv() -> None:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(script_dir, ".env"),
        os.path.join(os.getcwd(), ".env"),
    ]
    for path in candidates:
        if os.path.isfile(path):
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    key, _, value = line.partition("=")
                    key, value = key.strip(), value.strip()
                    if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
                        value = value[1:-1]
                    if key and key not in os.environ:
                        os.environ[key] = value
            break

def _is_tccli_expired(cred_data: dict[str, Any]) -> bool:
    expires_at = cred_data.get("expiresAt")
    if expires_at is None:
        return False
    try:
        return int(datetime.datetime.now().timestamp()) >= (int(expires_at) - _CRED_EXPIRY_BUFFER_SECONDS)
    except (ValueError, TypeError):
        return False

def get_credential() -> credential.Credential:
    _load_dotenv()

    tccli_path = CREDENTIAL_PATH

    if os.path.isfile(tccli_path):
        try:
            with open(tccli_path, "r", encoding="utf-8") as f:
                tccli_cred = json.load(f)
            sid = tccli_cred.get("secretId", "")
            skey = tccli_cred.get("secretKey", "")
            if sid and skey:
                if _is_tccli_expired(tccli_cred):

                    try:
                        ok, reason = refresh_credential_file()
                        if ok:
                            with open(tccli_path, "r", encoding="utf-8") as f:
                                tccli_cred = json.load(f)
                            sid = tccli_cred.get("secretId", "") or sid
                            skey = tccli_cred.get("secretKey", "") or skey
                        else:

                            print(f"[Credential] 非交互刷新失败：{reason}，回退环境变量", file=sys.stderr)
                            sid = ""
                            skey = ""
                    except Exception as exc:
                        print(f"[Credential] 非交互刷新异常：{exc}，回退环境变量", file=sys.stderr)
                        sid = ""
                        skey = ""
                if sid and skey:
                    token = tccli_cred.get("token", "")
                    return credential.Credential(sid, skey, token=token if token else None)
        except (OSError, json.JSONDecodeError):
            pass

    sid = os.environ.get("TENCENTCLOUD_SECRET_ID", "")
    skey = os.environ.get("TENCENTCLOUD_SECRET_KEY", "")
    token = os.environ.get("TENCENTCLOUD_SECURITY_TOKEN", "")
    if sid and skey:
        return credential.Credential(sid, skey, token=token if token else None)

    fail(
        "未找到有效凭据。请按 references/sop.md 的认证恢复流程执行："
        "先 `python3 scripts/credential_refresh.py` 非交互刷新；仍失败则交互式登录"
        "（有头：tccli auth login；无头：scripts/credential_from_code.py）。"
        "或设置环境变量 TENCENTCLOUD_SECRET_ID / TENCENTCLOUD_SECRET_KEY。"
    )
    raise SystemExit(1)

def build_monitor_client() -> CommonClient:
    cred = get_credential()
    hp = HttpProfile()
    hp.endpoint = os.environ.get("MONITOR_ENDPOINT", "monitor.tencentcloudapi.com")
    hp.reqMethod = "POST"
    hp.reqTimeout = 30
    cp = ClientProfile(httpProfile=hp, signMethod="TC3-HMAC-SHA256", language="zh-CN")
    return CommonClient("monitor", "2023-06-16", cred, "ap-guangzhou", profile=cp)

def build_notice_client() -> CommonClient:
    cred = get_credential()
    hp = HttpProfile()
    hp.endpoint = os.environ.get("MONITOR_ENDPOINT", "monitor.tencentcloudapi.com")
    hp.reqMethod = "POST"
    hp.reqTimeout = 30
    cp = ClientProfile(httpProfile=hp, signMethod="TC3-HMAC-SHA256", language="zh-CN")
    return CommonClient("monitor", "2018-07-24", cred, "ap-guangzhou", profile=cp)

def build_chat_client() -> CommonClient:
    cred = get_credential()
    hp = HttpProfile()
    hp.endpoint = os.environ.get("FIBONA_ENDPOINT", "fibona.tencentcloudapi.com")
    hp.reqMethod = "POST"
    hp.reqTimeout = 120
    cp = ClientProfile(httpProfile=hp, signMethod="TC3-HMAC-SHA256", language="zh-CN")
    return CommonClient("fibona", "2025-04-15", cred, "ap-guangzhou", profile=cp)

def call_api(action: str, params: dict, client: CommonClient | None = None) -> dict:
    if client is None:
        client = build_monitor_client()
    resp = client.call_json(action, params)
    if isinstance(resp, str):
        resp = json.loads(resp)

    if isinstance(resp, dict) and "Response" in resp:
        return resp["Response"]
    return resp

def call_notice_api(action: str, params: dict) -> dict:
    client = build_notice_client()
    return call_api(action, params, client=client)
