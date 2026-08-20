# 时间参数标准化

## 默认时间

用户未指定时间时，默认最近 7 个完整自然日。

## 对外展示

返回统计结果时，必须先写明完整统计区间，格式为“开始日 00:00:00 至结束日 23:59:59”。例如：`2026-07-09 00:00:00 至 2026-07-15 23:59:59`。

## 格式转换

| 场景 | 规则 |
|------|------|
| `beginDate` | 用户指定开始日转成 `yyyy-MM-dd 00:00:00` |
| `endDate`（包含当天口径） | 用户指定结束日按自然日包含，转成 `yyyy-MM-dd 23:59:59` |
| `endDate`（左闭右开口径） | DataCube 类查询取查询截止日下一天的 `yyyy-MM-dd 00:00:00` |
| 自然语言时间 | "近一个月""本月""上周"先解析为当前统计周期，再统一生成 `beginDate/endDate` |
| 营业日查询 | `--settle-date yyyy-MM-dd --date-type 2` |
| 时间范围查询 | `--begin-date "yyyy-MM-dd HH:mm:ss" --end-date "yyyy-MM-dd HH:mm:ss" --date-type 5` |

## 上一周期自动计算

不要向用户额外索要上一区间；按以下前端平移公式自动计算：

```text
rangeDays = (Date.parse(endDate) - Date.parse(beginDate) + 1000) / 1000 / 60 / 60 / 24
preBeginDate = beginDate - rangeDays days
preEndDate = endDate - rangeDays days
```

示例：当前周期为 `2026-05-11 00:00:00` 到 `2026-05-17 23:59:59` 时，`rangeDays=7`，上一区间为 `2026-05-04 00:00:00` 到 `2026-05-10 23:59:59`。

## 趋势粒度

| 参数 | 规则 |
|------|------|
| `dateType=1` | 按天（默认） |
| `dateType=2` | 按月；用户问月趋势或按月时使用 |
