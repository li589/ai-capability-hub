#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""私域标签体系搭建 —— Excel 模板生成脚本 (v0.1.0)

生成一份「拿来即填」的私域标签体系空白 Excel 模板（含表头样式 / 冻结 / 列宽 / 示例行），
便于运营/数据岗落盘后直接在 Excel 里填自己的标签字典、打标方式、治理 SOP、落地路线。

五个 Sheet：
  1. 标签字典（18 字段表头 + 3 行示例）
  2. 打标方式矩阵
  3. 治理 SOP
  4. 落地实施路线
  5. 标签-活动关联

依赖：openpyxl（缺失时本脚本引导安装，不强制）。
纯本地、不联网、不扣点。

用法：
  python3 scripts/gen_tag_system_xlsx.py [--out PATH]
  python3 scripts/gen_tag_system_xlsx.py --install-deps   # 自动 pip 安装 openpyxl
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

OUTPUT_PREFIX = "私域标签体系模板"


def _ensure_openpyxl(install_deps: bool):
    """检测 openpyxl；缺失时引导安装。返回 openpyxl 模块或退出。"""
    try:
        import openpyxl  # noqa: F401
        return openpyxl
    except ImportError:
        sys.stderr.write(
            "[gen_tag_system_xlsx] ⚠️ 缺少依赖 openpyxl，无法生成 Excel。\n"
            "请先安装：pip3 install openpyxl（或 python3 -m pip install openpyxl）\n"
            "也可重跑本脚本并带 --install-deps 自动安装：\n"
            "  python3 scripts/gen_tag_system_xlsx.py --install-deps\n"
        )
        if install_deps:
            sys.stderr.write("[gen_tag_system_xlsx] 正在自动安装 openpyxl …\n")
            import subprocess
            rc = subprocess.call([sys.executable, "-m", "pip", "install", "openpyxl"])
            if rc != 0:
                sys.stderr.write("[gen_tag_system_xlsx] 自动安装失败，请手动安装后重试。\n")
                sys.exit(2)
            try:
                import openpyxl  # noqa: F401
                return openpyxl
            except ImportError:
                sys.stderr.write("[gen_tag_system_xlsx] 安装后仍导入失败，请检查 pip 环境。\n")
                sys.exit(2)
        sys.exit(2)


# 样式 ------------------------------------------------------------------
def _header_style(openpyxl):
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    thin = Side(style="thin", color="BFBFBF")
    return {
        "font": Font(bold=True, color="FFFFFF", size=11),
        "fill": PatternFill("solid", fgColor="305496"),
        "align": Alignment(horizontal="center", vertical="center", wrap_text=True),
        "border": Border(left=thin, right=thin, top=thin, bottom=thin),
    }


def _cell_style(openpyxl):
    from openpyxl.styles import Alignment, Border, Side
    thin = Side(style="thin", color="D9D9D9")
    return {
        "align": Alignment(vertical="top", wrap_text=True),
        "border": Border(left=thin, right=thin, top=thin, bottom=thin),
    }


def _apply_header(ws, row_idx, n_cols, openpyxl):
    st = _header_style(openpyxl)
    for c in range(1, n_cols + 1):
        cell = ws.cell(row=row_idx, column=c)
        cell.font = st["font"]
        cell.fill = st["fill"]
        cell.alignment = st["align"]
        cell.border = st["border"]


def _apply_body(ws, row_idx, n_cols, openpyxl):
    st = _cell_style(openpyxl)
    for c in range(1, n_cols + 1):
        cell = ws.cell(row=row_idx, column=c)
        cell.alignment = st["align"]
        cell.border = st["border"]


