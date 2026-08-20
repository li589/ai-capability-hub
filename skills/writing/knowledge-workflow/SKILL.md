---
name: knowledge-workflow
version: 1.0.0
description: ［何时使用］当用户需要沉淀知识、分类知识、让知识产生新内容时；当用户说"处理这个知识""知识管理工作流""整理这篇笔记""生成文章"时；当检测到"飞书文档""微信读书""知识整理""打标""知识发芽"等关键词时；基于 Karpathy LLM Wiki 思路，打造会"生长"的知识库
author: 燃冰 & ant
created: 2026-04-14T00:00:00.000Z
skill_type: 通用
related_skills:
  - note-tagger
  - knowledge-evolution
  - wechat-publisher
tags:
  - 知识管理，工作流，AI
  - 知识沉淀，自进化，Karpathy
install_source: official
install_method: download
skill_id: official_m2llCD1G
enabled_at: 1787231982931
name_zh: 知识管理工作流
---

# 知识管理工作流 🎯

**基于 Karpathy LLM Wiki 思路，打造会"生长"的知识库**

**让知识从"收藏"变成"产出"的完整系统**

---

## 📋 功能描述

基于 Karpathy LLM Wiki 思路，帮助用户打造会"生长"的知识库。

**适用场景：**
- 处理飞书文档/微信读书/网页文章
- 自动打标（主题 📚 + 场景 🎬 + 行动 ⚡）
- 自动建立 [[wikilinks]] 交叉引用
- 知识发芽（💡灵光/🧠心智模型/🔀跨界/🎯微习惯/🧘潜意识）
- 生成公众号文章/周报/月报
- 规则提炼（从经验中学习）
- 信念更新（数据驱动认知升级）
- 自我修复（lint 检查 + 自动修复）

**边界条件：**
- 不替代手动深度思考
- 需配合人工 review
- 飞书文档需要协作权限

**核心理念：**
> 传统知识库：人工维护 → 越来越乱 → 放弃
> 
> 自进化知识库：LLM 维护 + 自进化 → 越来越有序 → 复利增长

---

## ⚠️ 常见错误

**错误 1：来源类型不支持**
```
问题：
• 用户输入了不支持的来源类型（如 notion）

解决：
✓ 当前支持：feishu|wechat|url|text
✓ 提示用户选择支持的类型
```

**错误 2：飞书文档无法读取**
```
问题：
• doc_token 错误或无权限
• 飞书文档是私有的

解决：
✓ 检查 doc_token 是否正确（从飞书链接 `/docx/XXX` 提取 XXX）
✓ 检查飞书文档权限（设置为公开或添加协作者）
✓ 使用 `feishu_doc action=read` 测试权限
```

**错误 3：知识发芽类型错误**
```
问题：
• 用户输入了不支持的发芽类型

解决：
✓ 当前支持：spark|model|cross|habit|subconscious
✓ 提供默认值 spark
✓ 提示用户可用类型
```

**错误 4：存储目录无权限**
```
问题：
• ~/kb 目录不存在或无写入权限

解决：
✓ 创建目录：`mkdir -p ~/kb/{00-Inbox,outputs}`
✓ 设置权限：`chmod 755 ~/kb`
```

---

## 🧪 使用示例

### 示例 1：一键处理飞书文档

**输入：**
```
@ant knowledge-workflow:
来源：飞书文档 PFAvdKEILouK29xCgNuc5b1bnnK
自动执行：collect → tag → store → evolve → output
```

**预期输出：**
```json
{
  "workflow_id": "wf-20260414-001",
  "status": "completed",
  "steps": {
    "collect": {"note_id": "note-001", "status": "success"},
    "tag": {"tags": {"themes": ["知识管理"]}, "status": "success"},
    "store": {"path": "~/kb/40-管理/note-001.md", "status": "success"},
    "evolve": {"evolve_id": "spark-001", "status": "success"},
    "output": {"article_id": "article-001", "status": "success"}
  }
}
```

