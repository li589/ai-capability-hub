---
name: qingflow-business-system-builder
display_name: 轻流业务系统搭建
display_name_en: Qingflow Business System Builder
description: 构建、更新、修复、审核、发布和验证轻流业务系统。覆盖表单排版、视图、流程、门户、Word 打印模板及数据播种的端到端强制规范与最佳实践。
description_zh: 构建、更新、修复、审核、发布和验证轻流业务系统。覆盖表单排版、视图、流程、门户、Word 打印模板及数据播种的端到端强制规范与最佳实践。
description_en: Build, update, repair, audit, publish, and validate Qingflow
  business systems. End-to-end conventions covering form layout, views,
  workflows, portals, Word print templates, and data seeding.
category: business
version: 1.0.0
author: 轻流
visibility: public
disable-model-invocation: true
---

# 轻流业务系统搭建 Skill

## 快速上手

**这个 Skill 适合你吗？**

- ✅ 你需要在轻流中从零搭建一套业务系统（如采购管理、销售管理、出入库管理）
- ✅ 你需要修复、审核、发布或验证已有的轻流应用
- ✅ 你希望按照轻流最佳实践自动完成表单排版、视图配置、流程设计和门户搭建
- ✅ 你已连接轻流 MCP（`qingflow-app-builder` + `qingflow-app-user`）

**这个 Skill 不适合：**

- ❌ 轻流账号开通、工作区创建等平台管理操作
- ❌ 非轻流平台的业务系统搭建
- ❌ 纯前端页面开发或与轻流无关的代码编写
- ❌ 浏览器自动化操作（本 Skill 全程走 MCP，不操作浏览器）

**怎么开始？**

直接在对话中描述你要搭建的业务系统，例如：
- "帮我搭建一套采购管理系统"
- "给已有的订单应用加上审批流程"
- "给门户添加数据看板"

AI 会根据本 Skill 的规范自动执行全部步骤。

---

**这是强制规范，不是建议。本文件已将所有 reference 内容内联，无需外部文件。每条规则都是 non-negotiable。跳过任何一条 = 任务未完成。**

每次行动前必须自问："我即将做的事情是否满足本规范中所有适用规则？" 如果答案是"否"，停下来，按规范正确执行。如果某条规则在当前工具版本下确实无法执行，STOP 并报告——不允许静默跳过。

---

## 零、MCP 依赖

- `qingflow-app-builder`：应用、字段、排版、视图、按钮、关联资源、图表、流程、门户、发布
- `qingflow-app-user`：记录、任务、导入导出、流程动作、业务数据验证
- 登录和切换工作区使用轻流 MCP，禁止浏览器自动化

> **注意：** 流程相关操作（读取、创建、修改）全部通过 `qingflow-app-builder` 的 `app_flow_get` / `app_flow_apply` 等工具完成，没有独立的 workflow-builder MCP。

---

## 一、硬性规则

### 编号

- 使用轻流系统默认编号。禁止新增冗余的订单/单据/项目/任务编号字段。
- 关联匹配使用真实数据 ID，禁止用显示编号代替。

### 流程状态

- 禁止创建 `审核状态`、`审批状态`、`当前审批节点`、`当前流程状态` 等与系统流程节点重复的字段。
- 禁止用 Q-Robot、公式或人工填写维护系统流程状态。
- `订单履约状态`、`发货状态`、`回款状态`、`库存状态` 等独立业务状态可保留，但必须表达流程节点以外的业务事实。

### 表单排版

- 普通字段一行四个（`rows` 矩阵中）。
- 一行最多两个引用/关联字段。复杂引用字段单独占行。
- 长文本、附件、地址、子表、Q-Linker、代码块各占独立行。
- 写入后回读实际行列分组，移除隐藏/系统/已删除字段污染。

### 视图 —— 不可跳过

每个应用最终只能有三个业务视图：一个 `table`、一个 `board`、一个 `card`。

**三步强制流程：**

1. 创建三个业务视图后，回读全部 view_key。
2. 删除这三个目标之外的所有视图——包括 `全部数据`、`我的数据`、`我发起的`、`待办`、`已办`、`抄送` 等系统视图，以及任何历史/额外视图。
3. 再次回读，确认视图总数 = 3，类型集合 = `{table, board, card}`。

**这步不可跳过。不可留下系统视图。**

