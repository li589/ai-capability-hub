#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""直播脚本创作 —— Excel 模板生成脚本

生成一份「拿来即填」的带货直播脚本空白 Excel 模板（含表头样式 / 冻结首行 / 列宽 / 示例行），
便于运营/编导/主播落盘后直接在 Excel 里填自己的整场节奏、单品话术、话术库、合规清单。

六个 Sheet（第6个为可选，仅场景命中时启用）：
  1. 使用说明（四件套+可选逐字稿评分规则 + 六阶段链路 + 七步 + 违禁词速查 + 逐字稿立场）
  2. 整场节奏脚本表（时间节点/直播阶段/主播口播/副播场控/商品链接号/原价/直播价/优惠力度/赠品/库存/画面道具/互动引导/话术类型/备注，14列）
  3. 单品讲解话术表（品名/七步：钩子痛点-引入产品-FABE卖点-信任背书-价格锚点-逼单-FAQ）
  4. 话术分类库（12类话术，每类预留多行）
  5. 合规约束清单（违禁词分类自查 + 憋单合规 + 价格真实性，含改写替代表）
  6. 单品逐字讲稿（可选）：品名/时段/六阶段分段逐字，逼单数字[X]占位

依赖：openpyxl（缺失时本脚本引导安装，不强制）。
纯本地、不联网、不扣点。

用法：
  python3 scripts/gen_live_script_xlsx.py [--out PATH]
  python3 scripts/gen_live_script_xlsx.py --install-deps   # 自动 pip 安装 openpyxl
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

OUTPUT_PREFIX = "直播脚本模板"


