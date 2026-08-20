---
name: ec-crm-zh
description: EC CRM 中文操作技能，覆盖客户管理、工商数据查询与导入、客户标签与 AI
  画像、销售跟进记录与待办、联络中心记录与质检分析、订单管理。用于通过 ec-crm CLI
  搜索、查看、创建、更新、转让、放弃、共享、打标签、画像分析、跟进、联系、质检或管理 EC 客户与订单。
disable-model-invocation: true
---

# EC CRM 中文版

使用本技能通过 `ec-crm` 处理 EC CRM 任务。能力范围包括客户、工商数据、客户洞察、销售协同、联络中心、质检分析和订单管理。

## 硬约束

### 铁律：`ec-crm` 报错即停。以下规则不可协商，不可绕过。

| 错误类型 | 识别 | 行动 | 严禁 |
| --- | --- | --- | --- |
| 命令不存在 | `command not found` 或找不到 `ec-crm` | 先执行 `npm install -g @workec/ec-crm`，再执行 `ec-crm --version` 验证 | 跳过安装验证 |
| 入参错误 | 参数格式、类型或取值不合法 | 读错误，修正后重试，最多 2 次；超限后停止并告知正确格式 | 猜参、删参、填默认值 |
| 业务错误 | 权限不足、客户不存在、订单不存在、状态不允许等 | 立即停止，原样展示错误 | 重试、换命令、绕路 |
| 结果为空 | 命令正常退出但数据为空 | 告知“查询无结果”，结束当前任务 | 换条件重查、扩大范围 |
| 数据错误 | 字段缺失、格式异常、空数据或前后不一致 | 立即停止，告知数据异常 | 跳过字段、补造字段 |
| `flow` 命令限制 | 调用 `ec-crm flow` 相关命令 | 只能携带 `--help` 参数，用于获取流程 | 传入任何业务参数或其他选项 |
| 可重试错误 | 超时、429、5xx 等临时错误 | 单次会话内最多重试 5 次 | 无限重试或静默失败 |

任何未列出的错误一律视为“停”。删除、放弃客户、删除待办、删除订单等破坏性操作必须先向用户确认。绝不泄露、记录或回显 `EC_AUTH`、token 等授权凭证。绝不编造请求参数。

### 注意

- 当执行命令的返回结果过长并被系统截断时，主动读取完整数据文件内容，确保后续步骤使用完整数据。
- 当用户请求缺少必要业务对象时，先通过对应搜索/详情流程获取 ID，如 `crmId`、订单 ID，再继续执行目标动作。
- 多步骤任务中任一步失败，都要停止后续步骤，并告知用户已完成与未完成的内容。

## 意图路由

根据用户意图选择业务域。跨域任务按顺序执行，任一步失败即停止后续步骤。

- 客户管理：搜索、筛选、查看详情、创建、编辑、转让、放弃到公海、共享客户。
- 工商数据：查询企业工商信息、查看工商详情、将工商数据导入为 CRM 客户。
- 客户洞察与标签：查询标签/进展/分组/来源配置，修改客户标签，查看或执行 AI 客户画像。
- 销售跟进：创建或查询跟进记录，管理待办，创建或查询工作报告。
- 联络中心与质检：按渠道查询联系记录，加入待拨列表，加入 AI 电话，话术复盘，违规/SOP 质检，ASR 沟通分析。
- 订单管理：搜索订单，查询回款计划或回款记录，编辑订单，删除订单。

## 意图拆分

- “先找到客户再打标签/写跟进/打电话/查记录”：先走客户管理搜索获取 `crmId`，再转客户洞察、销售跟进或联络中心。
- “修改客户信息并写跟进”：先创建或更新客户，再创建跟进记录。
- “查工商信息然后导入”：先查工商信息列表，必要时查详情，再导入客户库。
- “导入工商信息后打标签/写跟进/联系客户”：先完成工商导入，再转客户洞察、销售跟进或联络中心。
- “分析客户画像并记录结论”：先执行画像分析，再查询画像报告，最后创建跟进记录。
- “写跟进并设置提醒”：先创建跟进记录，再创建或修改待办。
- “质检/沟通分析后记跟进”：先完成违规质检、SOP 质检或 ASR 分析，再创建跟进记录。
- “找到订单并查看/修改客户信息”：先搜索订单获取关联客户标识，再转客户详情或客户更新。
- “找到订单并修改订单备注/状态/自定义字段”：先搜索订单定位目标订单，再编辑订单。
- 多域组合中，如果前置步骤没有拿到后续所需 ID 或关键字段，停止并说明缺失信息，不继续猜测。

## 客户管理

| 用户意图 | 执行动作 | 获取流程 |
| --- | --- | --- |
| 找客户、搜客户、按条件筛选客户 | 搜索客户 | `ec-crm flow customer-search --help` |
| 看客户详情、负责人、进展、资料 | 查询客户详情 | `ec-crm flow customer-detail --help` |
| 新建、编辑、更新客户信息 | 创建或更新客户 | `ec-crm flow customer-create-update --help` |
| 将客户转给他人 | 转让客户 | `ec-crm flow customer-move --help` |
| 放弃客户、退回公海 | 放弃客户 | `ec-crm flow customer-discard --help` |
| 分享客户 | 共享客户 | `ec-crm flow customer-share --help` |

常见跨域流程：
- 给指定客户打标签、写跟进或联系客户时，先搜索客户获取 `crmId`，再执行目标业务域流程。
- 修改客户信息并写跟进时，先更新客户，再创建跟进记录。

## 工商数据

