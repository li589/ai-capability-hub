#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""短视频内容审核 —— Excel 模板生成脚本

生成一份「拿来即填」的视频发布前内容质检空白 Excel 模板（含表头样式 / 冻结首行 / 列宽 / 示例行），
便于品牌运营/MCN编导/电商投手落盘后直接在 Excel 里逐条填风险点、改写文案、勾选复核项。

五个 Sheet：
  1. 使用说明（风险分级4档+总判定规则+违禁词A-J分类+绝对化用语两档+特殊行业双关+多模态边界）
  2. 文本层质检表（编号/检查维度/风险描述+真实话术/平台依据/风险等级/修改建议/处置后果/复检状态，8列）
  3. 画面声音复核表（5项固定检查清单+待人工复核标注）
  4. 特殊行业专项表（医美7条绝对禁止+资质关/金融收益承诺禁+持牌/教培学科类禁投+承诺禁/招商投资回报禁+授权，逐项可勾选）
  5. 违禁词基线速查表（A-J分类，明禁vs语境禁两档+语境适用说明）

依赖：openpyxl（缺失时本脚本引导安装，不强制）。
纯本地、不联网、不扣点。

用法：
  python3 scripts/gen_qc_xlsx.py [--out PATH]
  python3 scripts/gen_qc_xlsx.py --install-deps   # 自动 pip 安装 openpyxl
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

OUTPUT_PREFIX = "短视频内容审核清单"


