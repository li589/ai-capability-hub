---
install_source: official
install_method: download
skill_id: official_Onz2199m
enabled_at: 1787231829917
version: 1.0.0
name_zh: A股行情查询工具
---
# A 股行情 Skill

实时获取 A 股股票行情数据（使用新浪财经免费 API）

## 命令

```bash
# 查询单只股票
a-stock <股票代码>

# 查询多只股票
a-stock <代码 1> <代码 2> ...

# 查询指数
a-stock sh000001  # 上证指数
a-stock sz399001  # 深证成指
a-stock sh000300  # 沪深 300
```

## 股票代码格式

- 上交所：`sh` + 6 位数字 (如 `sh600519` 贵州茅台)
- 深交所：`sz` + 6 位数字 (如 `sz000858` 五粮液)

## 示例

```bash
a-stock sh600519
a-stock sz000858 sh600519
```