def _ensure_openpyxl(install_deps: bool):
    """检测 openpyxl；缺失时引导安装。返回 openpyxl 模块或退出。"""
    try:
        import openpyxl  # noqa: F401
        return openpyxl
    except ImportError:
        sys.stderr.write(
            "[gen_live_script_xlsx] ⚠️ 缺少依赖 openpyxl，无法生成 Excel。\n"
            "请先安装：pip3 install openpyxl（或 python3 -m pip install openpyxl）\n"
            "也可重跑本脚本并带 --install-deps 自动安装：\n"
            "  python3 scripts/gen_live_script_xlsx.py --install-deps\n"
        )
        if install_deps:
            sys.stderr.write("[gen_live_script_xlsx] 正在自动安装 openpyxl …\n")
            import subprocess
            rc = subprocess.call([sys.executable, "-m", "pip", "install", "openpyxl"])
            if rc != 0:
                sys.stderr.write("[gen_live_script_xlsx] 自动安装失败，请手动安装后重试。\n")
                sys.exit(2)
            try:
                import openpyxl  # noqa: F401
                return openpyxl
            except ImportError:
                sys.stderr.write("[gen_live_script_xlsx] 安装后仍导入失败，请检查 pip 环境。\n")
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
        ["直播脚本模板 —— 使用说明", ""],
        ["", ""],
        ["本文件由「直播脚本创作」技能生成，是一份拿来即填的带货直播脚本空白模板。", ""],
        ["共 4 个 Sheet（对应四件套）+ 1 个可选 Sheet（单品逐字讲稿）：", ""],
        ["  1. 整场节奏脚本表", "时间节点/直播阶段/主播口播/副播场控/商品链接号/原价/直播价/优惠力度/赠品/库存/画面道具/互动引导/话术类型/备注"],
        ["  2. 单品讲解话术表", "品名/七步（钩子痛点-引入产品-FABE卖点-信任背书-价格锚点-逼单-FAQ）"],
        ["  3. 话术分类库", "12类话术（开场/留人/互动/锁客/说服/憋单/催单/逼单/成交/活动/感谢/收尾），每类3-5条照念句"],
        ["  4. 合规约束清单", "违禁词分类自查 + 憋单合规 + 价格真实性，含改写替代表"],
        ["  5. 单品逐字讲稿(可选)", "品名/时段/六阶段分段逐字，逼单数字[X]占位——仅新手首播/品牌自播统一/高客单踩词场景才用"],
        ["", ""],
        ["填表要点：", ""],
        ["  · 整场三阶段框架：开场(5-15min暖场) → 正式售卖(初引流/高潮主推/后期返场) → 收尾(15min预告)", ""],
        ["  · 每个主推品走六阶段链路：聚人→留客→锁客举证→说服→催单→逼单→下单", ""],
        ["  · 时间节点必须分钟级（如 0-5min），禁\"开场后\"；直播价/优惠力度/库存必须具体数值，禁\"有优惠\"", ""],
        ["  · 单品七步每步有内容，空步标\"无\"并说明原因，空步>2 不通过", ""],
        ["  · ③卖点用 FABE：特征-优势-利益-证据，句式\"因为…从而…对您而言…你看…\"", ""],
        ["  · ⑤价格锚点必须给原价对比数值；原价须有依据(建议零售价/历史成交价)，无依据算虚假对比", ""],
        ["  · ⑥逼单必须含库存数+倒计时口令（如\"321上链接/最后X单\"），按三型(价格/库存/痛点)组合", ""],
        ["  · 逼单心理学：损失厌恶+价格锚定+稀缺+登门槛，配中控\"电商捧哏\"组合拳", ""],
        ["  · 话术库每条必须是可照念完整句（如\"欢迎XX来到直播间点关注不迷路\"），禁\"做暖场话术\"指令式", ""],
        ["  · 违禁词(四平台2025版)：禁 绝对化(最/第一/唯一/全网最低价)/医疗功效(防脱/治愈)/虚假时限(限时秒杀无时限)/引导第三方加V", ""],
        ["  · 2026审核演进：不只听词还分析语调节奏，规避核心是改表达非躲词（\"价格非常有优势建议比价\"替代\"全网最低价\"）", ""],
        ["  · 憋单合规(抖音)：单次憋单放单≤10min，明确上架时间/库存量/福利发放时间，禁\"条件才上架\"", ""],
        ["", ""],
        ["带货直播默认节奏档（4h抖音带货，按此套用再回填）：", ""],
        ["  · 主推5-8个（讲透七步）+ 引流款 + 利润款 + 活动款，高低价交叉排序", ""],
        ["  · 开场5-15min聚人→留客，售卖初期低价引流，高潮主推，后期返场秒杀，收尾预告", ""],
        ["", ""],
        ["评分判定规则（全可量化，禁\"较好/一般\"）：", ""],
        ["  · 整场阶段枚举覆盖率=开场/售卖/收尾三段+≥3个售卖内阶段齐全 → 通过", ""],
        ["  · 单品七步完整度=七步全有内容 → 通过；空步>2 → 不通过", ""],
        ["  · 话术库12类齐全+每类≥3条 → 通过", ""],
        ["  · 合规违禁词检出数=0 → 通过；>0逐条标红改写复检", ""],
        ["  · 时间节点分钟级占比=100% → 通过", ""],
        ["  · 逐字稿仅场景命中(新手首播/品牌自播统一/高客单踩词)产出，逼单数字[X]占位 → 否则不强出整篇逐字稿", ""],
        ["", ""],
        ["生成脚本：scripts/gen_live_script_xlsx.py（依赖 openpyxl）", ""],
    ]
    for r, (a, b) in enumerate(lines, 1):
        ws.cell(row=r, column=1, value=a)
        ws.cell(row=r, column=2, value=b)
    ws.cell(row=1, column=1).font = openpyxl.styles.Font(bold=True, size=14, color="305496")
    ws.column_dimensions["A"].width = 62
    ws.column_dimensions["B"].width = 62
    ws.sheet_view.showGridLines = False


