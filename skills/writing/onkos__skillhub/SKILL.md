---
name: onkos
version: 1.1.2
description: 支持2000章规模的AI长篇小说创作伙伴，通过6级分层摘要、SQLite事实相关性引擎、本地语义检索和多角色协作实现600万字级连贯性保证；当用户需要创作小说、管理长篇创作项目、检查情节连贯性、构建角色心理模型、追踪伏笔回收时使用
dependency:
  python:
    - jieba>=0.42.1
    - onnxruntime>=1.16.0
  system:
    - mkdir -p onkos/assets/models
---

# Onkos - 长篇小说创作伙伴

## 任务目标
- 本 Skill 用于: 基于智能体协作的长篇小说创作，支持2000章（600万字）规模的连贯性保证
- 能力包含: 6级分层上下文压缩、事实相关性引擎、知识图谱、角色心理建模、伏笔追踪、质量审计
- 触发条件: 用户希望创作小说、管理创作项目、检查故事连贯性、构建角色设定、追踪伏笔

## 前置准备
- 依赖: `jieba>=0.42.1`, `onnxruntime>=1.16.0`
- ONNX 语义模型下载（首次使用前执行一次）:
  ```bash
  python scripts/semantic_model.py --action download
  ```
  未下载时自动降级为FTS5关键词搜索

## 交互模型

用户通过自然语言对话使用本Skill，智能体负责识别意图并自动编排脚本调用。用户无需了解任何命令或参数。

### 意图识别总览

| 意图类别 | 典型表达 | 核心操作 |
|---------|---------|---------|
| 规划 | "我要写一部玄幻小说"/"加个势力"/"建个新角色" | init → 构建世界 → 建模角色 |
| 创作 | "写第15章"/"继续写"/"这段换个写法" | for-creation → 创作 → 存储 → 提取 → 录入 |
| 查询 | "林风境界是什么"/"之前发生了什么"/"有哪些角色" | get-fact / search / list-chars / list-hooks |
| 检查 | "检查连贯性"/"有没有矛盾"/"伏笔该收了" | audit / check-continuity / overdue-hooks |
| 修改 | "改一下第10章"/"把青云宗改成天剑宗" | analyze-revision → 修订 → 更新 |
| 分支 | "加个支线"/"宗门大比这条线怎么样了" | add-plot / create-branch / check-branches |
| 风格 | "分析一下风格"/"这两段风格像不像" | analyze-style / compare-style |
| 管理 | "进度怎么样"/"归档旧事实" | arc-progress / archive-facts / mem-stats |

### 帮助指令

用户输入以下任意表达时，智能体输出帮助信息:
- `/帮助` `/help` `/指令列表` `/命令列表` `/?`

**输出模板**（智能体直接渲染以下内容）:

```
OnKos 快捷指令一览（输入 /指令详情 <名> 查看详情）

【系统】 /帮助(help) /指令详情 /状态(status)
【规划】 /创建项目(init) /添加节点(add-node) /添加关系(add-edge) /创建角色(create-char) /创建阶段 /创建弧线
【创作】 /写(write) /续写 /存储(store) /提取实体 /录入事实 /种伏笔 /更新摘要 /完成章节
【查询】 /查事实 /查所有事实 /搜索(search) /相关事实 /获取上下文 /列出角色 /列出伏笔 /列出弧线 /列出节点
【检查】 /检查 /OOC检测 /审计(audit) /伏笔 /伏笔统计 /矛盾 /覆盖检查 /预算
【修改】 /修订 /更新事实 /回收伏笔 /放弃伏笔 /归档事实 /完成弧线
【分支】 /添加情节 /创建支线 /检查支线 /情节时间线
【风格】 /分析风格 /比较风格 /角色提示词
【管理】 /进度(progress) /建议(suggest) /统计 /图谱统计 /查节点 /查路径 /查邻居

提示: 也可以直接用自然语言描述需求，如"写第15章"、"检查一下连贯性"
括号内为英文别名，如 /help /write /store /search /audit /progress /suggest
```

