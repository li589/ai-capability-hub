#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""会员体系搭建 —— Excel 模板生成脚本

生成一份「拿来即填」的会员积分体系空白 Excel 模板（含表头样式 / 冻结首行 / 列宽 / 示例行），
便于运营/会员岗落盘后直接在 Excel 里填自己的等级体系、积分规则、权益矩阵、财务测算。

六个 Sheet：
  1. 使用说明（模板填写要点速查）
  2. 会员等级成长表（等级/成长值/晋级/保级/降级/有效期/升级礼包）
  3. 积分获取规则（行为类型×渠道×权重×上限×生日倍率×有效期）
  4. 积分消耗规则（兑换类型×汇率×ROI×库存×过期/抵现三道门/退款扣分）
  5. 权益配置矩阵（等级×权益类型，含发放方式与动态阈值）
  6. 积分财务测算（预算/单积分价值/月度成本/7大运营指标/积分负债）

依赖：openpyxl（缺失时本脚本引导安装，不强制）。
纯本地、不联网、不扣点。

用法：
  python3 scripts/gen_member_points_xlsx.py [--out PATH]
  python3 scripts/gen_member_points_xlsx.py --install-deps   # 自动 pip 安装 openpyxl
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

OUTPUT_PREFIX = "会员积分体系模板"


def _ensure_openpyxl(install_deps: bool):
    """检测 openpyxl；缺失时引导安装。返回 openpyxl 模块或退出。"""
    try:
        import openpyxl  # noqa: F401
        return openpyxl
    except ImportError:
        sys.stderr.write(
            "[gen_member_points_xlsx] ⚠️ 缺少依赖 openpyxl，无法生成 Excel。\n"
            "请先安装：pip3 install openpyxl（或 python3 -m pip install openpyxl）\n"
            "也可重跑本脚本并带 --install-deps 自动安装：\n"
            "  python3 scripts/gen_member_points_xlsx.py --install-deps\n"
        )
        if install_deps:
            sys.stderr.write("[gen_member_points_xlsx] 正在自动安装 openpyxl …\n")
            import subprocess
            rc = subprocess.call([sys.executable, "-m", "pip", "install", "openpyxl"])
            if rc != 0:
                sys.stderr.write("[gen_member_points_xlsx] 自动安装失败，请手动安装后重试。\n")
                sys.exit(2)
            try:
                import openpyxl  # noqa: F401
                return openpyxl
            except ImportError:
                sys.stderr.write("[gen_member_points_xlsx] 安装后仍导入失败，请检查 pip 环境。\n")
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
def _sheet_readme(wb, openpyxl):
    ws = wb.create_sheet("使用说明", 0)  # 放第一个 sheet
    lines = [
        ["会员积分体系模板 —— 使用说明", ""],
        ["", ""],
        ["本文件由「会员体系搭建」技能生成，是一份拿来即填的空白模板。", ""],
        ["共 5 个 Sheet（对应四件套 + 防刷合规在财务表脚注）：", ""],
        ["  1. 会员等级成长表", "等级/成长值/晋级门槛(五选一)/保级/降级/有效期/升级礼包"],
        ["  2. 积分获取规则", "行为类型×渠道×权重×上限×生日倍率×有效期（含负向行为）"],
        ["  3. 积分消耗规则", "兑换类型×汇率×ROI×库存×过期 + 抵现三道门 + 退款扣分"],
        ["  4. 权益配置矩阵", "等级×权益类型，每格填 valueOrRatio/quota/发放方式"],
        ["  5. 积分财务测算", "预算/单积分价值/月度成本/7大运营指标/积分负债"],
        ["", ""],
        ["填表要点：", ""],
        ["  · 等级数 ≤5 通过；6级警告认知负担；>6 要求精简（腾讯视频8级反例）", ""],
        ["  · 晋级门槛从五选一取值 + 具体数值：累计消费金额/次数/单笔满额/指定商品/积分值", ""],
        ["  · 兑换 ROI = 兑换积分价值 / 商品成本价值，必须 ≥1（<1 触发反向薅羊毛）", ""],
        ["  · 单积分价值 = 总预算 / 总发放量，必须给数值（如0.01元/分），禁\"按市场行情\"", ""],
        ["  · 兑换率目标落 15%-30%，>50% 警告门槛过低，<15% 获取易消耗难", ""],
        ["  · 有效期按行为差异化：消费1年/签到30天/活动7天/会员专属按等级延长（全永久=通胀）", ""],
        ["  · 抵现三道门：使用门槛(满X) + 比例≤50% + 整数倍（如200），缺一不通过", ""],
        ["  · 退款必须原路收回对应积分（防套现漏洞）", ""],
        ["  · 通兑闭环：积分限本平台，禁提现/互兑/通兑通用（防金融化触发人行监管）", ""],
        ["", ""],
        ["三行业默认参数档（按所属行业套用再微调）：", ""],
        ["  · 餐饮（高频复购）：4-5级 / 1元1成长值+1积分 / 90天滚动 / 体验特权 / 预算营收1%", ""],
        ["  · 零售（客单周期）：6级 / 消费分+行为分 / 年制 / 价格+服务特权 / 营收1.5%", ""],
        ["  · 电商（跨品类省钱）：无等级付费一卡通 / 品类返利0.5%-2% / 生态+售后特权", ""],
        ["", ""],
        ["生成脚本：scripts/gen_member_points_xlsx.py（依赖 openpyxl）", ""],
    ]
    for r, (a, b) in enumerate(lines, 1):
        ws.cell(row=r, column=1, value=a)
        ws.cell(row=r, column=2, value=b)
    ws.cell(row=1, column=1).font = openpyxl.styles.Font(bold=True, size=14, color="305496")
    ws.column_dimensions["A"].width = 62
    ws.column_dimensions["B"].width = 62
    ws.sheet_view.showGridLines = False


