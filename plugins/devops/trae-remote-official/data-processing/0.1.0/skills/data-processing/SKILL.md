---
name: data-processing
description: "数据整理与可视化。读取CSV/Excel/JSON文件，进行数据探索、清洗、转换、合并、可视化。当用户提到分析数据、处理数据、清洗数据、数据可视化、做图表、合并表格、格式转换、数据探索、看看这个数据、帮我整理数据，或用户提供了数据文件并要求处理时触发。"
---

# 数据整理与可视化

将用户的原始数据文件（CSV/Excel/JSON）整理为干净可用的数据，并按需生成交互式图表。

## 定位与边界

**做**：数据探索、清洗、格式转换、多表合并、数据透视、可视化图表、看板搭建
**不做**：业务结论生成、归因分析、预测建模、报告撰写、数据采集/爬虫、数据库连接、统计假设检验


---

## 核心约束（始终遵守）

1. **不修改原始文件**。所有处理结果写入新文件。
2. **先说明再执行**。任何数据修改操作前，先告知用户将做什么、影响多少行/列，等用户确认后再执行。
3. **不假设数据含义**。列名不清晰、数据含义不明确时，向用户确认而非自行猜测。
4. **不强行套用固定流程**。根据实际数据情况灵活判断分析路径。
5. **大数据量谨慎处理**。数据量 > 1000 行时，先在前 50 行上验证处理逻辑正确性，再全量执行。
6. **处理记录**。每次数据变换操作完成后输出摘要：做了什么、影响了多少行、为什么这样做。
7. **输出规范**。遵循 `references/output-standards.md` 中的编码、命名规范。

---

## 工作流

根据用户意图路由到三条路径。如果用户意图不明确，先按路径A做数据探索再询问用户下一步。

### 路径A：数据探索

**触发**：用户说"帮我看看这份数据"、"数据有什么问题"、"分析一下数据质量"等探索性需求。

**执行步骤**：

1. **读取文件**
   - 参考 `references/data-recipes.md` 中的文件读取模式
   - 中文 CSV 注意编码检测（chardet），尝试 utf-8 → gbk → gb2312
   - 读取失败时告知用户具体错误，不要静默跳过

2. **概况输出**
   - 行数、列数、文件大小
   - 各列的名称、数据类型、非空行数
   - 前5行数据预览

3. **质量检查**（按 `references/quality-checklist.md` 的6维度逐项检查）
   - 完整性：各列空值率（标注严重程度）
   - 唯一性：疑似主键列的重复情况
   - 有效性：数据类型合理性、值域范围
   - 一致性：日期格式是否混用、数值格式是否统一
   - 准确性：负值、零值、异常大值
   - 时效性：日期列的时间覆盖范围

4. **问题分级与建议**
   - 🔴 **阻断性问题**（关键列全空、主键大量重复）：停下来等用户决策
   - 🟡 **需要决策的问题**（缺失率高、含义不明的异常值）：列出处理方案的利弊，让用户选择
   - 🟢 **轻微问题**（少量空格、格式不一致）：可建议直接处理，但要告知

5. **输出建议的处理方案**，等用户确认后进入路径B执行

**示例交互**：
```
用户：帮我看看这份数据

AI：我来分析这份文件。

## 数据概况
- 文件：sales_dirty.csv（20 行 × 7 列）
- 列：订单ID(文本)、下单日期(文本)、商品类别(文本)、金额(数值)、客户城市(文本)、支付状态(文本)、客户姓名(文本)

## 质量问题

🔴 重复数据：第13行与第1行完全重复（订单ORD001）
🟡 空值：
  - 金额列：1个空值（第3行）
  - 客户城市列：1个空值（第9行）
🟡 日期格式不统一：存在3种格式
  - 2024-01-15（14行）
  - 2024/01/16（1行）
  - 01/18/2024（1行）
🟢 姓名前后有空格：第17行" 赵六 "
🟢 客户姓名含"N/A"文本：第20行

## 建议处理方案
1. 删除重复行
2. 统一日期格式为 YYYY-MM-DD
3. 金额空值 → 需要你确认：填0还是删除该行？
4. 城市空值 → 填"未知"还是删除？
5. 清理姓名空格和N/A

是否按以上方案处理？或者你有其他想法？
```

