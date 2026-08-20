# flash 模块硬约束

## 模块合同

本文件的目标不是介绍闪购命令，而是约束 agent 在 `flash` 模块下的行为。

必须遵守：

1. 只处理当前 Go 版 CLI 已注册的 `flash` 命令。
2. 只使用当前模块明确指定的事实源。
3. 不得把统计口径、时间范围或来源业务做主观改写。
4. 如果请求超出允许命令范围，必须直接停止。
5. **禁止直接调用 HTTP API（含 curl）**；所有统计必须通过 CLI 命令完成。
6. CLI 启动方式遵守 [runtime.md](runtime.md)；启动失败时不得改用 curl 或自建 launcher。
7. **🔒 闪送日报仅统计闪送业务，source=1（注册）/ sourceBusiness=1 + businessUnit=1（下单）是 CLI 内置固定过滤，无需用户额外指定，无需确认提示，直接按此规则执行。**

## 事实源

只按以下顺序取事实：

1. `internal/flash/flash.go`
2. `docs/COMMAND_SPEC.md`
3. `workbuddy/references/flash.md`

以下材料不是事实源：

- `dist/` 下副本
- 历史发布包说明
- 其他仓库的闪购统计命令
- 未在当前源码或 `COMMAND_SPEC.md` 中出现的统计口径

## 闪送日报查询策略

查询闪送日报时，**只使用 CLI 命令**，按下表分工：

| 日报指标 | CLI 命令 |
|---------|---------|
| 完整日报（推荐） | `yc-cloud flash summary` |
| 当日注册量（仅闪送） | `yc-cloud flash register --range today` |
| 累计注册量（仅闪送） | `yc-cloud flash register --range all` |
| 当日下单量（含子订单，仅闪送店铺订单） | `yc-cloud flash order --range today --source-business 1` |
| 累计下单量（含子订单，仅闪送店铺订单） | `yc-cloud flash order --range all --source-business 1` |

### 统计口径（由 CLI 内置，agent 不得改写）

| 指标 | 内置过滤条件 |
|------|-------------|
| 注册量 | `source=1`（闪送）；`today` 时附加 `registerTime` 时间窗 |
| 下单量 | `sourceBusiness=1`（闪送）+ `businessUnit=1`（店铺订单，排除配送订单） |

禁止：

- 读取 `~/.yc-cloud/config.json` 获取 `apiKey` 后直接调接口
- 用 curl / Postman / 脚本绕过 CLI
- 因「CLI 统计不准」等历史理由改用直接 API 调用

## Allowlist

当前只允许以下 4 个命令：

```text
yc-cloud flash summary
yc-cloud flash register
yc-cloud flash order
yc-cloud flash district-order
```

规则：

- allowlist 之外的任何 `flash` 子命令，一律视为不支持
- 不得把 `flash` 命令替换为 `travel`、`collection`、`order` 或其他模块命令
- 不得因为历史经验脑补新的闪购统计命令
- **🔒 闪送日报的 source=1（注册）和 sourceBusiness=1 + businessUnit=1（下单）是固定硬约束，不允许出现「提示用户确认」或「询问是否需要闪送」等交互，直接按此执行**

## Routing

用户请求命中以下关键词时，进入本模块：

- 闪购
- 日报
- 注册量
- 下单量
- 订单统计
- 商圈订单数据
- 商圈数据
- 商圈运营数据
- 商圈订单
- `flash`

如果请求同时涉及闪购和其他模块：

- 先完成模块判断
- 若核心目标是闪购日报、闪购注册量、闪购下单量，优先进入本模块
- 不得在未完成路由前执行命令
- **🔒 「闪送日报」即视为仅统计闪送业务，自动绑定 source=1 / sourceBusiness=1 + businessUnit=1，不再询问**

## Refusal Rules

遇到以下情况必须停止：

1. 请求命令不在 allowlist 中
2. 本地 CLI 未注册对应 `flash` 子命令
3. 缺少必要时间参数且当前上下文无法可靠补齐
4. 统计口径与当前实现冲突
5. 文档与当前 Go 源码冲突且无法以源码直接定论

停止时只允许给出以下结论：

- 当前版本不支持
- 缺少必要条件
- 需要补充明确参数
- 统计口径未确认

## Parameter Rules

以下参数必须保守处理：

- `date`
- `start-time`
- `end-time`
- `range`
- `source-business`

规则：

- `range` 只允许：`today` / `all`
- `source-business` 不得凭记忆脑补新的默认值
- 未传 `source-business` 时，按当前实现默认 `1`
- 只传 `--date` 时，允许自动展开成当天时间窗口
- 同时传 `--date` 与 `--start-time/--end-time` 时，后者优先
- `--start-time` 与 `--end-time` 必须成对出现

## Parameter Allowlist

AI 不得自己发明参数。每个命令只允许使用下面列出的参数。

### `flash summary`

命令形态：

```text
yc-cloud flash summary [--date <yyyy-MM-dd>] [--start-time <yyyy-MM-dd HH:mm:ss>] [--end-time <yyyy-MM-dd HH:mm:ss>] [--source-business <int>] [--json] [--debug]
```

只允许这些参数：

| 参数 | 说明 | 默认值/枚举 |
|---|---|---|
| `--date` | 统计日期 | 默认当天 |
| `--start-time` | 自定义开始时间 | - |
| `--end-time` | 自定义结束时间 | - |
| `--source-business` | 下单来源业务 | 默认 `1` |
| `--json` | JSON 输出 | - |
| `--debug` | 调试输出 | - |

### `flash register`

命令形态：

```text
yc-cloud flash register [--date <yyyy-MM-dd>] [--start-time <yyyy-MM-dd HH:mm:ss>] [--end-time <yyyy-MM-dd HH:mm:ss>] [--range <today|all>] [--json] [--debug]
```

