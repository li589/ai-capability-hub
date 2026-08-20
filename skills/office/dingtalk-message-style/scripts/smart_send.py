#!/usr/bin/env python3
"""
钉钉消息智能发送 - 自动选择最佳格式 + 模板库
官方文档: https://open.dingtalk.com/document/development/robot-message-type

用法:
    python3 smart_send.py --list                    # 列出模板
    python3 smart_send.py --template <模板名> --vars '<JSON>'  # 使用模板
"""
import sys
import json
import urllib.request
import os
import re

WEBHOOKS_FILE = "/Users/qf/.copaw/dingtalk_session_webhooks.json"
TEMPLATES_FILE = "/Users/qf/.copaw/skills/dingtalk-message-style/templates/templates.json"

def get_webhook(session_id=None):
    """获取 webhook"""
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
    """修复淘宝图片链接"""
    if not url:
        return url
    return re.sub(r'\.(jpg|png|jpeg)_\.webp', r'.\1', url)

def send_message(payload, webhook=None):
    """发送消息"""
    if webhook is None:
        webhook = get_webhook()
    
    data = json.dumps(payload, ensure_ascii=False).encode('utf-8')
    req = urllib.request.Request(webhook)
    req.add_header('Content-Type', 'application/json')
    
    response = urllib.request.urlopen(req, data, timeout=10)
    return json.loads(response.read().decode('utf-8'))

# ============ 消息发送函数 ============

def send_text(content, at_mobiles=None, at_user_ids=None, at_all=False):
    """发送文本消息"""
    payload = {"msgtype": "text", "text": {"content": content}}
    if at_mobiles or at_user_ids or at_all:
        payload["at"] = {"atMobiles": at_mobiles or [], "atUserIds": at_user_ids or [], "isAtAll": at_all}
    return send_message(payload)

def send_markdown(title, text, at_mobiles=None, at_user_ids=None, at_all=False):
    """发送 Markdown 消息（不支持图片）"""
    payload = {"msgtype": "markdown", "markdown": {"title": title, "text": text}}
    if at_mobiles or at_user_ids or at_all:
        payload["at"] = {"atMobiles": at_mobiles or [], "atUserIds": at_user_ids or [], "isAtAll": at_all}
    return send_message(payload)

def send_link(title, text, pic_url, message_url):
    """发送链接消息（支持图片）"""
    payload = {
        "msgtype": "link",
        "link": {"title": title, "text": text, "messageUrl": message_url}
    }
    if pic_url:
        payload["link"]["picUrl"] = fix_taobao_image_url(pic_url)
    return send_message(payload)

def send_action_card_single(title, text, single_title, single_url):
    """发送单按钮 ActionCard"""
    return send_message({
        "msgtype": "actionCard",
        "actionCard": {"title": title, "text": text, "singleTitle": single_title, "singleURL": single_url}
    })

def send_action_card_multi(title, text, buttons, btn_orientation="0"):
    """发送多按钮 ActionCard"""
    return send_message({
        "msgtype": "actionCard",
        "actionCard": {"title": title, "text": text, "btnOrientation": btn_orientation, "btns": buttons}
    })

def send_feed_card(links):
    """发送多图文 FeedCard"""
    for link in links:
        if "picURL" in link:
            link["picURL"] = fix_taobao_image_url(link["picURL"])
    return send_message({"msgtype": "feedCard", "feedCard": {"links": links}})

# ============ 智能格式选择 ============

