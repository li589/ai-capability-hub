---
name: whatsapp-conversation-summary
version: 1.3.0
description: WhatsApp Conversation Summary workflow for foreign-trade teams,
  with explicit evidence, controlled CRM access, confirmation, and safety
  boundaries.
description_zh: 按账号和联系人聚合已保存的WhatsApp消息，提取采购要素、意向信号、摘要和待办。适用于用户要求WhatsApp会话摘要、生成相关结果或检查执行边界时。
disable-model-invocation: true
---

# WhatsApp会话摘要

## 目标与边界

定位：按账号和联系人聚合已保存的WhatsApp消息，提取采购要素、意向信号、摘要和待办。边界：不补全未推送历史，不把媒体链接内容当作已解析事实，不直接回复。

## 输入要求

- 企业接口已保存的WhatsApp推送数据
- 账号与联系人信息
- 产品资料及企业话术
- 用户希望的统计或回复语言

## 工作流程

1. 读取企业接收接口已保存的消息，识别账号、联系人、方向、时间和类型。
2. 按messageId去重并区分首次全量与后续增量。
3. 按账号和联系人聚合消息，保留媒体链接但不假装已解析媒体内容。
4. 提取采购要素、意向、缺口和待办，并标注原文依据。
5. 输出分析或回复草稿；不得拉取未推送历史，也不得直接发送消息。

## 输出要求

- 消息统计或会话摘要
- 采购要素与意向信号
- 待办和待确认项
- 必要时提供多语言回复草稿

## 固定口径与输出模板

- 输入schema：messageId、accountId、contactKey（标准化E.164号码或平台联系人ID）、direction、messageType、occurredAt、text、mediaUrl。
- required：messageId/accountId/contactKey/direction/messageType/occurredAt；direction仅inbound/outbound；occurredAt使用ISO 8601并保留时区。
- 去重键为accountId+messageId；同一号码在不同accountId下不得合并。媒体只有URL时标记“未解析媒体内容”。
- 输出列：账号｜联系人键｜时间｜方向｜类型｜文本/媒体状态｜采购事实｜意向推断｜待办｜CRM候选及置信依据。

## 实战使用卡

### 可直接复制的任务示例

> 汇总accountId=wa-sales-01、contactKey=+491701234567的两条消息：m-1001询问500件和9月交期，m-1002为未解析PDF链接；按时间输出采购事实、推断和待办。

### 最小任务卡

用户信息不完整时，只补问会阻塞执行的项目；其余内容先按已知事实交付草稿。

- accountId与contactKey
- 消息时间范围或messageId
- 希望提取的采购要素
- 输出语言与是否需要回复草稿

### 默认交付顺序

1. 消息范围与去重口径
2. 采购事实、意向推断和缺失信息
3. 待办清单与负责人建议
4. 可直接修改的多语言回复草稿

### 完成标准

- 结果可被业务人员直接复制、筛选、修改或提交复核，不只给方法论。
- 每个关键结论能追溯到输入、CRM字段、消息原文或明确标注的推断。
- 缺失信息用占位符或缺口清单表达，不因缺一个非关键字段而停止全部工作。
- 涉及发送、发布、投放或CRM写入时，停在明确的确认点。

## 询盘云API接入

- 本Skill不读取或写入实时CRM。若用户提出CRM操作，说明超出本Skill边界并转交已配置的CRM能力；禁止索取任何密钥。

## 禁止事项

- 不编造客户、公司、产品、价格、认证、案例、实时数据或商业承诺。
- 不把推断写成事实；资料不足时明确列出待确认项。
- 不执行本Skill边界外的发送、发布、删除、批量修改或系统写入。
- 涉及CRM写入时，不得跳过字段发现、目标查询、变更预览、明确确认和执行回查。
- 不得把 client_id、client_secret 或 access_token 写入SKILL.md、参考资料、工作簿、对话或日志。

## 上线前重点测试

- 跨账号隔离
- 消息顺序
- 媒体缺内容
- 不得扩展历史
