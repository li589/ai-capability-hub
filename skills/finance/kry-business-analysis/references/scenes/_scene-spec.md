# 场景定义格式规范

## 文件命名

- 文件名用英文短横线连接，如 `boss-daily.md`
- 统一放在 `references/scenes/` 目录下

## 文件结构

每个场景文件 **必须** 包含以下章节（按顺序）：

---

### 1. 元信息（YAML frontmatter）

```yaml
---
id: S1
name: 经营日报
level: brand          # brand=总部 | region=区域 | store=门店 | multi=多层级
period: daily         # daily | weekly | monthly | on_demand
triggers:
  - 经营日报
  - 每日经营概览
  - 今天生意怎么样
  - 日报
---
```

**level 说明**：

| 值 | 含义 | orgStatisticsType | shopIds 策略 |
|---|---|---|---|
| brand | 总部层级 | BY_BRAND + BY_SHOP | 全品牌（空数组或全量） |
| region | 区域层级 | BY_SHOP | 仅辖区门店 shopIds |
| store | 门店层级 | BY_SHOP | 单店 shopId |
| multi | 多层级共用 | 根据当前用户角色动态决定 | 动态 |

---

### 2. 数据计划（Data Plan）

描述需要调用的 API 列表，每个 API 包含：

```markdown
## 数据计划

### API-1: 店内营收统计
- **路径**: `/open/standard/report/business/income/v3/list`
- **入参模板**:
  ```json
  {
    "dateRange": {"startDate": "{{yesterday}}", "endDate": "{{yesterday}}"},
    "shopIds": {{shopIds}},
    "periodType": "BY_DAY",
    "orgStatisticsType": "BY_BRAND",
    "couponStatisticalType": "BY_NAME",
    "storeStatisticalType": "COMBINE",
    "pageBean": {"pageNum": 1, "pageSize": 1000}
  }
  ```
- **取数字段**: saleAmt, businessIncomeAmt, orderCnt, avgCustomerAmtAfterDiscount, reopenTableRate, orderPeopleCnt
- **用途**: 核心指标卡片
```

**入参模板变量**：

`dateRange` 为对象类型，模板中用 `"dateRange": {"startDate": "{{变量}}", "endDate": "{{变量}}"}` 格式。

| 变量 | 含义 | 展开值（日期字符串） |
|------|------|------|
| `{{today}}` | 当天日期 | `2026-07-01` |
| `{{yesterday}}` | 昨天日期 | `2026-06-30` |
| `{{dayBeforeYesterday}}` | 前天日期 | `2026-06-29` |
| `{{thisWeekStart}}` | 本周一 | `2026-06-30` |
| `{{thisWeekEnd}}` | 本周截止 | `2026-07-06`（或 `{{today}}`） |
| `{{lastWeekStart}}` | 上周一 | `2026-06-23` |
| `{{lastWeekEnd}}` | 上周日 | `2026-06-29` |
| `{{thisMonthStart}}` | 本月1号 | `2026-07-01` |
| `{{thisMonthEnd}}` | 本月末 | `2026-07-31`（或 `{{today}}`） |
| `{{lastMonthStart}}` | 上月1号 | `2026-06-01` |
| `{{lastMonthEnd}}` | 上月末 | `2026-06-30` |
| `{{periodStart}}` / `{{periodEnd}}` | 用户指定范围 | 由用户输入决定 |
| `{{compareStart}}` / `{{compareEnd}}` | 对比周期 | 由主周期推算 |
| `{{shopIds}}` | 门店ID数组 | `["7758479","60096115"]` |
| `{{brandShopIds}}` | 品牌全部门店 | `[]`（空数组=全部） |

**`pageBean` 固定格式**：`{"pageNum": 1, "pageSize": N}`（字段名为 `pageNum`，非 pageNo/pageIndex）

**`couponStatisticalType`**：可选 `BY_NAME`（按券名称）或 `BY_SOURCE`（按平台），无 `ALL` 值

---

### 3. 报告模板（Report Template）

