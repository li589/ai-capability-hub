---
name: stock-researcher
version: 9.3.0
description: |
  全球智能投研工具 v9.3 — 历史形态匹配预测 + 基金/期货量化增强 + 深度板块 + 深度指数 + 体制感知预测，全资产量化 + 真实数据源。
  覆盖 12 个全球市场，支持股票/基金/指数/板块/商品/期货/债券/货币基金/可转债，
  零依赖核心（纯 stdlib）。

  🆕 v9.3 量化预测增强：
    - 历史形态匹配预测：检索自身历史相似走势窗口推断未来涨跌（股票/基金/期货通用，纯离线确定性）+ quant_analyze_asset 接线
    - 基金：尾部风险（偏度/峰度/VaR）/回撤恢复期/滚动稳定性/Treynor + NAV 短期预测
    - 期货：波动率置信区间预测/ATR 风险预算仓位/展期收益估算

  🆕 v9.0 三大支柱：
    - 深度板块：RPS 相对强度百分位排名、板块宽度（%在MA20/50/200、新高新低、
      Zweig 推动、背离）、横截面离散度、主题概念板块（AI算力/人形机器人等）、
      经典轮动周期阶段（美林时钟）
    - 深度指数：市场体制（牛/熊/震荡+概率）、波动率体制、市场结构（高低点/关键位）、
      市场内含（涨跌家数/McClellan）、真实指数 PE/PB 历史分位
    - 体制感知预测：体制条件化权重（熊市动量折扣）、信号共识度、命名宏观情景
      概率加权、预测置信度校准；regime="auto" 一键开启

  数据源：腾讯 + 东方财富（免费无 Key）+ akshare（可选）。测试 527。

  触发词：股票、基金、行情、分析、预测、涨跌、指数、板块、商品、黄金、债券、可转债、
  货币基金、全球市场、量化、技术指标、组合优化、风险平价、夏普、回测、价值投资、
  蒙特卡洛、VaR、Sharpe、涨跌预测、量化分析、全资产、因子库、策略回测、数据质量、
  相对强度、RPS、板块宽度、轮动周期、市场体制、牛熊、波动率体制、市场内含、
  McClellan、指数估值、PE分位、情景分析、软着陆、硬着陆、预测校准、自上而下、
  主题板块、AI算力、人形机器人、低空经济、形态匹配、净值预测、仓位建议、展期收益
auto_trigger:
  keywords: [股票, 基金, 行情, 分析, 预测, 涨跌, 指数, 板块, 商品, 黄金, 债券, 可转债,
    货币基金, 全球市场, 量化, 技术指标, 组合优化, 风险平价, 夏普, 回测, 价值投资,
    蒙特卡洛, VaR, Sharpe, 涨跌预测, 量化分析, 全资产, 因子库, 策略回测, 数据质量,
    相对强度, RPS, 板块宽度, 轮动周期, 市场体制, 牛熊, 波动率, 市场内含, 指数估值,
    PE分位, 情景, 软着陆, 硬着陆, 校准, 自上而下, 主题板块, AI算力, 人形机器人]
  patterns:
    - "(分析|预测|查询|筛选|看下|看看).*(股票|基金|涨跌|行情|指数|板块|黄金|原油|债券|可转债)"
    - "(技术|指标|量化|基本面).*分析"
    - "(看涨|看跌|买入|卖出).*信号"
    - "(推荐|建议|排名).*(板块|个股|基金|投资|指数)"
    - "(护城河|DCF|内在价值|安全边际|财务健康).*(分析|评估)"
    - "(舆情|情绪|新闻|论坛).*(监控|分析|预警)"
    - "(港股|美股|日经|标普|纳斯达克|恒生|道琼斯).*(分析|预测|筛选|走势)"
    - "(全球|跨市场|海外).*(指数|市场|分析)"
    - "(黄金|原油|商品|债券).*(分析|预测|走势|期货)"
    - "(政策|监管|宏观).*(解读|分析|影响)"
    - "(未来|下个|短期).*(走势|趋势|涨跌)"
    - "(板块|行业).*(轮动|排名|推荐|趋势)"
    - "(相对强度|RPS|宽度|离散度|强弱).*(板块|行业)"
    - "(市场体制|牛熊|震荡市).*(判断|分析|分类|预测)"
    - "(波动率|波动).*(体制|扩张|压缩|高波动)"
    - "(情景|软着陆|硬着陆|衰退|通胀).*(分析|推演|预测)"
    - "(置信度|校准|可靠性).*(预测|评分)"
    - "(自上而下|市场全景|TopDown).*(分析|报告)"
    - "(五维|资金面|财经信息|社会舆情).*(分析|综合|评估)"
    - "(推演|涨跌预测|方向预测).*(股票|基金|期货|指数)"
    - "(PE|PB|估值).*(分位|历史|真实|估算)"
    - "(数据|财务|报表).*(质量|时效|准确|过时|新鲜)"
    - "(严格|宽松).*(模式|分析|校验)"
    - "(start_date|end_date|日期|时间).*(区间|范围|参数)"
    - "(组合|仓位|资产配置).*(优化|风险平价|马科维茨|夏普)"
    - "(货币基金|货基|余额宝类).*(评分|分析|收益)"
    - "(可转债|转债).*(分析|评分|转股|溢价)"
