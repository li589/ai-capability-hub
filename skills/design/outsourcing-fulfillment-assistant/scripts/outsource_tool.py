#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
委外发货回货 CLI 工具（数据源 = 用户提供的 OPENAPI 接口，不读数据库）
============================================================
链路：查询清单接口(getCanOutsourceList / getOutSourceList) → 匹配 → --dry-run 预览
      → 用户确认 → 调执行接口(SendOutsource / sendOutsourceBack) → 反馈

⚠️ 防重复执行铁律：
  - 匹配/展示阶段必须加 --dry-run：只输出匹配与执行计划，不调任何执行接口
  - 用户明确确认后去掉 --dry-run 执行一次，绝不重复调用
  - 不确定是否已执行 → 先 --dry-run 查状态，不要盲目重跑

接口（config.json apis，2026-08-17 用户提供）：
  querySendList  /open-api/bp/getCanOutsourceList      可委外清单查询
  execSend       /open-api/bp/SendOutsource            委外发货(生成委外单)
  queryBackList  /open-api/bp/getOutSourceList         待回货委外单查询
  execBack       /open-api/bp/sendOutsourceBack        委外回货(单条)
  execBackBatch  /open-api/bp/batchSendOutsourceBack   委外回货(批量)

用法:
  # 委外发货(生成委外单)：先 --dry-run 预览，确认后执行一次
  python outsource_tool.py --action send --product FCW-01 --process 钢材切割 --supplier FZHGYS --qty 10 --delivery-date 2026-08-20 --dry-run
  python outsource_tool.py --action send --product FCW-01 --process 钢材切割 --supplier FZHGYS --qty 10 --delivery-date 2026-08-20
  # 委外回货：先 --dry-run 预览，确认后执行一次
  python outsource_tool.py --action back --outsource-id OU-20260811001 --qty 10 --ok 9 --ng 1 --dry-run
  python outsource_tool.py --action back --outsource-id OU-20260811001 --qty 10 --ok 9 --ng 1

参数:
  --action        send(委外发货/生成委外单) | back(委外回货)
  --product       产品关键词(匹配 MA_ID/MATERIAL_NAME)
  --process       工艺关键词(匹配 OP_ID/OP_NAME)
  --supplier      供应商编号/名称(匹配 SUPPLIER_ID/SUPPLIER_NAME)
  --outsource-id  委外单号(回货用)
  --qty           发货/回货数量
  --ok            验收合格数量(仅回货,GOODQTY; OK+NG=BACK)
  --ng            验退数量(仅回货,NG_QTY)
  --delivery-date 要求回货日期 YYYY-MM-DD(仅发货,写入 BACKDATE/backDate)
  --dry-run       ★ 只查询+匹配+输出执行计划,不调执行接口
  --no-cache      强制重新查询清单