### 示例 2：分步处理 - 只打标

**输入：**
```
@ant knowledge-workflow tag:
笔记内容：知识管理的本质不是囤积，而是让知识"生长"和"被用"。
```

**预期输出：**
```json
{
  "note_id": "note-001",
  "tags": {
    "themes": ["知识管理"],
    "scenes": ["场景/学习时"],
    "actions": ["行动/存档"]
  },
  "confidence": 0.8,
  "status": "tagged"
}
```

### 示例 3：知识发芽

**输入：**
```
@ant knowledge-workflow evolve:
笔记 ID：note-001
发芽类型：spark
```

**预期输出：**
```json
{
  "evolve_id": "spark-001",
  "evolve_type": "spark",
  "content": {
    "title": "知识管理的本质",
    "insight": "知识管理不是\"建图书馆\"，而是\"种花园\"",
    "insight_chain": ["表面问题", "深层原因", "本质规律"],
    "cross_links": ["花园×知识管理", "健身×知识管理"]
  },
  "status": "evolved"
}
```

---

## ⚙️ 配置说明

编辑 `config.yaml`：

```yaml
storage:
  default_type: "local"  # local|feishu|obsidian
  base_path: "~/kb"

tagging:
  auto_tag: true
  confidence_threshold: 0.6

evolution:
  default_type: "spark"  # spark|model|cross|habit|subconscious

output:
  default_type: "article"  # article|weekly|monthly
```

**首次使用检查**：
```bash
# 检查配置
cat config.yaml

# 创建目录
mkdir -p ~/kb/{00-Inbox,outputs}

# 测试运行
python main.py collect feishu PFAvdKEILouK29xCgNuc5b1bnnK
```

---

## 🔗 相关技能

- `note-tagger` - 笔记打标（本技能的前置技能，可单独使用）
- `knowledge-evolution` - 知识演化（本技能的核心功能）
- `wechat-publisher` - 公众号发布（配合产出使用）

**推荐组合**：
```
knowledge-workflow → wechat-publisher
（处理知识）    （发布文章）
```

---

## 🔧 故障排查

| 问题 | 检查项 |
|------|--------|
| 不触发 | clawhub.yaml 中 description 是否包含触发词？ |
| 收集失败 | 飞书 doc_token 是否正确？有权限吗？ |
| 打标失败 | 笔记内容是否为空？ |
| 存储失败 | 目录有写入权限吗？(`chmod 755 ~/kb`) |
| 发芽失败 | evolve_type 是否支持（spark\|model\|cross\|habit\|subconscious）？ |
| 输出失败 | outputs 目录存在吗？ |

**调试模式**：
```bash
# 查看详细日志
python main.py run feishu <doc_token> 2>&1 | tee debug.log

# 检查 Python 依赖
pip install -r requirements.txt

# 测试单个功能
python main.py collect feishu <doc_token>
```

---

## 📋 Skill 描述

**名称**：`knowledge-workflow`

**用途**：完整的知识管理工作流，让 Agent 可以快速调用，沉淀知识、分类知识、让知识产生新内容。

**触发词**：
- "处理这个知识"
- "知识管理工作流"
- "knowledge-workflow"
- "沉淀这个知识"

---

## 🎯 完整工作流

```
输入内容 → 收集 → 打标 → 存储 → 知识发芽 → 产出
```

**5 个核心阶段，每个阶段都是可调用的子功能**：

| 阶段 | 子功能 | 输入 | 输出 |
|------|-------|------|------|
| **1. 收集** | `collect` | 飞书链接/微信读书/网页 URL | Markdown 笔记 |
| **2. 打标** | `tag` | Markdown 笔记 | 带标签的笔记 |
| **3. 存储** | `store` | 带标签的笔记 | 存储到知识库 + 双链建议 |
| **4. 发芽** | `evolve` | 已存储笔记 | 5 种知识发芽产出 |
| **5. 产出** | `output` | 发芽内容 | 公众号文章/周报/月报 |

