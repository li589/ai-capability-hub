#!/usr/bin/env python3
"""Classify energy daily-report and directly related business scenarios."""

from __future__ import annotations

import argparse
import json
import re

SCENARIOS = {
    "energy_daily": ["能源日报", "能耗日报", "能源台账", "能耗台账", "抄表", "表计", "用电", "用水", "天然气", "蒸汽", "压缩空气", "单耗"],
    "energy_target": ["能源目标", "能耗目标", "能源预算", "目标单耗", "节能目标"],
    "energy_cost": ["能源成本", "能源价格", "电价", "水价", "气价", "成本分析"],
    "energy_anomaly": ["能耗异常", "能源异常", "超耗", "异常整改", "节能整改", "预警阈值"],
    "production": ["生产日报", "生产班报", "工单", "产量", "计划达成"],
    "quality": ["质量", "不良", "检验", "整改", "客诉", "放行"],
    "equipment": ["设备", "点检", "保养", "维修", "故障", "停机"],
    "inventory_procurement": ["库存", "仓库", "采购", "物料", "缺料", "到货", "在途"],
    "attendance_handover": ["考勤", "交接班", "班组", "排班", "培训"],
    "safety": ["安全", "巡检", "隐患", "风险", "整改闭环"],
    "meeting_tasks": ["会议", "任务", "待办", "责任人", "催办"],
    "custom_ledger": ["台账", "登记", "档案", "记录表", "查询统计"],
}

HIGH_RISK = {
    "自动付款": "财务付款必须保留人工审批和外部系统授权",
    "自动下单": "采购下单必须保留人工审批和外部系统授权",
    "自动放行": "质量放行不能仅由生成系统自动决定",
    "自动处分": "人事处分不能由生成系统自动决定",
    "关闭安全联锁": "安全联锁只能上报，不允许由生成系统关闭",
    "绕过审批": "不能绕过权限或审批控制",
}

REQUIRES_CONFIRMATION = {
    "金额": "确认币种、精度、税口径和审批权限",
    "薪资": "确认敏感数据范围、脱敏和最小权限",
    "身份证": "确认合法用途、脱敏、保留期限和访问审计",
    "多公司": "确认组织隔离、跨公司查询和管理员范围",
    "跨部门审批": "确认审批顺序、会签/或签和退回规则",
    "电子签名": "确认签名法律效力、身份认证和证据保留要求",
    "外部接口": "提供真实接口合同、凭据方式、超时和失败补偿",
    "实时采集": "提供真实设备或 API 连接与联调证据",
}

DISPLAY_NAMES = {
    "energy_daily": "能源日报与表计抄表",
    "energy_target": "能源目标与预算",
    "energy_cost": "能源成本分析",
    "energy_anomaly": "能耗异常与整改",
    "production": "生产日报与班报",
    "quality": "质量问题与整改",
    "equipment": "设备点检维修",
    "inventory_procurement": "库存采购预警",
    "attendance_handover": "考勤与交接班",
    "safety": "安全巡检整改",
    "meeting_tasks": "会议任务闭环",
    "custom_ledger": "自定义台账",
}


def classify(text: str) -> dict:
    normalized = re.sub(r"\s+", "", str(text or "")).casefold()
    matched = []
    evidence = {}
    for scenario, keywords in SCENARIOS.items():
        hits = [keyword for keyword in keywords if keyword.casefold() in normalized]
        if hits:
            matched.append(scenario)
            evidence[scenario] = hits

    prohibited = [{"phrase": phrase, "reason": reason} for phrase, reason in HIGH_RISK.items() if phrase in normalized]
    confirmations = [{"topic": phrase, "question": question} for phrase, question in REQUIRES_CONFIRMATION.items() if phrase in normalized]

    if prohibited:
        decision = "supported_with_prohibited_automation_removed" if matched else "not_supported_as_requested"
    elif not matched:
        decision = "needs_business_description"
        confirmations.append({"topic": "业务目标", "question": "请说明要管理的记录、使用角色、状态流程、查询统计和导入来源。"})
    elif confirmations:
        decision = "supported_after_confirmation"
    elif len(matched) >= 2:
        decision = "supported_combined_scenario"
    else:
        decision = "supported_standard_scenario"

    recommended_modules = [DISPLAY_NAMES[item] for item in matched]
    return {
        "decision": decision,
        "matched_scenarios": matched,
        "scenario_evidence": evidence,
        "recommended_modules": recommended_modules,
        "confirmation_items": confirmations,
        "prohibited_automation": prohibited,
        "first_call_gate": bool(matched) and not prohibited,
        "next_action": {
            "supported_standard_scenario": "直接进入安全检查和完整生成闭环。",
            "supported_combined_scenario": "生成统一蓝图，使用共享组织、权限、审计和主数据，避免拼接多个孤立系统。",
            "supported_after_confirmation": "先确认列出的关键边界，再正式导入；其他非阻塞工作继续执行。",
            "supported_with_prohibited_automation_removed": "移除禁止自动决策，仅生成记录、预警、审批和审计能力。",
            "not_supported_as_requested": "不能按原要求自动执行高风险决定；可改为人工审批和证据留痕系统。",
            "needs_business_description": "补充最少业务描述后再判断，不根据模糊词生成空壳。",
        }[decision],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="判断能源日报及关联场景是否适用本地系统生成器")
    parser.add_argument("description", nargs="+")
    args = parser.parse_args()
    result = classify(" ".join(args.description))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["decision"] not in {"not_supported_as_requested", "needs_business_description"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
