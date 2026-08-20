---
name: global-market-entry-navigator
description: 帮助企业评估不同国家和区域市场，从市场空间、客户需求、竞争格局、渠道、定价、政策和本地化要求出发，形成市场选择与分阶段进入建议。当用户提到出海、国际化、海外业务、区域市场评估、跨境创业、全球战略、市场进入、Go/No-Go 决策时使用。
description_en: Evaluates and compares international markets for overseas expansion based on market potential, customer needs, competition, channels, pricing, regulations, and localization requirements.
version: 5.1.0
---

# 出海导航 / Global Market Entry Navigator

选对市场，找准进入方式。

## 触发条件

出海、国际化、海外业务、区域市场、跨境创业、全球战略、渠道拓展、市场进入、Go/No-Go、国家筛选、market entry、海外市場参入、是否退出、继续投入还是退出

## 不负责

海外公司注册执行 / 税务最终结论 / 法律合规最终意见 / 海外招聘执行 / 渠道销售执行 / 广告账户代投

## 路由判定 + Reference 按需加载

**第一步：判断路由类型。第二步：仅读取该类型需要的 reference 文件。不要一次性读取所有 reference。**

### 路由判定表

| 信号 | → 轻量 | → 标准 | → 完整 | → 单国深评 | → 再评估 |
|------|--------|--------|--------|-----------|---------|
| 市场数 | 未指定/只说地区 | 2-3 国 | 3+国+列交付物 | 明确只 1 国 | 已在市场中 |
| 上下文 | 无或极简 | 有产品+规模 | 产品+规模+预算 | "已决定进X" | 有运营数据 |
| 问题 | "值得看吗" | "评估可行性" | 列出多项交付物 | "深入分析X" | "继续还是退出" |

**默认**: 标准。信号不足往轻量走。

### Reference 加载规则

判定路由类型后，**仅读取下表中 ✅ 标记的 reference**：

| Reference 文件 | 轻量 | 标准 | 完整 | 单国 | 再评估 |
|---------------|:----:|:----:|:----:|:----:|:-----:|
| `references/market-screening.md` | — | ✅ | ✅ | ✅ | — |
| `references/financial-modeling.md` | — | ✅ | ✅ | — | — |
| `references/entry-mode-execution.md` | — | ✅ | ✅ | ✅ | — |
| `references/risk-monitoring.md` | — | — | ✅ | — | — |
| `references/capability-assessment.md` | — | — | ✅ | ✅ | — |
| `references/industry-overlays.md` | — | ✅ | ✅ | ✅ | — |
| `references/reassessment.md` | — | — | — | — | ✅ |

**轻量路由不读取任何 reference**——SKILL.md 本身包含足够信息完成轻量输出。

---

## 各路由的交付物定义

### 轻量 — 帮用户聚焦

无需读 reference，直接基于 SKILL.md 中的 7 维度定义执行。

交付:
- 第一行结论（BLUF）
- 候选国家推荐或 7 维度快评表格（每维度 1 行评分+1 句依据）
- 🟢/🟡/🔴 Go/No-Go 一行判定
- 每国 Top 1 风险 + Top 1 机会
- 结尾引导: "需要深入对比其中 X 个吗？" 或 "需要我详细展开某个维度吗？"

### 标准 — 评估决策

读取: market-screening + financial-modeling + entry-mode-execution + industry-overlays

交付:
1. **BLUF 结论**（第一行: "A > B > C，推荐先进 A"）
2. **国家对比矩阵**（7 维度 + CAGE 距离修正）
3. **加权评分排序**（展示计算公式+结果）
4. **Go/No-Go 判定**（每国: 结论 + 核心理由 + 翻转条件）
5. **进入模式推荐**（每国推荐 + 理由）
6. **投入估算**（Bottom-up 表格拆解）
7. **Unit Economics**（break-even 条件 + sensitivity 表）
8. ⚡ 每国反直觉洞察 + ⚠️ 隐性成本

### 完整 — 评估 + 执行规划

读取: 全部 6 个 reference（不含 reassessment）

交付: 标准全部 8 项 +
9. **分阶段路线图**（含量化 Go/No-Go Gate）
10. **首 30 天行动计划**（日期/角色/产出物）
11. **信号监控表**（Green/Amber/Red 阈值）
12. **退出成本矩阵**（各 Gate 止损额）
13. **能力缺口评估**（✅/🟡/🔴 + 弥补方式）
14. **类比案例**（每市场 1 个先例: 公司/结果/教训/差异）

### 单国深评 — 已确定目标

读取: market-screening + entry-mode-execution + capability-assessment + industry-overlays

