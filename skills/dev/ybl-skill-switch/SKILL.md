---
name: ybl-skill-switch
display_name: 技能开关
description: 管理已安装 Skill
  的启用与禁用。当用户说"打开/关闭某某技能""启用/禁用某某skill""把涉及XX的skill启用""列出禁用的skill""查看启用/禁用的某某技能""查看某类skill启用/禁用状态""查看启用的/禁用的某类
  skill"时触发；不处理非 Skill
  的开关操作（如关闭网页、打开文件、关闭电脑），也不处理纯查看状态类请求（无启用/禁用/打开/关闭用词时由系统内置能力接管）。
version: 1.4.2
allowed-tools: Read, Edit, Glob, Grep
display_name_en: Skill Switch
description_zh: 管理已安装 Skill 的启用与禁用——一句话批量操作，不用记名称，不用翻列表。支持按编号选择、按类别筛选、全部批量操作，每次执行前有确认闸门防止误操作。
description_en: Enable or disable installed Skills in one sentence. Batch
  operations by number, category filter, or all at once, with a confirmation
  gate before every change to prevent mistakes.
visibility: public
disable-model-invocation: true
---

# 技能开关（ybl-skill-switch）

一句话启用或禁用 `~/.workbuddy/skills/` 下的用户级 Skill。通用版，不绑定特定用户。通过编辑各 Skill 的 SKILL.md 内 disable 字段开关，无需回 UI 翻列表。属于 ybl 系列（由应变力创建）。

## 机制

编辑目标 Skill 的 `SKILL.md` frontmatter 中 `disable` 字段：
- `disable: true` → 禁用（下一轮对话的技能列表刷新后不加载该 Skill）
- `disable: false` 或**无该字段** → 启用（无字段 = 默认启用，视为 `false`）

## 启用流程

1. 用户说"启用/打开 XX"（或回复查看列表的编号，如"启用 2"）→ 扫描 `~/.workbuddy/skills/**/SKILL.md` 读取 name + description + disable 状态
2. 解析目标（按优先级）：
   - 用户给**编号** → 映射到【最近一次查看列表】中的对应技能（上下文里已有该编号清单），无需用户重复名称
   - 用户说"**全部**" → 作用于当前列表全部技能
   - 用户给**名称/类别词** → 语义匹配候选（原逻辑不变）
   - 编号**无法映射**（跨轮过多或上下文已清）→ 提示用户重述名称，或先说"查看 XX"重新生成列表
3. 执行前，先将选中项**按「编号 + 名称 + 将执行动作」重述一遍**（如"将启用：② deep-research-clawhub"），并标注跳过项（已启用 / 自身保护）；待用户明确说"确认 / 执行 / 好"后才改文件。**当用户说「全部」时，重述必须列出受影响技能**总数**，并额外要求用户回复「确认全部启用 N 个」才执行（与其他单项确认强度拉开）。**
4. 按候选当前状态分支处理：
   - 当前 `disable: true` → 用 Edit 改为 `disable: false`
   - 当前无 `disable` 字段 或 已是 `disable: false` → 反馈"已启用，无需操作"，不改文件
5. 反馈结果

## 禁用流程

1. 用户说"禁用/关闭 XX"（或回复查看列表的编号，如"禁用 1,3"）→ 扫描 `~/.workbuddy/skills/**/SKILL.md` 读取 name + description + disable 状态
2. 解析目标（按优先级）：
   - 用户给**编号** → 映射到【最近一次查看列表】中的对应技能，无需用户重复名称
   - 用户说"**全部**" → 作用于当前列表全部技能
   - 用户给**名称/类别词** → 语义匹配候选（原逻辑不变）
   - 编号**无法映射** → 提示用户重述名称，或先说"查看 XX"重新生成列表
3. 执行前，先将选中项**按「编号 + 名称 + 将执行动作」重述一遍**（如"将禁用：① deep-research ② deep-research-clawhub"），并标注跳过项（已禁用 / 自身保护 ybl-skill-switch）；待用户明确说"确认 / 执行 / 好"后才改文件。**当用户说「全部」时，重述必须列出受影响技能总数，并额外要求用户回复「确认全部禁用 N 个」才执行（与其他单项确认强度拉开）。**
4. 按候选当前状态分支处理：
   - 当前 `disable: false` → 用 Edit 改为 `disable: true`
   - 当前无 `disable` 字段 → 在 frontmatter 插入一行 `disable: true`（锚定 frontmatter 闭合的 `---` 之前插入；若 frontmatter 无 version 等字段，直接插在 `---` 前一行即可）
   - 当前已是 `disable: true` → 反馈"已禁用，无需操作"，不改文件
5. 反馈结果

## 查看流程（列示，不改文件）

纯查看，不改动任何文件。用户想先看清"哪些 skill 在启用/禁用"再决定操作时使用。

**本流程使用的工具**：Glob（扫描全部 SKILL.md 获取文件清单）、Read（读取单个 SKILL.md 的 name/description/disable 字段）、Grep（匹配 `^disable: true` 筛选禁用集）。Edit 仅用于启用/禁用流程的写操作，查看阶段不调用。

1. 用户说"查看/列出 **启用的/打开的** XX""查看/列出 **禁用的/关闭的** XX""查看启用的/禁用的某类 skill"
2. 确定范围（用 Glob 扫描全部 `SKILL.md` 后用 Grep 过滤，不做 shell 命令依赖）：
   - 启用集：Glob `~/.workbuddy/skills/**/SKILL.md` 全集，减去 Grep `^disable: true` 命中集（无字段 或 `disable: false` 都算启用）
   - 禁用集：Grep `^disable: true` 命中集
   - 某类全部：扫描所有 `SKILL.md`，不做状态过滤