def _ensure_openpyxl(install_deps: bool):
    """检测 openpyxl；缺失时引导安装。返回 openpyxl 模块或退出。"""
    try:
        import openpyxl  # noqa: F401
        return openpyxl
    except ImportError:
        sys.stderr.write(
            "[gen_qc_xlsx] ⚠️ 缺少依赖 openpyxl，无法生成 Excel。\n"
            "请先安装：pip3 install openpyxl（或 python3 -m pip install openpyxl）\n"
            "也可重跑本脚本并带 --install-deps 自动安装：\n"
            "  python3 scripts/gen_qc_xlsx.py --install-deps\n"
        )
        if install_deps:
            sys.stderr.write("[gen_qc_xlsx] 正在自动安装 openpyxl …\n")
            import subprocess
            rc = subprocess.call([sys.executable, "-m", "pip", "install", "openpyxl"])
            if rc != 0:
                sys.stderr.write("[gen_qc_xlsx] 自动安装失败，请手动安装后重试。\n")
                sys.exit(2)
            try:
                import openpyxl  # noqa: F401
                return openpyxl
            except ImportError:
                sys.stderr.write("[gen_qc_xlsx] 安装后仍导入失败，请检查 pip 环境。\n")
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
        ["短视频内容审核清单 —— 使用说明", ""],
        ["", ""],
        ["本文件由「短视频内容审核」技能生成，是一份拿来即填的视频发布前内容质检空白模板。", ""],
        ["共 5 个 Sheet：", ""],
        ["  1. 文本层质检表", "编号/检查维度/风险描述+真实话术/平台依据/风险等级/修改建议(违规词→合规换词)/处置后果/复检状态"],
        ["  2. 画面声音复核表", "5项固定检查清单（过度P图/车牌门头logo二维码/未成年出镜/BGM版权音画同步/AIGC标识）+待人工复核"],
        ["  3. 特殊行业专项表", "医美7条绝对禁止+资质关/金融收益承诺禁+持牌/教培学科类禁投+承诺禁/招商投资回报禁+授权，逐项可勾选"],
        ["  4. 违禁词基线速查表", "A-J分类，明禁vs语境禁两档+语境适用说明（词表只作基线提示，须语境判断不当唯一标尺）"],
        ["", ""],
        ["多模态边界：", ""],
        ["  · 本技能是纯文本方法论，无法直接解析视频/音频二进制", ""],
        ["  · 文本层（口播文案/字幕/标题封面文案）做实质质检：违禁词+语境判断+合规换词", ""],
        ["  · 画面/声音/BGM层只给\"需人工复核的检查清单\"，不强作二进制裁断，诚实标注交人工复核", ""],
        ["", ""],
        ["风险分级4档（禁\"较好/一般/适度\"模糊词）：", ""],
        ["  · 高危(封号级)：涉政/暴恐/色情低俗/绝对化用语明禁(国家级·最高级·最佳)/医疗功效夸大+疗效保证/AIGC未标识/无资质发布专业内容 → 必须修改后方可发布", ""],
        ["  · 中危(限流级)：语境敏感词(顶级·极品·第一)/虚假宣传/诱导导流/恶意营销/夸张标题党/图文不符/价格虚假对比 → 建议人工复查后发布", ""],
        ["  · 低危(扣分级)：低俗过度暴露/过度营销/违规诱导/资料违规/同质化 → 高召回场景再处理或接受", ""],
        ["  · 提示(人工复核)：画面声音层检查清单未确认项 → 标注\"待人工复核\"，不计入分级判定但须提示", ""],
        ["", ""],
        ["总判定规则（全可量化）：", ""],
        ["  · 高危检出数=0 且 中危检出数=0 → 可发布", ""],
        ["  · 高危检出数=0 且 中危检出数>0 → 需修改后发布", ""],
        ["  · 高危检出数>0 → 不建议发布", ""],
        ["", ""],
        ["绝对化用语两档（核心裁定，降低误杀）：", ""],
        ["  · 明确禁用档（广告法第9条原文）：国家级 / 最高级 / 最佳 → 直接判高危", ""],
        ["  · 语境禁用档（2016年文件废止后实务可语境使用）：顶级 / 极品 / 第一 / 首个 / 独家 / 唯一", ""],
        ["    语境可用：自我比较(\"连续三年第一\")·经营理念·分级用语·固定用语·有依据客观陈述(\"本店首个联名款\")", ""],
        ["    语境禁用：无依据承诺(\"全网第一\"\"销量第一\")→ 判中危", ""],
        ["", ""],
        ["违禁词只作基线提示（抖音官方辟谣市面流传词表以讹传讹，如\"米\"是误传）：", ""],
        ["  · 须强制语境判断，不当唯一标尺——\"美白色连衣裙\"的\"美白\"不算功效敏感，不能误删", ""],
        ["  · A-J分类见违禁词基线速查表Sheet", ""],
        ["", ""],
        ["特殊行业资质×内容双关（首批4行业）：", ""],
        ["  · 医美/医疗：资质(医疗机构执业许可证+医疗广告审查证明·广告法46条) + 内容(7条绝对禁止)", ""],
        ["  · 金融/理财：资质(持牌银行/证券/期货/保险/基金) + 内容(禁保本/稳赚不赔/承诺收益·广告法25条)", ""],
        ["  · 教培：资质(学科类基本禁投·标部分待印证/非学科办学许可) + 内容(禁保过/升学率/名师押题·广告法24条)", ""],
        ["  · 招商/加盟：资质(商标注册证+品牌授权) + 内容(禁零风险/躺赚/月入十万·广告法25条)", ""],
        ["  · 原则：\"资质解决能不能发，内容红线解决能不能这么说\"——两道关分开判", ""],
        ["", ""],
        ["平台差异（分平台给判定，不一刀切）：", ""],
        ["  · 加V咨询：抖音禁(引导第三方)/视频号小红书相对宽", ""],
        ["  · 视频号：禁虚假价格对比·价格真实性严", ""],
        ["  · 小红书：禁过度P图·虚构体验·拉踩", ""],
        ["", ""],
        ["生成脚本：scripts/gen_qc_xlsx.py（依赖 openpyxl，缺失退出码2给安装引导；Excel 纯本地生成不上传）", ""],
    ]
    for r, (a, b) in enumerate(lines, 1):
        ws.cell(row=r, column=1, value=a)
        ws.cell(row=r, column=2, value=b)
    ws.cell(row=1, column=1).font = openpyxl.styles.Font(bold=True, size=14, color="305496")
    ws.column_dimensions["A"].width = 62
    ws.column_dimensions["B"].width = 62
    ws.sheet_view.showGridLines = False


