#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""全量用户运营体系搭建 —— Excel 模板生成脚本 (v0.2.0)

生成一份「拿来即填」的全量用户运营体系搭建空白 Excel 模板（含表头样式 / 冻结 / 列宽 / 示例行），
便于运营岗落盘后直接在 Excel 里填自己的阶段分层表、旅程图、阶段策略、交叉矩阵、召回漏斗。

六个 Sheet：
  1. 使用说明
  2. 阶段分层表（5 阶段表头 + 示例行）
  3. 生命周期旅程图（阶段 × 七要素）
  4. 阶段运营策略表（阶段 × 维度咬合）
  5. 阶段×价值矩阵（5 阶段 × 高/中/低）
  6. 召回漏斗

依赖：openpyxl（缺失时本脚本引导安装，不强制）。
纯本地、不联网、不扣点。

用法：
  python3 scripts/gen_user_journey_xlsx.py [--out PATH]
  python3 scripts/gen_user_journey_xlsx.py --install-deps   # 自动 pip 安装 openpyxl
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

OUTPUT_PREFIX = "全量用户运营体系搭建模板"


def _ensure_openpyxl(install_deps: bool):
    """检测 openpyxl；缺失时引导安装。返回 openpyxl 模块或退出。"""
    try:
        import openpyxl  # noqa: F401
        return openpyxl
    except ImportError:
        sys.stderr.write(
            "[gen_user_journey_xlsx] ⚠️ 缺少依赖 openpyxl，无法生成 Excel。\n"
            "请先安装：pip3 install openpyxl（或 python3 -m pip install openpyxl）\n"
            "也可重跑本脚本并带 --install-deps 自动安装：\n"
            "  python3 scripts/gen_user_journey_xlsx.py --install-deps\n"
        )
        if install_deps:
            sys.stderr.write("[gen_user_journey_xlsx] 正在自动安装 openpyxl …\n")
            import subprocess
            rc = subprocess.call([sys.executable, "-m", "pip", "install", "openpyxl"])
            if rc != 0:
                sys.stderr.write("[gen_user_journey_xlsx] 自动安装失败，请手动安装后重试。\n")
                sys.exit(2)
            try:
                import openpyxl  # noqa: F401
                return openpyxl
            except ImportError:
                sys.stderr.write("[gen_user_journey_xlsx] 安装后仍导入失败，请检查 pip 环境。\n")
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


def _write_sheet(ws, headers, samples, widths, note, openpyxl, extra_rows=20):
    from openpyxl.utils import get_column_letter
    for c, h in enumerate(headers, 1):
        ws.cell(row=1, column=c, value=h)
    _apply_header(ws, 1, len(headers), openpyxl)
    for r, row in enumerate(samples, 2):
        for c, v in enumerate(row, 1):
            ws.cell(row=r, column=c, value=v)
        _apply_body(ws, r, len(headers), openpyxl)
    for r in range(2 + len(samples), 2 + len(samples) + extra_rows):
        _apply_body(ws, r, len(headers), openpyxl)
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.row_dimensions[1].height = 40
    ws.freeze_panes = "A2"
    if note:
        note_row = 2 + len(samples) + extra_rows + 1
        ws.cell(row=note_row, column=1, value=note)
        ws.cell(row=note_row, column=1).font = openpyxl.styles.Font(italic=True, color="7F7F7F")


