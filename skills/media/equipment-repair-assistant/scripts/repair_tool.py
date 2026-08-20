#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MES 设备智能报修助手 CLI 工具
========================
参数化调用，避免每次重写脚本。仿语音报工 report_tool.py。

用法:
  python repair_tool.py --action candidates --eq "数控中心"      # 报修候选：历史故障+通用原因+系统字典
  python repair_tool.py --action list    --eq "数控中心"          # 查设备维修单（含状态机判断）
  python repair_tool.py --action create  --eq "数控中心" --reason "打码机故障" --dry-run  # 预览
  python repair_tool.py --action create  --eq "数控中心" --reason "打码机故障"            # 确认生成
  python repair_tool.py --action start   --eq "XH1C1001" --dry-run
  python repair_tool.py --action start   --eq "XH1C1001"
  python repair_tool.py --action end     --eq "XH1C1001" --items "维修=1;润滑=正常" --dry-run
  python repair_tool.py --action end     --eq "XH1C1001" --items "维修=1;润滑=正常"

参数:
  --action   create(报修生成维修单) | list(查设备维修单) | start(开始维修) | end(结束维修) | candidates(报修原因候选)
  --eq       设备编号或名称关键词（匹配 EQ_ID / EQ_NAME，取最优一条）
  --reason   故障原因名称（create 用，AIGetCollData COLLECTION_TYPE=8 解析 DCCDID）
  --repair   维修单号 eqMainId（start/end 用；不传则自动取该设备状态最匹配的一张）
  --items    结束维修项目结果，格式 "项目1=结果1;项目2=结果2"
  --picture  结束维修图片（可选，默认空）
  --config   config.json 路径（默认同目录）
  --no-cache 强制刷新缓存
  --dry-run  只查询+匹配+输出计划，不调用任何执行接口（防重复执行铁律）