class SmartSender:
    """智能消息发送器 - 自动选择最佳格式"""
    
    def __init__(self):
        self.items = []
        self.title = ""
        self.content = ""
        self.at_mobiles = []
        self.at_user_ids = []
        self.at_all = False
    
    def add_product(self, title, image_url=None, link_url=None, price=None, desc=None):
        """添加商品/链接项"""
        self.items.append({
            "title": title,
            "picURL": fix_taobao_image_url(image_url) if image_url else None,
            "messageURL": link_url,
            "price": price,
            "desc": desc
        })
        return self
    
    def set_title(self, title):
        """设置标题"""
        self.title = title
        return self
    
    def set_content(self, content):
        """设置文本内容"""
        self.content = content
        return self
    
    def at(self, mobiles=None, user_ids=None, at_all=False):
        """设置@对象"""
        if mobiles:
            self.at_mobiles = mobiles if isinstance(mobiles, list) else [mobiles]
        if user_ids:
            self.at_user_ids = user_ids if isinstance(user_ids, list) else [user_ids]
        self.at_all = at_all
        return self
    
    def analyze_and_send(self):
        """分析内容并选择最佳格式发送"""
        
        # 1. 多个商品项 → FeedCard
        if len(self.items) > 1:
            links = []
            for item in self.items:
                if item.get("picURL"):
                    links.append({
                        "title": item["title"],
                        "picURL": item["picURL"],
                        "messageURL": item.get("messageURL") or "https://clawhub.ai"
                    })
            if links:
                return send_feed_card(links)
        
        # 2. 单商品 + 图片 + 链接 → Link
        if len(self.items) == 1 and self.items[0].get("picURL") and self.items[0].get("messageURL"):
            item = self.items[0]
            text = item.get("desc") or ""
            if item.get("price"):
                text = f"💰 价格: {item['price']}\n{text}"
            return send_link(item["title"], text, item["picURL"], item["messageURL"])
        
        # 3. 有内容 → Markdown（不支持图片）
        if self.content:
            text = self.content
            if self.title:
                text = f"### {self.title}\n\n{text}"
            return send_markdown(self.title or "消息", text, self.at_mobiles, self.at_user_ids, self.at_all)
        
        # 4. 只有标题 → Text
        if self.title:
            return send_text(self.title, self.at_mobiles, self.at_user_ids, self.at_all)
        
        raise Exception("没有可发送的内容")

# ============ 模板库 ============

def get_default_templates():
    """默认模板库"""
    return {
        "goods_recommend": {
            "name": "商品推荐",
            "emoji": "🔥",
            "description": "推荐单个商品，带图片和链接",
            "format": "link",
            "example": '{"商品名":"iPhone","价格":"5999","亮点":"最新款","描述":"性能强劲","图片URL":"...","商品链接":"..."}'
        },
        "goods_list": {
            "name": "商品列表",
            "emoji": "📋",
            "description": "多个商品推荐列表（FeedCard）",
            "format": "feedCard",
            "example": '{"商品":[{"名称":"商品1","图片":"...","链接":"...","价格":"99"},{"名称":"商品2","图片":"...","链接":"...","价格":"199"}]}'
        },
        "task_report": {
            "name": "任务报告",
            "emoji": "📋",
            "description": "任务完成情况报告（Markdown表格）",
            "format": "markdown",
            "example": '{"时间":"2026-03-18","任务表格":"|任务|状态|\\n|A|✅|","完成数":"1","总数":"1","总结":"完成"}'
        },
        "price_alert": {
            "name": "降价提醒",
            "emoji": "📉",
            "description": "商品降价通知（Link卡片）",
            "format": "link",
            "example": '{"商品名":"iPhone","原价":"6999","现价":"5999","降幅":"1000","图片URL":"...","商品链接":"..."}'
        },
        "order_status": {
            "name": "订单状态",
            "emoji": "📦",
            "description": "订单状态更新通知",
            "format": "markdown",
            "example": '{"订单号":"123","商品名":"iPhone","状态":"已发货","物流信息":"顺丰快递","时间":"2026-03-18"}'
        },
        "daily_summary": {
            "name": "每日总结",
            "emoji": "📊",
            "description": "每日工作总结",
            "format": "markdown",
            "example": '{"日期":"2026-03-18","已完成":"任务A,任务B","进行中":"任务C","待办":"任务D","完成数":"2","进行中数":"1"}'
        },
        "meeting_notice": {
            "name": "会议通知",
            "emoji": "📅",
            "description": "会议提醒（ActionCard单按钮）",
            "format": "actionCard_single",
            "example": '{"主题":"项目会议","时间":"10:00","地点":"会议室A","参会人":"张三,李四","链接":"..."}'
        },
        "confirm_action": {
            "name": "操作确认",
            "emoji": "❓",
            "description": "需要用户确认的操作（ActionCard多按钮）",
            "format": "actionCard_multi",
            "example": '{"标题":"确认下单?","描述":"商品:iPhone 价格:5999","按钮1标题":"确认","按钮1URL":"...","按钮2标题":"取消","按钮2URL":"..."}'
        },
        "alert_notify": {
            "name": "告警通知",
            "emoji": "⚠️",
            "description": "系统告警通知（@相关人员）",
            "format": "markdown",
            "example": '{"标题":"服务器告警","内容":"CPU使用率超过90%","手机号":"138xxxx"}'
        },
        "shopping_cart": {
            "name": "购物车提醒",
            "emoji": "🛒",
            "description": "购物车商品汇总",
            "format": "markdown",
            "example": '{"商品数":"5","总金额":"1999","商品表格":"|商品|价格|\\n|A|99|","优惠":"满200减20"}'
        }
    }

