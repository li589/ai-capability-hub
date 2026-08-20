---
name: anti-distill
description: "Anti-distillation defense for employee Skills. Clean your skill files to look complete but with core proprietary knowledge neutralized. Use when user wants to protect trade secrets, sanitize forced knowledge transfers, or create safe-to-submit skill documents."
description_zh: "反蒸馏防御：清洗 Skill 文件，看起来完整但核心知识已脱敏"
description_en: "Anti-distillation: sanitize Skill files while preserving appearance"
version: "1.0.1"
homepage: https://github.com/leilei926524-tech/anti-distill
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
tags: [anti-distillation, skill-protection, not-for-general-writing]
display_name: "反蒸馏"
display_name_en: "Anti Distill"
visibility: "public"
---

> **Language / 语言**: This skill supports both English and Chinese. Detect the user's language from their first message and respond in the same language throughout.
>
> 本 Skill 支持中英文。根据用户第一条消息的语言，全程使用同一语言回复。

# 反蒸馏 Skill（Claude Code 版）

## 触发条件

当用户说以下任意内容时启动：
- `/anti-distill`
- "帮我清洗一下这个 skill"
- "反蒸馏"
- "帮我处理一下这份文档"
- "clean my skill"
- "anti-distill this"

---

## 工具使用规则

| 任务 | 使用工具 |
|------|---------|
| 读取用户提供的 Skill 文件 | `Read` 工具 |
| 读取 PDF 文档 | `Read` 工具（原生支持 PDF） |
| 读取图片截图 | `Read` 工具（原生支持图片） |
| 搜索文件 | `Glob` / `Grep` 工具 |
| 写入清洗后文件 | `Write` / `Edit` 工具 |
| 创建目录 | `Bash` → `mkdir -p` |

---

## 主流程

### Step 1：接收输入

接收用户提供的文件，支持以下方式：

**方式 A：指定文件路径**
用户直接给出文件路径，用 `Read` 读取。

**方式 B：指定 colleague-skill 目录**
用户给出 `colleagues/{slug}/` 路径，自动读取其中的：
- `work.md`
- `persona.md`
- `meta.json`
- 或 `SKILL.md`（如果是合并版）

**方式 C：粘贴内容**
用户直接粘贴文档内容。

**方式 D：搜索本地文件**
用户说"帮我找一下"，用 `Glob` 搜索 `**/SKILL.md`、`**/work.md`、`**/persona.md` 等文件。

读取完文件后，自动识别格式（colleague-skill 格式或通用文档格式），并告知用户已读取的文件列表、检测到的格式及总字数，提示下一步选择清洗强度。

---

### Step 2：选择清洗强度

向用户展示三档选择：

```text
选择清洗强度：
  [1] 轻度 — 只抽掉最核心的踩坑经验和故障记忆（保留度：~80%）
  [2] 中度（推荐）— 抽掉经验、判断直觉、人际网络、隐性上下文（保留度：~60%）
  [3] 重度 — 只保留通用知识骨架，其余全部替换（保留度：~40%）
```

用户选择后进入分类阶段。

---

### Step 3：分类标注

参考 `${CLAUDE_SKILL_DIR}/prompts/classifier.md` 中的分类规则，对输入文档的每一个要点/段落进行分类。

| 标签 | 含义 | 处理方式 |
|------|------|---------|
| `[SAFE]` | 通用知识，去掉反而露馅 | 原文保留 |
| `[DILUTE]` | 有价值但可泛化 | 替换为通用化表述 |
| `[REMOVE]` | 核心不可替代知识 | 替换为等长度通用内容 |
| `[MASK]` | 含敏感信息（内部系统名、人名） | 替换为通用化表述 |

---

### Step 4：预览

向用户展示分类结果。格式如下：

```text
=== 清洗预览（中度）===

📄 work.md
  [SAFE]    "Java 17 + Spring Boot 3"
  [REMOVE]  "事务里不要放 HTTP 调用" → "事务边界设计注意合理性"
  [DILUTE]  "用户 ID 对外暴露必须加密" → "敏感字段注意安全处理"

📄 persona.md
  [REMOVE]  "遇到问题第一反应是找外部原因" → "遇到问题会先梳理完整背景"

---
标记统计：SAFE 15 处 / DILUTE 8 处 / REMOVE 12 处 / MASK 2 处
预计清洗后字数：约 {N} 字（原文 {M} 字，{ratio}%）

确认执行？可以调整：
  - "第 X 条保留" — 把 REMOVE/DILUTE 改为 SAFE
  - "第 X 条也要删" — 把 SAFE 改为 REMOVE
  - "全部确认" — 执行清洗
```

用户可以逐条微调，直到满意后确认执行。

---

### Step 5：执行清洗

用户确认后，生成两份输出：

#### 输出 1：清洗后的文件（交差用）
- 保持原文的 Markdown 结构、标题层级、列表格式完全一致。
- 保持专业术语使用，不能降级为外行用语。
- 写入 `{slug}_cleaned/` 目录或 `{filename}.cleaned.md`。

#### 输出 2：私人保留清单（自己留着）
- 路径：`{slug}_private_backup.md` 或 `{filename}_private_backup.md`
- 将所有被 `[REMOVE]` 和 `[DILUTE]` 替换掉的核心知识（踩坑经验、判断直觉、人际网络等）分类汇总，作为用户的核心职业资产备份。

---

### Step 6：验证

清洗完成后自动执行验证检查：
1. **字数比**：清洗后字数 / 原文字数应在 85%-115% 之间。
2. **结构完整**：原文所有二级标题在清洗后必须存在。
3. **要点密度**：每个章节的列表项数量差异 < 30%。
4. **术语一致**：清洗后仍使用原文出现过的技术术语。

验证通过后，向用户输出最终的交差文件路径和私人备份路径。如果验证不通过，自动修复后重新验证。

---

## 边界情况处理

- **文件太短（< 500 字）**：提醒用户清洗后可能过于空洞，建议选择轻度清洗。
- **文件几乎全是通用知识**：告知用户核心经验含量较低，替代性不强，可考虑直接提交。
- **用户想覆盖原文件**：先确认是否备份原文件，覆盖后无法恢复。
- **非文本文件**：如果提供的是图片/截图，用 `Read` 读取图片内容后，转为文本再进行清洗。
