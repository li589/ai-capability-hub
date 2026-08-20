---
name: insurance-product-configuration
description: This skill should be used when insurance agents need to configure
  insurance products from a confirmed needs diagnosis, compare product terms,
  create a compliant single-main-policy plan, calculate premiums from an
  approved rate source, explain recommendation rationale, or prepare options for
  agent confirmation.
disable-model-invocation: true
---

# 保险产品配置

## Purpose

根据已确认的家庭财富规划诊断、客户预算和有效产品资料，完成产品筛选、产品组合、条款对比、保费测算、合规校验和推荐理由说明。输出简短、可调整的方案决策，不替代正式核保、投保、签署、支付或出单。

本 Skill 严格遵循“需求诊断 → 产品配置 → 建议书生成”的顺序：先确认本次重点模块和预算，再选品与报价，最后由代理人确认是否进入建议书制作。

## When to use

在出现以下请求时使用：

- 根据客户需求、保障待补足金额和预算配置产品。
- 比较候选产品的责任、期限、缴费方式、等待期、免责和现金价值。
- 根据保额、缴费期和附加责任计算保费或调整报价。
- 解释为什么选某产品、为什么不选其他候选产品。
- 输出主方案、备选方案或“可选同步补”建议。

不要用于：

- 信息不完整时直接推荐产品；先转入需求诊断。
- 直接制作建议书、对客解释或发送方案；转入建议书生成能力。
- 代替保险公司做核保、承保、投保、签署、支付或出单结论。

## Readiness gate

开始前必须具备：

1. 已确认的客户与家庭资料。
2. 需求诊断输出的本次重点模块、建议保额或待补足金额。
3. 已确认的预算范围与缴费偏好。
4. 本 Skill 读取的外部产品库中可匹配的产品、费率、组合规则和投保规则资料（数据外置于 `~/.workbuddy/copilot/企鹅保险/product-library/`，不随 Skill 打包）。

缺少第 1-3 项时，停止选品并回到需求诊断补充信息。

当前产品库默认有效，引用统一标记为“资料库版 2025-03-17（按代理人确认有效）”。产品不在库、参数未覆盖或条款资料缺失时，明确标记“待核验”，不得编造报价或结论。

## 产品库（外部数据，不随 Skill 打包）

产品库是**公司专属、频繁变动的数据**，与 Skill 逻辑解耦：Skill 只含代码与规则，产品数据放在 Skill 之外，便于独立更新、跨公司复用，也避免和 `agent-copilot-rate-engine` 的 `rates.db` 出现多份真相源。

- **默认位置**：`~/.workbuddy/copilot/企鹅保险/product-library/`，包含 `catalog.json`（产品元数据/组合规则/主险规则）、`rate_tables.json`（费率）、`source/`（原始脱敏 PDF/XLSX/DOCX 构建输入）、`README.md`。
- **环境变量覆盖**：`export PRODUCT_LIBRARY_DIR=/path/to/your/product-library`，`quote_plan.py` 与构建脚本均读此变量；未设置时回退到默认位置。
- **缺失处理**：若目录/文件不存在，`quote_plan.py` 会报错并提示设置 `PRODUCT_LIBRARY_DIR` 或放置 `catalog.json`/`rate_tables.json`，不会静默失败。
- **重建**：用 `scripts/build_product_library.py --source <source目录> --output catalog.json --rates-output rate_tables.json` 从 `source/` 重新生成两份 JSON 到外部目录。

## Workflow

### 1. Receive the needs diagnosis handoff

读取以下输入：

- 客户年龄、性别、被保对象与家庭结构。
- 本次重点模块与建议保额/待补足金额。
- 已有保障摘要。
- 年度预算、缴费偏好与预算上限。
- 后续规划模块与待确认事项。

不重复输出客户画像；只提取与本次配置相关的信息。

### 2. Select products from the external product library