def load_templates():
    """加载模板"""
    if os.path.exists(TEMPLATES_FILE):
        with open(TEMPLATES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return get_default_templates()

def apply_template(template_name, **kwargs):
    """应用模板并发送"""
    templates = load_templates()
    
    if template_name not in templates:
        raise Exception(f"模板不存在: {template_name}\n可用模板: {list(templates.keys())}")
    
    tmpl = templates[template_name]
    fmt = tmpl["format"]
    
    def replace(text, values):
        if isinstance(text, str):
            for k, v in values.items():
                text = text.replace(f"{{{k}}}", str(v))
        return text
    
    if fmt == "link":
        return send_link(
            replace(tmpl.get("title_template", "{商品名}"), kwargs),
            replace(tmpl.get("text_template", ""), kwargs),
            fix_taobao_image_url(kwargs.get("图片URL", "")),
            kwargs.get("商品链接", "https://clawhub.ai")
        )
    
    elif fmt == "markdown":
        title = replace(tmpl.get("title_template", "消息"), kwargs)
        text = replace(tmpl.get("text_template", ""), kwargs)
        at_mobiles = kwargs.get("手机号", "").split(",") if kwargs.get("手机号") else None
        at_all = kwargs.get("@所有人", False)
        return send_markdown(title, text, at_mobiles, at_all=at_all)
    
    elif fmt == "actionCard_single":
        return send_action_card_single(
            replace(tmpl.get("title_template", ""), kwargs),
            replace(tmpl.get("text_template", ""), kwargs),
            replace(tmpl.get("button_title", "查看详情"), kwargs),
            kwargs.get("链接", "https://clawhub.ai")
        )
    
    elif fmt == "actionCard_multi":
        buttons = []
        for i in range(1, 6):  # 最多5个按钮
            btn_title = kwargs.get(f"按钮{i}标题")
            btn_url = kwargs.get(f"按钮{i}URL")
            if btn_title and btn_url:
                buttons.append({"title": btn_title, "actionURL": btn_url})
        btn_orientation = kwargs.get("按钮排列", "0")  # 0=竖直, 1=横向
        return send_action_card_multi(
            replace(tmpl.get("title_template", ""), kwargs),
            replace(tmpl.get("text_template", ""), kwargs),
            buttons,
            btn_orientation
        )
    
    elif fmt == "feedCard":
        links = []
        items = kwargs.get("商品", [])
        for item in items:
            links.append({
                "title": item.get("名称", ""),
                "picURL": fix_taobao_image_url(item.get("图片", "")),
                "messageURL": item.get("链接", "https://clawhub.ai")
            })
        return send_feed_card(links)
    
    else:
        raise Exception(f"不支持的格式: {fmt}")

def list_templates():
    """列出所有模板"""
    templates = load_templates()
    print("\n📋 可用模板:\n")
    print(f"{'模板名':<20} {'名称':<15} {'说明'}")
    print("-" * 60)
    for key, tmpl in templates.items():
        print(f"{tmpl['emoji']} {key:<18} {tmpl['name']:<12} {tmpl['description']}")
    print()

def main():
    args = sys.argv[1:]
    
    if not args or args[0] == "--help":
        print(__doc__)
        list_templates()
        return
    
    if args[0] == "--list":
        list_templates()
        return
    
    if args[0] == "--template":
        if len(args) < 2:
            print("请指定模板名: --template <模板名>")
            list_templates()
            return
        
        template_name = args[1]
        vars_data = {}
        
        if "--vars" in args:
            vars_idx = args.index("--vars")
            if len(args) > vars_idx + 1:
                vars_data = json.loads(args[vars_idx + 1])
        
        result = apply_template(template_name, **vars_data)
        
        if result.get('errcode', 0) == 0:
            print(f"✅ 消息发送成功 (模板: {template_name})")
        else:
            print(f"❌ 发送失败: {result}")
            sys.exit(1)

if __name__ == "__main__":
    main()