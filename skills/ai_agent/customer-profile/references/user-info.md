# 客户资料查询参考（query-user-info）

## 用途

查询单个客户个人资料，适合“看这个客户资料”“查 wid 为 xxx 的客户详情”。

## 参数

| 参数 | 必填 | 说明 |
|---|---|---|
| `--queryWid` | 是 | 目标客户 wid |
| `--mask` | 否 | 对响应做额外脱敏；默认不额外脱敏，以匹配后台客户详情展示 |

## 请求要点

- 请求体包含 `queryWid` 和 `basicInfo`。

## 返回结构

| 字段 | 说明 |
|---|---|
| `userInfos` | 客户资料字段值 |
| `cardGroups` | 字段分组与选项元数据 |
| `paasOpen` | 是否开通 PaaS |

## 格式化输出规则（模型按返回处理）

- 时间戳字段转换为 `YYYY-MM-DD`。
- 单选/多选字段按 `optionList` 映射为中文。
- 地址 JSON 拼接为省市区街道和详细地址。
- 图片字段保留 URL。

## 示例

```bash
# 查看客户详情
woscli admin-api query-user-info --queryWid 1001693477
```

## 注意

- 只有目标客户 wid 才能查询详情；只有手机号时先用 `query-user-list --phone` 定位。
- 返回包含手机号、头像、地址等敏感字段，自然语言回复中不要额外展开。
