---
name: 财务数据规范
version: 1.0.0
description: "Shared spec for financial data sourcing, cross-validation and exact calculation. Internal knowledge base referenced by all research skills. Bundles Python tools for precise valuation math and report auditing."
description_zh: "财务数据获取、交叉验证与精确计算的共享规范。作为内部知识库被所有研究技能引用，内置精确估值计算与报告审计的 Python 工具。"
user-invocable: false
---

# 财务数据获取与交叉验证规范（内部知识库）

本规范适用于套件内所有涉及企业财务数据的研究。**每个关键数据必须来自两个独立来源，误差>1%须标记。** 其它技能在需要取数、验算、审计时引用本技能。

> 客观性原则（最高优先级，所有技能通用）：所有分析必须基于事实和数据，严禁主观臆断；严格区分"事实"与"观点"；不预设看多/看空；对不确定的事诚实说"不确定"或"数据不足"，不要用推测填充确定性；每个核心判断附反面论据。

---

## 一、数据源优先级

### 美股（PDD、腾讯ADR、网易ADR等）
| 优先级 | 来源 | 获取方式 |
|--------|------|---------|
| 1（主） | macrotrends.net/stocks/charts/{ticker} | 直接访问，无需注册 |
| 2（副） | stockanalysis.com/stocks/{ticker}/financials | 直接访问，无需注册 |
| 原始一手 | SEC EDGAR（sec.gov） | 10-K / 10-Q 原文 |

### 港股（腾讯0700、网易9999、美团3690等）
| 优先级 | 来源 | 获取方式 |
|--------|------|---------|
| 1（主） | aastocks.com | 直接访问 |
| 2（副） | macrotrends（ADR代码，腾讯TCEHY/网易NTES） | 直接访问 |
| 原始一手 | HKEX 披露易（hkexnews.hk） | 年报PDF |

### A股（三七互娱、吉比特等）
| 优先级 | 来源 | 获取方式 |
|--------|------|---------|
| 1（主） | 东方财富（eastmoney.com） | 搜股票代码 → 财务报表 |
| 2（副） | 巨潮资讯（cninfo.com.cn） | 原始年报/季报PDF |

---

## 二、执行规范

### 第一步：获取数据
对每个财务指标（收入、净利润、毛利率、经营现金流、资产负债率等），分别从来源1和来源2取数。

### 第二步：误差计算与标记
```
误差率 = |来源1数值 - 来源2数值| / 来源1数值 × 100%
```
| 误差 | 处理方式 |
|------|---------|
| ≤ 1% | ✅ 一致，取来源1数值，标注两个来源 |
| 1% ~ 5% | ⚠️ 标记"数据存在差异"，注明两个数值和可能原因（汇率/会计口径） |
| > 5% | ❌ 标记"数据存在重大差异"，必须查原始财报核实，不得直接使用 |

### 第三步：数据呈现格式
```
收入：1,239亿元 ✅
  - macrotrends: 1,241亿元
  - stockanalysis: 1,237亿元
  - 误差: 0.3%
```
差异示例：
```
净利润：245亿元 ⚠️ 数据存在差异
  - macrotrends: 245亿元（GAAP）
  - stockanalysis: 278亿元（Non-GAAP）
  - 误差: 13.5% — 原因：会计口径不同（GAAP vs Non-GAAP）
```

---

## 三、常见差异原因（不一定是数据错误）
| 原因 | 说明 |
|------|------|
| GAAP vs Non-GAAP | 最常见，尤其利润类数据 |
| 汇率换算 | 港币/人民币/美元换算时间点不同 |
| 财年定义 | 自然年 vs 财年（如苹果财年10月结束） |
| 合并口径 | 是否含少数股东权益 |
| 数据更新滞后 | 某平台尚未更新最新一期财报 |

---

## 四、特别规则
1. **未上市公司**（米哈游、莉莉丝等）：只有一手数据来源时，数据前标记 `[估计]`，不执行交叉验证
2. **季度 vs 年度**：优先用年度数据做交叉验证，季度数据部分来源可能滞后
3. **原始财报优先**：若两个来源均与原始财报不符，以原始财报为准，标记来源错误

---

