# 限时折扣活动表单字段

本文件由 `activity-forms/discount.json` 转写，用于创建「限时折扣」活动时生成活动表单草稿。最终前端工具参数外壳以 `get_web_client_tool_schema(<工具名>)` 返回的 inputSchema 为准。

## 填写规则

- 活动表单草稿字段名和层级必须与下表字段路径一致；真实调用时按前端工具 inputSchema 决定是否需要外层 `formData`。
- “必填=是”的字段必须填写；嵌套字段在其父对象存在时按必填规则处理。
- 有默认值的字段直接使用默认值；只有一个可选项的枚举直接使用该选项；没有默认值的高风险业务参数先从 query 和上下文抽取，仍无法可靠补齐时按主流程保守默认生成。只有活动权限校验失败、表单填充工具不可用、用户明确指定过去的绝对时间且无法安全修正等主流程允许的阻断场景才追问或终止。
- 枚举字段必须使用枚举值，不要填写中文说明。
- 时间字段必须使用 `YYYY-MM-DD HH:mm:ss` 格式字符串，例如 `2026-04-28 17:17:35`。
- 调用实际表单填充工具只表示把表单内容填入页面，不代表活动已提交或创建成功。

## 顶层必填字段

- `activityName`
- `activityTime`
- `limitPurchaseSetting`
- `orderAutoClosedTime`

## 字段说明

| 字段路径 | 类型 | 必填 | 默认值 | 枚举 | 约束 | 说明 |
|---|---|---|---|---|---|---|
| `activityName` | string | 是 |  |  | 最大长度: 30 | 活动名称，最多30字 |
| `activityTime` | object | 是 |  |  |  | 活动时间 |
| `activityTime.type` | string | 是 | "1" | "1" |  | 时间类型，1 固定时间 |
| `activityTime.start` | string | 是 |  |  |  | 活动开始时间，格式：YYYY-MM-DD HH:mm:ss |
| `activityTime.end` | string | 是 |  |  |  | 活动结束时间，格式：YYYY-MM-DD HH:mm:ss |
| `limitPurchaseSetting` | object | 是 |  |  |  | 限购设置 |
| `limitPurchaseSetting.limitNum` | integer | 否 |  |  | 最小值: 1 | 限购数量，当 `limitType` 不为 "1" 时必填 |
| `limitPurchaseSetting.limitType` | string | 是 | "1" | "1"<br>"2"<br>"3" |  | 1 不限购，2 每人所有商品限购{limitNum}件超过不可原价购买，3 每人所有商品前{limitNum}件享受折扣，超过可原价购买 |
| `orderAutoClosedTime` | integer | 是 |  |  | 最小值: 3<br>最大值: 360 | 订单设置：订单[3-360]分钟后自动关闭，提示：下单扣减商品库存，设置合理时间便于及时释放库存，可输入3～360分钟 |
| `useOfCustomer` | object | 否 |  |  |  |  |
| `useOfCustomer.type` | string | 否 | "301" | "301" |  | 适用人群: 301 全部人群 |
| `useOfPlace` | object | 否 |  |  |  |  |
| `useOfPlace.type` | string | 否 | "201" | "201" |  | 适用组织: 201 全部归属组织 |
| `activityDesc` | string | 是 |  |  | 最大长度: 300 | 活动说明，最多300字 |

## 表单填充工具调用示例

```json
{
  "name": "<实际表单填充工具名>",
  "tool_args": {
    "<按 get_web_client_tool_schema 返回的 inputSchema 组装>": "<字段值>"
  }
}
```