交付:
1. **BLUF**: Go/No-Go + 核心理由
2. **7 维度逐项展开**（每维度 3-5 句深入分析，非表格对比）
3. **CAGE 距离分析**（与出发国的关键差异 Top 3）
4. **进入模式决策树**（完整走一遍，标注选择路径）
5. **该国 Top 5 隐性成本**（带具体数字）
6. **竞品详细画像**（Top 3-5 竞品: 定位/规模/优势/弱点）
7. **3 个类比案例**（含至少 1 个失败）
8. **合作伙伴推荐**（3-5 家具名 + 角色 + 发现渠道）
9. 若 No-Go: 推荐 2 个替代国 + 1 句理由

### 再评估 — Stay / Pivot / Exit

读取: reassessment.md（仅此一个）

交付:
1. **BLUF**: "判定: Stay/Pivot/Exit，理由: [1 句]"
2. **原始假设 vs 实际对照表**
3. **Gate KPI 达成率**
4. **Stay/Pivot/Exit 决策理由**
5. 若 Pivot: 可调整方向 + 验证周期
6. 若 Exit: 退出清单 + 成本 + 再进入条件

---

## 7 维度定义（轻量输出可直接使用）

| 维度 | 回答的问题 | 默认权重 |
|------|-----------|---------|
| 市场规模与增长 | 蛋糕多大、在变大吗? | 25% |
| 客户需求与行为 | 用户要什么、怎么买、愿出多少钱? | 20% |
| 竞争格局 | 谁在做、做得怎样、还有空间吗? | 15% |
| 定价与支付 | 卖多少钱合适、怎么收钱? | 10% |
| 渠道结构 | 通过谁卖、线上还是线下? | 15% |
| 政策与合规 | 牌照/认证/数据驻留/外资限制? | 10% |
| 本地化要求 | 语言/文化/技术适配要多少钱和时间? | 5% |

评分 1-5: 5=高度有利/1=近乎不可行。
按行业调整权重（读 industry-overlays.md 后执行）。

## 执行纪律


### 联网搜索规则

**轻量路由**：可跳过搜索（速度优先，用模型知识+标注 [E]）。
**标准/完整/单国路由**：以下维度的关键数据必须通过 WebSearch 验证，不允许仅靠模型记忆：

| 维度 | 必搜场景 | 搜索关键词模板 |
|------|---------|---------------|
| 市场规模 | TAM/CAGR 数字 | "[country] [industry] market size 2024" OR "[country] [industry] CAGR forecast" |
| 竞争格局 | 头部竞品融资/估值/市占 | "[competitor] funding round" OR "[competitor] revenue valuation 2024" |
| 政策合规 | 牌照/认证/数据法规 | "[country] [regulation name] requirements 2024" OR "[country] foreign investment restrictions" |
| 认证标准 | 认证周期和费用 | "[certification body] [country] application cost timeline" |
| 定价基准 | 当地可比产品价格 | "[product category] pricing [country]" OR "[competitor] pricing [country]" |

**搜索时机**：
1. 先基于模型知识完成初步分析框架
2. 识别标注为 [E] 的关键决策依赖数字（通常 5-10 个）
3. 逐一搜索验证，升级为 [V] 并注明来源
4. 若搜索结果与模型知识冲突，以搜索结果为准并标注

**搜索上限**：标准路由 ≤8 次搜索，完整路由 ≤15 次。避免对每个数字都搜——只搜影响 Go/No-Go 判定的核心数字。

**Sub-Agent 限制**：尽可能避免使用 sub-agent，优先由主 agent 直接完成搜索和分析。

### 数据标注

仅对**决策依赖的核心数字**标注：市场规模/CAGR/市场份额/认证费用/牌照费/投入总额。
格式：`[V]`已验证 / `[E]`估算 / `[R]`范围 / `[O]`过时。
内部计算中间值、权重乘积等不标注。

### 分析规则

- 多国对比时至少 2 国（单国模式除外）
- 给数字不给形容词
- 每国至少 1 条 `⚡ 反直觉洞察`
- 隐性成本标 `⚠️`
- 合作伙伴推荐: 标准级 Top 2 具名 + 发现渠道，完整/单国 3-5 家

### 地缘政治检查（标准+完整+单国 强制）

5 项必答: 制裁/实体清单? 贸易限制联盟? 两用技术管制? 原产地规则? 供应链单点依赖?

### 行业自适应

SaaS → LTV:CAC>3:1 / 消费品 → 到岸毛利>30% / 金融 → 牌照为关键路径 / 医疗 → 注册周期为约束。
未匹配行业 → 自行推导核心约束并声明调权理由。