def _sheet_member_tier(wb, openpyxl):
    from openpyxl.utils import get_column_letter
    ws = wb.create_sheet("会员等级成长表")
    headers = [
        "等级名", "成长值区间", "定级货币", "晋级门槛类型(五选一)", "晋级门槛值",
        "累计制/阶段制", "保级周期", "保级条件", "降级规则", "等级有效期",
        "人数", "占比", "人均LTV", "升级礼包",
    ]
    # 示例行（3 行，茶饮正例脱敏，可删）
    samples = [
        ["见习", "0", "成长值", "注册即得", "-", "阶段制", "-", "-", "-", "永久", "12000", "40%", "80元", "-"],
        ["银卡", "100-799", "成长值", "累计消费金额", "≥100元", "阶段制", "90天滚动", "90天内累计≥100元", "降一级", "90天", "9000", "30%", "280元", "50分"],
        ["金卡", "800-2999", "成长值", "累计消费金额", "≥800元", "阶段制", "90天滚动", "90天内累计≥800元", "降一级", "90天", "5400", "18%", "720元", "100分+满50减10券"],
        ["铂金", "3000-7999", "成长值", "累计消费金额", "≥3000元", "阶段制", "90天滚动", "90天内累计≥3000元(可积分享扣20%)", "降一级", "90天", "2400", "8%", "1800元", "200分+券+赠饮"],
        ["黑卡", "≥8000", "成长值", "累计消费金额", "≥8000元", "阶段制", "90天滚动", "90天内累计≥8000元(可积分享扣30%)", "降一级", "90天", "1200", "4%", "4500元", "300分+券+赠饮+生日双倍"],
    ]
    for c, h in enumerate(headers, 1):
        ws.cell(row=1, column=c, value=h)
    _apply_header(ws, 1, len(headers), openpyxl)
    for r, row in enumerate(samples, 2):
        for c, v in enumerate(row, 1):
            ws.cell(row=r, column=c, value=v)
        _apply_body(ws, r, len(headers), openpyxl)
    for r in range(2 + len(samples), 2 + len(samples) + 12):
        _apply_body(ws, r, len(headers), openpyxl)
    widths = [10, 14, 10, 18, 14, 12, 12, 28, 12, 12, 8, 8, 10, 22]
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.row_dimensions[1].height = 40
    ws.freeze_panes = "A2"
    note_row = 2 + len(samples) + 12 + 1
    ws.cell(row=note_row, column=1, value="说明：等级数≤5通过/6警告/>6不通过；晋级门槛五选一(累计消费金额/次数/单笔满额/指定商品/积分值)+具体数值；必有降级机制(只升不降会金字塔塌缩)；保级门槛略低于升级；高级玩法可积分享扣保级防淡季流失。")
    ws.cell(row=note_row, column=1).font = openpyxl.styles.Font(italic=True, color="7F7F7F")


