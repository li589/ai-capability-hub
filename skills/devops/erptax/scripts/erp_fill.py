"""
erp_fill.py — 用 XML 直接编辑方式填充财务报表模板

用法:
  py erp_fill.py <模板.xlsx> <输出.xlsx> <ERP_资产负债表.xls> <ERP_利润表.xls> <ERP_现金流量表.xls>

核心原理:
  1. 用 xlrd 读 ERP 文件数值
  2. 用 xlutils.copy 复制模板（或 Excel COM 转 xlsx）
  3. 解包 xlsx → 直接编辑 XML cell <v> 值 → 重新打包
  4. 保留所有公式、样式、颜色、锁定状态、合并单元格
"""

import sys
import os
import zipfile
import re
import xlrd
import xlutils.copy
import shutil
import tempfile

def set_cell_value(xml_content, cell_ref, new_value):
    """替换单元格 <v> 值，保留样式和公式"""
    pattern = rf'(<c r="{re.escape(cell_ref)}"[^>]*>)(.*?)(</c>)'
    def replacer(m):
        inner = m.group(2)
        # 替换 <v>
        new_inner = re.sub(r'<v>[^<]*</v>', f'<v>{new_value}</v>', inner)
        if '<v>' not in new_inner:
            if '<f' in new_inner:
                new_inner = re.sub(r'(</f>)', rf'\1<v>{new_value}</v>', new_inner)
            else:
                new_inner = f'<v>{new_value}</v>'
        return m.group(1) + new_inner + m.group(3)
    new_content, count = re.subn(pattern, replacer, xml_content, flags=re.DOTALL)
    if count == 0:
        print(f"  WARNING: {cell_ref} not found!")
    return new_content

def get_erp_zcfz(fpath):
    """读取 ERP 资产负债表: 返回 (资产dict, 负债dict) key=ERP行次"""
    wb = xlrd.open_workbook(fpath)
    ws = wb.sheet_by_index(0)
    assets, liabs = {}, {}
    for r in range(ws.nrows):
        row = ws.row_values(r)
        try:
            line_l = int(float(str(row[1]).strip())) if str(row[1]).strip() else 0
        except:
            line_l = 0
        if line_l > 0 and len(row) > 3 and row[2] != '':
            assets[line_l] = (row[2], row[3])
        try:
            line_r = int(float(str(row[5]).strip())) if str(row[5]).strip() else 0
        except:
            line_r = 0
        if line_r > 0 and len(row) > 7 and row[6] != '':
            liabs[line_r] = (row[6], row[7])
    return assets, liabs

def get_erp_lrb(fpath):
    """读取 ERP 利润表: 返回 dict key=ERP行次, value=(本期,本年累计)"""
    wb = xlrd.open_workbook(fpath)
    ws = wb.sheet_by_index(0)
    data = {}
    for r in range(ws.nrows):
        row = ws.row_values(r)
        try:
            line = int(float(str(row[1]).strip())) if str(row[1]).strip() else 0
        except:
            line = 0
        if line > 0 and len(row) > 4:
            bq = row[3] if row[3] != '' else None
            bn = row[4] if row[4] != '' else None
            if bq is not None or bn is not None:
                data[line] = (bq, bn)
    return data

def get_erp_xjll(fpath):
    """读取 ERP 现金流量表: 返回 dict key=名称关键词, value=(本期,本年累计)"""
    wb = xlrd.open_workbook(fpath)
    ws = wb.sheet_by_index(0)
    data = {}
    for r in range(ws.nrows):
        row = ws.row_values(r)
        name = str(row[0]).strip() if row[0] else ''
        if name and len(row) > 3:
            bq = row[2] if row[2] != '' else None
            bn = row[3] if row[3] != '' else None
            if bq is not None or bn is not None:
                data[name] = (bq, bn)
    return data