---

# 股票研究员 v9.0 — 深度板块 + 深度指数 + 体制感知预测

> 纯 Python 标准库核心，零 pip 依赖。覆盖 12 个全球市场 + 股票/基金/指数/债券/商品/期货/货币基金/可转债。
> 数据源：腾讯 + 东方财富（免费无 Key）+ akshare（可选增强，未装自动降级）。

## ⚠️ 支持范围与限制（重要，请先读）

### 支持的市场

| 市场 | 代码格式 | 示例 | 数据源 |
|------|---------|------|--------|
| **A股** | 6 位数字 / `cn:` 前缀 | `600519` `cn:600519` | 腾讯/东财 |
| **港股** | `hk:` 前缀 / `.HK` 后缀 | `hk:00700` `00700.HK` | 腾讯 |
| **美股** | `us:` 前缀 / `.US` 后缀 | `us:AAPL` `AAPL.US` | 腾讯/东财 |
| **全球指数** | `idx:` 前缀 | `idx:N225` `idx:SPX` `idx:上证指数` | 腾讯 |
| **商品期货** | `品种:交易所` | `gold:comex` `crude:wti` | 腾讯 |
| **基金/ETF** | 6 位数字 / `fund:` 前缀 | `110022` `fund:510300` | 天天基金/akshare |
| **可转债** | 6 位数字（11/12 开头自动识别） | `128046` | 东财 |
| **债券** | 代码 / `bond:` 前缀 | `bond:国债` | akshare |

### 限制条件

| 限制 | 说明 |
|------|------|
| 🔴 **需国内直连** | 数据源为腾讯/东财国内接口，**开启代理反而会失败**（会走海外 IP 被拒） |
| 🔴 **非实时数据** | 腾讯/东财接口延迟约 3~5 秒，非交易时段返回收盘价 |
| 🟡 **评分≠盈利预测** | 预测评分表示历史上相似条件下约 X% 概率上涨，**不保证未来** |
| 🟡 **不构成投资建议** | 仅供学习参考，买卖决策自行负责 |
| 🟡 **akshare 可选** | 部分高级功能（基金净值/债券/可转债/宏观）需要 `pip install akshare`，未装自动降级 |

## ⚡ 快速上手

```bash
# 离线自检 / 单股预测 / 批量多市场
python scripts/stock_predict.py --test
python scripts/stock_predict.py 600519
python scripts/stock_predict.py "600519,hk:00700,us:AAPL" --json

# 统一全资产量化分析（任意金融产品）
python -c "from stock_researcher import quant_analyze_asset; print(quant_analyze_asset('600519'))"

# v9.0 深度板块/指数/体制感知预测
python scripts/stock_predict.py --sector-ranking cn      # 板块RPS相对强度排名
python scripts/stock_predict.py --index-regime sh000001  # 市场体制（牛/熊/震荡）
python scripts/stock_predict.py --scenario               # 宏观情景概率加权
python scripts/stock_predict.py --topdown cn             # 自上而下市场全景
```

### v9.0 深度分析速查

