# 智能自动脱敏工具

> 保护用户隐私的智能脱敏工具，支持文本、JSON、图片的自动敏感信息识别与脱敏

---

## 🤖 Agent 一键安装

将以下内容发送给你的龙虾（Agent），即可自动安装并启用：

```
请帮我安装智能自动脱敏工具：

1. 从 GitHub 下载本项目：https://github.com/{你的用户名}/smart-desensitize-tool

2. 解压到 ./工具/脱敏工具/ 目录

3. 导入测试：from smart_desensitize_skill import SmartDesensitizer

工具会自动完成初始化，以后新建 agent 时脱敏规则也会自动生效！
```

---

## ✨ 功能特性

| 功能 | 说明 |
|------|------|
| 📝 文本脱敏 | 手机号、身份证、银行卡、邮箱等 9 种类型 |
| 📊 JSON 脱敏 | 自动识别敏感字段并处理 |
| 🖼️ 图片脱敏 | OCR 识别敏感文字 + 区域模糊 |
| ⚡ 智能策略 | 根据图片大小自动选择处理模式 |
| 🔄 自动初始化 | 新建 agent 时自动启用脱敏规则 |
| 🗑️ 自动清理 | 脱敏后自动删除原图 |

## 📋 支持脱敏的敏感信息

| 类型 | 示例 | 脱敏后 |
|------|------|--------|
| 手机号 | 13812345678 | 138****5678 |
| 身份证 | 110101199001011234 | 110101********1234 |
| 银行卡 | 6222021234567890123 | 6222****1234 |
| 邮箱 | test@example.com | te****@example.com |
| 姓名 | 张三丰 | 张** |
| 地址 | 北京市海淀区中关村大街1号 | 北********* |
| QQ号 | 12345678 | 123****78 |
| 微信号 | wechat123 | wec****23 |
| 车牌号 | 京A12345 | 京A****5 |

---

## 🚀 快速开始

### 安装

```bash
# 方法一：直接下载 ZIP
# 下载后解压到 ./工具/脱敏工具/

# 方法二：Git 克隆
cd ./工具/
git clone https://github.com/{你的用户名}/smart-desensitize-tool.git 脱敏工具
```

### 初始化

首次导入时自动完成初始化：

```python
from smart_desensitize_skill import SmartDesensitizer

# 输出：
# ✓ 全局脱敏配置已存在: ./基础设定/DESENSITIZE_RULES.md
# ✓ MEMORY.md 已包含脱敏规则
```

### 使用示例

```python
from smart_desensitize_skill import SmartDesensitizer

# 文本脱敏
text = "我的手机号是13812345678，身份证是110101199001011234"
result = SmartDesensitizer().desensitize_text(text)
# 输出: 我的手机号是138****5678，身份证是110101********1234

# JSON 脱敏
import json
data = {"name": "张三", "phone": "13812345678"}
result = SmartDesensitizer().desensitize_json(data)
# 输出: {"name": "张**", "phone": "138****5678"}
```

---

## 📦 文件结构

```
脱敏工具/
├── smart_desensitize_skill.py   # 主程序（含自动初始化）
├── deep_desensitize_skill.py    # 标准版深度学习脱敏器
├── fast_deep_desensitize_skill.py # 高性能版脱敏器
├── skill.json                   # Skill 配置
├── SOP.md                       # 标准操作流程
├── INSTALL.md                   # 安装指南
└── README.md                    # 本文件
```

---

## 📋 依赖说明

### 核心功能（无需额外依赖）

- ✅ 文本脱敏
- ✅ JSON 脱敏
- ✅ 图片基础模糊

### 增强功能（可选依赖）

```bash
# OCR 文字识别（图片中文字脱敏）
pip install easyocr

# 或使用 PaddleOCR（中文效果更好）
pip install paddleocr

# 人脸检测
pip install opencv-python-headless
```

---

## 🔧 配置说明

### 自动创建的配置文件

工具首次导入时会自动创建：

1. **`./基础设定/DESENSITIZE_RULES.md`** — 全局脱敏配置
   - 新建 agent 时会继承此文件
   - 包含脱敏规则、例外情况等

2. **更新 `./MEMORY.md`** — 添加脱敏规则到记忆

### 脱敏流程

```
用户发送内容 → 检查是否需要脱敏 → 执行脱敏 → 删除原图（如有） → 处理后续任务
```

### 例外情况

以下情况不会脱敏：
- 用户明确要求"不要脱敏"
- 已知的安全/测试数据

---

## ❓ 常见问题

**Q: 新建 agent 后脱敏规则丢失怎么办？**

A: 工具已内置自检功能，首次导入时会自动创建配置。只需确保工具目录存在，然后导入一次：
```python
from smart_desensitize_skill import SmartDesensitizer
```

**Q: 图片脱敏后文字还可见？**

A: 需要安装 OCR 依赖：
```bash
pip install easyocr
```

**Q: 如何临时关闭脱敏？**

A: 告诉 Agent "这条消息不要脱敏"

**Q: 支持哪些图片格式？**

A: JPEG、PNG、GIF（通过 base64 编码传入）

---

## 📄 License

MIT License

---

## 🙏 致谢

感谢所有为隐私保护做出贡献的开发者！