用户输入 `/指令详情 <名称>` 时，智能体在 [references/command_index.md](references/command_index.md) 中查找对应指令并展示完整定义。

### 快捷指令与英文别名

用户可输入 `/` 开头的快捷指令精确触发操作，支持中文和英文两种写法。

| 中文 | 英文别名 | 说明 |
|------|---------|------|
| `/帮助` | `/help` | 显示帮助 |
| `/状态` | `/status` | 项目状态 |
| `/写` | `/write` | 写新章节 |
| `/续写` | `/continue` | 继续写 |
| `/存储` | `/store` | 存储章节 |
| `/搜索` | `/search` | 搜索记忆 |
| `/查事实` | `/fact` | 查询事实 |
| `/检查` | `/check` | 连贯性检查 |
| `/审计` | `/audit` | 质量审计 |
| `/进度` | `/progress` | 弧线进度 |
| `/建议` | `/suggest` | 建议下一步 |
| `/统计` | `/stats` | 记忆统计 |
| `/修订` | `/revise` | 修订章节 |
| `/分析风格` | `/style` | 风格分析 |

**所有指令的完整定义**（参数、步骤、示例）见 [references/command_index.md](references/command_index.md)。

---

## 一、规划类意图

当用户表达"开始新小说"、"搭建世界观"、"建角色"等意图时，执行以下流程。

### 1.1 创建新项目

**用户说**: "我想写一部叫《苍穹破》的玄幻小说" / "开一个新项目"

智能体操作:
1. [脚本] 调用 `init`，传入 title、genre、author
2. [脚本] 调用 `download`（如模型未下载）下载ONNX语义模型
3. [智能体] 主动与用户讨论：总章数规划、核心冲突、力量体系
4. [脚本] 根据讨论结果，调用 `create-phase` 创建阶段（100-300章粒度）
5. [脚本] 调用 `create-arc-am` 在阶段下创建弧线（30-60章粒度）

**智能体应主动推进**：不要等用户问，而是主动提出"建议分为X个阶段、Y条弧线"。

### 1.2 构建知识图谱

**用户说**: "加一个势力叫青云宗" / "林风和青云宗是什么关系" / "设定一下修炼体系"

智能体操作:
1. [脚本] 调用 `add-node`，传入节点类型和名称
2. [脚本] 调用 `add-edge`，传入源实体、目标实体和关系

节点类型: `person`(人物) / `faction`(势力) / `location`(地点) / `item`(物品) / `event`(事件)

**智能体应主动补全**：用户说"加个青云宗"时，主动询问宗门定位、与其他势力的关系，一次性录入节点和边。

### 1.3 创建角色

**用户说**: "创建主角林风" / "加个反派角色" / "林风的性格是怎样的"

智能体操作:
1. [智能体] 与用户讨论角色定位、性格特质、行为禁忌、说话风格
2. [脚本] 调用 `create-character`，传入完整参数

角色定位: `protagonist`(主角) / `antagonist`(反派) / `mentor`(导师) / `sidekick`(伙伴) / `npc`

**智能体应主动建模**：不只要问名字，还要主动建议Big Five人格维度、典型行为模式、禁忌行为，让角色活起来。参考 [references/agent_roles.md](references/agent_roles.md) 中 CharacterMind 角色模板。

---

## 二、创作类意图

当用户要写新章节、续写、修改写法时，执行以下流程。这是最核心的工作流。

### 2.1 写新章节（完整流程）

**用户说**: "写第15章" / "继续写下一章" / "帮我写林风突破的场景"

智能体按以下7步执行，**不可跳步**:

1. **获取上下文** [脚本]
   - 调用 `for-creation`，传入 chapter 和 query（用章节核心事件作为查询词）
   - 返回: 全书摘要 → 当前阶段/弧线摘要 → 前章摘要 → 相关事实 → 活跃伏笔

2. **阅读大纲** [智能体]
   - 检查 outline/ 目录下对应章节的大纲
   - 如无大纲，主动向用户确认本章节要写什么