- 视图展示顺序：`table → board → card`，表格视图必须是默认入口。
- 表格列：第一列选项类型字段（状态/类型/分类），第二列核心名称字段。没有选项字段时才把核心名称放第一列并记录例外。
- 查询条件：每个应用主表格视图必须有模糊查询，`query_conditions.rows` 只能有一行、三个字段，顺序 `选项 → 日期 → 核心名称`，`exact=false`。禁止增加第二行。门户引用的表格视图不豁免。

### 关联与按钮

多应用方案必须具备：真实关联 + 关联选择后引用填充（≥3个关键字段）+ 核心应用有创建下游记录的当前记录按钮 + 核心详情反向查看 + 业务数据回写。

按钮配置规则：
- 只为有明确主从关系的应用配置按钮，不为凑数量新增。
- 回读按钮目录，已有同义按钮先按 button_id 修复，不重复创建。
- 同一动作必须同时绑定 `list`（数据操作主按钮）和 `detail`（数据详情主按钮），均设 `primary=true`。
- 表格视图禁止保留自定义 `header` 顶部按钮。
- 按钮名称使用明确业务动词（如 `新建销售开票`）。
- 按钮使用"当前数据 ID → 下游引用字段"传递记录。
- 发布后回读 compiled_match_rules：来源必须是 `数据ID(-17)`，目标必须是预期引用字段。

### Q-Robot

更新筛选优先级：
1. 目标 `数据ID` = 来源引用/关联字段（优先）
2. 无引用字段时：目标 `数据ID` = 来源保存的数据 ID
3. 无引用和数据 ID 时：目标系统编号 = 来源系统编号

禁止模糊匹配。零条或多条匹配时停止并保留异常。已有直接引用关系时禁止冗余新增目标数据 ID 或系统编号字段。

### 流程

一个完整的业务流程必须覆盖发起、审批、执行和确认等必要阶段。禁止只创建一个 `applicant` 节点就结束。禁止说"流程已完成"但实际只有 1 个节点。

**流程决策：** 只在包含审批、指派、填写/抄送阶段、提醒、路由、状态同步、任务处理或字段权限控制时才创建流程。主数据和纯记录型应用（如物料、供应商、客户）不需要流程。

---

#### 一、流程搭建完整步骤

**Step 1 — 回读现有流程：**

使用 `app_flow_get` 工具读取当前应用流程，确认当前是否有流程、有几个节点、是什么类型。新应用通常有一个自动生成的 `applicant` 节点。

**Step 2 — 确定节点数量和类型：**

节点类型：

| type | 含义 | 何时使用 |
|------|------|---------|
| `applicant` | 发起节点 | 流程起点。谁发起谁是申请人。一个流程只能有一个。 |
| `approval` | 审批节点 | 需要某人审批通过/驳回。适用于部门主管、财务、总经理等审批环节。 |
| `filling` | 填写节点 | 需要某人填写/更新数据。适用于执行、确认、验收等操作环节。 |
| `gateway` | 分支/汇合 | 平行分支用 `mode=parallel`，分支汇合用 `mode=join`。 |

节点数取决于业务阶段数。典型采购流程至少 5-6 个节点，销售流程 5-6 个，出入库 3 个。

**Step 3 — 构建完整 spec JSON 并通过 `app_flow_apply` 写入：**

```json
{
  "nodes": [
    {"type": "applicant", "id": 1, "name": "发起采购申请", "attrs": {"fieldPermissions": []}},
    {"type": "approval",   "id": 2, "name": "部门主管审批", "attrs": {"fieldPermissions": []}},
    {"type": "approval",   "id": 3, "name": "财务审批",     "attrs": {"fieldPermissions": []}},
    {"type": "filling",    "id": 4, "name": "采购执行",     "attrs": {"fieldPermissions": []}},
    {"type": "filling",    "id": 5, "name": "到货确认",     "attrs": {"fieldPermissions": []}},
    {"type": "filling",    "id": 6, "name": "完成归档",     "attrs": {"fieldPermissions": []}}
  ],
  "edges": {
    "edges": [
      {"from": 1, "to": 2}, {"from": 2, "to": 3},
      {"from": 3, "to": 4}, {"from": 4, "to": 5}, {"from": 5, "to": 6}
    ]
  }
}
```

写入后执行发布。

**Step 4 — 回读验证：**

使用 `app_flow_get` 回读，确认节点数和连线数正确。每个节点有了后端分配的真实 ID（不再是 spec 中的临时数字 ID）。

---

#### 二、逐节点字段权限配置

每个节点的 `attrs.fieldPermissions` 数组声明该节点对每个字段的权限。**必须覆盖全部表单业务字段**，不能只声明本节点的可编辑字段。

