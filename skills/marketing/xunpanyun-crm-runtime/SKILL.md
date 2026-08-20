---
name: xunpanyun-crm-runtime
version: 1.3.0
description: Install and authorize the shared Xunpanyun CRM runtime, then
  provide a secure CLI for WorkBuddy experts and skills. Use when live
  LeadsCloud access is requested, the runtime dependency is missing,
  authorization is required, or a task needs field discovery, queries, or
  controlled writes.
description_zh: 自动恢复询盘云CRM运行依赖并引导安全授权，为所有询盘云专家和Skill提供统一CRM接口。适用于Runtime缺失、首次授权、凭证校验、字段发现、实时查询或受控写入。
allowed-tools: Bash
disable-model-invocation: true
---

# 询盘云API授权与连接

## 快速安装与续跑

1. 若当前工作区缺少本Runtime，立即调用 WorkBuddy 的 `marketplace-skill-installer` 或等效市场安装能力安装 `xunpanyun-crm-runtime@^1.3.0`；平台要求确认时，只请求一次安装确认。
2. 安装成功后立即执行 `xunpanyun-crm auth status`，不要搜索 PATH、installed_plugins.json 或文件系统。
3. 若未授权，优先触发平台提供的插件配置/授权入口；只告诉用户完成当前动作，禁止在对话中索取密钥。
4. 授权完成后自动继续用户最初的CRM任务，不要求用户重新描述，也不要先追问尚未阻塞执行的统计口径。
5. 自动安装能力不存在、市场找不到资产或安装失败时，只输出脱敏失败原因和一个人工下一步动作；不要输出环境检查表或五段式失败报告。

## 授权规则

1. 执行 `xunpanyun-crm auth status` 检查配置，不读取或显示凭证明文。
2. 若返回 `AUTH_REQUIRED`，唤起插件配置/授权入口；禁止让用户在对话中粘贴 client_id 和 client_secret。
3. 执行 `xunpanyun-crm auth check` 验证凭证，只有接口返回成功码后才允许继续。
4. 不把 client_id、client_secret 或 access_token 写入文件、对话、参考资料、工作簿或日志。

## 统一调用

- 字段发现：`xunpanyun-crm fields <object>`
- 对象查询：`xunpanyun-crm query <object> [options]`
- 通用对象写入：`create/update lead|customer|contact|opportunity|followUpRecord`
- 公私海：`pool assign|transfer|return`；private transfer不开放transferRelatedObj相关参数
- 商机阶段：`opportunity-stage`；订单头/明细：`order-data`
- 写入预览：使用对应写命令并加 `--dry-run`
- 确认写入：只有用户明确确认后才加 `--confirm`

## 面向业务人员的执行回执

每次调用都先给业务人员一个简短“执行卡”，包含：本次对象、筛选/变更范围、是否只读、是否需要确认。执行后固定返回：结果摘要、记录ID或命中数、异常/未处理项、下一步动作。不得把CLI命令、环境变量和技术堆栈作为主要交付。

常用说法可直接触发：

- “查询这个客户最近90天的联系人、商机、跟进和订单摘要。”
- “先预览把这两条公海线索分配给指定负责人，不要直接执行。”
- “根据会议纪要生成跟进记录预览，确认后再写回。”
- “检查这张订单的币种、明细合计和SKU关联。”

## 写入边界

所有CRM写入必须依次执行：字段发现 → 查询目标 → dry-run预览 → 用户明确确认 → confirm写入。非公私海写入随后同步查询回查；公私海三类批量接口返回code=10000时只能说明“已受理，待系统通知确认”，不得用同步查询代替最终系统通知，也不得宣称完成。private transfer不得传递枚举未明确的transferRelatedObj及关联对象保留参数。

## 错误处理

- `AUTH_REQUIRED`：尚未配置凭证。
- `AUTH_INVALID`：凭证无效或无权限，提示重新配置。
- `API_ERROR`：保留脱敏后的HTTP状态和询盘云业务错误码。
- 不因接口失败而编造或缓存业务结果。

## 重点测试

- Runtime缺失时由市场安装器快速安装
- 安装后自动进入授权并续跑原任务
- 自动安装失败时只给一个下一步动作
- 不扫描PATH、installed_plugins.json或文件系统
- 首次安装配置弹窗
- 密钥不进入对话和日志
- 错误凭证与过期Token
- 不同客户凭证隔离
- 字段动态发现
- 查询分页与空结果
- 非公私海写入必须经过dry-run、确认和同步回查
- 公私海异步受理与最终完成状态分离
- private transfer不暴露transferRelatedObj