# 各 Sheet --------------------------------------------------------------
def _sheet_tag_dict(wb, openpyxl):
    from openpyxl.utils import get_column_letter
    ws = wb.create_sheet("标签字典")
    headers = [
        "标签ID", "标签名", "标签释义", "一级类目", "二级维度", "三级值", "标签类型",
        "口径定义(三段式:①数据源 ②规则 ③优先级/兜底)", "取值枚举", "数据源", "物理落表",
        "打标方式", "打标主体", "标签载体", "优先级(P1-P4)", "业务目的", "应用场景/适用人群",
        "owner(治理)", "新鲜度", "质量分", "状态",
    ]
    # 示例行（3 行，来自 references/sample.md 脱敏）
    samples = [
        ["T001", "用户分层", "复购且频繁互动的高价值客", "价值层级", "用户分层", "A+", "事实",
         "①订单+社群 ②近30天≥2单且互动≥3次 ③订单优先", "A+/A/B/C/D/S/T", "订单+社群", "会员消费表",
         "工具自动", "订单系统T+1", "企微标签", "P1", "重点维护防御", "复购客/1v1", "运营A+数据B", "T+1", "0.85", "上线"],
        ["T002", "来源渠道", "用户进入私域的引流来源", "渠道来源", "公转私来源", "包裹卡/AI外呼/...", "事实",
         "①渠道码 ②加好友时记录来源码 ③渠道码为准", "包裹卡/AI外呼/公众号/小程序/裂变/直播/短信",
         "渠道码系统", "渠道码表", "渠道码自动", "网易云商", "企微标签", "P1", "溯源/差异化欢迎", "新客/公转私入口", "运营A", "实时", "0.90", "上线"],
        ["T003", "促销敏感度", "对促销的响应倾向", "偏好属性", "促销敏感", "排斥/一般/喜欢", "行为",
         "①订单+券 ②促销期领券用券率 ③近3次促销", "排斥/一般/喜欢", "订单+券", "券表",
         "工具自动", "数据中台", "系统标签", "P2", "促销人群筛选", "促销期触达", "运营C", "周", "0.70", "待验证"],
    ]
    for c, h in enumerate(headers, 1):
        ws.cell(row=1, column=c, value=h)
    _apply_header(ws, 1, len(headers), openpyxl)
    for r, row in enumerate(samples, 2):
        for c, v in enumerate(row, 1):
            ws.cell(row=r, column=c, value=v)
        _apply_body(ws, r, len(headers), openpyxl)
    # 留若干空行供填
    for r in range(2 + len(samples), 2 + len(samples) + 20):
        _apply_body(ws, r, len(headers), openpyxl)
    # 列宽
    widths = [8, 12, 22, 10, 12, 16, 8, 32, 26, 12, 12, 12, 14, 10, 12, 16, 18, 14, 10, 8, 8]
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.row_dimensions[1].height = 40
    ws.freeze_panes = "A2"
    # 备注行
    note_row = 2 + len(samples) + 20 + 1
    ws.cell(row=note_row, column=1, value="说明：口径三段式=①数据源 ②规则 ③优先级/兜底，禁「较高/适度」等模糊词；预测标签带 得分+置信度+时间戳；每标签必填打标方式+打标主体+优先级。")
    ws.cell(row=note_row, column=1).font = openpyxl.styles.Font(italic=True, color="7F7F7F")


def _sheet_tag_matrix(wb, openpyxl):
    from openpyxl.utils import get_column_letter
    ws = wb.create_sheet("打标方式矩阵")
    headers = ["标签类别", "打标方式", "打标场景", "操作路径示例", "重要性(S/A/B/C)"]
    samples = [
        ["渠道来源", "渠道码自动", "公转私入口", "网易云商:登录→营销自动化→企微活码→创建→填渠道+打标→生成码引流", "S"],
        ["生日/基础", "SCRM批量", "注册/会员", "SCRM:读身份证7-14位出生月，T+1批量打标", "A"],
        ["消费金额/频次", "工具自动", "下单后", "订单系统按累计金额分桶自动打标", "S"],
        ["偏好/促销敏感", "工具自动", "行为累积", "数据中台按近N次行为计算", "B"],
        ["晒单/活动互动", "活动打标", "活动期", "关联活动，共享表登记+定期更新（见「标签-活动关联」）", "B"],
        ["肤质/护肤诉求", "导购手打", "1v1沟通", "企微侧边栏手动打标", "C"],
    ]
    for c, h in enumerate(headers, 1):
        ws.cell(row=1, column=c, value=h)
    _apply_header(ws, 1, len(headers), openpyxl)
    for r, row in enumerate(samples, 2):
        for c, v in enumerate(row, 1):
            ws.cell(row=r, column=c, value=v)
        _apply_body(ws, r, len(headers), openpyxl)
    for r in range(2 + len(samples), 2 + len(samples) + 10):
        _apply_body(ws, r, len(headers), openpyxl)
    for i, w in enumerate([16, 14, 14, 60, 14], 1):
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.row_dimensions[1].height = 30
    ws.freeze_panes = "A2"