**fieldPermissions 格式：** 每个权限项包含 `fieldId`（整数，从 record schema 的 `field_id` 获取）和 `fieldAuth`（权限值）。

```json
{
  "type": "approval",
  "id": 2,
  "name": "部门主管审批",
  "attrs": {
    "fieldPermissions": [
      {"fieldId": 463452399, "fieldAuth": "readonly"},
      {"fieldId": "field_463452400", "fieldAuth": "readonly"},
      {"fieldId": "field_463452402", "fieldAuth": "readonly"},
      {"fieldId": "field_463452403", "fieldAuth": "hide"},
      {"fieldId": "field_463452408", "fieldAuth": "readonly"},
      {"fieldId": "field_463452409", "fieldAuth": "hide"}
    ]
  }
}
```

**字段 ID 获取方式：** 先用 `app_get` 或 `record_insert_schema_get` 回读应用的字段列表，拿到每个字段的 `field_id`（格式为 `field_XXXXXXXXX`）。

**权限取值：**

| permission | 含义 |
|-----------|------|
| `edit` | 当前节点可编辑 |
| `readonly` | 只读展示，不可修改 |
| `hide` | 完全隐藏 |

**逐节点权限分配规则：**

1. **申请人节点（第一个节点）：** 只有首节点需要填写的字段设 `edit`。所有后续流程分区及其内部字段全部设 `hide`。
2. **审批节点：** 已填写的业务字段设 `readonly`。审批意见/备注字段设 `edit`。执行类字段（如实际采购量、到货数量）设 `hide`。
3. **执行/填写节点：** 历史审批信息设 `readonly`。本节点需要填写的字段设 `edit`。后续节点字段设 `hide`。
4. **最终节点：** 全部历史字段设 `readonly`。只开放归档备注等收尾字段为 `edit`。

**权限配置示例（采购订单 6 节点完整 JSON）：**

```json
{
  "nodes": [
    {
      "type": "applicant", "id": 1, "name": "发起采购申请",
      "attrs": {"fieldPermissions": [
        {"fieldId": "field_供应商", "fieldAuth": "edit"},
        {"fieldId": "field_采购日期", "fieldAuth": "edit"},
        {"fieldId": "field_预计到货日", "fieldAuth": "edit"},
        {"fieldId": "field_采购状态", "fieldAuth": "edit"},
        {"fieldId": "field_采购明细", "fieldAuth": "edit"},
        {"fieldId": "field_采购总额", "fieldAuth": "edit"},
        {"fieldId": "field_备注", "fieldAuth": "edit"}
      ]}
    },
    {
      "type": "approval", "id": 2, "name": "部门主管审批",
      "attrs": {"fieldPermissions": [
        {"fieldId": "field_供应商", "fieldAuth": "readonly"},
        {"fieldId": "field_采购日期", "fieldAuth": "readonly"},
        {"fieldId": "field_预计到货日", "fieldAuth": "readonly"},
        {"fieldId": "field_采购状态", "fieldAuth": "readonly"},
        {"fieldId": "field_采购明细", "fieldAuth": "readonly"},
        {"fieldId": "field_采购总额", "fieldAuth": "readonly"},
        {"fieldId": "field_备注", "fieldAuth": "edit"}
      ]}
    },
    {
      "type": "approval", "id": 3, "name": "财务审批",
      "attrs": {"fieldPermissions": [
        {"fieldId": "field_供应商", "fieldAuth": "readonly"},
        {"fieldId": "field_采购日期", "fieldAuth": "readonly"},
        {"fieldId": "field_预计到货日", "fieldAuth": "readonly"},
        {"fieldId": "field_采购状态", "fieldAuth": "readonly"},
        {"fieldId": "field_采购明细", "fieldAuth": "readonly"},
        {"fieldId": "field_采购总额", "fieldAuth": "readonly"},
        {"fieldId": "field_备注", "fieldAuth": "edit"}
      ]}
    },
    {
      "type": "filling", "id": 4, "name": "采购执行",
      "attrs": {"fieldPermissions": [
        {"fieldId": "field_供应商", "fieldAuth": "readonly"},
        {"fieldId": "field_采购日期", "fieldAuth": "readonly"},
        {"fieldId": "field_预计到货日", "fieldAuth": "edit"},
        {"fieldId": "field_采购状态", "fieldAuth": "edit"},
        {"fieldId": "field_采购明细", "fieldAuth": "readonly"},
        {"fieldId": "field_采购总额", "fieldAuth": "readonly"},
        {"fieldId": "field_备注", "fieldAuth": "edit"}
      ]}
    },
    {
      "type": "filling", "id": 5, "name": "到货确认",
      "attrs": {"fieldPermissions": [
        {"fieldId": "field_供应商", "fieldAuth": "readonly"},
        {"fieldId": "field_采购日期", "fieldAuth": "readonly"},
        {"fieldId": "field_预计到货日", "fieldAuth": "readonly"},
        {"fieldId": "field_采购状态", "fieldAuth": "edit"},
        {"fieldId": "field_采购明细", "fieldAuth": "readonly"},
        {"fieldId": "field_采购总额", "fieldAuth": "readonly"},
        {"fieldId": "field_备注", "fieldAuth": "edit"}
      ]}
    },
    {
      "type": "filling", "id": 6, "name": "完成归档",
      "attrs": {"fieldPermissions": [
        {"fieldId": "field_供应商", "fieldAuth": "readonly"},
        {"fieldId": "field_采购日期", "fieldAuth": "readonly"},
        {"fieldId": "field_预计到货日", "fieldAuth": "readonly"},
        {"fieldId": "field_采购状态", "fieldAuth": "readonly"},
        {"fieldId": "field_采购明细", "fieldAuth": "readonly"},
        {"fieldId": "field_采购总额", "fieldAuth": "readonly"},
        {"fieldId": "field_备注", "fieldAuth": "edit"}
      ]}
    }
  ],
  "edges": {
    "edges": [
      {"from": 1, "to": 2}, {"from": 2, "to": 3},
      {"from": 3, "to": 4}, {"from": 4, "to": 5}, {"from": 5, "to": 6}
    ]
  }
}
```