# 各 Sheet --------------------------------------------------------------
def _sheet_readme(wb, openpyxl):
    ws = wb.create_sheet("使用说明", 0)
    lines = [
        ["全量用户运营体系搭建模板 —— 使用说明", ""],
        ["", ""],
        ["本文件由「全量用户运营体系搭建」技能生成，是一份拿来即填的空白模板。", ""],
        ["共 5 个业务 Sheet：", ""],
        ["  1. 阶段分层表", "5 阶段(引入/成长/成熟/休眠/流失)×转换条件/特征/指标；把你的阶段逐行填（示例行可删）"],
        ["  2. 生命周期旅程图", "阶段 × 七要素(行为/心智/情绪/触点/痛点/机会/AHA/可离开风险)"],
        ["  3. 阶段运营策略表", "阶段 × 需求/目标/动作/触点/内容/权益/指标/频次"],
        ["  4. 阶段×价值矩阵", "5 阶段 × 高/中/低价值，每格一句话主策略（引用父技能 RFM，不重算）"],
        ["  5. 召回漏斗", "召回次序/人群筛选/渠道/频次/内容权益/效果指标"],
        ["", ""],
        ["填表要点：", ""],
        ["  · 阶段数=5（引入/成长/成熟/休眠/流失）；4 段警告可用，>6 或 <4 回到 5 段", ""],
        ["  · 转换条件必给可量化阈值（天数/次数/金额）+ 标注阈值四法之一（均值/五分位/二八/固定锚定）", ""],
        ["  · 流失阈值基于品类采购周期（餐饮7-15天/零售26-30天/电商60-90天/大家电90-180天），禁纯拍天数", ""],
        ["  · R 口径统一为「最近一次消费距今间隔天数，越小越近期=越有价值」，避免与「R得分越高越好」混用", ""],
        ["  · 新客单独走引入期专属旅程，不并入 RFM 低价值层（RFM 对新客无效）", ""],
        ["  · 价值层收敛高/中/低三档（非 RFM 全 8 象限），每格一句话主策略降负担", ""],
        ["  · 深促(≤5折)设围栏仅给休眠/流失客；成熟高价值客主策略为权益/服务非打折", ""],
        ["  · 召回按「召回 ROI vs 拉新 ROI」决策，仅历史高价值沉睡召回；前 3 次每次≥24h 间隔", ""],
        ["  · 三件套阶段须对齐（分层表/旅程图/策略表），每阶段必挂核心指标，否则「分完不会用」", ""],
        ["", ""],
        ["生成脚本：scripts/gen_user_journey_xlsx.py（依赖 openpyxl）", ""],
    ]
    for r, (a, b) in enumerate(lines, 1):
        ws.cell(row=r, column=1, value=a)
        ws.cell(row=r, column=2, value=b)
    ws.cell(row=1, column=1).font = openpyxl.styles.Font(bold=True, size=14, color="305496")
    ws.column_dimensions["A"].width = 60
    ws.column_dimensions["B"].width = 60
    ws.sheet_view.showGridLines = False


def _sheet_stage_table(wb, openpyxl):
    ws = wb.create_sheet("阶段分层表")
    headers = [
        "阶段", "口语映射", "区间", "阶段定义", "进入条件(转换阈值)", "离开条件",
        "用户特征", "占健康比", "核心指标", "复算节奏",
    ]
    samples = [
        ["引入期", "新客", "获客", "首次接触未成首单", "加好友/注册", "完成首单=AHA", "无交易,认知中", "10-20%", "CAC/首单率/7日留存", "周"],
        ["成长期", "活跃", "升值", "有首单未稳定复购", "首单", "N周期内≥M单=AHA", "1-N单,习惯形成", "20-30%", "复购率/客单价/活跃度", "月"],
        ["成熟期", "高价值客", "升值", "稳定复购贡献主力LTV", "N周期内≥M单且累计达RFM重要价值", "R超休眠阈值", "复购稳定,贡献高", "15-25%", "LTV/客单价/留存/NPS", "月"],
        ["休眠期", "沉睡", "留存", "活跃衰减未流失", "R超休眠阈值(如连续N天未购/未登录)", "R超流失阈值", "历史活跃现衰减", "10-20%", "沉睡占比/唤醒率", "月"],
        ["流失期", "流失", "留存", "长期无互动已离开", "R超流失阈值(如未购≥采购周期×K)", "-", "长期无互动", "5-15%", "流失率/召回率/召回ROI", "季"],
    ]
    note = "说明：转换条件必给可量化阈值+标注四法之一(均值/五分位/二八/固定锚定)；流失阈值基于品类采购周期；R=最近消费距今天数越小越好；高价值是价值维度≠时间维度。"
    _write_sheet(ws, headers, samples, [10, 12, 8, 24, 28, 22, 18, 12, 24, 10], note, openpyxl, extra_rows=20)


