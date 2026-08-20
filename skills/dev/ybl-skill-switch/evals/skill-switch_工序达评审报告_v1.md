# skill-switch · 工序达评审报告

> 评审人：工序达（Rex）  
> 五轴审查  
> 2026-07-21

---

## Review Summary

**Verdict:** APPROVE WITH CHANGES

**Overview:** 2 文件、61 行 SKILL.md、4 Gotchas、3 Few-Shots（外置 references/）。定位清晰——一句话启禁 Skill，只改 disable 字段，不删文件。泥总要求极致简洁，整体骨架达标。独立审发现 3 个 Important——白名单自相矛盾、缺 evals/ 目录、description 缺负面触发；3 个 Suggestions。

---

## 🟡 Important

### I1 — 白名单自相矛盾

**Location:** L36-41

**问题**：L37-39 写死了 `skill-switch`、`skill-creator`、`humanizer` 三个白名单成员，但 L41 又说"首次运行时白名单为空或自动生成，不写死特定用户 Skill"。这两句话直接冲突——要么写死，要么不写死，不能两个都写。

**量化影响**：Agent 执行时无法判断白名单到底是哪三个还是动态生成，可能跳过白名单检查直接禁用。

**Fix:** 二选一。泥总要求"通用版"，建议改为：

```
## 白名单

白名单中的 Skill 永不进入禁用清单。

默认白名单：
- skill-switch（自身，禁用后无法再启用）

用户可随时说"把 XX 加入白名单"/"把 XX 移出白名单"管理。
```

只保留自身（这是硬逻辑——禁用了自己就没法再启用自己），其余由用户动态配置。

### I2 — 缺少 evals/ 目录

**Location:** 整个目录结构

**问题**：种子知识质量红线明确要求每个 Skill 必须有 evaluation/ 目录，含 test-cases.yaml + eval-report.md + regression-log.md 三者齐全。当前 skill-switch 目录下只有 SKILL.md + references/，完全没有评估文件。

**量化影响**：无法验证触发准确率 ≥ 90%；无法做回归检查；修改后无法判断是否退步。

**Fix:** 补充 `evals/test-cases.yaml`（至少 10 个用例：启用/禁用/语义匹配/白名单保护/边界触发）+ `evals/eval-report.md`（五维评分）+ `evals/regression-log.md`（首版留空模板）。

### I3 — description 缺少负面触发条件

**Location:** L3

**问题**：种子知识明确要求 description 是"触发契约"，必须包含正面触发 + 负面触发（边界守护）。当前只有正面触发（"用户说'禁用/启用 XX'时触发"），没有说明什么时候**不触发**。

**量化影响**：用户说"关闭电脑""打开网页"等含"关闭/打开"语义的指令时，可能误触发本 Skill。

**Fix:**

```
description: 禁用或启用用户级 Skill。用户说"禁用/启用 XX Skill""把 XX 关掉/打开"时触发。不处理非 Skill 的开关操作（如关闭网页、打开文件）。
```

---

## 🟢 Suggestions

### S1 — Few-Shot 示例缺少"说明"字段

**Location:** references/few-shots.md

**问题**：种子知识模板要求每个示例包含"说明：为什么这个示例重要"。当前 3 个示例只有操作步骤，没有说明。

**Fix:** 每个示例末尾加一行说明，如：

```
说明：验证精确名称匹配 + 单个启用流程
说明：验证精确名称匹配 + 单个禁用流程
说明：验证语义匹配 + 多个批量启用 + 已启用的跳过
```

### S2 — 白名单管理流程缺失

**Location:** 启用流程 / 禁用流程之间

**问题**：L41 提到"用户可随时说'把 XX 加入白名单'追加"，但全文没有描述白名单管理的操作流程。Agent 收到这个指令时不知道该改哪个文件、怎么改。

**Fix:** 在禁用流程后补充一段：

```
## 白名单管理流程

1. 用户说"把 XX 加入/移出白名单"
2. 语义匹配候选 → 列出结果
3. 用户确认 → 在本 SKILL.md 的白名单列表中增删条目
4. 反馈结果
```

### S3 — 缺少 allowed-tools 声明

**Location:** frontmatter

**问题**：种子知识最佳实践第 11 条"权限最小化，allowed-tools 只声明真正需要的工具"。当前 frontmatter 没有声明 allowed-tools。

**Fix:** 在 frontmatter 中添加：

```
allowed-tools: Read, Edit, Glob, Grep
```

只需这四个——Read/Glob/Grep 用于扫描 Skill 列表，Edit 用于改 disable 字段。不需要 Write（不创建文件）、Bash（不执行命令）、WebFetch（不联网）。

---

## What's Done Well

1. **渐进式披露执行到位。** Few-Shot 拆到 references/，SKILL.md 只留一行引用——符合种子知识第 3 条"核心指令进 SKILL.md，细节移入 references/"。
2. **安全边界清晰。** "只改 disable 字段，不删除文件、不改其他内容"+"只管 ~/.workbuddy/skills/"——负面约束明确，不留模糊空间。
3. **Gotchas 来自真实场景。** G1（无 disable 字段）和 G3（用户没确认就执行）都是实际会发生的典型坑，不是臆想的。
4. **61 行——极致简洁达成。** 在泥总"极致简洁"的要求下，没有冗余的背景介绍、没有重复的流程描述、没有多余的装饰性文字。

---

## Verification Story

- 文件数：2（SKILL.md + references/few-shots.md）✅
- Gotchas：4 ✅（每条有避坑方案 ✅）
- Few-Shot：3 ✅（但缺"说明"字段 ❌ S1）
- SKILL.md 行数：61 ✅（≤400）
- 安全：Read+Edit ✅
- frontmatter：name kebab-case ✅ / description 含触发条件 ✅ / 缺负面触发 ❌（I3）/ 缺 allowed-tools ❌（S3）
- 白名单逻辑一致性：❌（I1）
- evals/ 目录：❌（I2）
- 白名单管理流程：❌（S2）
- TODO 残留：无 ✅
- 依赖完整性：references/few-shots.md 存在 ✅

---

## 八维度评分

| 维度 | 权重 | 得分 | 说明 |
|------|------|------|------|
| D1 元数据质量 | 20% | 3/5 | description 有正面触发但缺负面触发 |
| D2 执行引导清晰度 | 15% | 4/5 | 流程清晰，但白名单管理流程缺失 |
| D3 领域知识密度 | 15% | 4/5 | Gotchas 覆盖了核心坑，简洁有效 |
| D4 工作流完整性 | 15% | 4/5 | 启用/禁用流程完整，白名单管理缺流程 |
| D5 输入输出清晰度 | 10% | 5/5 | 输入（用户指令）→ 输出（disable 字段变更+反馈）清晰 |
| D6 资源利用 | 10% | 4/5 | references 拆分到位，但缺 evals/ 目录 |
| D7 写作质量 | 10% | 5/5 | 极致简洁，无废话 |
| D8 范围与聚焦 | 5% | 5/5 | 只做启禁，不越界 |

**加权总分：4.15 / 5.0 → 可发布（≥ 4.0），但需先修复 I1-I3**
