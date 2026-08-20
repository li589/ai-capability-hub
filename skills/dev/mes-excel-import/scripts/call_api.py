# -*- coding: utf-8 -*-
"""
接口调用模块：POST/GET JSON 到 OpenAPI，支持超时重试 + Token 鉴权（SSO 模式）。
鉴权模式（config.json 的 auth 配置）：
  - auth.enabled = true 时，调用前自动检查 token，无/过期则先走 SSO 换取
  - SSO 两段式（mode="sso"）：
      1) POST {base}{code_endpoint}   body: {userNo, appId}          → result = 临时授权码 code（1 分钟有效）
      2) POST {base}{token_endpoint}  body: {appId, appSecret, code, language, envType, mode}
                                                                     → result = accessToken（1 小时有效）+ refreshToken + tokenCode
  - token 从响应 result 提取（支持 result 为字符串 / JSON 字符串 / 对象，字段 accessToken/access_token/token）
  - 请求头带 token_header: token_prefix + token（默认 Authorization: Bearer xxx）
返回: {"ok": bool, "status": HTTP状态码, "data": 解析后的返回(JSON) 或原始文本,
       "error": 错误信息(ok=False 时)}
"""
import json
import time
import requests
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOKEN_TTL = 3600  # accessToken 有效期（秒），超过则重新走 SSO 换取


def load_config():
    with open(ROOT / "config.json", encoding="utf-8") as f:
        return json.load(f)