| 用户意图 | 执行动作 | 获取流程 |
| --- | --- | --- |
| 查询企业工商信息、易企查信息 | 查询工商信息列表 | `ec-crm flow business-info-list --help` |
| 查看完整工商详情 | 查询工商信息详情 | `ec-crm flow business-info-detail --help` |
| 将工商企业导入客户库 | 导入工商客户 | `ec-crm flow business-info-import --help` |

常见跨域流程：
- 查询公司并导入时，先查列表，必要时看详情，再导入。
- 导入后打标签或写跟进时，先完成导入，再进入客户洞察或销售跟进流程。

## 客户洞察与标签

| 用户意图 | 执行动作 | 获取流程 |
| --- | --- | --- |
| 查询有哪些标签、进展、分组、来源 | 查询组合配置 | `ec-crm flow combine-config --help` |
| 给客户打标签、改标签、移除标签 | 修改客户标签 | `ec-crm flow customer-tag --help` |
| 查看客户画像、画像报告 | 查询 AI 画像报告 | `ec-crm flow customer-ai-report-detail --help` |
| 分析客户、生成画像 | 执行 AI 画像分析 | `ec-crm flow customer-ai-report-analyze --help` |

常见跨域流程：
- 给指定客户打标签时，先搜索客户，再修改标签。
- 分析客户并记录结论时，先执行分析，再查询报告，最后创建跟进记录。

## 销售跟进与协同

| 用户意图 | 执行动作 | 获取流程 |
| --- | --- | --- |
| 写跟进、添加跟进记录 | 创建跟进记录 | `ec-crm flow customer-record-add --help` |
| 查跟进、看客户跟进时间线 | 查询跟进记录 | `ec-crm flow customer-record-list --help` |
| 创建待办、修改待办、设置提醒 | 保存待办 | `ec-crm flow todo-save --help` |
| 查看待办列表 | 查询待办 | `ec-crm flow todo-list --help` |
| 标记待办完成、更新待办状态 | 标记待办 | `ec-crm flow todo-mark --help` |
| 删除待办、取消待办 | 删除待办 | `ec-crm flow todo-delete --help` |
| 查日报、周报、月报 | 查询工作报告 | `ec-crm flow work-report-list --help` |
| 写日报、周报、月报 | 新建工作报告 | `ec-crm flow work-report-add --help` |

常见跨域流程：
- 写跟进并设置提醒时，先创建跟进记录，再保存待办。
- 给指定客户写跟进时，先搜索客户，再创建跟进记录。

## 联络中心与质检

| 用户意图 | 执行动作 | 获取流程 |
| --- | --- | --- |
| 查电话记录、通话记录 | 查询电话联系记录 | `ec-crm flow record-phone-list --help` |
| 查微信联系记录 | 查询微信记录 | `ec-crm flow record-wx-list --help` |
| 查短信联系记录 | 查询短信记录 | `ec-crm flow record-sms-list --help` |
| 查企业微信联系记录 | 查询企微记录 | `ec-crm flow record-workwx-list --help` |
| 查邮件联系记录 | 查询邮件记录 | `ec-crm flow record-email-list --help` |
| 查拜访记录 | 查询拜访记录 | `ec-crm flow record-visit-list --help` |
| 查系统生成的跟进动作记录 | 查询跟进动作记录 | `ec-crm flow record-follow-list --help` |
| 加入待拨打列表 | 添加到待拨列表 | `ec-crm flow call-center-add --help` |
| 加入 AI 电话助手 | 添加到 AI 外呼 | `ec-crm flow call-center-ai-add --help` |
| 查话术复盘热门问题 | 查询话术复盘热门问题 | `ec-crm flow talk-review-top-list --help` |
| 查话术复盘问题详情 | 查询话术复盘问题详情 | `ec-crm flow talk-review-quest --help` |
| 查违规质检记录 | 查询违规质检列表 | `ec-crm flow inspect-violation-list --help` |
| 看违规质检详情 | 查询违规质检详情 | `ec-crm flow inspect-violation-detail --help` |
| 查 SOP 质检记录 | 查询 SOP 质检列表 | `ec-crm flow inspect-sop-list --help` |
| 看 SOP 质检详情 | 查询 SOP 质检详情 | `ec-crm flow inspect-sop-detail --help` |
| 查 ASR 沟通分析记录 | 查询 ASR 列表 | `ec-crm flow asr-list --help` |
| 看 ASR 沟通分析详情 | 查询 ASR 详情 | `ec-crm flow asr-detail --help` |

常见跨域流程：
- 联系指定客户时，先搜索客户，再加入对应待拨或 AI 电话流程。
- 质检或沟通分析后要记录跟进时，先完成质检/ASR 流程，再创建跟进记录。

## 订单管理

| 用户意图 | 执行动作 | 获取流程 |
| --- | --- | --- |
| 找订单、搜订单、筛选订单 | 搜索订单 | `ec-crm flow order-search --help` |
| 查回款计划、收款安排 | 查询回款计划 | `ec-crm flow order-payment-plan-search --help` |
| 查回款记录、收款明细 | 查询回款记录 | `ec-crm flow order-payment-record-search --help` |
| 编辑、修改、更新订单字段 | 编辑订单 | `ec-crm flow order-edit --help` |
| 删除、移除订单 | 删除订单 | `ec-crm flow order-delete --help` |

常见跨域流程：
- 找到订单后查看对应客户时，先搜索订单，再用返回的客户标识查询客户详情。
- 修改订单备注、状态或自定义字段时，必要时先搜索订单，再编辑订单。

## 跨会话恢复

当用户说“继续上次”或提到之前的客户、订单、工商查询、跟进、待办、工作报告、联系记录、质检项或分析结果时，先检索本地记忆中的 `crmId`、订单 ID、公司名称或历史查询词，再向用户追问。
