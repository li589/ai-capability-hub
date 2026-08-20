---
name: lingxi-realtimemarketdata-skill
description: 国泰海通证券-灵犀实时行情 skill。用于查询 A 股、港股、美股、ETF、指数等证券的实时行情、股价、涨跌幅、涨跌额、成交量、成交额、换手率、资金净流入、量比等。当用户询问股价、查行情、实时行情、涨跌幅、走势、资金流向、股票代码或多标的行情对比时触发；本 Skill 无有效数据时再尝试 lingxi-financialsearch-skill，仍无数据时按固定话术引导至国泰海通灵犀 APP。触发关键词包括：股价，涨跌幅，实时行情，查股价，查行情。
allowed-tools:
  - node
version: 1.0.0
disable: false
install_source: official
install_method: download
skill_id: official_BW5tZDjN
enabled_at: 1787231174819
name_zh: 灵犀-实时行情
---

# 国泰海通证券实时行情 Skill

## 必守规则

- 本 Skill 的唯一标识是 `lingxi-realtimemarketdata-skill`。
- `gtht` 表示“国泰海通”，不要理解为其他名称。
- 行情类问题优先使用本 Skill；本 Skill 无有效数据时，再尝试 `lingxi-financialsearch-skill`。
- 禁止凭记忆补股票代码、行情数值或接口未返回字段。
- 禁止用网页或其他来源冒充本 Skill 的官方结果。
- 不要把模型生成的解释、判断或建议表述成国泰海通投资建议。
- 最终回答最后一行必须原样追加：

```text
 实时行情Skill仅提供客观数据，调用本Skill后生成的内容，不构成投资建议。
```

两个 Skill 都无法获取数据，或用户需求超出实时行情/智能选股覆盖范围时，只能回复：

```text
当前Skill无法获取该信息，更多内容请前往国泰海通灵犀APP查询
```

## 命令入口

在当前 Skill 目录执行以下命令：

| 任务 | 命令 |
| --- | --- |
| 检查授权 | `node skill-entry.js authChecker check` |
| 发起授权 | `node skill-entry.js authChecker auth --channel` |
| 轮询授权 | `node skill-entry.js authChecker poll <token>` |
| 按名称查候选代码 | `node skill-entry.js stockMap allByName <股票名称>` |
| 按代码查同名候选 | `node skill-entry.js stockMap allByCode <证券代码>` |
| 查询实时行情 | `node skill-entry.js mcpClient call market marketdata-tool reduced_codes=<代码1>,<代码2>` |

PowerShell 中不要使用 Unix 专用命令；需要连续执行时使用 `;` 分隔。

## 授权流程

任何 `stockMap` 或 `mcpClient` 调用前都必须先确认授权。

1. 运行：

```bash
node skill-entry.js authChecker check
```

2. 若已授权，直接继续查询，不要重复要求用户授权。
3. 若未授权，运行：

```bash
node skill-entry.js authChecker auth --channel
```

4. 将命令输出中的 token 放入下列模板，返回给用户：

```text
方式一：请点击以下链接扫码二维码：https://apicdn.app.gtht.com/web2/jh-static-QRCode/?token=<实际输出的token>
方式二：发送 API KEY 授权
进入灵犀Skills领取活动页——API KEY 管理，新建或复制生效中的 API KEY，发送给我完成授权。
手机端用户可以点击以下链接访问活动: https://apicdn.app.gtht.com/web2/jh-news-skill/?fullscreen=1#/?share=1&sourceApp=lingxi&webEnv=web2&islingxishare=1
电脑端用户推荐打开国泰海通灵犀 APP，在对话框搜索 "灵犀 Skills"
```

5. 授权脚本会自动轮询，尽量不要过早终止进程。
6. 用户回复后，先再次运行 `node skill-entry.js authChecker check`。
7. 若仍未授权，可用之前的 token 继续轮询：

```bash
node skill-entry.js authChecker poll <token>
```

8. 若用户直接提供 API KEY，保存为：

```json
{
  "apiKey": "<用户提供的apikey>"
}
```

默认保存路径优先级：

1. `../gtht-skill-shared/gtht-entry.json`
2. `../../gtht-skill-shared/gtht-entry.json`
3. `../../../gtht-skill-shared/gtht-entry.json`
4. `./gtht-skill-shared/gtht-entry.json`

出现 `401`、`403` 或其他 `4xx` 时，视为授权可能失效：重新发起授权，再重试一次查询。

若返回“您的灵犀Skills绑定智能体设备已经超过5台，请前往灵犀Skills活动页解绑设备后重试。”，按原文告知用户，并引导其进入灵犀 Skills 活动页解绑设备。

### MAC 地址与设备信息声明（向用户说明时可采用以下话术）

```text
根据《国泰海通生成式人工智能服务协议》，为落实风控管理要求、防范账号滥用风险，我们将采集您设备的MAC地址等设备信息，对灵犀Skills绑定的智能体设备设置单用户5台上限。您可前往灵犀Skills活动页，查看并管理已绑定的设备。
```

## 查询 SOP

