# -*- coding: utf-8 -*-
import json
from pathlib import Path

BASE = Path(r"E:\AI文件\智能交付")
SPEC = BASE / "api_specs"
CN = {
    "workstation_data": "车间数据", "eq_data": "设备数据", "factory_data": "工厂数据",
    "material_data": "物料数据", "me_op_data": "工艺数据", "mo_data": "工单数据",
    "process_route_data": "工艺路线数据", "order_data": "订单数据",
    "process_route_detail_data": "领料数据", "warehouse_data": "仓库数据",
    "pqc_data": "PQC检验数据", "mold_data": "模具数据", "emcheck_data": "设备模具点检方案",
}
ORDER = ["factory_data", "workstation_data", "me_op_data", "eq_data", "material_data",
         "mo_data", "process_route_data", "order_data", "process_route_detail_data", "warehouse_data",
         "pqc_data", "mold_data", "emcheck_data"]


def field_row(f):
    parts = []
    if f.get("required"):
        parts.append("✅必填")
    if f.get("auto_generate"):
        parts.append("(系统自增不传)")
    if "default" in f:
        parts.append(f"留空默认{json.dumps(f['default'])}")
    if f.get("desc"):
        parts.append(f.get("desc"))
    return f"| {f['api_field']} | {f.get('type','string')} | {' '.join(parts) if parts else '-'} |"


lines = []
lines.append("# MES 数据导入接口传参清单（10 个）")
lines.append("")
lines.append("> 生成时间：2026-08-06 ｜ 依据：openapi-web 接口文档 + 实测确认 ｜ 供客户核对")
lines.append("")
lines.append("## 公共约定")
lines.append("")
lines.append("- 请求方式：`POST http://{服务器IP}:{端口}/open-api/bp/{接口名}`（服务器 IP/端口由使用方配置，不预制），Content-Type: application/json，**需要 Bearer Token 鉴权（账密登录 /account/v1/login 或 SSO 两段式换取）**")
lines.append("- 请求体公共结构：`{\"OperationType\": 0, \"content\": [...]}`，OperationType：**0=新增 / 1=更新**")
lines.append("- 响应：成功 `{\"res\": true}`；失败 `{\"code\": 1, \"message\": \"原因\"}`")
lines.append("- 空值规则：可选字段 Excel 留空 → **不传该字段**；标了\"留空默认\"的数字字段 → 留空传默认值")
lines.append("- ID 规则：无前缀 ID（如 mo_data 的 `ID`）= 系统自增，**不传**；带前缀 ID 均需传值")
lines.append("")

for i, name in enumerate(ORDER, 1):
    s = json.load(open(SPEC / f"{name}.json", encoding="utf-8"))
    lines.append(f"## {i}. {name}（{CN[name]}）")
    lines.append("")
    lines.append(f"- endpoint：`{s['endpoint']}` ｜ 文档接口：{s.get('doc_api','-')} ｜ 批量：每批 {s.get('batch_size',500)} 条")
    lines.append("- 请求体：`{\"OperationType\": 0, \"content\": [{...}]}`")
    lines.append("")
    if "nested" in s:
        lines.append("### content[] 元素（单头+单身）")
        lines.append("")
        lines.append("**head（单头）**")
        lines.append("")
        lines.append("| 字段 | 类型 | 必填/说明 |")
        lines.append("|---|---|---|")
        for f in s["nested"]["head"]:
            lines.append(field_row(f))
        lines.append("")
        lines.append("**body[]（单身明细）**")
        lines.append("")
        lines.append("| 字段 | 类型 | 必填/说明 |")
        lines.append("|---|---|---|")
        for f in s["nested"]["body"]:
            lines.append(field_row(f))
    else:
        lines.append("**content[] 元素（平铺）**")
        lines.append("")
        lines.append("| 字段 | 类型 | 必填/说明 |")
        lines.append("|---|---|---|")
        for f in s["fields"]:
            lines.append(field_row(f))
    lines.append("")
    lines.append("---")
    lines.append("")

(BASE / "接口传参清单.md").write_text("\n".join(lines), encoding="utf-8")
print("已生成 接口传参清单.md，共", sum(1 for x in lines if x.startswith("## ")), "个接口")
