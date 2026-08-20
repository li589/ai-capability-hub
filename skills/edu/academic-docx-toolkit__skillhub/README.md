# 学术论文DOCX排版工具包 / Academic DOCX Toolkit

## 中文

### 概述

学术论文DOCX排版工具包是一个面向学术写作场景的python-docx增强代码模板集合。它提供经过验证的学术排版代码示例、操作策略和常见期刊/学位论文模板参数，帮助学术写作者高效地生成符合规范的DOCX文档。

### 功能亮点

- **3套学术表格配色方案** — 深蓝、深灰（灰阶打印安全）、简约三种风格，含完整python-docx代码
- **图片逆向插入机制** — 从图8到图1逆向插入，彻底解决索引漂移问题
- **段落精细操作** — 拆分、合并、标记清除、标题层级管理，基于XML层直接操作
- **多文档安全合并** — 从末尾向前操作策略，两阶段替换，分批提交防止数据丢失
- **主流期刊模板** — GB/T标准、中文学位论文、IEEE双栏、Elsevier期刊的页面参数
- **批量操作安全模式** — 备份→分批→验证→提交的完整安全链

### 与 python-docx 的关系

本工具包**不是**python-docx的替代品或封装库。python-docx本身已经提供了强大的DOCX操作能力。本工具包的价值在于：

- 将python-docx的API组合成**可直接复用的学术排版代码模板**
- 提供在批量操作中**避免常见陷阱**（如段落索引漂移）的策略
- 整理**期刊和学位论文的格式参数**，省去反复查手册的时间

### 与现有 docx 技能的关系

QClaw 中已存在两个 DOCX 相关技能：`docx` 和 `word-docx`。本技能是它们的**学术场景补充**，而非替代：

- `docx` 技能 — 通用DOCX创建、读取、编辑
- `word-docx` 技能 — 专业功能（修订追踪、模板、表格等）
- **本技能** — 学术排版专项（表格配色、图片管理、格式模板、安全批量操作）

推荐先用 `docx` 或 `word-docx` 技能完成基础操作，在遇到学术格式需求时查阅本技能的 references 获取代码模板。

### 文件结构

```
academic-docx-toolkit/
├── SKILL.md                          # 技能入口与导航
├── README.md                         # 本文件
└── references/
    ├── table-styling.md              # 学术表格配色与样式
    ├── figure-management.md          # 图片插入/替换/编号管理
    ├── paragraph-ops.md              # 段落拆分合并与格式操作
    ├── merging-strategy.md           # 多文档合并策略
    ├── journal-templates.md          # 期刊/学位论文页面模板
    └── safety-patterns.md            # 批量操作安全模式
```

---

## English

### Overview

The Academic DOCX Toolkit is a curated collection of python-docx code templates and operational strategies designed specifically for academic writing scenarios. It provides battle-tested code examples, formatting parameters for common journals and theses, and safety patterns for batch document manipulation.

### Key Features

- **3 Academic Table Color Schemes** — Dark blue, dark gray (grayscale-print safe), and minimalist styles with complete python-docx code
- **Reverse Figure Insertion** — Insert from Figure N down to Figure 1 to eliminate paragraph index drift
- **Fine-grained Paragraph Operations** — Split, merge, markup removal, heading hierarchy via XML-level manipulation
- **Safe Multi-document Merging** — Bottom-up operation strategy, two-phase replacement, batched commits
- **Journal Templates** — GB/T standard, Chinese thesis format, IEEE two-column, and Elsevier journal parameters
- **Batch Operation Safety** — Full safety chain: backup → batch → verify → commit

### Relationship with python-docx

This toolkit is **not** a replacement or wrapper for python-docx. python-docx already provides robust DOCX manipulation capabilities. The toolkit adds value by:

- Combining python-docx APIs into **ready-to-reuse academic formatting code templates**
- Providing strategies to **avoid common pitfalls** (like paragraph index drift) during batch operations
- Curating **journal and thesis formatting parameters** to save manual lookup time

### Relationship with Existing docx Skills

Two DOCX-related skills already exist in QClaw: `docx` and `word-docx`. This skill is an **academic scenario enhancement**, not a replacement:

- `docx` skill — General-purpose DOCX creation, reading, and editing
- `word-docx` skill — Professional features (tracked changes, templates, tables, etc.)
- **This skill** — Academic formatting specialization (table color schemes, figure management, format templates, safe batch operations)

Recommended workflow: use `docx` or `word-docx` for basic operations first, then consult this skill's references for academic formatting code templates when needed.

### File Structure

```
academic-docx-toolkit/
├── SKILL.md                          # Skill entry point and navigation
├── README.md                         # This file
└── references/
    ├── table-styling.md              # Academic table styling
    ├── figure-management.md          # Figure insertion/replacement/indexing
    ├── paragraph-ops.md              # Paragraph split/merge/formatting
    ├── merging-strategy.md           # Multi-document merging strategy
    ├── journal-templates.md          # Journal/thesis page templates
    └── safety-patterns.md            # Batch operation safety patterns
```

---

作者：人类Nan
