# 天天基金网数据接口文档

## 页面URL结构

### 基金经理列表
- 全部经理：`https://fund.eastmoney.com/manager/default.html`
- 股票型经理：`https://fund.eastmoney.com/manager/jjjl_gp.html`
- 混合型经理：`https://fund.eastmoney.com/manager/jjjl_hh.html`
- 债券型经理：`https://fund.eastmoney.com/manager/jjjl_zq.html`

### 单个经理详情
- URL模式：`https://fund.eastmoney.com/manager/{经理代码}.html`

### 基金公司
- 列表：`https://fund.eastmoney.com/company/default.html`
- 单个公司：`https://fund.eastmoney.com/company/{公司代码}.html`

## API接口

### 基金经理数据接口
```
https://fund.eastmoney.com/Data/FundDataPortfolio_Interface.aspx
```

**参数**：
| 参数 | 说明 | 示例值 |
|------|------|--------|
| dt | 数据类型 | 14=经理列表, 17=经理详情 |
| ft | 基金类型 | all/gp/hh/zq/sy |
| pn | 每页数量 | 20 |
| pi | 页码 | 1 |
| sc | 排序字段 | abbname |
| st | 排序方式 | asc/desc |
| mc | 回调函数 | returnjson |

**返回格式**：JavaScript变量调用（非标准JSON）
```javascript
var returnjson = {...}
```

### 基金持仓数据接口
```
https://fund.eastmoney.com/pingzhongdata/{基金代码}.js?v={时间戳}
```

**返回数据**（JavaScript变量）：
```javascript
// 股票代码
var stockCodes = ["300308", "688012"];

// 债券代码
var zqCodes = "019827,524462";

// 收益率
var syl_1n = "59.6";  // 近一年

// 净值数据
var Data_netWorthTrend = [...];

// 股票仓位
var Data_fundSharesPositions = [...];
```

## akshare天天基金数据接口

```python
import akshare as ak

# 基金持股明细（通过年报）
ak.fund_report_stock_group()

# 基金重仓股
ak.fund_top_positions()

# 基金经理列表
ak.fund_manager()

# 基金基本信息
ak.fund_info_em()
```

## 数据字段

| 字段 | 说明 | 来源 |
|------|------|------|
| manager_id | 经理代码 | 天天基金 |
| name | 姓名 | 天天基金 |
| company_id | 公司代码 | 天天基金 |
| fund_list | 管理基金列表 | 天天基金 |
| incep_date | 任职日期 | 天天基金 |
| scale | 管理规模 | 天天基金 |
| top_stocks | 十大重仓股 | 年报/季报 |
| top_bonds | 十大重仓债 | 年报/季报 |
| investment_style | 投资风格 | 分析判断 |