def _sheet_text_qc(wb, openpyxl):
    from openpyxl.utils import get_column_letter
    ws = wb.create_sheet("文本层质检表")
    headers = [
        "编号", "检查维度", "风险描述+真实话术", "平台依据", "风险等级",
        "修改建议(违规词→合规换词)", "处置后果", "复检状态",
    ]
    samples = [
        ["P-001(示例)", "绝对化用语", "\"全网最低价\"(无依据绝对化承诺)", "广告法第9条", "高危",
         "\"全网最低价\"→\"今天直播间价格非常有优势,建议比价\"(语境适用：价格优势表达可,禁绝对化承诺)", "限流/扣分/封号", "待修改"],
        ["P-002(示例)", "医疗功效夸大", "\"敏感肌一星期就脱敏\"(非医疗品宣称医疗功效+疗效保证)", "广告法第16条/小红书蒲公英虚假不实类", "高危",
         "\"一星期就脱敏\"→\"换季敏感泛红期可用,坚持保湿有助舒缓\"(语境适用：客观描述可,禁疗效保证)", "下架/限流", "待修改"],
        ["P-003(示例)", "商品功效越界", "\"美白祛斑\"(普通化妆品宣称特殊化妆品功效)", "广告法第16条/蒲公英美妆个护规范", "高危",
         "\"美白祛斑\"→\"提亮肤色\"(或办特妆资质；语境适用：普通化妆品禁特殊功效宣称)", "下架/限流", "待修改"],
        ["P-004(示例)", "诱导导流", "\"加我V咨询详情\"(引导第三方交易)", "抖音第34条恶意导流", "中危",
         "\"加我V咨询详情\"→\"评论区留言或店铺咨询\"(语境适用：抖音严格,小红书相对宽,分平台判)", "限流", "待修改"],
    ]
    for c, h in enumerate(headers, 1):
        ws.cell(row=1, column=c, value=h)
    _apply_header(ws, 1, len(headers), openpyxl)
    for r, row in enumerate(samples, 2):
        for c, v in enumerate(row, 1):
            ws.cell(row=r, column=c, value=v)
        _apply_body(ws, r, len(headers), openpyxl)
    for r in range(2 + len(samples), 2 + len(samples) + 20):
        _apply_body(ws, r, len(headers), openpyxl)
    widths = [12, 16, 40, 30, 14, 44, 16, 12]
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.row_dimensions[1].height = 36
    ws.freeze_panes = "C2"
    note_row = 2 + len(samples) + 20 + 1
    ws.cell(row=note_row, column=1, value="说明：检查维度取枚举(绝对化用语/医疗功效夸大/虚假宣传/诱导导流/恶意营销/夸张标题党/图文不符/价格虚假对比/特殊行业专项/平台通则)；风险描述必含真实话术原文摘录(来自输入)禁空泛；平台依据必引用具体出处(法律条款号\"广告法第16条\"或平台规则\"蒲公英虚假不实类/视频号5.17.2/抖音第33条\")禁无依据；修改建议必\"违规词→合规换词\"成对样例非泛泛建议；风险等级4档枚举(高危/中危/低危/提示)禁\"一般/较好\"；违禁词按语境判断非纯字面(\"美白色连衣裙\"的\"美白\"不算功敏感)；语境禁用词不直接判高危看语境。")
    ws.cell(row=note_row, column=1).font = openpyxl.styles.Font(italic=True, color="7F7F7F")


def _sheet_visual_audio(wb, openpyxl):
    from openpyxl.utils import get_column_letter
    ws = wb.create_sheet("画面声音复核表")
    headers = ["检查项", "规则依据", "说明", "待人工复核", "复核结论(通过/不通过/不适用)"]
    checks = [
        ["是否过度P图/前后对比暗示功效", "视频号第15类制作缺陷/蒲公英过度P图类",
         "前后对比暗示功效、过度P图对比属违规；4.11.6禁\"承诺无法验证的使用前后效果\"", "[ ] 待人工复核", ""],
        ["是否出现车牌/店铺门头/品牌logo/二维码/手机号", "视频号暗限流触发项",
         "画面出现导流信息元素触发暗限流(不提示违规但卡播放量)", "[ ] 待人工复核", ""],
        ["是否未成年出镜", "未成年人保护·蒲公英未成年营销类",
         "<10周岁禁代言；不适宜品类(医美/金融/烟酒等)禁出现未成年形象含表情包", "[ ] 待人工复核", ""],
        ["BGM版权与音画同步", "视频号声音制作缺陷类",
         "禁用未授权流行歌(版权风险)；音画不同步属制作缺陷", "[ ] 待人工复核", ""],
        ["AIGC生成内容是否显著标识", "视频号6.4条/抖音2026.3治理/网信办数字虚拟人征求意见稿",
         "AIGC生成内容须显著标识(4源一致义务)", "[ ] 待人工复核", ""],
    ]
    for c, h in enumerate(headers, 1):
        ws.cell(row=1, column=c, value=h)
    _apply_header(ws, 1, len(headers), openpyxl)
    for r, row in enumerate(checks, 2):
        for c, v in enumerate(row, 1):
            ws.cell(row=r, column=c, value=v)
        _apply_body(ws, r, len(headers), openpyxl)
    for r in range(2 + len(checks), 2 + len(checks) + 6):
        _apply_body(ws, r, len(headers), openpyxl)
    widths = [32, 38, 44, 16, 22]
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.row_dimensions[1].height = 36
    ws.freeze_panes = "A2"
    note_row = 2 + len(checks) + 6 + 1
    ws.cell(row=note_row, column=1, value="说明：本技能是纯文本方法论无法做二进制实质识别，画面/声音层只给\"需人工复核\"提示项不做实质判断；每项标\"待人工复核\"不计入分级判定但须提示；5项固定清单齐全含AIGC标识；用户给画面描述则针对性补项；要画面实质识别建议用平台机审或多模态工具(异常7)。")
    ws.cell(row=note_row, column=1).font = openpyxl.styles.Font(italic=True, color="7F7F7F")