```python
# 板块：相对强度 + 宽度 + 离散度 + 主题 + 轮动周期
from stock_researcher import rps_ranking, analyze_breadth, analyze_dispersion, \
    list_themes, analyze_theme, detect_cycle_stage
ranking = rps_ranking("cn")                 # RPS 百分位排名（真实成分股 vs 沪深300）
b = analyze_breadth("电子")                  # 宽度：%在MA20/50/200、Zweig推动、背离
d = analyze_dispersion("电子")               # 离散度：横截面σ、龙头-落后差、齐涨/分化
themes = list_themes("cn")                  # AI算力/人形机器人/低空经济/固态电池...
t = analyze_theme("AI算力", "cn")            # 主题板块强度+宽度+离散度+资金
stage = detect_cycle_stage("cn")            # 美林时钟：早/中/晚周期/衰退概率

# 指数：体制 + 波动率 + 结构 + 内含 + 估值分位
from stock_researcher import classify_market_regime, analyze_volatility, \
    analyze_market_structure, analyze_market_internals, classify_index_valuation
reg = classify_market_regime("sh000001")    # 牛/熊/震荡 + 概率
vol = analyze_volatility("sh000001")        # 波动率体制（低/扩张/高/压缩）
ms = analyze_market_structure("sh000001")   # 高低点结构 + 阻力/支撑
mi = analyze_market_internals("sh000300")   # 涨跌家数 + McClellan（混合数据策略）
iv = classify_index_valuation("sh000300")   # 真实 PE 历史分位（多级降级不编造）

# 体制感知预测（regime="auto" 一键开启；默认 None 与 v8.0 行为一致）
from stock_researcher.fusion.multi_horizon_forecaster import MultiHorizonForecaster
fc = MultiHorizonForecaster().forecast_stock("600519", regime="auto")
print(fc.regime, fc.horizons["1M"].regime, fc.horizons["1M"].consensus)

# 宏观情景 + 校准
from stock_researcher import analyze_scenarios, calibrate_confidence
rep = analyze_scenarios(base_return=0.08, base_vol=0.20)   # 6情景概率加权+尾部
adj = calibrate_confidence(0.7, horizon="1M")               # 历史校准后置信度

# 自上而下全景（三支柱一条线）
from stock_researcher import build_topdown
print(build_topdown("cn").summary)

# v9.2 定期报告解读（年报/半年报/季报 同比环比 + 亮点风险 + 中文报告）
from stock_researcher import interpret_report, format_report
rep = interpret_report("600519", period="2024")     # "2024"=年报；"2025Q3"/"2025H1"/"2024-06-30" 亦可
print(rep.verdict, rep.metrics["revenue_yoy"], rep.metrics["net_profit_yoy"])
print(format_report(rep))

# v9.3 历史形态匹配预测 + 基金 NAV 预测 + 期货置信区间预测
from stock_researcher import quick_pattern_forecast
pf = quick_pattern_forecast(prices, horizon=5)      # 形态重演：预期涨跌+上涨概率+置信度
from stock_researcher.funds.fund_quant_analyzer import FundQuantAnalyzer
nav_fc = FundQuantAnalyzer().forecast_nav(nav, 5)   # 基金净值 5 日预测 + 80% 区间
from stock_researcher.quantitative.futures_analyzer import FuturesAnalyzer
fut = FuturesAnalyzer().predict_futures("IF9999", prices)  # 含预测区间+置信度+仓位建议
```

## 🚀 Agent 执行指南（先探测环境，再分析，最后按模板输出）

### Step 1: 运行时检测（不要假设环境，先探测再决策）

```bash
# ① Python 解释器（Windows 优先用 py launcher 定位）
python --version 2>/dev/null || py --version 2>/dev/null || echo "NO_PYTHON"

# ② 可选依赖探测（决定降级路径）
python -c "import akshare" 2>/dev/null && echo "AKSHARE_OK" || echo "AKSHARE_MISSING"
python -c "import numpy, sklearn" 2>/dev/null && echo "ML_OK" || echo "ML_MISSING"

# ③ 数据源连通性（腾讯/东财需国内直连，开代理会失败）
python scripts/stock_predict.py --test
```

| 检测结果 | 决策 |
|---|---|
| `NO_PYTHON` | Windows 用 `py -3.11`；Linux/macOS 用 `python3`；`py --list` 查看可用版本 |
| `AKSHARE_MISSING` | 基金净值/债券/可转债/宏观走降级路径（自动跳过，不崩溃）；其余功能不受影响 |
| `ML_MISSING` | 短期(1d/3d/5d) ML 概率叠加自动跳过（no-op），主预测链路仍可用 |
| `--test` 失败/超时 | 疑似开了代理/VPN → 提示用户关闭代理后重试；或用纯离线函数（不联网的量化/回测/组合优化） |

### Step 2: 按需求选择入口（参数默认值见下表）

