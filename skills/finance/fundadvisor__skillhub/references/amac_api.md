# 基金业协会数据接口文档

## 数据源

**官网**：www.amac.org.cn
**公募基金管理人公示**：需要通过爬虫或API获取

## 接口分析

### 公募基金管理人查询

**URL模式**：
- 分页公示页：`https://gs.amac.org.cn/amac-infodisc/res/pof/manager/managerList.html`
- 私募基金管理人API：`/amac-infodisc/api/pof/manager`

**注意**：基金业协会网站主要展示私募基金管理人，公募基金管理人可能需要通过不同路径访问。

### 备用数据源

如果基金业协会网站难以直接爬取，可以使用以下替代方案：

1. **天天基金网基金公司数据**
   - URL：`https://fund.eastmoney.com/company/default.html`
   - 覆盖：所有公募基金公司

2. **Wind资讯**
   - 需要Wind账号
   - 数据最全面

3. **akshare库**
   - 基金数据接口：`fund_manager()`、`fund_info()`等
   - 覆盖：基金基本信息、经理信息、规模数据

## akshare基金数据接口

```python
import akshare as ak

# 获取基金经理列表
ak.fund_manager()

# 获取基金基本信息
ak.fund_info(fund_code="000001")

# 获取基金持仓
ak.fund_portfolio_hold_em()
```

## 数据字段

| 字段 | 说明 | 来源 |
|------|------|------|
| company_id | 公司代码 | 自动生成 |
| name | 公司名称 | 基金业协会/天天基金 |
| type | 公募/私募 | 基金业协会 |
| scale | 管理规模（亿） | 定期报告 |
| establish_date | 成立日期 | 基金业协会 |
| manager_count | 基金经理数量 | 统计 |