定义报告的板块结构：

```markdown
## 报告模板

### 板块1: 核心指标卡片
- **图表类型**: kpi-card
- **数据来源**: API-1
- **指标清单**:
  - 营业额(saleAmt) + 环比
  - 营业收入(businessIncomeAmt) + 环比
  - 订单数(orderCnt) + 环比
  - 客单价(avgCustomerAmtAfterDiscount) + 环比
- **环比计算**: (今值 - 昨值) / 昨值 × 100%
- **样式**: 绿涨红跌，箭头标识

### 板块2: 门店排行
- **图表类型**: bar-ranking
- **数据来源**: API-2
- **排序**: 按 saleAmt 降序
- **展示**: Top5 + Bottom5
```

---

### 4. AI 分析指令（Analysis Instructions）

指导 AI 如何生成洞察文本：

```markdown
## AI 分析指令

### 异动判定规则
- 环比涨跌超过 ±20% → 标记为「显著变化」
- 环比涨跌超过 ±50% → 标记为「异常波动」
- 连续3天下降 → 标记为「持续下滑」

### 洞察生成规则
1. 必须基于数据，禁止编造
2. 每条洞察包含：现象 + 数据支撑 + 可能原因
3. 最多生成 5 条洞察，按重要性排序
4. 建议必须可执行，避免空泛

### 结论模板
- 正面: "{{指标}}表现优异，{{环比方向}}{{百分比}}%，主要由{{归因}}贡献"
- 负面: "{{指标}}出现下滑，{{环比方向}}{{百分比}}%，建议关注{{建议方向}}"
```

---

### 5. ECharts 配置（Charts Config）

引用图表注册表中的图表类型，填充数据映射：

```markdown
## ECharts 配置

### chart-1: 核心指标卡片
- **引用**: charts/_chart-registry.md#kpi-card
- **数据映射**:
  - title[0] = "营业额"
  - value[0] = saleAmt
  - trend[0] = 环比百分比
  - unit[0] = "元"
```

---

## 场景执行流程

AI 收到用户请求后的标准执行流程：

```
1. 意图识别 → 匹配 triggers 关键词 → 确定场景 ID
2. 加载场景文件 → 解析数据计划
3. 确定层级 → 根据 level 决定 orgStatisticsType 和 shopIds
4. 如需环比 → 同时拉取对比周期数据
5. 按 API 列表逐一调用（可并行无依赖的 API）；用 fetch.mjs `-o` 按对应 manifest 的 sources 文件名保存到同一数据目录
6. 数据校验 → 检查空数据容错
7. **构建组件数据**：`node scripts/report-data.mjs build --manifest scripts/manifests/<场景>.mjs --data-dir <目录> --out report-data.json`，由构建库确定性完成聚合/环比/排序/派生，禁止心算
8. 以 report-data.json 的 facts 为依据组织洞察文本 → 生成 Markdown 分析
9. 加载 charts/_chart-registry.md → 使用「HTML 报告外壳模板」骨架 + 完整 CSS 主题 + COLORS 色板 → 用 components 填充数据 → 渲染 HTML 报告
10. 报告质检 → 执行 check-report.mjs（退出码须 0）+ init.md#报告质检 检查项，发现问题先修复再输出
11. 输出最终报告
```

> **构建库接入**：每个场景对应一个 `scripts/manifests/<场景>.mjs`，声明 `sources`（数据源文件名映射）与 `build(lib, data)`（组件计算规则）。组件数据一律由构建库产出，详见 [SKILL.md#组件数据构建库](../../SKILL.md)。

## 降级策略

当部分数据获取失败时：

| 失败情况 | 降级方式 |
|---------|---------|
| 对比周期数据拉取失败 | 去掉环比，仅展示当期数据 |
| 某个 API 完全无数据 | 跳过对应板块，在报告末尾注明 |
| 门店名称缺失 | 用 shopId 代替 |
| 全部 API 失败 | 输出错误提示，建议检查授权/日期范围 |