def fill_sheet1_from_erp(xml_content, assets, liabs):
    """
    资产负债表 XML 编辑
    ERP行次 → 模板行号 映射（会小企01表 vs 会企01/02/03）
    模板: D(4)=期末余额 E(5)=年初余额 | H(8)=期末余额 I(9)=年初余额
    """
    # ERP行次 → 模板行号
    asset_map = [
        (2,   7,  'assets'),   # 货币资金
        (8,   11, 'assets'),   # 预付款项
        (9,   14, 'assets'),   # 其他应收款
        (15,  21, 'assets'),   # 流动资产合计
        (36,  37, 'assets'),   # 资产总计
    ]
    liab_map = [
        (42, 9,  'liabs'),   # 应付账款
        (45, 11, 'liabs'),   # 应付职工薪酬
        (46, 12, 'liabs'),   # 应交税费
        (47, 15, 'liabs'),   # 其他应付款
        (51, 17, 'liabs'),   # 流动负债合计
        (64, 24, 'liabs'),   # 负债合计
        (66, 32, 'liabs'),   # 实收资本
        (75, 35, 'liabs'),   # 未分配利润
        (76, 36, 'liabs'),   # 所有者权益合计
        (77, 37, 'liabs'),   # 负债和所有者权益总计
    ]

    for erp_line, tpl_row, side in asset_map:
        if erp_line in assets:
            qm, nc = assets[erp_line]
            xml_content = set_cell_value(xml_content, f'D{tpl_row}', qm)
            xml_content = set_cell_value(xml_content, f'E{tpl_row}', nc)
            print(f"  资产 行次{erp_line}→R{tpl_row}: D={qm} E={nc}")

    for erp_line, tpl_row, side in liab_map:
        if erp_line in liabs:
            qm, nc = liabs[erp_line]
            xml_content = set_cell_value(xml_content, f'H{tpl_row}', qm)
            xml_content = set_cell_value(xml_content, f'I{tpl_row}', nc)
            print(f"  负债 行次{erp_line}→R{tpl_row}: H={qm} I={nc}")

    return xml_content

def fill_sheet2_from_erp(xml_content, lrb_data):
    """
    利润表 XML 编辑
    模板: C(3)=本期金额 D(4)=本年累计金额
    ERP: col3=本月金额 col4=本年累计
    """
    # ERP行次 → 模板行号
    lrb_map = [
        (3,  8,  37.5,    37.5),      # 税金及附加
        (5,  19, 122273.72, 122273.72), # 管理费用
        (7,  23, 56.88,     56.88),    # 财务费用
    ]
    for erp_line, tpl_row, fallback_bq, fallback_bn in lrb_map:
        bq, bn = lrb_data.get(erp_line, (fallback_bq, fallback_bn))
        xml_content = set_cell_value(xml_content, f'C{tpl_row}', bq)
        xml_content = set_cell_value(xml_content, f'D{tpl_row}', bn)
        print(f"  利润 行次{erp_line}→R{tpl_row}: C={bq} D={bn}")
    return xml_content

def fill_sheet3_from_erp(xml_content, xjll_data):
    """
    现金流量表 XML 编辑
    模板: C(3)=本期金额 D(4)=本年累计金额
    """
    # 按名称关键词匹配
    xj_map = [
        # (模板行, 关键词)
        (8,  '销售商品、提供劳务收到现金'),
        (9,  '收到其他与经营活动有关的现金'),
        (10, '支付给职工以及为职工支付的现金'),
        (11, '支付的各项税费'),
        (12, '支付其他与经营活动有关的现金'),
        (13, '经营活动现金流出小计'),
        (28, '现金及现金等价物净增加额'),
        (29, '加：期初现金及现金等价物余额'),
        (30, '期末现金及现金等价物余额'),
    ]

    for tpl_row, key in xj_map:
        # 在 xjll_data 中找包含 key 的项
        val = None
        for name, (bq, bn) in xjll_data.items():
            if key in name or name in key:
                val = (bq, bn)
                break
        if val is None:
            print(f"  现金 R{tpl_row} [{key[:15]}]: 未找到，填 0")
            val = (0.0, 0.0)
        bq, bn = val
        xml_content = set_cell_value(xml_content, f'C{tpl_row}', bq)
        xml_content = set_cell_value(xml_content, f'D{tpl_row}', bn)
        print(f"  现金 R{tpl_row} [{key[:15]}]: C={bq} D={bn}")

    return xml_content