3. **创作正文** [智能体]
   - 以 Writer 角色创作，结合上下文、大纲、角色性格
   - 参考创作指南 [references/creation_guide.md](references/creation_guide.md)

4. **存储章节** [脚本]
   - 调用 `store-chapter`，传入 chapter 和 content
   - 系统自动按场景分割入库

5. **提取实体** [脚本]
   - 调用 `extract-entities`，传入 content 和 genre
   - 题材选项: `fantasy`/`urban`/`wuxia`/`scifi`，不指定时从项目配置读取
   - 返回: 角色名/地点/物品/事件，含置信度(high/medium/low)

6. **录入事实与伏笔** [脚本 + 智能体]
   - 智能体审阅提取结果，识别需录入的事实
   - [脚本] 调用 `set-fact` 录入关键事实（注意选择正确的 importance）
   - [脚本] 调用 `plant-hook` 种埋新伏笔（如有）

7. **更新摘要** [脚本]
   - [脚本] 调用 `store-summary`，更新 chapter 级摘要
   - 每10章左右应补充 arc 级摘要

### 2.2 续写当前章节

**用户说**: "继续写" / "再写一段"

智能体操作: 同2.1的步骤3-7，从上次内容继续创作。

### 2.3 换种写法

**用户说**: "这段换个写法" / "写得太平淡了，改一下"

智能体操作: 纯自然语言处理，根据用户反馈调整风格重写。必要时参考 `style_learner` 的风格分析结果。

---

## 三、查询类意图

当用户询问故事中的事实、人物状态、过去发生的事件时。

### 3.1 查角色/物品状态

**用户说**: "林风现在什么境界" / "灵剑在谁手上" / "苏瑶的背景是什么"

智能体操作:
1. [脚本] 调用 `get-fact`，传入 entity 和 attribute
2. [智能体] 将结果以自然语言回答，如"林风目前在筑基三层，这是第15章突破的"

### 3.2 查过去事件

**用户说**: "第10章发生了什么" / "之前林风和赵云有什么交集"

智能体操作:
1. [脚本] 调用 `search`，传入 query 和可选的 chapter 范围
2. [智能体] 整理搜索结果，以叙事方式回答

### 3.3 查当前相关事实

**用户说**: "现在有哪些重要的事需要记住" / "当前状态总结一下"

智能体操作:
1. [脚本] 调用 `relevant-facts`，传入 current_chapter（可选，省略时自动推断）
2. [智能体] 按重要性组织回答: permanent事实 > 弧线内事实 > 近期事实

### 3.4 列出/浏览

**用户说**: "有哪些角色" / "显示所有伏笔" / "列出弧线" / "知识图谱里有什么"

智能体操作:
1. [脚本] 根据意图调用 `list-chars` / `list-hooks` / `list-arcs` / `list-nodes`
2. [智能体] 以结构化列表展示

---

## 四、检查类意图

当用户担心连贯性、想审查质量、或检查伏笔状态时。

### 4.1 连贯性检查

**用户说**: "检查一下" / "有没有矛盾" / "这段OOC了吗"

智能体操作:
1. [脚本] 调用 `check-continuity`，传入 chapter 和 content
2. [智能体] 对检查结果进行分析:
   - 位置矛盾: 角色不可能同时出现在两个地方
   - 事实矛盾: 与已录入事实冲突
   - OOC检测: 角色行为是否违反心理模型设定
3. [智能体] 以清晰的方式报告问题，并建议修复方案

### 4.2 质量审计

**用户说**: "这章写得好不好" / "打个分"

智能体操作:
1. [脚本] 调用 `audit`，传入 chapter 和 content
2. 返回 health_score(0-100) 和五个维度评分
3. [智能体] 对低分维度给出改进建议

### 4.3 伏笔健康

**用户说**: "伏笔怎么样了" / "有没有该收的伏笔" / "哪些伏笔拖太久了"

