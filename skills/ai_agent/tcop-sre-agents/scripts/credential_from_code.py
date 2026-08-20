import base64
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _cred_common import (
    CREDENTIAL_PATH,
    _atomic_write_json,
    get_temp_cred,
)

def cmd_finish(code_b64):

    try:
        decoded = base64.b64decode(code_b64).decode("utf-8")
        oauth_data = json.loads(decoded)
    except Exception as e:
        print(f"LOGIN_FAILED: 验证码解码失败: {e}")
        return 1

    access_token = oauth_data.get("accessToken", "")
    refresh_token = oauth_data.get("refreshToken", "")
    open_id = oauth_data.get("openId", "")
    expires_at = oauth_data.get("expiresAt", 0)
    site = oauth_data.get("site", "cn")

    if not access_token or not open_id:
        print("LOGIN_FAILED: 验证码缺少必要字段 (accessToken/openId)")
        return 1

    if not refresh_token:
        print("LOGIN_FAILED: 验证码缺少 refreshToken（无法启用非交互续期）")
        return 1

    sts, err = get_temp_cred(access_token, site)
    if err:
        print(f"LOGIN_FAILED: STS 兑换失败: {err}")
        return 1

    credential = {
        "type": "oauth",
        "secretId": sts["secretId"],
        "secretKey": sts["secretKey"],
        "token": sts["token"],
        "expiresAt": sts["expiresAt"],
        "oauth": {
            "openId": open_id,
            "accessToken": access_token,
            "expiresAt": expires_at,
            "refreshToken": refresh_token,
            "site": site,
        },
    }

    cred_dir = os.path.dirname(CREDENTIAL_PATH)
    os.makedirs(cred_dir, exist_ok=True)
    _atomic_write_json(CREDENTIAL_PATH, credential)

    print("LOGIN_OK")
    return 0

def main():
    if len(sys.argv) < 2:
        print("用法: credential_from_code.py <Base64验证码>")
        return 1

    code_b64 = sys.argv[1]

    if code_b64 == "finish" and len(sys.argv) >= 3:
        code_b64 = sys.argv[2]

    return cmd_finish(code_b64)

if __name__ == "__main__":
    sys.exit(main())