def _sheet_governance(wb, openpyxl):
    from openpyxl.utils import get_column_letter
    ws = wb.create_sheet("治理SOP")
    headers = ["治理项", "规则/口径", "示例"]
    samples = [
        ["打标主体制", "每标签执行owner到工具或人（网易云商渠道码/微盛CRM/SCRM批量/活动打标/导购手打/工具自动），非抽象双owner", "T001→订单系统T+1；T002→网易云商；T004→微盛CRM"],
        ["建设优先级", "P1-P4，P4=实施范围外", "P1(T001/T002/T004)先建，P2(T003)后建"],
        ["运营重要性", "S/A/B/C 4级，决定维护力度", "S(T001/T002)重点维护，B(T003)按需"],
        ["口径冲突仲裁", "同义标签按品类适配，非统一；定主源余者映射", "消费金额分桶随客单价：美妆上限2000/纸品400/咖啡1000"],
        ["上下线规则", "质量分≥0.6 且 人数>0 才上线；<阈值下线或重构；人数=0僵尸标签直接下线", "质量分0.4<0.6 → 下线或重构"],
        ["质量分公式", "覆盖率×0.4 + 准确率×0.4 + 时效性×0.2", "0.85"],
        ["标签-活动关联", "活动打标标签必关联 活动名+激励机制+更新方式", "晒单活动-满3000送150券-共享表每周更新（见「标签-活动关联」sheet）"],
        ["刷新节奏", "月度质量分复核 + 季度标签盘点", "—"],
        ["新标签准入", "业务需求+owner+口径+数据源+打标方式 齐全方可建", "—"],
    ]
    for c, h in enumerate(headers, 1):
        ws.cell(row=1, column=c, value=h)
    _apply_header(ws, 1, len(headers), openpyxl)
    for r, row in enumerate(samples, 2):
        for c, v in enumerate(row, 1):
            ws.cell(row=r, column=c, value=v)
        _apply_body(ws, r, len(headers), openpyxl)
    for r in range(2 + len(samples), 2 + len(samples) + 8):
        _apply_body(ws, r, len(headers), openpyxl)
    for i, w in enumerate([16, 56, 50], 1):
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.row_dimensions[1].height = 30
    ws.freeze_panes = "A2"


def _sheet_rollout(wb, openpyxl):
    from openpyxl.utils import get_column_letter
    ws = wb.create_sheet("落地实施路线")
    headers = ["阶段", "动作", "产出", "验收标准"]
    samples = [
        ["1 盘点", "梳理现有标签+数据源，带人数统计", "标签清单+数据源地图", "人数=0 标僵尸待下线"],
        ["2 设计", "搭架构+字典+治理（前三件套）", "四件套", "口径三段式无模糊、有打标方式+优先级"],
        ["3 打标", "按标签类别定打标方式矩阵", "打标方式矩阵", "每类别有打标方式+操作路径"],
        ["4 验证", "抽样校验准确率/覆盖率", "质量分", "质量分≥阈值、人数>0"],
        ["5 上线", "按 P1-P4 + SABC 重要性分批上线（非全上）", "上线标签集(分批)", "分批有排序"],
        ["6 迭代", "月度复核+季度盘点", "复盘表", "低分/僵尸下线、新需求补建"],
    ]
    for c, h in enumerate(headers, 1):
        ws.cell(row=1, column=c, value=h)
    _apply_header(ws, 1, len(headers), openpyxl)
    for r, row in enumerate(samples, 2):
        for c, v in enumerate(row, 1):
            ws.cell(row=r, column=c, value=v)
        _apply_body(ws, r, len(headers), openpyxl)
    for r in range(2 + len(samples), 2 + len(samples) + 6):
        _apply_body(ws, r, len(headers), openpyxl)
    for i, w in enumerate([10, 40, 28, 40], 1):
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.row_dimensions[1].height = 30
    ws.freeze_panes = "A2"


def _sheet_activity(wb, openpyxl):
    from openpyxl.utils import get_column_letter
    ws = wb.create_sheet("标签-活动关联")
    headers = ["标签ID", "标签名", "关联活动", "激励机制", "更新方式"]
    samples = [
        ["T005", "消费时间", "社群晒单领奖品", "累计消费满3000送150元券", "共享表登记+每周更新"],
        ["T006", "首单", "首单礼活动", "首单送XX", "下单自动触发"],
    ]
    for c, h in enumerate(headers, 1):
        ws.cell(row=1, column=c, value=h)
    _apply_header(ws, 1, len(headers), openpyxl)
    for r, row in enumerate(samples, 2):
        for c, v in enumerate(row, 1):
            ws.cell(row=r, column=c, value=v)
        _apply_body(ws, r, len(headers), openpyxl)
    for r in range(2 + len(samples), 2 + len(samples) + 10):
        _apply_body(ws, r, len(headers), openpyxl)
    for i, w in enumerate([10, 16, 22, 32, 28], 1):
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.row_dimensions[1].height = 30
    ws.freeze_panes = "A2"


