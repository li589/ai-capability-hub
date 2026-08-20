# 门店编码获取

## CRM 门店查询

按名称查询：

```bash
sl store find --type crm --name "<门店关键词>" --format json
```

按关键词或门店 ID 查询：

```bash
sl store find --type crm --keyword "<门店关键词或门店ID>" --format json
```

## 判定规则

| 返回情况 | 处理 |
|---------|------|
| 返回 `[]` 或数组长度为 0 | 停止并提示未找到门店，让用户补充更准确的门店名称或 ID |
| 返回 1 条 | 使用该条的 `omShopCode`（放入 `shopIds`、`shopFilterTypeValue` 或 `omShopCodes`） |
| 返回多条 | 展示候选门店名称让用户确认，不静默选择第一条 |
| 命令提示 token 缺门店清单 | 先执行 `sl token refresh dc`，再重试一次同一条门店查询 |

## 默认行为

用户未指定门店时，不传门店参数，按当前 token 默认权限执行。

## 编码使用与展示

- 门店范围只可使用检索结果中的真实门店编码；不得把客户输入的名称、旧编码或猜测编码直接用于查询。
- 支持门店范围的查询统一使用正向门店条件 `--shopid`；不得在筛选语句中拼接门店条件。
- 客户要求排除门店时，先取得当前可查门店清单，移除已确认门店后，将剩余真实编码作为正向范围传入。
- 最终展示的门店名称必须保持检索结果原样，不得截取、改写、映射或另行生成名称。

## 门店缓存与口头切换

- `cache/cysms-stores.json` 只作为门店候选清单和名称解析缓存；不得把它当成用户已选择门店。
- 不要主动读取或依赖 `cache/cysms-selected-stores.json`；该文件可能不存在，且不属于 Skill 运行契约。尤其不要从 Skill 目录下的 `cache/` 读取它；缺失不是错误。门店上下文只能来自用户本轮明示、命令显式参数或当前脚本自己的 scoped cache。
- 用户本轮明确指定门店或说「换成/切到/看某店」时，必须在本轮所有相关命令中显式传入门店参数；餐饮用 `--store-name`/`--store-id`，CRM 用 `omShopCodes`/`shopIds`/`shopFilterTypeValue`，供应链用 `--organName` 等对应参数。
- 用户未指定门店且命令不支持集团/默认权限口径时，先请用户确认门店；不要因为 selected cache 存在就直接查询。
