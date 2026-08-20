# CLI 使用指南

> **本文件相对上游有增补**（「前置条件」补安装说明，新增「命令注册与登录耦合」「退出码」两节）。
> 改动清单见 [../NOTICE.md](../NOTICE.md)。

## 前置条件

运行环境需要 Node.js 18+。所有命令通过 `meegle` 执行。

`meegle` 不随飞书套件默认安装。缺失时按父技能 [lark-unified 第 0.3 节](../../../SKILL.md) 按需安装：

```bash
npx -y @lark-project/meegle@latest install --no-skills --no-auth --host <host> --lang zh
```

`--no-skills` 是必需的：官方向导默认会执行 `skills add` 往全局技能目录再装一份 meegle 技能，与本
子技能重复。该向导内部走 `npm install -g @lark-project/meegle`，会写全局 npm 前缀，执行前先告知用户。

## 命令注册与登录耦合（先读这条）

**未登录时业务命令不会注册。** `meegle --help` 只列出 `auth` / `config` / `url` / `inspect` /
`completion` / `version`，调用任何业务命令都会得到：

```
unknown command "workitem" for "meegle"     # 退出码 1
```

这与**命令真的不存在**时的报错文本、退出码完全一致，无法从报错本身区分。所以：

- 看到 `unknown command` 先查 `meegle auth status --format json`，确认不是未登录，再怀疑命令名。
- 未登录时 `meegle inspect` 返回 `No commands available (not connected to server or cache is empty)`，
  **退出码 0**。这同样是未登录的表现，不是 CLI 坏了。

## 命令结构

```bash
meegle <resource> <method> [flags] --format json
```

命令采用 `resource method` 两级结构。所有输出推荐使用 `--format json` 获取结构化数据。

## 全局 Flag

| Flag | 说明 |
|------|------|
| `--format json\|table\|ndjson` | 输出格式，默认 json |
| `--select <props>` | 选取输出属性，逗号分隔（支持 dot path，如 `name,owner.name`） |
| `--profile <name>` | 临时切换 profile |
| `--verbose` | 显示详细日志 |
| `--refresh` | 从服务端刷新本地命令缓存（旁路 24h cache） |

## 参数传递

几种方式，优先级从高到低：

1. **Flag 模式**（推荐）：`--project-key PROJ --work-item-type story`
2. **--fields 模式**（写工作项字段，可重复）：`--fields '{"field_key":"name","field_value":"任务标题"}' --fields '{"field_key":"priority","field_value":"1"}'`；`field_value` 支持任意 JSON 值（数组/对象原样传）
3. **--params 模式**（完整 JSON 兜底）：`--params '{"fields":[{"field_key":"name","field_value":"任务标题"}]}'`
4. **--set 模式**（仅顶层参数快捷写法，不支持 fields[]）：`--set page_num=1` 等价于 `--page-num 1`，支持 dot-path 嵌套；不要用它写工作项字段

Flag 覆盖 `--params`；`--set` 只影响顶层参数，**不会**写到 `fields[]`。

## 命令发现

CLI 的命令和参数会随版本更新。遇到不确定的命令或参数时，使用 `inspect` 获取最新信息：

```bash
meegle inspect                    # 列出所有可用命令
meegle inspect workitem.create    # 查看具体命令的参数 schema
```

> 命令清单本地缓存 24 小时。如果 `inspect` 输出的参数与服务端实际不符，或服务端有新命令但 CLI 报 `unknown command`，加上 `--refresh` 强制从服务端重新拉取最新清单：
> ```bash
> meegle --refresh inspect workitem.create
> ```

## 输出处理

- 始终使用 `--format json` 获取结构化输出，方便解析
- 使用 `--select` 精简返回字段，如 `--select id,name,current_nodes.name`
- 命令返回错误时，JSON 中包含 `error` 和 `message` 字段

## 退出码

**判断成功失败用退出码或结构化 `error` 字段，并且必须同行捕获退出码：**

```bash
OUT=$(meegle workitem get --work-item-id 123 --format json 2>&1); RC=$?
```

写成 `meegle ... | head` 之后再取 `$?`，拿到的是 `head` 的退出码，会把失败误判成成功。

两个已知的"退出码不反映真实状态"的例子：

| 命令 | 情形 | 退出码 | 正确判据 |
|------|------|--------|----------|
| `auth login --phase poll --once` | 用户尚未完成授权 | **0** | 读 `status`，`authorization_pending` ≠ 成功 |
| `inspect` | 未登录 | **0** | 输出为 `No commands available ...` 即视为未登录 |
| `auth status` | 未登录 | 1 | 以 `authenticated` 字段为准 |
