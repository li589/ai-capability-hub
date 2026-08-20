# Skill Switch 示例库

来自本窗口（2026-07-21～22）创建 skill 前的真实实测对话，非编造。

## 示例1：启用 market-researcher（验证 disable 字段机制）

**背景**：用户质疑"禁用的 skill 是否真的能靠改文件重新启用"，要求实测。

**用户**：做一下这个实测验证

**操作**：
```
读取 ~/.workbuddy/skills/market-researcher/SKILL.md
→ 基线：第13行 disable: true（当前禁用，不在可用列表）
→ 用户确认后 Edit: disable: true → disable: false
→ 反馈："已改，下一轮对话生效；本轮快照不会刷新，需下一轮验证"
```
**验证（下一轮）**：用户在 available_skills 中找到了 market-researcher；
对照组 deep-research-clawhub（未改动，仍 disable: true）未出现 → 证明 disable 字段即开关源头。
用户随后在 UI 技能界面确认"确实启用了"。

说明：验证"编辑文件字段 = 重新启用"这一核心机制，A/B 对照排除误判。

## 示例2：启用 github（复测不同 skill 走同一机制）

**背景**：market-researcher 实测 + UI 双验证通过后，用户要求再测一个。

**用户**：你把那个 GitHub 启用

**操作**：
```
定位 ~/.workbuddy/skills/github/SKILL.md（find 命中）
→ 第8行 disable: true
→ Edit: disable: true → disable: false
→ 反馈：与示例1同一手法，下一轮对话生效
```
**附带发现**：顺手 grep `^disable: true` 一次性列出全部 15 个禁用 skill
（wechat-viral-topic / self-improving-agent / visual-master-image / deep-research 全套5个 /
deep-research-clawhub / kdense-literature-review / ontology / github / okr-landing-system /
remotion-best-practices），比 UI 列表更高效。用户回 UI 确认 GitHub 变绿。

说明：验证"不同 skill 共用同一套文件机制"，并演示"列出禁用项"命令的实际产出。

## 示例3：列出禁用的 skill

**用户**：有哪些关着的 skill / 列出禁用的 skill

**操作**：
```
grep -rn "^disable: true" ~/.workbuddy/skills/*/SKILL.md
→ 输出全部禁用 skill 路径 + 行号
```
说明：验证"无需回 UI 翻列表即可查看禁用项"这一核心卖点；grep 范围覆盖
`~/.workbuddy/skills/`，与 UI 禁用清单一致（plugins/ 下另有 1 个需单独补搜）。

## 示例4：禁用无字段的 skill（验证"插入而非改值"分支）

**背景**：v2 评审发现 73% 的 skill（含全部 ybl-*）根本没有 disable 字段，若禁用流程只写
"把 false 改成 true"，Edit 会因 old_string 不存在而失败。需验证"无字段→插入"分支。

**用户**：把 ybl-search-web 禁用

**操作**（走管理器流程）：
```
扫描 ~/.workbuddy/skills/ybl-search-web/SKILL.md
→ 基线：frontmatter 仅 name/description/allowed-tools，无 disable 字段
→ 用户确认后，在 frontmatter 插入一行 disable: true（锚定 frontmatter 闭合的 `---` 之前插入）
→ 反馈："已禁用，下一轮对话生效"
```
**真实对照**：同日下午用户从 UI 手动禁用 ybl-search-web，读其 SKILL.md 发现第7行
自动新增 `disable: true` —— 证明 WorkBuddy 原生禁用机制也是"插入字段"，
管理器"无字段→插入"分支与系统行为一致。测后已改回 `disable: false` 恢复。

说明：覆盖 73% 主流 skill（无字段）的禁用路径，是 C1 修复的核心回归用例。

## 示例5：查看某类 skill（含启用与禁用）

**背景**：用户想先看清"某类技能里哪些开着、哪些关着"，再决定要不要精简其中一部分。

**用户**：查看深度研究类的 skill，启用的和禁用的都列出来

**操作**（纯查看，不改文件）：
```
1. 扫描 ~/.workbuddy/skills/*/SKILL.md 全部（不做状态过滤）
2. 按 name + description 关键词过滤：research / 调研 / 深度研究 / 文献 / 综述
3. 逐个标注状态（强制编号 + ✅/⛔，见 G7；分类展示时编号跨类连续递增）：
   ① deep-research-pro        ✅启用（无 disable 字段）
   ② deep-research-v8         ✅启用（无 disable 字段）
   ③ market-researcher        ✅启用（disable: false）
   ④ ybl-orchestrator         ✅启用（无 disable 字段）
   ⑤ ybl-research-report      ✅启用（无 disable 字段）
   ⑥ ybl-search-academic      ✅启用（无 disable 字段）
   ⑦ deep-research-clawhub    ⛔禁用（disable: true）
   ⑧ deep-research（全套5个）  ⛔禁用（disable: true）
4. 末尾附选择提示："要启/禁用其中某些，直接回复编号即可，如『禁用 1,3』…"
```
说明：演示"查看某类（含启用+禁用）"入口；类别完全靠 description 关键词匹配，
不维护额外标签。纯展示、零文件改动，与启用/禁用严格分离。**输出必须带编号（G7 硬规则）。**

## 示例6：查看后按编号禁用（解决"100+ skill 列表无搜索、逐个打名很烦"痛点）

**背景**：用户装了很多 skill，UI 列表无搜索，想禁用其中好几个却不愿逐个打冗长名称。
先查看、再靠编号选择，是核心用法。

**用户**：查看深度研究类的 skill（先列出编号清单）

**助手输出**（带编号 + 状态 + 选择提示）：
```
① ✅ deep-research
② ⛔ deep-research-clawhub
③ ✅ kdense-literature-review
…（此处列出全部）
要禁用其中某些，直接回复编号，如「禁用 2,5」，无需输入名称。
```

**用户**：禁用 2,5

**助手**（执行前先重述待确认，不改文件）：
```
将禁用（插入 disable:true）：
  ② deep-research-clawhub（当前 disable: true，已禁用，无需操作）
  ⑤ …（举例）
跳过（已禁用 / 自身保护）：…
确认执行请输入"确认"，取消请说"取消"。
```

**用户**：确认

**操作**：按编号映射回【最近一次查看列表】对应技能 → Edit `disable` 字段 → 反馈 ✅/⛔ 结果。

说明：编号选择让用户**点数字即可**，不用打长名称；映射依赖对话上下文里的查看清单。
若用户跨太多轮或清了上下文导致编号失效，提示重述名称或重新查看。关联 G7（编号强制）、
查看流程 step 4 / step 7、启用/禁用流程"编号解析"分支。
推荐触发方式：显式 `@ybl-skill-switch 查看深度研究类的 skill`（见「触发与调用须知」）。