| 需求 | 入口 | 命令/调用 |
|---|---|---|
| 单股/多市场预测 | CLI | `python scripts/stock_predict.py 600519` |
| 全资产量化 | `quant_analyze_asset(code)` | 股票/基金/指数/债券/商品/可转债统一收口 |
| 板块深度 | `rps_ranking`/`analyze_breadth`/`analyze_dispersion`/`analyze_theme` | v9.0 深度板块 |
| 指数深度 | `classify_market_regime`/`analyze_volatility`/`analyze_market_internals`/`classify_index_valuation` | v9.0 深度指数 |
| 价值投资 | `ValueInvestingDecision().analyze(code)` | DCF/护城河/财务健康/管理层/行业 |
| 基金评分 | `score_fund_v3(code)` | 基金十维评分 |
| 组合优化/回测 | `allocate_portfolio`/`BacktestEngine` | 纯 stdlib MVO/风险平价/VaR |
| 定期报告解读 | `interpret_report(code, period)` | 年报/半年报/季报 同比环比+亮点风险（v9.2） |
| 历史形态预测 | `quick_pattern_forecast(prices)` | 形态匹配推断涨跌，股票/基金/期货通用（v9.3） |

> 批量/快速场景优先加 `--simple --quick`（跳过蒙特卡洛 + 全球风险偏好，提速约 60%）。

### 参数默认值

| 参数 | 默认值 | 说明 |
|---|---|---|
| `market` | `cn` | 可选 cn/hk/us；港股美股需 `hk:`/`us:` 前缀 |
| `asset_type` | 自动识别 | 可转债 11/12 开头、6 位数字=基金/股票、`gold`=商品 |
| `top_n` | 20（筛选）/ 5（板块） | 返回前 N 条 |
| `horizon` | 1d~6M 全周期 | `MultiHorizonForecaster` 默认输出 1d/3d/5d/1M/3M/6M |
| `regime` | `None`（=v8.0 行为） | 传 `"auto"` 开启体制感知预测（熊市动量折扣+共识度校准） |
| `strict` | `False` | `True` 拒绝估算值（estimated）只保留 actual/derived |
| `distribution` | `normal` | 蒙特卡洛可选 `t`（肥尾）+ `use_jumps=True`（跳跃扩散） |
| `track` | `False` | `True` 写入 PredictionTracker（进化闭环） |
| 缓存 TTL | 300 秒 | `config/settings.json` 的 `cache.ttl` |

### Step 3: 输出报告（结构化模板，编号分节）

每次分析按以下模板输出，数据缺失时如实标注，不编造：

1. **标的概览** — 代码 / 名称 / 市场 / 最新价 / 涨跌幅 / 数据时效（`data_freshness`）
2. **核心指标** — 评分、方向、置信度、关键量化指标（Sharpe/最大回撤/PE 分位等）
3. **多周期预测** — 1d/5d/1M/3M/6M 方向 + 概率 + 共识度（`regime` 开启时附体制标签）
4. **风险提示** — VaR/最大回撤/情景尾部风险 + 数据质量标记（actual/derived/estimated/unavailable）
5. **结论** — 一句话结论 + 免责声明（仅供学习参考，不构成投资建议）

## 核心能力总览

