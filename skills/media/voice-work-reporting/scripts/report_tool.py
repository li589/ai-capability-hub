#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MES 语音报工 CLI 工具
====================
参数化调用，避免每次重写脚本。

用法:
  python report_tool.py --action report --product YZTEST --process 组装 --qty 15 --operator {工号}
  python report_tool.py --action start  --product YZTEST --process 组装 --qty 1  --operator {工号}

参数:
  --action     report(报工/完工) | start(开工/开始加工)
  --product    产品关键词，匹配 MA_ID 或 MATERIAL_NAME（品号→MA_ID，品名→MATERIAL_NAME）
  --process    工序关键词，匹配 OP_NAME 或 OP_ID（工艺编号→OP_ID，工艺名称→OP_NAME）
  --qty        报工数量（小数）
  --scrap      报废数量（小数，仅报工有效；>0 时填入 exceptionReason:
               exceptionType=2, exceptionQty=报废数, reasonId=解析后ID, sn="")
  --reason     报废原因名称（可选，仅报工有效）：调 AIGetCollData 获取原因列表，
               按名称匹配出 reasonId；不填或匹配不到 → 取默认第一条
  --operator   工号（填入 workHours.userId）
  --config     config.json 路径（默认同目录）
  --no-cache   不使用 MOLIST/原因列表缓存，强制查询