def _sheet_industry(wb, openpyxl):
    from openpyxl.utils import get_column_letter
    ws = wb.create_sheet("特殊行业专项表")
    # 区块标题
    ws.cell(row=1, column=1, value="特殊行业专项检查（仅命中医美/金融/教培/招商任一才填本Sheet，否则走通用红线+差异提示）").font = openpyxl.styles.Font(bold=True, size=13, color="305496")

    row = 3
    # 医美/医疗
    ws.cell(row=row, column=1, value="医美/医疗").font = openpyxl.styles.Font(bold=True, color="C00000")
    row += 1
    ws.cell(row=row, column=1, value="资质关：医疗机构执业许可证 + 医疗广告审查证明（广告法46条·发布前审查）；无→医疗功效宣称判高危禁发").font = openpyxl.styles.Font(bold=True)
    row += 1
    ws.cell(row=row, column=1, value="内容关（7条绝对禁止，逐项核）：").font = openpyxl.styles.Font(bold=True)
    medicine = [
        ["①说明治愈率或有效率", "[ ] 是否命中"],
        ["②与其他产品功效和安全性比较", "[ ] 是否命中"],
        ["③明示暗示成分为\"天然\"因而安全", "[ ] 是否命中"],
        ["④利用学术机构/行业协会/专业人士/患者形象推荐证明", "[ ] 是否命中"],
        ["⑤明示暗示可治疗所有疾病/适应所有症状/人群", "[ ] 是否命中"],
        ["⑥引起公众对健康状况产生不必要担忧恐惧", "[ ] 是否命中"],
        ["⑦含诱导性内容(热销/抢购/试用/家庭必备/免费治疗/无效退款/保险公司保险)", "[ ] 是否命中"],
    ]
    headers2 = ["检查项", "是否命中"]
    for c, h in enumerate(headers2, 1):
        ws.cell(row=row, column=c, value=h)
    _apply_header(ws, row, len(headers2), openpyxl)
    row += 1
    for item in medicine:
        for c, v in enumerate(item, 1):
            ws.cell(row=row, column=c, value=v)
        _apply_body(ws, row, len(headers2), openpyxl)
        row += 1
    row += 1

    # 金融/理财
    ws.cell(row=row, column=1, value="金融/理财").font = openpyxl.styles.Font(bold=True, color="C00000")
    row += 1
    fin_headers = ["检查项", "要求", "是否通过"]
    fin = [
        ["资质关", "持牌(银行/证券/期货/保险/基金)；无牌荐股/导流配资→拒", "[ ] 通过"],
        ["内容关·收益承诺", "禁\"保本/稳赚不赔/承诺收益X%/高息/内幕消息\"(广告法25条)", "[ ] 通过"],
        ["内容关·收益表述", "改\"历史业绩不代表未来,投资有风险,请谨慎决策\"", "[ ] 通过"],
    ]
    for c, h in enumerate(fin_headers, 1):
        ws.cell(row=row, column=c, value=h)
    _apply_header(ws, row, len(fin_headers), openpyxl)
    row += 1
    for item in fin:
        for c, v in enumerate(item, 1):
            ws.cell(row=row, column=c, value=v)
        _apply_body(ws, row, len(fin_headers), openpyxl)
        row += 1
    row += 1

    # 教培
    ws.cell(row=row, column=1, value="教育/培训").font = openpyxl.styles.Font(bold=True, color="C00000")
    row += 1
    edu_headers = ["检查项", "要求", "是否通过"]
    edu = [
        ["资质关", "学科类基本禁投(双减·标【部分待印证】)；非学科凭办学许可/备案", "[ ] 通过"],
        ["内容关·承诺", "禁\"保过/升学率/名校承诺/名师押题/提分保证\"(广告法24条)", "[ ] 通过"],
        ["内容关·代言", "禁利用受益者名义形象作推荐证明", "[ ] 通过"],
    ]
    for c, h in enumerate(edu_headers, 1):
        ws.cell(row=row, column=c, value=h)
    _apply_header(ws, row, len(edu_headers), openpyxl)
    row += 1
    for item in edu:
        for c, v in enumerate(item, 1):
            ws.cell(row=row, column=c, value=v)
        _apply_body(ws, row, len(edu_headers), openpyxl)
        row += 1
    row += 1

    # 招商/加盟
    ws.cell(row=row, column=1, value="招商/加盟").font = openpyxl.styles.Font(bold=True, color="C00000")
    row += 1
    inv_headers = ["检查项", "要求", "是否通过"]
    inv = [
        ["资质关", "商标注册证 + 品牌授权", "[ ] 通过"],
        ["内容关·投资回报", "禁\"零风险/躺赚/月入十万/稳赚不亏\"(广告法25条·投资回报保证)", "[ ] 通过"],
        ["内容关·收益表述", "改客观经营描述,不承诺投资回报", "[ ] 通过"],
    ]
    for c, h in enumerate(inv_headers, 1):
        ws.cell(row=row, column=c, value=h)
    _apply_header(ws, row, len(inv_headers), openpyxl)
    row += 1
    for item in inv:
        for c, v in enumerate(item, 1):
            ws.cell(row=row, column=c, value=v)
        _apply_body(ws, row, len(inv_headers), openpyxl)
        row += 1

    widths = [48, 50, 18]
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.sheet_view.showGridLines = False
    note_row = row + 1
    ws.cell(row=note_row, column=1, value="说明：仅命中首批4行业(医美/金融/教培/招商)才填本Sheet；资质关与内容关分开判——\"资质解决能不能发,内容红线解决能不能这么说\"；资质未确认→高危提示须办资质(异常3)；学科类校外培训判高危须标【部分待印证】(异常9)；其余行业(房地产/烟酒/母婴/保健/宠物)走通用红线+差异提示,完整子库下版扩展。")
    ws.cell(row=note_row, column=1).font = openpyxl.styles.Font(italic=True, color="7F7F7F")