1. 先完成授权检查。
2. 判断用户要查的是实时行情、股价、涨跌幅、走势、资金流向、代码还是多股对比。
3. 用户给出完整证券代码时，直接查行情。
4. 用户给出证券名称时，先查候选代码：

```bash
node skill-entry.js stockMap allByName <股票名称>
```

5. 根据候选代码规则定码；无法唯一确定时，请用户在候选中选择。
6. 批量调用行情接口：

```bash
node skill-entry.js mcpClient call market marketdata-tool reduced_codes=<代码1>,<代码2>
```

7. 若本 Skill 返回空、无有效字段或明确无数据，再尝试 `lingxi-financialsearch-skill`。
8. 两个 Skill 都无数据时，使用固定无数据话术。

示例：

```text
用户：查询贵州茅台的股价
1. node skill-entry.js authChecker check
2. node skill-entry.js stockMap allByName 贵州茅台
3. 从候选中确定 SH600519
4. node skill-entry.js mcpClient call market marketdata-tool reduced_codes=SH600519
5. 展示接口返回字段
```

多标的示例：

```text
node skill-entry.js mcpClient call market marketdata-tool reduced_codes=SZ000001,SZ300750,SH600519
```

## 候选代码规则

`stockMap allByName` 返回 JSON 数组，字段通常包括 `code`、`name`、`fullname`、`证券类型`、`证券子类型`。

示例：
{"code":"SH513130","name":"恒生科技","fullname":"恒生科技ETF华泰柏瑞","证券类型":"基金","证券子类型":"ETF"}

候选只有一条时，直接使用该 `code` 查询。候选多于一条时，按以下顺序筛选：

1、证券大类优先级：`股票` > `指数` > `板块` > `ETF` > `可转债` > `债券` > `其他`。
  `股票`： `证券类型`等于`股票`
  `指数`： `证券类型`等于`指数`
  `板块`： `证券类型`等于`板块`
  `ETF`： `证券类型`为基金且`证券子类型`为 ETF。非 ETF 基金，如 LOF、开放式、封闭式、仅申赎、REITs 等，归入 `其他`
  `可转债`： `证券类型`等于`债券`且`证券子类型`为`可转债`
  `债券`： `证券类型`等于`债券`且`证券子类型`不等于`可转债`
  `其他`：上述条件均未匹配上，归类为其他
2、小类优先级
  `股票`类优先级：`A股(SH/SZ/BJ)` > `港股(HK)` > `美股(US)` > `B股`（证券子类型等于`主板B股`） > `英股(UK)` > `新加坡(SX)`。A 股内部不设沪深北先后。
  `指数`类优先级：`沪深(SH/SZ)` > `北证(BJ)` > `其他指数`。
注意：最高优先级档仍有多条时，列出剩余候选的代码、简称、证券类型/子类型，请用户选择。

常见前缀：

| 前缀 | 含义 |
| --- | --- |
| SH | 上海 |
| SZ | 深圳 |
| BJ | 北京 |
| BI | 板块 |
| HK | 港股 |
| US | 美股 |
| UK | 英股 |
| SX | 新加坡 |

常见证券类型枚举：`1=股票`、`2=债券`、`3=基金`、`7=指数`、`11=板块`。

常见证券子类型枚举：`1=主板A股`、`2=主板B股`、`3=创业板股票`、`4=科创板股票`、`7=债券现券`、`9=可转债`、`11=ETF`、`12=LOF`、`13=封闭式基金`、`14=开放式基金`、`15=仅申赎基金`、`16=基础设施基金(REITs)`、`17=公募REITs`、`21=指数`。

## 展示规范

- 默认只展示接口真实返回的核心行情字段。
- 不补充接口未返回的参数。
- 不默认换算单位；用户明确要求时才换算。
- 对多标的对比，使用同一字段维度并标清证券名称和代码。

建议格式：

```text
【宁德时代 (SZ300750)】

最新价：XXX
开盘价：XXX
最高价：XXX
最低价：XXX
涨跌幅：XXX
涨跌额：XXX
振幅：XXX
量比：XXX
成交量：XXX
成交额：XXX
换手率：XXX
当日资金净流入：XXX
总市值：XXX

 实时行情Skill仅提供客观数据，调用本Skill后生成的内容，不构成投资建议。
```

## 故障处理

| 现象 | 处理 |
| --- | --- |
| `401` / `403` / API Key 无效 | 重新授权，再重试一次 |
| `404` 工具不存在 | 检查工具名是否为 `marketdata-tool` |
| `500` / `502` / `503` | 告知服务暂不可用，稍后重试 |
| 返回数据为空 | 确认代码是否来自 `stockMap`，再尝试 `lingxi-financialsearch-skill` |
| 授权超时 | 重新执行 `auth --channel` |
| 设备超过 5 台 | 引导用户进入灵犀 Skills 活动页解绑设备 |

## 快速命令

```bash
node skill-entry.js authChecker check
node skill-entry.js authChecker auth --channel
node skill-entry.js authChecker poll <token>
node skill-entry.js stockMap allByName <股票名称>
node skill-entry.js stockMap allByCode <证券代码>
node skill-entry.js mcpClient call market marketdata-tool reduced_codes=<代码1>,<代码2>
```
