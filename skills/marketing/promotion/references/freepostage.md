# 满减邮活动表单字段

本文件由 `activity-forms/freepostage.json` 转写，用于创建「满减邮」活动时生成活动表单草稿。最终前端工具参数外壳以 `get_web_client_tool_schema(<工具名>)` 返回的 inputSchema 为准。

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
- `postageSetting`
- `activityDesc`

## 字段说明

| 字段路径 | 类型 | 必填 | 默认值 | 枚举 | 约束 | 说明 |
|---|---|---|---|---|---|---|
| `activityName` | string | 是 |  |  | 最大长度: 30 | 活动名称，最多30字 |
| `activityTime` | object | 是 |  |  |  | 活动时间 |
| `activityTime.type` | string | 是 | "1" | "1" |  | 时间类型，1 固定时间 |
| `activityTime.start` | string | 是 |  |  |  | 活动开始时间，格式：YYYY-MM-DD HH:mm:ss |
| `activityTime.end` | string | 是 |  |  |  | 活动结束时间，格式：YYYY-MM-DD HH:mm:ss |
| `postageSetting` | object | 是 |  |  |  |  |
| `postageSetting.postageSettingFactor` | string | 是 | "102" | "102"<br>"103" |  | 包邮条件：102满元，103满件 |
| `postageSetting.ruleList` | array | 是 |  |  | 最少项数: 1 |  |
| `postageSetting.ruleList[].postageCondition` | number | 是 |  |  |  | 活动条件: 最大值{postageSettingFactor=='102' ? 9999999 : 300};最小值{postageSettingFactor== '102' ? 0 : 1};保留小数位数{postageSettingFactor == '102' ? 2 : 0};文案 满{postageCondition}{postageSettingFactor=='102' ? '元' : '件'} |
| `postageSetting.ruleList[].postageType` | string | 是 | "2001" | "2001"<br>"2002" |  | 优惠方式：2001 包邮，2002 满减邮 |
| `postageSetting.ruleList[].postageReduceAmt` | number | 否 |  |  | 最小值: 0.01<br>最大值: 9999999 | 减免费用: 只有postageType为2002时，postageReduceAmt才有效 |
| `postageSetting.ruleList[].limitDistrictType` | string | 是 | "0" |  |  | 固定值为 0 |
| `useOfCustomer` | object | 否 |  |  |  |  |
| `useOfCustomer.type` | string | 否 | "301" | "301" |  | 适用人群: 301 全部人群 |
| `useOfPlace` | object | 否 |  |  |  |  |
| `useOfPlace.type` | string | 否 | "201" | "201" |  | 适用组织: 201 全部归属组织 |
| `useOfGoods` | object | 否 |  |  |  |  |
| `useOfGoods.type` | string | 否 | "101" | "101" |  | 适用商品: 101 全部商品 |
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
