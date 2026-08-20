# 售后查询参考（query-rights / query-rights-detail）

> 底层命令为 `woscli admin-api query-rights` 与 `query-rights-detail`，由 woscli 统一处理登录态、商户、门店上下文。

## query-rights 参数词典

| 参数 | 说明 |
|---|---|
| `--pageNum` | 页码（从 1 开始） |
| `--pageSize` | 每页数量 |
| `--startTime` | 时间范围起点（必填，ISO 8601 UTC） |
| `--endTime` | 时间范围终点（必填，ISO 8601 UTC） |
| `--queryTimeType` | 时间口径（售后固定 `0`=创建时间） |
| `--rightsStatuses` | 售后状态，多个用英文逗号分隔 |
| `--rightsTypes` | 售后类型：`1=退货退款`、`2=仅退款`、`5=换货` |

> 不支持 `--relative` / `--days` / `--begin-date` / `--end-date` 简写：调用前先把相对时间或自然日范围换算为实际 ISO 8601 UTC 时间。

## 售后状态（--rightsStatuses）

| 值 | 含义 |
|---|---|
| `0` | 待处理 |
| `1` | 已申请等待处理 |
| `2` | 等待买家退货 |
| `3` | 买家已退货等待商家确认收货 |
| `5` | 系统退款中 |
| `6` | 售后完成 |
| `7` | 取消 |
| `8` | 商家拒绝 |
| `9` | 退款失败 |
| `10` | 商家退款中 |
| `20` | 换货中 |
| `30` | 商家拒绝_待平台介入 |
| `31` | 待平台介入 |

## query-rights 返回结构

- `totalCount`、`pageNum`、`pageSize` 或 `pageList` 内的列表项（以接口实际返回为准）。
- `rights`：售后单列表，包含售后单号、申请 ID、状态、类型、来源、渠道、买家、退款金额、创建时间、原订单号、售后商品。

## query-rights-detail

参数：

- `--rightsOrderNo`：售后单号，必填。

返回结构：

- 售后单号、申请 ID、状态、类型、来源、原因、自动处理时间、退款失败原因
- 买家信息、商户信息、原订单、退款详情、售后商品、退货物流、售后轨迹、标记信息

## 示例

```bash
# 近 7 天售后，状态 1,2,6（queryTimeType 0=创建时间）
woscli admin-api query-rights --startTime 2026-08-04T00:00:00.000Z --endTime 2026-08-10T23:59:59.999Z --queryTimeType 0 --rightsStatuses 1,2,6
# 本月仅退款（type 2）
woscli admin-api query-rights --startTime 2026-08-01T00:00:00.000Z --endTime 2026-08-31T23:59:59.999Z --queryTimeType 0 --rightsTypes 2
# 售后详情
woscli admin-api query-rights-detail --rightsOrderNo 'R202604230001'
```