"""
import json, urllib.request, urllib.error, os, sys, time, argparse

DEFAULT_CONFIG = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json')
CACHE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.eqlist_cache.json')
REASON_CACHE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.reason8_cache.json')
TOKEN_CACHE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.sso_token_cache.json')
CACHE_TTL = 30  # 秒
TOKEN_TTL = 3500  # accessToken 有效期（秒），1 小时，提前 100s 刷新

_CFG = None  # 当前生效配置（load_config 时更新）

# 维修单状态（用户确认）
ST_PLAN = 0    # 计划中
ST_MAINT1 = 1  # 保养中
ST_MAINT2 = 2  # 保养完成
ST_WAIT = 3    # 待维修  ← 可开始
ST_DONE = 4    # 维修完成
ST_ING = 5     # 维修中   ← 可结束

# 设备状态（AIgetEqStatusList 返回）
EQ_ST_FAULT = 6  # 故障


def load_config(path):
    global _CFG
    with open(path, 'r', encoding='utf-8') as f:
        cfg = json.load(f)
    _CFG = cfg
    host = cfg['server']['host']
    port = cfg['server']['port']
    base = f"http://{host}:{port}"
    apis = cfg.get('apis', {})
    return base, apis, cfg


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
    """从登录/token 响应提取 accessToken（兼容 result 为字符串/JSON字符串/对象/嵌套 result.token）"""
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
    import base64 as _b64
    KEY = "xNDFz6LH67LOv7xKbWFpbMu1wejrM7SzvV4tLRvq3X47m708O1xMHLoaMNCqGhoaEN"
    xor = "".join(chr(ord(KEY[i]) ^ ord(pwd[i])) for i in range(len(pwd)))
    s1 = _b64.b64encode(xor.encode("latin1")).decode("ascii")
    s2 = s1[::-1]
    s3 = _b64.b64encode(s2.encode("latin1")).decode("ascii")
    return s3[::-1]


def account_login(base, cfg, force=False):
    """账密登录模式：POST /account/v1/login（密码按前端算法加密）→ result.token.accessToken。
    返回 (token or None, error)。token 缓存到本地文件（1 小时有效）。"""
    auth = cfg.get('auth') or {}
    acct = auth.get('account') or {}
    user_name = acct.get('user_name')
    password = acct.get('password')
    if not force and os.path.exists(TOKEN_CACHE_FILE):
        try:
            with open(TOKEN_CACHE_FILE, 'r', encoding='utf-8') as f:
                c = json.load(f)
            if c.get('token') and (time.time() - c.get('ts', 0)) < TOKEN_TTL:
                return c['token'], None
        except Exception:
            pass
    if not user_name or not password:
        return None, "auth.mode=account 但未配置 account.user_name/password"
    login_url = base + acct.get('login_endpoint', '/account/v1/login')
    body = {
        'userName': user_name,
        'password': _encrypt_password(str(password)),
        'language': acct.get('language', 'zh_CN'),
        'platform': acct.get('platform', 'PC'),
    }
    if acct.get('captcha'):
        body['captcha'] = acct['captcha']
    code, resp = _post_json(login_url, body)
    if isinstance(resp, dict) and resp.get('code') not in (None, 0):
        exc = resp.get('exception') or {}
        return None, f"登录失败: {exc.get('errorMessage') or resp}"
    token = _extract_token(resp)
    if not token:
        return None, f"登录响应未找到 token: {str(resp)[:200]}"
    try:
        with open(TOKEN_CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump({'ts': time.time(), 'token': token}, f)
    except Exception:
        pass
    return token, None


def ensure_token(base, cfg, force=False):
    """获取 accessToken（SSO 两段式 或 账密登录），缓存到本地文件（1 小时有效）。
    返回 (token or None, error)。"""
    auth = cfg.get('auth') or {}
    if not auth.get('enabled'):
        return None, None
    if auth.get('mode') == 'account':
        return account_login(base, cfg, force)
    sso = auth.get('sso') or {}
    # 缓存检查
    token = None
    if not force and os.path.exists(TOKEN_CACHE_FILE):
        try:
            with open(TOKEN_CACHE_FILE, 'r', encoding='utf-8') as f:
                c = json.load(f)
            if c.get('token') and (time.time() - c.get('ts', 0)) < TOKEN_TTL:
                return c['token'], None
        except Exception:
            pass
    if not sso.get('user_no') or not sso.get('app_id') or not sso.get('app_secret'):
        return None, "auth.mode=sso 但未配置 sso.user_no/app_id/app_secret"
    # ① 获取临时授权码
    code_url = base + sso.get('code_endpoint', '/sso/v1/code')
    code, resp = _post_json(code_url, {'userNo': sso['user_no'], 'appId': sso['app_id']})
    if isinstance(resp, dict) and resp.get('code') != 0:
        exc = resp.get('exception') or {}
        return None, f"获取授权码失败: {exc.get('errorMessage') or resp}"
    code_val = _deep_get(resp, 'result') if isinstance(resp, dict) else None
    if not code_val:
        return None, f"获取授权码响应无 result: {str(resp)[:150]}"
    # ② 换 accessToken
    tok_url = base + sso.get('token_endpoint', '/sso/v1/token')
    tok_body = {
        'appId': sso['app_id'], 'appSecret': sso['app_secret'], 'code': code_val,
        'language': sso.get('language', 'zh_CN'),
        'envType': sso.get('env_type', 'sMOMDev'),
        'mode': sso.get('mode', 'Url'),
    }
    for opt in ('appNo', 'platform', 'pageNo'):
        if sso.get(opt.lower()):
            tok_body[opt] = sso[opt.lower()]
    code2, resp2 = _post_json(tok_url, tok_body)
    if isinstance(resp2, dict) and resp2.get('code') != 0:
        exc = resp2.get('exception') or {}
        return None, f"换取 accessToken 失败: {exc.get('errorMessage') or resp2}"
    token = _extract_token(resp2)
    if not token:
        return None, f"token 响应未找到 accessToken: {str(resp2)[:200]}"
    try:
        with open(TOKEN_CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump({'ts': time.time(), 'token': token}, f)
    except Exception:
        pass
    return token, None


def post(base, path, body):
    """POST 到 OpenAPI（自动带 SSO Bearer Token；401 强制刷新重试一次）"""
    cfg = _CFG if _CFG is not None else load_config(DEFAULT_CONFIG)[2]
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
    # 401 → 强制刷新 token 重试一次
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


def get_eq_list(base, apis, use_cache=True):
    """获取全量设备清单（接口不做过滤，客户端匹配）。"""
    path = apis.get('eqStatusList', '/open-api/bp/AIgetEqStatusList')
    if use_cache and os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                cache = json.load(f)
            if time.time() - cache.get('ts', 0) < CACHE_TTL:
                return cache['eqList']
        except Exception:
            pass
    _, r = post(base, path, {})
    eq_list = _result(r).get('eqList', []) if isinstance(r, dict) else []
    try:
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump({'ts': time.time(), 'eqList': eq_list}, f, ensure_ascii=False)
    except Exception:
        pass
    return eq_list


def get_fault_reasons(base, apis, use_cache=True):
    """获取故障原因字典（COLLECTION_TYPE=8）。返回 LIST。"""
    path = apis.get('collData', '/open-api/bp/AIGetCollData')
    if use_cache and os.path.exists(REASON_CACHE_FILE):
        try:
            with open(REASON_CACHE_FILE, 'r', encoding='utf-8') as f:
                cache = json.load(f)
            if time.time() - cache.get('ts', 0) < CACHE_TTL:
                return cache['list']
        except Exception:
            pass
    # 键名必须大写 COLLECTION_TYPE（小写报"属性 [COLLECTION_TYPE] 必填"）
    _, r = post(base, path, {'COLLECTION_TYPE': 8})
    lst = _result(r).get('LIST', []) if isinstance(r, dict) else []
    try:
        with open(REASON_CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump({'ts': time.time(), 'list': lst}, f, ensure_ascii=False)
    except Exception:
        pass
    return lst


def resolve_reason_id(reason_list, reason_name=None):
    """按名称解析 reasonId（DCCDID）。同报废原因规则。"""
    if not reason_list:
        return 0
    default_id = int(reason_list[0].get('DCCDID', 0))
    if not reason_name:
        return default_id
    name = str(reason_name).strip()
    if not name:
        return default_id
    for it in reason_list:
        if str(it.get('COLLECTION_CHOICE_NAME', '')).strip() == name:
            return int(it['DCCDID'])
    for it in reason_list:
        if str(it.get('COLLECTION_NAME', '')).strip() == name:
            return int(it['DCCDID'])
    for it in reason_list:
        choice = str(it.get('COLLECTION_CHOICE_NAME', ''))
        if choice and (name in choice or choice in name):
            return int(it['DCCDID'])
    for it in reason_list:
        coll = str(it.get('COLLECTION_NAME', ''))
        if coll and (name in coll or coll in name):
            return int(it['DCCDID'])
    return default_id


def resolve_reason_name(reason_list, reason_id):
    """按 DCCDID 反查原因名（用于展示）。"""
    for it in reason_list:
        if int(it.get('DCCDID', 0)) == reason_id:
            return it.get('COLLECTION_CHOICE_NAME') or it.get('COLLECTION_NAME') or ''
    return ''


def match_eq(eq_list, keyword):
    """按关键词匹配设备，返回按相似度排序的候选。精确>包含；EQ_ID 优先于 EQ_NAME。"""
    if not eq_list or not keyword:
        return []
    kw = str(keyword).strip().upper()
    if not kw:
        return []
    cands = []
    for e in eq_list:
        eq_id = str(e.get('EQ_ID', '') or '').upper()
        eq_name = str(e.get('EQ_NAME', '') or '').upper()
        score = 0
        if eq_id == kw:
            score = 100
        elif eq_name == kw:
            score = 90
        elif kw in eq_id:
            score = 70
        elif kw in eq_name:
            score = 60
        if score > 0:
            cands.append((score, e))
    cands.sort(key=lambda x: -x[0])
    return [c for _, c in cands]


def get_eq_main_list(base, apis, eq_id):
    """查询设备维修单。"""
    path = apis.get('eqMainList', '/open-api/bp/AIgetEqMainList')
    _, r = post(base, path, {'EQ_ID': eq_id})
    return _result(r).get('eqMainList', []) if isinstance(r, dict) else []


def get_oee(base, apis, eq_id):
    """查询设备历史稼动/故障记录（AIGetOee）。"""
    path = apis.get('eqOee', '/open-api/bp/AIGetOee')
    _, r = post(base, path, {'EQ_ID': eq_id})
    return _result(r).get('list', []) if isinstance(r, dict) else []


def guess_eq_type(eq_name, eq_id=''):
    """根据设备名/ID 猜设备类型：注塑机 / CNC / 通用。"""
    s = (str(eq_name or '') + str(eq_id or '')).upper()
    if any(k in s for k in ('注塑', '射出', 'INJECTION')):
        return '注塑机'
    if any(k in s for k in ('数控', '加工中心', 'CNC', '车床', '铣床', '钻床', '磨床', '加工')):
        return 'CNC'
    return '通用'


def load_generic_reasons(path):
    """读取 fault_reasons.json 通用原因库。"""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}


def build_candidates(base, apis, eq, use_cache=True):
    """报修候选 = 系统字典原因（AIGetCollData COLLECTION_TYPE=8，唯一带 DCCDID 可建单的来源）。
    历史故障(AIGetOee)原因名若能在系统字典匹配到 DCCDID 则并入前置；
    通用原因库(fault_reasons.json)不含系统 ID 不可直接建单，不列入候选（建议走新增接口录入系统后生效）。
    返回 (eq_id, eq_name, eq_type, reasons[])  reasons 每项 {name, source, id?}"""
    eq_id, eq_name = eq.get('EQ_ID'), eq.get('EQ_NAME')
    eq_type = guess_eq_type(eq_name, eq_id)
    reason_list = get_fault_reasons(base, apis, use_cache)

    # 系统字典：名称 → DCCDID（唯一可传给 AIEqError 的 ID）
    dict_name2id = {}
    for it in reason_list:
        name = str(it.get('COLLECTION_CHOICE_NAME') or '').strip()
        if name and name not in dict_name2id:
            dict_name2id[name] = int(it.get('DCCDID', 0))

    reasons = []
    seen = set()

    # ① 历史故障：仅保留能在系统字典匹配到 DCCDID 的（排最前）
    for rec in get_oee(base, apis, eq_id):
        name = str(rec.get('COLLECTION_CHOICE_NAME') or '').strip()
        if name and name in dict_name2id and name not in seen:
            seen.add(name)
            reasons.append({'name': name, 'source': '历史', 'id': dict_name2id[name]})

    # ② 系统字典全部原因（去重）
    for it in reason_list:
        name = str(it.get('COLLECTION_CHOICE_NAME') or '').strip()
        if name and name not in seen:
            seen.add(name)
            reasons.append({'name': name, 'source': '系统', 'id': dict_name2id[name]})

    return eq_id, eq_name, eq_type, reasons

    return eq_id, eq_name, eq_type, reasons


def pick_repair(repairs, action):
    """按状态机规则挑选可操作的维修单：
       start → 状态3(待维修)；end → 状态5(维修中)。"""
    target = ST_WAIT if action == 'start' else ST_ING
    for r in repairs:
        if r.get('EQ_MAINTENANCE_STATUS') == target:
            return r
    return None


def send_record(base, apis, main_operate, eq_main_id, main_record, picture=''):
    """执行开始/结束维修（AIsendEqMainRecord）。"""
    path = apis.get('sendEqMainRecord', '/open-api/bp/sendEqMainRecord')
    body = {'mainOperate': main_operate, 'eqMainId': eq_main_id,
            'mainRecord': main_record, 'picture': picture}
    return post(base, path, body)


def parse_items(items_str):
    """解析 '项目1=结果1;项目2=结果2' → [{'EQ_MAINTENANCE_ITEM':..., 'EQ_MAINTENANCE_RECORD':...}]"""
    out = []
    if not items_str:
        return out
    for seg in items_str.split(';'):
        seg = seg.strip()
        if not seg:
            continue
        if '=' in seg:
            k, v = seg.split('=', 1)
        elif ':' in seg:
            k, v = seg.split(':', 1)
        else:
            k, v = seg, ''
        out.append({'EQ_MAINTENANCE_ITEM': k.strip(), 'EQ_MAINTENANCE_RECORD': v.strip()})
    return out


def main():
    t_start = time.time()
    ap = argparse.ArgumentParser()
    ap.add_argument('--action', required=True, choices=['create', 'list', 'start', 'end', 'candidates'])
    ap.add_argument('--eq', required=True, help='设备编号或名称关键词')
    ap.add_argument('--reason', default=None, help='故障原因名称（create 用）')
    ap.add_argument('--reason-id', default=None, help='故障原因 DCCDID（create 用，AI 从 candidates 序号取到直接传，优先于 --reason）')
    ap.add_argument('--repair', default=None, help='维修单号 eqMainId（start/end 用，默认自动取）')
    ap.add_argument('--items', default='', help='结束维修项目结果 "项目=结果;项目2=结果2"')
    ap.add_argument('--picture', default='', help='结束维修图片路径（可选）')
    ap.add_argument('--config', default=DEFAULT_CONFIG)
    ap.add_argument('--no-cache', action='store_true')
    ap.add_argument('--dry-run', action='store_true', help='只查询匹配+预览，不调用执行接口')
    args = ap.parse_args()

    base, apis, cfg = load_config(args.config)
    use_cache = not args.no_cache

    # ── 1. 设备匹配（全量拉取 + 客户端匹配）──
    eq_list = get_eq_list(base, apis, use_cache)
    cands = match_eq(eq_list, args.eq)
    if not cands:
        print(json.dumps({'ok': False, 'reason': 'no_eq',
                          'message': f'未找到匹配设备：{args.eq}'}, ensure_ascii=False))
        sys.exit(2)
    eq = cands[0]
    eq_id, eq_name = eq.get('EQ_ID'), eq.get('EQ_NAME')
    if len(cands) > 1:
        print(json.dumps({'ok': True, 'notice': 'multi_eq_candidates',
                          'eq': eq_id, 'eq_name': eq_name,
                          'candidates': [{'EQ_ID': c.get('EQ_ID'), 'EQ_NAME': c.get('EQ_NAME')} for c in cands[:5]],
                          'message': '命中多条设备，默认取最优一条，如不符请用更精确的设备编号'},
                         ensure_ascii=False, indent=2))

    # ── 2. 按 action 分发 ──
    if args.action == 'candidates':
        eq_id, eq_name, eq_type, reasons = build_candidates(base, apis, eq, use_cache)
        out = {'ok': True, 'action': 'candidates', 'eq_id': eq_id, 'eq_name': eq_name,
               'eq_type': eq_type, 'count': len(reasons),
               'reasons': [{'name': r['name'], 'source': r['source'],
                            'id': r.get('id', 0)} for r in reasons],
               'message': f'设备类型判定={eq_type}，候选共{len(reasons)}条（历史>通用>系统字典）',
               'elapsed_ms': round((time.time() - t_start) * 1000)}
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return

    if args.action == 'list':
        repairs = get_eq_main_list(base, apis, eq_id)
        # 标注每张单可执行的动作
        for r in repairs:
            st = r.get('EQ_MAINTENANCE_STATUS')
            if st == ST_WAIT:
                r['ALLOW'] = 'start'
            elif st == ST_ING:
                r['ALLOW'] = 'end'
            else:
                r['ALLOW'] = ''
        out = {'ok': True, 'action': 'list', 'eq_id': eq_id, 'eq_name': eq_name,
               'count': len(repairs), 'repairs': repairs,
               'elapsed_ms': round((time.time() - t_start) * 1000)}
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return

    if args.action == 'create':
        # 原因解析：--reason-id 优先（AI 从 candidates 序号取到 DCCDID 直接传），否则按名称解析
        reason_list = get_fault_reasons(base, apis, use_cache)
        if args.reason_id:
            reason_id = int(args.reason_id)
            reason_name = resolve_reason_name(reason_list, reason_id)
        else:
            reason_id = resolve_reason_id(reason_list, args.reason)
            reason_name = resolve_reason_name(reason_list, reason_id) if reason_id else ''
        body = {'eqId': eq_id, 'reasonId': reason_id}
        if args.dry_run:
            out = {'ok': True, 'dry_run': True, 'action': 'create',
                   'eq_id': eq_id, 'eq_name': eq_name,
                   'reason_id': reason_id, 'reason_name': reason_name,
                   'will_send': body,
                   'message': '预览模式：将调用 AIEqError 生成维修单（状态=待维修3）。确认请去掉 --dry-run。',
                   'elapsed_ms': round((time.time() - t_start) * 1000)}
            print(json.dumps(out, ensure_ascii=False, indent=2))
            return
        # ⚠️ AIEqError 实测返回 {"code":1,"message":"状态错误，请重试","result":null} 但实际建单成功！
        #   因此不能按 code=1 判失败，需调用后回查 AIgetEqMainList 确认单据是否生成。
        code, resp = post(base, apis.get('eqError', '/open-api/bp/AIEqError'), body)
        # 回查确认：该设备是否出现新的待维修单
        new_repair = None
        try:
            repairs_now = get_eq_main_list(base, apis, eq_id)
            for r in repairs_now:
                if r.get('EQ_MAINTENANCE_STATUS') == ST_WAIT:
                    new_repair = r
                    break
        except Exception:
            pass
        if new_repair is not None:
            out = {'ok': True, 'action': 'create', 'eq_id': eq_id, 'eq_name': eq_name,
                   'reason_id': reason_id, 'reason_name': reason_name,
                   'repair_id': new_repair.get('EQ_MAINTENANCE_ID'),
                   'maintenance_status': new_repair.get('EQ_MAINTENANCE_STATUS'),
                   'raw_response': resp if isinstance(resp, dict) else str(resp),
                   'message': f'维修单 {new_repair.get("EQ_MAINTENANCE_ID")} 已生成（状态=待维修3）',
                   'elapsed_ms': round((time.time() - t_start) * 1000)}
            print(json.dumps(out, ensure_ascii=False, indent=2))
        else:
            msg = resp.get('message', str(resp)) if isinstance(resp, dict) else str(resp)
            print(json.dumps({'ok': False, 'action': 'create',
                              'error': msg, 'raw_response': resp if isinstance(resp, dict) else str(resp)},
                             ensure_ascii=False))
            sys.exit(3)
        return

    # ── start / end：先查维修单 → 状态机校验 → 执行 ──
    repairs = get_eq_main_list(base, apis, eq_id)
    target = ST_WAIT if args.action == 'start' else ST_ING
    repair = None
    if args.repair:
        for r in repairs:
            if r.get('EQ_MAINTENANCE_ID') == args.repair:
                repair = r
                break
        if repair is None:
            # ⚠️ AIgetEqMainList 实测只返回状态3(待维修)的单；
            #    结束维修(状态5)时查询接口拿不到单据，需直接凭单据号执行。
            if args.action == 'end':
                repair = {'EQ_MAINTENANCE_ID': args.repair,
                          'EQ_MAINTENANCE_STATUS': ST_ING,
                          'EQ_ID': eq_id}
                print(json.dumps({'ok': True, 'notice': 'repair_by_manual_id',
                                  'message': f'结束维修使用手动单据号 {args.repair}（AIgetEqMainList 仅返回待维修单，维修中单据需凭单据号操作）'},
                                 ensure_ascii=False, indent=2))
            else:
                print(json.dumps({'ok': False, 'reason': 'no_repair',
                                  'message': f'设备 {eq_id} 下未找到待维修单 {args.repair}'},
                                 ensure_ascii=False))
                sys.exit(2)
    else:
        repair = pick_repair(repairs, args.action)
        if repair is None:
            hint = '可结束' if args.action == 'end' else '可开始'
            extra = '；结束维修需提供维修单号（如 --repair WX-xxxx），AIgetEqMainList 仅返回待维修单' if args.action == 'end' else ''
            print(json.dumps({'ok': False, 'reason': 'no_actionable',
                              'message': f'设备 {eq_id} 没有{hint}的维修单'
                                          f'（要求状态={"待维修3" if args.action=="start" else "维修中5"}）{extra}'},
                             ensure_ascii=False))
            sys.exit(2)

    eq_main_id = repair.get('EQ_MAINTENANCE_ID')
    cur_st = repair.get('EQ_MAINTENANCE_STATUS')
    # 状态机校验：start 只对 3，end 只对 5
    if cur_st != target:
        print(json.dumps({'ok': False, 'reason': 'status_mismatch',
                          'message': f'维修单 {eq_main_id} 当前状态={cur_st}，'
                                     f'{"开始" if args.action=="start" else "结束"}操作只允许状态={"3(待维修)" if args.action=="start" else "5(维修中)"}'},
                         ensure_ascii=False))
        sys.exit(2)

    main_record = parse_items(args.items)
    main_operate = 1 if args.action == 'start' else 2

    if args.dry_run:
        out = {'ok': True, 'dry_run': True, 'action': args.action,
               'eq_id': eq_id, 'eq_name': eq_name,
               'repair_id': eq_main_id, 'status': cur_st,
               'main_operate': main_operate,
               'main_record': main_record,
               'will_send': {'mainOperate': main_operate, 'eqMainId': eq_main_id,
                             'mainRecord': main_record, 'picture': args.picture},
               'message': '预览模式：未调用执行接口。确认请去掉 --dry-run。',
               'elapsed_ms': round((time.time() - t_start) * 1000)}
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return

    code, resp = send_record(base, apis, main_operate, eq_main_id, main_record, args.picture)
    # ⚠️ AIsendEqMainRecord 实测返回 {"code":1,"message":"状态错误，请重试"} 但实际执行成功！
    #   不能按 code 判断，需回查单据状态确认（start→5, end→4）。
    #   ⚠️ AIgetEqMainList 不返回状态4(维修完成)的单 → end 后回查会查不到；
    #   此时尝试数据库只读兜底确认；数据库不可用时，若接口有响应（非网络错误）视为已提交成功。
    target_st = ST_ING if args.action == 'start' else ST_DONE
    confirmed = None
    try:
        repairs_now = get_eq_main_list(base, apis, eq_id)
        for r in repairs_now:
            if r.get('EQ_MAINTENANCE_ID') == eq_main_id:
                confirmed = r.get('EQ_MAINTENANCE_STATUS')
                break
    except Exception:
        pass
    # 兜底：AIgetEqMainList 查不到（end 后状态4不返回）→ 尝试数据库只读确认
    # （数据库连接从 config.json 的 database 段读取，可配置；未配置则跳过）
    if confirmed is None and cfg.get('database'):
        try:
            import pymysql
            db = cfg['database']
            conn = pymysql.connect(host=db.get('host', '127.0.0.1'), port=int(db.get('port', 3306)),
                                   user=db.get('user', ''), password=db.get('password', ''),
                                   database=db.get('dbname', ''), charset='utf8mb4',
                                   connect_timeout=5, read_timeout=5)
            cur = conn.cursor()
            cur.execute('SELECT EQ_MAINTENANCE_STATUS FROM eq_maintenance_plan_data WHERE EQ_MAINTENANCE_ID=%s',
                        (eq_main_id,))
            row = cur.fetchone()
            conn.close()
            if row:
                confirmed = row[0]
        except Exception:
            pass
    # 数据库也不可查时：接口有 HTTP 响应（非网络错误/非 4xx-5xx）即视为已提交
    # ⚠️ 实测 AIsendEqMainRecord 返回 body 为字面 "None"（json.loads 后是 None），
    #    不能用 isinstance(resp, dict) 判断，必须看 HTTP code。
    resp_ok = bool(code) and code < 400
    if confirmed == target_st or (confirmed is None and resp_ok):
        out = {'ok': True, 'action': args.action, 'eq_id': eq_id, 'eq_name': eq_name,
               'repair_id': eq_main_id, 'from_status': cur_st,
               'to_status': target_st,
               'confirmed_status': confirmed,
               'main_operate': main_operate, 'main_record': main_record,
               'raw_response': resp if isinstance(resp, dict) else str(resp),
               'message': f'单据 {eq_main_id} 状态已变更为 {"维修中5" if args.action=="start" else "维修完成4"}',
               'elapsed_ms': round((time.time() - t_start) * 1000)}
        print(json.dumps(out, ensure_ascii=False, indent=2))
    else:
        msg = resp.get('message', str(resp)) if isinstance(resp, dict) else str(resp)
        print(json.dumps({'ok': False, 'action': args.action, 'error': msg,
                          'confirmed_status': confirmed,
                          'raw_response': resp if isinstance(resp, dict) else str(resp)},
                         ensure_ascii=False))
        sys.exit(3)


if __name__ == '__main__':
    main()
