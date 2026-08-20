---
name: order-detail-query
version: 1.4.0
description: "Order and Detail Query workflow for foreign-trade teams, with explicit evidence, controlled CRM access, confirmation, and safety boundaries."
description_zh: "查询order及其orderProduct，按客户、时间、SKU、数量和金额汇总并标注数据范围。适用于用户要求订单与明细查询、生成相关结果或检查执行边界时。"
allowed-tools: Bash
---

# 订单与明细查询

## 目标与边界

定位：查询order及其orderProduct，按客户、时间、SKU、数量和金额汇总并标注数据范围。边界：只读；订单和明细关联、可见字段受OpenAPI视图限制。

## 前置依赖

- dependency: xunpanyun-crm-runtime
- version: ^1.3.0
- required: true
- 未安装时，优先调用 WorkBuddy 已提供的 `marketplace-skill-installer` 或等效市场安装能力，直接安装兼容版本；若平台弹出确认卡，只请求一次安装确认。
- 安装成功后立即重试 `xunpanyun-crm auth status`；不要搜索 PATH、installed_plugins.json 或文件系统，也不要先输出技术诊断报告。
- 返回 `AUTH_REQUIRED` 时，优先触发平台提供的插件配置/授权入口；禁止在对话中索取 client_id、client_secret。
- 安装或授权需要用户操作时，只说明一个当前动作，并承诺完成后自动续跑原任务；不要提前追问统计口径或输出五段式失败报告。
- 只有自动安装能力不存在、市场找不到资产或安装失败时，才给出简短人工路径和脱敏错误码；不得声称读取了实时CRM。

## 输入要求

- 业务问题、对象和统计口径
- 时间范围、筛选条件与排序
- 租户权限和动态字段映射
- 必要的记录ID或负责人范围

## 工作流程

1. 把业务问题转换为对象、时间范围、筛选条件、排序和所需字段。
2. 发现租户实际字段和权限，只使用OpenAPI视图开放内容。
3. 使用dataId、可重复字段filter、filter-mode/expression、排序、分组、公私海标识和分页参数查询，记录完整口径、页数和命中数量。
4. 核对跨对象关联、重复计数、空结果、缺失字段和表达式逻辑。
5. 输出结果、证据范围、数据缺口和下一步建议，不触发任何写入。

## 输出要求

- 查询口径与数据范围
- 结构化结果或统计
- 异常/缺失/关联限制
- 可执行的下一步建议

## 固定口径与输出模板

- 订单头与orderProduct按可验证订单ID关联；无关联键时不得猜测归属。
- 数量按SKU和计量单位分组；金额按currency+tradeTerm分组，未给汇率来源、日期和规则时禁止跨币种换算或合计。
- 明细合计与订单头金额分别展示；税费、运费、折扣未知时只报告差额，不直接判断错误。
- 输出列：订单ID｜客户｜币种｜贸易条款｜SKU｜数量/单位｜明细金额｜订单头金额｜差额｜异常。

## 实战使用卡

### 可直接复制的任务示例

> 查询customer dataId=100234在2026-01-01至2026-07-31的order/orderProduct；USD和EUR分组，按订单ID关联，核对数量、单位、明细合计与订单头金额。

### 最小任务卡

用户信息不完整时，只补问会阻塞执行的项目；其余内容先按已知事实交付草稿。

- 业务问题与对象
- 时间范围与负责人范围
- 筛选、排序和去重口径
- 希望看到的字段或指标

### 默认交付顺序

1. 查询口径卡
2. 带recordId的结果表或指标表
3. 空值、权限、关联和分页异常
4. 按优先级排列的下一步动作

### 完成标准

- 结果可被业务人员直接复制、筛选、修改或提交复核，不只给方法论。
- 每个关键结论能追溯到输入、CRM字段、消息原文或明确标注的推断。
- 缺失信息用占位符或缺口清单表达，不因缺一个非关键字段而停止全部工作。
- 涉及发送、发布、投放或CRM写入时，停在明确的确认点。

## Runtime能力校准

- coverage: query-only
- 查询命令支持dataId、可重复字段filter、and/or、expression、排序、分组、公私海标识和分页；字段apiKey、选项值和排序字段必须先动态发现。
- objFieldData通用create/update覆盖lead、customer、contact、opportunity、followUpRecord；order/orderProduct使用orderData专用命令，商机阶段使用salesStageStatus专用命令。
- 本Skill只读；不得使用任何写命令。

## 询盘云API接入

1. 检查共享能力 `xunpanyun-crm-runtime`；若缺失，立即调用 `marketplace-skill-installer` 或平台等效安装能力安装 `xunpanyun-crm-runtime@^1.3.0`。
2. 安装后立即执行 `xunpanyun-crm auth status`；不要扫描 PATH、插件清单或文件系统来证明缺失。
3. 若返回 `AUTH_REQUIRED`，优先唤起插件配置/授权入口，只提示用户完成当前授权动作；禁止要求用户在对话中粘贴 client_id 或 client_secret。
4. 授权完成后自动回到用户最初的业务问题，继续字段发现、查询或受控写入，不让用户重复描述任务。
5. 自动安装不可用或失败时，只输出“失败原因 + 一个下一步动作”；不要输出长篇环境诊断、风险清单或尚未阻塞执行的口径问题。
6. 只在本Skill边界内使用CRM数据，并标注对象、筛选口径、分页和异常。

## 禁止事项

- 不编造客户、公司、产品、价格、认证、案例、实时数据或商业承诺。
- 不把推断写成事实；资料不足时明确列出待确认项。
- 不执行本Skill边界外的发送、发布、删除、批量修改或系统写入。
- 涉及CRM写入时，不得跳过字段发现、目标查询、变更预览、明确确认和执行回查。
- 不得把 client_id、client_secret 或 access_token 写入SKILL.md、参考资料、工作簿、对话或日志。

## 上线前重点测试

- 订单明细关联
- 金额合计
- 分页
- 缺少SKU字段
- Runtime缺失时优先自动安装，不扫描PATH或文件系统，不输出五段式失败报告
- 未授权时只引导当前授权动作，授权后自动续跑原任务
