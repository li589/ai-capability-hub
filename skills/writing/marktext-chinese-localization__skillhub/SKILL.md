---
name: marktext-hanhua
description: >
  MarkText 中文汉化技能。当用户要求汉化 MarkText、把 MarkText 改为中文、
  对 MarkText 进行汉化操作，或恢复 MarkText 英文版时触发本技能。
  本技能通过修改 app.asar 内部文件，替换 409 处 UI 文本，实现完整的中文界面。
version: 1.4.3
license: MIT
metadata:
  category: desktop-tool
  tags:
    - marktext
    - chinese-localization
    - desktop-app
  author: 金色巨龙
  created: "2026-04-27"
---

# MarkText 汉化技能

## 安装说明

1. 解压 `marktext-hanhua-skill.zip`，得到 `marktext-hanhua` 文件夹
2. 将整个 `marktext-hanhua` 文件夹放入 WorkBuddy 的技能目录：
   - **Windows**：`C:\Users\<你的用户名>\.workbuddy\skills\`
   - **macOS / Linux**：`~/.workbuddy/skills/`
3. 安装完成，无需重启，AI 下次对话会自动识别并使用本技能

**安装后目录结构应如下：**
```
~/.workbuddy/skills/
└── marktext-hanhua/
    ├── SKILL.md
    └── scripts/
        ├── hanhua-apply.js
        ├── hanhua-core.js
        └── hanhua-restore.js
```

## 使用方法

安装完成后，只需在对话中告诉 AI：

- **汉化 MarkText**：说「帮我汉化 MarkText」，AI 自动完成全部流程
- **恢复英文版**：说「恢复 MarkText 英文版」，AI 一键还原
- **补充遗漏词汇**：说「MarkText 有个地方没翻译」并发截图，AI 自动追加翻译后重新汉化

## 前提条件

1. **Node.js** 已安装（v16+）
2. **@electron/asar** 工具已全局安装：
   ```
   npm install -g @electron/asar
   ```
3. MarkText 已安装（支持 Windows / macOS）

## 技能脚本位置

本技能的脚本位于技能目录的 `scripts/` 文件夹：

| 脚本 | 功能 |
|------|------|
| `hanhua-apply.js` | 一键汉化（备份 → 解包 → 汉化 → 打包 → 替换） |
| `hanhua-core.js` | 核心翻译字典，包含 409 处文本映射（v1.4.1） |
| `hanhua-restore.js` | 恢复英文版 |

## 操作工作流

### 汉化 MarkText（最常用）

**步骤：**

1. **检查 asar 工具是否已安装**
   ```
   asar --version
   ```
   如果未安装：`npm install -g @electron/asar`

2. **运行汉化脚本**（需要管理员权限）

   Windows（PowerShell 管理员）：
   ```
   node "<技能目录>/scripts/hanhua-apply.js"
   ```
   或指定安装目录：
   ```
   node "<技能目录>/scripts/hanhua-apply.js" "D:\Program Files\MarkText"
   ```

   macOS（终端）：
   ```
   sudo node "<技能目录>/scripts/hanhua-apply.js"
   ```

3. **重启 MarkText** 查看效果

> **注意**：脚本会自动备份原始文件为 `app.asar.backup`，可随时恢复。

### 恢复英文版

```
node "<技能目录>/scripts/hanhua-restore.js"
```

### 手动执行（如脚本无法自动替换）

当自动脚本因权限问题失败时，按以下步骤手动操作：

```
# 1. 解包
asar extract "D:\Program Files\MarkText\resources\app.asar" C:\Temp\mt-src

# 2. 汉化
set HANHUA_UNPACKED_DIR=C:\Temp\mt-src
node "<技能目录>/scripts/hanhua-core.js"

# 3. 打包
asar pack C:\Temp\mt-src C:\Temp\app.asar.patched

# 4. 替换（管理员 cmd）
copy /Y C:\Temp\app.asar.patched "D:\Program Files\MarkText\resources\app.asar"
```

## 汉化覆盖范围（v1.4.1，409 处）

1. **菜单栏**：顶层菜单 + 所有子菜单（文件/编辑/段落/格式/视图/窗口/帮助/主题）
2. **右键菜单**：剪切/复制/粘贴/格式/图片等
3. **设置面板**（全覆盖）：
   - 通用（启动/侧边栏/排序/语言/缩放/自动保存）
   - 编辑器（宽度/代码块/写作行为/文件格式/文本方向/行尾格式/尾空行）
   - Markdown（列表/扩展/兼容性/图表/标题样式/前言格式）
   - 主题（自动调整）
   - 图片（路径/默认操作）
   - 快捷键（所有描述条目）
   - 拼写检查（所有选项）
4. **界面 UI**：
   - 表格操作（对齐/行列插入/删除/单元格合并）
   - 标签页右键（关闭/重命名/复制路径）
   - 搜索框（搜索/替换/全部替换/替换单个）
   - 段落菜单（标题1~6/提升降低/代码块/引用/公式/列表/水平线/前言）
   - 字数统计（字数/字符数/段落数）
   - 图表类型（Vega/流程图/时序图/PlantUML/Mermaid）
   - 图片工具栏（编辑/行内/链接/删除）
   - 通知消息（保存失败/粘贴错误/更新提示等）
   - 新文档段落选择器（全部选项）
   - 导出选项（通用/页眉页脚/主题/样式/页面/信息）
   - 更新对话框
   - 隐私声明/服务条款/反馈

## 升级后重新汉化

MarkText 升级后，直接再次运行 `hanhua-apply.js` 即可。
脚本设计为幂等操作：已有备份时不会覆盖备份，翻译字典直接应用在新版本上。

新版本如有新增词汇未被翻译，用户可截图反馈，向 `hanhua-core.js` 中的 `TRANSLATIONS` 字典追加条目后重新打包。

## 常见问题

| 问题 | 解决方案 |
|------|----------|
| `asar: command not found` | `npm install -g @electron/asar` |
| 替换失败（权限拒绝）| 以管理员/sudo 身份运行脚本 |
| 汉化后 MarkText 无法启动 | 运行 `hanhua-restore.js` 恢复英文版 |
| 找不到安装目录 | 传入路径参数：`node hanhua-apply.js "安装目录"` |
| 有新遗漏词汇 | 向 `hanhua-core.js` 的 `TRANSLATIONS` 追加映射条目 |

## 用户反馈

### 技能完成后的主动提示

当技能执行完成（汉化成功/恢复成功）时，AI 应主动提示用户有反馈渠道：

> 如果使用过程中发现问题，或者有遗漏的词汇需要补充，欢迎反馈，我会持续优化。

### 邮箱联系方式的触发条件

只有当用户明确表达了反馈意愿时（如"想反馈""有问题要反映""怎么联系作者"等），才提供邮箱：

> 可以通过邮箱联系我：shuaichewang@foxmail.com

### 禁止行为
- ❌ 不要主动显示完整邮箱地址
- ❌ 不要在技能执行前提示反馈渠道
- ❌ 不要在用户未表达反馈意愿时主动提供联系方式