---

### 路径B：数据处理

**触发**：用户明确要求清洗、转换、合并、筛选、透视等操作。

**执行步骤**：

1. **理解意图**
   - 确认用户要做什么操作
   - 确认操作涉及哪些列/行
   - 如有歧义，先问清楚再做

2. **方案确认**
   - 向用户说明将执行的具体操作
   - 预估影响范围（多少行会被修改/删除）
   - 等用户确认

3. **执行**
   - 生成 pandas 处理脚本
   - 参考 `references/data-recipes.md` 中的代码模式
   - 脚本中先读取文件 → 处理 → 保存为新文件
   - 通过 Shell 执行脚本

4. **验证与汇报**
   - 执行后读取新文件前几行，验证处理结果
   - 向用户输出处理记录（参考 `references/output-standards.md` 的格式）

**处理代码编写规范**：
- 代码开头总是先做编码检测和读取
- 每个处理步骤加 print 说明做了什么（用户可看到执行过程）
- 最后输出文件时遵循命名和编码规范
- 脚本写入临时 .py 文件再执行（而非 python3 -c，避免引号问题）

**示例**：
```python
# 由 LLM 生成的处理脚本（写入临时文件后执行）
import pandas as pd
import chardet

# 读取
with open('sales_dirty.csv', 'rb') as f:
    enc = chardet.detect(f.read(10000))['encoding'] or 'utf-8'
df = pd.read_csv('sales_dirty.csv', encoding=enc)
print(f"读取完成：{len(df)} 行 × {len(df.columns)} 列")

# 1. 去重
before = len(df)
df = df.drop_duplicates()
print(f"去重：{before} → {len(df)} 行（移除 {before - len(df)} 行）")

# 2. 日期标准化
df['下单日期'] = pd.to_datetime(df['下单日期'], format='mixed', errors='coerce')
df['下单日期'] = df['下单日期'].dt.strftime('%Y-%m-%d')
print("日期格式已统一为 YYYY-MM-DD")

# 3. 空值填充
df['金额'] = df['金额'].fillna(0)
print("金额空值已填充为 0")

# 输出
output_path = 'sales_dirty_processed.csv'
df.to_csv(output_path, index=False, encoding='utf-8-sig')
print(f"已保存：{output_path}（{len(df)} 行）")
```

---

### 路径C：可视化

**触发**：用户要求做图表、可视化、看板。

**意图升级判断**：
- 如果用户只说"做趋势图"但上下文涉及多步操作（如合并+汇总+可视化），主动建议升级为看板模式
- 如果用户说"做个看板"或数据维度丰富（≥3个数值列+分类列），直接走仪表板模式
- 多文件合并后做可视化时，除图表外建议同时输出汇总表（pivot结果的CSV）

**执行步骤**：

1. **理解可视化需求**
   - 用户想看什么？（趋势/对比/占比/分布/关系）
   - 哪些列参与可视化？
   - 是单图还是多图看板？
   - 数据是否需要先聚合/透视？

2. **选择图表类型**
   - 参考 `references/chart-selection.md` 的决策树和场景化推荐
   - 如果用户没指定图表类型，根据数据特征推荐并说明理由
   - 看板模式至少3种不同图表类型
   - 有两个数值列可能存在关系时，优先加散点图
   - 有分组+多指标时，优先加雷达图

3. **数据准备**
   - 用 pandas 将数据转换为图表所需的 JSON 格式
   - 可能需要聚合、透视、筛选等操作
   - 数值计算结果用 `.round(2)` 避免浮点精度问题
   - 将 JSON 写入临时文件或 `data/` 目录