def _sheet_points_earn(wb, openpyxl):
    from openpyxl.utils import get_column_letter
    ws = wb.create_sheet("积分获取规则")
    headers = [
        "行为类型", "行为", "渠道倍率", "单次积分", "单次上限", "日上限", "月上限",
        "生日倍率", "有效期", "备注",
    ]
    samples = [
        ["消费", "CONSUME 消费下单", "小程序1x·企微1.2x", "每元1分", "无", "5000分", "15万分", "黑卡×2", "1年", "核心行为，明确公式"],
        ["日常", "SIGN_IN 每日签到", "-", "5分", "1次/日", "5分", "150分", "-", "30天", "积分锚点，其他行为相对换算"],
        ["日常", "REVIEW 评价", "-", "20分", "1条首条给分", "20分", "100分", "-", "30天", "同行为限次(仅首条)"],
        ["日常", "CHECK_IN_STORE 门店打卡", "-", "10分", "1次/日", "10分", "100分", "-", "30天", "私域行为"],
        ["传播", "REFERRAL 邀请好友", "-", "200分", "5人/月", "1000分", "1000分", "-", "1年", "裂变激励"],
        ["传播", "SHARE_ORDER 晒单分享", "-", "15分", "1次/日", "15分", "300分", "-", "30天", "UGC"],
        ["新手", "FIRST_PURCHASE 首单", "-", "100分", "1次", "-", "-", "-", "1年", "首次行为>单次>重复"],
        ["新手", "PROFILE_COMPLETE 完善资料", "-", "50分", "1次", "-", "-", "-", "1年", "私域关键行为"],
        ["负向", "退款", "-", "原路收回对应积分", "-", "-", "-", "-", "-", "防套现漏洞"],
        ["负向", "违规/客诉", "-", "扣分", "-", "-", "-", "-", "-", "反薅羊毛"],
    ]
    for c, h in enumerate(headers, 1):
        ws.cell(row=1, column=c, value=h)
    _apply_header(ws, 1, len(headers), openpyxl)
    for r, row in enumerate(samples, 2):
        for c, v in enumerate(row, 1):
            ws.cell(row=r, column=c, value=v)
        _apply_body(ws, r, len(headers), openpyxl)
    for r in range(2 + len(samples), 2 + len(samples) + 12):
        _apply_body(ws, r, len(headers), openpyxl)
    widths = [8, 22, 16, 16, 12, 10, 10, 10, 10, 24]
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.row_dimensions[1].height = 30
    ws.freeze_panes = "A2"
    note_row = 2 + len(samples) + 12 + 1
    ws.cell(row=note_row, column=1, value="说明：行为四类配比参考 新手10-15%/日常30-40%/消费返1-2%销售额/传播30%；三道上限必齐(单次/日/月)；私域行为(加企微/加群/群活跃/完善资料)纳入；赋值排序 首次>单次>重复。")
    ws.cell(row=note_row, column=1).font = openpyxl.styles.Font(italic=True, color="7F7F7F")


