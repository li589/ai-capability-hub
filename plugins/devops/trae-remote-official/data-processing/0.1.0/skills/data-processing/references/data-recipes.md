# 数据处理 Pandas 代码模式

生成数据处理代码时参考以下模式。根据实际数据情况组合使用。

**重要约定**：生成的脚本应写入临时 .py 文件后通过 Shell 执行（避免 python3 -c 的引号嵌套问题）。脚本中每个处理步骤后加 print 说明。

---

## 文件读写

### 读取（处理编码问题）

```python
import pandas as pd
import chardet

def read_data(path):
    """智能读取数据文件，自动处理编码"""
    ext = path.rsplit('.', 1)[-1].lower() if '.' in path else ''
    
    if ext in ('xlsx', 'xls'):
        return pd.read_excel(path)
    elif ext == 'json':
        return pd.read_json(path)
    elif ext in ('csv', 'tsv', 'txt'):
        # 编码检测
        with open(path, 'rb') as f:
            raw = f.read(50000)
        detected = chardet.detect(raw)
        enc = detected['encoding'] or 'utf-8'
        # chardet 有时返回 'ascii'，对中文文件尝试 utf-8
        if enc.lower() in ('ascii', 'iso-8859-1'):
            enc = 'utf-8'
        sep = '\t' if ext == 'tsv' else ','
        try:
            return pd.read_csv(path, encoding=enc, sep=sep)
        except UnicodeDecodeError:
            # 回退尝试 gbk
            return pd.read_csv(path, encoding='gbk', sep=sep)
    else:
        return pd.read_csv(path)

df = read_data('input.csv')
print(f"读取完成：{len(df)} 行 × {len(df.columns)} 列")
print(f"列名：{list(df.columns)}")
```

### 输出

```python
# CSV（Excel 兼容 — 必须用 utf-8-sig）
df.to_csv('output.csv', index=False, encoding='utf-8-sig')

# Excel
df.to_excel('output.xlsx', index=False, engine='openpyxl')

# JSON（保留中文）
df.to_json('output.json', orient='records', force_ascii=False, indent=2)
```

---

## 数据探索

```python
# 基本概况
print(f"数据规模：{df.shape[0]} 行 × {df.shape[1]} 列")
print(f"\n列信息：")
for col in df.columns:
    dtype = df[col].dtype
    null_count = df[col].isnull().sum()
    null_pct = null_count / len(df) * 100
    unique = df[col].nunique()
    print(f"  {col}: {dtype}, 空值 {null_count}({null_pct:.1f}%), 唯一值 {unique}")

# 数值列统计
print(f"\n数值列统计：")
print(df.describe().round(2).to_string())

# 重复行检测
dup_count = df.duplicated().sum()
print(f"\n完全重复行：{dup_count} 行")

# 前5行预览
print(f"\n前5行：")
print(df.head().to_string())
```

---

## 清洗

### 去重

```python
before = len(df)
df = df.drop_duplicates()
print(f"去重：{before} → {len(df)} 行（移除 {before - len(df)} 行）")

# 按指定列去重（保留第一次出现）
df = df.drop_duplicates(subset=['订单ID'], keep='first')
```

### 空值处理

```python
# 查看空值分布
null_info = df.isnull().sum()
print("空值分布：")
print(null_info[null_info > 0])

# 填充策略
df['金额'] = df['金额'].fillna(0)                        # 数值列填0
df['金额'] = df['金额'].fillna(df['金额'].median())       # 数值列填中位数
df['城市'] = df['城市'].fillna('未知')                     # 文本列填默认值
df['金额'] = df['金额'].ffill()                           # 前向填充（时间序列）

# 删除关键列为空的行
df = df.dropna(subset=['订单ID', '金额'])
```

### 文本清理

```python
# 去前后空格
df['姓名'] = df['姓名'].str.strip()

# 统一空白字符（多个空格合并为一个）
df['地址'] = df['地址'].str.replace(r'\s+', ' ', regex=True).str.strip()

# 替换无效文本为空值
invalid_markers = ['N/A', 'n/a', 'NA', 'null', 'NULL', '-', '--', '无']
for col in df.select_dtypes(include='object').columns:
    df[col] = df[col].replace(invalid_markers, pd.NA)

# 统一大小写
df['城市'] = df['城市'].str.title()
```

### 日期标准化

```python
# 自动解析混合格式日期
df['日期'] = pd.to_datetime(df['日期'], format='mixed', errors='coerce', dayfirst=False)

# 格式化为统一字符串
df['日期'] = df['日期'].dt.strftime('%Y-%m-%d')

# 检查解析失败的行
failed = df['日期'].isna()
if failed.any():
    print(f"日期解析失败：{failed.sum()} 行")
```

### 类型转换

```python
# 文本转数值（带异常处理）
df['金额'] = pd.to_numeric(df['金额'].astype(str).str.replace(',', '').str.replace('¥', ''), errors='coerce')

# 转整数（先去空值）
df['数量'] = df['数量'].fillna(0).astype(int)
```

### 异常值处理

```python
import numpy as np

# 识别异常值（3倍标准差法）
col = '金额'
mean, std = df[col].mean(), df[col].std()
outliers = df[(df[col] > mean + 3*std) | (df[col] < mean - 3*std)]
print(f"异常值：{len(outliers)} 行")

# 标记而非删除（保留原始数据）
df['金额_异常'] = np.where(
    (df['金额'] > mean + 3*std) | (df['金额'] < mean - 3*std),
    '异常', '正常'
)

# 裁剪到合理范围
df['金额_裁剪'] = df['金额'].clip(lower=0, upper=mean + 3*std)
```