**fieldPermissions 关键规则：**
- 必须覆盖全部表单业务字段，不能只声明本节点可编辑的字段。未声明的字段默认行为不可控。
- 分区标题和分区内部字段都要配置权限，不能只处理其中一层。依赖标题 hide 级联隐藏子字段不可靠。
- 子表字段作为一个整体字段配置（`field_采购明细`），不需要展开到子表内部的每个子字段。
- 禁止新增或编辑冗余审核状态字段。

---

#### 三、更新已有流程的权限

已有流程需要修改权限时，使用 `app_flow_apply` 的 `patch_nodes` 模式，禁止重建节点或改变节点 ID。

`patch_nodes` 数据格式：
```json
[
  {
    "id": "90690527",
    "set": {
      "attrs": {
        "fieldPermissions": [
          {"fieldId": "field_463452399", "fieldAuth": "edit"},
          ...
        ]
      }
    }
  }
]
```

**禁止做法：**
- 禁止为改权限而重建整个流程 spec（会丢失后端分配的节点 ID）
- 禁止减少、重建或重新编号现有节点和连线
- 发布后必须读发布版本快照，不只看草稿
- 逐节点统计 edit/readonly/hide 数量，确认覆盖全部表单字段
- 确认发布前后节点数、连线数和条件分支数一致

---

#### 四、节点角色绑定

每个节点绑定的处理人必须是工作区存在的真实成员或角色。**默认全部绑定当前登录用户**，确保流程能跑通。完成后明确告知用户所有节点默认设为自己的账号，需要手动调整。

**禁止创建没有处理人的空节点。**

---

#### 五、分支与汇合（gateway）

需要平行审批或多分支时使用 `gateway` 节点：

```json
{"type": "gateway", "id": 10, "name": "分支", "attrs": {"mode": "parallel"}},
// ... 分支节点 ...
{"type": "gateway", "id": 20, "name": "汇合", "attrs": {"mode": "join"}}
```

分支节点权限规则：
- 每个分支节点 hide 同级其他分支字段
- 汇合后的节点 readonly 展示判定所需历史，hide 未来字段

---

#### 六、状态回写

- 下游完成后回写核心应用的状态、累计金额、累计数量或完成进度
- 多次发货、多次回款用累计逻辑，不简单覆盖历史值
- 核心记录完结后限制关键字段修改
- 审核进度优先用系统流程状态；履约、发货、回款等业务进度才用独立业务状态

---

## 二、门户规则 —— 不可跳过

门户/工作台/数据看板任务必须满足以下所有规则。

### 图表丰富度 —— 不可过拟合

**禁止只放指标卡+柱状图两种类型就结束。** 那和 Excel 透视表没区别。同一个门户必须根据实际业务数据，覆盖至少 4 种不同图表类型。