## 五、股价与复权（历史序列必读）
| 口径 | 含义 | 用途 |
|------|------|------|
| 不复权 | 实际成交价，除权除息日跳空 | 仅用于"当前时点"快照 |
| 前复权 | 以最新价为基准回调历史价 | 历史股价对比、N年涨幅、历史PE band |
| 后复权 | 以上市首日为基准前推 | 计算历史总回报/年化收益 |

规则：涉及历史价格统一用前复权且同一分析内不得混用；当前市值/PE 用当前实际股价×当前总股本；跨越拆股的每股指标必须复权还原后再同比；总回报需计入分红。

---

## 六、内置精确计算与审计工具（Python，零外部依赖）

本技能 `references/tools/` 目录下捆绑了 AI Berkshire 的核心 Python 工具。**所有涉及计算的数据必须通过工具验算，禁止心算。**

> 运行方式：这些工具随插件安装在本技能的 `references/tools/` 目录下。运行前先用 Bash 定位本技能目录（插件通常安装在 `~/.qoderwork/plugins-custom/` 或 `~/.qoderworkcn/plugins-custom/` 下），把 `{TOOLS}` 替换为该 `references/tools` 的绝对路径。例如先执行：
> ```bash
> TOOLS=$(find ~ -type d -path '*value-investing-suite*/skills/财务数据规范/references/tools' 2>/dev/null | head -1); echo "$TOOLS"
> ```
> 之后用 `python3 "$TOOLS/financial_rigor.py" ...` 调用。工具需要 Python ≥ 3.7。

### financial_rigor.py — 精确金融计算（decimal，非浮点）
```bash
# 市值验算：股价 × 总股本 对比报告市值
python3 "$TOOLS/financial_rigor.py" verify-market-cap \
  --price {股价} --shares {总股本} --reported {报告市值} --currency {币种}

# 估值指标验算（PE/PB/ROE/FCF Yield/股息率）
python3 "$TOOLS/financial_rigor.py" verify-valuation \
  --price {股价} --eps {EPS} --bvps {每股净资产} --fcf-per-share {每股FCF} --dividend {每股股息}

# 关键数据多源交叉验证
python3 "$TOOLS/financial_rigor.py" cross-validate \
  --field {字段名} --values '{"来源1": 数值, "来源2": 数值}' --unit {单位}

# 三情景估值（乐观/中性/悲观）
python3 "$TOOLS/financial_rigor.py" three-scenario \
  --price {股价} --eps {EPS} --shares {总股本亿} \
  --growth {乐观增速} {中性增速} {悲观增速} \
  --pe {乐观PE} {中性PE} {悲观PE} --years 3 --currency {币种}

# Benford 异常检测 / 精确算式
python3 "$TOOLS/financial_rigor.py" benford --values '[1234, 2345, ...]'
python3 "$TOOLS/financial_rigor.py" calc --expr '{精确算式}'
```

### report_audit.py — 报告数据抽检（准出流程）
```bash
# Step 1 提取抽检清单（15% 随机抽样）
python3 "$TOOLS/report_audit.py" extract --report <报告文件路径>
# Step 2 对清单每项按本规范从可靠信源取数，填入 fetched_value/fetched_source 等字段
# Step 3 输出准出/打回判决
python3 "$TOOLS/report_audit.py" verdict --results '<填好的JSON>' --report <报告文件名>
```
- 【准出】所有抽检点偏差 ≤ 1% → 报告可发布
- 【打回】任意点偏差 > 1% → 修正对应数据后重新抽检，直到准出

### 其它工具
- `stock_screener.py`：批量选股/去劣筛选辅助
- `xueqiu_scraper.py`：抓取雪球大V发言（段永平 user_id `1247347556`）
- `ashare_data.py`：A股行情数据
- `morningstar_fair_value.py`：晨星公允价值参考

若运行环境无 Python 或工具不可用，退回手工计算并在报告中**明确标注"未经工具验算，请自行核实"**。

---

## 七、快速索引
| 场景 | 主要来源 | 备用来源 |
|------|---------|---------|
| PDD / 拼多多 | macrotrends.net/stocks/charts/PDD | stockanalysis.com/stocks/pdd |
| 腾讯 | macrotrends（TCEHY） | aastocks（0700.HK） |
| 网易 | macrotrends（NTES） | aastocks（9999.HK） |
| 三七互娱 | eastmoney（002555） | cninfo.com.cn |
| A股通用 | 东方财富 | 巨潮资讯 |