3. 若用户给了技能名或类别词，按 name + description **关键词**过滤（**不维护额外标签**，直接读各 SKILL.md 的 description 匹配）
4. 列示每个技能——**必须按出现顺序编号 + 标注状态（✅启用 / ⛔禁用）**。这是强制输出格式，不可省略编号、不可用无编号表格替代。正确格式：

   ① ✅ deep-research —— 结构化深度研究流程
   ② ⛔ deep-research-clawhub —— 企业级多源综合研究
   ③ ✅ kdense-literature-review —— 系统文献综述
   ……

   若需分类展示（如"深度研究/搜索类（5）"），每个分类下的条目同样必须带编号，编号跨分类连续递增不重置。
5. 末尾附**选择提示**：
   「要启/禁用其中某些，直接回复编号即可，如『禁用 1,3』『启用 2』，无需输入名称。也可说『全部禁用』『全部启用』。回复后我会先列明将执行的操作，等你确认再改文件。」
6. 仅展示，不写文件、无需确认
7. **操作引导**：查看后续想启/禁用所列技能，优先用**编号回复**（如『禁用 1,3』），最省事；也可开新对话发独立指令，或显式调用 `@ybl-skill-switch 禁用 XXX`。同一对话紧接查看结果后直接说"禁用某技能名称"，可能不经本技能而由通用能力直接改文件——用编号或显式调用可规避此问题。

## 白名单

白名单只含一项硬规则：**永不禁用 ybl-skill-switch 自身**（禁用了自己就无法再启用自己）。

除此之外**不设任何白名单**——启用与禁用都需经用户显式确认（列出候选 → 用户确认 → 才改文件），主动权始终在用户手上。

## 安全边界

- 只管 `~/.workbuddy/skills/` 用户级，不碰 plugins/、connectors/、内置 Skill
- 只改 disable 字段，不删除文件、不改其他内容
- 禁用前确认，启用前确认——每一步都要用户明确同意
- 查看当前禁用项：用 Grep 匹配 `^disable: true` 扫描各 Skill 的 SKILL.md

## 触发与调用须知

本技能能否被调用取决于平台路由层，以下是从实测中总结的调用模式，执行时参考：

- **自然语言（普通模式）通常可用**：如"禁用 deep-research-clawhub""启用深度研究类的 skill"，含启用/禁用/打开/关闭用词时多数情况能路由到本技能。
- **⚠️ 查看后同对话直接说"禁用某技能名称"可能被通用能力接管**：模型手里有上一步上下文，会自行 Edit 文件、**绕过本技能的确认闸门与 ✅/⛔ 报告**。规避方法：引导用户用编号回复（"禁用 1,3"）或显式调用 `@ybl-skill-switch 禁用 XXX`（详见查看流程 step 7 的操作引导）。

## Few-Shot

见 `references/few-shots.md`（实测示例：启用 / 禁用无字段 / 列出禁用项 / 查看某类技能状态）。

## Gotchas

| # | 坑 | 避坑 |
|:-|:---|:------|
| G1 | 扫描时漏掉没有 disable 字段的 Skill | 没有 disable 字段 = 默认启用，视为 `disable: false`；禁用时直接**插入**字段，而非改值 |
| G2 | 禁用了 ybl-skill-switch 自身 | 自身永远受保护，绝不进禁用清单 |
| G3 | 改了 disable 但用户没确认就执行 | 先列候选 → 用户明确说"确认"/"好"/"执行"才改文件 |
| G4 | 误碰 plugins/ 或内置 Skill | 只扫描 `~/.workbuddy/skills/`，其他目录不碰 |
| G5 | 查看时误改文件 | 查看流程只读不写；任何写操作都须经用户确认，查看与启用/禁用严格分离 |
| G6 | 禁用无 disable 字段的 skill 时插入失败 | 插入锚点用 frontmatter 闭合的 `---`（永远存在），不要用 `version:`（约 80% 的 skill 无此字段，Edit 会因 old_string 不存在报错） |
| G7 | 查看输出漏掉编号或用了无编号表格/列表 | **编号是强制要求，不可省略。** 输出必须每行带 `①②③…` 或 `1.2.3.` 编号前缀 + ✅/⛔ 状态标记。禁止输出不带编号的纯表格或纯名称列表。用户靠编号做后续选择，没有编号 = 功能失效。 |
| G8 | 多个 skill 的 `name` 字段相同导致语义匹配歧义（实测：`deep-research` 与 `deep-research-clawhub` 都叫 `deep-research`） | 用户说"启用 deep-research"会命中错目标。避坑：①匹配时若发现**多个同名候选**，必须**列出全部同名项让用户确认**，不得自行选定其一；②引导用户用查看列表里的**编号**选，或给更具体的描述词（如"clawhub 版 deep-research"），不依赖 name 精确匹配。 |
| G9 | 去 `settings.json` 或其他全局配置找启用/禁用状态 | 状态**只存在于各 skill 的 `SKILL.md` frontmatter 的 `disable` 字段**，不在 settings.json（那里只有插件，没有 skill 开关状态）、不在任何全局配置。避坑：永远用 grep 各 `SKILL.md` 的 `disable` 字段判定状态，不要读 settings.json。 |
