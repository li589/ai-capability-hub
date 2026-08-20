#!/usr/bin/env python3
"""
统一输出工具

所有 cmd.py 通过此模块输出 JSON，保证格式一致。
"""

import json
from typing import List, Dict, Optional

from _errors import SkillError, AuthError

def make_output(success: bool, markdown: str, data: dict) -> dict:
    return {"success": success, "markdown": markdown, "data": data}

def print_output(success: bool, markdown: str, data: dict):
    """打印标准 JSON 输出"""
    print(json.dumps(make_output(success, markdown, data), ensure_ascii=False, indent=2))

def print_error(e: Exception, default_data: dict = None):
    """将异常转为标准错误输出并打印"""
    if isinstance(e, AuthError):
        msg = f"❌ {e.message}\n\n如果还没有 API_KEY，请前往 https://clawhub.1688.com/ 获取。\n\n请运行: `cli.py configure YOUR_AK`"
    elif isinstance(e, SkillError):
        msg = f"❌ {e.message}"
    elif isinstance(e, ValueError):
        msg = f"❌ 参数错误：{e}"
    else:
        msg = f"❌ 操作失败：{e}"
    print_output(False, msg, default_data or {})


def _truncate(text: str, max_len: int = 20) -> str:
    """截断过长文本"""
    if not text:
        return ""
    text = str(text).replace("|", "｜").replace("\n", " ").strip()  # 替换管道符和换行
    if len(text) > max_len:
        return text[:max_len-2] + ".."
    return text


def _format_number(n: int) -> str:
    """将大数字缩写为易读格式"""
    if n >= 10000_0000:
        return f"{n / 10000_0000:.1f}亿"
    if n >= 10000:
        return f"{n / 10000:.0f}万"
    return str(n)


def _parse_service_selling_points(service_infos: List, selling_points: List) -> str:
    """
    解析商品服务和卖点信息
    
    Args:
        service_infos: 商品服务 JSON 字符串数组
        selling_points: 商品卖点 JSON 字符串数组
    
    Returns:
        格式化后的字符串
    """
    items = []
    
    # 解析服务信息
    for info in (service_infos or []):
        try:
            if isinstance(info, str):
                data = json.loads(info)
            else:
                data = info
            value = data.get('value', '')
            if value:
                items.append(value)
        except (json.JSONDecodeError, AttributeError):
            continue
    
    # 解析卖点信息
    for point in (selling_points or []):
        try:
            if isinstance(point, str):
                data = json.loads(point)
            else:
                data = point
            value = data.get('value', '')
            if value:
                items.append(value)
        except (json.JSONDecodeError, AttributeError):
            continue
    
    return '/'.join(items[:4]) if items else '暂无'  # 最多显示4个


def _clean_url(url: str) -> str:
    """去掉 URL 中的冗余查询参数，缩短原始字符长度"""
    if not url:
        return ""
    idx = url.find('?')
    return url[:idx] if idx != -1 else url


def _escape_cell(text: str) -> str:
    """转义表格单元格中的特殊字符"""
    if not text:
        return ""
    return str(text).replace("|", "｜").replace("\n", " ").strip()


def _parse_items(raw_list: List) -> List[str]:
    """从 JSON 字符串或字典列表中提取 value 值"""
    items = []
    for item in (raw_list or []):
        try:
            data = json.loads(item) if isinstance(item, str) else item
            value = data.get('value', '')
            if value:
                items.append(value)
        except (json.JSONDecodeError, AttributeError):
            continue
    return items


def format_products_table(products: List[Dict], header: Optional[str] = None) -> str:
    """
    将商品列表格式化为 Markdown 表格（精简6列版）
    
    表头：序号 | 商品名称 | 价格 | 供应商 | 服务与卖点 | 链接
    商品名称完整展示；服务与卖点分行显示。
    
    Args:
        products: 商品列表
        header: 可选的表格前置标题/描述
    
    Returns:
        Markdown 格式的表格字符串
    """
    if not products:
        return "未找到匹配商品"
    
    lines = []
    
    # 添加可选的标题
    if header:
        lines.append(header)
        lines.append("")
    
    # 6列表头
    lines.append("| 序号 | 商品名称 | 价格 | 供应商 | 服务与卖点 | 链接 |")
    lines.append("|:-:|:-----|------:|:------|:------|:----:|")
    
    # 表格内容
    for idx, p in enumerate(products, 1):
        # 商品名称：纯文本，完整展示
        title = _escape_cell(p.get('title', '未知商品'))
        
        # 价格
        price = p.get('price')
        price_str = f"￥{price}" if price is not None else "-"
        
        # 供应商：截断8字符
        supplier = _truncate(p.get('supplier') or "-", 8)
        
        # 保障服务与卖点信息，分行显示
        services = _parse_items(p.get('service_infos', []))
        points = _parse_items(p.get('selling_points', []))
        
        tag_parts = []
        if services:
            tag_parts.append(f"🛡️ {'、'.join(services)}")
        if points:
            tag_parts.append(f"🏷️ {'、'.join(points)}")
        tag_cell = "<br>".join(tag_parts) if tag_parts else "-"
        
        # 链接：单独一列，去掉冗余参数缩短 URL
        detail_url = _clean_url(p.get('detail_url', ''))
        link_cell = f"[详情]({detail_url})" if detail_url else "-"
        
        lines.append(f"| {idx} | {title} | {price_str} | {supplier} | {tag_cell} | {link_cell} |")
    
    return "\n".join(lines)