def _sheet_journey(wb, openpyxl):
    ws = wb.create_sheet("生命周期旅程图")
    headers = [
        "阶段", "用户行为", "心智想法", "情绪曲线", "触点渠道", "痛点", "机会", "AHA触发器", "可离开风险",
    ]
    samples = [
        ["引入期", "加好友/浏览", "这品牌靠不靠谱", "↑好奇/↓陌生感", "企微/小程序/包装卡", "不懂产品", "新人礼/首单引导", "首单", "高"],
        ["成长期", "复购/互动", "用着不错", "↑认可", "社群/1v1/朋友圈", "选择困难", "组货/复购券", "稳定复购", "中"],
        ["成熟期", "稳定复购/推荐", "认准这家", "↑—满意顶点", "1v1/专属客服", "缺新鲜感", "权益/新品内测", "跨品类/裂变", "中"],
        ["休眠期", "互动衰减", "最近没需求", "↓冷淡", "模板消息/短信", "被打扰", "低打扰唤醒", "重新互动", "高"],
        ["流失期", "无互动", "已遗忘", "↓冷漠", "AI外呼/人工1v1", "无召回理由", "高价值召回", "复购回归", "极高"],
    ]
    note = "说明：七要素齐全；每阶段标注可离开风险；情绪曲线识别「低点+高可离开风险」断点；阶段须与分层表/策略表对齐。"
    _write_sheet(ws, headers, samples, [10, 16, 14, 16, 22, 14, 18, 14, 12], note, openpyxl, extra_rows=20)


def _sheet_strategy(wb, openpyxl):
    ws = wb.create_sheet("阶段运营策略表")
    headers = [
        "阶段", "用户需求", "运营目标", "关键动作", "触点", "内容策略", "权益配置", "核心指标", "频次上限",
    ]
    samples = [
        ["引入期", "降低尝试门槛", "首单转化", "新人礼+破冰引导", "企微1v1+小程序", "产品价值+首单爆款", "新人券/首单礼", "CAC/首单率/7日留存", "首周3次内"],
        ["成长期", "复购激励", "提频+客单价", "复购券+主题组货", "社群+1v1", "使用场景+复购提醒", "复购券/2倍积分", "复购率/客单价", "每周≤2次主动"],
        ["成熟期", "被重视+专属感", "留存+提客单+防流失前置", "权益/服务+新品内测", "1v1专属客服", "会员专属+新品", "权益卡/服务(非打折)", "LTV/客单价/留存/NPS", "每月≤2次主动"],
        ["休眠期", "重新有理由买", "低成本唤醒", "低打扰唤醒,按ROI", "模板消息/短信", "新利益点/回归礼", "回归券(深促设围栏)", "沉睡占比/唤醒率", "前3次≥24h间隔"],
        ["流失期", "被召回理由", "仅高价值召回", "召回漏斗,ROI决策", "AI外呼/人工1v1", "专属召回+情感", "历史偏好召回礼", "流失率/召回率/召回ROI", "≤4次阶梯"],
    ]
    note = "说明：每阶段必挂核心指标；高价值客主策略非深促打折（深促≤5折设围栏仅给休眠/流失）；召回有ROI判断；成熟期不只挂GMV。"
    _write_sheet(ws, headers, samples, [10, 16, 22, 22, 20, 22, 22, 26, 16], note, openpyxl, extra_rows=15)


