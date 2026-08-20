---
name: order-maintenance
version: 1.4.0
description: "Order Maintenance workflow for foreign-trade teams, with explicit evidence, controlled CRM access, confirmation, and safety boundaries."
description_zh: "通过orderData新增或更新order及orderProduct，核对订单头、明细、SKU、数量、单价和币种，确认后执行并同步回查。适用于用户要求订单维护、生成相关结果或检查执行边界时。"
allowed-tools: Bash
---

# 订单维护

## 目标与边界

定位：通过orderData新增或更新order及orderProduct，核对订单头、明细、SKU、数量、单价和币种，确认后执行并同步回查。边界：字段、币种、计量单位或明细关联不明确时停在预览。

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

- 用户明确的写入目标与范围
- 租户凭证由运行环境安全提供
- 目标记录ID及动态字段映射
- 需要写入的已确认业务数据

## 工作流程

1. 明确目标对象、记录范围、预期变更和用户权限。
2. 先发现租户实际字段、对象类型、选项值和负责人ID，禁止硬编码。
3. 查询目标记录并核对关联关系、当前值、重复数据和必填约束。
4. 先使用--dry-run生成变更预览，逐项显示记录ID、变更前、变更后及影响；确认前禁止执行。
5. 等待用户明确确认；范围、目标负责人或关键值变化时重新确认。
6. 使用--confirm执行后同步查询目标记录回查；分别报告接口响应、实际字段状态、失败和待人工处理项。

## 输出要求

- 变更对象与查询依据
- 变更前后差异预览
- 用户确认点
- 执行结果与查询回查

## 固定口径与输出模板

- 金额按币种分组，数量保留计量单位；订单头、明细、税费、运费和折扣不得混为同一字段。
- 输出：订单/明细ID｜字段｜当前值｜建议值｜币种/单位｜依据｜dry-run差异｜确认状态｜同步回查结果。

## 实战使用卡

### 可直接复制的任务示例

> 为order dataId=88001生成orderData dry-run：交期从2026-08-20改为2026-08-25；保持USD币种和原明细不变，展示预览并停在确认门。

### 最小任务卡

用户信息不完整时，只补问会阻塞执行的项目；其余内容先按已知事实交付草稿。

- 目标对象与recordId
- 要修改的字段、当前值和目标值
- 业务依据与执行人
- 只预览或确认执行

### 默认交付顺序

1. 目标与影响范围
2. 逐字段变更前后对照
3. dry-run结果与唯一确认问题
4. 执行回执、回查结果和失败项

### 完成标准

- 结果可被业务人员直接复制、筛选、修改或提交复核，不只给方法论。
- 每个关键结论能追溯到输入、CRM字段、消息原文或明确标注的推断。
- 缺失信息用占位符或缺口清单表达，不因缺一个非关键字段而停止全部工作。
- 涉及发送、发布、投放或CRM写入时，停在明确的确认点。

## Runtime能力校准

- coverage: order-data-write
- 查询命令支持dataId、可重复字段filter、and/or、expression、排序、分组、公私海标识和分页；字段apiKey、选项值和排序字段必须先动态发现。
- objFieldData通用create/update覆盖lead、customer、contact、opportunity、followUpRecord；order/orderProduct使用orderData专用命令，商机阶段使用salesStageStatus专用命令。
- 使用order-data命令；确认执行后同步查询order及orderProduct回查订单头和明细。

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

- SKU/币种校验
- 数量边界
- 变更差异
- 删除二次确认
- Runtime缺失时优先自动安装，不扫描PATH或文件系统，不输出五段式失败报告
- 未授权时只引导当前授权动作，授权后自动续跑原任务
