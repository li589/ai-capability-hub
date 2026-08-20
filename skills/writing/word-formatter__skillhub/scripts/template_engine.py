#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模板引擎模块
支持模板加载、继承机制、模板应用
"""

import os
import re
import yaml
from pathlib import Path
from copy import deepcopy

def load_template(template_id, gov_doctype=None):
    """
    加载模板
    
    Args:
        template_id: 模板 ID
        gov_doctype: 公文类型（仅 gov_ 模板）
    
    Returns:
        dict: 模板配置
    """
    result = {
        "success": False,
        "template_id": template_id,
        "name": None,
        "config": None,
        "error": None
    }
    
    try:
        # 1. 确定模板文件路径
        if template_id.startswith("gov_") and gov_doctype:
            # 公文模板，根据 doctype 确定具体模板
            gov_template_map = {
                "通知": "gov_tongzhi",
                "报告": "gov_baogao",
                "请示": "gov_qingshi",
                "批复": "gov_pifu",
                "纪要": "gov_jiyao",
                "函": "gov_han",
                "意见": "gov_yijian",
                "通报": "gov_tongbao",
                "公告": "gov_gonggao",
                "决定": "gov_jueding"
            }
            template_id = gov_template_map.get(gov_doctype, template_id)
        
        # 2. 查找模板文件
        template_dir = os.path.join(os.path.dirname(__file__), "..", "templates")
        template_path = find_template(template_id, template_dir)
        
        if not template_path:
            result["error"] = f"模板不存在：{template_id}"
            return result
        
        # 3. 读取模板配置
        with open(template_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # 解析 frontmatter
        match = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
        if match:
            frontmatter = yaml.safe_load(match.group(1))
            template_body = content[match.end():].strip()
        else:
            frontmatter = {}
            template_body = content
        
        # 4. 检查继承
        base_template_id = frontmatter.get("extends", None)
        if base_template_id:
            base_template = load_template(base_template_id)
            if base_template["success"]:
                # 合并配置（子类覆盖父类）
                config = merge_config(base_template["config"], frontmatter)
            else:
                config = frontmatter
        else:
            config = frontmatter
        
        # 5. 添加模板正文
        config["body"] = template_body
        
        result["success"] = True
        result["name"] = config.get("name", template_id)
        result["config"] = config
        result["path"] = template_path
        
    except Exception as e:
        result["error"] = str(e)
    
    return result

def find_template(template_id, template_dir):
    """
    查找模板文件
    
    Args:
        template_id: 模板 ID
        template_dir: 模板目录
    
    Returns:
        str: 模板文件路径
    """
    # 遍历所有子目录
    for root, dirs, files in os.walk(template_dir):
        for file in files:
            if file.endswith(".md") and template_id in file:
                return os.path.join(root, file)
    
    return None

def merge_config(base_config, override_config):
    """
    合并配置（子类覆盖父类）
    
    Args:
        base_config: 基础配置
        override_config: 覆盖配置
    
    Returns:
        dict: 合并后的配置
    """
    merged = deepcopy(base_config)
    
    for key, value in override_config.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            # 递归合并字典
            merged[key] = merge_config(merged[key], value)
        else:
            # 直接覆盖
            merged[key] = value
    
    return merged

def apply_template(doc_structure, template, format_options=None):
    """
    应用模板到文档
    
    Args:
        doc_structure: 文档结构
        template: 模板配置
        format_options: 格式选项
    
    Returns:
        dict: 排版后的文档结构
    """
    result = deepcopy(doc_structure)
    config = template["config"]
    format_options = format_options or {}
    
    # 1. 应用页面设置
    if "page_setup" in config:
        result["page_setup"] = config["page_setup"]
    
    # 2. 应用字体规则
    font_rules = config.get("fonts", {})
    result["font_rules"] = font_rules
    
    # 3. 应用段落规则
    paragraph_rules = config.get("paragraph", {})
    result["paragraph_rules"] = paragraph_rules
    
    # 4. 处理段落
    for i, para in enumerate(result.get("paragraphs", [])):
        # 根据标题层级应用不同样式
        level = para.get("level", None)
        
        if level == 1:
            apply_heading1_style(para, config)
        elif level == 2:
            apply_heading2_style(para, config)
        elif level == 3:
            apply_heading3_style(para, config)
        elif level == 4:
            apply_heading4_style(para, config)
        else:
            apply_body_style(para, config)
    
    # 5. 处理表格
    for table in result.get("tables", []):
        apply_table_style(table, config)
    
    # 6. 应用中英文加空格规则
    if config.get("auto_spacing", True):
        result = apply_auto_spacing(result)
    
    # 7. 应用标点规范化
    if config.get("punct_normalize", True):
        result = apply_punct_normalize(result)
    
    return result

def apply_heading1_style(para, config):
    """应用一级标题样式"""
    fonts = config.get("fonts", {})
    paragraph = config.get("paragraph", {})
    
    # 字体
    h1_font = fonts.get("h1", fonts.get("一级标题", "黑体 16pt"))
    font_name, font_size = parse_font(h1_font)
    
    for run in para.get("runs", []):
        run["font_name"] = font_name
        run["font_size"] = font_size
        run["bold"] = True
    
    # 段落
    para["alignment"] = paragraph.get("h1_alignment", "left")
    para["line_spacing"] = paragraph.get("h1_line_spacing", 28)
    para["space_before"] = paragraph.get("h1_space_before", 12)
    para["space_after"] = paragraph.get("h1_space_after", 6)

def apply_heading2_style(para, config):
    """应用二级标题样式"""
    fonts = config.get("fonts", {})
    paragraph = config.get("paragraph", {})
    
    h2_font = fonts.get("h2", fonts.get("二级标题", "楷体 16pt"))
    font_name, font_size = parse_font(h2_font)
    
    for run in para.get("runs", []):
        run["font_name"] = font_name
        run["font_size"] = font_size
        run["bold"] = False
    
    para["alignment"] = paragraph.get("h2_alignment", "left")
    para["line_spacing"] = paragraph.get("h2_line_spacing", 28)
    para["space_before"] = paragraph.get("h2_space_before", 6)
    para["space_after"] = paragraph.get("h2_space_after", 6)

def apply_heading3_style(para, config):
    """应用三级标题样式"""
    fonts = config.get("fonts", {})
    paragraph = config.get("paragraph", {})
    
    h3_font = fonts.get("h3", fonts.get("三级标题", "仿宋 16pt 加粗"))
    font_name, font_size = parse_font(h3_font)
    
    for run in para.get("runs", []):
        run["font_name"] = font_name
        run["font_size"] = font_size
        run["bold"] = True
    
    para["alignment"] = paragraph.get("h3_alignment", "left")
    para["line_spacing"] = paragraph.get("h3_line_spacing", 28)
    para["space_before"] = paragraph.get("h3_space_before", 6)
    para["space_after"] = paragraph.get("h3_space_after", 6)

def apply_heading4_style(para, config):
    """应用四级标题样式"""
    fonts = config.get("fonts", {})
    paragraph = config.get("paragraph", {})
    
    h4_font = fonts.get("h4", fonts.get("四级标题", "仿宋 16pt"))
    font_name, font_size = parse_font(h4_font)
    
    for run in para.get("runs", []):
        run["font_name"] = font_name
        run["font_size"] = font_size
        run["bold"] = False
    
    para["alignment"] = paragraph.get("h4_alignment", "left")
    para["line_spacing"] = paragraph.get("h4_line_spacing", 28)
    para["space_before"] = paragraph.get("h4_space_before", 6)
    para["space_after"] = paragraph.get("h4_space_after", 6)

def apply_body_style(para, config):
    """应用正文样式"""
    fonts = config.get("fonts", {})
    paragraph = config.get("paragraph", {})
    
    body_font = fonts.get("body", fonts.get("正文", "仿宋 16pt"))
    font_name, font_size = parse_font(body_font)
    
    for run in para.get("runs", []):
        run["font_name"] = font_name
        run["font_size"] = font_size
        run["bold"] = False
    
    para["alignment"] = paragraph.get("body_alignment", "justify")
    para["line_spacing"] = paragraph.get("body_line_spacing", 28)
    para["first_line_indent"] = paragraph.get("body_first_line_indent", 2)
    para["space_before"] = paragraph.get("body_space_before", 0)
    para["space_after"] = paragraph.get("body_space_after", 0)

def apply_table_style(table, config):
    """应用表格样式"""
    table_style = config.get("table", {})
    
    # 简化实现
    table["style"] = table_style.get("style", "Table Grid")
    table["border"] = table_style.get("border", "single")
    table["shading"] = table_style.get("shading", None)

def apply_auto_spacing(doc_structure):
    """应用中英文之间自动加空格"""
    import re
    
    for para in doc_structure.get("paragraphs", []):
        text = para.get("text", "")
        
        # 中文后面跟英文/数字
        text = re.sub(r"([\u4e00-\u9fa5])([A-Za-z0-9])", r"\1 \2", text)
        
        # 英文/数字后面跟中文
        text = re.sub(r"([A-Za-z0-9])([\u4e00-\u9fa5])", r"\1 \2", text)
        
        para["text"] = text
        
        # 同步更新 runs
        if para.get("runs"):
            # 简化：只更新第一个 run
            para["runs"][0]["text"] = text
    
    return doc_structure

def apply_punct_normalize(doc_structure):
    """应用标点规范化"""
    import re
    
    for para in doc_structure.get("paragraphs", []):
        text = para.get("text", "")
        
        # 规范化省略号
        text = re.sub(r"\.{2,}", "……", text)
        
        # 规范化破折号
        text = re.sub(r"-{2,}", "——", text)
        
        # 规范化引号（简化）
        text = text.replace(""", """).replace(""", """)
        text = text.replace(""", """).replace(""", """)
        
        para["text"] = text
    
    return doc_structure

def parse_font(font_str):
    """
    解析字体字符串
    
    Args:
        font_str: 字体字符串（如 "黑体 16pt"）
    
    Returns:
        tuple: (font_name, font_size)
    """
    import re
    
    # 匹配字号
    size_match = re.search(r"(\d+)pt", font_str)
    font_size = int(size_match.group(1)) if size_match else 12
    
    # 提取字体名
    font_name = re.sub(r"\d+pt", "", font_str).strip()
    font_name = re.sub(r"加粗|加粗|italic", "", font_name).strip()
    
    return font_name, font_size

if __name__ == "__main__":
    # 测试
    import sys
    
    if len(sys.argv) > 1:
        template_id = sys.argv[1]
        result = load_template(template_id)
        import json
        print(json.dumps(result, ensure_ascii=False, indent=2))
