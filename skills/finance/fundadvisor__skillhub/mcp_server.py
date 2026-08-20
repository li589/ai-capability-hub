#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fund-advisor MCP Server — 基金投资智能顾问
通过 MCP 协议暴露持仓导入/导出、客户管理、组合分析等工具。

使用方式（配置 mcpServers）:
{
  "mcpServers": {
    "fund-advisor": {
      "command": "python",
      "args": ["./mcp_server.py"]
    }
  }
}
"""

from __future__ import annotations
import json
import sys
import os
sys.dont_write_bytecode = True
import re
from pathlib import Path

# 路径初始化
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR / "scripts"))

from fund_advisor_paths import DATA_DIR, load_json_data, load_holdings  # noqa: E402
from analysis.fund_predictor import FundPredictor  # noqa: E402　v7.3

# v8.0 模块（延迟导入以保持启动速度）
def _get_backtest_engine():
    from analysis.backtest_engine import get_backtest_engine
    return get_backtest_engine()

def _get_factor_engine():
    from analysis.factor_engine import get_factor_engine
    return get_factor_engine()

def _get_simulator():
    from analysis.scenario_simulator import get_simulator
    return get_simulator()

# 延迟导入：让工具实际被调用时再加载重的依赖
def _get_importer():
    from client_manager.holdings_importer import HoldingsImporter
    return HoldingsImporter()


# 工具函数实现（同步形式 — FastMCP 会自动包装）




def _validate_file(file_path: str, allowed_exts: tuple = None) -> str | None:
    """验证文件路径有效性，返回 None 表示通过，否则返回错误信息。
    v9.0: 用 Path.resolve() + commonpath 防 ../ 前缀穿越与 DATA_DIR 前缀误判。"""
    from pathlib import Path
    try:
        r = Path(file_path).resolve()
        d = Path(str(DATA_DIR)).resolve()
        common = os.path.commonpath([str(r), str(d)])
        if common != str(d):
            return f"文件不在 DATA_DIR 范围内: {file_path}"
    except (ValueError, OSError):
        return f"文件路径无效: {file_path}"
    if allowed_exts and r.suffix.lower() not in allowed_exts:
        return f"不支持的文件格式，允许: {allowed_exts}"
    return None


def _validate_url(url: str) -> str | None:
    """v9.0: 校验导入 URL 的 scheme 与域名白名单，返回 None 表示通过。"""
    from urllib.parse import urlparse
    try:
        u = urlparse(url)
    except ValueError:
        return f"URL 无效: {url}"
    if u.scheme not in ("http", "https"):
        return f"仅支持 http/https URL: {url}"
    host = (u.netloc or "").lower()
    allowed = ("fund.eastmoney.com", "fund.eastmoney.com.cn", "funddb.cn",
               "danjuanfunds.com", "licai.laocaixinxi.com", "licai.qq.com")
    if host and not any(host == d or host.endswith("." + d) for d in allowed):
        return f"URL 域名不在白名单内: {host}"
    return None


def _to_float(text) -> float:
    """v9.0: 容错数值转换，脏文本返回 0.0 而非抛异常。"""
    try:
        cleaned = re.sub(r"[^\d.]", "", str(text or "0"))
        return float(cleaned) if cleaned else 0.0
    except (ValueError, TypeError):
        return 0.0


def import_holdings_screenshot(image_path: str, client_id: str = "") -> str:
    """从截图OCR识别基金持仓信息。
    支持常见图片格式(.png/.jpg/.jpeg/.bmp)。支持中英文混合识别，自动解析基金代码、名称、份额、成本价。
    适用场景：客户发送了基金持仓页面的手机截图或电脑截图。

    Args:
        image_path: 截图文件的完整路径，如 /path/to/张先生持仓.png
        client_id: 客户姓名或ID（可选），如 "张先生"
    """
    err = _validate_file(image_path, (".png", ".jpg", ".jpeg", ".bmp", ".gif", ".tiff"))
    if err:
        return err
    importer = _get_importer()
    result = importer.import_from_screenshot(image_path, client_id=client_id or None)
    if result['success']:
        items = result['holdings']
        lines = [f"识别到 {len(items)} 条基金持仓:"]
        for h in items:
            lines.append(
                f"  {h.get('fund_code')} {h.get('fund_name', '未知')} "
                f"份额:{h.get('shares', '?')} 成本:{h.get('cost', '?')}"
            )
        if client_id:
            lines.append(f"已保存到客户「{client_id}」的持仓仓库。")
        return '\n'.join(lines)
    return f"识别失败: {'; '.join(result['errors'])}"


def import_holdings_docx(file_path: str, client_id: str = "") -> str:
    """从Word文档(.docx)导入基金持仓信息。
    仅支持 .docx 格式（不支持旧版 .doc）。自动解析文档中的表格和文本段落。
    适用场景：客户提供了Word格式的基金持仓清单。

    Args:
        file_path: Word文档的完整路径，如 /path/to/持仓明细.docx
        client_id: 客户姓名或ID（可选）
    """
    err = _validate_file(file_path, (".docx",))
    if err:
        return err
    importer = _get_importer()
    result = importer.import_from_docx(file_path, client_id=client_id or None)
    if result['success']:
        items = result['holdings']
        lines = [f"从Word文档识别到 {len(items)} 条基金持仓:"]
        for h in items:
            lines.append(
                f"  {h.get('fund_code')} {h.get('fund_name', '未知')} "
                f"份额:{h.get('shares', '?')} 成本:{h.get('cost', '?')}"
            )
        if client_id:
            lines.append(f"已保存到客户「{client_id}」的持仓仓库。")
        return '\n'.join(lines)
    return f"导入失败: {'; '.join(result['errors'])}"


def import_holdings_pdf(file_path: str, client_id: str = "") -> str:
    """从PDF文档导入基金持仓信息。
    支持文本型PDF，扫描版PDF请使用截图导入。支持文本型PDF和含表格的PDF。
    适用场景：客户提供了PDF格式的基金对账单或持仓报告。
    注意：扫描版PDF（图片型）请使用截图导入功能。

    Args:
        file_path: PDF文件的完整路径，如 /path/to/对账单.pdf
        client_id: 客户姓名或ID（可选）
    """
    err = _validate_file(file_path, (".pdf",))
    if err:
        return err
    importer = _get_importer()
    result = importer.import_from_pdf(file_path, client_id=client_id or None)
    if result['success']:
        items = result['holdings']
        lines = [f"从PDF识别到 {len(items)} 条基金持仓:"]
        for h in items:
            lines.append(
                f"  {h.get('fund_code')} {h.get('fund_name', '未知')} "
                f"份额:{h.get('shares', '?')} 成本:{h.get('cost', '?')}"
            )
        if client_id:
            lines.append(f"已保存到客户「{client_id}」的持仓仓库。")
        return '\n'.join(lines)
    return f"导入失败: {'; '.join(result['errors'])}"


def import_holdings_url(url: str, client_id: str = "",
                        username: str = "", password: str = "") -> str:
    """从浏览器链接抓取基金持仓信息。支持天天基金等平台的公开页面，
    也可处理需要登录的平台（提供用户名密码）。
    适用场景：客户提供了基金平台的持仓页面链接。

    Args:
        url: 持仓页面URL，如 https://fund.eastmoney.com/001924.html
        client_id: 客户姓名或ID（可选）
        username: 登录用户名（可选，仅需登录的平台需要）
        password: 登录密码（可选，仅需登录的平台需要）
    """
    # v9.0: URL 沙箱校验（scheme + 域名白名单）
    url_err = _validate_url(url)
    if url_err:
        return url_err
    importer = _get_importer()
    credentials = None
    if username:
        credentials = {"username": username, "password": password}
    result = importer.import_from_url(
        url,
        client_id=client_id or None,
        credentials=credentials
    )
    if result['success']:
        items = result['holdings']
        lines = [f"从链接抓取到 {len(items)} 条基金持仓:"]
        for h in items:
            lines.append(
                f"  {h.get('fund_code')} {h.get('fund_name', '未知')} "
                f"净值:{h.get('current_nav', h.get('estimated_nav', '?'))}"
            )
        if client_id:
            lines.append(f"已保存到客户「{client_id}」的持仓仓库。")
        return '\n'.join(lines)
    return f"抓取失败: {'; '.join(result['errors'])}"


def export_holdings_excel(client_id: str = "", output_path: str = "") -> str:
    """将客户持仓导出为Excel表格（.xlsx），包含格式化的持仓明细和汇总sheet。
    适用场景：需要生成客户持仓报表或打印存档。

    Args:
        client_id: 客户姓名或ID
        output_path: 输出文件路径（可选，默认自动生成到客户目录下）
    """
    if not client_id:
        return "请提供 client_id 参数指定客户。使用 list_clients 查看所有客户。"
    importer = _get_importer()
    holdings = importer.load_client_holdings(client_id)
    if not holdings:
        return f"客户「{client_id}」暂无持仓记录。请先导入持仓数据。"
    try:
        path = importer.export_to_excel(
            holdings, output_path=output_path or None, client_id=client_id
        )
        return (f"Excel文件已生成！\n"
                f"  客户: {client_id}\n"
                f"  持仓数: {len(holdings)}条\n"
                f"  文件路径: {path}")
    except ImportError:
        return "需要安装 openpyxl: pip install openpyxl"
    except Exception as e:
        return f"导出失败: {str(e)}"


def export_holdings_csv(client_id: str = "", output_path: str = "") -> str:
    """将客户持仓导出为CSV文件，方便导入其他系统或Excel打开。
    适用场景：需要将持仓数据导入到其他系统或进行自定义分析。

    Args:
        client_id: 客户姓名或ID
        output_path: 输出文件路径（可选）
    """
    if not client_id:
        return "请提供 client_id 参数指定客户。"
    importer = _get_importer()
    holdings = importer.load_client_holdings(client_id)
    if not holdings:
        return f"客户「{client_id}」暂无持仓记录。请先导入持仓数据。"
    try:
        path = importer.export_to_csv(
            holdings, output_path=output_path or None, client_id=client_id
        )
        return (f"CSV文件已生成！\n"
                f"  客户: {client_id}\n"
                f"  持仓数: {len(holdings)}条\n"
                f"  文件路径: {path}")
    except Exception as e:
        return f"导出失败: {str(e)}"


def list_clients() -> str:
    """列出所有已导入持仓的客户及其概览信息。
    返回每个客户的持仓数量、总市值和最后更新时间。
    """
    importer = _get_importer()
    clients = importer.list_clients()
    if not clients:
        return "暂无客户持仓记录。使用导入工具开始添加客户持仓。"
    lines = ["【客户持仓仓库】"]
    for client_id, info in clients.items():
        count = info.get('holdings_count', 0)
        value = info.get('total_value', 0)
        updated = info.get('last_updated', '')
        lines.append(f"  {client_id}    {count}条    ¥{value:,.2f}    {updated}")
    return '\n'.join(lines)


def get_client_holdings(client_id: str) -> str:
    """查看指定客户的当前持仓详情，包括每只基金的代码、名称、份额、成本、市值和盈亏。

    Args:
        client_id: 客户姓名或ID
    """
    importer = _get_importer()
    holdings = importer.load_client_holdings(client_id)
    if not holdings:
        return f"客户「{client_id}」暂无持仓记录。"
    lines = [f"【{client_id} 的持仓明细】共 {len(holdings)} 条"]
    total_cost = 0
    total_value = 0
    for h in holdings:
        shares = h.get('shares', 0) or 0
        cost = h.get('cost', 0) or 0
        nav = h.get('current_nav', cost)
        market_value = shares * nav
        cost_value = shares * cost
        profit = market_value - cost_value
        profit_pct = (profit / cost_value * 100) if cost_value > 0 else 0
        total_cost += cost_value
        total_value += market_value
        lines.append(
            f"  {h.get('fund_code')} {h.get('fund_name', '未知'):<20s} "
            f"份额:{shares:>10,.0f} 成本:{cost:>8.4f} "
            f"市值:{market_value:>12,.2f} 盈亏:{profit:>+10,.2f} ({profit_pct:>+.1f}%)"
        )
    total_profit = total_value - total_cost
    total_pct = (total_profit / total_cost * 100) if total_cost > 0 else 0
    lines.append("───")
    lines.append(f"  合计: 总成本 ¥{total_cost:,.2f}  总市值 ¥{total_value:,.2f}  "
                 f"总盈亏 ¥{total_profit:+,.2f} ({total_pct:+.1f}%)")
    return '\n'.join(lines)


def get_import_history(client_id: str) -> str:
    """查看指定客户的历史导入记录。包括每次导入的时间、来源和持仓数量。

    Args:
        client_id: 客户姓名或ID
    """
    importer = _get_importer()
    history = importer.get_import_history(client_id)
    if not history:
        return f"客户「{client_id}」暂无导入记录。"
    lines = [f"【{client_id} 的导入历史】共 {len(history)} 次"]
    for record in history[:20]:
        ts = record.get('timestamp', '')
        source = record.get('source', '')
        count = record.get('count', 0)
        lines.append(f"  {ts}  来源:{source}  数量:{count}条")
    return '\n'.join(lines)


def _parse_holdings_rows(rows, header, client_id=None):
    """共享的表格行解析逻辑，Excel/CSV 复用。"""
    from client_manager.holdings_importer import HoldingsImporter
    importer = HoldingsImporter()
    col_map = importer._map_table_columns(header)
    if not col_map or 'fund_code' not in col_map:
        return {'success': False, 'holdings': [], 'errors': [f'未识别到基金代码列（首行: {header[:6]}）']}
    holdings = []
    for row in rows:
        if not row or all(c is None or str(c).strip() == '' for c in row):
            continue
        row_dict = {header[i] if i < len(header) else f'col_{i}': row[i] for i in range(len(row))}
        code_raw = str(row_dict.get(col_map['fund_code'], '') or '')
        code = re.sub(r'\D', '', code_raw)[:6]
        if not code or len(code) < 5:
            continue
        shares_raw = row_dict.get(col_map.get('shares', ''), '0') or '0'
        cost_raw = row_dict.get(col_map.get('cost', ''), '0') or '0'
        holdings.append({
            'fund_code': code.zfill(6),
            'fund_name': str(row_dict.get(col_map.get('fund_name', ''), '') or ''),
            'shares': _to_float(shares_raw),
            'cost': _to_float(cost_raw),
        })
    if not holdings:
        return {'success': False, 'holdings': [], 'errors': ['未解析到任何持仓数据']}
    result = {'success': True, 'holdings': holdings}
    if client_id:
        _get_importer().save_to_repository(client_id, holdings)
    return result


def auto_import_file(file_path: str, client_id: str = "") -> str:
    """智能导入：根据文件扩展名自动选择导入方式。
    支持: .png/.jpg/.jpeg/.bmp/.gif (截图OCR), .docx (Word), .pdf (PDF),
          .xlsx/.xls (Excel), .csv (CSV)

    Args:
        file_path: 文件完整路径
        client_id: 客户姓名或ID（可选）
    """
    # v9.0: 统一沙箱校验（此前 Excel/CSV 绕过 _validate_file）
    allowed_exts = ('.png', '.jpg', '.jpeg', '.bmp', '.gif', '.docx', '.pdf', '.xlsx', '.xls', '.csv')
    err = _validate_file(file_path, allowed_exts)
    if err:
        return err

    ext = Path(file_path).suffix.lower()
    cid = client_id or None

    if ext in ('.png', '.jpg', '.jpeg', '.bmp', '.gif'):
        importer = _get_importer()
        result = importer.import_from_screenshot(file_path, client_id=cid)
        method = "截图OCR识别"
    elif ext == '.docx':
        importer = _get_importer()
        result = importer.import_from_docx(file_path, client_id=cid)
        method = "Word文档导入"
    elif ext == '.pdf':
        importer = _get_importer()
        result = importer.import_from_pdf(file_path, client_id=cid)
        method = "PDF文档导入"
    elif ext in ('.xlsx', '.xls'):
        result = _excel_import(file_path, client_id=cid)
        method = "Excel表格导入"
    elif ext == '.csv':
        result = _csv_import(file_path, client_id=cid)
        method = "CSV表格导入"
    else:
        return f"不支持的文件类型: {ext}。支持的格式: .png/.jpg/.jpeg/.bmp/.gif/.docx/.pdf/.xlsx/.xls/.csv"

    if result.get('success'):
        items = result.get('holdings', [])
        if not isinstance(items, list):
            items = []
        lines = [f"{method}成功，识别到 {len(items)} 条持仓:"]
        for h in items:
            lines.append(
                f"  {h.get('fund_code', h.get('code', ''))} "
                f"{h.get('fund_name', h.get('name', '未知'))}"
            )
        if client_id:
            lines.append(f"已保存到客户「{client_id}」的持仓仓库。")
        return '\n'.join(lines)
    errors = result.get('errors', ['未知错误'])
    return f"{method}失败: {'; '.join(errors)}"


def _excel_import(file_path: str, client_id: str = None) -> dict:
    """Excel 文件导入：复用共享表格解析"""
    result = {'success': False, 'holdings': [], 'errors': []}
    try:
        from openpyxl import load_workbook
        wb = load_workbook(file_path, data_only=True, read_only=True)
        ws = wb.active
        rows = list(ws.iter_rows(values_only=True))
        if not rows:
            result['errors'].append('Excel 文件为空')
            return result
        header = [str(c) if c is not None else '' for c in rows[0]]
        return _parse_holdings_rows(rows[1:], header, client_id=client_id)
    except ImportError:
        result['errors'].append('缺少 openpyxl，请 pip install openpyxl')
    except Exception as e:
        result['errors'].append(f'Excel 解析失败: {e}')
    return result


def _csv_import(file_path: str, client_id: str = None) -> dict:
    """CSV 文件导入（UTF-8 / GBK 自动识别）"""
    result = {'success': False, 'holdings': [], 'errors': []}
    try:
        import csv
        text = None
        for enc in ('utf-8-sig', 'utf-8', 'gbk', 'gb2312'):
            try:
                with open(file_path, 'r', encoding=enc) as f:
                    text = f.read()
                break
            except UnicodeDecodeError:
                continue
        if text is None:
            result['errors'].append('CSV 文件编码不支持（尝试了 utf-8/gbk/gb2312）')
            return result
        import io
        reader = csv.reader(io.StringIO(text))
        rows = [r for r in reader if r]
        if len(rows) < 2:
            result['errors'].append('CSV 文件无数据行')
            return result
        header = [str(c).strip() for c in rows[0]]
        return _parse_holdings_rows(rows[1:], header, client_id=client_id)
    except Exception as e:
        result['errors'].append(f'CSV 解析失败: {e}')
    return result



# ── 基金查询与量化分析 ──────────────────────────────────────────────


def query_fund(fund_code: str) -> str:
    """查询基金详细信息。根据基金代码返回基金名称、类型、基金经理、公司、最新季报重仓股。

    Args:
        fund_code: 6位基金代码，如 001924 或 000858
    """
    code = re.sub(r'\D', '', str(fund_code))[:6].zfill(6)
    fund = _lookup_fund(code)
    if not fund:
        return f"未找到基金代码 {code} 的信息。请确认代码是否正确。"
    lines = [f"【{fund.get('name', code)}】({code})"]
    if fund.get('type'):
        lines.append(f"  类型: {fund['type']}")

    # 反查现任基金经理（fund_managers_distilled）
    mgr = _lookup_manager_by_fund(code)
    if mgr:
        lines.append(f"  基金经理: {mgr.get('name', '')}（{mgr.get('company_name', '')}）")
        if mgr.get('total_scale') not in (None, ''):
            lines.append(f"  经理管理规模: {mgr['total_scale']}亿")

    # 最新季报十大重仓（holdings_database，季度见元数据）
    try:
        rows = load_holdings()
        stocks = [r for r in rows if str(r.get('fund_code', '')).zfill(6) == code]
        if stocks:
            quarter = _holdings_quarter()
            lines.append(f"  {quarter}十大重仓:")
            total_w = 0.0
            for r in stocks[:10]:
                w = r.get('weight') or 0
                total_w += float(w)
                name = r.get('stock_name') or r.get('stock_code')
                lines.append(f"    {r.get('stock_code', '')} {name}  {w}%")
            lines.append(f"    合计占净值: {total_w:.2f}%")
    except Exception:
        pass
    return '\n'.join(lines)


def _lookup_manager_by_fund(code: str) -> dict | None:
    """按基金代码反查现任基金经理"""
    try:
        data = load_json_data('fund_managers_distilled.json')
        for m in data.get('items', data.get('d', [])):
            if isinstance(m, dict) and str(m.get('current_fund_code', '')).zfill(6) == code:
                return m
    except Exception:
        pass
    return None


def _holdings_quarter() -> str:
    """读取持仓库元数据中的季度标识"""
    try:
        path = DATA_DIR / 'holdings_database.json'
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        meta = data.get('m', {}) if isinstance(data, dict) else {}
        q = meta.get('quarter', '')
        return f"{q} " if q else ''
    except Exception:
        return ''


def query_manager(manager_name: str) -> str:
    """查询基金经理档案。返回经理简介、管理规模、代表产品、投资风格和近期观点。

    Args:
        manager_name: 基金经理姓名，如 张坤 或 葛兰
    """
    mgr = _lookup_manager(manager_name.strip())
    if not mgr:
        # 模糊搜索
        mgrs = _search_managers(manager_name.strip())
        if not mgrs:
            return f"未找到基金经理「{manager_name}」的信息。"
        if len(mgrs) > 1:
            names = [m.get('name', '?') for m in mgrs[:5]]
            return f"找到 {len(mgrs)} 位匹配「{manager_name}」的经理：{', '.join(names)}。请指定完整姓名。"
        mgr = mgrs[0]
    lines = [f"【{mgr.get('name', manager_name)}】"]
    for k, label in [('company', '所属公司'), ('tenure', '从业年限'), ('scale', '管理规模'),
                      ('best_return', '任职最佳回报'), ('current_fund', '现任基金')]:
        v = mgr.get(k)
        if v:
            if isinstance(v, list):
                v = ', '.join(str(x) for x in v[:5])
            lines.append(f"  {label}: {v}")
    return '\n'.join(lines)


def _lookup_fund(code: str) -> dict | None:
    """从本地数据查找基金（fund_products 实际列: code/name/type/pinyin/update）"""
    try:
        data = load_json_data('fund_products.json')
        items = data.get('items', data.get('d', []))
        code = str(code).strip().zfill(6)
        for item in items:
            if isinstance(item, dict) and str(item.get('code', '')).zfill(6) == code:
                return {
                    'name': item.get('name', ''),
                    'type': item.get('type', ''),
                    'update': item.get('update', ''),
                }
    except Exception:
        pass
    return None


def _lookup_manager(name: str) -> dict | None:
    """从本地数据精确查找基金经理

    fund_managers_distilled 实际列: manager_id/name/company_name/tenure_days/
    total_scale/best_return/current_fund_code/current_fund_name
    """
    try:
        data = load_json_data('fund_managers_distilled.json')
        managers = data.get('items', data.get('d', []))
        for m in managers:
            if isinstance(m, dict) and m.get('name', '') == name:
                tenure_days = m.get('tenure_days') or 0
                try:
                    tenure = f"{float(tenure_days) / 365:.1f}年"
                except (TypeError, ValueError):
                    tenure = ''
                scale = m.get('total_scale')
                current_fund = m.get('current_fund_name', '')
                if m.get('current_fund_code'):
                    current_fund = f"{current_fund}({m['current_fund_code']})"
                return {
                    'name': m.get('name', ''),
                    'company': m.get('company_name', ''),
                    'tenure': tenure,
                    'scale': f"{scale}亿" if scale not in (None, '') else '',
                    'best_return': f"{m['best_return']}%" if m.get('best_return') not in (None, '') else '',
                    'current_fund': current_fund,
                }
    except Exception:
        pass
    return None


def _search_managers(name: str) -> list:
    """模糊搜索基金经理"""
    results = []
    try:
        data = load_json_data('fund_managers_distilled.json')
        managers = data.get('items', data.get('d', []))
        for m in managers:
            if isinstance(m, dict) and name in m.get('name', ''):
                results.append({'name': m.get('name', '')})
                if len(results) >= 10:
                    break
    except Exception:
        pass
    return results


# ==================== v7.2 新增工具：投顾报告 / 经理对比 ====================


def get_advisor_report(fund_code: str, target_style: str = "") -> str:
    """生成单只基金的综合投顾报告。🧭 (v7.2)

    整合：多源评级聚合（晨星/好买/东财等，带 provenance）、风险调整对比（Sharpe vs 同类）、
    本地最新季报十大重仓穿透、可选风格漂移检测与持仓加权估值（需 akshare）。
    每项结论标注数据来源。

    Args:
        fund_code: 6位基金代码，如 001924
        target_style: 目标风格（成长/价值/均衡），提供时检测风格漂移
    """
    code = re.sub(r'\D', '', str(fund_code))[:6].zfill(6)
    try:
        from analysis.advisor_engine import AdvisorEngine
        # 本地最新季报重仓 → 引擎持仓格式 [{code, ratio, name}]
        current_holdings = [
            {'code': r.get('stock_code', ''), 'ratio': r.get('weight', 0),
             'name': r.get('stock_name', '')}
            for r in load_holdings()
            if str(r.get('fund_code', '')).zfill(6) == code
        ][:10]
        eng = AdvisorEngine()
        rep = eng.generate_advice(code, target_style=target_style,
                                  current_holdings=current_holdings or None)
        lines = [f"🧭 投顾报告 {code}  |  {rep.generated_at}", "=" * 60]
        cr = rep.consensus_rating or {}
        if cr.get('consensus_star'):
            lines.append(f"【多源评级】{cr['consensus_star']}★（{cr.get('source_count', 0)}源）")
        ra = (rep.risk_adjusted or {}).get('compare', {})
        if ra.get('sharpe', {}).get('fund') is not None:
            s = ra['sharpe']
            lines.append(f"【风险调整】夏普 {s.get('fund')} vs 同类中位 {s.get('peer_median')} → {s.get('verdict')}")
        if rep.style_drift:
            d = rep.style_drift
            lines.append(f"【风格漂移】{d.get('drift_level')}（得分{d.get('drift_score')}）→ {d.get('action')}")
        if rep.holdings_valuation and 'weighted_pe' in rep.holdings_valuation:
            hv = rep.holdings_valuation
            lines.append(f"【持仓估值】加权PE {hv['weighted_pe']}（{hv.get('valuation_level')}） PB {hv.get('weighted_pb')}")
        if current_holdings:
            lines.append(f"【本地持仓】已穿透最新季报前 {len(current_holdings)} 大重仓股")
        if rep.advice:
            lines.append("【建议】")
            for a in rep.advice:
                lines.append(f"  · {a}")
        if rep.source_status:
            lines.append("  源状态: " + " ".join(f"{k}:{v}" for k, v in rep.source_status.items()))
        return '\n'.join(lines)
    except Exception as e:
        return f"投顾报告生成失败: {type(e).__name__}: {e}"


def compare_managers(manager_names: str) -> str:
    """对比多位基金经理。⚖️ (v7.2)

    基于全市场经理档案（4,000+ 人）与最新季报重仓数据，对比：
    所属公司、从业年限、管理规模、任职最佳回报、现任基金、前十集中度、前三大重仓股；
    两位经理时给出相似度评分（持仓重叠/年限/规模/公司）。

    Args:
        manager_names: 经理姓名，用逗号/顿号分隔，如 "张坤,葛兰"（至少2位）
    """
    try:
        from analysis.comparison_engine import ComparisonEngine
        names = [n.strip() for n in re.split(r'[,，、;；\s]+', manager_names) if n.strip()]
        if len(names) < 2:
            return "请提供至少2位基金经理姓名，用逗号分隔。"
        eng = ComparisonEngine()
        result = eng.compare_managers(names)
        if result.get('error'):
            return result['error']
        lines = ["⚖️ 基金经理对比", "=" * 60]
        headers = result['headers']
        for row in result['rows']:
            vals = '  |  '.join(str(v) for v in row['values'])
            lines.append(f"{row['metric']}: {vals}")
        lines.append("-" * 60)
        lines.append("经理顺序: " + '  |  '.join(headers[1:]))
        sim = result.get('similarity')
        if sim:
            lines.append(f"相似度: {sim['score']}（{sim['level']}）"
                         + (f" — {'; '.join(sim['details'])}" if sim['details'] else ''))
        return '\n'.join(lines)
    except Exception as e:
        return f"经理对比失败: {type(e).__name__}: {e}"


# ==================== v6.0 新增工具：多源数据/风格定制/持续跟踪/调仓 ====================


def get_fund_multi_source(code: str) -> str:
    """多源基金数据聚合。📊 (v6.0)

    聚合 9 类数据源（akshare/财联社/华尔街见闻/中证指数/晨星/好买/韭圈儿/蛋卷/东方财富）
    返回基金评级、净值、持仓、持有人结构，每项标注数据源 provenance。
    不再限于天天基金/东方财富。

    Args:
        code: 基金代码（如 110022）
    """
    try:
        from data_collection.multi_source import get_provider
        detail = get_provider().get_fund_detail(code)
        lines = [f"📊 {code} 多源数据聚合  |  {detail.get('fetched_at')}", "=" * 60]
        rt = detail.get("ratings", {})
        if rt.get("consensus_star"):
            lines.append(f"【多源评级】{rt['consensus_star']}★ ({rt.get('source_count',0)}源)")
            for src, star in rt.get("source_stars", {}).items():
                lines.append(f"  · {src}: {star}★")
            ss = rt.get("source_status", {})
            lines.append("  源状态: " + " ".join(f"{k}:{v}" for k, v in ss.items()))
        nv = detail.get("nav", {})
        if nv.get("nav"):
            n = nv["nav"]
            lines.append(f"【净值】{n.get('nav')} ({n.get('nav_date')}) 涨跌{n.get('change_pct')}%  源:{nv.get('source')}")
        return "\n".join(lines)
    except Exception as e:
        return f"获取失败: {type(e).__name__}: {e}"


def get_macro_real() -> str:
    """真实宏观经济数据。🌐 (v6.0 替换原模拟数据)

    通过 akshare 获取真实 GDP/CPI/PPI/PMI/M2/LPR 等宏观指标。
    原 macro_analyzer 的硬编码假数据已替换为真实值。

    适用场景："看看当前宏观经济"、"GDP/CPI 多少"
    """
    try:
        from data_collection.multi_source import get_provider
        r = get_provider().get_macro()
        inds = r.get("indicators", {})
        lines = [f"🌐 真实宏观经济  |  {r.get('fetched_at')}", "=" * 50]
        names = {"gdp_yoy": "GDP同比", "cpi_yoy": "CPI同比", "ppi_yoy": "PPI同比",
                 "pmi": "制造业PMI", "m2_yoy": "M2同比", "m1_yoy": "M1同比",
                 "lpr_1y": "LPR1Y", "lpr_5y": "LPR5Y", "social_financing": "社融"}
        for k, label in names.items():
            v = inds.get(k)
            if v:
                lines.append(f"  {label}: {v['value']}  ({v['source']})")
        ss = r.get("source_status", {})
        lines.append("  源: " + " ".join(f"{k}:{v}" for k, v in ss.items()))
        lines.append("=" * 50)
        return "\n".join(lines)
    except Exception as e:
        return f"宏观数据获取失败: {type(e).__name__}: {e}"


def build_style_portfolio(answers: str = "", amount: float = 10.0) -> str:
    """根据自身风格定制投资组合。🎨 (v6.0)

    10 题风格问卷 -> 5 轴风格画像（价值↔成长/大盘↔小盘/行业↔主题/主动↔被动/国内↔海外）
    -> 目标资产配置 + 风格化基金筛选（多源评级排序）。

    Args:
        answers: 10 题答案，逗号分隔(每题0-4)。如 "3,2,1,2,1,2,3,2,2,1"。留空返回问卷题目。
        amount: 投资金额（万元，默认10）
    """
    try:
        from analysis.style_portfolio_builder import StylePortfolioBuilder, format_style_profile, QUESTIONNAIRE
        builder = StylePortfolioBuilder()
        if not answers.strip():
            lines = ["🎨 投资风格问卷（10题，每题选0-4）", "=" * 60]
            for i, q in enumerate(QUESTIONNAIRE, 1):
                opts = " / ".join(f"{j}.{t}" for j, (t, _) in enumerate(q["a"]))
                lines.append(f"{i}. {q['q']}\n   {opts}")
            lines.append("\n调用: build_style_portfolio(answers=\"3,2,1,2,1,2,3,2,2,1\", amount=20)")
            return "\n".join(lines)
        ans = [int(x.strip()) for x in answers.split(",") if x.strip().isdigit()]
        result = builder.build_portfolio(ans, amount_wan=amount)
        profile = builder.build_profile_from_answers(ans)
        lines = [format_style_profile(profile), "",
                 f"【推荐基金】(多源评级排序, 金额{amount}万)"]
        for f in result["recommended_funds"][:6]:
            lines.append(f"  · {f['code']}: {f['star']}★ ({f['source_count']}源)")
        lines.append(f"\n【金额分配】" + "  ".join(f"{k}:{v}万" for k, v in result["amount_allocation"].items()))
        return "\n".join(lines)
    except Exception as e:
        return f"风格组合构建失败: {type(e).__name__}: {e}"


def track_portfolio_returns(client_id: str) -> str:
    """持仓确认后持续跟踪投资收益率。📈 (v6.0)

    客户确认持仓后，多源净值(akshare主/天天基金备)持续跟踪累计收益、年化、
    当前权重。需先用 confirm_baseline 锁定持仓（或自动用现有 holdings）。

    Args:
        client_id: 客户标识
    """
    try:
        from analysis.portfolio_rebalancer import PortfolioRebalancer
        rb = PortfolioRebalancer()
        tracking = rb.track_returns(client_id)
        if "error" in tracking:
            # 自动用现有 holdings 建 baseline
            try:
                from client_manager.holdings_importer import HoldingsImporter
                holdings_raw = HoldingsImporter().get_holdings(client_id)
                holdings = [{"fund_code": h.get("fund_code"), "shares": h.get("shares", 0),
                             "cost": h.get("cost", 0), "purchase_date": h.get("purchase_date", "")}
                            for h in holdings_raw]
                if holdings:
                    rb.confirm_baseline(client_id, holdings)
                    tracking = rb.track_returns(client_id)
            except Exception:
                pass
        if "error" in tracking:
            return f"❌ {tracking['error']}"
        lines = [f"📈 {client_id} 持仓收益跟踪  |  {tracking.get('tracked_at')}", "=" * 60,
                 f"  总市值: {tracking['total_value']:.0f}  总成本: {tracking['total_cost']:.0f}  "
                 f"收益: {tracking['total_profit']:+.0f} ({tracking['total_profit_pct']:+.2f}%)",
                 "  【持仓明细】"]
        for h in tracking.get("holdings", []):
            icon = "🟢" if h["profit_pct"] > 0 else "🔴"
            lines.append(f"  {icon} {h['fund_code']} 份额{h['shares']} 成本{h['cost']} 现价{h['current_nav']}"
                         f"({h['nav_source']})  收益{h['profit_pct']:+.2f}% 年化{h['annual_return']:+.1f}%")
        return "\n".join(lines)
    except Exception as e:
        return f"跟踪失败: {type(e).__name__}: {e}"


def get_rebalance_advice(client_id: str) -> str:
    """漂移+信号调仓建议。📐 (v6.0)

    持仓确认后，基于目标配置漂移(>5%)+量化信号(非仅profit阈值)输出调仓建议：
    减持超配/增持低配/止盈/止损/转换，每项带源引用理由。仅建议不自动执行。

    Args:
        client_id: 客户标识
    """
    try:
        from analysis.portfolio_rebalancer import PortfolioRebalancer, format_rebalance_report
        rb = PortfolioRebalancer()
        report = rb.generate_rebalance_report(client_id)
        return format_rebalance_report(report)
    except Exception as e:
        return f"调仓建议获取失败: {type(e).__name__}: {e}"


def get_fund_ratings(code: str) -> str:
    """多源基金评级聚合。⭐ (v6.0)

    聚合晨星/好买/韭圈儿/雪球/东方财富评级 -> 加权一致星级。
    每源独立标注 provenance，失败源优雅降级。

    Args:
        code: 基金代码
    """
    try:
        from data_collection.multi_source import get_provider
        r = get_provider().get_fund_ratings(code)
        lines = [f"⭐ {code} 多源评级  |  {r.get('fetched_at')}", "=" * 50]
        if r.get("consensus_star"):
            lines.append(f"  一致评级: {r['consensus_star']}★ ({r.get('source_count',0)}源)")
        for src, data in r.get("ratings", {}).items():
            if isinstance(data, dict):
                star = data.get("star") or data.get("rating")
                extras = {k: v for k, v in data.items() if k not in ("source_detail",) and v is not None}
                lines.append(f"  · {src}: star={star} {extras}")
        ss = r.get("source_status", {})
        lines.append("  源状态: " + " ".join(f"{k}:{v}" for k, v in ss.items()))
        lines.append("=" * 50)
        return "\n".join(lines)
    except Exception as e:
        return f"评级获取失败: {type(e).__name__}: {e}"


# ── v7.0 新增工具：健康度/归因/配置/检视/学习 ─────────────────────────

def _now_str() -> str:
    """当前时间字符串（mcp_server 顶层未 import datetime，局部取用）"""
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def run_portfolio_healthcheck(client_id: str) -> dict:
    """组合健康度检查。🩺 (v7.0)

    8 维健康评分（每维 10 分，总分 80）：
    分散度/股债配比/风格匹配/费率/行业集中度/最大回撤/经理稳定性/流动性。
    数据缺失的维度给中性分并标注。返回 {score, grade, dimensions, suggestions}。

    Args:
        client_id: 客户标识（需已有 baseline 或持仓）
    """
    try:
        from analysis.portfolio_rebalancer import PortfolioRebalancer
        rb = PortfolioRebalancer()
        tracking = rb.track_returns(client_id)
        if "error" in tracking:
            # 尝试用现有持仓自动建 baseline（与 track_portfolio_returns 相同策略）
            try:
                from client_manager.holdings_importer import HoldingsImporter
                holdings_raw = HoldingsImporter().get_holdings(client_id)
                holdings = [{"fund_code": h.get("fund_code"), "shares": h.get("shares", 0),
                             "cost": h.get("cost", 0), "purchase_date": h.get("purchase_date", "")}
                            for h in holdings_raw]
                if holdings:
                    rb.confirm_baseline(client_id, holdings)
                    tracking = rb.track_returns(client_id)
            except Exception:
                pass
        if "error" in tracking:
            return {"error": tracking["error"]}
        baseline = rb.load_baseline(client_id) or {}
        holdings = tracking.get("holdings", [])
        n = len(holdings)
        weights = list(tracking.get("current_weights", {}).values())
        dims = []
        # 1. 分散度
        s = 10 if n >= 6 else (8 if n >= 4 else (6 if n == 3 else (4 if n == 2 else 2)))
        dims.append({"维度": "分散度", "score": s, "comment": f"持有 {n} 只基金"})
        # 2. 股债配比（用 baseline 目标配置的股/(股+债) 比例衡量均衡度）
        tgt = baseline.get("target_allocation", {})
        stock, bond = tgt.get("stock"), tgt.get("bond")
        if isinstance(stock, (int, float)) and isinstance(bond, (int, float)) and stock + bond > 0:
            ratio = stock / (stock + bond)
            s = 10 if 0.25 <= ratio <= 0.75 else (7 if 0.15 <= ratio <= 0.85 else 4)
            dims.append({"维度": "股债配比", "score": s, "comment": f"目标股债比 {ratio:.0%}"})
        else:
            dims.append({"维度": "股债配比", "score": 6, "comment": "无目标配置数据，中性分"})
        # 3. 风格匹配
        if baseline.get("target_style"):
            dims.append({"维度": "风格匹配", "score": 8, "comment": f"目标风格: {baseline['target_style']}"})
        else:
            dims.append({"维度": "风格匹配", "score": 6, "comment": "未设定目标风格，中性分"})
        # 4. 费率（本地无费率库，中性分）
        dims.append({"维度": "费率", "score": 7, "comment": "费率数据未接入，中性分"})
        # 5. 行业集中度（用最大单基权重近似）
        max_w = max(weights) if weights else 0
        s = 10 if max_w < 30 else (7 if max_w <= 50 else 4)
        dims.append({"维度": "行业集中度", "score": s, "comment": f"最大单基权重 {max_w:.1f}%"})
        # 6. 最大回撤
        try:
            from analysis.review_engine import ReviewEngine
            from analysis import perf_metrics as pm
            nav_info = ReviewEngine().portfolio_nav_series(client_id, days=120)
            mdd = pm.max_drawdown(nav_info.get("nav_series", []))
            if mdd and not nav_info.get("degraded"):
                v = mdd["mdd"]
                s = 10 if v > -10 else (7 if v > -20 else (4 if v > -30 else 2))
                dims.append({"维度": "最大回撤", "score": s, "comment": f"近120日 {v:.2f}%"})
            else:
                dims.append({"维度": "最大回撤", "score": 6, "comment": "净值历史不可用(降级)，中性分"})
        except Exception:
            dims.append({"维度": "最大回撤", "score": 6, "comment": "计算失败，中性分"})
        # 7. 经理稳定性（本地经理库查得到=稳定信号）
        try:
            mgr_db = load_json_data("fund_managers_distilled.json")
            mgrs = mgr_db.get("managers", mgr_db.get("items", []))
            codes = {h.get("fund_code") for h in holdings}
            hit = sum(1 for m in mgrs if m.get("current_fund_code") in codes)
            s = 8 if codes and hit >= len(codes) * 0.6 else 6
            dims.append({"维度": "经理稳定性", "score": s,
                         "comment": f"{hit}/{len(codes)} 只基金在经理库中可查"})
        except Exception:
            dims.append({"维度": "经理稳定性", "score": 6, "comment": "经理库不可用，中性分"})
        # 8. 流动性（持有货币/短债类或持仓只数适中即视为流动性尚可）
        s = 8 if n >= 2 else 6
        dims.append({"维度": "流动性", "score": s, "comment": "开放式基金默认 T+1~T+3 可赎回"})
        score = sum(d["score"] for d in dims)
        grade = "优秀" if score >= 64 else ("良好" if score >= 56 else ("一般" if score >= 40 else "需改善"))
        suggestions = [f"【{d['维度']}】{d['comment']}" for d in dims if d["score"] <= 6]
        if not suggestions:
            suggestions.append("各维度健康，保持现有配置并按季度检视")
        return {"client_id": client_id, "score": score, "max_score": 80, "grade": grade,
                "dimensions": dims, "suggestions": suggestions,
                "checked_at": _now_str()}
    except Exception as e:
        return {"error": f"健康检查失败: {type(e).__name__}: {e}"}


def get_attribution_analysis(client_id: str, period: str = "1y") -> dict:
    """绩效归因分析。🧮 (v7.0)

    简化归因（配置贡献/选基贡献/时机贡献）+ 风险指标（年化/波动/夏普/回撤/Calmar）。
    净值历史不可用时自动降级并标注。

    Args:
        client_id: 客户标识
        period: 观察窗口 1m/3m/6m/1y（默认 1y）
    """
    try:
        from analysis.review_engine import ReviewEngine
        from analysis import perf_metrics as pm
        eng = ReviewEngine()
        tracking = eng.rebalancer.track_returns(client_id)
        if "error" in tracking:
            return {"error": tracking["error"]}
        days_map = {"1m": 22, "3m": 66, "6m": 125, "1y": 250}
        days = days_map.get(period, 250)
        nav_info = eng.portfolio_nav_series(client_id, days=days)
        series = nav_info.get("nav_series", [])
        metrics = pm.compute_all_metrics(series) if len(series) >= 2 else {}
        attribution = eng._simple_attribution(tracking, nav_info)
        return {"client_id": client_id, "period": period,
                "attribution": attribution,
                "risk_metrics": metrics,
                "degraded": nav_info.get("degraded", False),
                "degraded_note": nav_info.get("note", ""),
                "note": "简化为单组合归因（无基准）：配置=漂移拖累，选基=加权超额，时机=残差"}
    except Exception as e:
        return {"error": f"归因分析失败: {type(e).__name__}: {e}"}


def score_risk_profile(answers: str = "") -> dict:
    """风险承受能力问卷评分。📝 (v7.0)

    10 题问卷（每题 0-4）-> 五轴得分 + 五档风险等级
    （保守型/稳健型/平衡型/成长型/进取型）。

    Args:
        answers: 10 题答案，逗号分隔，如 "2,2,3,3,2,2,1,1,2,2"
    """
    try:
        from analysis.asset_allocator import score_risk_questionnaire
        ans = [int(x.strip()) for x in (answers or "").split(",") if x.strip().lstrip("-").isdigit()]
        result = score_risk_questionnaire(ans)
        if "error" in result:
            result["hint"] = "answers 需为逗号分隔的 10 个 0-4 整数"
        return result
    except Exception as e:
        return {"error": f"问卷评分失败: {type(e).__name__}: {e}"}


def build_allocation_plan(amount: float, risk_level: str = "",
                          horizon_years: float = 3.0, goal: str = "",
                          answers: str = "") -> dict:
    """一站式资产配置方案。🧭 (v7.0)

    问卷或风险等级 -> 战略配置 SAA + 下滑曲线(养老/教育) + 核心卫星 +
    基金槽位建议 + 再平衡规则。纯本地计算，离线可用。

    Args:
        amount: 投资金额（元）
        risk_level: 保守型/稳健型/平衡型/成长型/进取型（留空则用问卷或默认平衡型）
        horizon_years: 投资期限（年）
        goal: 目标场景（养老/教育/购房/现金，可空）
        answers: 10 题问卷答案，逗号分隔（优先于 risk_level）
    """
    try:
        from analysis.asset_allocator import build_allocation_plan as _build
        ans = [int(x.strip()) for x in (answers or "").split(",") if x.strip().lstrip("-").isdigit()]
        return _build(amount, answers=ans or None, risk_level=risk_level,
                      horizon_years=horizon_years, goal=goal)
    except Exception as e:
        return {"error": f"配置方案生成失败: {type(e).__name__}: {e}"}


def plan_dca_investment(monthly_amount: float, risk_level: str = "",
                        horizon_years: float = 3.0, goal: str = "",
                        answers: str = "") -> dict:
    """定投规划器。📆 (v7.1)

    每月定投金额 -> 资产类别拆分(含核心-卫星) + 到期三档情景测算
    (悲观/中性/乐观) + 止盈目标与检视频率建议。纯本地计算，离线可用。

    Args:
        monthly_amount: 每月定投金额（元）
        risk_level: 保守型/稳健型/平衡型/成长型/进取型（留空则用问卷或默认平衡型）
        horizon_years: 定投年限
        goal: 目标场景（养老/教育/购房/现金，可空）
        answers: 10 题问卷答案，逗号分隔（优先于 risk_level）
    """
    try:
        from analysis.dca_planner import plan_dca
        ans = [int(x.strip()) for x in (answers or "").split(",") if x.strip().lstrip("-").isdigit()]
        return plan_dca(monthly_amount, answers=ans or None, risk_level=risk_level,
                        horizon_years=horizon_years, goal=goal)
    except Exception as e:
        return {"error": f"定投规划失败: {type(e).__name__}: {e}"}


def estimate_rebalance_cost(sells: str = "", buys: str = "",
                            annual_excess_return: float = 0.0) -> dict:
    """调仓成本测算器。💰 (v7.1)

    换仓前估算摩擦成本：赎回费阶梯(持有<7天1.5%惩罚性费率) + 申购费(默认1折)，
    并给出回本周期——新基金需多跑赢多少才值得换。

    Args:
        sells: 卖出明细，分号分隔，每项 "名称,金额,持有天数[,基金类型]"，
               如 "A基金,50000,200,混合型;B基金,30000,5"
        buys: 买入明细，分号分隔，每项 "名称,金额"，如 "C基金,80000"
        annual_excess_return: 新基金相对旧基金预期年化超额收益 %（可选，>0 时算回本周期）
    """
    try:
        from analysis.fee_calculator import estimate_rebalance_cost as _est, breakeven_months
        sell_list = []
        for item in (sells or "").split(";"):
            parts = [p.strip() for p in item.split(",") if p.strip()]
            if len(parts) >= 3:
                sell_list.append({"name": parts[0], "amount": float(parts[1]),
                                  "holding_days": int(float(parts[2])),
                                  "fund_type": parts[3] if len(parts) > 3 else "混合型"})
        buy_list = []
        for item in (buys or "").split(";"):
            parts = [p.strip() for p in item.split(",") if p.strip()]
            if len(parts) >= 2:
                buy_list.append({"name": parts[0], "amount": float(parts[1])})
        if not sell_list and not buy_list:
            return {"error": "sells/buys 至少提供一个",
                    "hint": "sells 格式: 'A基金,50000,200,混合型;B基金,30000,5'"}
        result = _est(sell_list, buy_list)
        if "error" not in result and annual_excess_return != 0:
            result["breakeven"] = breakeven_months(result["cost_pct"], annual_excess_return)
        return result
    except Exception as e:
        return {"error": f"成本测算失败: {type(e).__name__}: {e}"}


def get_portfolio_metrics(client_id: str) -> dict:
    """组合业绩指标。📊 (v7.0)

    拼组合净值序列（baseline 份额加权），计算总收益/年化/波动/夏普/
    Sortino/最大回撤/Calmar。净值历史不可用时降级为成本常数序列并标注。

    Args:
        client_id: 客户标识
    """
    try:
        from analysis.review_engine import ReviewEngine
        from analysis import perf_metrics as pm
        eng = ReviewEngine()
        nav_info = eng.portfolio_nav_series(client_id, days=250)
        series = nav_info.get("nav_series", [])
        if len(series) < 2:
            return {"error": nav_info.get("note") or "净值序列不足，无法计算指标",
                    "degraded": nav_info.get("degraded", True)}
        metrics = pm.compute_all_metrics(series)
        metrics["client_id"] = client_id
        metrics["degraded"] = nav_info.get("degraded", False)
        metrics["degraded_note"] = nav_info.get("note", "")
        metrics["window_days"] = len(series)
        return metrics
    except Exception as e:
        return {"error": f"组合指标计算失败: {type(e).__name__}: {e}"}


def generate_review_report(client_id: str, period: str = "weekly") -> str:
    """生成投后检视报告。📋 (v7.0)

    周度：六维 Dashboard + 健康灯号 + 本周要点；
    月度：表现表 + 归因汇总 + 告警汇总 + 下月建议。输出 markdown 文本。

    Args:
        client_id: 客户标识
        period: weekly（默认）或 monthly
    """
    try:
        from analysis.review_engine import ReviewEngine, format_review
        eng = ReviewEngine()
        if period == "monthly":
            return format_review(eng.monthly_review(client_id))
        return format_review(eng.weekly_review(client_id))
    except Exception as e:
        return f"检视报告生成失败: {type(e).__name__}: {e}"


def log_advice(client_id: str, kind: str, target: str, action: str,
               reasons: str = "", confidence: float = 0.6) -> dict:
    """记录一条投顾建议（学习闭环第一步）。🧠 (v7.0)

    建议落盘到 data/learning/advice_log.jsonl，30 天后可回填实际表现，
    用于命中率统计、参数校准与规则库进化。

    Args:
        client_id: 客户标识
        kind: 建议类型 rebalance/fund_pick/risk_alert/other
        target: 标的基金代码
        action: 建议动作（增持/减持/减持止盈/评估止损/替换/持有等）
        reasons: 理由，多条用分号分隔
        confidence: 置信度 0-1（默认 0.6）
    """
    try:
        from learning import LearningEngine
        reason_list = [r.strip() for r in (reasons or "").replace("；", ";").split(";") if r.strip()]
        le = LearningEngine()
        advice_id = le.log_advice(client_id, kind, target, action, reason_list,
                                  confidence=confidence)
        return {"advice_id": advice_id, "logged": True,
                "note": f"建议已记录，{30} 天后可 record_outcome 回填或由 auto_evaluate_pending 自动评估"}
    except Exception as e:
        return {"error": f"建议记录失败: {type(e).__name__}: {e}"}


def get_learning_report() -> dict:
    """自学习报告。📈 (v7.0)

    汇总：建议样本量/整体命中率/分组统计/当前校准参数/规则库启用情况/最近建议。
    学习闭环：记录建议→事后回填→统计命中→校准参数→更新规则库→下次建议用新参数。
    """
    try:
        from learning import LearningEngine
        return LearningEngine().get_learning_report()
    except Exception as e:
        return {"error": f"学习报告生成失败: {type(e).__name__}: {e}"}


# ── FastMCP 装配 ────────────────────────────────────────────────────
# ==================== v7.3 新增工具：基金/组合趋势预测 ====================

def predict_fund_trend(fund_code: str, periods: str = "week,month,quarter") -> str:
    """预测单个基金未来涨跌趋势。📈 (v7.3)

    Args:
        fund_code: 基金代码（如 000858）
        periods: 预测周期，逗号分隔（week/month/quarter），默认全部

    Returns:
        包含因子分析、各周期方向、置信度、蒙特卡洛收益区间的预测报告。
    """
    try:
        p = FundPredictor()
        period_list = [x.strip() for x in periods.split(",") if x.strip()]
        result = p.predict_fund(fund_code, periods=period_list)
        return p.format_prediction(result)
    except Exception as e:
        return f"预测失败: {type(e).__name__}: {e}"


def predict_portfolio_trend(holdings_json: str) -> str:
    """预测投资组合整体涨跌趋势。📊 (v7.3)

    Args:
        holdings_json: JSON字符串，格式 [{"fund_code":"000858","weight":0.4,"fund_type":"混合型"},...]

    Returns:
        组合方向、加权评分、VaR/CVaR、各成分基金预测。
    """
    try:
        holdings = json.loads(holdings_json)
        p = FundPredictor()
        result = p.predict_portfolio(holdings)
        return p.format_portfolio_prediction(result)
    except Exception as e:
        return f"组合预测失败: {type(e).__name__}: {e}"


# ── v8.0 新工具：回测 / 压力测试 / 因子分析 / 情景模拟 ──────────────

def run_backtest(holdings_json: str = "", start_date: str = "",
                 end_date: str = "", rebalance_rule: str = "quarterly",
                 benchmark: str = "000300") -> str:
    """Run portfolio backtest. (v8.0)"""
    try:
        holdings = json.loads(holdings_json) if holdings_json else []
        if not holdings:
            return "请提供持仓数据（holdings_json参数）"
        engine = _get_backtest_engine()
        result = engine.run_portfolio_backtest(
            holdings, start_date or "2024-01-01", end_date or "2026-01-01",
            rebalance_rule=rebalance_rule, benchmark_code=benchmark,
        )
        from analysis.backtest_engine import format_backtest_report
        return format_backtest_report(result)
    except Exception as e:
        return f"回测失败: {type(e).__name__}: {e}"


def stress_test_portfolio(holdings_json: str = "", client_id: str = "",
                           scenarios: str = "") -> str:
    """Run portfolio stress test. (v8.0)"""
    try:
        holdings = []
        if holdings_json:
            holdings = json.loads(holdings_json)
        elif client_id:
            cdata = load_json_data(f"clients/{client_id}/holdings.json")
            holdings = cdata if isinstance(cdata, list) else cdata.get("holdings", [])
        if not holdings:
            return "请提供持仓数据"
        sc_list = [s.strip() for s in scenarios.split(",") if s.strip()] if scenarios else None
        sim = _get_simulator()
        result = sim.run_scenarios(holdings, sc_list)
        lines = ["=" * 60, "  压力测试报告", "=" * 60, ""]
        for s in result.get("scenarios", []):
            lines.append(f"  {s.get('scenario', '')}: 损失 {s.get('total_impact_pct', 0):+.2f}% ({s.get('severity', '')})")
        if result.get("worst_case"):
            wc = result["worst_case"]
            lines.append(f"\n  最坏情景: {wc.get('scenario', '')} 损失 {wc.get('total_impact_pct', 0):+.2f}%")
        return "\n".join(lines)
    except Exception as e:
        return f"压力测试失败: {type(e).__name__}: {e}"


def analyze_factor_exposures(fund_code: str) -> str:
    """Analyze fund factor exposures. (v8.0)"""
    try:
        engine = _get_factor_engine()
        result = engine.compute_factor_exposures(fund_code)
        lines = [
            f"因子分析 — {result['fund_name']} ({fund_code})",
            f"类型: {result['fund_type']}  综合评分: {result['composite_score']:.1f}  {result['grade']}",
            "", "因子暴露:",
        ]
        for factor, score in result["factors"].items():
            bar = "█" * int(score * 20) + "░" * (20 - int(score * 20))
            name = {"momentum": "动量", "volatility": "波动率", "quality": "质量",
                    "value": "价值", "sentiment": "情绪", "macro_sensitivity": "宏观"}.get(factor, factor)
            lines.append(f"  {name:6s} [{bar}] {score:.3f}")
        return "\n".join(lines)
    except Exception as e:
        return f"因子分析失败: {type(e).__name__}: {e}"


def simulate_scenario(holdings_json: str, scenario_type: str = "market_crash",
                       params_json: str = "") -> str:
    """What-If scenario simulation. (v8.0)"""
    try:
        holdings = json.loads(holdings_json)
        sim = _get_simulator()
        if scenario_type == "market_crash":
            p = json.loads(params_json) if params_json else {}
            result = sim.market_shock(holdings,
                                      equity_shock_pct=p.get("equity_shock", -20),
                                      bond_shock_pct=p.get("bond_shock", 2))
        elif scenario_type == "rate_hike":
            p = json.loads(params_json) if params_json else {}
            result = sim.rate_change(holdings, rate_delta_bps=p.get("rate_bps", 100))
        elif scenario_type == "inflation_impact":
            p = json.loads(params_json) if params_json else {}
            result = sim.inflation_impact(holdings,
                                          inflation_rate_pct=p.get("inflation", 3),
                                          years=p.get("years", 1))
        elif scenario_type == "fund_swap":
            p = json.loads(params_json) if params_json else {}
            result = sim.fund_swap(holdings,
                                   sell_code=p.get("sell", ""),
                                   buy_code=p.get("buy", ""))
        else:
            return f"未知情景类型: {scenario_type}"
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"情景模拟失败: {type(e).__name__}: {e}"


# ==================== v10.0 新增工具：经理对话 / 跟仓 / 心理画像 / 定制报告 ====================


def chat_with_manager(manager_name: str, question: str, fund_code: str = "") -> str:
    """与基金经理「对话」。🗣️ (v10.0)

    基于蒸馏的人设卡（履历/风格/投资范围/季报观点/新闻采访），以经理口吻回答客户经理的问题。
    配置 DEEPSEEK_API_KEY（.env）时启用 LLM 观点蒸馏；离线自动降级为规则+真实数据回答。
    所有回答自带免责声明（观点来自公开报告/新闻整理，非经理本人实时言论）。

    Args:
        manager_name: 基金经理姓名，如 张坤
        question: 想向经理提问的内容，如 "你对后市怎么看？"
        fund_code: 基金代码（可选，同名经理多只产品时用于定位）
    """
    try:
        from analysis.manager_dialogue import ManagerDialogue
        dlg = ManagerDialogue()
        return dlg.chat(manager_name=manager_name.strip() or None,
                        fund_code=fund_code.strip() or None,
                        question=question)
    except Exception as e:
        return f"经理对话失败: {type(e).__name__}: {e}"


def get_manager_persona(manager_name: str, fund_code: str = "") -> str:
    """生成基金经理「人设卡」。🪪 (v10.0)

    汇总经理履历、投资风格、股票池、合同投资范围（投资目标/投资范围/基准）、
    最新季报观点、近期新闻采访与风险提示，供客户经理快速了解一位经理。

    Args:
        manager_name: 基金经理姓名，如 葛兰
        fund_code: 基金代码（可选，用于定位同名经理）
    """
    try:
        from analysis.manager_persona import ManagerPersona
        eng = ManagerPersona()
        persona = eng.build(manager_name=manager_name.strip() or None,
                            fund_code=fund_code.strip() or None)
        if not persona:
            return f"未找到基金经理「{manager_name}」。请确认姓名或先 update_data.py full 重建数据。"
        return eng.format_persona(persona)
    except Exception as e:
        return f"人设卡生成失败: {type(e).__name__}: {e}"


def get_manager_news(manager_name: str, limit: int = 5) -> str:
    """查询基金经理近期新闻/采访/公告。📰 (v10.0)

    来源：东方财富经理档案页 + 天天基金公告（需先运行 manager_news_collector.py 采集）。

    Args:
        manager_name: 基金经理姓名
        limit: 返回条数（默认5）
    """
    try:
        from fund_advisor_paths import load_json_data
        data = load_json_data('manager_news.json')
        news = [n for n in data.get('news', [])
                if n.get('manager_name') == manager_name.strip()]
        if not news:
            return (f"暂无「{manager_name}」的新闻记录。"
                    f"（提示：运行 python scripts/data_collection/manager_news_collector.py "
                    f"--names {manager_name} 采集）")
        lines = [f"【{manager_name}】近期新闻/采访（{len(news)}条）"]
        for n in news[:limit]:
            lines.append(f"  [{n.get('type', '新闻')}] {n.get('title', '')}"
                         f"（{n.get('date') or n.get('source', '')}）")
        return '\n'.join(lines)
    except FileNotFoundError:
        return ("经理新闻数据未采集。运行 python scripts/data_collection/"
                "manager_news_collector.py 采集后再查询。")
    except Exception as e:
        return f"新闻查询失败: {type(e).__name__}: {e}"


def compare_holdings_change(fund_code: str, q1: str = "", q2: str = "") -> str:
    """对比基金两个季度的十大重仓变动。📉 (v10.0)

    展示新增/剔除/加仓/减仓的股票与权重变化（跟仓核心能力）。
    历史快照自 v10.0 起积累（holdings_history/），首个季度为基线、次季起可对比。

    Args:
        fund_code: 6位基金代码
        q1: 起始季度，如 2026Q1（缺省=次新季度）
        q2: 结束季度，如 2026Q2（缺省=最新季度）
    """
    code = re.sub(r'\D', '', str(fund_code))[:6].zfill(6)
    try:
        from analysis.manager_follower import ManagerFollower
        follower = ManagerFollower()
        diff = follower.diff_fund_holdings(code, q1=q1.strip() or None,
                                           q2=q2.strip() or None)
        if diff.get('error'):
            return f"基金 {code}: {diff.get('message', diff['error'])}"
        lines = [f"📉 持仓变动对比 {diff['quarters'][0]} → {diff['quarters'][1]}（{code}）"]
        s = diff['summary']
        lines.append(f"  新增 {s['added_count']} | 剔除 {s['removed_count']} | "
                     f"加仓 {s['increased_count']} | 减仓 {s['decreased_count']} | "
                     f"维持 {s['kept_count']} | 换手率 {s['turnover']:.0%}")
        for tag, items in (('新增', diff['added']), ('剔除', diff['removed']),
                           ('加仓', diff['increased']), ('减仓', diff['decreased'])):
            if items:
                lines.append(f"  【{tag}】")
                for it in items[:5]:
                    if tag == '新增':
                        lines.append(f"    {it['stock_name']}({it['stock_code']}) {it['weight']}%")
                    elif tag == '剔除':
                        lines.append(f"    {it['stock_name']}({it['stock_code']}) 原{it['prev_weight']}%")
                    else:
                        lines.append(f"    {it['stock_name']}({it['stock_code']}) "
                                     f"{it['prev_weight']}% → {it['weight']}% "
                                     f"({it['change']:+.2f})")
        return '\n'.join(lines)
    except Exception as e:
        return f"持仓变动对比失败: {type(e).__name__}: {e}"


def build_mirror_portfolio(fund_code: str, mode: str = "weighted",
                           total_amount: float = 100000) -> str:
    """构建基金「镜像组合」（跟仓方案）。🪞 (v10.0)

    按最新季报十大重仓生成可执行的跟仓组合：加权（按披露权重）或等权两种模式，
    输出每只股票的权重、金额分解、集中度指标与合规风险提示。

    Args:
        fund_code: 6位基金代码
        mode: 加权方式 weighted（按披露权重）/ equal（等权）
        total_amount: 拟跟仓总金额（元，默认10万）
    """
    code = re.sub(r'\D', '', str(fund_code))[:6].zfill(6)
    try:
        from analysis.manager_follower import ManagerFollower
        follower = ManagerFollower()
        pf = follower.build_mirror_portfolio(code, mode=mode,
                                             total_amount=total_amount)
        if pf.get('error'):
            return f"基金 {code}: {pf.get('message', pf['error'])}"
        lines = [f"🪞 镜像组合（{pf['fund_name']} {code}，{pf['quarter']}季报，"
                 f"{'按披露权重' if mode == 'weighted' else '等权'}）"]
        lines.append(f"  经理: {pf.get('manager_name', '')}")
        for p in pf['positions']:
            lines.append(f"    {p['stock_name']}({p['stock_code']}) "
                         f"{p['mirror_weight']:.2f}% ≈ ¥{p['amount_breakdown']:,.0f}")
        c = pf['concentration']
        lines.append(f"  集中度: 第一大 {c['top1']}% | 前三大 {c['top3']}% | "
                     f"前五大 {c['top5']}% | 未覆盖(债/现金) {pf['cash_ratio']}%")
        for w in pf['warnings']:
            lines.append(f"  ⚠️ {w}")
        lines.append(f"  {pf['disclaimer']}")
        return '\n'.join(lines)
    except Exception as e:
        return f"镜像组合构建失败: {type(e).__name__}: {e}"


def track_mirror_portfolio(fund_code: str, days: int = 30) -> str:
    """跟踪镜像组合表现。📈 (v10.0)

    以基金净值为近似给出区间收益，并尝试用重仓股当日行情估算当日涨跌（best effort）。

    Args:
        fund_code: 6位基金代码
        days: 回看天数（默认30）
    """
    code = re.sub(r'\D', '', str(fund_code))[:6].zfill(6)
    try:
        from analysis.manager_follower import ManagerFollower
        follower = ManagerFollower()
        r = follower.track_mirror_performance(code, days=max(1, min(int(days), 365)))
        if r.get('error'):
            return f"基金 {code}: {r.get('message', r['error'])}"
        lines = [f"📈 镜像组合跟踪 {r['fund_name']}（{code}）"]
        lines.append(f"  区间: {r['period']}")
        nav = r.get('fund_nav_return_pct')
        if nav is not None:
            marker = '🟢' if nav >= 0 else '🔴'
            lines.append(f"  基金净值区间收益（近似）: {marker} {nav:+.2f}%")
        else:
            lines.append("  净值区间收益: 暂无净值序列（可运行 update_data.py 后重试）")
        day = r.get('day_change_estimate_pct')
        if day is not None:
            lines.append(f"  今日镜像组合估算: {day:+.2f}%（基于 {r.get('day_change_quotes_used', 0)} 只重仓股行情）")
        lines.append(f"  说明: {r.get('note', '')}")
        if r.get('degraded'):
            lines.append("  （已降级：无净值也无行情数据）")
        return '\n'.join(lines)
    except Exception as e:
        return f"镜像组合跟踪失败: {type(e).__name__}: {e}"


def get_follow_signals(fund_codes: str = "") -> str:
    """获取跟仓信号。🚨 (v10.0)

    汇总关注基金（或全部有持仓数据的基金）的：持仓季度变动信号（含置信度）、
    基金经理变动告警（manager_changes.json 存在时）。按严重度排序。

    Args:
        fund_codes: 关注的基金代码，逗号分隔（缺省=全部）
    """
    try:
        from analysis.manager_follower import ManagerFollower
        follower = ManagerFollower()
        codes = [c.strip() for c in fund_codes.split(',') if c.strip()] or None
        result = follower.get_follow_signals(fund_codes=codes)
        sigs = result['signals']
        meta = result['meta']
        if not sigs:
            return f"暂无跟仓信号（季度 {meta.get('quarter', '?')}，历史快照 {meta.get('history_quarters')}）"
        level_icon = {'high': '🔴', 'medium': '🟠', 'low': '🟡', 'info': '⚪'}
        lines = [f"🚨 跟仓信号（{meta.get('quarter', '?')}季度，共{len(sigs)}条）"]
        for s in sigs:
            lines.append(f"  {level_icon.get(s.get('level'), '⚪')} "
                         f"{s.get('fund_name', s.get('fund_code'))} "
                         f"[{s.get('confidence', '')}] {s.get('message', '')[:120]}")
            if s.get('manager_change'):
                lines.append(f"      └ 经理变动: {s['manager_change'].get('detail', '')}")
        lines.append(f"  {result['disclaimer']}")
        return '\n'.join(lines)
    except Exception as e:
        return f"跟仓信号获取失败: {type(e).__name__}: {e}"


def assess_client_profile(client_id: str, answers: str = "") -> str:
    """评估客户行为偏差画像（心理+投资风格）。🧠 (v10.0)

    基于 10 题行为问卷（可选）与情绪记录/持仓导入历史，输出 6 个偏差维度分
    （损失厌恶/处置效应/过度自信/从众追涨/频繁交易/短视）、投资者心理类型与沟通策略。

    Args:
        client_id: 客户ID（姓名或编号）
        answers: 行为问卷答案 JSON 字符串，如 '{"q1":0,"q2":2,"q3":1}'（缺省读取已保存的）
    """
    try:
        import json as _json
        from client_manager.behavioral_profile import BehavioralBiasEngine
        eng = BehavioralBiasEngine()
        parsed = None
        if answers.strip():
            try:
                parsed = _json.loads(answers)
            except _json.JSONDecodeError:
                return ("问卷答案格式错误：请传 JSON 对象，如 "
                        "'{\"q1\":0,\"q2\":2}'（值为选项下标 0-3）。")
        assessment = eng.assess(client_id=client_id, answers=parsed)
        if parsed:
            eng.save_answers(client_id, parsed)
        return eng.format_report(assessment)
    except Exception as e:
        return f"行为画像评估失败: {type(e).__name__}: {e}"


def get_client_communication_guide(client_id: str) -> str:
    """获取客户的沟通策略建议。💬 (v10.0)

    已评估行为画像的客户：返回心理类型、语气要点、风险提示频率与预警阈值建议，
    供客户经理把控客户心理与投资风格。

    Args:
        client_id: 客户ID
    """
    try:
        from client_manager.user_profile_manager import UserProfileManager
        mgr = UserProfileManager()
        return mgr.get_behavioral_summary(client_id)
    except Exception as e:
        return f"沟通策略获取失败: {type(e).__name__}: {e}"


def generate_custom_report(client_id: str = "", report_type: str = "weekly",
                           modules: str = "", template: str = "standard") -> str:
    """生成定制报告（模块自由组合+模板）。📄 (v10.0)

    内容模块可选：news(财经要闻)/holdings(持仓业绩)/manager_views(经理观点)/
    psychology(客户心理)/follow(跟仓信号)/allocation(配置建议)/outlook(市场展望)/risk(风险提示)。
    模板：standard / concise(精简) / professional(专业)。

    Args:
        client_id: 客户ID
        report_type: daily/weekly/biweekly/monthly/quarterly
        modules: 模块列表，逗号分隔（缺省用该报告类型默认组合）
        template: standard/concise/professional
    """
    try:
        from client_manager.report_generator import ReportGenerator
        gen = ReportGenerator()
        mods = [m.strip() for m in modules.split(',') if m.strip()] or None
        content = gen.generate_report(user_id=client_id or None,
                                      report_type=report_type.strip() or 'weekly',
                                      modules=mods,
                                      template=template.strip() or 'standard')
        path = gen.save_report(client_id or 'general', report_type.strip() or 'weekly',
                               content=content, modules=mods,
                               template=template.strip() or 'standard')
        return f"报告已生成并保存: {path}\n\n{content}"
    except Exception as e:
        return f"定制报告生成失败: {type(e).__name__}: {e}"


def generate_batch_reports(client_ids: str = "", report_type: str = "weekly") -> str:
    """批量生成多个客户的定期报告（客户经理一键出报告）。📚 (v10.0)

    按各客户在 report_subscriptions.json 中的订阅配置生成（未订阅的客户使用默认配置）。

    Args:
        client_ids: 客户ID列表，逗号分隔（缺省=全部已订阅客户）
        report_type: 报告频率（缺省 weekly）
    """
    try:
        from client_manager.report_scheduler import ReportScheduler
        sched = ReportScheduler()
        if client_ids.strip():
            results = [sched.generate_one(c.strip(), report_type=report_type.strip() or None)
                       for c in client_ids.split(',') if c.strip()]
            ok = [r for r in results if r.get('ok')]
            total = len(results)
        else:
            summary = sched.generate_all()
            results, ok = summary['results'], [r for r in summary['results'] if r.get('ok')]
            total = summary['total']
        lines = [f"📚 批量报告生成完成: 成功 {len(ok)}/{total}"]
        for r in results:
            if r.get('ok'):
                lines.append(f"  ✅ {r['client_id']}（{r['report_type']}）→ {r['path']}")
            else:
                lines.append(f"  ❌ {r.get('client_id')}: {r.get('error', '未知错误')}")
        return '\n'.join(lines)
    except Exception as e:
        return f"批量报告生成失败: {type(e).__name__}: {e}"


def chat_with_client(client_id: str, message: str) -> str:
    """与客户对话（客户经理助手入口）。💬 (v10.0)

    复用本地对话引擎（17 类意图识别+情感回复），并叠加行为画像心理感知层
    （已评估画像的客户自动附加个性化沟通提示）。

    Args:
        client_id: 客户ID
        message: 客户的消息/问题
    """
    try:
        from client_manager.conversation_engine import ClientManager
        cm = ClientManager()
        return cm.chat(client_id, message)
    except Exception as e:
        return f"客户对话失败: {type(e).__name__}: {e}"


# ── FastMCP 装配 ────────────────────────────────────────────────────
try:
    from mcp.server.fastmcp import FastMCP
    _mcp_available = True
except ImportError:
    _mcp_available = False

if _mcp_available:
    server = FastMCP("fund-advisor")

    # 注册所有工具
    server.add_tool(import_holdings_screenshot, name="import_holdings_screenshot",
                    description=import_holdings_screenshot.__doc__)
    server.add_tool(import_holdings_docx, name="import_holdings_docx",
                    description=import_holdings_docx.__doc__)
    server.add_tool(import_holdings_pdf, name="import_holdings_pdf",
                    description=import_holdings_pdf.__doc__)
    server.add_tool(import_holdings_url, name="import_holdings_url",
                    description=import_holdings_url.__doc__)
    server.add_tool(export_holdings_excel, name="export_holdings_excel",
                    description=export_holdings_excel.__doc__)
    server.add_tool(export_holdings_csv, name="export_holdings_csv",
                    description=export_holdings_csv.__doc__)
    server.add_tool(list_clients, name="list_clients",
                    description=list_clients.__doc__)
    server.add_tool(get_client_holdings, name="get_client_holdings",
                    description=get_client_holdings.__doc__)
    server.add_tool(get_import_history, name="get_import_history",
                    description=get_import_history.__doc__)
    server.add_tool(auto_import_file, name="auto_import_file",
                    description=auto_import_file.__doc__)
    server.add_tool(query_fund, name="query_fund",
                    description=query_fund.__doc__)
    server.add_tool(query_manager, name="query_manager",
                    description=query_manager.__doc__)
    # v7.2 新增 2 工具（投顾报告/经理对比）
    server.add_tool(get_advisor_report, name="get_advisor_report",
                    description=get_advisor_report.__doc__)
    server.add_tool(compare_managers, name="compare_managers",
                    description=compare_managers.__doc__)
    # v7.3 新增 2 工具（基金趋势预测/组合预测）
    server.add_tool(predict_fund_trend, name="predict_fund_trend",
                    description=predict_fund_trend.__doc__)
    server.add_tool(predict_portfolio_trend, name="predict_portfolio_trend",
                    description=predict_portfolio_trend.__doc__)
    # v6.0 新增 6 工具（多源数据/风格定制/持续跟踪/调仓）
    server.add_tool(get_fund_multi_source, name="get_fund_multi_source",
                    description=get_fund_multi_source.__doc__)
    server.add_tool(get_macro_real, name="get_macro_real",
                    description=get_macro_real.__doc__)
    server.add_tool(build_style_portfolio, name="build_style_portfolio",
                    description=build_style_portfolio.__doc__)
    server.add_tool(track_portfolio_returns, name="track_portfolio_returns",
                    description=track_portfolio_returns.__doc__)
    server.add_tool(get_rebalance_advice, name="get_rebalance_advice",
                    description=get_rebalance_advice.__doc__)
    server.add_tool(get_fund_ratings, name="get_fund_ratings",
                    description=get_fund_ratings.__doc__)
    # v7.0 新增 8 工具（健康度/归因/风险问卷/配置方案/组合指标/检视报告/学习闭环）
    server.add_tool(run_portfolio_healthcheck, name="run_portfolio_healthcheck",
                    description=run_portfolio_healthcheck.__doc__)
    server.add_tool(get_attribution_analysis, name="get_attribution_analysis",
                    description=get_attribution_analysis.__doc__)
    server.add_tool(score_risk_profile, name="score_risk_profile",
                    description=score_risk_profile.__doc__)
    server.add_tool(build_allocation_plan, name="build_allocation_plan",
                    description=build_allocation_plan.__doc__)
    server.add_tool(get_portfolio_metrics, name="get_portfolio_metrics",
                    description=get_portfolio_metrics.__doc__)
    server.add_tool(generate_review_report, name="generate_review_report",
                    description=generate_review_report.__doc__)
    server.add_tool(log_advice, name="log_advice",
                    description=log_advice.__doc__)
    server.add_tool(get_learning_report, name="get_learning_report",
                    description=get_learning_report.__doc__)

    # v7.1 新增：定投规划 + 调仓成本测算
    server.add_tool(plan_dca_investment, name="plan_dca_investment",
                    description=plan_dca_investment.__doc__)
    server.add_tool(estimate_rebalance_cost, name="estimate_rebalance_cost",
                    description=estimate_rebalance_cost.__doc__)

    # v8.0 新增：回测 + 压力测试 + 因子分析 + 情景模拟
    server.add_tool(run_backtest, name="run_backtest",
                    description=run_backtest.__doc__)
    server.add_tool(stress_test_portfolio, name="stress_test_portfolio",
                    description=stress_test_portfolio.__doc__)
    server.add_tool(analyze_factor_exposures, name="analyze_factor_exposures",
                    description=analyze_factor_exposures.__doc__)
    server.add_tool(simulate_scenario, name="simulate_scenario",
                    description=simulate_scenario.__doc__)

    # v10.0 新增 12 工具：经理对话/人设/新闻 + 跟仓(4) + 心理画像(2) + 定制报告(2) + 客户对话
    server.add_tool(chat_with_manager, name="chat_with_manager",
                    description=chat_with_manager.__doc__)
    server.add_tool(get_manager_persona, name="get_manager_persona",
                    description=get_manager_persona.__doc__)
    server.add_tool(get_manager_news, name="get_manager_news",
                    description=get_manager_news.__doc__)
    server.add_tool(compare_holdings_change, name="compare_holdings_change",
                    description=compare_holdings_change.__doc__)
    server.add_tool(build_mirror_portfolio, name="build_mirror_portfolio",
                    description=build_mirror_portfolio.__doc__)
    server.add_tool(track_mirror_portfolio, name="track_mirror_portfolio",
                    description=track_mirror_portfolio.__doc__)
    server.add_tool(get_follow_signals, name="get_follow_signals",
                    description=get_follow_signals.__doc__)
    server.add_tool(assess_client_profile, name="assess_client_profile",
                    description=assess_client_profile.__doc__)
    server.add_tool(get_client_communication_guide, name="get_client_communication_guide",
                    description=get_client_communication_guide.__doc__)
    server.add_tool(generate_custom_report, name="generate_custom_report",
                    description=generate_custom_report.__doc__)
    server.add_tool(generate_batch_reports, name="generate_batch_reports",
                    description=generate_batch_reports.__doc__)
    server.add_tool(chat_with_client, name="chat_with_client",
                    description=chat_with_client.__doc__)

    # v9.0: 工具数常量（供测试断言，避免硬编码魔法数；新增工具时同步更新）
    TOOL_COUNT = 48
    def main():
        """MCP Server 入口 — 走 stdio 协议"""
        server.run(transport="stdio")

    if __name__ == '__main__':
        main()
else:
    def main():
        """MCP 未安装时给出明确报错"""
        print("=" * 60, file=sys.stderr)
        print("  fund-advisor MCP Server 需要安装 mcp 包", file=sys.stderr)
        print("  pip install mcp", file=sys.stderr)
        print("  使用方式：以 MCP 客户端连接 stdio 运行本脚本", file=sys.stderr)
        print("=" * 60, file=sys.stderr)
        sys.exit(1)

    if __name__ == '__main__':
        main()