| 能力 | 入口 | 说明 |
|---|---|---|
| **统一全资产量化** 🆕 | `quant_analyze_asset(code)` | 一个 API 量化股票/基金/指数/债券/商品/可转债，输出指标+场景+预测+专属分析 |
| **组合优化** 🆕 | `allocate_portfolio` / `mean_variance_optimize` | MVO（Frank-Wolfe）/ 最大Sharpe / 风险平价 / 组合 VaR-ES，纯 stdlib |
| **蒙特卡洛增强** 🆕 | `quick_scenario_forecast(..., distribution='t', use_jumps=True)` | 跳跃扩散 + 肥尾 t 分布（默认保持 GBM） |
| **ML 预测叠加** 🆕 | `MultiHorizonForecaster.forecast_stock(track=True)` | 短期(1d/3d/5d) ML 概率叠加 + 进化闭环记录 |
| **债券量化** 🆕 | `analyze_bond` / `bond_price` | 定价/久期/凸性/YTM/信用利差/收益率曲线形态 |
| **货币基金** 🆕 | `MoneyFundAnalyzer` | 7 日年化水平+稳定性+规模评分 |
| **可转债** 🆕 | `ConvertibleBondAnalyzer` | 转股价值/溢价率/双低指数/股性/强赎 |
| **板块相对强度 RPS** 🆕 | `SectorRelativeStrength` / `rps_ranking(market)` | 成分股构造板块代理指数 → 相对基准 5/20/60/120d RS + Mansfield RPS 百分位排名 + RS 趋势 |
| **板块宽度** 🆕 | `SectorBreadth` / `analyze_breadth(sector)` | %在MA20/50/200之上、新高新低、Zweig 宽度推动、价格-宽度背离、健康度 |
| **板块离散度** 🆕 | `SectorDispersion` / `analyze_dispersion(sector)` | 横截面σ、龙头-落后差、集中度、偏度、齐涨/齐跌/分化 |
| **主题概念板块** 🆕 | `list_themes` / `analyze_theme` / `rank_themes` | AI算力/人形机器人/低空经济/固态电池/氢能/创新药等跨行业概念（cn/hk/us） |
| **轮动周期阶段** 🆕 | `RotationCycleDetector` / `detect_cycle_stage` | 美林时钟：早/中/晚周期/衰退概率 + 受益/回避板块 |
| **市场体制分类** 🆕 | `MarketRegimeClassifier` / `classify_market_regime(code)` | 牛/熊/震荡 + 概率（MA200斜率+回撤+52周位置），体制切换信号 |
| **波动率体制** 🆕 | `VolatilityRegimeAnalyzer` | 20/60d 年化已实现波动、低/扩张/高/压缩标签、vol-of-vol、历史分位 |
| **市场结构** 🆕 | `MarketStructureAnalyzer` | 摆动高低点、HH-HL趋势结构、阻力/支撑关键位、破位信号、ATR |
| **市场内含** 🆕 | `MarketInternalsAnalyzer` | 涨跌家数、新高新低、McClellan 震荡子、宽度超买超卖（混合数据策略） |
| **指数估值分位** 🆕 | `IndexValuation` / `classify_index_valuation(code)` | 指数级 PE/PB 真实历史分位（多级降级，无分位不编造） |
| **体制感知预测** 🆕 | `MultiHorizonForecaster.forecast_stock(regime="auto")` | 体制条件化权重 + 熊市动量折扣 + 信号共识度置信调整 |
| **宏观情景** 🆕 | `MacroScenarioEngine` / `analyze_scenarios` | 6 命名情景（软着陆/硬着陆/通胀/地缘/刺激/衰退）概率加权 + 尾部 VaR |
| **预测校准** 🆕 | `PredictionCalibrator` / `calibrate_confidence` | 历史命中率分桶可靠性曲线 + Brier + 保序回归置信度校准 |
| **自上而下全景** 🆕 | `TopDownReport` / `build_topdown(market)` | 宏观体制→受益板块(RPS)→指数健康→仓位倾向+风险提示，三支柱串成一条 |
| **定期报告解读** 🆕 | `interpret_report(code, period)` / `FinancialReportInterpreter` | 年报/半年报/季报 同比(YoY)/环比(QoQ) + 业绩亮点/风险（增收不增利/经营杠杆/盈利质量/杠杆变化）+ 中文解读报告 |
| **历史形态匹配预测** 🆕 | `quick_pattern_forecast` / `HistoricalPatternPredictor` | 检索历史相似形态窗口 → 预期涨跌/上涨概率/分位区间/置信度，股票/基金/期货通用，纯离线 |
| **基金量化增强** 🆕 | `FundQuantAnalyzer` | 新增偏度/峰度/VaR/回撤恢复期/滚动稳定性/Treynor + `forecast_nav` NAV 短期预测 |
| **期货量化增强** 🆕 | `FuturesAnalyzer` | 置信区间预测 + 波动率预测（扩张/压缩）+ ATR 风险预算仓位 + 展期收益估算 |
| 多周期涨跌预测 | `MultiHorizonForecaster` | 1d~6M 十维信号融合（技术/资金/政策/舆情/宏观等） |
| 因子库 | `FactorLibrary` / `EnhancedFactorLibrary` | 5 类基础因子 + v7.6 四因子（动量反转/资金流/波动率/日历） |
| 策略回测 | `Backtester` / `BacktestEngine` | RSI/MACD/双均线 P&L 模拟 + 漫步前向命中率 |
| 价值投资 | `ValueInvestingDecision` | DCF/护城河/财务健康/管理层/行业五维 |
| 五维聚合 | `FiveDimAnalyzer` | 政策+资金+财经+论坛+舆情 |

