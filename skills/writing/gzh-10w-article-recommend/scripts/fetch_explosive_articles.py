#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
公众号爆款内容榜单获取脚本

功能：
1. 调用API获取爆款内容数据
2. 按阅读数排序，取前10条
3. 输出TOP10榜单列表（纯文本格式）
4. 生成HTML样式文件展示榜单

使用方法：
python fetch_explosive_articles.py --origin_word "AI编程" --spit_words '["AI","编程"]' --expansion_words '["AI科技","人工智能","大模型"]'
"""

import argparse
import json
import sys
import os
from datetime import datetime
import requests


def fetch_explosive_articles(origin_word: str, spit_words: list, expansion_words: list) -> dict:
    """调用API获取爆款内容数据"""
    url = "https://onetotenvip.com/skill/cozeSkill/getWxLowFanExplosiveArticle"
    
    payload = {
        "originWord": origin_word,
        "spitWords": spit_words,
        "expansionWords": expansion_words
    }
    
    headers = {"Content-Type": "application/json"}
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        if response.status_code >= 400:
            raise Exception(f"HTTP请求失败: 状态码 {response.status_code}")
        
        data = response.json()
        if "code" in data and data["code"] != 2000:
            raise Exception(f"API错误: {data.get('message', data.get('msg', '未知错误'))}")
        return data
    except Exception as e:
        if "requests" in type(e).__module__:
            raise Exception(f"网络请求失败: {str(e)}")
        raise
    except json.JSONDecodeError as e:
        raise Exception(f"JSON解析失败: {str(e)}")


def parse_count_to_int(count_str) -> int:
    """将字符串类型的计数转换为整数"""
    if isinstance(count_str, (int, float)):
        return int(count_str)
    if not count_str:
        return 0
    
    count_str = str(count_str).strip()
    if 'w+' in count_str.lower():
        return int(float(count_str.lower().replace('w+', '').replace('w', '')) * 10000)
    elif 'w' in count_str.lower():
        return int(float(count_str.lower().replace('w', '')) * 10000)
    
    try:
        return int(count_str)
    except:
        return 0


def process_ranking_data(data: dict) -> list:
    """处理榜单数据，按阅读数排序取前10条"""
    articles = []
    
    if isinstance(data, list):
        articles = data
    elif isinstance(data, dict):
        articles = data.get("data", data.get("list", data.get("articles", [])))
        if isinstance(articles, dict):
            articles = articles.get("list", articles.get("records", []))
    
    if not articles:
        return []
    
    # 按阅读数排序
    sorted_articles = sorted(articles, key=lambda x: parse_count_to_int(x.get("clicksCount", "0")), reverse=True)
    
    return sorted_articles[:10]


def validate_ranking_data(articles: list) -> dict:
    """自检榜单数据"""
    validation_result = {
        "valid": True,
        "errors": []
    }
    
    for idx, article in enumerate(articles, 1):
        # 检查互动数据字段
        like_count = article.get("likeCount")
        comment_count = article.get("commentCount")
        share_count = article.get("shareCount")
        
        if like_count is None or comment_count is None or share_count is None:
            validation_result["errors"].append(f"第{idx}条数据缺少互动数据")
            validation_result["valid"] = False
    
    return validation_result


def format_ranking_list(articles: list) -> str:
    """将榜单数据格式化为三行一段的段落形式"""
    if not articles:
        return "未获取到符合条件的爆款内容数据"
    
    output_lines = []
    for idx, article in enumerate(articles, 1):
        title = article.get("title", "未知标题")
        author = article.get("userName", article.get("accountId", "未知作者"))
        publish_time = article.get("publicTime", "未知时间")
        article_link = article.get("oriUrl", "#")
        
        like_count = article.get("likeCount", 0)
        comment_count = article.get("commentCount", 0)
        share_count = article.get("shareCount", 0)
        
        # 只保留月日（格式：04-08）
        if len(publish_time) > 10:
            publish_time = publish_time[5:10]  # 取 MM-DD 部分
        
        title_display = f"[{title}]({article_link})" if article_link and article_link != "#" else title
        
        # 第一行：排名 + 标题
        output_lines.append(f"🔢 【{idx}.】{title_display}")
        # 第二行：作者 + 发布时间
        output_lines.append(f"👤 {author}  |  📅 {publish_time}")
        # 第三行：作品数据
        output_lines.append(f"👍 {like_count}  |  💬 {comment_count}  |  🔗 {share_count}")
        
        if idx < len(articles):
            output_lines.append("")
    
    return "\n".join(output_lines)


def generate_html_file(articles: list, keyword: str) -> str:
    """生成HTML样式文件展示榜单（全内联样式）"""
    
    # 微信公众号主题色
    gzh_green = "#07C160"
    
    # 生成卡片HTML（全内联样式）
    cards_html = ""
    if not articles:
        cards_html = f'<div style="grid-column: 1 / -1; text-align: center; padding: 60px 20px; color: #999;"><div style="font-size: 48px; margin-bottom: 16px;">📭</div><div style="font-size: 18px; margin-bottom: 8px;">暂无符合条件的爆款内容</div><div style="font-size: 14px;">建议尝试其他关键词或拓展搜索范围</div></div>'
    else:
        for idx, article in enumerate(articles, 1):
            title = article.get("title", "未知标题")
            author = article.get("userName", article.get("accountId", "未知作者"))
            publish_time = article.get("publicTime", "未知时间")
            article_link = article.get("oriUrl", "#")
            
            like_display = format_number(article.get("likeCount", 0))
            comment_display = format_number(article.get("commentCount", 0))
            share_display = format_number(article.get("shareCount", 0))
            read_display = format_number(article.get("clicksCount", 0))
            
            # 日期只保留月日（格式：04-08）
            publish_time_short = publish_time[5:10] if len(publish_time) > 10 else publish_time
            
            card = f'''<div style="background: white; border-radius: 12px; padding: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); transition: all 0.3s ease; display: flex; flex-direction: column; gap: 12px;">
        <div style="display: flex; align-items: flex-start; gap: 8px;">
            <div style="flex-shrink: 0; font-size: 14px; font-weight: 700; color: {gzh_green}; line-height: 1.5;">{idx}.</div>
            <div style="flex: 1; font-size: 15px; font-weight: 600; color: #333; line-height: 1.6;">
                <a href="{article_link}" target="_blank" style="color: #333; text-decoration: none;">{title}</a>
            </div>
        </div>
        <div style="border-bottom: 1px solid #eee; margin: 0;"></div>
        <div style="display: flex; align-items: center; gap: 12px; font-size: 12px; color: #666; flex-wrap: wrap;">
            <span style="display: flex; align-items: center; gap: 4px;">👤 {author}</span>
            <span style="display: flex; align-items: center; gap: 4px;">📅 {publish_time_short}</span>
            <span style="display: flex; align-items: center; gap: 4px;">👁 {read_display}</span>
        </div>
        <div style="display: flex; align-items: center; justify-content: space-between; gap: 12px;">
            <div style="display: flex; align-items: center; gap: 16px; font-size: 13px;">
                <span style="color: #666;">👍 <span style="color: {gzh_green}; font-weight: 600;">{like_display}</span></span>
                <span style="color: #666;">💬 <span style="color: {gzh_green}; font-weight: 600;">{comment_display}</span></span>
                <span style="color: #666;">🔗 <span style="color: {gzh_green}; font-weight: 600;">{share_display}</span></span>
            </div>
            <a href="{article_link}" target="_blank" style="color: {gzh_green}; text-decoration: none; font-size: 13px; font-weight: 500;">查看作品 →</a>
        </div>
    </div>'''
            cards_html += card
    
    # 完整的HTML（全内联样式，简约设计）
    html_content = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>公众号爆款文章推荐 - {keyword}</title>
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Microsoft YaHei', Arial, sans-serif; background: #f5f7fa; min-height: 100vh;">
    <div style="max-width: 1200px; margin: 0 auto; padding: 40px 20px;">
        <h1 style="text-align: center; font-size: 32px; font-weight: 600; color: #333; margin-bottom: 30px;">公众号爆款文章推荐</h1>
        <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 20px; margin-bottom: 30px;">
{cards_html}
        </div>
        <div style="text-align: center; color: #999; font-size: 14px; padding: 20px;">
            <p>数据更新时间：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
            <p style="margin-top: 8px; font-size: 12px; color: #bbb;">数据非实时，为入库快照</p>
        </div>
    </div>
</body>
</html>'''
    
    # 生成文件
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"ranking_{timestamp}.html"
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    return filename


def format_number(num) -> str:
    """格式化数字显示（万、亿）"""
    try:
        num = int(num)
        if num >= 100000000:
            return f"{num/100000000:.1f}亿"
        elif num >= 10000:
            return f"{num/10000:.1f}万"
        else:
            return str(num)
    except:
        return str(num)


def main():
    parser = argparse.ArgumentParser(description="获取公众号爆款内容榜单")
    parser.add_argument("--origin_word", required=True, help="原词（用户输入）")
    parser.add_argument("--spit_words", required=True, help="分词组（JSON数组字符串）")
    parser.add_argument("--expansion_words", required=True, help="拓展词组（JSON数组字符串）")
    
    args = parser.parse_args()
    
    try:
        spit_words = json.loads(args.spit_words)
        expansion_words = json.loads(args.expansion_words)
        
        print(f"正在获取爆款内容数据...")
        print(f"原词: {args.origin_word}")
        print(f"分词: {spit_words}")
        print(f"拓展词: {expansion_words}")
        print("-" * 60)
        
        data = fetch_explosive_articles(args.origin_word, spit_words, expansion_words)
        articles = process_ranking_data(data)
        
        # 自检数据
        if articles:
            validation = validate_ranking_data(articles)
            if not validation["valid"]:
                print("数据自检发现问题：")
                for error in validation["errors"]:
                    print(f"  - {error}")
                print("-" * 60)
        
        if len(articles) < 10:
            print(f"提示：当前获取到 {len(articles)} 条数据，不足10条")
            print("建议：可尝试拓展更多相关关键词以获取更多数据")
            print("-" * 60)
        
        # 输出文本榜单
        ranking_list = format_ranking_list(articles)
        print(ranking_list)
        
        # 自动生成HTML文件（无论数据多少都生成）
        html_file = generate_html_file(articles, args.origin_word)
        if html_file:
            print("\n" + "=" * 60)
            print(f"HTML榜单已生成：{html_file}")
            print("请在浏览器中打开查看完整榜单")
        
        print("\n" + "=" * 60)
        if articles:
            print(f"共获取到 {len(articles)} 条爆款内容数据（按阅读数排序）")
        else:
            print("未获取到符合条件的爆款内容数据")
        
        return 0
        
    except json.JSONDecodeError as e:
        print(f"错误: JSON参数解析失败 - {str(e)}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"错误: {str(e)}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
