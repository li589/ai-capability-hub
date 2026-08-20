---
name: customer-profile
description: 客户资料与客户列表查询助手，支持按手机号、姓名、昵称、客户编号、会员卡号检索，并按消费金额、积分、余额、企微关系筛选。触发词：查客户资料、搜客户列表、按手机号找客户、筛消费客户。
displayName:
  zh: 客户资料查询
  en: Customer Profile Search
displayDescription:
  zh: 查询客户资料和客户列表，支持按身份信息检索，并按消费、积分、余额及企微关系等条件筛选。
  en: Search customer profiles and lists by identity details, then filter by
    spending, points, balance, and WeCom relationship criteria.
disable-model-invocation: true
---

# 客户管理

## 功能说明

本 skill 让 WAI 代表商家查询 CRM 客户资料与客户列表，结果全部来自微盟商家后台真实接口（`woscli admin-api`），不做汇总建模，也不做数据写入。

| 能力 | 命令 | 产出 |
|---|---|---|
| 客户个人资料 | `woscli admin-api query-user-info` | 单个客户的完整资料字段 |
| 客户列表检索 | `woscli admin-api query-user-list` | 分页客户列表与多维筛选结果 |

### 前置条件

- 当前登录态、商户、门店上下文由 Weimob Assistant 上层统一提供，woscli 自动注入。
- 本 skill 不负责获取或写入会话级上下文数据。
- **重要：只能查询当前店铺的数据，禁止使用其他店铺的 bos_id、vid 等标识进行查询。**
- `query-user-info` 的 `--queryWid` 是**目标客户** wid。

## 触发场景

- 查客户资料、看这个客户详情、查 wid 为 xxx 的客户
- 搜客户列表、翻页看客户、按条件筛客户
- 按手机号找客户、按姓名找客户、按微信昵称找客户
- 按客户编号查客户、按会员卡号查客户
- 筛最近消费客户、筛累计消费金额区间客户、筛售后次数多的客户
- 看积分区间客户、看余额区间客户
- 筛企微好友客户、看已流失/未流失企微客户

## 调用方式

```bash
woscli admin-api <command> [args]
```

### 通用调用约定

- 命令入口：`woscli admin-api <command> [args]`，底层为微盟商家后台真实接口，由 woscli 统一处理登录态、商户、门店上下文。
- 命令与能力对应：`query-user-info`（客户详情）、`query-user-list`（客户列表）。
- 依赖上层提供登录态、当前商户、当前门店；缺失时按命令返回提示上层补齐。

### 能力路由

| 用户意图 | 处理方式 |
|---|---|
| 已知目标客户 wid，要看客户详情 | `query-user-info --queryWid <目标客户wid>` |
| 只有手机号/姓名/昵称，要找客户 | 先 `query-user-list` 定位，再按需 `query-user-info` |
| 要按消费、积分、余额、企微条件筛人群 | `query-user-list` 并组合筛选参数 |
| 要查某客户的积分/储值流水 | 本 skill 先定位 wid，流水交给积分或储值 skill |
| 要客户数汇总、增长趋势、分层分析 | 不属于本 skill，转数据分析能力 |

## 支持的操作

### 1. 客户个人资料查询（query-user-info）

用途：查询单个客户个人资料，适合“看这个客户资料”“查 wid 为 xxx 的客户详情”。

| 参数 | 说明 |
|---|---|
| `--queryWid` | 目标客户 wid，必填 |

```bash
woscli admin-api query-user-info --queryWid 1001693477
```

> 说明：原 `--display` 为脚本本地格式化参数；woscli 直接返回接口字段，模型按 `optionList` 把单选/多选字段映射为中文、时间戳转为 `YYYY-MM-DD` 后回复即可。

格式化输出规则与字段分组说明见 `@references/user-info.md`。

### 2. 客户列表查询（query-user-list）

用途：查询客户列表，支持精确检索与多维筛选。