## 执行步骤

1. **读 query → 判断路由类型**（轻量/标准/完整/单国/再评估）
2. **按加载规则读取对应 reference**（不多读）
3. 若缺必要信息（行业/产品/目标市场），追问后暂停
4. **第一行输出 BLUF 结论**
5. 按路由类型输出交付物（详见上方各路由定义）
6. 结尾 30 秒总结 + 可追问方向

## 可视化输出规则

### 产物形态判定

根据路由复杂度和用户意图，自动选择输出形态：

| 判定条件 | → 产物形态 | 工具 |
|----------|-----------|------|
| 轻量路由 | inline 可视化 | Generative UI (PureShowWidget) |
| 标准路由，用户未要求报告 | inline 可视化 | Generative UI |
| 标准路由 + 用户要求"报告/导出/分享" | HTML 报告文件 | html-report skill |
| 完整/单国路由（交付物 ≥5 项） | HTML 报告文件 | html-report skill |
| 再评估路由 | inline 可视化 | Generative UI |

**简单规则**：交付物 ≤4 项 → Generative UI；交付物 ≥5 项或用户明确要报告 → html-report。

### Generative UI 使用规则（轻量/标准/再评估）

**仅在图表能显著增强理解时使用**，不要为用而用。适合 inline 渲染的场景：
- ≥2 国对比评分 → 雷达图或对比柱图
- 成本/收入有多层拆解 → 瀑布图或堆叠柱图
- 有明确的阈值判定（Go/No-Go/翻转条件）→ 决策卡片
- 时间维度的阶段规划 → 简易时间轴

**不适合 inline 的场景**（纯文字即可）：
- 单一结论 + 简短理由（如"不建议进入，原因是…"）
- 定性分析为主、无量化对比数据
- 用户问题极简（"值不值得看"类）

**要求**：
- 图表配色跟随下方主题规则，禁用深色背景
- 文字结论 + 可视化组件穿插，不堆在末尾

### html-report 模板选择规则（完整/单国路由，或用户要求报告时）

| 数据/诉求特征 | 选择模板 | 原因 |
|---|---|---|
| 多国对比、≥3 维度评分、有雷达/热力图 | **cockpit** | 高信息密度，KPI 卡片 + 多图网格适合多国并排 |
| 完整路由、详细归因、路线图、退出分析 | **editorial** | 长文叙事 + 图表穿插，适合逐步推导结论 |
| 单国评估、轻量/标准输出、简洁对比 | **folio** | 单栏结构，中等信息密度 |

### 主题选择规则

根据用户行业/出海场景匹配明亮色系主题（禁用深色系）：

| 行业/场景 | 选择主题 | 色彩特点 |
|---|---|---|
| SaaS / 互联网 / 科技出海 | **ocean-depths** | 深海蓝绿 `#2D8B8B` + 淡绿底，专业清爽 |
| 消费品 / 电商 / 快消 / 母婴 | **botanical-garden** | 森林绿 `#4A7C59` + 暖白底，自然清新 |
| 金融科技 / 支付 / B2B 贸易 | **modern-minimalist** | 灰阶 + 黑白线条，克制专业 |
| 新能源 / 制造业 / 工业品 | **golden-hour** | 琥珀金 `#D4910A` + 暖白底，温暖典雅 |
| 医疗健康 / 保健品 / 生物科技 | **soft-morandi** | 灰绿 `#7C9A92` + 奶油底，低饱和优雅 |
| 通用 / 多行业混合 | **soft-morandi** | 灰绿 `#7C9A92` + 奶油底，适配广 |

### 图表类型映射

出海分析常见数据结构到 ECharts 图表的映射：

| 数据结构 | 推荐图表 | ECharts 类型 |
|---|---|---|
| 7 维度国家评分对比 | 雷达图 | radar |
| 多国加权总分排名 | 横向柱图 | bar (horizontal) |
| 市场规模/CAGR 时序 | 折线图 | line |
| 进入成本拆解（各阶段） | 瀑布图 | bar (waterfall) |
| 投入 vs 回收 break-even | 双轴折线 | line + multi yAxis |
| 维度占比（渠道/客群） | 环形图 | pie (donut) |
| Stay/Pivot/Exit 决策矩阵 | 热力图 | heatmap |
| 路线图时间轴 | 甘特/阶段条 | custom (gantt pattern) |

### 调用 html-report 时的传参

在 `plan.md` 中声明模板和主题：

```
## Theme
- **Name**: botanical-garden
- **Template**: cockpit
- **选择依据**: 消费品行业，三国对比评分，含雷达图和成本瀑布图，适合高密度看板
```
