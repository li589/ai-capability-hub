# -*- coding: utf-8 -*-
import json
from pathlib import Path

BASE = Path(r"E:\AI文件\智能交付")


def f(name, t, required=False, desc=""):
    tr = "float" if t == "float" else ("int" if t == "int" else "strip")
    return {"api_field": name, "label": name, "type": t, "required": required,
            "desc": desc, "transform": tr}


spec = {
    "api_name": "emcheck_data", "doc_api": "erp_emcheck", "endpoint": "/open-api/bp/erp_emcheck",
    "method": "POST", "batch_mode": "array", "batch_size": 500,
    "payload": {"OperationType": 0, "content": "rows"},
    "success_rule": {"ok_key": "res", "ok_value": True, "fail_key": "code", "fail_value": 1},
    "nested": {
        "head": [
            f("EQ_CHECK_ID", "string", True, "点检方案编号(必填)"),
            f("CHECKLIST_TYPE", "int", False, "点检清单类型"),
            f("CHECK_FREQUENCY", "int", False, "点检频率"),
            f("CHECK_DESCRIPTION", "string", False, "点检描述"),
        ],
        "body": [
            f("EQ_CHECK_ID", "string", True, "点检方案编号(与head一致)"),
            f("EQ_CHECK_NAME", "string", False, "点检项名称"),
            f("CHECK_TYPE", "int", False, "检查类型"),
            f("STANDARD_VALUE", "string", False, "标准值"),
            f("MIN_VALUE", "float", False, "最小值"),
            f("MAX_VALUE", "float", False, "最大值"),
        ],
    },
    "_note": "设备/模具点检方案。单头+单身。2026-08-06 按客户模板填写；BP公式ecb.EQ_CHECK_ID编译失败待客户修复",
}
(BASE / "api_specs" / "emcheck_data.json").write_text(json.dumps(spec, ensure_ascii=False, indent=2), encoding="utf-8")

cfg = json.load(open(BASE / "config.json", encoding="utf-8"))
cfg["apis"]["emcheck_data"] = "/open-api/bp/erp_emcheck"
(BASE / "config.json").write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
print("emcheck_data spec + config 已建")
print("head:", [x["api_field"] for x in spec["nested"]["head"]])
print("body:", [x["api_field"] for x in spec["nested"]["body"]])
