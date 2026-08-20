#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MES 智能问数 · 对话查询工具（Skill 核心）
用法：
  python query_tool.py "M02今天的产量"
  python query_tool.py "为什么今天的产量下降了"
  python query_tool.py "M02今天的产量和昨天比"
输出：JSON { parse, results[{tag,sql,cols,rows,truncated,error}], follow_ups }
说明：AI 对话层负责四要素解析与自然语言组织，本工具负责 路由->SQL->执行->翻译->追问索引。
"""
import sys, os, json, datetime, decimal


def _default(o):
    if isinstance(o, (datetime.datetime, datetime.date)):
        return o.strftime("%Y-%m-%d %H:%M:%S")
    if isinstance(o, decimal.Decimal):
        return float(o)
    return str(o)

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, "scripts"))

from generate_sql import generate, parse_entity, parse_time, match_intent
import db_query


def build_follow_ups(out):
    """根据结果构造可追问索引 follow_ups（供 AI 解析"原因1/A设备/具体数据"类追问）"""
    fus = []
    if out.get("parse", {}).get("归因") == "是":
        # 归因四维度 -> 可追问"原因N的具体数据"
        dims = ["设备故障/点检", "设备状态切换(停机/稼动)", "工单状态堆积", "不良/报废"]
        for i, d in enumerate(dims, 1):
            fus.append({"ref": f"原因{i}", "dim": d, "hint": f"查看{d}的详细数据"})
        return fus
    # 普通查询：按结果里的实体生成下钻建议（取结果行中的产品/设备/工单列）
    for r in out.get("results", []):
        cols = r.get("cols") or []
        for i, c in enumerate(cols):
            if c in ("产品", "MA_ID", "EQ_ID", "MO_ID", "工单号"):
                for row in (r.get("rows") or [])[:3]:
                    v = row[i]
                    if v is None:
                        continue
                    if c in ("产品", "MA_ID"):
                        fus.append({"ref": f"{v}的明细", "entity": v, "type": "product",
                                    "hint": f"查看 {v} 的报工/产量明细"})
                    elif c in ("EQ_ID",):
                        fus.append({"ref": f"{v}的状态", "entity": v, "type": "equipment",
                                    "hint": f"查看设备 {v} 的状态/故障记录"})
    return fus


def run_query(question, session=None):
    """问题 -> 解析+SQL -> 执行+翻译 -> follow_ups"""
    out = generate(question)
    for r in out.get("results", []):
        sql = r.get("sql")
        if not sql:
            r["rows"], r["cols"], r["truncated"] = [], [], False
            continue
        ok, msg = db_query.validate_sql(sql)
        if not ok:
            r["error"] = f"校验拒绝: {msg}"
            r["rows"], r["cols"], r["truncated"] = [], [], False
            continue
        try:
            cols, rows, trunc = db_query.run(sql)
            r["cols"], r["rows"], r["truncated"] = cols, rows, trunc
        except Exception as e:
            r["error"] = f"执行失败: {e}"
            r["rows"], r["cols"], r["truncated"] = [], [], False
    out["follow_ups"] = build_follow_ups(out)
    out["asked_at"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return out


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    args = sys.argv[1:]
    q = args[0] if args else "M02今天的产量"
    out = run_query(q)
    # 精简输出：行转成 dict 列表
    for r in out.get("results", []):
        if r.get("cols") and r.get("rows"):
            # 翻译枚举值后转 dict
            r["data"] = [{c: db_query.translate(c, v) for c, v in zip(r["cols"], row)}
                         for row in r["rows"]]
            r.pop("cols"); r.pop("rows")
    print(json.dumps(out, ensure_ascii=False, indent=1, default=_default))


if __name__ == "__main__":
    main()