| 数据类型 | 用什么图表 | 示例 |
|---------|-----------|------|
| 总量/计数/金额 | 指标卡（target） | 物料总数、采购总额 |
| 状态/分类占比 | 柱状图（bar）或条形图 | 采购状态分布、物料分类占比 |
| 日期/时间变化趋势 | 折线图（line）或面积图 | 月度采购金额、销售额趋势 |
| 排行/对比 | 横向条形图 | 供应商采购额排行 |
| 多字段明细 | 汇总表（summary） | 库存明细、订单明细 |
| 达成率/完成度 | 进度图（progress）或仪表图 | 采购到货率、订单完成率 |

**必须根据数据实际维度来选择，不允许所有门户套用同一组图表类型。** 有日期字段才做趋势，有排行需求才做条形图，不为了凑数硬加。

每张图表必须回读验证且 `beingShowTitle=false`。

### 筛选器 —— 必须有一个

有且仅有一个 `source_type=filter`。PC：`x=0, cols=24, rows=3`。移动：`x=0, cols=6, rows=1`。默认 `dftJudgeType=2`（"包含"）。1-3 个文本/选项筛选项。如果 MCP 创建 filter 失败，必须在结果中明确标注，并指导用户在轻流 UI 中手动添加。

### 指标卡

≤6 张，PC 全部同行 `rows=4`。宽度：1→24, 2→12+12, 3→8+8+8, 4→6×4, 5→4+5+5+5+5, 6→4×6。

### 表格视图

至少一个全宽（`cols=24`）表格视图用于明细钻取。

### 门户完成标准

以下四项全部满足才能报告门户完成，缺任何一项 = 不合格：

- [ ] 筛选器：有且仅有一个，PC 24×3，dftJudgeType=2
- [ ] 图表类型 ≥ 4 种，且类型选择与实际数据维度匹配
- [ ] 至少一个全宽表格视图
- [ ] 所有图表组件 `beingShowTitle=false`，指标卡 `selectedMetrics[].fieldName` 不是系统默认名

### 布局

- PC：24 栅格。移动：6 栅格，按业务顺序单列重排，禁止照搬 PC 坐标。
- 汇总表和复杂明细必须 `cols=24`。只有低密度趋势/分布图可 `12+12`。
- 禁止 `source_type=grid`、快捷入口、九宫格、应用跳转按钮。

### 图表创建流程 —— 先读后写，不可跳过

**每张图表（含指标卡和柱状图）必须执行以下五步：**

**Step 1** — 检查版本和契约：使用 `builder_tool_contract` 获取最新契约。

**Step 2** — 先读取完整配置：
使用 `app_get`（含 charts 参数）和 `chart_get` 读取图表完整配置。
必须保留：`selectedDimensions`、`selectedMetrics`、`dataSource`、`beforeAggregationFilterMatrix`、`afterAggregationFilterMatrix`、`chartStyleConfigs`、`conditionFormatMatrix`、`displayLimitConfig`、`rawDataConfigDTO`。禁止只提交孤立片段。

**Step 3** — 原位修改：从回读结果的 `.config` 复制完整配置。按 `styleConfigType` 查找并原位修改，不存在时才新增。禁止删除其他有效 styleConfigType。

**Step 4** — 完整回写（`app_charts_apply`）：
```json
[{"chart_id": "真实ID", "name": "业务名称", "chart_type": "target", "config": {/* 完整config */}}]
```
正确层级：`config.chartStyleConfigs`，不是顶层 `chartStyleConfigs`。

**Step 5** — 回读验证（`chart_get`）：
只有 `status=success`、`failed=0`、`verified=true` 且回读样式值匹配时才能报告成功。

### 指标卡样式 —— 6 个 chartStyleConfigType 必须全部配置

所有 `styleValue` 必须是字符串，禁止布尔值或数字。字号也是字符串。