## 数据层（v8.0 真实数据）

| 修复/增强 | 说明 |
|---|---|
| **PE/PB 真实历史分位** 🆕 | `fundamental.get_valuation` 拉 250 期历史 → `analyzer` 真实分位（此前 pageSize=1 死代码） |
| **财务时效** 🆕 | 补 `report_date` → `data_freshness` 校验生效（此前恒 unknown） |
| **资金流真实化** 🆕 | 东财 f62 主力净流入（此前腾讯硬编码 0 / 编造趋势数据） |
| **DCF 债务/利息** 🆕 | 资产负债表贷款字段探测 + 财务费用别名 → WACC 债务权重不再恒 0 |
| **safe_float 1e15** 🆕 | 大市值/大营收不再被清零（茅台 1500 亿营收） |
| **多源管理器** 🆕 | 腾讯+新浪+东财真实冗余降级（此前仅腾讯单源） |
| **宏观映射** 🆕 | GDP/CPI/PPI/PMI/M2 独立 reportName（此前全指 GDP） |
| **港美股分页** 🆕 | 全列表翻页拉全 |
| **akshare 可选** 🆕 | 基金净值/债券/可转债/宏观/港美股财务（未装自动降级） |

## 量化模型（v8.0）

```python
# 组合优化（纯 stdlib，不依赖 numpy/scipy）
from stock_researcher.quantitative.portfolio_models import mean_variance_optimize, allocate_portfolio
weights = mean_variance_optimize(returns_matrix, risk_aversion=2.5)["weights"]
port = allocate_portfolio(returns_matrix, method="risk_parity")
# 蒙特卡洛增强（跳跃扩散 + 肥尾 t）
from stock_researcher.quantitative.scenario_simulator import quick_scenario_forecast
r = quick_scenario_forecast(prices, distribution="t", use_jumps=True, dof=5)
# ML 预测叠加 + 进化闭环
from stock_researcher.fusion.multi_horizon_forecaster import MultiHorizonForecaster
fc = MultiHorizonForecaster().forecast_stock("600519", track=True)  # track 写入 PredictionTracker
```

## 全资产统一入口

```python
from stock_researcher import quant_analyze_asset
r = quant_analyze_asset("600519")            # 股票
r = quant_analyze_asset("128046")            # 可转债（11/12 开头自动识别）
r = quant_analyze_asset("gold")              # 商品
r = quant_analyze_asset("510300", asset_type="fund")  # ETF
# 返回：metrics(QuantMetrics) + scenario(蒙特卡洛) + forecast(多周期) + asset_specific
```

## 预测链路（三栈关系）

- **`scripts/stock_predict.py`**：CLI 七维评分（趋势/动量/量价/波动/概率/环境/黄金）+ 蒙特卡洛，零依赖单股快速预测
- **`fusion/multi_horizon_forecaster`**：主预测链路，十维信号融合 1d~6M，v8.0 叠加 ML 短期概率 + 进化闭环
- **`core/prediction_engine`**：三维预测（情绪/估值/历史/技术）+ GBM 蒙特卡洛
- 三栈独立可并用；v8.0 `quant_analyze_asset` 统一收口全资产预测

## 核心模块 API

| 模块 | import | 关键函数 |
|---|---|---|
| 数据 | `stock_researcher.data` | `MarketData` / `FundamentalData` / `MoneyFlowData` / `source_manager` / `akshare_provider` |
| 量化 | `stock_researcher.quantitative` | `compute_quant_metrics` / `quant_analyze_asset` / `allocate_portfolio` / `analyze_bond` / `MoneyFundAnalyzer` / `ConvertibleBondAnalyzer` / `quick_scenario_forecast` |
| 预测 | `stock_researcher.fusion` | `MultiHorizonForecaster` |
| 价值 | `stock_researcher.value_investing` | `ValueInvestingDecision` |
| 基金 | `pkg.fund_analyzer` | `score_fund_v3` / `fetch_fund_nav` / `predict_fund_multi_horizon` |

## 版本历史

<details>
<summary>📜 展开查看历史版本</summary>

