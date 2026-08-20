# 字段值与筛选器

## 字段值

| 字段类型 | `value` |
|---|---|
| text / textarea | 字符串 |
| number | 数字 |
| datetime | ISO时间字符串 |
| radiogroup / combo | 单个选项字符串 |
| checkboxgroup / combocheck | 字符串数组 |
| phone | `{"phone":"..."}` |
| address | 省、市、区、详情对象 |
| user / usergroup | username或username数组 |
| dept / deptgroup | dept_no或dept_no数组 |
| image / upload | 文件key数组 |
| subform | 子字段对象数组 |

更新子表单原有行时保留行 `_id`。缺少 `_id` 的行可能被当作新增行。

## 筛选器

```json
{"rel":"and","cond":[{"field":"_widget_xxx","type":"text","method":"eq","value":["精确值"]}]}
```

文本、文本域、下拉和单选不要使用 `like`。使用 `eq`、`in`，或 `not_empty` 拉取后在客户端过滤。电话与流水号可按接口支持使用 `like`。

使用 `jdy_list_data_2` 让客户端在发请求前校验常见字段类型与筛选方法。
