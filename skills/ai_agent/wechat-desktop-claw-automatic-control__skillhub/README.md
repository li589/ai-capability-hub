# 微信 PC 端自动控制 Skill

> 本 Skill 是 OpenClaw / WorkBuddy 的插件，通过 `pywinauto` 自动化操作微信 Windows 桌面端。

## ✨ 功能

| 功能 | 说明 |
|------|------|
| 打开微信 | 如未运行自动启动，已运行则直接连接 |
| 搜索联系人 | 支持昵称、备注名、群名 |
| 发送文本 | 支持长文本（从文件读取） |
| 发送图片 | 通过剪贴板 DIB 格式直接粘贴 |
| 发送文件 | 通过微信文件选择对话框 |
| 被其他 Skill 调用 | 可作为自动化推送通道 |

## 📦 安装

### 方式一：SkillHub（推荐）

```bash
skillhub install wechat-desktop-claw-automatic-control
```

### 方式二：手动安装

将本 Skill 目录复制到 OpenClaw workspace skills 目录：

```bash
cp -r wechat-desktop ~/.openclaw/workspace/skills/wechat-desktop
```

## 🔧 依赖安装

```bash
pip install pywinauto pyperclip pillow pywin32
```

## ⚙️ 配置

编辑 `scripts/wechat_send.py` 第 33 行，修改微信安装路径：

```python
WECHAT_PATH = "D:/Tencent/WeiXin/WeiXin.exe"  # 改为你的路径
```

常见路径：
- `C:\Program Files (x86)\Tencent\WeChat\WeChat.exe`
- `D:\Tencent\WeiXin\WeiXin.exe`（用户实际路径，注意拼写是 WeiXin）

## 🚀 使用方法

### 命令行直接调用

```bash
# 发送文本
python scripts/wechat_send.py --contact "微光浮影" --message "你好！"

# 从文件读取长文本发送（适合报告/长消息）
python scripts/wechat_send.py --contact "微光浮影" --message-file "report.txt"

# 发送图片
python scripts/wechat_send.py --contact "微光浮影" --image "C:\screenshot.png"

# 发送文件
python scripts/wechat_send.py --contact "微光浮影" --file "C:\document.pdf"

# 仅启动微信（不发送）
python scripts/wechat_send.py --launch-only
```

### 在 OpenClaw / WorkBuddy 中触发

对话中说出以下触发词即可：

- "给 XXX 发微信：消息内容"
- "打开微信发消息给 XXX"
- "通过微信发给 XXX：内容"
- "微信发送 XXX"

### 被其他 Skill 调用

```python
import subprocess

subprocess.run([
    "python",
    "scripts/wechat_send.py",
    "--contact", "微光浮影",
    "--message", "B站播报内容..."
])
```

## 🔬 技术原理

### 窗口连接

使用 `pywinauto` 的 `uia` 后端，窗口标题必须为**中文"微信"**（不是 "WeChat"）：

```python
app = Application(backend='uia').connect(title_re="微信", timeout=10)
```

### 中文输入方案

直接键入中文会出现编码问题，统一采用 **剪贴板 + Ctrl+V** 方案：

```python
pyperclip.copy(text)
send_keys("^v")  # Ctrl+V 粘贴
```

### 图片发送原理

将图片转为 BMP 格式，去掉前 14 字节文件头（保留 DIB 数据），写入 Windows 剪贴板 `CF_DIB` 格式，在聊天框 Ctrl+V 即可发送图片。

```python
# 核心代码（详见 scripts/wechat_send.py）
output = io.BytesIO()
img.convert("RGB").save(output, "BMP")
data = output.getvalue()[14:]  # 去掉 BMP 文件头
win32clipboard.SetClipboardData(win32con.CF_DIB, data)
```

## ⚠️ 注意事项

1. **微信窗口必须可见**（不能最小化到托盘）
2. **登录状态**：通常自动登录，偶尔需要扫码确认
3. **联系人名称**：搜索精确匹配第一个结果
4. **UI 依赖**：依赖微信 Windows 版 UI 结构，版本更新可能失效
5. **仅发送，不读取**：本 Skill 不读取微信消息内容

## 📁 文件结构

```
wechat-desktop/
├── SKILL.md              # Skill 定义（OpenClaw 识别用）
├── scripts/
│   └── wechat_send.py    # 核心自动化脚本
├── LICENSE               # MIT 开源协议
└── README.md            # 本文件
```

## 🐛 问题反馈

- SkillHub 评论区：https://skillhub.cn/skills/wechat-desktop-claw-automatic-control
- 或联系作者：微光浮影

## 📄 协议

MIT License — 自由使用、修改、分发。详见 [LICENSE](LICENSE) 文件。