```json
{"styleConfigType": "indicatorAlignment", "styleDetailList": [
  {"styleDetailType": "fold", "styleValue": "false"}, {"styleDetailType": "align", "styleValue": "center"}]}
{"styleConfigType": "contentMiddle", "styleDetailList": [
  {"styleDetailType": "fold", "styleValue": "false"}, {"styleDetailType": "switchOn", "styleValue": "true"},
  {"styleDetailType": "titleSize", "styleValue": "14"}, {"styleDetailType": "contentSize", "styleValue": "36"},
  {"styleDetailType": "titleColor", "styleValue": "#494F57"}, {"styleDetailType": "contentColor", "styleValue": "#121315"}]}
{"styleConfigType": "indicatorPrimary", "styleDetailList": [
  {"styleDetailType": "fold", "styleValue": "false"}, {"styleDetailType": "displayName", "styleValue": "true"},
  {"styleDetailType": "textSize", "styleValue": "13"}, {"styleDetailType": "contentSize", "styleValue": "36"},
  {"styleDetailType": "textColor", "styleValue": "#494F57"}, {"styleDetailType": "contentColor", "styleValue": "#121315"}]}
{"styleConfigType": "colorBackground", "styleDetailList": [
  {"styleDetailType": "color", "styleValue": "#ffb3ba"}]}
{"styleConfigType": "card", "styleDetailList": [
  {"styleDetailType": "fold", "styleValue": "false"}, {"styleDetailType": "borderColor", "styleValue": "#ffb3ba"},
  {"styleDetailType": "backgroundColor", "styleValue": "#ffb3ba"}]}
{"styleConfigType": "title", "styleDetailList": [
  {"styleDetailType": "fold", "styleValue": "false"}, {"styleDetailType": "switchOn", "styleValue": "false"},
  {"styleDetailType": "fontSize", "styleValue": "16"}, {"styleDetailType": "color", "styleValue": "#121315"}]}
```

同时必须把 `selectedMetrics[].fieldName` 改为业务名称（如 `物料总量`、`客户总量`）。禁止保留 `数据总量`、`数据数量`、`汇总值`。

### 非指标卡图表样式

柱状图/折线图等：`chart_get` 先读取完整配置，设置白色背景 `#FFFFFF`、浅边框 `#E6EAF0`、`title.switchOn: "true"` 和明确 `chartName`。

### 门户组件标题 —— beingShowTitle

**每个门户图表组件**必须设 `config.beingShowTitle=false`。回读必须显示 `chartConfig.beingShowTitle=false`。

这是门户层设置，与图表内部 `title.switchOn` 是不同层级。禁止通过清空 `section.title`、清空 `chartName`、修改 `dash_style_config` 或只改图表内部 `title.switchOn` 来模拟。

### 颜色色组

同一指标行只能使用一个色组，按顺序从左到右取色：

| 场景 | 颜色 |
|------|------|
| 库存/仓储/生产 | `#e3fdfd`, `#cbf1f5`, `#a6e3e9`, `#71c9ce` |
| 采购/到货/回款/履约 | `#d7fbe8`, `#9df3c4`, `#62d2a2`, `#1fab89` |
| 客户/综合/5-6跨主题 | `#ffb3ba`, `#ffdfba`, `#ffffba`, `#baffc9`, `#baeffe`, `#b3cde0`, `#ff677d`, `#d4a5a5` |

普通图表：白底 `#FFFFFF`，浅边框 `#E6EAF0`，辅助文字 `#767E89`/`#494F57`，主体数据 `#121315`。汇总表表头 `#EFF2F8`，字号 13，单元格垂直居中。默认主题 `themeId=4`。

### 禁止做法

- 禁止提交孤立 `chartStyleConfigs` 片段探测后端
- 禁止用 `dash_style_config` 设置指标卡内部样式
- 禁止只看 HTTP 200 报告成功——必须 `chart_get` 回读验证
- 禁止按报表名称猜测目标——必须用 `chart_id`
- 禁止覆盖或清空 `selectedMetrics`
- 禁止把 `styleValue` 写成布尔值或数字
- 禁止修改后不做 `chart_get` 回读
- 遇到 500 错误：先恢复原完整配置，检查字段层级和数据类型，不得盲目重试

---

## 三、数据清理与播种（仅在用户明确要求时执行）

### 清空

1. 从应用包回读全部 app_key
2. 用 `system:all` 读取记录，处理分页，收集的记录 ID 数等于 total_count
3. 删除前保存应用、记录数量和真实 record_id 清单
4. 按逆依赖顺序删除：下游过程数据 → 主业务数据 → 产品与基础字典
5. 使用 `view_id=system:all` 执行删除
6. 删除后回读所有应用，总数归零才能报告清空完成

### 播种

1. 每个应用先使用 `record_insert_schema_get` 读取新增记录 Schema
2. 先录基础字典，再录主业务数据，最后录下游数据
3. 引用数据指向本轮已创建的真实上游记录 ID
4. 录入完成后验证引用关系、自动填充和记录数量

**内容规范：**
- 贴合真实行业、岗位、客户、产品、金额、日期和业务阶段
- 禁止出现 `模拟`、`测试`、`虚拟`、`样例数据`
- 禁止使用 `客户A`、`产品1`、`张三测试` 等低质量占位
- 跨应用名称、金额、日期和引用关系必须一致
- 未指定数量时每个业务应用约 3 条，覆盖主要状态

