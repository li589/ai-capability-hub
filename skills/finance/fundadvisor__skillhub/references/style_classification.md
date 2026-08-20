# 投资风格分类标准

## 分类维度

### 1. 按投资标的分类

| 类型 | 代码 | 说明 |
|------|------|------|
| 股票型 | STOCK | 股票仓位≥80% |
| 混合型 | MIXED | 股票仓位40-80% |
| 债券型 | BOND | 债券仓位≥80% |
| 货币型 | MONEY | 货币市场工具 |
| FOF | FOF | 基金中基金 |
| 指数型 | INDEX | 跟踪特定指数 |
| QDII | QDII | 海外市场投资 |

### 2. 按投资风格分类

| 风格 | 代码 | 判断依据 |
|------|------|---------|
| 价值型 | VALUE | 市盈率低、ROE稳定、分红高 |
| 成长型 | GROWTH | 营收/利润增速高、估值容忍度高 |
| 均衡型 | BALANCED | 兼顾价值和成长 |
| 积极型 | AGGRESSIVE | 高仓位、高换手、高波动 |
| 稳健型 | STABLE | 回撤控制好、波动低 |

### 3. 按市场覆盖分类

| 市场 | 代码 | 说明 |
|------|------|------|
| A股 | A_SHARE | 沪深股票 |
| 港股 | HK_SHARE | 港交所上市 |
| 美股 | US_SHARE | 美股市场 |
| 全球 | GLOBAL | 多市场配置 |
| QDII | QDII | 海外QDII基金 |

### 4. 按持仓特征分类

| 特征 | 代码 | 判断依据 |
|------|------|---------|
| 高仓位 | HIGH_POS | 股票仓位>85% |
| 择时型 | TIMING | 仓位波动大 |
| 行业集中 | SECTOR_CONCENTRATED | 单行业>30% |
| 分散配置 | DIVERSIFIED | 前十大持仓<50% |
| 集中配置 | CONCENTRATED | 前十大持仓>70% |

## 风格判断算法

### 基于持仓数据判断

```python
def classify_style(fund_data):
    # 计算因子
    pe_ratio = calculate_pe(fund_data)  # 市盈率
    revenue_growth = calculate_growth(fund_data)  # 营收增速
    position_ratio = fund_data['stock_ratio']  # 仓位
    turnover = fund_data['annual_turnover']  # 换手率

    # 风格判断
    if pe_ratio < 15 and revenue_growth < 20:
        style = "VALUE"
    elif pe_ratio > 25 and revenue_growth > 30:
        style = "GROWTH"
    else:
        style = "BALANCED"

    # 仓位判断
    if position_ratio > 85:
        position_style = "HIGH_POS"
    elif position_ratio.std() > 20:
        position_style = "TIMING"
    else:
        position_style = "STABLE_POS"

    return {"style": style, "position": position_style}
```

### 基于净值波动判断

```python
def classify_by_volatility(returns):
    # 计算年化波动率
    volatility = returns.std() * sqrt(252)

    # 计算最大回撤
    max_drawdown = calculate_max_drawdown(returns)

    if volatility < 15 and max_drawdown < 20:
        return "STABLE"
    elif volatility > 30 or max_drawdown > 40:
        return "AGGRESSIVE"
    else:
        return "BALANCED"
```

## 风格画像标签

每个基金经理/基金公司生成风格标签：

```
GROWTH-A_SHARE-HIGH_POS-SECTOR_CONCENTRATED
```

含义：成长风格、A股为主、高仓位、行业集中

## 匹配算法

基于客户风险偏好匹配风格：

| 风险偏好 | 推荐风格 |
|---------|---------|
| 保守型 | VALUE-STABLE, BOND-STABLE |
| 稳健型 | BALANCED-STABLE, MIXED-STABLE |
| 积极型 | GROWTH-AGGRESSIVE, STOCK-HIGH_POS |
| 激进型 | GROWTH-HIGH_POS, TIMING |