def _sheet_wordlist(wb, openpyxl):
    from openpyxl.utils import get_column_letter
    ws = wb.create_sheet("违禁词基线速查表")
    headers = ["分类", "档位", "基线词/表达", "语境适用说明", "命中判定"]
    wordlist = [
        ["A.全行业通用禁用", "明确禁用档(广告法9条原文)", "国家级 / 最高级 / 最佳", "无语境可用，直接判高危", "高危"],
        ["B.语境禁用", "语境禁用档", "顶级 / 极品 / 第一 / 首个 / 独家 / 唯一", "自我比较(\"连续三年第一\")·经营理念·分级用语·固定用语·有依据客观陈述(\"本店首个联名款\")可用；无依据承诺(\"全网第一\"\"销量第一\")判中危", "看语境：可用 / 中危"],
        ["B.语境禁用", "语境禁用档", "最先进 / 最新技术 / 最权威 / 最安全", "有依据客观陈述可用；无依据承诺判中危", "看语境：可用 / 中危"],
        ["C.医美医疗专项", "明确禁用", "安全无副作用 / 根治 / 最权威专家 / 最佳效果", "医美7条绝对禁止（治愈率/与他品比较/明示天然安全/专业人士患者形象推荐/明示适应所有/引起健康担忧/诱导性内容）；无医疗广告审查证明→禁发", "高危"],
        ["C.医美医疗专项", "明确禁用", "治愈率 / 有效率 / 疗效保证 / 一招见效 / 包治百病 / 无效退款", "同上，医疗功效断言保证禁", "高危"],
        ["D.金融专项", "明确禁用", "保本 / 稳赚不赔 / 零风险 / 承诺收益X% / 高息 / 内幕消息", "金融收益承诺禁(广告法25条)；须持牌，无牌荐股/导流配资→拒", "高危"],
        ["E.教培专项", "明确禁用", "升学率 / 保过 / 名师押题 / 名校承诺 / 提分保证", "教培承诺禁(广告法24条)；学科类基本禁投(标部分待印证)", "高危"],
        ["F.招商专项", "明确禁用", "零风险 / 躺赚 / 月入十万 / 稳赚不亏", "投资回报保证禁(广告法25条)", "高危"],
        ["G.房地产专项", "明确禁用", "升值/投资回报承诺 / 以时间表示位置 / 规划中设施误导宣传", "房地产广告禁投资回报承诺与误导", "高危"],
        ["H.烟酒专项", "明确禁用", "烟草广告(大众媒介) / 饮酒动作 / 酒功效暗示(消除紧张/增加体力)", "烟草大众媒介禁投广告；酒禁饮酒动作与功效暗示诱导无节制饮酒", "高危"],
        ["I.未成年保护专项", "明确禁用", "<10周岁代言 / 儿童网红 / 打赏诱导 / 性征化软色情 / 不安全模仿 / 炫富拜金", "未成年人保护禁项", "高危"],
        ["J.平台通则", "明确禁用", "涉政 / 暴恐 / 色情低俗 / 引战 / 地域歧视 / 虚假宣传 / 恶意导流 / 流量造假 / AIGC未标识 / 夸张标题党 / 图文不符", "跨平台一致通则；AIGC须显著标识(4源一致义务)", "高危(涉政暴恐色情/无资质/AIGC未标识) / 中危(其余)"],
    ]
    for c, h in enumerate(headers, 1):
        ws.cell(row=1, column=c, value=h)
    _apply_header(ws, 1, len(headers), openpyxl)
    for r, row in enumerate(wordlist, 2):
        for c, v in enumerate(row, 1):
            ws.cell(row=r, column=c, value=v)
        _apply_body(ws, r, len(headers), openpyxl)
    widths = [18, 22, 44, 56, 22]
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.row_dimensions[1].height = 30
    ws.freeze_panes = "A2"
    note_row = 2 + len(wordlist) + 1
    ws.cell(row=note_row, column=1, value="说明：本词表只作\"基线提示\"，须强制语境判断不当唯一标尺(抖音官方辟谣市面流传词表以讹传讹如\"米\"是误传)；\"美白色连衣裙\"的\"美白\"不算功效敏感不能误删；逐字进正文引用的规则依据来自★已核验来源(广告法/蒲公英/视频号/网络短视频细则100条)；具体违禁词随平台规则季度更新，建议下版按平台官方更新滚动维护。")
    ws.cell(row=note_row, column=1).font = openpyxl.styles.Font(italic=True, color="7F7F7F")