"""
import json, os, sys, time, argparse

import api_common as ac

CACHE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.outsource_cache.json')
CACHE_TTL = 30  # 秒

# 接口 key(对应 config.json apis)
API_QUERY_SEND = "querySendList"
API_EXEC_SEND = "execSend"
API_QUERY_BACK = "queryBackList"
API_EXEC_BACK = "execBack"
API_EXEC_BACK_BATCH = "execBackBatch"

# 查询接口请求体固定字段(两个独立数据实体,各自容器,不共用)
SEND_QUERY_BODY = {"SUPPLIER_ID": "", "OP_ID": "", "MO_ID": "", "MA_ID": ""}   # 实体A: 可委外清单
BACK_QUERY_BODY = {"SUPPLIER_ID": "", "OP_ID": "", "MO_ID": "", "MA_ID": "",   # 实体B: 待回货清单
                   "OUTSOURCE_ID": "", "OUTDATE_START": "", "OUTDATE_END": ""}


def _query(entity_fn, body, use_cache=True, cache_key=""):
    """实体查询(可委外清单 / 待回货清单分别由 entity_fn 处理,容器互不混用)。"""
    if use_cache and cache_key and os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                c = json.load(f)
            if c.get('key') == cache_key and (time.time() - c.get('ts', 0)) < CACHE_TTL:
                return c.get('list'), None
        except Exception:
            pass
    lst, err = entity_fn(body)
    if err:
        return None, err
    if cache_key:
        try:
            with open(CACHE_FILE, 'w', encoding='utf-8') as f:
                json.dump({'key': cache_key, 'ts': time.time(), 'list': lst}, f)
        except Exception:
            pass
    return lst, None


def _exec(base, apis, key, body):
    """调执行接口;返回 (ok, 响应或错误)。"""
    path = apis.get(key)
    if not path:
        return False, f"执行接口 {key} 未配置:请在 config.json apis 填入执行接口路径"
    code, resp = ac.post(base, path, body)
    if code != 200:
        exc = resp.get('exception') if isinstance(resp, dict) else {}
        return False, f"执行失败(code={code}): {exc.get('errorMessage') or resp}"
    if isinstance(resp, dict) and resp.get('code') not in (None, 0):
        return False, f"执行失败: {resp.get('message') or resp}"
    return True, resp


def _match_contains(field_val, kw):
    if field_val is None:
        return False
    fv = str(field_val)
    if not fv:  # 空值不匹配任何关键词(防止空供应商被误过滤放过)
        return False
    return str(kw) in fv or fv in str(kw)


def _match_rows(rows, field_groups, kws):
    """匹配规则:field_groups 每组对应一个关键词;组内任一字段命中即算(OR),组间全部满足(AND)。
    例:  _match_rows(lst, [['MA_ID','MATERIAL_NAME']], [product])  产品=编号或名称命中
         _match_rows(lst, [['MA_ID','MATERIAL_NAME'],['SUPPLIER_ID','SUPPLIER_NAME']], [product, supplier])
    """
    hits = []
    for row in rows:
        ok = True
        for fields, kw in zip(field_groups, kws):
            if not kw:
                continue
            if not any(_match_contains(row.get(f), kw) for f in fields):
                ok = False
                break
        if ok:
            hits.append(row)
    return hits


def _pick(row, keys):
    """取行字段,缺省补空;数字补 0。"""
    out = {}
    for k in keys:
        v = row.get(k)
        if v is None:
            v = 0 if k in ('OUTSOURCE_STATUS', 'CANOUTQTY', 'CAN_BACK_QTY', 'SEND_QTY', 'GOODQTY', 'NG_QTY', 'OUTQTY') else ""
        out[k] = v
    return out


def _is_code(s):
    """判断是否为编号(字母/数字开头);中文名/描述不传给查询接口,靠本地模糊匹配。"""
    return bool(s) and s[0].isascii() and s[0].isalnum()


def _fill_query_body(body, mapping, args):
    """填充查询接口 body:仅编号类参数传给接口(接口按编号匹配),中文名留本地匹配。"""
    for field, val in mapping:
        if val and _is_code(val):
            body[field] = val
    return body


def cmd_send(args, base, apis):
    """委外发货:getCanOutsourceList → 匹配 → 预览/执行(SendOutsource)。
    供应商策略:查询不按供应商过滤(工单可能无预设);--supplier 指定时仅用于执行(可换供应商)。"""
    body = dict(SEND_QUERY_BODY)
    # 注意:SUPPLIER_ID 不传给查询接口——无预设供应商的工单会被接口按供应商过滤排掉
    _fill_query_body(body, [('OP_ID', args.process), ('MO_ID', args.mo), ('MA_ID', args.product)], args)
    lst, err = _query(ac.fetch_can_outsource, body, use_cache=not args.no_cache, cache_key='can')
    if err:
        print(json.dumps({'ok': False, 'reason': 'query_error', 'error': err}, ensure_ascii=False))
        return
    hits = _match_rows(lst, [['MA_ID', 'MATERIAL_NAME']], [args.product])
    if args.process:
        hits = _match_rows(hits, [['OP_ID', 'OP_NAME']], [args.process])
    if not hits:
        print(json.dumps({'ok': False, 'reason': 'no_match',
                          'error': f"可委外清单中未匹配到 产品[{args.product}] 工艺[{args.process}]"},
                         ensure_ascii=False))
        return
    # 指定供应商时:名称从绩效接口补全(无预设工单也可换供应商)
    sup_id, sup_name = '', ''
    if args.supplier:
        sup_id = args.supplier
        cols_perf, rows_perf = ac.fetch_supplier_perf()
        if cols_perf:
            i_id = cols_perf.index('SUPPLIER_ID')
            i_name = cols_perf.index('SUPPLIER_NAME')
            for r in rows_perf:
                if args.supplier in str(r[i_id]) or args.supplier in str(r[i_name]):
                    sup_name = r[i_name]
                    break
    # 执行计划:按 CANOUTQTY 拆数量;不传 --qty = 全部发货(每行发满 CANOUTQTY)
    plan = []
    remain = float(args.qty) if args.qty is not None else float('inf')
    for row in hits:
        if remain <= 0:
            break
        can = float(row.get('CANOUTQTY') or row.get('OUTQTY') or 0)
        qty = min(remain, can) if remain != float('inf') else can
        if qty <= 0:
            continue
        row_sid = row.get('SUPPLIER_ID') or ''
        plan.append({
            'OUTQTY': qty, 'CANOUTQTY': can, 'BACKDATE': args.delivery_date or row.get('BACKDATE') or '',
            'SUPPLIER_ID': sup_id or row_sid,
            'SUPPLIER_NAME': sup_name or row.get('SUPPLIER_NAME') or '',
            **{k: row.get(k, "") for k in ('MO_ID', 'ORDER_ID', 'OP_ID',
                                           'OP_NAME', 'OP_DESCRIPTION', 'WS_ID', 'WS_NAME', 'OP_SEQ',
                                           'MA_ID', 'MATERIAL_NAME', 'MATERIAL_DESCRIPTION')},
        })
        remain -= qty
    if not plan:
        print(json.dumps({'ok': False, 'reason': 'no_plan', 'error': '可委外数量不足'}, ensure_ascii=False))
        return
    if args.dry_run:
        # 默认供应商/回货日期提示(匹配行自带,如选择的数据有默认值可不重选供应商)
        default_sup = plan[0].get('SUPPLIER_ID') or ''
        default_sup_name = plan[0].get('SUPPLIER_NAME') or ''
        default_backdate = plan[0].get('BACKDATE') or ''
        note = '预览完成:确认后去掉 --dry-run 执行 SendOutsource 生成委外单'
        if not args.supplier and default_sup:
            note += (' | 默认供应商 %s(%s)、默认回货日期 %s:沿用请确认;'
                     '重新选择请用 --supplier 指定(可先查供应商绩效)'
                     % (default_sup_name, default_sup, default_backdate))
        print(json.dumps({'ok': True, 'dry_run': True, 'matched': len(hits), 'plan': plan,
                          'default_supplier': default_sup, 'default_supplier_name': default_sup_name,
                          'default_backdate': default_backdate, 'note': note},
                         ensure_ascii=False, default=str))
        return
    # 执行:SendOutsource
    exec_body = {
        "outSourceList": plan,
        "supplier_id": plan[0]['SUPPLIER_ID'] if args.supplier is None else args.supplier,
        "backDate": plan[0]['BACKDATE'],
    }
    ok, resp = _exec(base, apis, API_EXEC_SEND, exec_body)
    _invalidate_cache()
    print(json.dumps({'ok': ok, 'dry_run': False, 'count': len(plan),
                      'resp': resp if ok else {'error': resp}}, ensure_ascii=False, default=str))


def _back_sort_key(r):
    """回货多条匹配时,优先委外日期早的(按 CREATE_TIME 或 OUTSOURCE_ID 含日期排序)。"""
    return str(r.get('CREATE_TIME') or r.get('OUTSOURCE_ID') or '')


def cmd_back(args, base, apis):
    """委外回货:getOutSourceList → 匹配(多条按委外日期早的优先) → 预览/执行(sendOutsourceBack)。
    验收/验退:可填值或语音输入;不填则全部验收(OK=回货量, NG=0)。"""
    body = dict(BACK_QUERY_BODY)
    _fill_query_body(body, [('SUPPLIER_ID', args.supplier), ('OP_ID', args.process),
                            ('MO_ID', args.mo), ('MA_ID', args.product),
                            ('OUTSOURCE_ID', args.outsource_id)], args)
    lst, err = _query(ac.fetch_back_list, body, use_cache=not args.no_cache, cache_key='back')
    if err:
        print(json.dumps({'ok': False, 'reason': 'query_error', 'error': err}, ensure_ascii=False))
        return
    hits = _match_rows(lst, [['OUTSOURCE_ID']], [args.outsource_id]) if args.outsource_id else lst
    if args.product:  # 产品本地过滤(中文名不传接口,本地匹配确保只取该产品单据)
        hits = _match_rows(hits, [['MA_ID', 'MATERIAL_NAME']], [args.product])
    if args.process:
        hits = _match_rows(hits, [['OP_ID', 'OP_NAME']], [args.process])
    if not hits:
        print(json.dumps({'ok': False, 'reason': 'no_match',
                          'error': f"待回货清单中未找到匹配记录 [{args.outsource_id or ''} {args.product or ''}]"}, ensure_ascii=False))
        return
    # 多条匹配:按委外日期早的优先
    hits = sorted(hits, key=_back_sort_key)
    # 不传 --qty = 全部回货(查询出的所有产品/单据全部执行,每笔发满待回货量)
    if args.qty is None:
        back_qty = sum(float(r.get('CAN_BACK_QTY') or 0) for r in hits)
    else:
        back_qty = float(args.qty)
    if back_qty <= 0:
        print(json.dumps({'ok': False, 'reason': 'no_data', 'error': '没有可回货的数据'}, ensure_ascii=False))
        return
    # 验收/验退:不填 → 全部验收;填一个 → 另一个补齐
    if args.ok is None and args.ng is None:
        total_ok, total_ng = back_qty, 0.0
    elif args.ok is None:
        total_ok, total_ng = back_qty - float(args.ng), float(args.ng)
    elif args.ng is None:
        total_ok, total_ng = float(args.ok), back_qty - float(args.ok)
    else:
        total_ok, total_ng = float(args.ok), float(args.ng)
    if total_ok + total_ng != back_qty:
        print(json.dumps({'ok': False, 'reason': 'bad_qty',
                          'error': f"合格+验退({total_ok}+{total_ng})必须等于回货数量({back_qty})"},
                         ensure_ascii=False))
        return
    # 执行计划:按排序后逐笔扣减。
    # 规则(2026-08-17 用户确认):验退尽量放第一笔(不足顺延后续笔),其余全验收;
    # 每笔验收+验退 = 该笔回货量,不超过当条剩余待回货数量。
    plans = []
    remain = back_qty
    ng_left = total_ng
    for row in hits:
        if remain <= 0:
            break
        can = float(row.get('CAN_BACK_QTY') or 0)
        if can <= 0:
            continue
        q = min(remain, can)          # 该笔回货量 ≤ 当条待回货量
        ng_i = min(ng_left, q)        # 验退靠前(通常全在第一笔),且不超本笔回货量
        ng_left -= ng_i
        ok_i = q - ng_i               # 验收 = 本笔回货 - 本笔验退(OK+NG = q ≤ CAN_BACK_QTY)
        plans.append({
            **{k: row.get(k, "") for k in ('OUTSOURCE_ID', 'SUPPLIER_ID', 'SUPPLIER_NAME', 'MO_ID', 'OP_SEQ',
                                           'OP_ID', 'OP_NAME', 'MA_ID', 'MATERIAL_NAME', 'MATERIAL_DESCRIPTION',
                                           'UNIT', 'CREATE_TIME')},
            'OUTSOURCE_STATUS': row.get('OUTSOURCE_STATUS') or 0,
            'SEND_QTY': row.get('SEND_QTY') or 0,
            'CAN_BACK_QTY': can,
            'GOODQTY': ok_i,
            'NG_QTY': ng_i,
            '_BACK_QTY': q,
        })
        remain -= q
    if not plans:
        print(json.dumps({'ok': False, 'reason': 'no_plan', 'error': '待回货数量不足'}, ensure_ascii=False))
        return
    if args.dry_run:
        print(json.dumps({'ok': True, 'dry_run': True, 'matched': len(hits), 'plans': plans,
                          'total': {'back': back_qty, 'ok': total_ok, 'ng': total_ng},
                          'api': 'batchSendOutsourceBack' if len(plans) > 1 else 'sendOutsourceBack',
                          'note': '预览完成(按委外日期早的优先,不填验收=全部验收):确认后去掉 --dry-run 执行回货'},
                         ensure_ascii=False, default=str))
        return
    # 执行:多条 → 批量 batchSendOutsourceBack(BACKLIST 数组);单条 → sendOutsourceBack(OUTSOURCE_LIST)
    def _to_out_source_list(p):
        return {k: v for k, v in p.items() if not k.startswith('_')}
    if len(plans) > 1:
        exec_body = {'BACKLIST': [_to_out_source_list(p) for p in plans]}
        ok, resp = _exec(base, apis, API_EXEC_BACK_BATCH, exec_body)
        results = [{'outsource_id': p['OUTSOURCE_ID'], 'back': p['_BACK_QTY'],
                    'ok': ok, 'resp': resp if ok else {'error': resp}} for p in plans]
    else:
        exec_body = {'OUTSOURCE_LIST': _to_out_source_list(plans[0])}
        ok, resp = _exec(base, apis, API_EXEC_BACK, exec_body)
        results = [{'outsource_id': plans[0]['OUTSOURCE_ID'], 'back': plans[0]['_BACK_QTY'],
                    'ok': ok, 'resp': resp if ok else {'error': resp}}]
    _invalidate_cache()
    all_ok = all(r['ok'] for r in results)
    print(json.dumps({'ok': all_ok, 'dry_run': False, 'count': len(results), 'results': results},
                     ensure_ascii=False, default=str))


def _invalidate_cache():
    if os.path.exists(CACHE_FILE):
        try:
            os.remove(CACHE_FILE)
        except Exception:
            pass


def main():
    ap = argparse.ArgumentParser(description="委外发货/回货 CLI(查询+匹配+预览+执行)")
    ap.add_argument("--action", choices=["send", "back"], required=True)
    ap.add_argument("--product", help="产品关键词(MA_ID/MATERIAL_NAME 匹配)")
    ap.add_argument("--process", help="工艺关键词(OP_ID/OP_NAME 匹配)")
    ap.add_argument("--supplier", help="供应商编号/名称")
    ap.add_argument("--mo", help="工单编号")
    ap.add_argument("--outsource-id", help="委外单号(回货匹配)")
    ap.add_argument("--qty", type=float, help="发货/回货数量")
    ap.add_argument("--ok", type=float, help="验收合格数量 GOODQTY(仅回货)")
    ap.add_argument("--ng", type=float, help="验退数量 NG_QTY(仅回货)")
    ap.add_argument("--delivery-date", help="要求回货日期 YYYY-MM-DD(仅发货,BACKDATE)")
    ap.add_argument("--dry-run", action="store_true", help="只查询+匹配+输出执行计划,不调执行接口")
    ap.add_argument("--no-cache", action="store_true", help="强制重新查询清单")
    args = ap.parse_args()

    base, apis = ac.load_config()
    if args.action == "send":
        cmd_send(args, base, apis)
    else:
        cmd_back(args, base, apis)


if __name__ == "__main__":
    main()