**外部副作用：** 发邮件、真实开票、短信、支付、外部 API 和 Q-Robot 应用，写入前检查是否触发真实动作。可能触发时停止并说明，不得为了"覆盖所有应用"而执行。

---

## 四、Word 打印模板

### 能力边界

- 使用轻流当前 Word 打印模板能力。禁止配置已下架的旧版打印设计器。
- 本地完成 `.docx` 样式，再写入真实轻流字段占位符。

### 占位符获取优先级

1. 从轻流 Word 打印模板配置中复制的官方占位符
2. 已在同一应用中确认可用的模板
3. Builder MCP 返回的真实 `que_id` + 编码脚本

禁止：根据字段名猜测 Token、根据 app_key 猜测字段 ID、跨应用跨工作区复用 Token。

### que_id 编码

使用附录 A 中的 `qingflow_placeholder.py` 脚本：

```bash
# 普通字段
python3 qingflow_placeholder.py --que-id 462116040 --title "订单号"
# 输出: {订单号$$47445B6B8$$}

# 子表字段
python3 qingflow_placeholder.py --que-id 462116053 --parent "检验明细" --title "产品型号"
# 输出: {检验明细 · 产品型号$$编码$$}
```

已知验证向量：`462116040→47445B6B8`, `462116041→47445B6B9`, `3→ROXC`。

> ⚠️ 编码逻辑源自轻流打印模块实现，非稳定公开接口。轻流升级后如占位符不再被识别：停止批量生成，从当前轻流界面复制官方占位符对比，检查当前编码实现，更新脚本和验证向量后再继续。

### 字段映射

- 普通字段：`{字段名称$$编码$$}`
- 子表字段：`{子表名称 · 子字段名称$$编码$$}`
- 系统字段也必须使用真实 que_id
- 子表只保留一行占位符数据行，由轻流打印时扩展

### Word 版式

- 明细列多时用 A4 横向。信息少时可用 A4 纵向。
- 表格：固定布局、明确列宽不超页面、所有单元格强制上下居中、段前段后归零、表头统一行高且跨页重复、明细行用最小行高。
- 推荐结构：品牌抬头 → 单据标题 → 基础信息区 → 明细表 → 合计区 → 备注/条款 → 审核签章区 → 页脚。

### 制作流程

1. Builder MCP 读取字段配置取得 que_id
2. 建立字段-占位符映射表
3. 用一个普通字段、一个系统字段和一个子表字段做验证
4. 使用 `documents` 相关工具创建或编辑 `.docx`
5. 每个占位符使用单独连续的 Word 文本运行
6. 保存为新文件，不覆盖用户原始模板
7. 渲染检查后再交付

### 校验

```bash
unzip -p "template.docx" word/document.xml | rg -o '\$\$[A-Z0-9-]+\$\$' | sort -u
```

验证：所有预期字段有 Token、无多余 Token、无跨工作区 Token、Token 未被 Word 拆分。生成 PDF 和每页 PNG 做结构检查。

---

## 五、MCP 工具路由

### qingflow-app-builder

- 包：`package_get`、`package_apply`
- 应用读：`app_resolve`、`app_get`、`app_get_fields`、`app_get_layout`、`app_get_views`、`app_get_charts`
- 流程读：`app_flow_get`、`app_flow_get_schema`
- 流程写：`app_flow_apply`
- 门户/图表读：`portal_list`、`portal_get`、`view_get`、`chart_get`（写前必读）
- 目录：`member_search`、`role_search`、`role_create`
- 写：`app_schema_apply`、`app_layout_apply`、`app_views_apply`、`app_associated_resources_apply`、`app_charts_apply`、`portal_apply`
- 维护：`app_custom_buttons_apply`（仅独立按钮维护；普通构建用 view `action_buttons`）
- 验收：`app_publish_verify`

### qingflow-app-user

- 记录读：`record_list`、`record_get`、`record_browse_schema_get`
- 记录写：`record_insert`、`record_update`、`record_delete`
- Schema：`record_insert_schema_get`、`record_update_schema_get`
- 任务：`task_list`、`task_get`、`task_action_execute`、`task_workflow_log_get`
- 导入导出：`record_export_start`、`record_export_get`、`record_import_start`、`record_import_template_get`
- 流程动作：通过 `task_action_execute` 执行审批/填写等流程操作
- 验证：`record_code_block_run`、`record_code_block_schema_get`

### 数据边界

禁止用 builder 工具做记录的增删改查。路由到 `qingflow-app-user`。