def save_config(cfg):
    with open(ROOT / "config.json", "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)


def _deep_get(obj, path):
    """按点路径取值：result.token / result.accessToken"""
    cur = obj
    for part in str(path).split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        elif isinstance(cur, list) and part.isdigit() and int(part) < len(cur):
            cur = cur[int(part)]
        else:
            return None
    return cur


def _extract_token(data, path):
    """通用 token 提取：
    - 先按配置路径取（如 result.token.accessToken）
    - result 可能是字符串：若是 JSON 再解析；否则视为 token 本身
    - 兜底常见字段：accessToken / access_token / token / result.token / data.access_token
    """
    if not isinstance(data, dict):
        return None
    # 1) 配置路径
    v = _deep_get(data, path) if path else None
    if isinstance(v, str) and v.strip():
        v = v.strip()
        if v.startswith("{"):
            try:
                v = json.loads(v)
            except Exception:
                pass
        if isinstance(v, dict):
            for k in ("accessToken", "access_token", "token", "access_token_value"):
                if v.get(k):
                    return v[k]
        return v
    if isinstance(v, dict):
        for k in ("accessToken", "access_token", "token"):
            if v.get(k):
                return v[k]
    # 2) 兜底：result 本身
    result = data.get("result")
    if isinstance(result, str) and result.strip():
        r = result.strip()
        if r.startswith("{"):
            try:
                r = json.loads(r)
            except Exception:
                pass
        if isinstance(r, dict):
            for k in ("accessToken", "access_token", "token"):
                if r.get(k):
                    return r[k]
            return None
        return r
    if isinstance(result, dict):
        # 兼容 result.token.accessToken 嵌套
        for k in ("accessToken", "access_token", "token"):
            if result.get(k):
                val = result[k]
                if isinstance(val, dict):
                    for k2 in ("accessToken", "access_token", "token"):
                        if val.get(k2):
                            return val[k2]
                else:
                    return val
    # 3) 再兜底
    for p in ("token", "access_token", "data.accessToken", "data.access_token",
              "result.access_token", "result.token.accessToken"):
        v2 = _deep_get(data, p)
        if v2 and not isinstance(v2, dict):
            return v2
        if v2 and isinstance(v2, dict):
            for k in ("accessToken", "access_token", "token"):
                if v2.get(k):
                    return v2[k]
    return None


def _encrypt_password(pwd):
    """复刻前端 c436 模块密码加密：XOR(key, pwd) → btoa → reverse → btoa → reverse"""
    import base64 as _b64
    KEY = "xNDFz6LH67LOv7xKbWFpbMu1wejrM7SzvV4tLRvq3X47m708O1xMHLoaMNCqGhoaEN"
    xor = "".join(chr(ord(KEY[i]) ^ ord(pwd[i])) for i in range(len(pwd)))
    s1 = _b64.b64encode(xor.encode("latin1")).decode("ascii")
    s2 = s1[::-1]
    s3 = _b64.b64encode(s2.encode("latin1")).decode("ascii")
    return s3[::-1]


def account_login(cfg, base):
    """账密登录模式：POST /account/v1/login（密码按前端算法加密）→ result.token.accessToken。
    返回 (token or None, error)"""
    auth = cfg.get("auth") or {}
    acct = auth.get("account") or {}
    user_name = acct.get("user_name")
    password = acct.get("password")
    if not user_name or not password:
        return None, "auth.mode=account 但未配置 account.user_name/password"
    try:
        login_url = base + acct.get("login_endpoint", "/account/v1/login")
        body = {
            "userName": user_name,
            "password": _encrypt_password(str(password)),
            "language": acct.get("language", "zh_CN"),
            "platform": acct.get("platform", "PC"),
        }
        if acct.get("captcha"):
            body["captcha"] = acct["captcha"]
        resp = requests.post(login_url, json=body,
                             headers={"Content-Type": "application/json"}, timeout=15)
        data = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else resp.text
        if isinstance(data, dict) and data.get("code") not in (None, 0):
            exc = data.get("exception") or {}
            return None, f"登录失败: {exc.get('errorMessage') or data}"
        token = _extract_token(data, auth.get("token_field") or "result.token.accessToken")
        if not token:
            return None, f"登录响应未找到 token: {str(data)[:200]}"
        # 保存 refreshToken
        refresh = None
        res = data.get("result") if isinstance(data, dict) else None
        if isinstance(res, str) and res.startswith("{"):
            try:
                res = json.loads(res)
            except Exception:
                pass
        if isinstance(res, dict):
            tok = res.get("token") if isinstance(res.get("token"), dict) else {}
            refresh = tok.get("refreshToken") or tok.get("refresh_token")
        auth["token"] = token
        auth["token_at"] = time.time()
        if refresh:
            auth["refresh_token"] = refresh
        save_config(cfg)
        return token, None
    except requests.exceptions.ConnectTimeout:
        return None, "登录超时"
    except Exception as e:
        return None, f"登录失败: {str(e)[:120]}"


def sso_login(cfg, base):
    """SSO 两段式换取 accessToken。返回 (token or None, error)"""
    auth = cfg.get("auth") or {}
    sso = auth.get("sso") or {}
    user_no = sso.get("user_no")
    app_id = sso.get("app_id")
    app_secret = sso.get("app_secret")
    if not user_no or not app_id or not app_secret:
        return None, "auth.mode=sso 但未配置 sso.user_no/app_id/app_secret"
    try:
        # ① 获取临时授权码
        code_url = base + sso.get("code_endpoint", "/sso/v1/code")
        code_body = {"userNo": user_no, "appId": app_id}
        if sso.get("scope"):
            code_body["scope"] = sso["scope"]
        resp = requests.post(code_url, json=code_body,
                             headers={"Content-Type": "application/json"}, timeout=15)
        data = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else resp.text
        if isinstance(data, dict) and data.get("code") != 0:
            exc = data.get("exception") or {}
            return None, f"获取授权码失败: {exc.get('errorMessage') or data}"
        code = _deep_get(data, "result") if isinstance(data, dict) else None
        if not code:
            return None, f"获取授权码响应无 result: {str(data)[:150]}"
        # ② 用 code 换 accessToken
        tok_url = base + sso.get("token_endpoint", "/sso/v1/token")
        tok_body = {
            "appId": app_id,
            "appSecret": app_secret,
            "code": code,
            "language": sso.get("language", "zh_CN"),
            "envType": sso.get("env_type", "sMOMDev"),
            "mode": sso.get("mode", "Url"),
        }
        for opt in ("appNo", "platform", "pageNo"):
            if sso.get(opt.lower()):
                tok_body[opt] = sso[opt.lower()]
        resp2 = requests.post(tok_url, json=tok_body,
                              headers={"Content-Type": "application/json"}, timeout=15)
        data2 = resp2.json() if resp2.headers.get("content-type", "").startswith("application/json") else resp2.text
        if isinstance(data2, dict) and data2.get("code") != 0:
            exc = data2.get("exception") or {}
            return None, f"换取 accessToken 失败: {exc.get('errorMessage') or data2}"
        token = _extract_token(data2, auth.get("token_field"))
        if not token:
            return None, f"token 响应未找到 accessToken: {str(data2)[:200]}"
        # 保存 refreshToken（供刷新）
        refresh = None
        res = data2.get("result") if isinstance(data2, dict) else None
        if isinstance(res, str) and res.startswith("{"):
            try:
                res = json.loads(res)
            except Exception:
                pass
        if isinstance(res, dict):
            refresh = res.get("refreshToken") or res.get("refresh_token")
        auth["token"] = token
        auth["token_at"] = time.time()
        if refresh:
            auth["refresh_token"] = refresh
        save_config(cfg)
        return token, None
    except requests.exceptions.ConnectTimeout:
        return None, "SSO 登录超时"
    except Exception as e:
        return None, f"SSO 登录失败: {str(e)[:120]}"


def ensure_token(cfg, base, force=False):
    """确保有有效 token；无/过期则走 SSO 换取。返回 (token or None, error)"""
    auth = cfg.get("auth") or {}
    if not auth.get("enabled"):
        return None, None
    token = auth.get("token")
    got_at = auth.get("token_at", 0)
    if token and not force and (time.time() - got_at) < TOKEN_TTL:
        return token, None
    if auth.get("mode") == "sso":
        return sso_login(cfg, base)
    if auth.get("mode") == "account":
        return account_login(cfg, base)
    # 兼容旧模式：单接口登录（username/password）
    login_url = base + auth.get("login_endpoint", "/OAPI/login")
    body = auth.get("login_body", {})
    if not body.get("username"):
        return None, "auth 已启用但未配置 login_body（username/password）"
    try:
        resp = requests.post(login_url, json=body,
                             headers={"Content-Type": "application/json"}, timeout=15)
        data = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else resp.text
        token = _extract_token(data, auth.get("token_field"))
        if not token:
            return None, f"登录响应未找到 token: {str(data)[:150]}"
        auth["token"] = token
        auth["token_at"] = time.time()
        save_config(cfg)
        return token, None
    except requests.exceptions.ConnectTimeout:
        return None, "登录超时"
    except Exception as e:
        return None, f"登录失败: {str(e)[:120]}"


def call_api(endpoint, payload, method="POST", timeout=None, retries=None, use_auth=True):
    """调用接口，自动失败重试。endpoint 形如 /open-api/bp/erp_eq"""
    cfg = load_config()
    server = cfg["server"]
    base = f"http://{server['host']}:{server['port']}"
    url = base + endpoint
    timeout = timeout or cfg.get("timeout_seconds", 30)
    retries = retries if retries is not None else cfg.get("max_retries", 2)

    auth = cfg.get("auth") or {}
    token = None
    if use_auth and auth.get("enabled"):
        token, err = ensure_token(cfg, base)
        if err:
            return {"ok": False, "status": None, "data": None, "error": err}

    last_err = None
    for attempt in range(retries + 1):
        headers = {"Content-Type": "application/json"}
        if token:
            headers[auth.get("token_header", "Authorization")] = auth.get("token_prefix", "Bearer ") + token
        try:
            if method.upper() == "POST":
                resp = requests.post(url, json=payload, headers=headers, timeout=timeout)
            else:
                resp = requests.get(url, params=payload, headers=headers, timeout=timeout)
            try:
                data = resp.json()
            except Exception:
                data = resp.text
            # token 失效（401）时强制重新换取重试一次
            if resp.status_code == 401 and token and attempt == 0:
                token, err = ensure_token(cfg, base, force=True)
                if err:
                    return {"ok": False, "status": 401, "data": data, "error": err}
                continue
            if resp.status_code >= 400:
                return {"ok": False, "status": resp.status_code, "data": data,
                        "error": f"HTTP {resp.status_code}"}
            return {"ok": True, "status": resp.status_code, "data": data, "error": None}
        except requests.exceptions.Timeout:
            last_err = f"超时({timeout}s)"
        except requests.exceptions.ConnectionError as e:
            last_err = f"连接失败: {e}"
        except Exception as e:
            last_err = str(e)
        if attempt < retries:
            time.sleep(1)
    return {"ok": False, "status": None, "data": None, "error": last_err}


if __name__ == "__main__":
    import sys
    ep = sys.argv[1] if len(sys.argv) > 1 else "/open-api/bp/erp_eq"
    payload = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
    r = call_api(ep, payload)
    print(json.dumps(r, ensure_ascii=False, indent=2, default=str))
