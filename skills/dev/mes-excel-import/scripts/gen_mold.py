# -*- coding: utf-8 -*-
import json
from pathlib import Path

BASE = Path(r"E:\AI文件\智能交付")


def f(name, t, required=False, auto=False, desc=""):
    tr = "datetime" if t == "date" else ("float" if t == "float" else ("int" if t == "int" else "strip"))
    return {"api_field": name, "label": name, "type": t, "required": required,
            "auto_generate": auto, "desc": desc, "transform": tr}


spec = {
    "api_name": "mold_data", "doc_api": "erp_mold", "endpoint": "/open-api/bp/erp_mold",
    "method": "POST", "batch_mode": "array", "batch_size": 500,
    "payload": {"OperationType": 0, "content": "rows"},
    "success_rule": {"ok_key": "res", "ok_value": True, "fail_key": "code", "fail_value": 1},
    "fields": [
        f("ID", "int", False, True, "系统自增ID，不传"),
        f("MUST_APPLE", "int", False, False, "是否必须报工？(拼写按模板)"),
        f("IS_SCRAP", "int", False, False, "是否报废: 0=否 1=是"),
        f("MOLD_ID", "string", True, False, "模具编号(必填)"),
        f("MOLD_NAME", "string", False, False, "模具名称"),
        f("MOLD_DESCRIPTION", "string", False, False, "模具描述"),
        f("MOLD_LIFE", "int", False, False, "模具寿命"),
        f("CAN_PROCESS_AFTER_LIFE", "int", False, False, "寿命后可加工: 0/1"),
        f("FAILURE_DATE", "date", False, False, "报废日期"),
        f("FAILURE_REASON", "string", False, False, "报废原因"),
        f("WS_ID", "string", False, False, "车间/工位"),
        f("OPER_ID", "string", False, False, "操作人/工艺ID"),
        f("REMIND_AFTER_LIFE_LIMIT", "int", False, False, "寿命到期提醒阈值"),
        f("MOLDCAVE_QTY", "string", False, False, "模穴数量"),
        f("MOLD_LIFE_LIMIT", "string", False, False, "寿命上限"),
        f("REMARK", "string", False, False, "备注"),
        f("CREATOR", "int", False, True, "创建人(系统自动)"),
        f("CREATOR_NAME", "string", False, True, "创建人姓名(系统自动)"),
        f("CREATE_TIME", "date", False, True, "创建时间(系统自动)"),
        f("EDITOR", "int", False, True, "编辑人(系统自动)"),
        f("EDITOR_NAME", "string", False, True, "编辑人姓名(系统自动)"),
        f("EDIT_TIME", "date", False, True, "编辑时间(系统自动)"),
    ],
    "_note": "模具数据。平铺结构。2026-08-06 按客户模板填写；ID+审计字段系统自动不传",
}
(BASE / "api_specs" / "mold_data.json").write_text(json.dumps(spec, ensure_ascii=False, indent=2), encoding="utf-8")

cfg = json.load(open(BASE / "config.json", encoding="utf-8"))
cfg["apis"]["mold_data"] = "/open-api/bp/erp_mold"
(BASE / "config.json").write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
print("mold_data spec + config 已建，字段数:", len(spec["fields"]))
