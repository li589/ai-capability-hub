---
name: video-to-manual
display_name: 鼎华eMES 智能交付助手-视频生成操作手册
display_name_en: Video to Operation Manual
description: Generate Word operation manuals/SOPs with embedded screenshots from
  screen-recorded videos (.mp4) and step descriptions. For implementation, IT
  ops and technical support.
description_zh: 根据操作录屏视频（.mp4）和文字描述，自动生成带截图的 Word 版操作手册/SOP，适用于系统实施、运维、技术支持场景。
description_en: Generate Word operation manuals/SOPs with embedded screenshots
  from screen-recorded videos (.mp4) and step descriptions. For implementation,
  IT ops and technical support.
category: writing
version: 1.0.0
author: Digihua
permissions:
  - file_read
  - file_write
  - network_request
  - process_exec
disable-model-invocation: true
---

# 智能交付助手-视频生成操作手册

## 概述

将视频录屏（如向日葵远程控制、屏幕录制等生成的 .mp4 文件）结合用户的文字描述，自动生成结构化的 Word 操作手册文档。文档包含：
- 标题页、目录结构、分章节内容
- 嵌入关键步骤截图（从视频中提取）
- 表格、代码块、提示框等格式化内容
- 自动对 IP 地址、密码等敏感信息进行脱敏处理（替换为 XXXX 占位符）

## 工作流程

此 skill 适用于以下完整流程：

```
用户提供视频文件(.mp4) + 操作说明(步骤描述) + 可选参考文档
          │
          ▼
  Phase 1: 分析 —— 理解视频内容与用户意图
          │
          ├── 单视频 → 直接确认文档结构
          │
          └── 多视频 → 按用户标注顺序处理，推断合并/拆分
                （用户已标注视频顺序，优先遵循，不反问）
          │
          ▼
  Phase 2: 截图 —— 从视频中提取关键帧，匹配用户描述的每一步
          │
          ▼
  Phase 3: 生成 —— 用 generate_manual.py 脚本输出 Word 文档
```

## Phase 1：分析视频与用户意图

### 1.1 获取视频基本信息
```bash
ffprobe -v quiet -print_format json -show_format -show_streams <video_path>
```
记录视频时长、分辨率，用于后续截图策略。

### 1.2 确认用户意图
用户通常会提供以下材料之一或多种：

- **视频文件**：.mp4 录屏
- **步骤描述**：文字说明视频展示了哪些操作步骤
- **参考文档**：已有的 Markdown/Word 文档作为内容参考或格式参考

**关键原则**：以用户的步骤描述为**主线索**，视频帧仅用于确认细节和截取对应画面。如果用户描述不够详细，基于视频帧分析后向用户确认补充，不要自行臆断。

### 1.3 明确文档结构
与用户确认最终文档的章节结构。标准结构参考：

- 一、场景概述（问题/背景/目标）
- 二、操作步骤（逐步展开，每步配截图）
- 三、总结与原理（可选）
- 四、常见问题与排查（可选）
- 五、附录（地址、服务、命令速查等）

## Phase 2：从视频提取截图

### 2.1 环境准备
确保 `imageio-ffmpeg` 包可用：
```bash
pip install imageio-ffmpeg -i https://pypi.tuna.tsinghua.edu.cn/simple
```

ffmpeg 路径通过 Python 获取：
```python
import imageio_ffmpeg
ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
```

### 2.2 粗略扫描（30 秒间隔）
```bash
ffmpeg -i <video> -vf "fps=1/30" <output_dir>/frame_%04d.png -y
```

### 2.3 匹配步骤与时间戳
- 逐一查看粗略帧，找到每个步骤对应的画面区间
- 对于时间跨度大的场景，用更小的步长（5s / 1s）做精细扫描
- 使用 Read 工具直接查看 PNG 帧内容，确认画面正确

### 2.4 提取最终截图
在精确时间戳提取截图，保存到 `final_screenshots/` 目录：
```bash
ffmpeg -ss <seconds> -i <video> -vframes 1 <output>.png -y
```

截图命名规则：`<两位序号>-<步骤英文简述>.png`
示例：`01-seq-error-log.png`、`02-platform-config.png`、`03-nacos-config-edit.png`

### 2.5 截图质量检查
- 确认每张截图画面清晰、内容正确
- 对应到用户描述的每一步操作
- 如果某张截图时戳不对，用更细粒度重新扫描

## Phase 3：生成 Word 文档