### 结果语义

- `partial_success`、超时、`safe_to_retry=false`、读回不可用 = 不确定，不可安全重试
- `write_executed=false` 的校验错误 = 修正 payload 后重试

---

## 六、领域建模原则

- 一个稳定业务对象建模为一个应用。应用可扮演：主数据、核心事务、事件/明细、台账、流程支持、内容、系统支持。
- 跨应用对象链接用真实关联字段，不用文本查找冒充关联。
- 字段类型按业务意图选择：标题→text，状态→single_select，金额→amount，重复行→subtable 等。
- 关联字段在下游记录依赖核心记录时设为必填单选。子记录不可无父记录。
- 关联选择后自动带出至少 3 个关键摘要（客户/负责人/日期/状态/金额）。

---

## 七、执行顺序

1. 确认账号、工作区、环境、应用包、目标应用。
2. 回读现有字段、排版、视图、关联、按钮和流程。
3. 应用包和应用结构。
4. 字段、真实关联、引用填充和表单排版。
5. 流程和逐节点字段权限矩阵。
6. **每个应用创建 table + board + card 三个视图 → 回读全部 view_key → 删除三个以外的所有视图 → 再次回读确认 count=3 → 设置查询条件（1行3字段 exact=false）。**
7. 当前记录按钮、关联资源、Q-Robot 更新和业务回写。
8. **图表：每张先 `chart_get` 读完整配置 → 按 `styleConfigType` 原位修改 → 完整 config 回写 → `chart_get` 验证。指标卡必须配齐 6 个 chartStyleConfigType，柱状图必须白底浅边框。**
9. **门户：筛选器 + 指标卡 + 图表 + 表格视图四类齐全。每个图表组件 `beingShowTitle=false`。`portal_get` 回读验证。**
10. 发布 → 回读 → 逐项对照完成标准。有未勾选的项目 = 未完成。

---

## 八、完成标准 —— 逐项检查

以下每个 checkbox 都是强制验收项。适用但未勾选 = 任务未完成。

### 视图
- [ ] 每个应用恰好 3 个视图：`{table, board, card}`
- [ ] `全部数据`、`我的数据`、`我发起的`、`待办`、`已办`、`抄送` 及所有额外视图已删除。回读确认 count=3
- [ ] 视图顺序：table → board → card。表格视图为默认入口
- [ ] 表格列：选项字段第一列，核心名称第二列
- [ ] 每个主表格视图：单行三字段模糊查询，`exact=false`，顺序 `选项→日期→核心名称`

### 门户
- [ ] 恰好一个筛选组件（`source_type=filter`），PC 24×3，`dftJudgeType=2`
- [ ] 无 `grid` 组件
- [ ] 所有引用视图为 `type=table`
- [ ] 每个图表组件：`chartConfig.beingShowTitle=false` —— 已通过 `portal_get` 回读验证
- [ ] 指标卡：≤6张同行，每张配齐 6 个 chartStyleConfigType —— 已通过 `chart_get` 回读验证
- [ ] `selectedMetrics[].fieldName` 为业务名称，无 `数据总量`/`数据数量`/`汇总值`
- [ ] 非指标卡图表：白底、浅边框、`title.switchOn=true`、明确 chartName
- [ ] 指标卡背景=边框同色，色组统一按顺序
- [ ] PC 布局无重叠。移动端单列。

### 数据
- [ ] 字段值中无 `模拟`、`测试`、`虚拟`、`样例数据`
- [ ] 无 `客户A`、`产品1`、`张三测试` 等低质量占位

### 通用
- [ ] 所有变更已发布并通过回读验证
- [ ] 每次 `app_charts_apply` 后都跟了 `chart_get` 回读确认
- [ ] 每次写入结果 `status=success`、`failed=0`、`verified=true`

---

## 附录 A：qingflow_placeholder.py

占位符编码脚本见 `scripts/qingflow_placeholder.py`。用法：

```bash
# 普通字段
python3 scripts/qingflow_placeholder.py --que-id 462116040 --title "订单号"
# 输出: {订单号$$47445B6B8$$}

# 子表字段
python3 scripts/qingflow_placeholder.py --que-id 462116053 --parent "检验明细" --title "产品型号"
# 输出: {检验明细 · 产品型号$$编码$$}

# 验证已知向量
python3 scripts/qingflow_placeholder.py --verify
```

已知验证向量：`462116040→47445B6B8`, `462116041→47445B6B9`, `3→ROXC`。

---

> 版本：2026年7月