- 使用外部产品库的 `catalog.json`（默认 `~/.workbuddy/copilot/企鹅保险/product-library/`，可用环境变量 `PRODUCT_LIBRARY_DIR` 覆盖）查询已维护的 13 款产品、中文名称、主附险身份、产品说明书、费率表、条款文档标识、组合规则和主险投保规则。
- 只从标记为“有效（按代理人确认）”且适用当前客户资料的产品中筛选。
- 对每个候选产品核对：保障责任、保障期限、缴费期、等待期、免责、现金价值/领取规则、适用人群与投保条件。
- 根据本次重点模块选主产品；将强相关但非本次重点的保障以“可选同步补”或“后续规划”呈现，不强推全量配置。
- 遵循“单主险”校验：一个方案只能有一个主险；附加险必须满足产品库中的主附关系、保额比例、保障期限和缴费期等规则。
- 对外展示只使用中文产品名称；产品代码仅用于内部匹配、数据查询或费率引擎输入。

参考 `references/product-configuration-rules.md`；产品库结构见外部目录 `~/.workbuddy/copilot/企鹅保险/product-library/README.md`。

### 3. Calculate premium and run compliance checks

- 使用 `scripts/quote_plan.py` 一次性提交完整组合，完成产品名称映射、费率读取、保费计算和已维护规则校验：

```bash
python3 scripts/quote_plan.py --input <方案输入.json> --output <报价结果.json>
```

- 当前支持：健康守护星终身重大疾病保险、附加健康守护星多次给付疾病保险、附加健康守护特定疾病保险、附加守护星终身重疾险、安康守护医疗保险、长乐尊享终身寿险、鸿运盈终身寿险、附加安享无忧定期寿险、福寿延年养老年金险等资料库已解析产品。
- 报价结果必须包含：年缴保费、保额、费率依据、产品说明书/费率表引用和资料库版本。
- 校验至少包括：单主险、已维护主附关系、已维护保额比例、费率表可覆盖的年龄/性别/缴费期/保障期限，以及预算承受能力。
- 非标准体加费、未解析的豁免险、资料库未覆盖的参数、健康告知和正式核保仍标记“待核验”，不得输出为自动通过。

### 4. Explain the recommendation

- 每个入选产品说明“为什么选”：对应哪个需求、待补足金额或服务目标，并标注产品说明书、费率表和资料库版本。
- 每个未选产品说明“为什么暂不选”：不匹配本次重点、预算、缴费偏好、适用条件或属于后续规划。
- 输出一句“利弊提示”：说明方案优势和代理人需与客户确认的限制或取舍。
- 不贬低竞品，不把未核验的卖点、收益、服务权益或理赔能力写成确定事实。

### 5. Present options and request confirmation

- 默认输出一个主方案；必要时再提供一个预算或保障取向不同的备选方案。
- 输出不超过 12 行，避免大表格和原始数据转储。
- 提供以下确认选项：确认方案、调整保额、调整缴费期、替换产品、返回需求诊断。
- 代理人确认后，才将方案交给建议书生成能力。

## Output formats

### Product configuration decision

```text
本次重点：{重点模块}

主方案
【主险】{中文产品名}｜{保额}｜{保障/缴费安排}｜{保费或待报价}
  → {匹配理由}
【附加】{中文产品名}｜{保额/责任}｜{保费或待报价}
  → {匹配理由}

合计：{年缴/月缴保费或待报价}｜{校验状态}
利弊提示：{一句话}
可选同步补：{可选项或“无”}
请确认：确认方案 / 调整保额 / 调整缴费期 / 替换产品 / 返回需求诊断。
```

### Product comparison

```text
对比维度：{责任/期限/缴费/等待期/免责/现金价值}
产品 A：{中文产品名}｜{核心差异}
产品 B：{中文产品名}｜{核心差异}
推荐：{产品}，原因：{与客户需求和预算的匹配理由}
暂不选：{产品}，原因：{预算、适用条件或本次重点不匹配}
```

### Handoff to proposal generation

```text
已确认方案
- 主险及附加责任：{中文产品名、保额、期限、缴费期}
- 保费：{年缴/月缴、报价版本或待正式确认说明}
- 推荐理由：{摘要}
- 待披露/待确认：{事项}
- 引用资料：{条款、费率、规则版本}
```

## Guardrails

- 不在需求诊断未确认前直接选品或报正式保费。
- 不心算保费；无有效报价来源时只能标记“待报价”。
- 不输出双主险方案；主附关系和组合限制未核验时不得标记“合规”。
- 不向代理人或客户展示内部产品代码、原始 JSON、脚本或数据库实现。
- 不只给价格；每个产品必须说明与客户需求的匹配理由。
- 不作承保、收益、续保、服务或理赔承诺；最终以保险公司有效条款、费率、核保和官方系统为准。