### 3.1 环境准备
```bash
pip install python-docx -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 3.2 创建 JSON 配置文件
创建一个 JSON 配置文件，描述文档的完整结构。配置说明详见 `references/workflow.md`。

JSON 配置的核心元素类型：

| 类型 | 用途 |
|------|------|
| `heading` | 章节标题，支持 level 1-3 |
| `para` | 普通段落，支持 bold/color |
| `note` | 蓝色加粗提示信息 |
| `bullet` | 无序列表 |
| `numbered` | 有序列表（编号步骤） |
| `code` | 等宽字体代码块 |
| `table` | 表格（headers + rows） |
| `screenshot` | 嵌入截图（file + caption） |
| `page_break` | 分页符 |

示例配置片段：
```json
{
  "title": "操作手册标题",
  "subtitle": "副标题：流程简述",
  "date_line": "文档日期：2026-XX-XX    基于录屏 xxx.mp4 整理",
  "output": "output.docx",
  "sections": [
    {"type": "heading", "text": "一、章节标题", "level": 1},
    {"type": "para", "text": "正文内容...", "bold": false},
    {"type": "note", "text": "关键提示信息"},
    {"type": "screenshot", "file": "01-xxx.png", "caption": "图：截图说明"},
    {"type": "page_break"}
  ]
}
```

### 3.3 运行生成脚本
```bash
python scripts/generate_manual.py config.json -o output.docx --screenshot-dir ./final_screenshots
```

### 3.4 验证输出
- 确认 .docx 文件大小合理（嵌入截图后通常在 2-8 MB）
- 向用户说明文档已生成，提供文件路径

### 3.5 展示结果
使用 `present_files` 展示生成的 .docx 文件。

## 敏感信息脱敏规则

文档中**必须**对以下信息进行脱敏处理：

- **IP 地址** → `XXXX.XXXX.XXXX.XXXX`
- **端口号（非标准）** → `XXXX`
- **密码/密钥** → 直接删除不输出
- **服务器域名** → `XXXX`
- **内部 URL** → 保留路径结构但脱敏主机部分，如 `http://XXXX:XXXX/client/index.html`

脱敏在编写内容（JSON 配置中的文字）时直接处理，不在脚本中自动替换。

## 多视频处理（合并 / 拆分）

当用户提供**多个视频**时（如文件夹中包含多个 .mp4 文件）：

### 视频顺序：以用户标注为准（最高优先级）

用户会在消息中显式标注视频顺序，例如：
- 文件名标注：`视频1-平台更新.mp4`、`视频2-版更.mp4`、`视频3-排查导入.mp4`
- 文字标注："第一个视频是平台更新，第二个视频是版本更新"

**处理规则**：
- 用户标注了什么顺序，就按什么顺序处理，**不要反问确认顺序**
- 只有当用户完全没有标注顺序时，才按文件名自然排序（数字序列 → 修改时间）
- 用户说"视频二放前面、视频一放后面"，直接按此顺序，不需要额外确认

### 合并 vs 拆分

优先从用户的话术中推断，无需每次都问：

| 用户说法 | 推断意图 |
|---|---|
| "帮我整理成操作文档"（单数 + 多视频） | 默认合并为一个文档 |
| "每个视频单独一份" / "拆成多个文档" | 拆分为多个独立文档 |
| "把版更的部分单独拆出来" | 从多视频中拆分指定部分 |

**仅在以下情况才反问**：用户既没说明合并也没说明拆分，且视频内容关联性不明确。

### 合并模式

```json
// 一个 JSON 配置，多个视频的章节按用户指定的顺序编排
{
  "title": "eMES 系统运维操作文档",
  "sections": [
    {"type": "heading", "text": "第一部分：更新低代码平台", "level": 1},
    // ... 视频一的章节内容（用户标注的第一个视频） ...
    {"type": "page_break"},
    {"type": "heading", "text": "第二部分：eMES 系统版更", "level": 1},
    // ... 视频二的章节内容（用户标注的第二个视频） ...
  ]
}
```

### 拆分模式

为每个视频分别创建独立的 JSON 配置，逐一调用 `generate_manual.py` 生成独立文档：

```
输出目录/
├── 操作手册一_平台更新.docx
├── 操作手册二_系统版更.docx
└── 操作手册三_导入报错排查.docx
```

各文档截图放在各自的 `final_screenshots/` 子目录中，避免文件名冲突。

## 依赖

- **Python**: 3.x（通过 WorkBuddy 管理的 Python 环境）
- **imageio-ffmpeg**: 视频帧提取
- **python-docx**: Word 文档生成
- **ffprobe/ffmpeg**: 通过 imageio-ffmpeg 提供的二进制文件

## 资源文件

- `scripts/generate_manual.py`：Word 文档生成脚本，接受 JSON 配置文件
- `references/workflow.md`：详细的工作流参考，包含 JSON 配置完整规范