def _sheet_readme(wb, openpyxl):
    from openpyxl.utils import get_column_letter
    ws = wb.create_sheet("使用说明", 0)  # 放第一个 sheet
    lines = [
        ["私域标签体系模板 —— 使用说明", ""],
        ["", ""],
        ["本文件由「私域标签体系搭建（免费版）」技能生成，是一份拿来即填的空白模板。", ""],
        ["共 5 个 Sheet：", ""],
        ["  1. 标签字典", "18 字段表头 + 3 行示例；把你的标签逐行填进去（示例行可删）"],
        ["  2. 打标方式矩阵", "按标签类别定「用哪个工具打/谁打/什么场景打」"],
        ["  3. 治理SOP", "owner制/口径仲裁/上下线/质量分等规则"],
        ["  4. 落地实施路线", "盘点→设计→打标→验证→上线→迭代 6 阶段"],
        ["  5. 标签-活动关联", "活动打标标签关联活动名+激励+更新方式"],
        ["", ""],
        ["填表要点：", ""],
        ["  · 口径三段式：①数据源 ②规则 ③优先级/兜底，禁「较高/适度」模糊词", ""],
        ["  · 预测标签带：得分 + 置信度(高/中/低) + 时间戳", ""],
        ["  · 每标签必填：打标方式 + 打标主体 + 优先级(P1-P4)", ""],
        ["  · 价值层级用 A+/A/B/C/D/S/T 七态（9 品牌强共识）", ""],
        ["  · 分桶按品类客单价适配（美妆上限2000/纸品400/咖啡1000+），不要统一分桶", ""],
        ["  · 僵尸标签（人数=0）直接下线，无需等质量分复核", ""],
        ["", ""],
        ["生成脚本：scripts/gen_tag_system_xlsx.py（依赖 openpyxl）", ""],
    ]
    for r, (a, b) in enumerate(lines, 1):
        ws.cell(row=r, column=1, value=a)
        ws.cell(row=r, column=2, value=b)
    ws.cell(row=1, column=1).font = openpyxl.styles.Font(bold=True, size=14, color="305496")
    ws.column_dimensions["A"].width = 60
    ws.column_dimensions["B"].width = 60
    ws.sheet_view.showGridLines = False


def build_workbook(openpyxl):
    wb = openpyxl.Workbook()
    # 删默认 sheet
    default = wb.active
    wb.remove(default)
    _sheet_readme(wb, openpyxl)
    _sheet_tag_dict(wb, openpyxl)
    _sheet_tag_matrix(wb, openpyxl)
    _sheet_governance(wb, openpyxl)
    _sheet_rollout(wb, openpyxl)
    _sheet_activity(wb, openpyxl)
    return wb


def write_to_disk(wb, out_path):
    """三级兜底：--out → 当前目录 → /tmp。返回绝对路径或空。"""
    candidates = []
    if out_path:
        p = Path(out_path).expanduser()
        if p.is_dir():
            p = p / (OUTPUT_PREFIX + ".xlsx")
        candidates.append(p)
    candidates.append(Path.cwd() / (OUTPUT_PREFIX + ".xlsx"))
    candidates.append(Path("/tmp") / (OUTPUT_PREFIX + ".xlsx"))
    last_err = None
    for p in candidates:
        try:
            p.parent.mkdir(parents=True, exist_ok=True)
            wb.save(str(p))
            return str(p.resolve())
        except OSError as e:
            last_err = e
            sys.stderr.write("[gen_tag_system_xlsx] 写盘失败(%s)，尝试下一兜底路径…\n" % p)
            continue
        except Exception as e:
            last_err = e
            sys.stderr.write("[gen_tag_system_xlsx] 写盘异常(%s)：%s，尝试下一兜底路径…\n" % (p, e))
            continue
    sys.stderr.write("[gen_tag_system_xlsx] ⚠️ 所有写盘路径均失败：%s（未生成 xlsx）\n" % last_err)
    return ""


def main():
    ap = argparse.ArgumentParser(description="生成私域标签体系空白 Excel 模板（含表头样式/冻结/示例行）")
    ap.add_argument("--out", default=None, help="输出 xlsx 路径（目录或文件均可）；缺省写当前目录")
    ap.add_argument("--install-deps", action="store_true", help="openpyxl 缺失时自动 pip 安装")
    args = ap.parse_args()

    openpyxl = _ensure_openpyxl(args.install_deps)
    wb = build_workbook(openpyxl)
    saved = write_to_disk(wb, args.out)
    # stdout 协议行：供 agent 解析后转告用户
    print("TAG_SYSTEM_XLSX_FILE=" + (saved or ""))
    if saved:
        sys.stderr.write("[gen_tag_system_xlsx] ✅ Excel 模板已生成：%s\n" % saved)
        sys.exit(0)
    sys.exit(2)


if __name__ == "__main__":
    main()