智能体操作:
1. [脚本] 调用 `overdue-hooks`，传入 current_chapter → 找出超期未回收的伏笔
2. [脚本] 调用 `forgotten-hooks`，传入 current_chapter → 找出可能被遗忘的伏笔
3. [智能体] 建议: 哪些伏笔该在近期回收、如何自然地融入情节

### 4.4 事实矛盾检测

**用户说**: "事实有没有冲突" / "设定有没有自相矛盾"

智能体操作:
1. [脚本] 调用 `detect-contradictions`，传入 chapter
2. [智能体] 分析矛盾，给出修复建议

---

## 五、修改类意图

当用户要修改已写内容时。**修改已写章节前必须先做影响分析**。

### 5.1 修订章节

**用户说**: "把第10章改一下" / "林风应该去天剑宗而不是青云宗"

智能体操作:
1. **影响分析**（必须先执行） [脚本]
   - 调用 `analyze-revision`，传入 chapter、old_content、new_content
   - 返回: risk_level(high/medium/low)、受影响的后续章节、受影响的事实、受影响的伏笔
2. [智能体] 向用户展示影响分析结果，确认是否继续修改
3. **清理旧数据** [脚本]
   - 调用 `clear-chapter`，传入 chapter
   - 一步清理该章节的旧场景、有效事实、open伏笔，防止数据膨胀
4. **执行修订** [智能体]
   - 根据用户确认重写内容
5. **重新录入** [脚本]
   - 调用 `store-chapter`（带 `replace=True`），覆盖存储新内容
   - 调用 `set-fact` 录入新事实
   - 调用 `store-summary` 重建摘要
   - 如伏笔受影响，调用 `plant-hook` 重新种埋（自动去重）

> **数据一致性说明**: 修改章节时必须先清理旧数据再录入新数据。`clear-chapter` 一步完成场景删除、事实废弃(superseded_by=-2)、伏笔放弃。`store-chapter` 的 `replace=True` 参数也会先清理该章节旧场景再录入。`chapter-complete` 命令默认启用替换模式。

### 5.2 仅更新事实

**用户说**: "林风的境界改成筑基五层" / "更新一下设定"

智能体操作:
1. [脚本] 调用 `set-fact`，传入更新后的值（同属性自动替代旧值）
2. 同属性再次录入时，旧事实自动标记为被替代(superseded)

---

## 六、管理类意图

当用户查看进度、归档数据、维护项目时。

### 6.1 查看进度

**用户说**: "进度怎么样" / "写到哪里了" / "接下来该写什么"

智能体操作:
1. [脚本] 调用 `status` → 项目总览
2. [脚本] 调用 `arc-progress`（current_chapter 可选，省略时自动推断最新章节）
3. [脚本] 调用 `suggest-next`（current_chapter 可选，省略时自动推断）
4. [智能体] 综合呈现: 已写章节、当前弧线、未回收伏笔数、待处理问题

### 6.2 归档清理

**用户说**: "归档旧事实" / "清理一下数据"

智能体操作:
1. [脚本] 调用 `archive-facts`，传入当前章节号和归档数量
2. 远期 chapter-scoped 事实会被归档，不再出现在上下文中

### 6.3 查看统计

**用户说**: "记忆库里有多少数据" / "知识图谱多大"

智能体操作:
1. [脚本] 调用 `mem-stats` → 记忆引擎统计
2. [脚本] 调用 `kg-stats` → 知识图谱统计

---

## 七、分支类意图

当用户要创建支线剧情、检查支线健康时。

### 7.1 创建情节/支线

**用户说**: "加个宗门大比的情节线" / "赵云那条线分出去"

智能体操作:
1. [脚本] 调用 `add-plot`，添加情节节点
2. [脚本] 调用 `create-branch`，创建支线（如需）

### 7.2 检查支线

**用户说**: "支线有没有断的" / "各条线健康吗"

智能体操作:
1. [脚本] 调用 `check-branches`，检查支线健康
2. [智能体] 分析断裂/孤立支线，给出修复建议

### 7.3 查看时间线