def _sheet_points_burn(wb, openpyxl):
    from openpyxl.utils import get_column_letter
    ws = wb.create_sheet("积分消耗规则")
    headers = [
        "兑换类型", "商品/权益", "兑换汇率", "ROI", "库存/配额", "日兑换上限", "过期规则",
    ]
    samples = [
        ["闭环券", "满50减10券(反哺主业)", "50分=10元(50:1)", "2.0", "不限", "3张", "兑换后30天"],
        ["闭环券", "免费升杯券", "100分=1张", "≥1", "500张/月", "1张", "兑换后30天"],
        ["开环实物", "品牌马克杯(成本20元)", "2000分=1个(100:1)", "1.0", "200个/月", "1个", "领取后90天"],
        ["抵现", "订单抵扣", "100分=1元", "-", "-", "-", "同获取积分有效期"],
        ["抽奖", "单次100分", "期望约束≤100分", "Σ(奖品积分×概率)≤100", "-", "3次/日", "-"],
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
    widths = [12, 24, 22, 22, 12, 12, 16]
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.row_dimensions[1].height = 30
    ws.freeze_panes = "A2"
    note_row = 2 + len(samples) + 10 + 1
    ws.cell(row=note_row, column=1, value="说明：兑换项含闭环(反哺主业券,50:1)+开环(实物,100:1)两类；每个ROI≥1(<1反向薅羊毛,天堂伞案例)；抵现三道门=使用门槛(满X元)+比例≤50%+整数倍(如200)，缺一不通过；抽奖期望约束 Σ(奖品积分×中奖概率)≤单次消耗；有效期按行为差异化(全永久=通胀)；退款原路收回对应积分。")
    ws.cell(row=note_row, column=1).font = openpyxl.styles.Font(italic=True, color="7F7F7F")


def _sheet_benefit_matrix(wb, openpyxl):
    from openpyxl.utils import get_column_letter
    ws = wb.create_sheet("权益配置矩阵")
    # 列：权益类型 + 5个等级（每格填 valueOrRatio / quota / 发放方式[自动/主动]）
    headers = ["权益类型", "见习", "银卡", "金卡", "铂金", "黑卡", "发放方式说明"]
    samples = [
        ["DISCOUNT 折扣", "-", "-", "-", "-", "85折", "自动(零成本)"],
        ["EXCLUSIVE_PRICE 会员价", "-", "部分", "部分", "全品", "全品", "自动"],
        ["FREE_SHIPPING 包邮", "-", "满99", "满79", "满50", "无门槛", "自动"],
        ["BIRTHDAY_GIFT 生日礼", "50分券", "100分券", "200分券+赠饮", "300分券+赠饮(动态阈值)", "500分券+私人订制", "主动(高成本,控兑换率)"],
        ["POINT_MULTIPLY 积分倍率", "1x", "1x", "1.2x", "1.5x", "2x", "自动"],
        ["PRIORITY_SERVICE 优先权", "-", "-", "-", "优先取餐", "优先取餐+专属客服", "自动"],
        ["LEVEL_UP_PACKAGE 升级礼包", "-", "50分", "100分+券", "200分+券", "300分+券+赠饮", "主动"],
        ["PRODUCT_TRIAL 新品试用", "-", "-", "升级赠饮", "升级赠饮", "升级赠饮+新品内测", "主动"],
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
    widths = [26, 12, 12, 16, 22, 24, 24]
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.row_dimensions[1].height = 30
    ws.freeze_panes = "B2"
    note_row = 2 + len(samples) + 10 + 1
    ws.cell(row=note_row, column=1, value="说明：权益三层分层=等级权益(按等级供给)+积分权益(按消耗解锁,见积分消耗规则)+付费会员权益(可选,与免费严格分离)；四原则=穷举/区隔免费与付费/聚焦易理解/每项测成本ROI；零成本权益(折扣/倍率/标识)自动发放，高成本权益(券/礼包)主动兑换控成本；高使用率权益不划入免费等级(伤付费)。")
    ws.cell(row=note_row, column=1).font = openpyxl.styles.Font(italic=True, color="7F7F7F")


def _sheet_finance(wb, openpyxl):
    from openpyxl.utils import get_column_letter
    ws = wb.create_sheet("积分财务测算")
    # 上半：核心测算
    headers = ["项目", "公式", "计划值", "警戒/备注"]
    samples = [
        ["积分预算", "固定比例法=营收×n% / 固定金额法=年X万", "月5万/年60万", "无预算触发异常(防不住通胀)"],
        ["单积分价值", "= 总预算 / 总发放量", "0.01元/分", "必须给数值(禁\"按市场行情\")"],
        ["总发放量(时间维度)", "= 单日发放 × 365 × n(n=1.1-1.2容错)", "6000万分/年", "-"],
        ["总发放量(用户维度)", "= 单人发放 × 总用户数 × n", "校验值", "与时间维度交叉验证"],
        ["月度成本", "= 月度发放量 × 单积分价值 × 实际履行率", "500万分×0.01×0.5=2.5万/月", "三要素齐"],
        ["目标兑换率", "正常区间15%-30%", "20%", "<15%获取易消耗难；>50%门槛过低"],
        ["沉淀率", "= 1 - 兑换率", "80%", "-"],
        ["财务计提成本", "= 沉淀积分 × 单积分价值", "测算值", "-"],
        ["积分负债", "合同负债科目(发分增/消耗减)", "账面值", "禁商户补偿款误记收入(崩盘案例)"],
        ["单等级权益成本ROI", "= 人均权益成本 / 人均贡献毛利", "≥1续档/<1砍权益", "逐档测算"],
    ]
    for c, h in enumerate(headers, 1):
        ws.cell(row=1, column=c, value=h)
    _apply_header(ws, 1, len(headers), openpyxl)
    for r, row in enumerate(samples, 2):
        for c, v in enumerate(row, 1):
            ws.cell(row=r, column=c, value=v)
        _apply_body(ws, r, len(headers), openpyxl)

    # 下半：7大运营指标（空一行）
    start = 2 + len(samples) + 2
    ws.cell(row=start, column=1, value="7大运营指标（带警戒阈值）").font = openpyxl.styles.Font(bold=True, color="305496")
    metric_headers = ["指标", "计划值", "实际值", "警戒"]
    metrics = [
        ["计划发放积分数", "600万分/月", "", "超预算×1.2预警"],
        ["实际发放积分数", "", "", "同上"],
        ["积分兑换率", "20%", "", "<15%获取易消耗难；>50%门槛过低"],
        ["用户使用率", "30%", "", "<20%权益吸引力不足"],
        ["新增客单价", "↑X%", "", "-"],
        ["复购率", "↑X%", "", "-"],
        ["订单占比", "X%", "", "-"],
    ]
    for c, h in enumerate(metric_headers, 1):
        ws.cell(row=start + 1, column=c, value=h)
    _apply_header(ws, start + 1, len(metric_headers), openpyxl)
    for i, row in enumerate(metrics, start + 2):
        for c, v in enumerate(row, 1):
            ws.cell(row=i, column=c, value=v)
        _apply_body(ws, i, len(metric_headers), openpyxl)

    widths = [20, 40, 24, 30]
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.row_dimensions[1].height = 30
    ws.freeze_panes = "A2"
    note_row = start + 2 + len(metrics) + 1
    ws.cell(row=note_row, column=1, value="涉税与会计脚注：消费积分兑换礼品不征个税(财税〔2011〕50号)；签到/注册积分兑换视同销售计销项税；企业所得税积分对应收入递延至兑换或失效时确认；积分负债计入「合同负债」科目，收入分摊用相对公允价值法。防刷合规：四道闸(单日上限/同行为限次/违规扣分/同设备多账号不计分)+通兑闭环(禁提现/互兑/通兑)+发放对象限终端消费者。")
    ws.cell(row=note_row, column=1).font = openpyxl.styles.Font(italic=True, color="7F7F7F")


def build_workbook(openpyxl):
    wb = openpyxl.Workbook()
    default = wb.active
    wb.remove(default)
    _sheet_readme(wb, openpyxl)
    _sheet_member_tier(wb, openpyxl)
    _sheet_points_earn(wb, openpyxl)
    _sheet_points_burn(wb, openpyxl)
    _sheet_benefit_matrix(wb, openpyxl)
    _sheet_finance(wb, openpyxl)
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
            sys.stderr.write("[gen_member_points_xlsx] 写盘失败(%s)，尝试下一兜底路径…\n" % p)
            continue
        except Exception as e:
            last_err = e
            sys.stderr.write("[gen_member_points_xlsx] 写盘异常(%s)：%s，尝试下一兜底路径…\n" % (p, e))
            continue
    sys.stderr.write("[gen_member_points_xlsx] ⚠️ 所有写盘路径均失败：%s（未生成 xlsx）\n" % last_err)
    return ""


def main():
    ap = argparse.ArgumentParser(description="生成会员积分体系空白 Excel 模板（含表头样式/冻结/示例行）")
    ap.add_argument("--out", default=None, help="输出 xlsx 路径（目录或文件均可）；缺省写当前目录")
    ap.add_argument("--install-deps", action="store_true", help="openpyxl 缺失时自动 pip 安装")
    args = ap.parse_args()

    openpyxl = _ensure_openpyxl(args.install_deps)
    wb = build_workbook(openpyxl)
    saved = write_to_disk(wb, args.out)
    # stdout 协议行：供 agent 解析后转告用户
    print("MEMBER_POINTS_XLSX_FILE=" + (saved or ""))
    if saved:
        sys.stderr.write("[gen_member_points_xlsx] ✅ Excel 模板已生成：%s\n" % saved)
        sys.exit(0)
    sys.exit(2)


if __name__ == "__main__":
    main()