4. **生成可视化（按优先级选择方案）**

   **方案一（优先）：触发 dashboard-page skill 完整工作流**

   当需求涉及多图看板时，**必须触发 dashboard-page skill 执行其完整工作流**，而不是自己仿写类似风格的 HTML。

   具体做法：
   1. 本 skill 负责数据准备——用 pandas 将原始数据清洗、聚合为 dashboard-page 能消费的 CSV/JSON，存入 `{dashboard-slug}/data/` 目录
   2. 然后**停止自行生成 HTML**，改为向用户说明"数据已准备好，接下来将使用 dashboard-page skill 生成看板"
   3. 触发 dashboard-page skill，让它按自己的 workflow 执行：copy template → 适配数据层 → 生成 index.html → 运行 validate 校验
   
   关键约束：
   - 不要自己写 HTML 来"模仿" dashboard-page 的风格，那样会丢失暗色主题、时间控件、面板菜单、数据源模态框等核心能力
   - 不要把 dashboard-page 当作"样式参考"——它是一个完整的生成系统，必须让它自己跑完
   - 本 skill 的角色仅限于：数据准备 + 看板需求描述（标题、指标定义、图表类型建议）

   适用条件：
   - 需要多图组合的仪表板
   - 需要时间范围控件或数据源审计功能
   - 需要反复使用/定期刷新的看板
   - 用户说"做看板"、"生成 dashboard"

   **方案二（退化）：调用 chart_render.py 或直接写 HTML**

   仅当以下条件满足时才用本 skill 自行生成图表：
   - dashboard-page skill 不可用
   - 只需单张图表（如一个趋势线图）
   - 用户明确要求简单输出、不需要完整看板

   调用chart_render方式：
   ```bash
   python3 {skill_dir}/scripts/chart_render.py \
     --data /path/to/data.json \
     --chart-type line \
     --title "图表标题" \
     --x-axis "X轴字段" \
     --y-axis "系列1" "系列2" \
     --output /path/to/output.html
   ```
   仪表板模式：
   ```bash
   python3 {skill_dir}/scripts/chart_render.py \
     --data /path/to/data.json \
     --dashboard \
     --config /path/to/config.json \
     --output /path/to/dashboard.html
   ```

5. **告知用户**
   - 说明图表内容和文件路径
   - 提示可在浏览器中打开查看交互效果

**数据 JSON 格式**（传给 chart_render.py 的标准格式）：
```json
[
  {"月份": "2024-01", "电子产品": 156000, "家居用品": 89000},
  {"月份": "2024-02", "电子产品": 142000, "家居用品": 95000}
]
```

**仪表板 config.json 格式**：
```json
{
  "title": "看板标题",
  "charts": [
    {"type": "line", "title": "趋势图", "x_axis": "月份", "y_axis": ["电子产品", "家居用品"]},
    {"type": "pie", "title": "占比图", "x_axis": "品类", "y_axis": ["销售额"]},
    {"type": "bar", "title": "对比图", "x_axis": "部门", "y_axis": ["人数", "薪资"]}
  ],
  "metrics": [
    {"label": "总员工数", "value": "30 人"},
    {"label": "整体离职率", "value": "30.0%", "status": "danger"}
  ],
  "insights": [
    {"level": "danger", "text": "技术部离职率50%，平均周加班18.4小时"},
    {"text": "财务部/人事部离职率为0%，是稳定标杆"}
  ],
  "table": {
    "title": "部门指标明细",
    "columns": ["部门", "人数", "离职率"],
    "data": [["技术部", 14, "50%"]]
  }
}
```

---

## 可视化原则

产出的图表和看板应该像内部分析工具，不像 AI 生成的演示页面。追求**数据密度高、视觉干扰低**。

### 禁止（典型 AI 生成特征）

- 装饰性渐变背景、发光/光球效果、大面积投影
- 花哨的入场动画（elasticOut、bounceIn 等）
- 多余的 hover 放大/位移动效
- 在 CSS 中罗列大段显式配色板
- 把每个面板包在厚重圆角+大阴影的卡片中
- 装饰性图标、emoji、分割线花边
- 为了"好看"而添加的空状态卡片或二级信息网格

### 遵循