"""
import json, urllib.request, urllib.error, os, sys, time, argparse
from concurrent.futures import ThreadPoolExecutor

DEFAULT_CONFIG = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json')
CACHE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.molist_cache.json')
REASON_CACHE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.reason_cache.json')
TOKEN_CACHE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.sso_token_cache.json')
CACHE_TTL = 30  # 秒
TOKEN_TTL = 3500  # accessToken 有效期（秒），1 小时，提前 100s 刷新

# 不良原因集合类型（COLLECTION_TYPE）：2=报废原因（报工用）；8=故障原因（报修用）
COLLECTION_TYPE_SCRAP = 2

STATUS_START = 1   # 待加工 → 开工
STATUS_END   = 2   # 加工中 → 报工

_CFG = None  # 当前生效配置（load_config 时更新）


def load_config(path):
    global _CFG
    with open(path, 'r', encoding='utf-8') as f:
        cfg = json.load(f)
    _CFG = cfg
    host = cfg['server']['host']
    port = cfg['server']['port']
    base = f"http://{host}:{port}"
    apis = cfg.get('apis', {})
    return base, apis


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
    """从 SSO token 响应提取 accessToken（兼容 result 为字符串/JSON字符串/对象）"""
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
    cfg = _CFG if _CFG is not None else load_config(DEFAULT_CONFIG)
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


def get_molist(base, apis, use_cache=True):
    """获取 MOLIST，带文件缓存。"""
    path = apis.get('queryMoList', '/open-api/bp/AIGetMoList')
    if use_cache and os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                cache = json.load(f)
            age = time.time() - cache.get('ts', 0)
            if age < CACHE_TTL:
                return cache['molist']
        except Exception:
            pass
    _, r = post(base, path, {'eqName': '', 'eqId': ''})
    molist = _result(r).get('MOLIST', [])
    try:
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump({'ts': time.time(), 'molist': molist}, f, ensure_ascii=False)
    except Exception:
        pass
    return molist


def invalidate_cache():
    if os.path.exists(CACHE_FILE):
        try:
            os.remove(CACHE_FILE)
        except Exception:
            pass


def get_reason_list(base, apis, use_cache=True):
    """获取报废原因列表（AIGetCollData，COLLECTION_TYPE=2），带文件缓存。返回 LIST 数组。"""
    path = apis.get('queryReasonList', '/open-api/bp/AIGetCollData')
    if use_cache and os.path.exists(REASON_CACHE_FILE):
        try:
            with open(REASON_CACHE_FILE, 'r', encoding='utf-8') as f:
                cache = json.load(f)
            age = time.time() - cache.get('ts', 0)
            if age < CACHE_TTL:
                return cache['list']
        except Exception:
            pass
    # 新接口 AIGetCollData 的 COLLECTION_TYPE 为必填：2=报废原因（报工），8=故障原因（报修）
    _, r = post(base, path, {'COLLECTION_TYPE': COLLECTION_TYPE_SCRAP})
    lst = _result(r).get('LIST', []) if isinstance(r, dict) else []
    try:
        with open(REASON_CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump({'ts': time.time(), 'list': lst}, f, ensure_ascii=False)
    except Exception:
        pass
    return lst


def resolve_reason_id(reason_list, reason_name=None):
    """
    根据原因名称解析 reasonId（DCCDID）。
    匹配优先级：
      1. COLLECTION_CHOICE_NAME 精确匹配（如 "报废1-1"）
      2. COLLECTION_NAME（原因组名）精确匹配（如 "报废"、"内废"）
      3. COLLECTION_CHOICE_NAME 包含匹配（互相包含）
      4. COLLECTION_NAME 包含匹配 → 取该组第一条
    无名称 / 未匹配 / 列表空 → 默认第一条（DCCDID）
    """
    if not reason_list:
        return 0
    default_id = int(reason_list[0].get('DCCDID', 0))
    if not reason_name:
        return default_id

    name = str(reason_name).strip()
    if not name:
        return default_id

    # 1. CHOICE_NAME 精确
    for it in reason_list:
        if str(it.get('COLLECTION_CHOICE_NAME', '')).strip() == name:
            return int(it['DCCDID'])
    # 2. COLLECTION_NAME（组名）精确 → 该组第一条
    for it in reason_list:
        if str(it.get('COLLECTION_NAME', '')).strip() == name:
            return int(it['DCCDID'])
    # 3. CHOICE_NAME 包含（互相）
    for it in reason_list:
        choice = str(it.get('COLLECTION_CHOICE_NAME', ''))
        if choice and (name in choice or choice in name):
            return int(it['DCCDID'])
    # 4. COLLECTION_NAME 包含 → 该组第一条
    for it in reason_list:
        coll = str(it.get('COLLECTION_NAME', ''))
        if coll and (name in coll or coll in name):
            return int(it['DCCDID'])
    # 5. 未匹配 → 默认第一条
    return default_id


def match(molist, product, process, action):
    """按产品和工序匹配，按 action 过滤状态。返回按 OP_SEQ 升序的候选列表。"""
    status_filter = STATUS_END if action == 'report' else STATUS_START
    cands = []
    for m in molist:
        ma_id = (m.get('MA_ID') or '').upper()
        mat_name = (m.get('MATERIAL_NAME') or '').upper()
        op_name = (m.get('OP_NAME') or '').upper()
        op_id = (m.get('OP_ID') or '').upper()
        p_match = (product.upper() in ma_id) or (product.upper() in mat_name)
        x_match = ('组装' if '组装' in process else process) in op_name or process.upper() in op_id
        # 工序匹配：包含即可（兼容"组装"匹配"组装"，也可匹配"组装2"由调用方过滤）
        x_match = (process in (m.get('OP_NAME') or '')) or (process.upper() in op_id)
        if p_match and x_match and m['LOT_STATUS'] == status_filter:
            cands.append(m)
    # 若调用方希望严格匹配工序名（如"组装"不含"组装2"），在 CLI 层用 --exact 控制
    cands.sort(key=lambda x: x.get('OP_SEQ', 999))
    return cands


def build_plan(molist, cands, qty_needed):
    """按 OP_SEQ 升序拆分数量。"""
    remaining = qty_needed
    plan = []
    for c in cands:
        if remaining <= 0:
            break
        take = min(remaining, float(c['QTY']))
        mo_id = c['MO_ID']
        cur_seq = c['OP_SEQ']
        same_mo = sorted([m for m in molist if m['MO_ID'] == mo_id and m['OP_SEQ'] > cur_seq],
                         key=lambda x: x['OP_SEQ'])
        plan.append({
            'mo_id': c['MO_ID'], 'op_seq': c['OP_SEQ'], 'op_id': c['OP_ID'],
            'op_name': c['OP_NAME'], 'take': take, 'ws_id': c['WS_ID'], 'ws_name': c['WS_NAME'],
            'eq_id': c.get('EQ_ID', ''), 'eps_id': int(c['EPSID']), 'wo_id': c.get('WO_ID', ''),
            'next_op_seq': str(same_mo[0]['OP_SEQ']) if same_mo else '',
            'next_op_id': str(same_mo[0]['OP_ID']) if same_mo else '',
            'next_ws_id': str(same_mo[0]['WS_ID']) if same_mo else '',
        })
        remaining -= take
    return plan, qty_needed - remaining


def _build_body(p, path, operator, scrap=0.0, reason_id=0):
    # AIStartPro（开工）只传开工接口需要的字段，
    # 避免把 workHours.reportQty / nextOpSeq 等报工字段传给开工接口导致重复扣减
    if 'StartPro' in path:
        return {
            'moId': p['mo_id'], 'opSeq': str(p['op_seq']), 'opId': str(p['op_id']),
            'qty': p['take'],
            'wsId': str(p['ws_id']), 'eqId': str(p['eq_id']),
            'epsId': p['eps_id'],
        }

    # AIEndPro（报工）完整请求体
    exception_reason = []
    if scrap and scrap > 0:
        exception_reason = [{'exceptionType': '2', 'exceptionQty': scrap,
                             'reasonId': reason_id, 'sn': ''}]
    return {
        'moId': p['mo_id'], 'opSeq': str(p['op_seq']), 'opId': str(p['op_id']),
        'qty': p['take'],
        'exceptionReason': exception_reason, 'dataCollection': [], 'useList': [],
        'workHours': [{'userId': str(p['wo_id'] or operator),
                       'reportQty': p['take'], 'humanTime': 0, 'machineTime': 0}],
        'humanTime': 0, 'machineTime': 0, 'eqId': str(p['eq_id']),
        'nextOpSeq': p['next_op_seq'], 'nextOpId': p['next_op_id'], 'nextWsId': p['next_ws_id'],
        'wsId': str(p['ws_id']), 'epsId': p['eps_id'],
    }


def execute(base, apis, plan, action, operator, scrap=0.0, reason_id=0):
    path = apis.get('endProduction' if action == 'report' else 'startProduction',
                    '/open-api/bp/AI_end_processing' if action == 'report' else '/open-api/bp/AI_start_processing')
    all_ok = True
    results = [None] * len(plan)

    # 串行场景（单笔）直接同步调用，避免线程池无意义开销
    if len(plan) == 1:
        p = plan[0]
        code, resp = post(base, path, _build_body(p, path, operator, scrap, reason_id))
        if isinstance(resp, dict) and 'res' in resp:
            results[0] = {'ok': True, 'mo_id': p['mo_id'], 'take': p['take'],
                          'amrpId': resp['res'].get('amrpId')}
        else:
            msg = resp.get('message', str(resp)) if isinstance(resp, dict) else str(resp)
            results[0] = {'ok': False, 'mo_id': p['mo_id'], 'take': p['take'], 'error': msg}
            all_ok = False
        return all_ok, results

    # 多笔：线程池并发调用，按原始顺序回填结果
    def _call(idx_p):
        idx, p = idx_p
        code, resp = post(base, path, _build_body(p, path, operator, scrap, reason_id))
        if isinstance(resp, dict) and 'res' in resp:
            return idx, {'ok': True, 'mo_id': p['mo_id'], 'take': p['take'],
                         'amrpId': resp['res'].get('amrpId')}
        else:
            msg = resp.get('message', str(resp)) if isinstance(resp, dict) else str(resp)
            return idx, {'ok': False, 'mo_id': p['mo_id'], 'take': p['take'], 'error': msg}

    with ThreadPoolExecutor(max_workers=min(len(plan), 8)) as ex:
        for idx, res in ex.map(_call, list(enumerate(plan))):
            results[idx] = res
            if not res['ok']:
                all_ok = False
    return all_ok, results


def main():
    t_start = time.time()
    ap = argparse.ArgumentParser()
    ap.add_argument('--action', required=True, choices=['report', 'start'])
    ap.add_argument('--product', required=True)
    ap.add_argument('--process', required=True)
    ap.add_argument('--qty', type=float, required=True)
    ap.add_argument('--scrap', type=float, default=0.0,
                    help='报废数量（仅报工有效，>0 时填入 exceptionReason）')
    ap.add_argument('--reason', default=None,
                    help='报废原因名称（仅报工有效，调 AIGetCollData 按名称解析 ID，默认第一条）')
    ap.add_argument('--operator', required=True)
    ap.add_argument('--config', default=DEFAULT_CONFIG)
    ap.add_argument('--no-cache', action='store_true')
    ap.add_argument('--exact-process', action='store_true',
                    help='严格匹配工序名（如"组装"不匹配"组装2"）')
    ap.add_argument('--dry-run', action='store_true',
                    help='只查询+匹配+输出执行计划，不调用执行接口（用于确认前预览，防止重复执行）')
    args = ap.parse_args()

    base, apis = load_config(args.config)
    molist = get_molist(base, apis, use_cache=not args.no_cache)

    cands = match(molist, args.product, args.process, args.action)
    if args.exact_process:
        cands = [c for c in cands if (c.get('OP_NAME') or '').strip() == args.process]

    if not cands:
        out = {'ok': False, 'reason': 'no_match',
               'message': f'未找到匹配记录：产品={args.product} 工序={args.process} 状态={"加工中" if args.action=="report" else "待加工"}'}
        print(json.dumps(out, ensure_ascii=False))
        sys.exit(2)

    plan, avail = build_plan(molist, cands, args.qty)
    unreported = round(args.qty - avail, 2)

    # 报工 + 报废 > 0 时，解析报废原因 ID（名称 → DCCDID，默认第一条）
    reason_id = 0
    reason_name_resolved = ''
    if args.action == 'report' and args.scrap and args.scrap > 0:
        reason_list = get_reason_list(base, apis, use_cache=not args.no_cache)
        reason_id = resolve_reason_id(reason_list, args.reason)
        # 回填解析结果（用于展示）：找到名称对应的 COLLECTION_CHOICE_NAME 或组名
        for it in reason_list:
            if int(it.get('DCCDID', 0)) == reason_id:
                reason_name_resolved = it.get('COLLECTION_CHOICE_NAME') or it.get('COLLECTION_NAME') or ''
                break

    # --dry-run：只预览计划，绝不调用执行接口
    if args.dry_run:
        out = {
            'ok': True,
            'dry_run': True,
            'action': args.action,
            'operator': args.operator,
            'product': args.product,
            'process': args.process,
            'reported': avail,
            'scrap': args.scrap if args.action == 'report' and args.scrap > 0 else 0.0,
            'unreported': unreported,
            'total_requested': args.qty,
            'batches': len(plan),
            'message': f'预览模式，未执行任何接口。确认执行请去掉 --dry-run 重新运行。',
            'details': [{
                'mo_id': p['mo_id'], 'op_seq': p['op_seq'], 'op_id': p['op_id'],
                'op_name': p['op_name'], 'take': p['take'], 'ws_id': p['ws_id'],
                'ws_name': p['ws_name'], 'next_op_seq': p['next_op_seq'],
            } for p in plan],
            'elapsed_ms': round((time.time() - t_start) * 1000),
        }
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return

    all_ok, results = execute(base, apis, plan, args.action, args.operator, args.scrap, reason_id)
    invalidate_cache()  # 报工/开工后状态变化，刷新缓存

    out = {
        'ok': all_ok,
        'action': args.action,
        'operator': args.operator,
        'product': args.product,
        'process': args.process,
        'reported': avail,
        'scrap': args.scrap if args.action == 'report' and args.scrap > 0 else 0.0,
        'reason_id': reason_id if args.action == 'report' and args.scrap > 0 else 0,
        'reason_name': reason_name_resolved,
        'unreported': unreported,
        'total_requested': args.qty,
        'batches': len(plan),
        'elapsed_ms': round((time.time() - t_start) * 1000),
        'details': results,
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
