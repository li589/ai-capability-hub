---
name: kry-meituan-analysis
version: 1.0.0
description: 美团/大众点评舆情数据、评价数据获取与分析
---

# kry-meituan-analysis 美团、大众点评舆情分析

## 命令说明

### 导出

导出美团、大众点评评价数据（美团经营宝）：

```bash
kry-cli comment meituan export -o /path/file.xlsx --start '2026-04-01' --end '2026-04-30'
```

| 参数             | 说明                                                    | 必填  | 示例                |
| -------------- | ----------------------------------------------------- | --- | ----------------- |
| `-o, --output` | 把数据保存到文件，格式为 .xlsx                                    | 否   | `/path/file.xlsx` |
| `--start`      | 开始时间，ISO 8601 格式 YYYY-MM-DD，单次最大查询范围为 90 天，不填默认最近 7 天 | 否   | `2026-05-01`      |
| `--end`        | 结束时间，ISO 8601 格式 YYYY-MM-DD，单次最大查询范围为 90 天，不填默认最近 7 天 | 否   | `2026-05-31`      |

> 导出耗时较长（约 1 分钟），请提示用户耐心等待

### 登录美团/经营宝/大众点评

```bash
kry-cli comment meituan login
```

### 退登美团/经营宝/大众点评

```bash
kry-cli comment meituan logout
```

---

## 返回格式

命令将导出评价数据为 `xlsx` 文件到本地

## 分析报告

- 报告内容：基于参考模版，并按照用户的需求补充章节、段落、内容
- 参考模版：[template_meituan.md](../../references/template_meituan.md)
- 格式要求：生成单文件、交互式 HTML
