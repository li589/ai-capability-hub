# 估值公式与异常值处理

## 一、经营指标公式

```excel
净利率    = 净利润 / 营收
ROE       = 净利润 / 净资产（TDX 可直接返回）
毛利率    = 毛利 / 营收
FCF利润率 = FCF / 营收
PEG       = PE / 预测增速(%)
EBITDA利润率 = EBITDA / 营收
资产负债率 = 总负债 / 总资产
经营杠杆  = 营收增速 / EBIT增速
```

确保分子分母取自同一报告期。

## 二、估值倍数公式

```excel
PE(TTM)  = 市值 / 归母净利润TTM（TDX 优先）
PB       = 市值 / 净资产（TDX 优先）
PS(TTM)  = 市值 / 营收TTM
PEG      = PE / 预测增速(%)
EV/EBITDA = 企业价值 / EBITDA
股息率    = 每股股利 / 股价
```

### EV 计算

```excel
EV = 市值 + 有息负债 - 货币资金及等价物
有息负债 = 短期借款 + 长期借款 + 应付债券 + 一年内到期非流动负债
```

批注中注明有息负债构成项，禁止用"总负债"替代。

## 三、统计块规则

在公司数据之后留一空行，放置统计公式：

```excel
=MAX(range)  =QUARTILE(range,3)  =MEDIAN(range)  =QUARTILE(range,1)  =MIN(range)
```

需统计列：营收增速%、净利率%、ROE%、PE(TTM)、PB、PEG、股息率%；数据可得时加毛利率%、EV/EBITDA。
不统计列：营收、净利润、市值、目标价、预测 EPS（绝对值不可比）。

| 样本量 | 统计方法 |
|--------|----------|
| n < 4 | 仅 MAX / MEDIAN / MIN；禁止四分位 |
| 4 ≤ n ≤ 8 | 完整五项（MAX/Q3/MEDIAN/Q1/MIN） |
| n > 8 | 五项 + STDEV.P + AVERAGE |

禁止增加额外标题行。

## 四、常用公式速查

```excel
// 容错
=IF(B7>0, C7/B7, "N/A")
=IFERROR(C7/D7, 0)
// 比率
净利率=净利润/营收  ROE=净利润/净资产  资产周转率=营收/总资产
// 估值
PE=市值/归母净利润  PB=市值/净资产  PS=市值/营收
PEG=PE/预测增速(%)  EV/EBITDA=企业价值/EBITDA  股息率=每股股利/股价
```

## 五、通用 openpyxl 公式模板

```python
# 估值倍数
cell.value = f'=IFERROR({col_市值}{row}/{col_净利润}{row},"N/A")'   # PE
cell.value = f"={col_市值}{row}/{col_净资产}{row}"                   # PB
cell.value = f"={col_市值}{row}/{col_营收}{row}"                     # PS
cell.value = f"={col_PE}{row}/({col_增速}{row}*100)"                # PEG
cell.value = f"=({col_市值}{row}+{col_有息负债}{row}-{col_现金}{row})/{col_EBITDA}{row}"  # EV/EBITDA

# 经营指标
cell.value = f"={col_净利润}{row}/{col_营收}{row}"                   # 净利率
cell.value = f"={col_毛利}{row}/{col_营收}{row}"                     # 毛利率
cell.value = f"={col_净利润}{row}/{col_净资产}{row}"                 # ROE
cell.value = f"=({col_营收本期}{row}-{col_营收上期}{row})/{col_营收上期}{row}"  # 营收增速

# 容错包裹（所有比率必须套用）
cell.value = f'=IF({col_净利润}{row}>0,{col_市值}{row}/{col_净利润}{row},"亏损")'
```

列变量须替换为真实列字母。TDX 直接返回的指标优先硬编码输入。

### 行业专用公式索引

| 行业 | 核心专用公式 | 详细模板 |
|------|-------------|----------|
| 银行/金融 | PB-ROE 回归、净息差、不良率、拨备覆盖率 | industry-metrics.md §银行 |
| 消费/白酒 | 吨价、经销商回款、合同负债覆盖率 | industry-metrics.md §消费 |
| 地产/物业 | NAV 折价率、净负债率、土储倍数 | industry-metrics.md §地产 |
| 互联网/科技 | ARPU、LTV/CAC、经调整净利润 | industry-metrics.md §互联网 |
| 军工 | 订单保障倍数、预付款变动率 | industry-metrics.md §军工 |
| 新能源/制造 | 单瓦利润、产能利用率、资本开支强度 | industry-metrics.md §新能源 |
| 环保/公用 | 单位处理成本、产能投产率 | industry-metrics.md §环保 |
| 汽车/零部件 | 单车利润、市占率、研发强度 | industry-metrics.md §汽车 |
| 传媒/游戏 | ARPPU、付费率、用户获取成本 | industry-metrics.md §传媒 |

禁止跨行业混用专用公式。

## 六、异常值检测与处理

### 检测规则

**统计法**（n ≥ 5）：超出 `Median ± 2σ` 标注为统计异常。n < 5 禁止使用统计法，改用业务法。

**业务法**：

| 条件 | 判定 | 处理 |
|------|------|------|
| PE < 0（亏损） | 异常 | 排除出统计，标注"亏损" |
| PE > 100x 且营收增速 < 30% | 异常 | 排除，不参与中位数 |
| PE > 200x | 极端异常 | 强制排除 |
| PB < 0 | 异常 | 排除，标注"资不抵债" |
| ROE > 40%（非金融） | 可疑 | 保留并标注，核实低净资产 |
| 毛利率 > 净利率 + 50pp | 可疑 | 检查费用结构 |
| 营收增速 > 300% | 可疑 | 核实并购/基数效应 |

统计法与业务法同时触发时，以业务法为准。

### 处理方式

| 方式 | 场景 | 操作 |
|------|------|------|
| 排除 | PE 为负、资不抵债、PE>200x | 移出统计范围，灰色字体展示 |
| 标注 | 并购/低基数等可解释异常 | 保留在统计范围，加批注 |
| 截尾 | n>8 且两端各有极端值 | 用 `=TRIMMEAN(range,0.2)` |

### 批注格式

```
[OUTLIER: <分类>] <说明>
```

分类枚举：LOSS / EXTREME_HIGH / EXTREME_LOW / BASE_EFFECT / M&A / NEGATIVE_EQUITY / DATA_MISSING

### 排除后公式调整

```excel
=MEDIAN(B7:B9,B11:B12)           // 跳过被排除行
=AGGREGATE(12, 5, B7:B12, 1)    // MEDIAN 忽略错误值
```

禁止排除异常值后不调整统计公式范围。
