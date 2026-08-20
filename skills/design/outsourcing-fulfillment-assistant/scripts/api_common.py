#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
委外发货回货 · OpenAPI 共享模块（标准 SSO/账密 Bearer Token 鉴权）
==========================================================
提供:config 读取 / POST JSON / SSO 两段式鉴权 / 账密登录 / Bearer Token 自动携带 / 401 强制刷新重试。

鉴权模式(auth.mode):
  - account: POST /account/v1/login(密码前端算法加密) → result.token.accessToken
  - sso:     POST /sso/v1/code(userNo+appId 拿临时授权码) → POST /sso/v1/token(appId+appSecret 换 accessToken)
             请求头 Authorization: Bearer {accessToken}
token 缓存到本地文件(1 小时有效);401 时强制刷新重试一次。
"""
import json, os, time, base64 as _b64, urllib.request, urllib.error

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_CONFIG = os.path.join(SKILL_DIR, 'config.json')   # 根目录 config.json(与 db.py 同一份)
TOKEN_CACHE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.sso_token_cache.json')
TOKEN_TTL = 3500  # accessToken 有效期(秒),1 小时,提前 100s 刷新

_CFG = None


def load_config(path=None):
    global _CFG
    with open(path or DEFAULT_CONFIG, 'r', encoding='utf-8') as f:
        cfg = json.load(f)
    _CFG = cfg
    host = cfg['server']['host']
    port = cfg['server']['port']
    base = f"http://{host}:{port}"
    return base, cfg.get('apis', {})


def _post_json(url, body, headers=None, timeout=30):
    """通用 POST JSON，返回 (http_code, 解析结果)。HTTP 错误时尝试解析 body JSON。"""
    req = urllib.request.Request(url, data=json.dumps(body).encode(),
                                 headers=headers or {'Content-Type': 'application/json'}, method='POST')
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.getcode(), json.loads(r.read())
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode('utf-8', errors='replace'))
        except Exception:
            return e.code, e.read().decode('utf-8', errors='replace')
    except Exception as e:
        return 0, str(e)


def _deep_get(obj, path):
    cur = obj
    for part in str(path).split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        elif isinstance(cur, list) and part.isdigit() and int(part) < len(cur):
            cur = cur[int(part)]
        else:
            return None
    return cur


def _extract_token(data):
    """从登录/SSO 响应提取 accessToken（兼容 result 为字符串/JSON字符串/对象）"""
    if not isinstance(data, dict):
        return None
    result = data.get('result')
    if isinstance(result, str) and result.strip():
        r = result.strip()
        if r.startswith('{'):
            try:
                r = json.loads(r)
            except Exception:
                pass
        if isinstance(r, dict):
            for k in ('accessToken', 'access_token', 'token'):
                if r.get(k):
                    v = r[k]
                    if isinstance(v, dict):
                        for k2 in ('accessToken', 'access_token', 'token'):
                            if v.get(k2):
                                return v[k2]
                    return v
            return None
        return r
    if isinstance(result, dict):
        for k in ('accessToken', 'access_token', 'token'):
            if result.get(k):
                v = result[k]
                if isinstance(v, dict):
                    for k2 in ('accessToken', 'access_token', 'token'):
                        if v.get(k2):
                            return v[k2]
                return v
    return None


def _encrypt_password(pwd):
    """复刻前端 c436 模块密码加密：XOR(key, pwd) → btoa → reverse → btoa → reverse"""
    KEY = "xNDFz6LH67LOv7xKbWFpbMu1wejrM7SzvV4tLRvq3X47m708O1xMHLoaMNCqGhoaEN"
    xor = "".join(chr(ord(KEY[i]) ^ ord(pwd[i])) for i in range(len(pwd)))
    s1 = _b64.b64encode(xor.encode("latin1")).decode("ascii")
    s2 = s1[::-1]
    s3 = _b64.b64encode(s2.encode("latin1")).decode("ascii")
    return s3[::-1]


def _read_token_cache():
    if os.path.exists(TOKEN_CACHE_FILE):
        try:
            with open(TOKEN_CACHE_FILE, 'r', encoding='utf-8') as f:
                c = json.load(f)
            if c.get('token') and (time.time() - c.get('ts', 0)) < TOKEN_TTL:
                return c['token']
        except Exception:
            pass
    return None


def _write_token_cache(token):
    try:
        with open(TOKEN_CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump({'ts': time.time(), 'token': token}, f)
    except Exception:
        pass


def account_login(base, cfg, force=False):
    """账密登录模式 → accessToken"""
    auth = cfg.get('auth') or {}
    acct = auth.get('account') or {}
    user_name, password = acct.get('user_name'), acct.get('password')
    if not force:
        t = _read_token_cache()
        if t:
            return t, None
    if not user_name or not password:
        return None, "auth.mode=account 但未配置 account.user_name/password"
    body = {
        'userName': user_name,
        'password': _encrypt_password(str(password)),
        'language': acct.get('language', 'zh_CN'),
        'platform': acct.get('platform', 'PC'),
    }
    if acct.get('captcha'):
        body['captcha'] = acct['captcha']
    code, resp = _post_json(base + acct.get('login_endpoint', '/account/v1/login'), body)
    if isinstance(resp, dict) and resp.get('code') not in (None, 0):
        exc = resp.get('exception') or {}
        return None, f"登录失败: {exc.get('errorMessage') or resp}"
    token = _extract_token(resp)
    if not token:
        return None, f"登录响应未找到 token: {str(resp)[:200]}"
    _write_token_cache(token)
    return token, None


def ensure_token(base, cfg, force=False):
    """获取 accessToken（SSO 两段式 或 账密登录），缓存 1 小时。返回 (token, error)"""
    auth = cfg.get('auth') or {}
    if not auth.get('enabled'):
        return None, None
    if auth.get('mode') == 'account':
        return account_login(base, cfg, force)
    sso = auth.get('sso') or {}
    if not force:
        t = _read_token_cache()
        if t:
            return t, None
    if not sso.get('user_no') or not sso.get('app_id') or not sso.get('app_secret'):
        return None, "auth.mode=sso 但未配置 sso.user_no/app_id/app_secret"
    # ① 临时授权码
    code, resp = _post_json(base + sso.get('code_endpoint', '/sso/v1/code'),
                            {'userNo': sso['user_no'], 'appId': sso['app_id']})
    if isinstance(resp, dict) and resp.get('code') != 0:
        exc = resp.get('exception') or {}
        return None, f"获取授权码失败: {exc.get('errorMessage') or resp}"
    code_val = _deep_get(resp, 'result') if isinstance(resp, dict) else None
    if not code_val:
        return None, f"获取授权码响应无 result: {str(resp)[:150]}"
    # ② 换 accessToken
    tok_body = {
        'appId': sso['app_id'], 'appSecret': sso['app_secret'], 'code': code_val,
        'language': sso.get('language', 'zh_CN'),
        'envType': sso.get('env_type', 'sMES'),
        'mode': sso.get('mode', 'Url'),
    }
    for opt in ('appNo', 'platform', 'pageNo'):
        if sso.get(opt.lower()):
            tok_body[opt] = sso[opt.lower()]
    code2, resp2 = _post_json(base + sso.get('token_endpoint', '/sso/v1/token'), tok_body)
    if isinstance(resp2, dict) and resp2.get('code') != 0:
        exc = resp2.get('exception') or {}
        return None, f"换取 accessToken 失败: {exc.get('errorMessage') or resp2}"
    token = _extract_token(resp2)
    if not token:
        return None, f"token 响应未找到 accessToken: {str(resp2)[:200]}"
    _write_token_cache(token)
    return token, None


def post(base, path, body):
    """POST 到 OpenAPI（自动带 Bearer Token；401 强制刷新重试一次）"""
    cfg = _CFG
    if cfg is None:
        load_config()
        cfg = _CFG
    auth = cfg.get('auth') or {}
    token, err = None, None
    if auth.get('enabled'):
        token, err = ensure_token(base, cfg)
        if err:
            return 401, {'exception': {'errorMessage': err}}
    headers = {'Content-Type': 'application/json'}
    if token:
        headers[auth.get('token_header', 'Authorization')] = auth.get('token_prefix', 'Bearer ') + token
    code, resp = _post_json(base + path, body, headers)
    if code == 401 and token and auth.get('enabled'):
        token, err = ensure_token(base, cfg, force=True)
        if err:
            return code, {'exception': {'errorMessage': err}}
        headers[auth.get('token_header', 'Authorization')] = auth.get('token_prefix', 'Bearer ') + token
        code, resp = _post_json(base + path, body, headers)
    return code, resp


def _result(r):
    """新接口响应统一 {code, result, serverTime}，数据在 result 里；兼容旧格式直接返回。"""
    if isinstance(r, dict) and isinstance(r.get('result'), dict):
        return r['result']
    return r or {}


# 供应商绩效列序(接口 getOutSourceDash 返回字段,与数据库全景汇总一致)
PERF_COLS = ['SUPPLIER_ID', 'SUPPLIER_NAME', 'HANDS_ORDER_CNT', 'HANDS_SEND_QTY',
             'GOOD_RATE', 'ONTIME_RATE', 'CHECK_TOTAL_QTY', 'NG_QTY',
             'FINISHED_CNT', 'OVERDUE_CNT']


def fetch_supplier_perf():
    """调 getOutSourceDash 获取供应商近一年绩效(无需参数,返回 list)。
    返回 (PERF_COLS, rows) 或 (None, 错误信息)。"""
    try:
        base, apis = load_config()
        path = apis.get('querySupplierPerf')
        if not path:
            return None, "config.json apis.querySupplierPerf 未配置"
        code, resp = post(base, path, {})
        if code != 200:
            exc = resp.get('exception') if isinstance(resp, dict) else {}
            return None, f"getOutSourceDash 失败(code={code}): {exc.get('errorMessage') or resp}"
        result = _result(resp)
        lst = result.get('list') if isinstance(result, dict) else result
        if isinstance(lst, list) and lst:
            return PERF_COLS, [tuple(r.get(c, 0) for c in PERF_COLS) for r in lst]
        return None, f"响应未找到 list: {str(result)[:150]}"
    except Exception as e:
        return None, str(e)


# ---------------- 两个独立数据实体(2026-08-17 用户要求分开处理,不共用容器) ----------------
# 实体A: 可委外清单(getCanOutsourceList) → 响应容器 canOutList
# 实体B: 待回货清单(getOutSourceList)   → 响应容器 MOLIST(待回货专用,与可委外清单无关)


def fetch_can_outsource(body):
    """实体A: 可委外清单。调 getCanOutsourceList,只解析其容器 canOutList。
    返回 (rows, error);error 非空表示失败。"""
    base, apis = load_config()
    path = apis.get('querySendList')
    if not path:
        return None, "config.json apis.querySendList 未配置(getCanOutsourceList)"
    code, resp = post(base, path, body)
    if code != 200:
        exc = resp.get('exception') if isinstance(resp, dict) else {}
        return None, f"getCanOutsourceList 失败(code={code}): {exc.get('errorMessage') or resp}"
    result = _result(resp)
    lst = result.get('canOutList') if isinstance(result, dict) else None
    if not isinstance(lst, list):
        return None, f"可委外清单实体:响应未找到 canOutList 容器: {str(result)[:150]}"
    return lst, None


def fetch_back_list(body):
    """实体B: 待回货清单。调 getOutSourceList,只解析其容器 MOLIST。
    返回 (rows, error);error 非空表示失败。"""
    base, apis = load_config()
    path = apis.get('queryBackList')
    if not path:
        return None, "config.json apis.queryBackList 未配置(getOutSourceList)"
    code, resp = post(base, path, body)
    if code != 200:
        exc = resp.get('exception') if isinstance(resp, dict) else {}
        return None, f"getOutSourceList 失败(code={code}): {exc.get('errorMessage') or resp}"
    result = _result(resp)
    lst = result.get('MOLIST') if isinstance(result, dict) else None
    if not isinstance(lst, list):
        return None, f"待回货清单实体:响应未找到 MOLIST 容器: {str(result)[:150]}"
    return lst, None
