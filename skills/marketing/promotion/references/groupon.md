# 拼团活动表单字段

本文件由 `activity-forms/groupon.json` 转写，用于创建「拼团」活动时生成活动表单草稿。最终前端工具参数外壳以 `get_web_client_tool_schema(<工具名>)` 返回的 inputSchema 为准。

## 填写规则

- 活动表单草稿字段名和层级必须与下表字段路径一致；真实调用时按前端工具 inputSchema 决定是否需要外层 `formData`。
- “必填=是”的字段必须填写；嵌套字段在其父对象存在时按必填规则处理。
- 有默认值的字段直接使用默认值；只有一个可选项的枚举直接使用该选项；没有默认值的高风险业务参数先从 query 和上下文抽取，仍无法可靠补齐时按主流程保守默认生成。只有活动权限校验失败、表单填充工具不可用、用户明确指定过去的绝对时间且无法安全修正等主流程允许的阻断场景才追问或终止。
- 枚举字段必须使用枚举值，不要填写中文说明。
- 时间字段按字段说明填写；`startDate`、`endDate` 使用毫秒级时间戳 number。生成时先得到 `YYYY-MM-DD HH:mm:ss` 标准时间字符串，再调用 `string_to_timestamp(time_string="<标准时间字符串>", fmt="%Y-%m-%d %H:%M:%S", timezone_offset=8, output_millis=True)`，使用工具返回值填入字段。
- 不要让模型直接推算、心算或编造 `startDate`、`endDate`；不要把 `YYYY-MM-DD HH:mm:ss` 字符串直接填入这两个字段。
- 调用实际表单填充工具只表示把表单内容填入页面，不代表活动已提交或创建成功。

## 顶层必填字段

- `title`
- `startDate`
- `endDate`
- `durationTime`

## 字段说明

| 字段路径 | 类型 | 必填 | 默认值 | 枚举 | 约束 | 说明 |
|---|---|---|---|---|---|---|
| `title` | string | 是 |  |  | 最大长度: 30 | 活动名称，最多30字 |
| `startDate` | number | 是 |  |  | 格式: 毫秒级时间戳 number，必须来自 `string_to_timestamp(..., output_millis=True)` 工具返回值 | 活动开始时间 |
| `endDate` | number | 是 |  |  | 格式: 毫秒级时间戳 number，必须来自 `string_to_timestamp(..., output_millis=True)` 工具返回值 | 活动结束时间 |
| `durationTime` | integer | 是 |  |  |  | 成团有效时间，单位分钟，必须为正整数,例如 1天是1440分钟 |
| `useOfCustomer` | object | 否 |  |  |  |  |
| `useOfCustomer.type` | string | 否 | "301" | "301" |  | 适用人群: 301 全部人群 |
| `useOfPlace` | object | 否 |  |  |  |  |
| `useOfPlace.type` | string | 否 | "201" | "201" |  | 适用组织: 201 全部归属组织 |
| `notes` | string | 是 |  |  | 最大长度: 300 | 活动说明，最多300字 |

## 表单填充工具调用示例

```json
{
  "name": "<实际表单填充工具名>",
  "tool_args": {
    "<按 get_web_client_tool_schema 返回的 inputSchema 组装>": "<字段值>"
  }
}
```