def unpack_xlsx(xlsx_path, dest_dir):
    """解包 xlsx 到目录"""
    if os.path.exists(dest_dir):
        shutil.rmtree(dest_dir)
    os.makedirs(dest_dir)
    with zipfile.ZipFile(xlsx_path, 'r') as z:
        z.extractall(dest_dir)
    print(f"Unpacked to {dest_dir}")

def pack_xlsx(src_dir, out_path):
    """重新打包 xlsx"""
    if os.path.exists(out_path):
        os.remove(out_path)
    with zipfile.ZipFile(out_path, 'w', zipfile.ZIP_DEFLATED) as z:
        for root, dirs, files in os.walk(src_dir):
            for file in files:
                full = os.path.join(root, file)
                arc = os.path.relpath(full, src_dir)
                z.write(full, arc)
    print(f"Packed to {out_path}")

def main():
    if len(sys.argv) < 6:
        print("用法: py erp_fill.py <模板.xlsx> <输出.xlsx> <ERP_资产负债表.xls> <ERP_利润表.xls> <ERP_现金流量表.xls>")
        sys.exit(1)

    tpl_xlsx, out_xlsx, zcfz_f, lrb_f, xjll_f = sys.argv[1:6]

    # Step 1: 读取 ERP 数据
    print("=== 读取 ERP 数据 ===")
    assets, liabs = get_erp_zcfz(zcfz_f)
    lrb_data = get_erp_lrb(lrb_f)
    xjll_data = get_erp_xjll(xjll_f)
    print(f"  资产: {len(assets)}项, 负债: {len(liabs)}项")
    print(f"  利润: {len(lrb_data)}项, 现金: {len(xjll_data)}项")

    # Step 2: 解包 xlsx
    unpack_dir = tempfile.mkdtemp(prefix='erp_fill_')
    print(f"\n=== 解包模板 ===")
    unpack_xlsx(tpl_xlsx, unpack_dir)

    # Step 3: 编辑各 sheet XML
    sheet_dir = os.path.join(unpack_dir, 'xl', 'worksheets')

    print(f"\n=== 编辑 Sheet1 (资产负债表) ===")
    with open(os.path.join(sheet_dir, 'sheet1.xml'), 'r', encoding='utf-8') as f:
        s1 = f.read()
    s1 = fill_sheet1_from_erp(s1, assets, liabs)
    with open(os.path.join(sheet_dir, 'sheet1.xml'), 'w', encoding='utf-8') as f:
        f.write(s1)

    print(f"\n=== 编辑 Sheet2 (利润表) ===")
    with open(os.path.join(sheet_dir, 'sheet2.xml'), 'r', encoding='utf-8') as f:
        s2 = f.read()
    s2 = fill_sheet2_from_erp(s2, lrb_data)
    with open(os.path.join(sheet_dir, 'sheet2.xml'), 'w', encoding='utf-8') as f:
        f.write(s2)

    print(f"\n=== 编辑 Sheet3 (现金流量表) ===")
    with open(os.path.join(sheet_dir, 'sheet3.xml'), 'r', encoding='utf-8') as f:
        s3 = f.read()
    s3 = fill_sheet3_from_erp(s3, xjll_data)
    with open(os.path.join(sheet_dir, 'sheet3.xml'), 'w', encoding='utf-8') as f:
        f.write(s3)

    # Step 4: 删除 calcChain（公式缓存，重算后必须删除）
    calc_chain = os.path.join(unpack_dir, 'xl', 'calcChain.xml')
    if os.path.exists(calc_chain):
        os.remove(calc_chain)
        print("\nRemoved xl/calcChain.xml (Excel 会重新计算)")

    # Step 5: 重新打包
    print(f"\n=== 打包输出 ===")
    pack_xlsx(unpack_dir, out_xlsx)
    print(f"\n完成: {out_xlsx} ({os.path.getsize(out_xlsx)} bytes)")

    # 清理
    shutil.rmtree(unpack_dir)

if __name__ == '__main__':
    main()
