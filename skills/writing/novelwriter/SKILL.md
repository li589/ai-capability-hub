---
name: novelwriter
description: 会自动成长的AI去痕小说创作技能，集成 humanizer-zh 自动去除 AI 痕迹。提供从创意生成、世界观构建、角色设计、大纲创作到章节写作的全流程能力，支持多风格（辰东、三九音域等）文风模拟。
version: 1.0.0
install_source: official
install_method: download
skill_id: official_AmYgwqdv
enabled_at: 1787232331100
name_zh: 智能去痕小说创作专家
---

# 会自动成长的ai去痕小说 Skill

## 概述

NovelWriter 是为 OpenClaw Agent 提供的小说创作核心技能，涵盖从创意收集到章节写作的全流程。Agent 可以利用此技能根据用户需求生成不同类型、不同风格的小说内容。

## 能力范围

### 核心功能

1. **创意生成（Ideation）**
   - 根据关键词/题材生成故事创意
   - 提供多个创意方向供用户选择
   - 评估创意的市场潜力（可选）

2. **世界观构建（Worldbuilding）**
   - 创建完整的世界观设定（历史、地理、种族、势力）
   - 设计力量体系/修炼体系/科技水平
   - 制定世界运行规则（魔法、科学、神秘学）

3. **角色设计（Character Design）**
   - 生成角色卡（姓名、年龄、性格、背景、能力、弱点、成长弧）
   - 确保角色动机合理性
   - 设计角色关系和互动模式

4. **大纲创作（Outline）**
   - 三幕式大纲（开端-发展-高潮-结局）
   - 多线叙事结构（主线/支线/感情线）
   - 章节级细纲（每章核心事件、出场人物、场景）

5. **章节写作（Chapter Writing）**
   - 根据大纲生成章节正文
   - 保持人物性格一致
   - 控制节奏（爽点密度、缓冲段落比例）
   - 章节结尾悬念设计

6. **金手指设计（Goldfinger）**
   - 根据题材自动推荐金手指类型
   - 设定金手指的强度和限制条件
   - 平衡金手指与剧情紧张感

7. **风格匹配（Style Matching）**
   - 小白文风（直白、快节奏、爽点多）
   - 老白文风（细腻、逻辑强、伏笔深）
   - 文艺风（语言精致、主题深刻、人物立体）
   - 各题材专属风格（克苏鲁的阴郁、甜宠的温馨等）

8. **质量检查（Quality Review）**
   - 前后一致性检查（时间、人物、设定）
   - 节奏分析（是否灌水、是否过快）
   - 伏笔回收验证
   - 角色弧完整性评估

## 使用方式

### 1. 直接调用（会话模式）

```
你是 NovelWriter 专家，请帮我设计一个都市异能故事的角色设定。
要求：
- 主角（男，25岁）：拥有"时间回档"能力，但每次使用会加速衰老
- 反派（女，30岁）：控制系能力，冷酷无情但有过悲惨过去
- 女主角（女，22岁）：治愈系能力，性格温柔但内心坚韧
```

### 2. 工作流模式（Job）

使用 `novel-workflow` Job 进行完整的小说创作流程：

```
执行 job: novel-workflow
用户提供：
- 题材：都市异能
- 故事创意：主角获得系统，完成任务变强
- 风格偏好： moderately paced, 老白文风
```

### 3. 模块化调用

针对特定需求调用特定模块：

```
请使用 build-world 模块：
题材：克苏鲁
核心设定：1920年代 America，调查员发现禁忌知识
要求：包含至少3个旧日支配者相关设定，提供不可名状场景描述模板
```

## 模块说明