**用户说**: "情节时间线" / "给我画个情节图"

智能体操作:
1. [脚本] 调用 `plot-timeline`

---

## 八、风格类意图

当用户想分析或比较写作风格时。

### 8.1 风格分析

**用户说**: "分析一下我的写作风格" / "这段文字什么风格"

智能体操作:
1. [脚本] 调用 `analyze-style`，传入待分析文本
2. [智能体] 解读风格特征并给出建议

### 8.2 风格比较

**用户说**: "这两段风格像不像" / "跟第1章比风格变了没"

智能体操作:
1. [脚本] 调用 `compare-style`，传入两段文本
2. [智能体] 指出风格差异和变化趋势

### 8.3 角色提示词

**用户说**: "帮我从林风视角写" / "生成林风的写作提示词"

智能体操作:
1. [脚本] 调用 `char-prompt`，传入角色名
2. [智能体] 使用生成的提示词以该角色视角创作

---

## 核心概念

事实3级重要性（permanent/arc-scoped/chapter-scoped）、摘要6级分层（book/phase/arc/volume/chapter/scene）、角色5种定位（protagonist/antagonist/mentor/sidekick/npc）、节点5种类型（person/faction/location/item/event）。详细说明见 [references/creation_guide.md](references/creation_guide.md)。

---

## 资源索引
- 引擎: [memory_engine.py](scripts/memory_engine.py)(场景/检索/摘要/弧线) [fact_engine.py](scripts/fact_engine.py)(事实) [context_retriever.py](scripts/context_retriever.py)(6级上下文) [arc_manager.py](scripts/arc_manager.py)(进度/建议)
- 存储: [knowledge_graph.py](scripts/knowledge_graph.py)(图谱) [hook_tracker.py](scripts/hook_tracker.py)(伏笔) [semantic_model.py](scripts/semantic_model.py)(ONNX)
- 辅助: [character_simulator.py](scripts/character_simulator.py)(角色OOC) [style_learner.py](scripts/style_learner.py)(风格) [plot_brancher.py](scripts/plot_brancher.py)(情节) [entity_extractor.py](scripts/entity_extractor.py)(实体) [quality_auditor.py](scripts/quality_auditor.py)(审计)
- 项目: [project_initializer.py](scripts/project_initializer.py)(初始化) [command_executor.py](scripts/command_executor.py)(统一入口，支持英文别名)
- 参考: [agent_roles.md](references/agent_roles.md)(8角色模板) [creation_guide.md](references/creation_guide.md)(创作指南+核心概念) [command_index.md](references/command_index.md)(53指令索引) [command_reference.md](references/command_reference.md)(参数速查)

## 注意事项
- 所有数据统一存储在 `data/novel_memory.db`（知识图谱、伏笔、弧线均在SQLite）
- ONNX语义检索为可选增强，未下载时自动降级到FTS5关键词搜索
- 每章完成后的标准流程: 存储→提取实体→录入事实→检查伏笔→更新摘要（不可跳步）
- 修订已写章节前**必须先执行** `analyze-revision`，避免连锁错误
- 修订章节时**必须先清理旧数据**（`clear-chapter`），否则场景/事实/伏笔会累积膨胀
- `store-chapter` 和 `store-scene` 支持 `replace=True` 参数，先删除旧场景再录入
- `chapter-complete` 默认启用替换模式，自动覆盖旧场景
- `plant-hook` 自动去重：同描述的open伏笔已存在时返回已有ID
- 智能体应主动推进创作，而非被动等待指令；主动建议下一步、主动发现问题
- 调用脚本时，通过 `command_executor` 统一入口，使用Python风格参数名（下划线），内部自动映射
- 具体脚本的参数名和格式，查阅 [references/command_reference.md](references/command_reference.md)
- 智能体在创作流程中切换8个角色之一，详见 [references/agent_roles.md](references/agent_roles.md)
- `arc-progress` 和 `suggest-next` 的 current_chapter 参数可选，省略时自动推断最新章节号
