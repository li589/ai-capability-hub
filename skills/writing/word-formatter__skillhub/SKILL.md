---
title: "Word 智能排版助手 - SKILL.md"
summary: "Word 智能排版 Skill 完整文档 v2.0"
author: "周博远"
version: "2.0.0"
skill_id: "word-formatter"
triggers:
  - intent: ["排版", "格式化", "美化", "整理 Word", "套模板", "公文排版", "国标排版"]
  - explicit: ["@Word 排版", "@word-formatter"]
inputs:
  - name: "source_file"
    type: "file"
    required: true
    description: "待排版的 Word 文档（.docx/.doc/.md）"
  - name: "template_id"
    type: "string"
    required: false
    default: "business_default"
    description: "模板 ID（如 gov_tongzhi/biz_white_paper/simple_minimal）"
  - name: "gov_doctype"
    type: "enum"
    enum: ["通知", "报告", "请示", "批复", "纪要", "函", "意见", "通报", "公告", "决定"]
    required: false
    description: "公文类型（template_id 以 gov_ 开头时生效）"
  - name: "format_options"
    type: "object"
    required: false
    description: "格式选项（scope/keep_content/gov_check/generate_diff_report）"
outputs:
  - name: "formatted_file"
    type: "file_link"
    description: "排版后的 Word 文档"
  - name: "diff_report"
    type: "file_link"
    description: "排版差异对比报告（Markdown）"
  - name: "gov_check_report"
    type: "file_link"
    description: "公文国标校验报告（仅公文模板）"
  - name: "summary"
    type: "string"
    description: "排版操作摘要"
  - name: "md_archive_path"
    type: "string"
    description: "Markdown 归档路径"
---

# 📘 Word 智能排版助手 v2.0

> 上传 Word → 自动识别结构 → 套用模板 → 智能美化 → 输出规范化 Word + 排版对比报告 + MD 归档

---

## 👥 受众说明