def _sheet_matrix(wb, openpyxl):
    ws = wb.create_sheet("阶段×价值矩阵")
    headers = ["价值/阶段", "引入期", "成长期", "成熟期", "休眠期", "流失期"]
    samples = [
        ["高价值(M/F高)", "新客专属旅程,首单礼", "提频+跨品类,深化", "权益/服务非打折,防流失前置", "黄金窗口唤醒,高ROI", "召回ROI决策,重点召回"],
        ["中价值", "新手引导,培养习惯", "复购券+主题组合", "提客单+续购提醒", "低成本自动化唤醒", "低成本召回或放弃"],
        ["低价值/新客", "破冰,首单转化", "体验引导,首单后", "基础维持", "放弃/低成本", "放弃"],
    ]
    note = "说明：价值层收敛高/中/低三档（引用父技能 RFM，不重算；非全 8 象限）；新客不并入 RFM 低价值层；每格一句话主策略。"
    _write_sheet(ws, headers, samples, [16, 22, 22, 26, 22, 22], note, openpyxl, extra_rows=15)


def _sheet_recall(wb, openpyxl):
    ws = wb.create_sheet("召回漏斗")
    headers = ["召回次序", "人群筛选", "触达渠道", "频次/间隔", "内容/权益", "效果监控指标"]
    samples = [
        ["第一次", "历史高价值沉睡", "模板消息", "即时", "回归礼券", "打开率/点击率"],
        ["第二次", "第一次未响应", "短信", "≥24h后", "新利益点+召回理由", "短信点击率"],
        ["第三次", "第二次未响应", "AI外呼", "≥24h后", "专属召回+情感", "接通率/召回率"],
        ["第四次", "第三次未响应", "人工1v1", "约7天后", "专属方案", "召回ROI"],
    ]
    note = "说明：前 3 次每次≥24h 间隔；渠道按价值逐级增强；召回 ROI>拉新 ROI 才召回（仅历史高价值），否则长尾走低成本自动化或放弃。"
    _write_sheet(ws, headers, samples, [12, 20, 14, 14, 24, 22], note, openpyxl, extra_rows=12)


def build_workbook(openpyxl):
    wb = openpyxl.Workbook()
    default = wb.active
    wb.remove(default)
    _sheet_readme(wb, openpyxl)
    _sheet_stage_table(wb, openpyxl)
    _sheet_journey(wb, openpyxl)
    _sheet_strategy(wb, openpyxl)
    _sheet_matrix(wb, openpyxl)
    _sheet_recall(wb, openpyxl)
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
            sys.stderr.write("[gen_user_journey_xlsx] 写盘失败(%s)，尝试下一兜底路径…\n" % p)
            continue
        except Exception as e:
            last_err = e
            sys.stderr.write("[gen_user_journey_xlsx] 写盘异常(%s)：%s，尝试下一兜底路径…\n" % (p, e))
            continue
    sys.stderr.write("[gen_user_journey_xlsx] ⚠️ 所有写盘路径均失败：%s（未生成 xlsx）\n" % last_err)
    return ""


def main():
    ap = argparse.ArgumentParser(description="生成全量用户运营体系搭建空白 Excel 模板（含表头样式/冻结/示例行）")
    ap.add_argument("--out", default=None, help="输出 xlsx 路径（目录或文件均可）；缺省写当前目录")
    ap.add_argument("--install-deps", action="store_true", help="openpyxl 缺失时自动 pip 安装")
    args = ap.parse_args()

    openpyxl = _ensure_openpyxl(args.install_deps)
    wb = build_workbook(openpyxl)
    saved = write_to_disk(wb, args.out)
    print("USER_JOURNEY_XLSX_FILE=" + (saved or ""))
    if saved:
        sys.stderr.write("[gen_user_journey_xlsx] ✅ Excel 模板已生成：%s\n" % saved)
        sys.exit(0)
    sys.exit(2)


if __name__ == "__main__":
    main()
