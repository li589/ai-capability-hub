#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""用户画像与人群洞察 —— JSON 校验 + Markdown 渲染

职责：
  1. 读取 agent 生成的画像与洞察方案 JSON（文件路径或 `-` 读 stdin）；
  2. 按 references/output-schema.md 的契约逐字段校验；
  3. 校验通过则渲染 Markdown 画像与洞察方案到 --out；失败按退出码返回中文报错。

退出码：0 成功 / 1 参数错误 / 2 schema 不合规 / 3 写盘失败 / 9 JSON 解析失败
纯标准库，无第三方依赖。
"""

import argparse
import json
import re
import sys
from pathlib import Path

# ---------- 枚举（与 output-schema.md 保持一致） ----------
DIMENSION_NAMES = [
    "数据基础", "标签体系", "分群建模", "画像刻画", "应用落地", "治理迭代",
]
# 标准 CDP 六类业务域（不再自行拆分交易/偏好/价值凑数）
TAG_LAYERS = {"基础属性", "行为", "消费价值", "生命周期", "渠道来源", "预测"}
LEVELS_HML = {"高", "中", "低"}
PRIORITY_LEVELS = {"P0", "P1", "P2"}
STAGE_MAP = [
    (1.9, "起步期"), (2.9, "成长期"), (3.9, "成熟期"), (5.0, "卓越期"),
]
# 量化标记：数字 / 天 / 次 / Top / % / 率 / 待校准 / 待验证
# （含 %/率 以覆盖 insights.expected_metric 的运营指标表达，如"复购率+15%"）
QUANT_RE = re.compile(r"(\d|天|次|Top|%|率|待校准|待验证)")


class SchemaError(Exception):
    """schema 不合规；退出码 2。"""


# ---------- 工具 ----------
def _require(obj, key, ctx):
    if key not in obj:
        raise SchemaError(f"{ctx}缺少字段 `{key}`")
    return obj[key]


def _nonempty_str(v, ctx):
    if not isinstance(v, str) or v.strip() == "":
        raise SchemaError(f"{ctx}必须为非空字符串")
    return v.strip()


def _enum(v, allowed, ctx):
    if v not in allowed:
        raise SchemaError(f"{ctx}值 `{v}` 非法，合法值：{sorted(allowed)}")
    return v


def _as_number(v, ctx):
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        raise SchemaError(f"{ctx}必须为数字")
    return float(v)


def _as_int(v, ctx):
    if isinstance(v, bool) or not isinstance(v, int):
        raise SchemaError(f"{ctx}必须为整数")
    return v


def _as_list(v, ctx, min_len=1):
    if not isinstance(v, list) or len(v) < min_len:
        raise SchemaError(f"{ctx}必须为长度 ≥{min_len} 的数组")
    return v


def _score_to_stage(score):
    for threshold, stage in STAGE_MAP:
        if score <= threshold:
            return stage
    return "卓越期"


# ---------- 校验 ----------
def validate(data):
    if not isinstance(data, dict):
        raise SchemaError("顶层必须为 JSON 对象")

    # conclusion
    _nonempty_str(_require(data, "conclusion", "顶层"), "顶层.conclusion")

    # maturity
    mat = _require(data, "maturity", "顶层")
    if not isinstance(mat, dict):
        raise SchemaError("顶层.maturity 必须为对象")
    score = _as_number(_require(mat, "score", "maturity"), "maturity.score")
    if not (1.0 <= score <= 5.0):
        raise SchemaError(f"maturity.score={score} 越界（应在 1.0–5.0）")
    declared_stage = _nonempty_str(_require(mat, "stage", "maturity"), "maturity.stage")
    _nonempty_str(_require(mat, "summary", "maturity"), "maturity.summary")

    # dimensions（6 项，顺序固定）
    dims = _as_list(_require(data, "dimensions", "顶层"), "顶层.dimensions", min_len=6)
    if len(dims) != 6:
        raise SchemaError(f"dimensions 必须恰好 6 项，实有 {len(dims)}")
    dim_scores = []
    for i, d in enumerate(dims):
        ctx = f"dimensions[{i}]"
        if not isinstance(d, dict):
            raise SchemaError(f"{ctx} 必须为对象")
        name = _nonempty_str(_require(d, "name", ctx), f"{ctx}.name")
        if name != DIMENSION_NAMES[i]:
            raise SchemaError(f"{ctx}.name 应为 `{DIMENSION_NAMES[i]}`，实为 `{name}`")
        _nonempty_str(_require(d, "status", ctx), f"{ctx}.status")
        cv = _require(d, "current_value", ctx)
        if not isinstance(cv, str):
            raise SchemaError(f"{ctx}.current_value 必须为字符串")
        bm = _require(d, "benchmark", ctx)
        if not isinstance(bm, str):
            raise SchemaError(f"{ctx}.benchmark 必须为字符串")
        _nonempty_str(_require(d, "problem", ctx), f"{ctx}.problem")
        _nonempty_str(_require(d, "impact", ctx), f"{ctx}.impact")
        ds = _as_int(_require(d, "score", ctx), f"{ctx}.score")
        if not (1 <= ds <= 5):
            raise SchemaError(f"{ctx}.score={ds} 越界（应在 1–5）")
        dim_scores.append(ds)
        _enum(_require(d, "priority", ctx), PRIORITY_LEVELS, f"{ctx}.priority")

    # 交叉校验：score ≈ 平均
    avg = sum(dim_scores) / 6
    if abs(score - avg) > 0.2:
        raise SchemaError(f"maturity.score={score} 与六维平均 {avg:.1f} 偏差 >0.2")
    expected_stage = _score_to_stage(score)
    if declared_stage != expected_stage:
        raise SchemaError(
            f"maturity.stage=`{declared_stage}` 与 score={score} 对应的分段"
            f"`{expected_stage}` 不一致")

    # tag_system
    ts = _require(data, "tag_system", "顶层")
    if not isinstance(ts, dict):
        raise SchemaError("顶层.tag_system 必须为对象")
    layers = _as_list(_require(ts, "layers", "tag_system"), "tag_system.layers", min_len=4)
    layer_types = set()
    for i, ly in enumerate(layers):
        ctx = f"tag_system.layers[{i}]"
        if not isinstance(ly, dict):
            raise SchemaError(f"{ctx} 必须为对象")
        lt = _enum(_require(ly, "layer", ctx), TAG_LAYERS, f"{ctx}.layer")
        layer_types.add(lt)
        _nonempty_str(_require(ly, "purpose", ctx), f"{ctx}.purpose")
        _nonempty_str(_require(ly, "example_tags", ctx), f"{ctx}.example_tags")
        _nonempty_str(_require(ly, "data_source", ctx), f"{ctx}.data_source")
    if len(layer_types) < 4:
        raise SchemaError(
            f"tag_system.layers 只覆盖 {len(layer_types)} 类（{sorted(layer_types)}），"
            f"六类中至少覆盖 4 类")
    key_tags = _as_list(_require(ts, "key_tags", "tag_system"), "tag_system.key_tags", min_len=3)
    kt_p = {"P0": 0, "P1": 0, "P2": 0}
    for i, kt in enumerate(key_tags):
        ctx = f"tag_system.key_tags[{i}]"
        if not isinstance(kt, dict):
            raise SchemaError(f"{ctx} 必须为对象")
        _nonempty_str(_require(kt, "tag", ctx), f"{ctx}.tag")
        _nonempty_str(_require(kt, "definition", ctx), f"{ctx}.definition")
        _nonempty_str(_require(kt, "rule", ctx), f"{ctx}.rule")
        kt_p[_enum(_require(kt, "priority", ctx), PRIORITY_LEVELS, f"{ctx}.priority")] += 1
    if len(key_tags) >= 3 and kt_p["P1"] + kt_p["P2"] == 0:
        raise SchemaError("tag_system.key_tags ≥3 项全标 P0，至少把 1 项降级到 P1/P2")

    # segments（≥3，rule 须含量化标记）
    segs = _as_list(_require(data, "segments", "顶层"), "顶层.segments", min_len=3)
    seg_names = set()
    for i, sg in enumerate(segs):
        ctx = f"segments[{i}]"
        if not isinstance(sg, dict):
            raise SchemaError(f"{ctx} 必须为对象")
        nm = _nonempty_str(_require(sg, "name", ctx), f"{ctx}.name")
        seg_names.add(nm)
        _nonempty_str(_require(sg, "definition", ctx), f"{ctx}.definition")
        rule = _nonempty_str(_require(sg, "rule", ctx), f"{ctx}.rule")
        if not QUANT_RE.search(rule):
            raise SchemaError(
                f"{ctx}.rule=`{rule}` 缺量化标记（须含 数字/天/次/Top/待校准 之一）")
        _nonempty_str(_require(sg, "scale_estimate", ctx), f"{ctx}.scale_estimate")
        _nonempty_str(_require(sg, "value", ctx), f"{ctx}.value")

    # personas（3–5，linked_segment 须在 segments 中）
    personas = _as_list(_require(data, "personas", "顶层"), "顶层.personas", min_len=3)
    if len(personas) > 5:
        raise SchemaError(f"personas 应为 3–5 项，实有 {len(personas)}")
    for i, ps in enumerate(personas):
        ctx = f"personas[{i}]"
        if not isinstance(ps, dict):
            raise SchemaError(f"{ctx} 必须为对象")
        _nonempty_str(_require(ps, "name", ctx), f"{ctx}.name")
        _nonempty_str(_require(ps, "snapshot", ctx), f"{ctx}.snapshot")
        _nonempty_str(_require(ps, "behaviors", ctx), f"{ctx}.behaviors")
        _nonempty_str(_require(ps, "needs", ctx), f"{ctx}.needs")
        _nonempty_str(_require(ps, "pain_points", ctx), f"{ctx}.pain_points")
        _nonempty_str(_require(ps, "touchpoints", ctx), f"{ctx}.touchpoints")
        _nonempty_str(_require(ps, "value_potential", ctx), f"{ctx}.value_potential")
        ls = _nonempty_str(_require(ps, "linked_segment", ctx), f"{ctx}.linked_segment")
        if ls not in seg_names:
            raise SchemaError(
                f"{ctx}.linked_segment=`{ls}` 未在 segments[].name 中出现（persona-分群一致性）")

    # applications（≥3）
    apps = _as_list(_require(data, "applications", "顶层"), "顶层.applications", min_len=3)
    for i, ap in enumerate(apps):
        ctx = f"applications[{i}]"
        if not isinstance(ap, dict):
            raise SchemaError(f"{ctx} 必须为对象")
        _nonempty_str(_require(ap, "scenario", ctx), f"{ctx}.scenario")
        _nonempty_str(_require(ap, "how_to_use", ctx), f"{ctx}.how_to_use")
        _nonempty_str(_require(ap, "target", ctx), f"{ctx}.target")
        _nonempty_str(_require(ap, "metric", ctx), f"{ctx}.metric")

    # insights（人群洞察与动作回路，必填；复用已构建的 seg_names）
    ins = _require(data, "insights", "顶层")
    if not isinstance(ins, dict):
        raise SchemaError("顶层.insights 必须为对象")
    # opportunity_matrix（≥3，segment 须在 segments 中，value_level/growth_potential 枚举高/中/低）
    om = _as_list(_require(ins, "opportunity_matrix", "insights"), "insights.opportunity_matrix", min_len=3)
    om_otypes = set()
    for i, row in enumerate(om):
        ctx = f"insights.opportunity_matrix[{i}]"
        if not isinstance(row, dict):
            raise SchemaError(f"{ctx} 必须为对象")
        seg = _nonempty_str(_require(row, "segment", ctx), f"{ctx}.segment")
        if seg not in seg_names:
            raise SchemaError(f"{ctx}.segment=`{seg}` 未在 segments[].name 中出现（洞察-分群一致性）")
        _enum(_require(row, "value_level", ctx), LEVELS_HML, f"{ctx}.value_level")
        _enum(_require(row, "growth_potential", ctx), LEVELS_HML, f"{ctx}.growth_potential")
        ot = _nonempty_str(_require(row, "opportunity_type", ctx), f"{ctx}.opportunity_type")
        om_otypes.add(ot)
        _nonempty_str(_require(row, "rationale", ctx), f"{ctx}.rationale")
    # action_map（≥3，target_segment 须在 segments 中，expected_metric 须含量化标记，≥3 项不能全 P0）
    am = _as_list(_require(ins, "action_map", "insights"), "insights.action_map", min_len=3)
    am_insights = set()
    am_p = {"P0": 0, "P1": 0, "P2": 0}
    for i, row in enumerate(am):
        ctx = f"insights.action_map[{i}]"
        if not isinstance(row, dict):
            raise SchemaError(f"{ctx} 必须为对象")
        ai = _nonempty_str(_require(row, "insight", ctx), f"{ctx}.insight")
        am_insights.add(ai)
        ts = _nonempty_str(_require(row, "target_segment", ctx), f"{ctx}.target_segment")
        if ts not in seg_names:
            raise SchemaError(f"{ctx}.target_segment=`{ts}` 未在 segments[].name 中出现（洞察-分群一致性）")
        _nonempty_str(_require(row, "action", ctx), f"{ctx}.action")
        _nonempty_str(_require(row, "channel", ctx), f"{ctx}.channel")
        em = _nonempty_str(_require(row, "expected_metric", ctx), f"{ctx}.expected_metric")
        if not QUANT_RE.search(em):
            raise SchemaError(
                f"{ctx}.expected_metric=`{em}` 缺量化标记（须含 数字/%/率/天/次 之一）")
        am_p[_enum(_require(row, "priority", ctx), PRIORITY_LEVELS, f"{ctx}.priority")] += 1
    if len(am) >= 3 and am_p["P1"] + am_p["P2"] == 0:
        raise SchemaError("insights.action_map ≥3 项全标 P0，至少把 1 项降级到 P1/P2")
    # priority_scores（≥3，score 1-5 整数，opportunity 应与 opportunity_type 或 action_map.insight 对应）
    ps = _as_list(_require(ins, "priority_scores", "insights"), "insights.priority_scores", min_len=3)
    valid_opps = om_otypes | am_insights
    for i, row in enumerate(ps):
        ctx = f"insights.priority_scores[{i}]"
        if not isinstance(row, dict):
            raise SchemaError(f"{ctx} 必须为对象")
        opp = _nonempty_str(_require(row, "opportunity", ctx), f"{ctx}.opportunity")
        if valid_opps and opp not in valid_opps:
            raise SchemaError(
                f"{ctx}.opportunity=`{opp}` 未在 opportunity_matrix.opportunity_type 或 action_map.insight 中出现")
        sc = _as_int(_require(row, "score", ctx), f"{ctx}.score")
        if not (1 <= sc <= 5):
            raise SchemaError(f"{ctx}.score={sc} 越界（应在 1–5）")
        _nonempty_str(_require(row, "reasoning", ctx), f"{ctx}.reasoning")

    # projects（≥3，≥4 项不能全 P0）
    projs = _as_list(_require(data, "projects", "顶层"), "顶层.projects", min_len=3)
    p_counts = {"P0": 0, "P1": 0, "P2": 0}
    for i, p in enumerate(projs):
        ctx = f"projects[{i}]"
        if not isinstance(p, dict):
            raise SchemaError(f"{ctx} 必须为对象")
        _nonempty_str(_require(p, "name", ctx), f"{ctx}.name")
        lvl = _enum(_require(p, "priority", ctx), PRIORITY_LEVELS, f"{ctx}.priority")
        p_counts[lvl] += 1
        _nonempty_str(_require(p, "input", ctx), f"{ctx}.input")
        _nonempty_str(_require(p, "output", ctx), f"{ctx}.output")
        _nonempty_str(_require(p, "owner_role", ctx), f"{ctx}.owner_role")
        _nonempty_str(_require(p, "dependency", ctx), f"{ctx}.dependency")
    if len(projs) >= 4 and p_counts["P1"] + p_counts["P2"] == 0:
        raise SchemaError(f"projects 有 {len(projs)} 项全标 P0，至少把 1 项降级到 P1/P2")

    # assumptions / missing_data
    for key in ("assumptions", "missing_data"):
        arr = _as_list(_require(data, key, "顶层"), f"顶层.{key}")
        for i, item in enumerate(arr):
            if not isinstance(item, str) or item.strip() == "":
                raise SchemaError(f"{key}[{i}] 必须为非空字符串")

    return data


# ---------- 渲染 ----------
def render(data):
    mat = data["maturity"]
    dims = data["dimensions"]
    ts = data["tag_system"]
    segs = data["segments"]
    personas = data["personas"]
    apps = data["applications"]
    projs = data["projects"]

    ins = data["insights"]

    L = []
    L.append("# 用户画像与人群洞察\n")

    L.append("## 一句话结论\n")
    L.append(data["conclusion"] + "\n")

    L.append("## 数据基础与画像就绪度\n")
    L.append(f"整体就绪度：{mat['score']:.1f}/5，属于「{mat['summary']}」。\n")

    L.append("## 画像就绪度评分表\n")
    L.append("| 维度 | 现状判断 | 关键指标当前值（待补） | 行业基准/参考 | "
             "主要问题 | 影响 | 成熟度评分 | 优先级 |")
    L.append("|---|---|---|---|---|---|:---:|:---:|")
    for d in dims:
        L.append(
            f"| {d['name']} | {d['status']} | {d['current_value']} | "
            f"{d['benchmark']} | {d['problem']} | {d['impact']} | "
            f"{d['score']} | {d['priority']} |"
        )
    L.append("")

    L.append("## 标签体系设计\n")
    L.append("**标签分层（标准 CDP 六类）**：\n")
    L.append("| 标签层 | 用途 | 示例标签 | 数据源 |")
    L.append("|---|---|---|---|")
    for ly in ts["layers"]:
        L.append(f"| {ly['layer']} | {ly['purpose']} | {ly['example_tags']} | {ly['data_source']} |")
    L.append("")
    L.append("**优先级标签**：\n")
    L.append("| 标签 | 定义 | 规则/口径 | 优先级 |")
    L.append("|---|---|---|:---:|")
    for kt in ts["key_tags"]:
        L.append(f"| {kt['tag']} | {kt['definition']} | {kt['rule']} | {kt['priority']} |")
    L.append("")

    L.append("## 用户分群模型\n")
    L.append("| 分群 | 定义 | 判定规则（量化） | 规模占比估算 | 价值定位 |")
    L.append("|---|---|---|:---:|---|")
    for sg in segs:
        L.append(
            f"| {sg['name']} | {sg['definition']} | {sg['rule']} | "
            f"{sg['scale_estimate']} | {sg['value']} |"
        )
    L.append("")

    L.append("## 代表性用户画像\n")
    L.append("| 画像 | 快照 | 行为特征 | 需求 | 痛点 | 触点偏好 | 价值潜力 | 关联分群 |")
    L.append("|---|---|---|---|---|---|---|---|")
    for ps in personas:
        L.append(
            f"| {ps['name']} | {ps['snapshot']} | {ps['behaviors']} | {ps['needs']} | "
            f"{ps['pain_points']} | {ps['touchpoints']} | {ps['value_potential']} | "
            f"{ps['linked_segment']} |"
        )
    L.append("")

    L.append("## 画像应用场景\n")
    L.append("| 场景 | 怎么用 | 目标人群（画像/分群） | 指标 |")
    L.append("|---|---|---|---|")
    for ap in apps:
        L.append(f"| {ap['scenario']} | {ap['how_to_use']} | {ap['target']} | {ap['metric']} |")
    L.append("")

    # 第 7 部分：人群洞察与动作回路（核心增量）
    L.append("## 人群洞察与动作回路\n")
    L.append("**人群机会矩阵**：\n")
    L.append("| 分群 | 价值定位 | 增长潜力 | 机会类型 | 理由 |")
    L.append("|---|:---:|:---:|---|---|")
    for row in ins["opportunity_matrix"]:
        L.append(
            f"| {row['segment']} | {row['value_level']} | {row['growth_potential']} | "
            f"{row['opportunity_type']} | {row['rationale']} |")
    L.append("")
    L.append("**洞察→动作映射**：\n")
    L.append("| 洞察 | 目标分群 | 动作 | 渠道 | 预期指标 | 优先级 |")
    L.append("|---|---|---|---|---|:---:|")
    for row in ins["action_map"]:
        L.append(
            f"| {row['insight']} | {row['target_segment']} | {row['action']} | "
            f"{row['channel']} | {row['expected_metric']} | {row['priority']} |")
    L.append("")
    L.append("**机会优先级评分**：\n")
    L.append("| 机会 | 评分 | 理由 |")
    L.append("|---|:---:|---|")
    for row in ins["priority_scores"]:
        L.append(f"| {row['opportunity']} | {row['score']} | {row['reasoning']} |")
    L.append("")

    L.append("## 项目事项清单\n")
    L.append("| 项目事项 | 优先级 | 需要输入 | 预期产出 | 建议负责人角色 | 依赖条件 |")
    L.append("|---|:---:|---|---|---|---|")
    for p in projs:
        L.append(
            f"| {p['name']} | {p['priority']} | {p['input']} | "
            f"{p['output']} | {p['owner_role']} | {p['dependency']} |"
        )
    L.append("")

    L.append("## 缺失信息与假设\n")
    for a in data["assumptions"]:
        L.append(f"- 假设：{a}")
    for m in data["missing_data"]:
        L.append(f"- 待补：{m}")
    L.append("- 不臆造数字：所有阈值/规模/预测分在补充前均标「待补/待验证」。")
    L.append("")

    return "\n".join(L)


# ---------- main ----------
class _ArgParser(argparse.ArgumentParser):
    def error(self, message):
        self.print_usage(sys.stderr)
        sys.stderr.write(f"{self.prog}: error: {message}\n")
        sys.exit(1)


def main():
    ap = _ArgParser(description="校验画像与洞察方案 JSON 并渲染为 Markdown（用户画像与人群洞察）")
    ap.add_argument("input", help="输入 JSON 文件路径，或 `-` 读 stdin")
    ap.add_argument("--out", required=True, help="输出 Markdown 文件路径")
    args = ap.parse_args()

    try:
        if args.input == "-":
            raw = sys.stdin.read()
        else:
            raw = Path(args.input).read_text(encoding="utf-8")
    except FileNotFoundError:
        print(f"错误：输入文件不存在：{args.input}", file=sys.stderr)
        return 1
    except OSError as e:
        print(f"错误：读取输入失败：{e}", file=sys.stderr)
        return 1

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"错误（exit 9）：JSON 解析失败：{e}", file=sys.stderr)
        return 9

    try:
        data = validate(data)
    except SchemaError as e:
        print(f"错误（exit 2）：schema 不合规：{e}", file=sys.stderr)
        return 2

    md = render(data)
    out_path = Path(args.out)
    try:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(md, encoding="utf-8")
    except OSError as e:
        print(f"错误（exit 3）：写盘失败：{e}", file=sys.stderr)
        return 3

    print(f"已渲染：{out_path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
