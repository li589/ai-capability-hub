# 数据质量评估清单

数据探索时，按以下6个维度逐项检查。输出格式为结构化的质量报告。

## 6维度检查

### 1. 完整性（Completeness）

检查各列的空值情况：

```python
null_report = df.isnull().sum()
null_pct = (null_report / len(df) * 100).round(1)
```

报告标准：
- 空值率 = 0：正常
- 0 < 空值率 ≤ 5%：轻微，可直接处理
- 5% < 空值率 ≤ 30%：需要决策（删除行 or 填充），询问用户
- 空值率 > 30%：严重，该列可能不可用，告知用户

### 2. 唯一性（Uniqueness）

检查是否存在重复数据：

```python
dup_count = df.duplicated().sum()
# 检查疑似主键列的唯一性
for col in potential_id_cols:
    dup_in_col = df[col].duplicated().sum()
```

识别疑似主键列的规则：列名含 "ID"/"id"/"编号"/"序号" 或唯一值比率 > 95%

### 3. 有效性（Validity）

检查数据类型和值域：

- 数值列：是否有非数值内容、是否在合理范围内
- 日期列：是否能正确解析、是否在合理时间范围内
- 分类列：唯一值数量是否合理（如"性别"列出现100个不同值则异常）

```python
for col in numeric_cols:
    print(f"{col}: min={df[col].min()}, max={df[col].max()}, 非数值行数={pd.to_numeric(df[col], errors='coerce').isna().sum()}")
```

### 4. 一致性（Consistency）

检查同一语义的数据格式是否统一：

- 日期格式：是否混用 `2024-01-15`、`2024/01/15`、`01/15/2024`
- 金额格式：是否混用 `1000`、`¥1,000`、`1000.00`
- 文本大小写/空格：同一名称是否有不同写法

```python
# 日期格式一致性检测示例
date_patterns = df['日期'].apply(lambda x: 'YYYY-MM-DD' if re.match(r'\d{4}-\d{2}-\d{2}', str(x)) else 'other')
```

### 5. 准确性（Accuracy）

标记可疑数据：

- 负值出现在不应为负的列（如金额、数量）
- 零值可能表示缺失而非真实为零
- 异常大值（超过均值 + 3倍标准差）

```python
for col in numeric_cols:
    mean, std = df[col].mean(), df[col].std()
    outliers = df[col][(df[col] > mean + 3*std) | (df[col] < mean - 3*std)]
```

### 6. 时效性（Timeliness）

如果有日期列，报告：

- 数据覆盖的时间范围（最早~最新）
- 是否有时间间隙（某些日期/月份缺失）
- 最新数据距今多久

## 输出格式

向用户呈现质量报告时，使用以下结构：

```
## 数据概况
- 行数：XXX 行
- 列数：XX 列
- 文件大小：XX KB

## 列信息
| 列名 | 类型 | 空值率 | 唯一值数 | 示例值 |
|------|------|--------|---------|--------|

## 质量问题（按严重程度排列）
🔴 严重：[描述]
🟡 注意：[描述]
🟢 轻微：[描述]

## 建议处理方案
1. [建议1]
2. [建议2]
```