| 版本 | 要点 |
|---|---|
| v9.3 | 量化预测增强：历史形态匹配预测（股票/基金/期货通用）+ 基金尾部风险/回撤恢复/稳定性/NAV预测 + 期货置信区间/仓位/展期收益 + quant_analyze_asset 接线 |
| v9.2 | 定期报告解读（年报/半年报/季报 同比环比 + 亮点风险 + 中文报告） |
| v9.1 | 板块评分真实性修复 + Agent 执行指南 + 文档清理 |
| v9.0 | 三大支柱：深度板块（RPS/宽度/离散度/主题/轮动周期）+ 深度指数（体制/波动率/结构/内含/真实PE分位）+ 体制感知预测（regime权重/共识度/宏观情景/校准）+ 自上而下整合 + CLI新命令；修复板块多市场死代码 |
| v8.0 | 全资产量化 + 真实数据（PE/PB分位/时效/资金流/DCF）+ 组合优化 + MC增强 + ML接入 + 债券/货基/可转债 + akshare |

</details>

## 目录速查

```
scripts/stock_researcher/
├── data/            # 数据源（腾讯/东财/新浪/akshare 可选）+ 多源管理器 + 数据质量
│                    #   + v9.0: macro_series 宏观序列 / index_constituents 指数成分
├── quantitative/    # 量化（指标/因子/组合优化/MC/回测/债券/货基/可转债/全资产入口）
│                    #   + v9.0: scenario_engine 宏观情景引擎
├── fusion/          # 十维信号融合多周期预测（含 ML overlay + 进化闭环）
│                    #   + v9.0: regime_overlay 体制权重 / signal_consensus 共识度
├── core/            # 分析器/预测引擎/技术/估值
├── value_investing/ # DCF/护城河/财务健康
├── funds/           # 基金量化
├── index_analysis/  # 指数：IndexAnalyzer + v9.0: 体制/波动率/结构/内含/估值分位
├── sector_analysis/ # 板块：Analyzer/Rotation + v9.0: RPS/宽度/离散度/主题/轮动周期
├── evolution/       # 回测 + 预测追踪（进化闭环）+ v9.0: calibration 预测校准
├── analysis/        # 五维聚合/资产推演 + v9.0: top_down 自上而下全景
├── sentiment/ agents/ screening/ advisor/ tracker/ # 舆情/大师/筛选/投顾/跟踪
├── research/        # 券商研报/宏观信号 + v9.2: financial_report 定期报告解读
scripts/stock_predict.py   # CLI 预测引擎（零依赖，v9.0 新命令 --sector-ranking 等）
pkg/fund_analyzer.py       # 基金深度分析
tests/                     # 527 测试（python runtests.py）
```

## ❓ 常见问题与避坑指南（FAQ）

### Q1: 开了代理（VPN）后数据获取失败？
**A**: 腾讯/东财数据源只接受国内 IP，**开启代理反而会失败**。解决方案：关闭代理后再运行，或设置代理绕过国内地址。

### Q2: 港股/美股代码怎么写？
**A**: 必须加市场前缀：

    python scripts/stock_predict.py hk:00700      # 港股腾讯
    python scripts/stock_predict.py us:AAPL        # 美股苹果
    python scripts/stock_predict.py "600519,hk:00700,us:AAPL"  # 批量

### Q3: 全球指数代码怎么写？
**A**: 用 `idx:` 前缀 + 指数代码：

    python scripts/stock_predict.py idx:N225       # 日经225
    python scripts/stock_predict.py idx:SPX        # 标普500
    python scripts/stock_predict.py idx:上证指数    # 中文名也行

### Q4: 预测评分 70 分是不是一定会涨？
**A**: **不是。** 评分 70 表示历史上相似条件下约 70% 的情况上涨，不保证未来。请结合基本面、政策、市场情绪综合判断。

### Q5: 返回的数据是实时的吗？
**A**: 不是。腾讯/东财接口延迟约 3~5 秒，非交易时段返回上一交易日收盘价。不适合做高频交易参考。

### Q6: akshare 相关功能报错？
**A**: akshare 是可选依赖，未安装时自动降级；如需启用执行 `pip install akshare`。

### Q7: 速度太慢怎么办？
**A**: 使用 `--quick` 模式跳过蒙特卡洛模拟和全球风险偏好获取，速度提升约 60%：
```bash
python scripts/stock_predict.py 600519 --simple --quick
```

> 📘 更多问题请查看 [README.md](README.md) 或运行 `python runtests.py` 验证环境。

---

## 免责声明

> ⚠️ **本工具仅供学习参考，不构成任何形式的投资建议。** 股市有风险，投资需谨慎。
