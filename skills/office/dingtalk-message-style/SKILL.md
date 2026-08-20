---
name: dingtalk-message-style
description: 提升钉钉消息展示样式，支持 Markdown、Link 卡片、ActionCard 按钮、FeedCard 图文列表等多种格式。支持智能格式选择、模板库、@提醒功能。
metadata:
  copaw:
    emoji: 🎨
install_source: official
install_method: download
skill_id: official_ZBptu1hd
enabled_at: 1787232383430
version: 1.0.0
name_zh: 钉钉消息样式增强技能
---

# 钉钉消息样式 Skill

提升钉钉消息的视觉效果和交互体验，支持智能格式选择、模板库、@提醒。

**官方文档**: https://open.dingtalk.com/document/development/robot-message-type

---

## 支持的消息类型

| 类型 | 图片 | 按钮 | @提醒 | 最佳场景 |
|------|:----:|:----:|:-----:|----------|
| **text** | ❌ | ❌ | ✅ | 简单通知 |
| **markdown** | ❌ | ❌ | ✅ | 报告、表格、列表 |
| **link** | ✅ | ❌ | ❌ | 商品推荐、文章分享 |
| **actionCard** | ✅ | ✅ | ❌ | 操作确认、选择菜单 |
| **feedCard** | ✅ | ❌ | ❌ | 多图文列表 |

⚠️ **注意**: Webhook 方式不支持纯图片(image)类型，需要图片请使用 Link 或 FeedCard

---

## 快速开始

### 1. 基础发送

```bash
# 文本消息
python3 ~/.copaw/skills/dingtalk-message-style/scripts/send_dingtalk.py text "内容"

# Markdown（支持表格）
python3 .../send_dingtalk.py markdown "标题" "### 内容\n| 列1 | 列2 |\n|-----|-----|\n| A | B |"

# Link 卡片（带图片）
python3 .../send_dingtalk.py link "标题" "描述" "图片URL" "跳转URL"

# 单按钮 ActionCard
python3 .../send_dingtalk.py action "标题" "描述" "按钮标题" "按钮URL"

# 多按钮 ActionCard（横向排列）
python3 .../send_dingtalk.py action_multi "标题" "描述" '[{"title":"按钮1","actionURL":"url1"},{"title":"按钮2","actionURL":"url2"}]' --btn-orientation 1

# 多图文 FeedCard
python3 .../send_dingtalk.py feed '[{"title":"标题1","picURL":"图片1","messageURL":"链接1"}]'
```

### 2. @提醒功能

```bash
# @所有人
python3 .../send_dingtalk.py markdown "标题" "内容 @所有人" --at-all

# @指定手机号
python3 .../send_dingtalk.py markdown "标题" "内容 @138xxxx" --at-mobiles "138xxxx,139xxxx"

# @指定用户ID
python3 .../send_dingtalk.py text "内容" --at-user-ids "user1,user2"
```

### 3. 使用模板

```bash
# 查看模板列表
python3 ~/.copaw/skills/dingtalk-message-style/scripts/smart_send.py --list

# 商品推荐
python3 .../smart_send.py --template goods_recommend --vars '{"商品名":"iPhone","价格":"5999","亮点":"最新款","描述":"性能强劲","图片URL":"...","商品链接":"..."}'

# 任务报告
python3 .../smart_send.py --template task_report --vars '{"时间":"2026-03-18","任务表格":"|任务|状态|\\n|A|✅|","完成数":"1","总数":"1","总结":"完成"}'

# 降价提醒
python3 .../smart_send.py --template price_alert --vars '{"商品名":"iPhone","原价":"6999","现价":"5999","降幅":"1000","图片URL":"...","商品链接":"..."}'
```

---

## 模板库

| 模板 | 类型 | 说明 |
|------|------|------|
| `goods_recommend` | Link | 单商品推荐 |
| `goods_list` | FeedCard | 多商品列表 |
| `price_alert` | Link | 降价提醒 |
| `task_report` | Markdown | 任务报告 |
| `order_status` | Markdown | 订单状态 |
| `daily_summary` | Markdown | 每日总结 |
| `meeting_notice` | ActionCard | 会议通知 |
| `confirm_action` | ActionCard | 操作确认 |
| `alert_notify` | Markdown | 告警通知 |
| `shopping_cart` | Markdown | 购物车提醒 |

---

## 智能格式选择

自动根据内容选择最佳格式：

```python
from smart_send import SmartSender

# 多商品 → FeedCard
sender = SmartSender()
sender.add_product("商品1", "图片1", "链接1", "¥99")
sender.add_product("商品2", "图片2", "链接2", "¥199")
sender.analyze_and_send()  # 自动选 FeedCard

# 单商品+图片+链接 → Link
sender = SmartSender()
sender.add_product("商品", "图片", "链接", "¥99", "描述")
sender.analyze_and_send()  # 自动选 Link

# 内容+@提醒 → Markdown
sender = SmartSender()
sender.set_title("告警")
sender.set_content("CPU超过90%")
sender.at(mobiles=["138xxxx"], at_all=False)
sender.analyze_and_send()  # 自动选 Markdown
```

---

## 按钮排列方向

ActionCard 多按钮支持两种排列：

```bash
# 竖直排列（默认）
--btn-orientation 0

# 横向排列
--btn-orientation 1
```

---

## 图片链接处理

淘宝图片 URL 需去掉 `_.webp` 后缀：

```python
# 自动处理
fix_taobao_image_url(url)  # xxx.jpg_.webp → xxx.jpg
```

---

## Markdown 支持的语法

| 语法 | 支持 | 说明 |
|------|:----:|------|
| 标题 `#` | ✅ | 支持 h1-h6 |
| 粗体 `**` | ✅ | |
| 引用 `>` | ✅ | |
| 链接 `[]()` | ✅ | |
| 代码 `` ` `` | ✅ | |
| 列表 `-` | ✅ | |
| 图片 `![]()` | ❌ | 请用 Link/FeedCard |

---

## 文件结构

```
~/.copaw/skills/dingtalk-message-style/
├── SKILL.md
├── _meta.json
├── scripts/
│   ├── send_dingtalk.py    # 基础发送
│   └── smart_send.py       # 智能发送+模板
└── templates/
    └── templates.json      # 模板定义
```

---

## 常见问题

### Q: 为什么图片不显示？
A: 
1. Markdown 不支持图片，请用 Link 或 FeedCard
2. 淘宝图片需去掉 `_.webp` 后缀

### Q: 如何@所有人？
A: 使用 `--at-all` 参数

### Q: 如何让按钮横向排列？
A: 使用 `--btn-orientation 1`

---

*版本: 1.1.0 | 更新: 2026-03-18*