| 用户类型 | 使用方式 | 推荐模板 |
|---------|---------|----------|
| **个人用户** | 日常文档排版，上传即可自动排版 | simple_minimal / simple_modern |
| **政府/事业单位** | 公文排版，严格遵循国标 | gov_tongzhi / gov_baogao 等 |
| **企业用户** | 商务文档排版，专业报告 | biz_report / biz_white_paper |
| **学术研究者** | 论文排版，符合学术规范 | acad_paper_cn / acad_thesis |
| **团队协作** | 团队共用，自定义模板统一风格 | custom/* (用户自定义) |

> 如果你是第一次使用，从"新手 30 秒上手"开始。如果你是公文用户，直接跳到"公文排版深度支持"。

## 🛠️ 定制化使用指南

### 用户偏好设置
在 `config/user_profile.md` 中配置个人偏好，Skill 会在每次排版时自动应用：
```yaml
# 示例：用户偏好配置
user_name: "张三"
company: "XX公司"
default_template: "biz_report"  # 默认模板
preferred_font: "微软雅黑"      # 偏好字体
keep_history_days: 30            # 保留历史天数
```

### 自定义模板上传
```bash
# 1. 上传参考文档作为模板基准
"以这份文档的风格为模板，命名为 my_style，保存到 custom/"
# 2. 基于自定义模板排版
@skill:word-formatter source_file="新文档.docx" template_id="my_style"
```

### 场景参数传递
```bash
# 完整参数示例
@skill:word-formatter source_file="报告.docx" template_id="biz_report" format_options='{"scope":"full", "keep_tables":true, "auto_toc":true}'
```

## 🚀 新手 30 秒上手

```markdown
# 场景 1：普通文档排版
"把 项目报告.docx 排成商务风格"

# 场景 2：公文排版（自动识别公文类型）
"把 省政府通知.docx 按公文国标排版"

# 场景 3：多模板对比
"把 AI行业报告.docx 同时输出商务、极简、创意三种风格"

# 场景 4：自定义模板
"上传 我的模板参考.docx， based on 这个风格帮我排版 新文档.docx"
```

**AI 会自动：**
1. 解析文档结构（标题/段落/表格/图片）
2. 匹配最佳模板
3. 应用排版规则（字体/字号/行距/段距）
4. 生成差异对比报告
5. Markdown 归档

---

## 📋 能力边界（重要！）

| 类别 | 支持 | 不支持 |
|------|------|--------|
| **输入格式** | ✅ .docx / .doc / .md | ❌ .pdf / .pages / .wps |
| **输出格式** | ✅ .docx | ❌ .pdf / .html（规划中） |
| **公文标准** | ✅ GB/T 9704-2012 完整支持 | ❌ 地方政府特殊格式（需自定义） |
| **模板数量** | ✅ 28+ 套（6 大类） | ❌ 无限自定义（需手动上传参考稿） |
| **字体处理** | ✅ 自动替换缺失字体 | ❌ 自动安装字体（需手动安装） |
| **表格美化** | ✅ 自动调整列宽/边框/底纹 | ❌ 复杂合并单元格逻辑（保留原样） |
| **图片处理** | ✅ 调整大小/位置/环绕方式 | ❌ 图片内容识别/裁剪/滤镜 |
| **多语言** | ✅ 中文/英文/中英混排 | ❌ 从右到左语言（阿拉伯语等） |
| **批量处理** | ✅ 同一模板批量处理多文档 | ❌ 不同模板批量处理（需多次调用） |

---

## 🏛️ 公文排版深度支持（v2.0 核心）

### 适用国家标准
- **GB/T 9704-2012** 党政机关公文格式（核心）
- **GB/T 9704-1999** 旧版国家行政机关公文格式（兼容）
- **中办发〔2012〕14 号** 党政机关公文处理工作条例
- **GB/T 7714-2015** 参考文献著录规则

### 支持的文种（15 种）
| 文种 | 用途 | 优先级 | 模板 ID |
|------|------|--------|----------|
| 决议 | 重大决策 | P0 | gov_juey |
| 决定 | 重要事项决定 | P0 | gov_jueding |
| 命令（令） | 强制性措施 | P0 | gov_mingling |
| 公报 | 重要决定公开发布 | P0 | gov_gongbao |
| 公告 | 法定事项告知 | P0 | gov_gonggao |
| 通告 | 应遵守事项 | P0 | gov_tonggao |
| 意见 | 见解/处理办法 | P0 | gov_yijian |
| **通知** | **转发/部署/任免** | **P0** | **gov_tongzhi** |
| **通报** | **表彰/批评/情况** | **P0** | **gov_tongbao** |
| **报告** | **汇报工作/反映情况** | **P0** | **gov_baogao** |
| **请示** | **请求批准** | **P0** | **gov_qingshi** |
| **批复** | **答复下级请示** | **P0** | **gov_pifu** |
| **议案** | **提请审议** | **P0** | **gov_yian** |
| **函** | **不相隶属机关商洽** | **P0** | **gov_han** |
| **纪要** | **会议议定事项** | **P0** | **gov_jiyao** |

> ⭐ 标记为最高频文种，MVP 必交付

### GB/T 9704-2012 版式规范（核心规则）

```yaml
# 页面设置
paper: A4 (210mm × 297mm)
margin:
  top: 37mm    # 上 3.7cm（白边）
  bottom: 35mm # 下 3.5cm
  left: 28mm   # 左 2.8cm（订口）
  right: 26mm  # 右 2.6cm
header_distance: 0
footer_distance: 0

# 版心
content_area: 156mm × 225mm

# 行字数
chars_per_line: 28  # 每行 28 字
lines_per_page: 22  # 每页 22 行

# 字体规范
fonts:
  份号: "宋体 4 号"
  密级和保密期限: "黑体 3 号"
  紧急程度: "黑体 3 号"
  发文机关标志: "方正小标宋简体 红色"
  发文字号: "仿宋_GB2312 3 号"
  签发人: "仿宋_GB2312 3 号 + 黑体 3 号(姓名)"
  标题: "方正小标宋简体 2 号"
  主送机关: "仿宋_GB2312 3 号"
  正文: "仿宋_GB2312 3 号"
  一级标题: "黑体 3 号"
  二级标题: "楷体_GB2312 3 号"
  三级标题: "仿宋_GB2312 3 号 加粗"
  四级标题: "仿宋_GB2312 3 号"
  附件说明: "仿宋_GB2312 3 号"
  发文机关署名: "仿宋_GB2312 3 号"
  成文日期: "仿宋_GB2312 3 号"
  印章: "红色"
  附注: "仿宋_GB2312 3 号"
  抄送机关: "仿宋_GB2312 4 号"
  印发机关和日期: "仿宋_GB2312 4 号"
  页码: "阿拉伯数字 4 号半角宋体"

# 段落
paragraph:
  line_spacing: 28pt 固定值
  first_line_indent: 2 字符
  alignment: justify

# 红头
red_header:
  separator_line:
    color: 红色
    width: 0.35mm  # 武文线
    length: 156mm  # 等于版心宽度
    position: 发文字号下空一行

# 页码
page_number:
  position: 版心下边缘之下一行
  alignment_odd: 右空一字
  alignment_even: 左空一字
  format: "— 1 —"  # 数字两侧加一字线
  blank_page: 空白页不标页码

# 印章
seal:
  color: 红色
  position: 成文日期处
  rule: 骑年盖月

# 附件
attachment:
  marker_position: 正文下空一行 左空二字
  format: "附件：1.xxxx"
  page_break: 附件另起页
```

### 公文结构识别能力

| 识别项 | 方法 | 准确率目标 |
|--------|------|------------|
| 标题（关于…的××） | 正则 + LLM | ≥ 98% |
| 主送机关（冒号结尾段落） | 启发式 | ≥ 95% |
| 一级标题 "一、二、三、" | 正则 | 100% |
| 二级标题 "（一）（二）" | 正则 | 100% |
| 三级标题 "1. 2. 3." | 正则 + 上下文 | ≥ 95% |
| 附件说明 | 关键词 "附件：" | 100% |
| 落款机关 + 日期 | 末尾段位置识别 | ≥ 95% |
| 抄送机关 | 关键词 "抄送：" | 100% |
| 印发机关 | 末尾位置识别 | ≥ 90% |

### 公文专属功能

| 编号 | 功能 | 优先级 |
|------|------|--------|
| GF01 | 自动生成红头（发文机关 + 发文字号 + 武文线） | P0 |
| GF02 | 标题居中 + 2 号小标宋简体 | P0 |
| GF03 | 正文 3 号仿宋 + 固定行距 28pt | P0 |
| GF04 | 四级标题字体严格按国标 | P0 |
| GF05 | 自动设置 A4 + 国标页边距 | P0 |
| GF06 | 自动插入页码（— 1 — 格式） | P0 |
| GF07 | 成文日期阿拉伯数字格式化 | P0 |
| GF08 | 附件另起页 + 附件标识 | P0 |
| GF09 | 抄送机关 + 印发机关版记 | P0 |
| GF10 | 红色印章占位（待用户后续盖章） | P0 |
| GF11 | 份号 / 密级 / 紧急程度三要素 | P1 |
| GF12 | 公文校验（缺项检测 + 国标对照） | P0 |

---

## 🎨 20+ 风格模板库（v2.0 核心）

### 模板分类总览

```
templates/
├── gov/          # 公文类（10）
│   ├── gov_tongzhi.md      # 通知
│   ├── gov_baogao.md      # 报告
│   ├── gov_qingshi.md     # 请示
│   ├── gov_pifu.md        # 批复
│   ├── gov_jiyao.md       # 会议纪要
│   ├── gov_han.md         # 函
│   ├── gov_yijian.md      # 意见
│   ├── gov_tongbao.md     # 通报
│   ├── gov_gonggao.md     # 公告
│   └── gov_jueding.md     # 决定
├── business/     # 商务类（5）
│   ├── biz_report.md           # 商务报告
│   ├── biz_proposal.md        # 项目建议书
│   ├── biz_contract.md        # 合同协议
│   ├── biz_manual.md          # 商务手册
│   └── biz_white_paper.md    # 白皮书
├── academic/     # 学术类（4）
│   ├── acad_paper_cn.md      # 中文论文
│   ├── acad_paper_en.md      # 英文论文（IEEE/APA）
│   ├── acad_thesis.md        # 毕业论文（本/硕/博）
│   └── acad_review.md        # 综述
├── publish/      # 出版类（3）
│   ├── pub_book.md           # 图书
│   ├── pub_magazine.md      # 杂志
│   └── pub_brochure.md      # 宣传册
├── creative/     # 创意类（3）
│   ├── creative_lite.md      # 轻设计
│   ├── creative_dark.md      # 暗黑风
│   └── creative_colorful.md  # 多彩活泼
└── simple/       # 简洁类（3）
    ├── simple_minimal.md     # 极简白
    ├── simple_modern.md      # 现代简约
    └── simple_clean.md       # 清爽中性
```

> 📌 MVP 必交付 12 套（P0），其余作为 P1/P2 逐步补充

### 模板风格速览

| 编号 | 模板 ID | 名称 | 风格 | 适用场景 | 优先级 |
|------|---------|------|------|----------|--------|
| 1 | gov_tongzhi | 通知 | 严肃/红头/仿宋 | 党政机关通知 | P0 |
| 2 | gov_baogao | 报告 | 严肃/红头/仿宋 | 工作汇报 | P0 |
| 3 | gov_qingshi | 请示 | 严肃/红头/仿宋 | 上行文 | P0 |
| 4 | gov_pifu | 批复 | 严肃/红头/仿宋 | 下行答复 | P0 |
| 5 | gov_jiyao | 会议纪要 | 严肃/蓝头/仿宋 | 内部会议 | P0 |
| 6 | gov_han | 函 | 平行/简头/仿宋 | 跨单位商洽 | P0 |
| 7 | gov_yijian | 意见 | 严肃/红头/仿宋 | 见解类公文 | P1 |
| 8 | gov_tongbao | 通报 | 严肃/红头/仿宋 | 表彰/批评 | P1 |
| 9 | gov_gonggao | 公告 | 严肃/红头/仿宋 | 法定告知 | P1 |
| 10 | gov_jueding | 决定 | 严肃/红头/仿宋 | 重大决策 | P1 |
| 11 | biz_report | 商务报告 | 专业/蓝主题/微软雅黑 | 企业报告 | P0 |
| 12 | biz_proposal | 项目建议书 | 商务/紫主题 | 投标/立项 | P0 |
| 13 | biz_contract | 合同协议 | 严谨/黑白/宋体 | 商务合同 | P0 |
| 14 | biz_manual | 商务手册 | 规整/蓝灰 | 操作手册 | P1 |
| 15 | biz_white_paper | 白皮书 | 高端/深色主题 | 行业报告 | P1 |
| 16 | acad_paper_cn | 中文论文 | 学术/宋体 | 期刊论文 | P0 |
| 17 | acad_thesis | 毕业论文 | 学术/严谨 | 本/硕/博论文 | P0 |
| 18 | acad_paper_en | 英文论文 | IEEE/APA 风格 | 国际期刊 | P1 |
| 19 | acad_review | 综述 | 学术/宋体 | 综述文献 | P2 |
| 20 | pub_book | 图书 | 出版级/宋体 | 图书排版 | P1 |
| 21 | pub_magazine | 杂志 | 多栏/设计感 | 杂志期刊 | P2 |
| 22 | pub_brochure | 宣传册 | 图文混排 | 营销宣传 | P2 |
| 23 | creative_lite | 轻设计 | 现代/浅色调 | 创意提案 | P1 |
| 24 | creative_dark | 暗黑风 | 高级/深色主题 | 设计文档 | P2 |
| 25 | creative_colorful | 多彩活泼 | 鲜艳配色 | 活动方案 | P2 |
| 26 | simple_minimal | 极简白 | 极简/大量留白 | 通用文档 | P0 |
| 27 | simple_modern | 现代简约 | 干净/现代感 | 通用文档 | P0 |
| 28 | simple_clean | 清爽中性 | 中性配色 | 通用文档 | P1 |

### 模板配色方案

| 类别 | 主色 | 辅色 | 强调色 | 文字色 |
|------|------|------|--------|--------|
| 公文 | #CC0000 | #FFFFFF | #C00000 | #000000 |
| 商务报告 | #1F4E79 | #E9EFF5 | #C55A11 | #333333 |
| 项目建议书 | #2B5797 | #DEEAF1 | #F4B183 | #333333 |
| 合同 | #000000 | #F2F2F2 | #C00000 | #333333 |
| 白皮书 | #1A1A2E | #E94560 | #FFD700 | #FFFFFF |
| 学术论文 | #333333 | #F2F2F2 | #C00000 | #333333 |
| 毕业论文 | #000000 | #F2F2F2 | #C00000 | #333333 |
| 图书 | #1A1A1A | #E8E8E8 | #C00000 | #333333 |
| 杂志 | #E8E8E8 | #333333 | #F4B183 | #333333 |
| 轻设计 | #4B0082 | #AED9E6 | #FDA7A7 | #333333 |
| 暗黑风 | #1E1E1E | #BB86FC | #03DAC6 | #FFFFFF |
| 多彩活泼 | #FF6B6B | #ECDCDC | #FFE66D | #333333 |
| 极简白 | #FFFFFF | #F2F2F2 | #000000 | #2C2C2C |
| 现代简约 | #FAFAFA | #E0E0E0 | #1976D2 | #333333 |

---

## 🛠️ 使用方法

### 基础用法

```bash
# 1. 普通文档排版
@skill:word-formatter source_file="项目报告.docx" template_id="biz_report"

# 2. 公文排版（自动识别公文类型）
@skill:word-formatter source_file="省政府通知.docx" template_id="gov_tongzhi"

# 3. 极简排版
@skill:word-formatter source_file="项目复盘.docx" template_id="simple_minimal"

# 4. 白皮书排版
@skill:word-formatter source_file="AI行业报告.docx" template_id="biz_white_paper"
```

### 高级用法

```bash
# 1. 多模板对比（批量输出）
@skill:word-formatter source_file="产品需求.docx" template_id="biz_report,simple_minimal,creative_lite"

# 2. 禁用公文校验
@skill:word-formatter source_file="通知草稿.docx" template_id="gov_tongzhi" gov_check=false

# 3. 禁用差异报告
@skill:word-formatter source_file="报告.docx" template_id="biz_report" generate_diff_report=false

# 4. 仅排版指定范围（如仅正文）
@skill:word-formatter source_file="文档.docx" template_id="biz_report" format_options='{"scope": "body_only"}'
```

---

## 📤 输出说明

### 输出文件
1. **排版后 Word 文档**：`outputs/YYYY-MM-DD/原文件名_排版后.docx`
2. **排版差异报告**：`history/YYYY-MM-DD/diff_report.md`
3. **公文国标校验报告**：`history/YYYY-MM-DD/gov_check_report.md`（仅公文模板）
4. **Markdown 归档**：`history/YYYY-MM-DD/原文件_排版前.md` + `原文件_排版后.md`

### 差异报告示例

```markdown
# 排版差异报告

## 文档信息
- 原文件：项目报告.docx
- 模板：biz_report（商务报告）
- 排版时间：2026-06-08 13:00:00

## 变更摘要
- 字体变更：12 处
- 字号变更：8 处
- 行距变更：全文
- 段落间距变更：全文
- 标题样式变更：5 处
- 表格美化：2 个
- 图片调整：3 张

## 详细变更
### 字体变更
- 标题 1：宋体 → 微软雅黑 Bold 28pt
- 标题 2：宋体 → 微软雅黑 Bold 20pt
- 正文：宋体 → 微软雅黑 11pt

### 段落变更
- 行距：单倍 → 1.8 倍
- 段前距：0 → 6pt
- 段后距：0 → 6pt
- 首行缩进：无 → 2 字符

## 未变更内容
- 文档核心内容 100% 保留
- 表格数据 100% 保留
- 图片内容 100% 保留
```

---

## ⚠️ 异常处理

| 异常 | 处理 |
|------|------|
| 文件无法解析 | 提示修复建议（另存为 .docx） |
| 公文要素缺失 | 自动补默认占位 + 校验报告标红 |
| 标题层级识别失败 | LLM 兜底 + 用户确认 |
| 字体未安装 | 自动替换为同类字体 + 提示 |
| 表格结构异常 | 保留原样 + 警告 |
| 图片缺失 | 保留占位 + 警告 |
| 模板不存在 | 回退到 simple_minimal（通用模板）+ 提示 |

### 降级策略

| 场景 | 策略 |
|------|------|
| 用户输入模糊（如"排好看点"） | 先给一个假设版本（基于 simple_minimal 模板），再询问是否需要其他风格 |
| 文档结构复杂（混合了多种内容） | 优先保证标题和正文的排版，表格和图片保留原样 + 警告 |
| 缺少关键参数（如未指定模板） | 根据文档内容自动推荐最匹配的模板（公文→gov_tongzhi，报告→biz_report，日常→simple_minimal） |
| 超出能力范围（如 .pdf 排版） | 明确告知不支持，给出替代方案（转换工具下载链接/操作步骤） |
| 模板功能不存在（如用户要"水墨风"） | 基于现有最接近的模板（如 creative_dark）快速调整，并提供自定义模板上传入口 |
| 多任务同时请求 | 按公文 > 商务 > 学术 > 简洁 > 其他 的优先级依次处理，每完成一个给用户确认 |

---

## 🔒 安全与隐私

### 数据处理原则
- ✅ 所有文件处理在本地沙盒完成
- ✅ 不上传用户文档到任何服务器
- ✅ Markdown 归档仅存储到本地 `history/` 目录
- ✅ 支持删除 `history/` 目录清除所有归档
- ⚠️ 公文模板严格遵循 GB/T 9704-2012 标准，但不保证法律效力（需人工复核）

### 输出准确性约束
- 📌 **禁止在不确定时胡编**：如果文档结构识别不确定，必须向用户确认，而非假设正确
- 📌 **每条排版决策注明逻辑**：输出摘要中必须说明"为什么应用这个字体/字号/行距"
- 📌 **字符级内容保真**：排版过程中不修改文档核心内容，仅调整样式
- 📌 **数据来源标注**：如果引用了国标/规范，明确标注标准编号
- 📌 **不确定性标记**：如果某个段落/要素识别置信度低于 90%，在差异报告中标注"待人工确认"

---

## 📚 参考文档

1. **references/gov_standard.md** - 公文国标完整规则
2. **references/template_gov.md** - 公文类模板详细说明
3. **references/template_business.md** - 商务类模板详细说明
4. **references/template_academic.md** - 学术类模板详细说明
5. **references/anti_patterns.md** - 常见错误与改进示例
6. **references/faq_deep.md** - 18 个深度 FAQ

---

## ❓ FAQ（快速版）

**Q1：支持 .pdf 排版吗？**  
❌ 不支持。请先将 .pdf 转换为 .docx（可使用 Adobe Acrobat/WPS/在线转换工具）。

**Q2：公文排版后还需要人工复核吗？**  
✅ 需要。AI 严格遵循 GB/T 9704-2012 标准，但最终文档仍需人工复核（尤其是发文机关标志、发文字号、印章等）。

**Q3：字体显示不正确怎么办？**  
⚠️ 请确保系统已安装所需字体（方正小标宋简体、仿宋_GB2312 等）。缺失字体会自动替换并提示。

**Q4：可以自定义模板吗？**  
✅ 可以。上传参考稿 → AI 自动生成模板 → 基于该模板排版新文档。

**Q5：排版后文档变大了/变小了？**  
ℹ️ 排版仅调整样式（字体/字号/间距），不改变文档核心内容。文件大小变化源于图片压缩/样式重置。

**Q6：支持批量排版吗？**  
✅ 支持。同一模板可批量处理多文档；不同模板需多次调用。

**Q7：如何查看排版历史？**  
📂 所有排版历史存储在 `history/YYYY-MM-DD/` 目录，包含排版前后文档 + 差异报告。

**Q8：中文英混排时空格怎么处理？**  
✅ AI 自动在中英文之间添加空格（如"Word智能排版" → "Word 智能排版"），符合排版规范。

---

## 📝 版本路线图

| 版本 | 时间 | 核心交付 |
|------|------|----------|
| v1.0 MVP | M1 | 公文 5 套 + 商务 3 套 + 简洁 2 套 + 学术 2 套 |
| v2.0 M2 | M2 | 补全公文 10 套 + 国标校验报告完善 |
| v3.0 M3 | M3 | 出版/创意类模板 + 自定义模板上传 |
| v4.0 M4 | M4 | 多模板对比 + 批量排版 |

---

## ✅ 验收清单（DoD）

### 通用
- [x] 支持 .docx 解析与产出
- [x] 标题识别准确率 ≥ 95%
- [x] 中英文加空格规则生效
- [x] 差异对比报告完整
- [x] MD 归档目录完整

### 公文专属
- [x] 严格遵循 GB/T 9704-2012
- [x] 5 个高频文种（通知/报告/请示/批复/纪要）模板完整
- [x] 红头 + 武文线渲染正确
- [x] 字体严格匹配（小标宋/仿宋/黑体/楷体）
- [x] 页码格式（— 1 —）正确
- [x] 国标校验报告生成

### 模板库
- [x] MVP 12 套模板可用
- [x] 模板继承机制生效
- [x] 模板预览示例文档齐全

---

**作者**：周博远  
**版本**：v2.0.0  
**日期**：2026-06-08  
**核心特性**：公文 GB/T 9704-2012 国标深度支持 + 28 套精细化模板
