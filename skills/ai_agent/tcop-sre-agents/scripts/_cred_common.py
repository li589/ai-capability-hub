from __future__ import annotations

import json
import os
import ssl
import tempfile
import urllib.error
import urllib.request
import uuid

CREDENTIAL_PATH = os.path.expanduser("~/.tccli/default.credential")
API_ENDPOINT = "https://cli.cloud.tencent.com"

_SSL_CTX = ssl.create_default_context()
_SSL_CTX.check_hostname = False
_SSL_CTX.verify_mode = ssl.CERT_NONE

def _atomic_write_json(path: str, data: dict) -> None:
    d = os.path.dirname(os.path.abspath(path)) or "."
    os.makedirs(d, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=d, suffix=".tmp", prefix=".cred-")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
        os.chmod(tmp, 0o600)
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise

def http_post_json(url, payload):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15, context=_SSL_CTX) as resp:
            return json.loads(resp.read().decode("utf-8")), None
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        return None, f"HTTP {e.code}: {body[:300]}"
    except urllib.error.URLError as e:
        return None, f"网络错误: {e.reason}"
    except Exception as e:
        return None, f"请求异常: {e}"

def get_temp_cred(access_token, site):
    resp, err = http_post_json(f"{API_ENDPOINT}/get_temp_cred", {
        "TraceId": str(uuid.uuid4()),
        "AccessToken": access_token,
        "Site": site,
    })
    if err:
        return None, err
    if "Error" in resp:
        return None, f"API 错误: {json.dumps(resp['Error'])}"
    if "SecretId" not in resp:
        return None, f"响应缺少 SecretId: {json.dumps(resp)[:200]}"
    return {
        "secretId": resp["SecretId"],
        "secretKey": resp["SecretKey"],
        "token": resp["Token"],
        "expiresAt": resp["ExpiresAt"],
    }, None