- **安静的容器**：面板用 1px 细线边框或极浅底色区分，不用厚影卡片
- **数据说话**：图表直接标注关键值，不依赖动效或渐变吸引视线
- **克制的颜色**：ECharts 默认配色即可，不要自定义彩虹色板；语义色仅用于告警状态
- **稳定的布局**：面板尺寸固定，加载/交互不导致布局抖动
- **功能性优先**：tooltip、dataZoom 等交互因为有用才加，不是为了"看起来高级"

### KPI 卡片

- 一行文字标签 + 一个格式化数值，够了
- 语义色通过左侧 3px 色条体现，不要整卡片变色
- 有时间对比时加一行小字变化值（↑/↓），不要彩色箭头图标

### 图表

- 使用 ECharts 默认主题配色，不注入自定义 color 数组（除非类别需要语义区分）
- 网格线、轴线保持默认浅灰即可
- 动画使用 ECharts 默认值（不指定 animationDuration/animationEasing）
- 图例在必要时才加（单系列不需要图例）

### 自检

生成后检查：
- 去掉所有装饰性 CSS 后，信息是否仍然完整可读？如果是，那些装饰就不该加
- 整体是否像 Grafana/Metabase 这类工具的输出？而不是 Dribbble 上的概念稿？
- 颜色数量是否 ≤ 5 种（不含灰阶）？

---

## 特殊场景处理

### 数据量过大
- > 1000 行：先在前50行验证逻辑，用户确认后全量执行
- > 10000 行：提醒用户处理可能需要较长时间
- > 100000 行：建议先采样分析，确认方案后再全量

### 多文件处理
- 用户提供多个文件时，先分别读取并比较结构
- 结构相同 → 建议纵向合并（concat）
- 有共同键列 → 建议横向关联（merge）
- 结构不同且无共同键 → 分别处理，不强行合并

### 编码问题
- CSV 打开乱码：用 chardet 检测编码，常见中文编码为 gbk/gb2312
- Excel 无此问题（内部使用 XML 编码）
- 输出 CSV 总是用 utf-8-sig（BOM），确保 Excel 正确打开

### 用户提供粘贴数据（非文件）
- 将粘贴的数据保存为临时 CSV 文件再处理
- 自动检测分隔符（逗号/制表符/空格）

---

## 环境与依赖

首次执行数据处理前，按以下顺序检测环境：

### 步骤1：检测 Python

运行 `python3 --version`（Mac/Linux）或 `python --version`（Windows）。

**如果 Python 不可用**，根据操作系统引导用户安装：

- **Mac**：系统自带 Python3，正常不会缺失。如确实没有：`brew install python3`
- **Windows（推荐 winget 一键安装）**：
  ```powershell
  winget install -e --id Python.Python.3.12
  ```
  安装后需要重启终端使 PATH 生效。
- **Windows（备选方案）**：
  - Microsoft Store 搜索 "Python 3.12" 直接安装
  - 或从 https://www.python.org/downloads/ 下载安装包，安装时**务必勾选 "Add python.exe to PATH"**

### 步骤2：检测 pip 依赖

```bash
python3 -c "import pandas, openpyxl, chardet" 2>/dev/null || pip3 install pandas openpyxl chardet
```

Windows 上使用：
```powershell
python -c "import pandas, openpyxl, chardet" 2>$null; if ($LASTEXITCODE -ne 0) { pip install pandas openpyxl chardet }
```

如果安装失败（权限问题），提示用户加 `--user` 参数：`pip install --user pandas openpyxl chardet`

### 注意

- chart_render.py 无外部依赖（仅用 Python 标准库），即使 pandas 未安装也能运行
- 环境检测只需首次执行一次，后续使用无需重复

---

## 资源索引

| 文档 | 用途 | 何时读取 |
|------|------|---------|
| `references/data-recipes.md` | pandas 常用代码模式 | 生成处理代码前 |
| `references/chart-selection.md` | 图表类型选择决策树 | 可视化场景(路径C) |
| `references/quality-checklist.md` | 数据质量评估标准 | 数据探索场景(路径A) |
| `references/output-standards.md` | 输出文件规范 | 写入文件前 |
| `scripts/chart_render.py` | ECharts渲染引擎 | 生成图表/看板时 |
