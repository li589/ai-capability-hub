# 高频实时行情工具统一说明

- 高频实时行情工具用于查询交易日日内的实时快照或高频时间序列
- 当前支持 `stock`、`fund`、`bond`、`index` 四个服务
- 工具名分别为 `stock_highfreq_quotes`、`fund_highfreq_quotes`、`bond_highfreq_quotes`、`index_highfreq_quotes`
- 高频实时行情工具使用结构化参数，不使用 `query` 字段
- 必填参数为 `symbols`、`indicators`、`data_mode`；`data_mode` 必须显式传入 `real_time` 或 `highfreq`，不可省略；
- 当 `data_mode` 为 `highfreq` 时，可传 `interval` 指定 1/3/5/10/15/30/60 分钟周期
- `symbols` 支持多个主体用英文逗号拼接，单次请求上限 10 个；
- `indicators` 支持多个指标用英文逗号拼接，单次请求上限 10 个

# 工具边界
- 数据边界：仅支持交易日日内数据查询，不支持历史数据查询；债券高频实时行情仅支持交易所债券数据，不支持银行间市场。
- 适用边界: 当用户询问“最新价、实时行情、盘中走势、1分钟/5分钟K线、日内分时”等需求时，优先选择对应服务的高频实时行情工具；当用户询问历史日频、财报、基本资料、公告事件等需求时，使用各服务内其他取数工具。