| 用途 | 关键参数 |
|---|---|
| 分页 | `--pageNum`、`--pageSize` |
| 基础检索 | `--phone`、`--name`、`--nickName`、`--cardNo` |
| 方案指定 | `--pointPlanId`、`--amountPlanId` |
| 时间筛选（ISO 8601 UTC） | `--startBecomeCustomerTime`/`--endBecomeCustomerTime`、`--startBecomeMemberTime`/`--endBecomeMemberTime`、`--startLastConsumeTime`/`--endLastConsumeTime`、`--startFollowTime`/`--endFollowTime` |
| 金额与次数筛选 | `--startLastConsumeAmount`/`--endLastConsumeAmount`、`--startConsumeAmountAll`/`--endConsumeAmountAll`、`--startAfterSalesCountAll`/`--endAfterSalesCountAll` |
| 积分与余额筛选 | `--startCurrentPoint`/`--endCurrentPoint`、`--startCurrentAmount`/`--endCurrentAmount` |
| 企微关系筛选 | `--followFriendsFlag` |

```bash
woscli admin-api query-user-list --phone '13800000000'
woscli admin-api query-user-list --nickName '小明' --pageNum 1 --pageSize 20
woscli admin-api query-user-list --startCurrentPoint 100 --endCurrentPoint 1000 --followFriendsFlag 1
woscli admin-api query-user-list --startLastConsumeTime 2026-03-01T00:00:00.000Z --endLastConsumeTime 2026-04-01T23:59:59.999Z
```

完整参数词典、时间格式与枚举值见 `@references/user-list.md`。

### 3. 工作流

1. 先判断用户要的是单个客户详情还是客户列表。
2. 单个客户详情且已知目标 wid，直接使用 `query-user-info`；否则先用 `query-user-list` 定位。
3. 列表检索使用 `query-user-list`，按需组合基础检索与筛选条件。
4. 如果后续还要查积分或储值流水，先从客户详情或列表中确定目标 wid 再移交对应 skill。

## 输出格式

### query-user-info 返回

- `userInfos`：客户资料字段值。
- `cardGroups`：字段分组与选项元数据。
- `paasOpen`：是否开通 PaaS。

`--display` 展示口径（模型按返回处理）：

- 时间戳字段转换为 `YYYY-MM-DD`。
- 单选/多选字段按 `optionList` 映射为中文。
- 地址 JSON 拼接为省市区街道和详细地址。
- 图片字段保留 URL。

### query-user-list 返回

- `pageNum`、`pageSize`、`totalCount`。
- `users`：客户列表。

客户字段分组：

- 基础：`wid`、`nickName`、`name`、`phone`、`headUrl`、成为客户/会员时间。
- 积分与储值：`point`、`totalPoint`、`depositAmount`、`balance`、`totalBalance`。
- 消费：最近消费、累计消费、消费次数、退款/售后金额和次数。
- 导购：绑定导购、分享导购、导购到访时间和次数。
- 推客：推客等级、绑定推客、分享推客。
- 状态：客户状态、黑名单、手机号存在状态、冻结信息。
- 企微：好友关系、首次添加时间、企微员工名称、来源。

### 回复要求

- 只返回命令真实结果，不捏造、不补全客户字段。
- `query-user-info` / `query-user-list` 输出通常包含敏感字段，除非业务明确需要，不要在自然语言中额外展开敏感值。
- 不向用户暴露 token、bosId、vid。
- 若已知当前商户/门店名称，回答结尾附带当前商户与门店。

## 注意事项/边界

- 客户资料包含手机号、头像、地址等敏感字段，自然语言回复只展示完成任务所需信息。
- `query-user-list` 的时间类参数使用 ISO 8601 UTC 格式（如 `2026-03-01T00:00:00.000Z`），不要传自然日字符串。
- `--pointPlanId` / `--amountPlanId` 不传时接口自动取第一条方案；若商户存在多套方案，需在回复中说明实际使用的方案 ID。
- 本 skill 只做客户查询，不做客户资料修改、打标、拉黑、发券等写操作。
- 客户数汇总、留存分层、增长趋势等分析型诉求不属于本 skill，转交数据分析能力。
