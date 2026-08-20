---
name: data-auto-analyzer
description: 通用数据自动分析 Skill。当用户上传 Excel（.xlsx/.xls）或 CSV 文件，或提到想分析数据、看报表、生成可视化报告、查看数据趋势时，必须使用此 Skill。自动识别所有列类型（日期、维度、数值指标），汇总全部指标，检测异常，生成包含交互式 ECharts 图表和可分页表格的 HTML 分析报告。适用于任何结构化表格数据：广告投放报表（巨量引擎、腾讯广告、Meta Ads、Google Ads 等）、销售数据、财务报表、运营指标、用户行为数据、电商订单、库存统计等。即使用户只是说"帮我看看这个表格""分析一下这个数据""这个 Excel 有什么规律"，也应触发此 Skill。
metadata:
  homepage: https://clawhub.ai/ming0429/data-auto-analyzer
  version: 2.0.0
  author: guojiaming
  tags:
    - data-analysis
    - analytics
    - excel
    - csv
    - 数据分析
    - 可视化
    - echarts
    - html
    - 报表分析
    - 趋势分析
  clawdbot:
    emoji: 📊
    requires:
      bins:
        - python3
      pip:
        - pandas
        - openpyxl
        - xlrd
        - jinja2
      env: []
install_source: official
install_method: download
skill_id: official_Bq10LiJk
enabled_at: 1787231020515
version: 1.0.0
name_zh: 数据自动分析
---

# 数据自动分析 Skill

分析用户上传的 Excel/CSV 数据文件，自动识别所有列，汇总指标，检测异常，生成**交互式 HTML 分析报告**（含可分页表格 + ECharts 图表），输出优化建议。适用于广告报表、销售数据、财务数据、运营指标等任何结构化表格。

## Setup

无需任何配置，开箱即用。支持 `.xlsx` / `.xls` / `.csv`，兼容 UTF-8 / GBK 编码。

## Usage

用户上传文件后，将分析脚本复制到工作目录并执行。**不要用 `-c` 内联方式运行**。

正确执行方式：
```bash
# 第一步：安装依赖
pip install pandas openpyxl xlrd jinja2 --break-system-packages -q

# 第二步：复制脚本到工作目录
cp /mnt/skills/user/data-auto-analyzer/scripts/analyze.py /home/claude/analyze.py

# 第三步：执行分析，生成 HTML 报告
python3 /home/claude/analyze.py --file /path/to/report.xlsx --out /mnt/user-data/outputs/data_report.html
```

## 分析脚本说明

脚本位于 `scripts/analyze.py`，执行后自动完成以下步骤：

1. **读取文件** — 自动识别 xlsx/xls/csv，自动尝试 utf-8/gbk 编码
2. **识别列类型** — 自动区分日期列、维度列（文字）、指标列（数值），不预设列名
3. **汇总指标** — 所有数值列的合计、均值、最大值、最小值
4. **分组分析** — 按每个维度列分组汇总，自动排序
5. **异常检测** — 均值 ±2 倍标准差自动标记异常行
6. **生成交互式 HTML 报告** — 单个 HTML 文件，内嵌 ECharts，包含：
   - 数据概览卡片（总行数、列数、日期范围等）
   - 核心指标汇总卡片
   - 异常检测结果
   - 优化建议
   - 可分页、可排序的数据表格（每页 20 行）
   - ECharts 交互图表：指标总量柱状图、趋势折线图、维度占比饼图、维度对比横向柱状图、相关性热力图
7. **输出建议** — 基于数据给出具体优化方向

## 输出

单个 HTML 文件，浏览器直接打开即可查看，包含完整分析报告和交互图表。

## Notes

- 必须保存为 `.py` 文件执行，不支持 `python3 -c` 内联模式
- 完全动态识别列名，表头是什么分析什么，一列不漏
- 数据不外传，完全本地处理
- 编码自动识别，兼容国内广告平台导出文件
- 生成的 HTML 报告内嵌所有依赖（ECharts CDN），无需额外安装

## Examples

分析 Excel 报表：
```bash
python3 analyze.py --file ~/Downloads/report.xlsx --out /mnt/user-data/outputs/data_report.html
```

分析 CSV 数据：
```bash
python3 analyze.py --file ~/Downloads/data.csv --out /mnt/user-data/outputs/data_report.html
```