---

## 转换

**重要：数值计算结果务必用 `.round(2)` 避免浮点精度问题（如 55×8.8=484.00000000000006）**

### 宽表转长表

```python
# 多列数值转为行
df_long = df.melt(
    id_vars=['月份'],          # 保持不变的列
    var_name='品类',            # 新的分类列名
    value_name='销售额'         # 新的数值列名
)
# 输入：月份 | 电子产品 | 家居用品 | 食品饮料
# 输出：月份 | 品类 | 销售额
```

### 长表转宽表

```python
df_wide = df.pivot_table(
    index='月份',               # 行标签
    columns='品类',             # 列标签
    values='销售额',            # 值
    aggfunc='sum'              # 聚合方式
).reset_index()
```

### 分组聚合

```python
summary = df.groupby('部门').agg(
    人数=('员工ID', 'count'),
    平均薪资=('月薪', 'mean'),
    最高薪资=('月薪', 'max'),
    最低薪资=('月薪', 'min'),
    总薪资=('月薪', 'sum')
).reset_index().round(0)
```

### 条件派生列

```python
import numpy as np

# 简单二分
df['薪资等级'] = np.where(df['月薪'] > 20000, '高薪', '普通')

# 多条件
conditions = [
    df['月薪'] >= 25000,
    df['月薪'] >= 15000,
    df['月薪'] >= 8000,
]
choices = ['高薪', '中薪', '基础']
df['薪资等级'] = np.select(conditions, choices, default='实习')

# 基于多列的复合条件
df['风险等级'] = np.where(
    (df['满意度'] < 3) & (df['加班'] > 20), '高风险', '正常'
)
```

### 排名与百分比

```python
# 排名
df['销售排名'] = df['销售额'].rank(ascending=False, method='dense').astype(int)

# 占比
df['占比(%)'] = (df['销售额'] / df['销售额'].sum() * 100).round(1)

# 累计占比
df = df.sort_values('销售额', ascending=False)
df['累计占比(%)'] = df['占比(%)'].cumsum().round(1)
```

---

## 合并

### 纵向合并（结构相同的多表）

```python
import glob

# 读取多个文件
files = glob.glob('data/月报_*.csv')
dfs = []
for f in files:
    tmp = read_data(f)
    tmp['来源文件'] = Path(f).stem  # 标记来源
    dfs.append(tmp)

df = pd.concat(dfs, ignore_index=True)
print(f"合并完成：{len(files)} 个文件 → {len(df)} 行")
```

### 横向关联（VLOOKUP逻辑）

```python
# 左连接（保留主表所有行）
df = df_orders.merge(df_customers, on='客户ID', how='left')

# 多键连接
df = df1.merge(df2, on=['年份', '部门'], how='inner')

# 检查连接后的行数变化（防止多对多导致膨胀）
print(f"连接前：{len(df_orders)} 行，连接后：{len(df)} 行")
if len(df) > len(df_orders) * 1.1:
    print("⚠️ 行数显著增加，可能存在多对多关系，请检查连接键的唯一性")
```

---

## 筛选

```python
# 条件筛选
df_filtered = df[df['金额'] > 1000]
df_filtered = df[df['城市'].isin(['北京', '上海', '广州'])]
df_filtered = df[df['日期'].between('2024-01-01', '2024-06-30')]

# 多条件（& 表示且，| 表示或）
df_filtered = df[(df['金额'] > 1000) & (df['状态'] == '已支付')]

# 文本模糊筛选
df_filtered = df[df['商品名'].str.contains('手机', na=False)]

# 排除筛选
df_filtered = df[~df['状态'].isin(['已退款', '已取消'])]
```

---

## 可视化数据准备

当需要调用 chart_render.py 时，先将处理好的 DataFrame 转为 JSON：

```python
import json

# 准备图表数据
chart_data = df[['月份', '电子产品', '家居用品', '食品饮料']].to_dict('records')

# 写入临时 JSON 文件
json_path = '/tmp/chart_data.json'
with open(json_path, 'w', encoding='utf-8') as f:
    json.dump(chart_data, f, ensure_ascii=False, indent=2)

print(f"图表数据已准备：{json_path}")
```

对于饼图等需要聚合的场景：
```python
# 聚合后准备饼图数据
pie_data = df.groupby('品类')['销售额'].sum().reset_index()
pie_data.columns = ['品类', '销售额']
chart_data = pie_data.to_dict('records')
```

---

## 多文件合并+汇总+可视化 标准产出模式

当用户要求"合并多文件并做可视化"时，标准产出应包含3个文件：

```python
# 1. 合并明细表（含计算列）
df['销售额'] = (df['数量'] * df['单价']).round(2)  # 注意round(2)
df.to_csv('sales_merged.csv', index=False, encoding='utf-8-sig')

# 2. 汇总透视表
summary = df.pivot_table(index='商品', columns='月份', values='销售额', aggfunc='sum').round(2)
summary['合计'] = summary.sum(axis=1).round(2)
summary.to_csv('sales_summary.csv', encoding='utf-8-sig')

# 3. 可视化HTML（看板或单图）
# 将summary转为JSON传给chart_render.py或直接生成HTML
```
