# 客户列表查询参考（query-user-list）

## 用途

查询 CRM 客户列表，支持精确检索和多维筛选。

## 基础检索参数

| 参数 | 说明 |
|---|---|
| `--phone` | 手机号，精确查询 |
| `--name` | 姓名，精确查询 |
| `--nickName` | 微信昵称，精确查询 |
| `--cardNo` | 会员卡号，精确查询 |
| `--pageNum` / `--pageSize` | 分页 |

## 方案参数

| 参数 | 说明 |
|---|---|
| `--pointPlanId` | 积分方案 ID；不传时接口自动取第一条积分方案 |
| `--amountPlanId` | 储值方案 ID；不传时接口自动取第一条储值方案 |

## 时间筛选（ISO 8601 UTC）

| 参数 | 说明 |
|---|---|
| `--startBecomeCustomerTime` / `--endBecomeCustomerTime` | 成为客户时间 |
| `--startBecomeMemberTime` / `--endBecomeMemberTime` | 成为会员时间 |
| `--startLastConsumeTime` / `--endLastConsumeTime` | 最近消费时间 |
| `--startFollowTime` / `--endFollowTime` | 企微添加时间 |

格式示例：`2026-03-01T00:00:00.000Z`

## 金额与次数筛选

| 参数 | 说明 |
|---|---|
| `--startLastConsumeAmount` / `--endLastConsumeAmount` | 最近消费金额 |
| `--startConsumeAmountAll` / `--endConsumeAmountAll` | 累计消费金额 |
| `--startAfterSalesCountAll` / `--endAfterSalesCountAll` | 累计售后次数 |

## 积分、余额与企微筛选

| 参数 | 说明 |
|---|---|
| `--startCurrentPoint` / `--endCurrentPoint` | 当前积分范围 |
| `--startCurrentAmount` / `--endCurrentAmount` | 账户余额范围 |
| `--followFriendsFlag` | 企微好友关系，见下表 |

### 企微好友关系（--followFriendsFlag）

| 值 | 含义 |
|---|---|
| `-2` | 全部 |
| `-1` | 从未加过 |
| `0` | 已流失 |
| `1` | 未流失 |

## 返回结构

- `pageNum`、`pageSize`、`totalCount`
- `pointPlanId`、`amountPlanId`：实际查询使用的方案 ID
- `users`：客户列表

### 客户字段

| 分组 | 字段 |
|---|---|
| 基础 | `wid`、`nickName`、`name`、`phone`、`headUrl`、成为客户/会员时间 |
| 积分/储值 | `point`、`totalPoint`、`depositAmount`、`balance`、`totalBalance` |
| 消费 | 最近消费、累计消费、消费次数、退款/售后金额和次数 |
| 导购 | 绑定导购、分享导购、导购到访时间和次数 |
| 推客 | 推客等级、绑定推客、分享推客 |
| 状态 | 客户状态、黑名单、手机号存在状态、冻结信息 |
| 企微 | 好友关系、首次添加时间、企微员工名称、来源 |

## 示例

```bash
woscli admin-api query-user-list --phone '13800000000'
woscli admin-api query-user-list --nickName '小明' --pageNum 1 --pageSize 20
woscli admin-api query-user-list --startLastConsumeTime 2026-03-01T00:00:00.000Z --endLastConsumeTime 2026-04-01T23:59:59.999Z
woscli admin-api query-user-list --startCurrentPoint 100 --endCurrentPoint 1000 --followFriendsFlag 1
```