def build_workbook(openpyxl):
    wb = openpyxl.Workbook()
    default = wb.active
    wb.remove(default)
    _sheet_readme(wb, openpyxl)
    _sheet_text_qc(wb, openpyxl)
    _sheet_visual_audio(wb, openpyxl)
    _sheet_industry(wb, openpyxl)
    _sheet_wordlist(wb, openpyxl)
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
            sys.stderr.write("[gen_qc_xlsx] 写盘失败(%s)，尝试下一兜底路径…\n" % p)
            continue
        except Exception as e:
            last_err = e
            sys.stderr.write("[gen_qc_xlsx] 写盘异常(%s)：%s，尝试下一兜底路径…\n" % (p, e))
            continue
    sys.stderr.write("[gen_qc_xlsx] ⚠️ 所有写盘路径均失败：%s（未生成 xlsx）\n" % last_err)
    return ""


def main():
    ap = argparse.ArgumentParser(description="生成视频发布前内容质检空白 Excel 模板（含表头样式/冻结/示例行）")
    ap.add_argument("--out", default=None, help="输出 xlsx 路径（目录或文件均可）；缺省写当前目录")
    ap.add_argument("--install-deps", action="store_true", help="openpyxl 缺失时自动 pip 安装")
    args = ap.parse_args()

    openpyxl = _ensure_openpyxl(args.install_deps)
    wb = build_workbook(openpyxl)
    saved = write_to_disk(wb, args.out)
    # stdout 协议行：供 agent 解析后转告用户
    print("VIDEO_QC_XLSX_FILE=" + (saved or ""))
    if saved:
        sys.stderr.write("[gen_qc_xlsx] ✅ Excel 模板已生成：%s\n" % saved)
        sys.exit(0)
    sys.exit(2)


if __name__ == "__main__":
    main()
