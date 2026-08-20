#!/usr/bin/env python3
"""
钉钉消息发送工具 - 完整支持 Webhook 消息类型
官方文档: https://open.dingtalk.com/document/development/robot-message-type

用法:
    python3 send_dingtalk.py text "内容" [--at-mobiles "手机号1,手机号2"] [--at-all]
    python3 send_dingtalk.py markdown "标题" "内容" [--at-mobiles "手机号1,手机号2"]
    python3 send_dingtalk.py link "标题" "描述" "图片URL" "跳转URL"
    python3 send_dingtalk.py action "标题" "描述" "按钮标题" "按钮URL" [--pic-url "图片URL"]
    python3 send_dingtalk.py action_multi "标题" "描述" '[{"title":"按钮1","actionURL":"url1"},{"title":"按钮2","actionURL":"url2"}]' [--btn-orientation 0|1]
    python3 send_dingtalk.py feed '[{"title":"标题","picURL":"图片","messageURL":"链接"}]'
"""
import sys
import json
import urllib.request
import os
import re
import argparse

WEBHOOKS_FILE = "/Users/qf/.copaw/dingtalk_session_webhooks.json"

def get_webhook(session_id=None):
    """获取 webhook，默认使用当前会话"""
    if not os.path.exists(WEBHOOKS_FILE):
        raise Exception("webhook 文件不存在")
    
    with open(WEBHOOKS_FILE, 'r') as f:
        data = json.load(f)
    
    if session_id:
        key = f"dingtalk:sw:{session_id}"
        if key in data:
            return data[key]
    
    for key, webhook in data.items():
        return webhook
    raise Exception("未找到 webhook")

def fix_taobao_image_url(url):
    """修复淘宝图片链接，去掉 _.webp 后缀"""
    if not url:
        return url
    return re.sub(r'\.(jpg|png|jpeg)_\.webp', r'.\1', url)

def send_message(payload, webhook=None):
    """发送消息到钉钉"""
    if webhook is None:
        webhook = get_webhook()
    
    data = json.dumps(payload, ensure_ascii=False).encode('utf-8')
    req = urllib.request.Request(webhook)
    req.add_header('Content-Type', 'application/json')
    
    response = urllib.request.urlopen(req, data, timeout=10)
    return json.loads(response.read().decode('utf-8'))

# ============ 消息类型函数 ============

def send_text(content, at_mobiles=None, at_user_ids=None, at_all=False):
    """
    发送文本消息
    
    参数:
        content: 文本内容
        at_mobiles: 被@人手机号列表
        at_user_ids: 被@人用户ID列表
        at_all: 是否@所有人
    """
    payload = {
        "msgtype": "text",
        "text": {
            "content": content
        }
    }
    
    if at_mobiles or at_user_ids or at_all:
        payload["at"] = {
            "atMobiles": at_mobiles or [],
            "atUserIds": at_user_ids or [],
            "isAtAll": at_all
        }
    
    return send_message(payload)

def send_markdown(title, text, at_mobiles=None, at_user_ids=None, at_all=False):
    """
    发送 Markdown 消息
    
    参数:
        title: 首屏会话透出的展示内容
        text: Markdown 格式的消息内容
        at_mobiles: 被@人手机号列表 (需要在 text 中包含 "@手机号")
        at_user_ids: 被@人用户ID列表
        at_all: 是否@所有人
    
    注意:
        - Markdown 只支持子集: 标题(#)、引用(>)、粗体(**)、链接等
        - 不支持图片显示！如需图片请使用 Link 或 ActionCard
    """
    payload = {
        "msgtype": "markdown",
        "markdown": {
            "title": title,
            "text": text
        }
    }
    
    if at_mobiles or at_user_ids or at_all:
        payload["at"] = {
            "atMobiles": at_mobiles or [],
            "atUserIds": at_user_ids or [],
            "isAtAll": at_all
        }
    
    return send_message(payload)

def send_link(title, text, pic_url, message_url):
    """
    发送链接消息
    
    参数:
        title: 消息标题
        text: 消息内容（如果太长只会部分展示）
        pic_url: 图片 URL（可选）
        message_url: 点击消息跳转的 URL
    """
    payload = {
        "msgtype": "link",
        "link": {
            "title": title,
            "text": text,
            "messageUrl": message_url
        }
    }
    
    if pic_url:
        payload["link"]["picUrl"] = fix_taobao_image_url(pic_url)
    
    return send_message(payload)

def send_action_card_single(title, text, single_title, single_url):
    """
    发送整体跳转 ActionCard（单按钮）
    
    参数:
        title: 首屏会话透出的展示内容
        text: Markdown 格式的消息内容
        single_title: 单个按钮的标题
        single_url: 单个按钮的跳转链接
    """
    payload = {
        "msgtype": "actionCard",
        "actionCard": {
            "title": title,
            "text": text,
            "singleTitle": single_title,
            "singleURL": single_url
        }
    }
    
    return send_message(payload)

