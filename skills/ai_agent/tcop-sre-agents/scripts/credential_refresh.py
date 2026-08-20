import json
import os
import sys
import time
import uuid

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _cred_common import (
    CREDENTIAL_PATH,
    API_ENDPOINT,
    _atomic_write_json,
    http_post_json,
    get_temp_cred,
)

_ACCESS_REFRESH_SAFE_DUR = 60 * 5

def refresh_user_token(refresh_token, open_id, site):
    resp, err = http_post_json(f"{API_ENDPOINT}/refresh_user_token", {
        "TraceId": str(uuid.uuid4()),
        "RefreshToken": refresh_token,
        "OpenId": open_id,
        "Site": site,
    })
    if err:
        return None, err
    if "Error" in resp:
        return None, f"API 错误: {json.dumps(resp['Error'])}"
    if "AccessToken" not in resp:
        return None, f"响应缺少 AccessToken: {json.dumps(resp)[:200]}"
    return {
        "accessToken": resp["AccessToken"],
        "expiresAt": resp["ExpiresAt"],
    }, None

def refresh_credential_file() -> tuple[bool, str]:

    if not os.path.isfile(CREDENTIAL_PATH):
        return False, "REFRESH_FAILED: 凭证文件不存在"

    try:
        with open(CREDENTIAL_PATH, "r") as f:
            cred = json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        return False, f"REFRESH_FAILED: 凭证文件解析失败: {e}"

    if cred.get("type") != "oauth":
        return True, "REFRESH_SKIP: 凭证类型不是 oauth（永久密钥），无需刷新"

    oauth = cred.get("oauth")
    if not oauth or not isinstance(oauth, dict):
        return False, "REFRESH_FAILED: 凭证文件中无 oauth 块"

    refresh_token = oauth.get("refreshToken", "")
    if not refresh_token:
        return False, "REFRESH_FAILED: 无 refreshToken"

    open_id = oauth.get("openId", "")
    site = oauth.get("site", "cn")
    access_token = oauth.get("accessToken", "")
    access_expires = oauth.get("expiresAt", 0)

    now = time.time()

    if not access_token or (access_expires - now < _ACCESS_REFRESH_SAFE_DUR):
        new_token, err = refresh_user_token(refresh_token, open_id, site)
        if err:
            return False, f"REFRESH_FAILED: 刷新 accessToken 失败: {err}"
        access_token = new_token["accessToken"]
        access_expires = new_token["expiresAt"]

        oauth["accessToken"] = access_token
        oauth["expiresAt"] = access_expires

    sts, err = get_temp_cred(access_token, site)

    if err and ("token error or expire" in err.lower() or "access" in err.lower()):
        new_token, refresh_err = refresh_user_token(refresh_token, open_id, site)
        if refresh_err:
            return False, f"REFRESH_FAILED: STS 兑换失败且 refreshToken 也无法刷新: {refresh_err}"
        access_token = new_token["accessToken"]
        access_expires = new_token["expiresAt"]
        oauth["accessToken"] = access_token
        oauth["expiresAt"] = access_expires

        sts, err = get_temp_cred(access_token, site)

    if err:
        return False, f"REFRESH_FAILED: STS 兑换失败: {err}"

    cred["secretId"] = sts["secretId"]
    cred["secretKey"] = sts["secretKey"]
    cred["token"] = sts["token"]
    cred["expiresAt"] = sts["expiresAt"]
    cred["oauth"] = oauth

    try:
        _atomic_write_json(CREDENTIAL_PATH, cred)
    except IOError as e:
        return False, f"REFRESH_FAILED: 写回凭证文件失败: {e}"

    return True, "REFRESH_OK"

def main():
    ok, msg = refresh_credential_file()
    print(msg)
    return 0 if ok else 1

if __name__ == "__main__":
    sys.exit(main())