def _sheet_full_run(wb, openpyxl):
    from openpyxl.utils import get_column_letter
    ws = wb.create_sheet("整场节奏脚本表")
    headers = [
        "时间节点(分钟级)", "直播阶段", "主播动作/口播", "副播场控配合", "商品/链接号",
        "原价", "直播价", "优惠力度", "赠品", "库存", "画面道具贴片", "互动引导", "话术类型", "备注",
    ]
    # 示例行（美妆正例脱敏，可删）
    samples = [
        ["0-5min", "聚人", "暖场问候+概括本场亮点", "场控发福袋", "-", "-", "-", "-", "-", "-", "主播近景", "签到抽免单", "开场", "暖场不省"],
        ["5-10min", "留客", "剧透主推款+宣布福利", "副播上同款照片", "1号链接", "299", "99", "7折+赠小样", "试用装2片", "500", "贴片写卖点", "点赞到1万发红包", "留人", "-"],
        ["10-15min", "锁客举证", "FABE讲品+背书", "场控上检测报告特写", "1号链接", "299", "99", "-", "-", "500", "成分特写", "设问互动", "锁客", "-"],
        ["15-18min", "说服", "功效价位包装对比再强调", "场控上对比图/竞品图", "1号链接", "299", "99", "-", "-", "500", "对比贴片", "想要的扣想要", "说服", "-"],
        ["18-22min", "催单", "宣布价格+限时折扣前X名", "场控改价+报福利", "1号链接", "299", "99", "前100名额外赠", "-", "500", "改价贴片", "要的扣要", "催单", "限时明确"],
        ["22-25min", "逼单", "倒计时+321上链接", "场控踢未付款+报剩余库存", "1号链接", "299", "99", "-", "-", "剩X件", "库存倒计时贴片", "拍下扣已拍", "逼单", "放单时间明确"],
        ["25-28min", "下单", "引导下单+感谢", "场控发补货/答疑", "1号链接", "-", "99", "-", "-", "-", "-", "没抢到的扣补货", "成交", "-"],
        ["230-240min", "返场", "呼声高返场", "场控补库存报剩余", "1号链接", "299", "99", "返场加赠", "-", "剩80件", "返场贴片", "错过1号的扣返场", "返场", "-"],
        ["240-255min", "收尾(剧透期)", "预告明日新品+强调关注", "场控发关注引导", "-", "-", "-", "-", "-", "-", "明日预告贴片", "点关注不错过明日", "收尾", "-"],
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
    widths = [14, 12, 26, 22, 12, 8, 8, 14, 12, 10, 16, 16, 10, 14]
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.row_dimensions[1].height = 40
    ws.freeze_panes = "C2"
    note_row = 2 + len(samples) + 20 + 1
    ws.cell(row=note_row, column=1, value="说明：阶段取枚举 聚人/留客/锁客举证/说服/催单/逼单/下单/返场/转场/收尾(剧透期)；开场/售卖/收尾三段+≥3个售卖内阶段齐全；时间节点分钟级(禁\"开场后\")占比100%；直播价/优惠力度/库存必须具体数值(禁\"有优惠\")；主推品5-8个(>20触发异常8)；每个主推品走完整六阶段链路，引流款跑缩略链路(聚人→催单→下单)。")
    ws.cell(row=note_row, column=1).font = openpyxl.styles.Font(italic=True, color="7F7F7F")


def _sheet_single_product(wb, openpyxl):
    from openpyxl.utils import get_column_letter
    ws = wb.create_sheet("单品讲解话术表")
    headers = [
        "品名", "①钩子/痛点", "②引入产品", "③卖点(FABE:特征-优势-利益-证据)",
        "④信任背书", "⑤价格锚点(原价/门店价/直播价)", "⑥限时限量逼单(库存/倒计时/口令)", "⑦FAQ",
    ]
    samples = [
        ["玻尿酸精华(示例)", "换季敏感泛红起皮", "引入0添加玻尿酸精华", "特征0添加玻尿酸/优势72h保湿实验/利益敏感肌可用不刺激/证据第三方检测报告", "皮肤科医生推荐+品牌专利", "原价299/门店价299/直播价99", "库存500件/倒数5个数/321上1号链接", "敏感肌能用/孕妇咨询医生/早晚用"],
        ["水乳套装(示例)", "敏感肌锁不住水越补越干", "敏感肌专研水乳套装", "特征神经酰胺复配/优势修复屏障/利益减少泛红/证据28天实测", "临床测试+品牌背书", "原价399/门店价399/直播价159", "库存300件/倒数5个数/321上2号", "敏感肌可用/搭配精华用"],
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
    widths = [16, 20, 20, 40, 22, 24, 28, 22]
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.row_dimensions[1].height = 40
    ws.freeze_panes = "B2"
    note_row = 2 + len(samples) + 10 + 1
    ws.cell(row=note_row, column=1, value="说明：七步每步有内容(空步标\"无\"+原因，空步>2不通过)；③卖点用FABE句式\"因为(特征)…从而(优势)…对您而言(利益)…你看(证据)…\"；⑤价格锚点必须给原价对比数值(原价无依据算虚假对比，须标\"建议零售价\"或删原价)；⑥必须含库存数+倒计时口令(如\"321上链接/最后X单\")，按逼单三型(价格/库存/痛点)组合；服饰类可套两公式(卖点+人群+折扣+逼单 / 细节+整体展示+穿搭场景+逼单)；高客单重④信任背书(测评/参数/质保)，⑥用库存型+痛点型非纯价格型。")
    ws.cell(row=note_row, column=1).font = openpyxl.styles.Font(italic=True, color="7F7F7F")


def _sheet_script_library(wb, openpyxl):
    from openpyxl.utils import get_column_letter
    ws = wb.create_sheet("话术分类库")
    headers = ["话术类型", "话术1(可照念完整句)", "话术2", "话术3", "话术4(可选)", "话术5(可选)"]
    # 12类预留示例句
    library = [
        ["开场", "欢迎宝宝来到直播间！点关注不迷路，今晚有重磅福利", "感谢大家来，今晚敏感肌救星千万别走开", "我每晚X点开播，今晚重磅是主推款", "", ""],
        ["留人", "12点整最先抽免单，没关注的点关注加粉丝团领10元券", "接下来这款是今晚重磅别走开", "点赞到1万我发红包", "", ""],
        ["互动(发问式/选择性/节奏型)", "想要的扣想要，我看看人气", "觉得划算的扣划算", "要1号还是2号扣1或2", "", ""],
        ["锁客(展示型/信任型/专业型)", "先看成分表，0添加", "检测报告放大看", "这个浓度同级没有第二家", "", ""],
        ["说服", "和市面含酒精的比，我们0添加", "门店同款你要XXX", "这个价位段没第二家", "", ""],
        ["憋单(⚠️需配套放单时间+库存+倒计时)", "这款库存不多我先讲完再上，想要的扣想要，22分准时上链接库存500件", "讲完倒数5个数放单，库存X件", "(禁\"条件才上架\"\"满X人才上\"，单次憋单放单≤10min)", "", ""],
        ["催单(讲时间/优惠/物流/自留四法)", "库存不多时间紧迫过这波没了", "链接改过价了放心拍先付先得最后2分钟", "有运费险", "这款我也买过门店要XXX今天才XX", ""],
        ["逼单", "所有宝宝准备，321，上链接！", "最后5单手快有手慢无刷新抢", "库存还剩X件，倒数3个数", "", ""],
        ["成交", "拍下的姐妹回来扣已拍优先发货", "没抢到的别急我再去申请库存", "", "", ""],
        ["活动(低价/买X送X/限时限量/差价补偿)", "今晚加赠试用装", "买2送1", "前100名额外赠小样", "买贵补差", ""],
        ["感谢", "感谢XX下单", "感谢大家支持", "", "", ""],
        ["收尾", "明天同一时间开播，剧透明天新品，点关注不错过", "没抢到的明天还有", "", "", ""],
    ]
    for c, h in enumerate(headers, 1):
        ws.cell(row=1, column=c, value=h)
    _apply_header(ws, 1, len(headers), openpyxl)
    for r, row in enumerate(library, 2):
        for c, v in enumerate(row, 1):
            ws.cell(row=r, column=c, value=v)
        _apply_body(ws, r, len(headers), openpyxl)
    widths = [32, 40, 40, 40, 30, 30]
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.row_dimensions[1].height = 30
    ws.freeze_panes = "B2"
    note_row = 2 + len(library) + 1
    ws.cell(row=note_row, column=1, value="说明：12类齐全每类≥3条(缺类补)；每条必须是可照念完整句(禁\"做暖场话术\"指令式)；憋单话术必须配套明确上架时间+库存量+放单倒计时(无触发异常6)；逼单按三型(价格型配价格锚点/库存型配报剩余/痛点型配场景化)组合，配\"电商捧哏\"中控组合拳。")
    ws.cell(row=note_row, column=1).font = openpyxl.styles.Font(italic=True, color="7F7F7F")


def _sheet_verbatim(wb, openpyxl):
    """第6个Sheet：单品逐字讲稿（可选，仅场景命中时启用）。"""
    from openpyxl.utils import get_column_letter
    ws = wb.create_sheet("单品逐字讲稿(可选)")
    ws.cell(row=1, column=1, value="单品逐字讲稿（可选）—— 仅场景命中时产出，否则跳过本Sheet").font = openpyxl.styles.Font(bold=True, size=13, color="305496")
    ws.cell(row=2, column=1, value="触发条件（任一命中才产出）：①新手主播首播要逐字兜底壮胆；②品牌自播要求话术多人轮播统一；③高客单/功效敏感品怕说错功效词踩合规。")
    ws.cell(row=3, column=1, value="原则：逐字讲稿是「单品讲解话术表七步」的展开版，按六阶段分段逐字，内容与七步一致不另起话术；逼单数字用 [X] 占位实时改，不写死假值；不得含违禁词与违规憋单。")
    # 表头（第5行）
    headers = [
        "品名", "逐字讲稿时段",
        "聚人·留客段(逐字)", "锁客举证段(逐字)", "说服段(逐字)",
        "催单段(逐字)", "逼单段(逐字·数字[X]占位)", "FAQ段(逐字)",
    ]
    headers_row = 5
    for c, h in enumerate(headers, 1):
        ws.cell(row=headers_row, column=c, value=h)
    _apply_header(ws, headers_row, len(headers), openpyxl)
    # 示例行（美妆正例脱敏）
    samples = [
        ["玻尿酸精华(示例)", "30-45min",
         "来，宝宝们先别走开，接下来这款是我今晚最想推给你们的一款——换季敏感泛红起皮的姐妹，你们的救星来了，点点关注别迷路",
         "先看成分表，0酒精、0香精、0添加，纯玻尿酸。再看检测报告，72小时保湿实测，敏感肌可用不刺激",
         "和市面上含酒精的精华比，我们这款0添加，敏感肌用着不刺痛；门店同款也是299，这个价位段敏感肌能用的没第二家",
         "今晚直播价只要99，前100名还额外送2片试用装，最后2分钟，先付先得",
         "所有宝宝准备，库存还有[X]件，倒数5个数，5 4 3 2 1，1号链接上！拍下的姐妹回来扣已拍，优先发货",
         "敏感肌能用，这款就是为敏感肌做的；孕妇建议先咨询医生；早晚都用洁面后拍两泵"],
    ]
    for r, row in enumerate(samples, headers_row + 1):
        for c, v in enumerate(row, 1):
            ws.cell(row=r, column=c, value=v)
        _apply_body(ws, r, len(headers), openpyxl)
    for r in range(headers_row + 1 + len(samples), headers_row + 1 + len(samples) + 8):
        _apply_body(ws, r, len(headers), openpyxl)
    widths = [16, 14, 44, 44, 44, 40, 48, 36]
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.row_dimensions[headers_row].height = 40
    ws.freeze_panes = "C6"
    note_row = headers_row + 1 + len(samples) + 8 + 1
    ws.cell(row=note_row, column=1, value="说明：仅场景命中产出（非命中触发异常13不强出）；按六阶段分段每段逐字完整句；逼单段库存/倒计时用[X]占位不写死假值；套用合规清单复检无违禁词无违规憋单；与单品七步内容一致不另起话术。逐字稿是安全垫不是默认件——直播动态性强，默认不出整篇逐字稿，话术库定式句+单品⑥逼单口令已逐字可照念。")
    ws.cell(row=note_row, column=1).font = openpyxl.styles.Font(italic=True, color="7F7F7F")


def _sheet_compliance(wb, openpyxl):
    from openpyxl.utils import get_column_letter
    ws = wb.create_sheet("合规约束清单")
    # 上：违禁词分类自查
    headers = ["检查项", "违规示例(禁用)", "合规改写/要求", "是否通过"]
    checks = [
        ["绝对化用语", "最/第一/唯一/全网最低价/史无前例/顶级/万能(含谐音/简写/拆分变体)", "改为\"今天直播间价格非常有优势，建议比价\"", "[ ] 通过"],
        ["医疗功效夸大(非医疗品)", "防脱发/改善睡眠/一洗白/治愈率", "用使用场景替代医疗词(如\"减少泛红\"非\"治愈\")", "[ ] 通过"],
        ["虚假时限", "限时/秒杀/抢疯了(未配明确时限)", "配明确时限(如\"今晚限时最后2分钟\")", "[ ] 通过"],
        ["引导欺骗/第三方(抖音)", "点击有惊喜/加V咨询/诱导第三方交易", "删引导第三方，留直播间内转化", "[ ] 通过"],
        ["虚假价格对比(视频号)", "\"全国最低价\"式虚假对比", "原价须有依据，改非绝对化表达", "[ ] 通过"],
        ["平台特化-小红书", "虚构体验/过度P图对比/拉踩其他品牌", "真实体验、不拉踩", "[ ] 通过"],
    ]
    for c, h in enumerate(headers, 1):
        ws.cell(row=1, column=c, value=h)
    _apply_header(ws, 1, len(headers), openpyxl)
    for r, row in enumerate(checks, 2):
        for c, v in enumerate(row, 1):
            ws.cell(row=r, column=c, value=v)
        _apply_body(ws, r, len(headers), openpyxl)

    # 下：憋单合规 + 价格真实性（空一行分块）
    start = 2 + len(checks) + 2
    ws.cell(row=start, column=1, value="憋单合规（抖音官方 school.jinritemai.com）").font = openpyxl.styles.Font(bold=True, color="305496")
    biao_headers = ["检查项", "要求", "是否通过"]
    biao = [
        ["单次憋单放单时长", "≤10min", "[ ] 通过"],
        ["放单时间", "明确标注上架时间(如22分)", "[ ] 通过"],
        ["库存量", "明确标注库存量(如500件)", "[ ] 通过"],
        ["福利发放时间", "明确福利发放时间", "[ ] 通过"],
        ["禁止项", "禁\"条件才上架\"\"长时间才上架\"\"满X人才上\"", "[ ] 通过"],
    ]
    for c, h in enumerate(biao_headers, 1):
        ws.cell(row=start + 1, column=c, value=h)
    _apply_header(ws, start + 1, len(biao_headers), openpyxl)
    for i, row in enumerate(biao, start + 2):
        for c, v in enumerate(row, 1):
            ws.cell(row=i, column=c, value=v)
        _apply_body(ws, i, len(biao_headers), openpyxl)

    start2 = start + 2 + len(biao) + 2
    ws.cell(row=start2, column=1, value="价格真实性").font = openpyxl.styles.Font(bold=True, color="305496")
    jia_headers = ["检查项", "要求", "是否通过"]
    jia = [
        ["原价依据", "每项原价须有依据(建议零售价/历史成交价/门店同款价)", "[ ] 通过"],
        ["无依据原价处理", "改标\"建议零售价\"或删原价列只留直播价", "[ ] 通过"],
        ["虚假价格对比", "禁无依据虚标原价做对比(视频号禁\"全国最低价\")", "[ ] 通过"],
    ]
    for c, h in enumerate(jia_headers, 1):
        ws.cell(row=start2 + 1, column=c, value=h)
    _apply_header(ws, start2 + 1, len(jia_headers), openpyxl)
    for i, row in enumerate(jia, start2 + 2):
        for c, v in enumerate(row, 1):
            ws.cell(row=i, column=c, value=v)
        _apply_body(ws, i, len(jia_headers), openpyxl)

    widths = [32, 40, 44, 14]
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.row_dimensions[1].height = 30
    ws.freeze_panes = "A2"
    note_row = start2 + 2 + len(jia) + 1
    ws.cell(row=note_row, column=1, value="说明：违禁词检出数=0通过(>0触发异常5逐条标红改写复检)；2026审核不只听词还分析语调节奏，规避核心是改表达非躲词——控制语速/制造停顿/用非绝对化表达/用画面场景代敏感词。")
    ws.cell(row=note_row, column=1).font = openpyxl.styles.Font(italic=True, color="7F7F7F")


def build_workbook(openpyxl):
    wb = openpyxl.Workbook()
    default = wb.active
    wb.remove(default)
    _sheet_readme(wb, openpyxl)
    _sheet_full_run(wb, openpyxl)
    _sheet_single_product(wb, openpyxl)
    _sheet_script_library(wb, openpyxl)
    _sheet_compliance(wb, openpyxl)
    _sheet_verbatim(wb, openpyxl)
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
            sys.stderr.write("[gen_live_script_xlsx] 写盘失败(%s)，尝试下一兜底路径…\n" % p)
            continue
        except Exception as e:
            last_err = e
            sys.stderr.write("[gen_live_script_xlsx] 写盘异常(%s)：%s，尝试下一兜底路径…\n" % (p, e))
            continue
    sys.stderr.write("[gen_live_script_xlsx] ⚠️ 所有写盘路径均失败：%s（未生成 xlsx）\n" % last_err)
    return ""


def main():
    ap = argparse.ArgumentParser(description="生成带货直播脚本空白 Excel 模板（含表头样式/冻结/示例行）")
    ap.add_argument("--out", default=None, help="输出 xlsx 路径（目录或文件均可）；缺省写当前目录")
    ap.add_argument("--install-deps", action="store_true", help="openpyxl 缺失时自动 pip 安装")
    args = ap.parse_args()

    openpyxl = _ensure_openpyxl(args.install_deps)
    wb = build_workbook(openpyxl)
    saved = write_to_disk(wb, args.out)
    # stdout 协议行：供 agent 解析后转告用户
    print("LIVE_SCRIPT_XLSX_FILE=" + (saved or ""))
    if saved:
        sys.stderr.write("[gen_live_script_xlsx] ✅ Excel 模板已生成：%s\n" % saved)
        sys.exit(0)
    sys.exit(2)


if __name__ == "__main__":
    main()