def send_action_card_multi(title, text, buttons, btn_orientation="0"):
    """
    发送独立跳转 ActionCard（多按钮）
    
    参数:
        title: 首屏会话透出的展示内容
        text: Markdown 格式的消息内容
        buttons: 按钮列表，格式: [{"title": "按钮1", "actionURL": "url1"}, ...]
        btn_orientation: 按钮排列方向
            "0" = 竖直排列（默认）
            "1" = 横向排列
    
    示例:
        send_action_card_multi(
            "标题",
            "描述内容",
            [
                {"title": "按钮1", "actionURL": "https://url1.com"},
                {"title": "按钮2", "actionURL": "https://url2.com"}
            ],
            btn_orientation="1"  # 横向排列
        )
    """
    payload = {
        "msgtype": "actionCard",
        "actionCard": {
            "title": title,
            "text": text,
            "btnOrientation": btn_orientation,
            "btns": buttons
        }
    }
    
    return send_message(payload)

def send_feed_card(links):
    """
    发送 FeedCard（多图文消息）
    
    参数:
        links: 图文链接列表，格式:
            [
                {
                    "title": "标题1",
                    "picURL": "图片URL1",
                    "messageURL": "跳转链接1"
                },
                ...
            ]
    
    注意:
        - Webhook 专用消息类型
        - 最多支持多条图文
    """
    # 修复所有图片链接
    for link in links:
        if "picURL" in link:
            link["picURL"] = fix_taobao_image_url(link["picURL"])
    
    payload = {
        "msgtype": "feedCard",
        "feedCard": {
            "links": links
        }
    }
    
    return send_message(payload)

def send_empty():
    """
    发送空消息（不回复消息到群里）
    """
    return send_message({"msgtype": "empty"})

# ============ 命令行入口 ============

def main():
    parser = argparse.ArgumentParser(
        description="钉钉消息发送工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    subparsers = parser.add_subparsers(dest="msg_type", help="消息类型")
    
    # Text 消息
    text_parser = subparsers.add_parser("text", help="发送文本消息")
    text_parser.add_argument("content", help="文本内容")
    text_parser.add_argument("--at-mobiles", help="被@人手机号，逗号分隔")
    text_parser.add_argument("--at-user-ids", help="被@人用户ID，逗号分隔")
    text_parser.add_argument("--at-all", action="store_true", help="@所有人")
    
    # Markdown 消息
    md_parser = subparsers.add_parser("markdown", help="发送Markdown消息")
    md_parser.add_argument("title", help="标题")
    md_parser.add_argument("text", help="Markdown内容")
    md_parser.add_argument("--at-mobiles", help="被@人手机号，逗号分隔")
    md_parser.add_argument("--at-user-ids", help="被@人用户ID，逗号分隔")
    md_parser.add_argument("--at-all", action="store_true", help="@所有人")
    
    # Link 消息
    link_parser = subparsers.add_parser("link", help="发送链接消息")
    link_parser.add_argument("title", help="标题")
    link_parser.add_argument("text", help="描述")
    link_parser.add_argument("pic_url", nargs="?", default="", help="图片URL")
    link_parser.add_argument("message_url", help="跳转URL")
    
    # ActionCard 单按钮
    action_parser = subparsers.add_parser("action", help="发送单按钮ActionCard")
    action_parser.add_argument("title", help="标题")
    action_parser.add_argument("text", help="描述")
    action_parser.add_argument("single_title", help="按钮标题")
    action_parser.add_argument("single_url", help="按钮URL")
    
    # ActionCard 多按钮
    action_multi_parser = subparsers.add_parser("action_multi", help="发送多按钮ActionCard")
    action_multi_parser.add_argument("title", help="标题")
    action_multi_parser.add_argument("text", help="描述")
    action_multi_parser.add_argument("buttons", help="按钮JSON数组")
    action_multi_parser.add_argument("--btn-orientation", default="0", choices=["0", "1"], 
                                     help="按钮排列: 0=竖直, 1=横向")
    
    # FeedCard
    feed_parser = subparsers.add_parser("feed", help="发送多图文FeedCard")
    feed_parser.add_argument("links", help="图文链接JSON数组")
    
    args = parser.parse_args()
    
    if not args.msg_type:
        parser.print_help()
        return
    
    try:
        if args.msg_type == "text":
            at_mobiles = args.at_mobiles.split(",") if args.at_mobiles else None
            at_user_ids = args.at_user_ids.split(",") if args.at_user_ids else None
            result = send_text(args.content, at_mobiles, at_user_ids, args.at_all)
        
        elif args.msg_type == "markdown":
            at_mobiles = args.at_mobiles.split(",") if args.at_mobiles else None
            at_user_ids = args.at_user_ids.split(",") if args.at_user_ids else None
            result = send_markdown(args.title, args.text, at_mobiles, at_user_ids, args.at_all)
        
        elif args.msg_type == "link":
            result = send_link(args.title, args.text, args.pic_url, args.message_url)
        
        elif args.msg_type == "action":
            result = send_action_card_single(args.title, args.text, args.single_title, args.single_url)
        
        elif args.msg_type == "action_multi":
            buttons = json.loads(args.buttons)
            result = send_action_card_multi(args.title, args.text, buttons, args.btn_orientation)
        
        elif args.msg_type == "feed":
            links = json.loads(args.links)
            result = send_feed_card(links)
        
        else:
            print(f"不支持的消息类型: {args.msg_type}")
            sys.exit(1)
        
        if result.get('errcode', 0) == 0:
            print(f"✅ 消息发送成功 ({args.msg_type})")
        else:
            print(f"❌ 发送失败: {result}")
            sys.exit(1)
    
    except Exception as e:
        print(f"❌ 错误: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()