---

## 🎯 子功能详解

完整子功能文档见：[references/子功能详解.md](references/子功能详解.md)

**快速概览**：

| 功能 | 用途 | 输入 | 输出 |
|------|------|------|------|
| **collect** | 收集知识 | 飞书/微信读书/URL/文本 | Markdown 笔记 |
| **tag** | 自动打标 | 笔记内容 | 主题 + 场景 + 行动标签 |
| **store** | 存储 + 双链 | 带标签笔记 | 存储路径 + 双链建议 |
| **evolve** | 知识发芽 | 已存储笔记 | 灵光/心智模型/跨界/微习惯/潜意识 |
| **output** | 内容产出 | 发芽内容 | 公众号文章/周报/月报 |

---

## 🔄 完整工作流调用

### 方式 1：分步调用

```
1. @ant knowledge-workflow collect: [来源]
2. @ant knowledge-workflow tag: [笔记内容]
3. @ant knowledge-workflow store: [带标签笔记]
4. @ant knowledge-workflow evolve: [笔记 ID]
5. @ant knowledge-workflow output: [发芽内容]
```

### 方式 2：一键调用（自动执行全流程）

```
@ant knowledge-workflow:
来源：飞书文档 PFAvdKEILouK29xCgNuc5b1bnnK
自动执行：collect → tag → store → evolve → output
```

**输出**：
```json
{
  "workflow_id": "wf-20260414-001",
  "status": "completed",
  "steps": {
    "collect": {"status": "success", "note_id": "note-001"},
    "tag": {"status": "success", "tags": {...}},
    "store": {"status": "success", "path": "..."},
    "evolve": {"status": "success", "evolve_id": "spark-001"},
    "output": {"status": "success", "article": "..."}
  }
}
```

---

## ⚙️ 配置说明

编辑 `config.yaml`：

```yaml
storage:
  default_type: "local"  # local|feishu|obsidian
  base_path: "~/kb"

tagging:
  auto_tag: true
  confidence_threshold: 0.6

evolution:
  default_type: "spark"  # spark|model|cross|habit|subconscious

output:
  default_type: "article"  # article|weekly|monthly
```

**首次使用检查**：
```bash
# 检查配置
cat config.yaml

# 创建目录
mkdir -p ~/kb/{00-Inbox,outputs}

# 测试运行
python main.py collect feishu PFAvdKEILouK29xCgNuc5b1bnnK
```

---

## 🔗 与其他 Skill 组合

- `note-tagger` - 笔记打标（前置技能）
- `knowledge-evolution` - 知识演化（核心功能）
- `wechat-publisher` - 公众号发布（产出配合）

**推荐工作流**：
```
knowledge-workflow → wechat-publisher
（处理知识）    （发布文章）
```

完整 API 文档见：[README.md](README.md)

---

## 📝 发布到 ClawHub

### 1. 创建 Skill 目录结构

```
~/kb/skills/knowledge-workflow/
├── SKILL.md              # 本文档
├── main.py               # 主程序
├── subfunctions/
│   ├── collect.py        # 收集功能
│   ├── tag.py            # 打标功能
│   ├── store.py          # 存储功能
│   ├── evolve.py         # 知识发芽
│   └── output.py         # 产出功能
├── config.yaml           # 配置文件
└── requirements.txt      # 依赖
```

### 2. 编写 clawhub.yaml

```yaml
name: knowledge-workflow
version: 1.0.0
description: 完整的知识管理工作流，让 Agent 可以快速调用，沉淀知识、分类知识、让知识产生新内容
author: 燃冰 & ant
tags: [知识管理，工作流，AI]

entry_point: main.py
dependencies:
  - python>=3.6
  - requests
  - pyyaml

triggers:
  - "处理这个知识"
  - "知识管理工作流"
  - "沉淀这个知识"
  - "knowledge-workflow"
```

### 3. 发布命令

```bash
cd ~/kb/skills/knowledge-workflow
clawhub publish
```

---



---



---