只允许这些参数：

| 参数 | 说明 | 默认值/枚举 |
|---|---|---|
| `--date` | 统计日期 | 默认当天 |
| `--start-time` | 自定义开始时间 | - |
| `--end-time` | 自定义结束时间 | - |
| `--range` | 统计范围 | `today` / `all`；默认 `today` |
| `--json` | JSON 输出 | - |
| `--debug` | 调试输出 | - |

### `flash order`

命令形态：

```text
yc-cloud flash order [--date <yyyy-MM-dd>] [--start-time <yyyy-MM-dd HH:mm:ss>] [--end-time <yyyy-MM-dd HH:mm:ss>] [--range <today|all>] [--source-business <int>] [--json] [--debug]
```

只允许这些参数：

| 参数 | 说明 | 默认值/枚举 |
|---|---|---|
| `--date` | 统计日期 | 默认当天 |
| `--start-time` | 自定义开始时间 | - |
| `--end-time` | 自定义结束时间 | - |
| `--range` | 统计范围 | `today` / `all`；默认 `today` |
| `--source-business` | 下单来源业务 | 默认 `1` |
| `--json` | JSON 输出 | - |
| `--debug` | 调试输出 | - |

### `flash district-order`

命令形态：

```text
yc-cloud flash district-order --area-name <商圈名称> --start-date <yyyy-MM-dd> --end-date <yyyy-MM-dd> [--json] [--debug]
```

只允许这些参数：

| 参数 | 说明 | 默认值/枚举 |
|---|---|---|
| `--area-name` | 商圈名称 | 必填 |
| `--start-date` | 起始日期 | 必填 |
| `--end-date` | 结束日期 | 必填 |
| `--json` | JSON 输出 | - |
| `--debug` | 调试输出 | - |

## Execution State Machine

所有 `flash` 请求必须按以下顺序执行：

1. 判断请求是否落在本模块范围
2. **🔒 路由到闪送日报 → 自动套用 source=1（注册）/ sourceBusiness=1 + businessUnit=1（下单）过滤，无需确认**
3. 校验目标命令是否在 allowlist 中
4. 校验时间参数和枚举参数是否合法
5. 执行目标 CLI 命令
6. 仅在失败时回看源码和 `COMMAND_SPEC.md`

禁止：

- 未完成参数校验就执行命令
- 擅自切换 `range`
- 擅自切换 `source-business`
- 把 `summary` 的聚合结果和 `register` / `order` 的单项结果混为一谈
- 直接调用后端 API 替代 CLI

## Per-Command Rules

### 闪送日报

查询完整闪送日报（含当日/累计注册量 + 下单量）时，优先使用：

```bash
yc-cloud flash summary --date <yyyy-MM-dd> --source-business 1 --json
```

也可分项查询：

```bash
yc-cloud flash register --date <yyyy-MM-dd> --range today --json
yc-cloud flash register --range all --json
yc-cloud flash order --date <yyyy-MM-dd> --range today --source-business 1 --json
yc-cloud flash order --range all --source-business 1 --json
```

取值：所有命令均取 `data.total`（`flash summary` 取各字段聚合值）。

### `flash summary`

只负责闪购日报总览。固定按四步聚合：

- ① 当日注册量 → 内置 `source=1` + `registerTime` 过滤
- ② 累计注册量 → 内置 `source=1` 过滤
- ③ 当日下单量（含子订单） → 内置 `sourceBusiness=1` + `businessUnit=1` + `createdTime` 过滤
- ④ 累计下单量（含子订单） → 内置 `sourceBusiness=1` + `businessUnit=1` 过滤

不得漏掉其中任一项，不得改成别的聚合口径。

只允许使用 `--date --start-time --end-time --source-business --json --debug`。

注意：`--source-business` 仅影响下单量（步骤③④），不影响注册量（步骤①②）。

### `flash register`

只负责注册量统计。

必须遵守：

- CLI 内置 `source=1` 过滤，仅统计闪送注册
- 统计值只取 `data.total`
- 查询请求体统一使用 `limit=1`、`offset=0`
- 只允许使用 `--date --start-time --end-time --range --json --debug`

### `flash order`

只负责下单量统计。

必须遵守：

- CLI 内置 `sourceBusiness=1` + `businessUnit=1` 过滤（店铺订单，排除配送订单）
- 统计值只取 `data.total`
- 查询请求体统一使用 `limit=1`、`offset=0`
- 默认 `sourceBusiness=1`
- 只允许使用 `--date --start-time --end-time --range --source-business --json --debug`

### `flash district-order`

只负责商圈订单分类统计。

必须遵守：

- 只调用 `/api/sfs/order/manage/query/commercialAreaStatistics`（通过 CLI）
- 不得用 `queryAll` 接口替代
- 输出格式固定，不可修改标题、字段顺序或换行结构
- 所有统计值必须为整数
- 日期范围格式为「X年X月X日」或「X年X月X日-X年X月X日」
- 单日查询时 `--start-date` 和 `--end-date` 传相同日期
- 只允许使用 `--area-name --start-date --end-date --json --debug`

## Output Rules

优先输出：

1. 实际执行的命令
2. 最终采用的时间窗口
3. `range` / `source-business`
4. 命中的事实源
5. 成功结果或失败原因

禁止：

- 长篇背景解释
- 未执行路径的猜测
- 把未确认的统计口径包装成确定事实

## Non-Goals

本模块不负责：

- 推断新的闪购统计命令
- 发明新的统计维度
- 修改默认统计口径
- 把闪购统计改写成其他模块命令
- 直接调用 HTTP API
- 解释历史架构