| 模块名 | 功能 | 主要输出 | 依赖配置 |
|--------|------|----------|----------|
| `generate-idea` | 创意生成 | 3-5个创意方向 | config/plot-modes.json |
| `build-world` | 世界观构建 | Worldbuilding Doc | config/world-templates.json |
| `design-character` | 角色设计 | Character Cards (JSON) | config/archetypes.json |
| `create-outline` | 大纲创作 | Outline (Markdown) | templates/outline.md |
| `write-chapter` | 章节写作 | Chapter (Markdown) | outline + config |
| `design-goldfinger` | 金手指设计 | Goldfinger Spec | config/goldfinger-types.json |
| `review-novel` | 质量检查 | Review Report | config/checklist.json |

## 配置说明

Skill 使用以下配置文件：

1. **config/novel-config.md** - 全局配置
```yaml
default_theme: "balanced"     # 默认风格
default_plot_mode: "growth"   # 默认剧情模式
goldfinger:
  auto_balance: true          # 自动平衡金手指强度
  max_count: 3                # 最多金手指数量
chapter:
  target_length: 4000        # 目标字数
  allow_deviation: 500       # 允许误差
  cliffhanger: true          # 强制章节结尾悬念
```

2. **config/theme-templates/** - 各题材提示词模板
   - `xuanhuan.md` - 玄幻修仙风格指令
   - `dushi.md` - 都市异能风格指令
   - `lishi.md` - 历史架空风格指令
   - `kechu.md` - 克苏鲁风格指令
   - `styles/` - 文风模板（小白文、老白文、文艺风）

3. **config/character-archetypes.json** - 角色原型库
```json
{
  "xuanhuan": {
    "protagonist": ["废柴逆袭", "天才陨落", "重生者", "穿越者", "系统宿主"],
    "antagonist": ["魔道巨擘", "宗门叛徒", "天道化身", "前世心魔"],
    "supporting": ["亦师亦友", "红颜知己", "忠心仆从", "亦敌亦友"]
  }
}
```

4. **config/plot-patterns.json** - 剧情模式详细说明
```json
{
  "growth": {
    "tone": "热血、励志",
    "structure": "线性成长",
    "key_elements": ["修炼体系", "等级划分", "越级挑战", "奇遇秘境"],
    "pacing": "快节奏，每章都有成长感"
  }
}
```

## 输出格式

### 角色卡格式

```markdown
## 角色卡：{姓名}

**基本信息**
- 年龄：{age}
- 性别：{gender}
- 身份：{role}
- 外貌特征：{appearance}

**性格特质**
- 主要性格：{personality}
- 外在表现：{mask}
- 内在真实：{true_self}

**背景故事**
{bio}

**能力设定**
- 能力名称：{ability_name}
- 能力描述：{ability_desc}
- 限制条件：{limitations}
- 弱点：{weakness}

**故事作用**
- 与主角关系：{relation_to_protagonist}
- 剧情功能：{plot_function}
- 成长弧线：{character_arc}
```

### 大纲格式

```markdown
# 《{书名}》大纲

## 一、故事一句话
{logline}

## 二、世界观设定
{worldbuilding_summary}

## 三、主要角色
{characters_summary}

## 四、剧情结构

### 第一幕：开端（第1-{num}章）
- 主要事件：{events}
- 引入角色：{characters}
- 悬念设置：{cliffhanger}

### 第二幕：发展（第{start}-{end}章）
...
```

## 错误处理

- **配置缺失**：检查 `config/` 目录是否存在所有必需文件
- **模板不存在**：确认 `templates/` 目录包含所需模板
- **依赖未安装**：安装对应主题经验包（如 `novel-xuanhuan`）
- **输出超长**：启用自动拆分（`auto-split` 模式）

## 扩展开发

要创建新的主题经验包，请参考 `experience/novel-{theme}` 目录结构。每个经验包应包含：

- `manifest.json` - 经验包元数据
- `prompts/` - 主题特定提示词
- `examples/` - 示例输出片段
- `README.md` - 使用说明

## 相关资源

- Wiki: https://github.com/your-repo/novel-writer/wiki
- Issues: https://github.com/your-repo/novel-writer/issues
- 示例作品：查看 `assets/examples/`

## License

MIT License © 2026
