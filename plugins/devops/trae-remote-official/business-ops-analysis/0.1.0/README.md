# business-ops-analysis

经营数据洞察引擎 — 从业务数据中提炼经营洞察，支持周期性经营汇报与管理决策。

## 插件用途与能力

面向运营分析师、业务分析师及业务负责人，从原始经营数据出发，完成从数据理解到可交付汇报的全链路分析。

### 能力列表

| 能力 | 说明 | Reference |
|---|---|---|
| 同比与环比分析 | 时间序列趋势、拐点识别、YoY/MoM/MTD/YTD | [trend-analysis.md](skills/business-ops-analysis/references/trend-analysis.md) |
| 业务结构拆解 + 目标完成度 | 占比分解、贡献归因、达成率、缺口量化 | [structure-analysis.md](skills/business-ops-analysis/references/structure-analysis.md) |
| 关键问题识别 | 异常检测、风险分级、问题归因 | [anomaly-identification.md](skills/business-ops-analysis/references/anomaly-identification.md) |
| 经营汇报 + 复盘 + 行动建议 | 多视角合成、四层 insight、格式交付 | [report-synthesis.md](skills/business-ops-analysis/references/report-synthesis.md) |

### 适用场景

- 月度/季度经营复盘（营收、成本、利润）
- 目标完成度追踪与缺口归因
- 业务结构变化分析（区域/产品/渠道占比）
- 同比环比趋势判断与拐点识别
- 关键经营问题定位与行动建议生成

### 不适用场景

- 纯技术性数据清洗/ETL（无业务分析诉求）
- 股票/投资组合分析（非经营视角）
- 一次性简单计算

## Skill、MCP 和 Connector 的关系

本插件为 **Skills-only** 模式，不含 MCP Server 和 Connector。

```
┌─────────────────────────────────────────┐
│          Trae Plugin Manifest          │
│  .trae-plugin/plugin.json              │
└──────────────────┬──────────────────────┘
                   │
                   ▼
        ┌─────────────────────┐
        │   Skills (1 个)     │
        │  business-ops-      │
        │  analysis           │
        └─────────────────────┘
```

- **Skill**：分析能力的载体，包含 Prompt 规范、工作流指引与参考文档。本插件有 1 个 Skill。
- **MCP**：不适用。本插件不依赖外部 MCP Server，所有分析在对话上下文中完成。
- **Connector**：不适用。无需第三方授权认证。

如需接入外部数据源（如数据库、BI 工具 API），可扩展为 Skills + MCP + Connector 模式。

## 认证方式及凭据运行时消费

本插件不涉及认证与凭据。

- 无 MCP Server，无需 API Key / Token
- 无 Connector，无需 OAuth / 授权流程
- 数据由用户在对话中直接提供（粘贴、上传文件等）

## 本地命令、运行时与第三方依赖

### 运行时依赖

- **Trae 客户端**：内置 Skill 引擎，无需额外安装
- **Node.js**：仅用于骨架生成与本地校验（开发期）

### 本地命令

```bash
# 校验插件结构
node ../scripts/validate-plugin.mjs ./business-ops-analysis
```

### 第三方依赖

无。本插件为纯 Prompt/Skill 型插件，不引入 npm、PyPI 或其他第三方库。

## 外部服务、项目来源与许可证

### 外部服务

本插件运行时不调用任何外部服务。

### 项目来源

- 插件骨架生成：Trae 插件骨架脚本
- Skill 内容：经营分析全链路方法论

### 许可证

- **插件 License**：UNLICENSED（详见 [plugin.json](.trae-plugin/plugin.json)）
- **图标**：自动生成的 SVG，白底黑字，无第三方版权

## 配置方法

### 安装

将 `business-ops-analysis/` 目录放入 Trae 插件目录或通过 Trae 插件管理界面加载。

### 配置项

本插件无运行时配置项。所有分析参数（时间口径、指标定义、维度选择等）在对话中由用户指定。

## 验证方式

```bash
# 结构校验
node scripts/validate-plugin.mjs ./business-ops-analysis

# 预期输出
# ./business-ops-analysis [Skills-only]
#   PASS  minimal plugin is valid
```

手动验证：在 Trae 中加载插件后，输入一段经营数据并要求分析，检查是否按标准工作流（趋势 → 结构 → 异常 → 报告）输出结果。

## 已知限制

1. **数据来源受限**：仅支持用户在对话中直接提供的数据，无法直连数据库/BI 工具
2. **无持久化**：分析结果不做持久化存储，会话结束即丢失
3. **单文件数据量限制**：受对话上下文窗口限制，超大数据集需提前聚合
4. **HTML 报告依赖 html-report Skill**：生成可视化看板需额外安装 `html-report` Skill
5. **无实时数据刷新**：不支持定时任务或数据自动更新
