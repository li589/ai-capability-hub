# 输出文件规范

所有数据处理操作的输出文件遵循以下规范。

## 文件编码

| 格式 | 编码 | 原因 |
|------|------|------|
| CSV | utf-8-sig (BOM) | Excel 打开 UTF-8 CSV 时不加 BOM 会中文乱码 |
| Excel | - | openpyxl 引擎，默认编码 |
| JSON | utf-8 | force_ascii=False 保留中文原文 |

## 文件命名

- 处理后文件：`{原文件名}_processed.{后缀}`
- 可视化文件：`{原文件名}_chart.html` 或 `{原文件名}_dashboard.html`
- 临时数据文件（传给 chart_render.py）：`/tmp/{原文件名}_chart_data.json`

用户指定了输出名称时，使用用户指定的名称。

## CSV 输出

```python
df.to_csv(output_path, index=False, encoding='utf-8-sig')
```

- 不输出行索引（index=False）
- 使用 utf-8-sig 编码

## Excel 输出

```python
df.to_excel(output_path, index=False, engine='openpyxl')
```

- 不输出行索引
- 使用 openpyxl 引擎（xlsxwriter 不支持读取已有文件）

## JSON 输出

```python
df.to_json(output_path, orient='records', force_ascii=False, indent=2)
```

- orient='records'：每行一个对象的数组格式
- force_ascii=False：保留中文
- indent=2：可读格式

## 处理记录

每次数据处理操作完成后，向用户输出处理记录摘要：

```
处理完成：
- 输入：sales_dirty.csv（20 行 × 7 列）
- 输出：sales_dirty_processed.csv（18 行 × 7 列）
- 操作：
  1. 去重：移除 1 行完全重复记录
  2. 日期标准化：统一为 YYYY-MM-DD 格式（影响 3 行）
  3. 空值填充：金额列 1 个空值填充为 0
```

## 可视化 HTML 输出

- 单个自包含 HTML 文件
- ECharts 通过 CDN 引入（需要网络）
- 响应式设计，适配不同屏幕
- 支持交互：悬停tooltip、缩放、数据下载
