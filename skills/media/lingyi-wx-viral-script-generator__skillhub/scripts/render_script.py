#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""视频号爆款文案生成（体验版）—— JSON 校验 + Markdown 渲染

职责：
  1. 读取 agent 生成的脚本 JSON（文件路径或 `-` 读 stdin）；
  2. 按 references/output-schema.md 的契约逐字段校验；
  3. 校验通过则渲染 Markdown 脚本文档到 --out；失败按退出码返回中文报错。

退出码：
  0 成功 / 1 参数错误 / 2 schema 不合规 / 3 写盘失败 / 9 JSON 解析失败

纯标准库，无第三方依赖。
"""

import argparse
import json
import sys
from pathlib import Path

# ---------- 枚举（与 references/output-schema.md 保持一致） ----------
CAMPAIGN_TYPES = {
    "short_video_seeding", "influencer_collaboration", "live_stream_clip",
    "brand_exposure", "fan_growth", "content_seeding", "product_review",
}
CAMPAIGN_CN = {
    "short_video_seeding": "短视频种草",
    "influencer_collaboration": "达人合作",
    "live_stream_clip": "直播切片",
    "brand_exposure": "品牌曝光",
    "fan_growth": "涨粉",
    "content_seeding": "内容种草",
    "product_review": "产品测评",
}
SCRIPT_TYPES = {"pain_point", "scene", "drama", "testimonial", "unboxing", "tutorial"}
DENSITY = {"high", "medium", "low"}
ENERGY = {"low", "medium", "high"}
CTA_TYPES = {"收藏", "关注", "购买", "点击购物车", "评论互动", "转发", "点赞"}
HOOK_TYPES = {
    "利益", "冲突", "痛点提问", "悬念", "反差", "共鸣", "数据", "反常识",
    "场景建立", "身份锚定",
}

# 教程/制作型中段上限 7，其余 5
SEG_LIMIT = {"tutorial": 7}


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
    return v


def _as_int_sec(v, ctx):
    """start_time/end_time 接受整数字符串或 int，转 int。允许带 [推断] 后缀。"""
    if isinstance(v, int):
        return v
    if isinstance(v, str):
        s = v.strip().rstrip("s")
        # 容忍 "138[推断]" 之类
        for cut in ("[", "（", "("):
            if cut in s:
                s = s.split(cut, 1)[0]
        try:
            return int(s)
        except ValueError:
            raise SchemaError(f"{ctx}时间值 `{v}` 不是合法整数秒")
    raise SchemaError(f"{ctx}时间值 `{v}` 必须为整数或整数字符串")


def _enum(v, allowed, ctx):
    if v not in allowed:
        raise SchemaError(f"{ctx}值 `{v}` 非法，合法值：{sorted(allowed)}")
    return v


# ---------- 校验 ----------
def validate(data):
    if not isinstance(data, dict):
        raise SchemaError("顶层必须为 JSON 对象")

    title = _nonempty_str(_require(data, "title", "顶层"), "顶层.title")
    if len(title) > 15:
        raise SchemaError(f"顶层.title 长度 {len(title)} 超过 15 字")
    # 无标点：宽松校验，仅禁止常见标点
    for ch in "，。！？、；：,.!?;:":
        if ch in title:
            raise SchemaError(f"顶层.title 不应含标点 `{ch}`")

    duration = _require(data, "duration_sec", "顶层")
    if not isinstance(duration, int) or duration <= 0:
        raise SchemaError("顶层.duration_sec 必须为正整数")

    # info
    info = _require(data, "info", "顶层")
    if not isinstance(info, dict):
        raise SchemaError("顶层.info 必须为对象")
    for k in ("purpose", "industry", "audience", "topic"):
        _nonempty_str(_require(info, k, "info"), f"info.{k}")
    # info.product 可选

    # campaign_types
    ct = _require(data, "campaign_types", "顶层")
    if not isinstance(ct, list) or not ct:
        raise SchemaError("顶层.campaign_types 必须为非空数组")
    for i, c in enumerate(ct):
        _enum(c, CAMPAIGN_TYPES, f"campaign_types[{i}]")

    # script_type
    st = _enum(_require(data, "script_type", "顶层"), SCRIPT_TYPES, "顶层.script_type")

    struct = _require(data, "structure", "顶层")
    if not isinstance(struct, dict):
        raise SchemaError("顶层.structure 必须为对象")

    hook = _require(struct, "hook", "structure")
    body = _require(struct, "body", "structure")
    cta = _require(struct, "cta", "structure")
    rhythm = _require(struct, "rhythm", "structure")
    _nonempty_str(_require(struct, "structure_summary", "structure"), "structure.structure_summary")
    _nonempty_str(_require(struct, "rhythm_evidence", "structure"), "structure.rhythm_evidence")
    pc = _require(struct, "product_conversion", "structure")
    if pc is not None and not isinstance(pc, dict):
        raise SchemaError("structure.product_conversion 必须为对象或 null")
    tags = _require(struct, "tags", "structure")
    if not isinstance(tags, list) or not tags:
        raise SchemaError("structure.tags 必须为非空数组")

    # ---- hook ----
    def _seg_common(seg, ctx, index_fixed=None, section=None, function=None,
                    allow_info=False, allow_visual=False):
        if not isinstance(seg, dict):
            raise SchemaError(f"{ctx} 必须为对象")
        if index_fixed is not None:
            if seg.get("index") != index_fixed:
                raise SchemaError(f"{ctx}.index 必须为 {index_fixed}，实为 {seg.get('index')}")
        if section is not None and seg.get("section") != section:
            raise SchemaError(f"{ctx}.section 必须为 `{section}`，实为 `{seg.get('section')}`")
        if function is not None and seg.get("function") != function:
            raise SchemaError(f"{ctx}.function 必须为 `{function}`，实为 `{seg.get('function')}`")
        _nonempty_str(_require(seg, "time_range", ctx), f"{ctx}.time_range")
        start = _as_int_sec(_require(seg, "start_time", ctx), f"{ctx}.start_time")
        end = _as_int_sec(_require(seg, "end_time", ctx), f"{ctx}.end_time")
        if start < 0 or end <= start:
            raise SchemaError(f"{ctx} 时间区间非法：start={start} end={end}")
        _nonempty_str(_require(seg, "visual", ctx), f"{ctx}.visual（画面）")
        _nonempty_str(_require(seg, "dialogue", ctx), f"{ctx}.dialogue（台词）")
        note = _require(seg, "note", ctx)
        if not isinstance(note, str) or note.strip() == "":
            raise SchemaError(f"{ctx}.note 必须为非空字符串（无内容填 -）")
        ttype = _require(seg, "type", ctx)
        if not isinstance(ttype, str):
            raise SchemaError(f"{ctx}.type 必须为字符串")
        if allow_info:
            _enum(_require(seg, "info_density", ctx), DENSITY, f"{ctx}.info_density")
            if allow_visual:
                _nonempty_str(_require(seg, "visual_switch", ctx), f"{ctx}.visual_switch")
        return start, end, ttype

    h_start, h_end, h_type = _seg_common(hook, "structure.hook",
                                           index_fixed=1, section="Hook段", function="抓注意力")
    _enum(h_type, HOOK_TYPES, "structure.hook.type")

    # ---- body.segments ----
    if not isinstance(body, dict):
        raise SchemaError("structure.body 必须为对象")
    segs = _require(body, "segments", "structure.body")
    if not isinstance(segs, list) or not segs:
        raise SchemaError("structure.body.segments 必须为非空数组")
    limit = SEG_LIMIT.get(st, 5)
    if len(segs) > limit:
        raise SchemaError(f"script_type=`{st}` 中段上限 {limit}，实有 {len(segs)} 段")

    prev_end = h_end
    for i, seg in enumerate(segs):
        ctx = f"structure.body.segments[{i}]"
        s_start, s_end, _ = _seg_common(seg, ctx, allow_info=True, allow_visual=True)
        expected_idx = i + 2
        if seg.get("index") != expected_idx:
            raise SchemaError(f"{ctx}.index 应为 {expected_idx}，实为 {seg.get('index')}")
        if s_start != prev_end:
            raise SchemaError(
                f"时间轴断裂：{ctx}.start_time={s_start}，应为上一段 end={prev_end}")
        prev_end = s_end

    # ---- cta ----
    c_start, c_end, c_type = _seg_common(cta, "structure.cta",
                                           index_fixed=99, section="CTA段", function="转化引导")
    _enum(c_type, CTA_TYPES, "structure.cta.type")
    if c_start != prev_end:
        raise SchemaError(
            f"时间轴断裂：structure.cta.start_time={c_start}，应为上一段 end={prev_end}")
    if c_end != duration:
        raise SchemaError(
            f"structure.cta.end_time={c_end} 必须等于 duration_sec={duration}")

    # ---- rhythm ----
    if not isinstance(rhythm, dict):
        raise SchemaError("structure.rhythm 必须为对象")
    _nonempty_str(_require(rhythm, "info_switch_interval", "rhythm"), "rhythm.info_switch_interval")
    _nonempty_str(_require(rhythm, "emotion_curve", "rhythm"), "rhythm.emotion_curve")
    _enum(_require(rhythm, "energy_level", "rhythm"), ENERGY, "rhythm.energy_level")

    return data


# ---------- 渲染 ----------
def render(data):
    info = data.get("info", {})
    st_map = {"pain_point": "痛点解决型", "scene": "场景植入型", "drama": "剧情种草型",
              "testimonial": "口播种草型", "unboxing": "开箱测评型", "tutorial": "教程/制作型"}
    s = data["structure"]
    sec = lambda v: f"{v // 3600:02d}:{(v % 3600) // 60:02d}:{v % 60:02d}"
    duration = data["duration_sec"]

    lines = []
    lines.append(f"# 爆款脚本：{data['title']}\n")
    lines.append("## 基本信息\n")
    lines.append("| 字段 | 内容 |")
    lines.append("|------|------|")
    lines.append(f"| 脚本类型 | {st_map.get(data['script_type'], data['script_type'])} |")
    lines.append(f"| 创作目的 | {info.get('purpose', '-')} |")
    lines.append(f"| 行业 | {info.get('industry', '-')} |")
    lines.append(f"| 受众 | {info.get('audience', '-')} |")
    lines.append(f"| 选题 | {info.get('topic', '-')} |")
    lines.append(f"| 产品 | {info.get('product', '无')} |")
    lines.append(f"| 预计时长 | {sec(duration)}（{duration}s） |")
    cn_campaigns = ", ".join(CAMPAIGN_CN.get(c, c) for c in data["campaign_types"])
    lines.append(f"| 投放类型 | {cn_campaigns} |\n")

    lines.append("## 脚本类型\n")
    lines.append(f"**{st_map.get(data['script_type'], data['script_type'])}**\n")

    lines.append("## 分段脚本\n")
    lines.append("| 序号 | 段落 | 起止时间 | 段落功能 | 类型 | 画面 | 台词 | 备注 |")
    lines.append("|------|------|---------|---------|------|------|------|------|")

    def row(seg, kind, seq):
        sec_name = seg.get("section", "")
        tr = seg.get("time_range", "")
        fn = seg.get("function", "")
        tp = seg.get("type", "")
        visual = seg.get("visual", "").replace("\n", " ")
        dialogue = seg.get("dialogue", "").replace("\n", " ")
        note = seg.get("note", "").replace("\n", " ")
        density = seg.get("info_density")
        if density:
            tp = f"{tp}（密度 {density}）"
        return f"| {seq} | **{sec_name}** | {tr} | {fn} | {tp} | {visual} | {dialogue} | {note} |"

    seq = 1
    lines.append(row(s["hook"], "hook", seq)); seq += 1
    for seg in s["body"]["segments"]:
        lines.append(row(seg, "body", seq)); seq += 1
    lines.append(row(s["cta"], "cta", seq))
    lines.append("")

    r = s["rhythm"]
    lines.append("## 节奏\n")
    lines.append("| 项 | 内容 |")
    lines.append("|------|------|")
    lines.append(f"| 信息切换间隔 | {r['info_switch_interval']} |")
    lines.append(f"| 情绪曲线 | {r['emotion_curve']} |")
    lines.append(f"| 能量水平 | {r['energy_level']} |")
    lines.append(f"| 结构脉络 | {s['structure_summary']} |")
    lines.append(f"| 节奏证据 | {s['rhythm_evidence']} |\n")

    pc = s.get("product_conversion")
    if pc:
        lines.append("## 产品转化\n")
        lines.append("| 字段 | 内容 |")
        lines.append("|------|------|")
        for k, v in pc.items():
            lines.append(f"| {k} | {v} |")
        lines.append("")

    lines.append("## 标签\n")
    lines.append(" · ".join(f"`{t}`" for t in s["tags"]) + "\n")

    # 口播全文附录
    lines.append("## 附录：口播全文\n")
    full = [s["hook"]["dialogue"]]
    for seg in s["body"]["segments"]:
        full.append(seg["dialogue"])
    full.append(s["cta"]["dialogue"])
    lines.append("\n\n".join(full))
    lines.append("")

    return "\n".join(lines) + "\n"


# ---------- main ----------
class _ArgParser(argparse.ArgumentParser):
    """argparse 默认参数错误退出码 2，与 schema 错误码冲突，覆写为 1。"""

    def error(self, message):
        self.print_usage(sys.stderr)
        sys.stderr.write(f"{self.prog}: error: {message}\n")
        sys.exit(1)


def main():
    ap = _ArgParser(
        description="校验脚本 JSON 并渲染为 Markdown（视频号爆款文案生成 体验版）")
    ap.add_argument("input", help="输入 JSON 文件路径，或 `-` 读 stdin")
    ap.add_argument("--out", required=True, help="输出 Markdown 文件路径")
    args = ap.parse_args()

    # 读输入
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

    # 解析 JSON
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"错误（exit 9）：JSON 解析失败：{e}", file=sys.stderr)
        return 9

    # 校验
    try:
        data = validate(data)
    except SchemaError as e:
        print(f"错误（exit 2）：schema 不合规：{e}", file=sys.stderr)
        return 2

    # 渲染 + 写盘
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
