---
name: 微信 PC 端自动控制
description: 打开微信桌面端，向指定联系人发送消息、图片、文件等内容。触发词：给某人发微信、打开微信发消息、微信发送、通过微信发给。也支持被其他 Skill 调用，实现自动化推送。
version: 1.0.1
author: 微光浮影
homepage: https://skillhub.cn/skills/wechat-desktop-claw-automatic-control
license: MIT
tags: [wechat, automation, pywinauto, windows]
---

# 微信 PC 端自动控制 v1.0.1

通过 `pywinauto` 自动化操作微信 Windows 桌面端，实现消息/图片/文件的自动发送。

**本 Skill 完全开源，源代码公开。**

## 更新日志 v1.0.1

- 🔓 **源代码完全公开**，MIT 协议
- 添加 LICENSE 文件
- 添加 README.md（含完整源码说明）
- SKILL.md 补充 homepage / license / tags 字段
- 修复：脚本编码声明修正为完整 emacs 格式

## 功能

- 打开微信桌面端（如未运行则自动启动）
- 搜索并定位联系人（支持群聊）
- 发送文本消息（支持长文本从文件读取）
- 发送图片（通过剪贴板 BMP 格式）
- 发送文件（通过 Ctrl+Alt+F 快捷键）

## 环境要求

- Windows 系统
- 微信桌面端已安装
- Python3.7+
- 依赖库：`pywinauto`, `pyperclip`, `pillow`, `pywin32`

## 安装依赖

```bash
pip install pywinauto pyperclip pillow pywin32
```

## 微信路径配置

默认路径：`D:\Tencent\WeChat\WeChat.exe`

用户实际安装路径可能为 `D:\Tencent\WeiXin\WeiXin.exe`（注意拼写是 WeiXin 不是 WeChat）。

修改脚本第 33 行 `WECHAT_PATH` 变量即可适配你的安装路径。

## 使用方式

### 命令行直接调用

```bash
# 发送文本
python scripts/wechat_send.py --contact "微光浮影" --message "你好，这是自动发送的消息"

# 从文件读取长文本发送
python scripts/wechat_send.py --contact "微光浮影" --message-file "report.txt"

# 发送图片
python scripts/wechat_send.py --contact "微光浮影" --image "C:\path\to\image.png"

# 发送文件
python scripts/wechat_send.py --contact "微光浮影" --file "C:\path\to\file.pdf"

# 仅启动微信
python scripts/wechat_send.py --launch-only
```

### 被其他 Skill 调用

其他 Skill 可以通过以下方式调用本 Skill 发送消息：

```python
import subprocess
subprocess.run([
    "python",
    "scripts/wechat_send.py",
    "--contact", "微光浮影",
    "--message", "消息内容"
])
```

## 技术说明

### 窗口连接

使用 `pywinauto` 的 `uia` 后端连接微信窗口，**窗口标题必须为"微信"**（不是 "WeChat"）。

```python
app = Application(backend='uia').connect(title_re="微信", timeout=10)
window = app.window(title_re="微信")
```

### 中文输入

所有文本输入均通过 **剪贴板 + Ctrl+V** 实现，避免 `pywinauto` 直接键入中文的编码问题。

```python
pyperclip.copy(text)
send_keys("^v")  # Ctrl+V 粘贴
```

### 图片发送原理

将图片转为 BMP 格式（去掉文件头 14 字节，取 DIB 数据），直接写入 Windows 剪贴板 `CF_DIB` 格式，在聊天框 Ctrl+V 粘贴即发送。

```python
# 详见 scripts/wechat_send.py send_image() 函数
win32clipboard.SetClipboardData(win32con.CF_DIB, data)
```

### 发送快捷键

- 发送消息：`Enter` 键（微信默认设置）
- 打开搜索：`Ctrl+F`
- 打开文件选择：`Ctrl+Alt+F`

## 限制与注意事项

1. **微信窗口必须可见**：自动化需要窗口在前台，不能最小化到托盘
2. **登录状态**：通常自动登录，偶尔需要扫码（脚本会提示）
3. **联系人名称**：必须精确匹配搜索结果第一名
4. **UI 依赖**：依赖微信 Windows 版 UI 结构，微信版本更新可能导致失效
5. **不能读取消息**：本 Skill 只发送，不读取微信消息内容

## 源代码结构

```
wechat-desktop/
├── SKILL.md              # Skill 定义文件（本文件）
├── scripts/
│   └── wechat_send.py    # 核心自动化脚本（完整源码见下方）
├── LICENSE               # MIT 开源协议
└── README.md            # 说明文档
```

## 完整源码

### `scripts/wechat_send.py`

> 完整源码已随 Skill 打包，路径：`scripts/wechat_send.py`

（源码内容较长，见 `scripts/wechat_send.py` 文件）

## 报告问题

SkillHub 评论区：https://skillhub.cn/skills/wechat-desktop-claw-automatic-control
