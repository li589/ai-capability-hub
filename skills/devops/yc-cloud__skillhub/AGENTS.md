# AGENTS.md (WorkBuddy Runtime)

## CLI Invocation

执行任何命令前，先读 [references/runtime.md](references/runtime.md)。

本包不含二进制。所有命令通过包内脚本执行：

```bash
sh ./scripts/yc-cloud.sh <子命令> [参数...]
```

脚本从 CDN 拉取 manifest，下载 loader，校验 SHA256 后执行加密 core。这是唯一允许的正式发布入口。

禁止：

- `which yc-cloud` / `find ~ -name "yc-cloud"` / 全局搜索二进制
- 直接执行 `~/.yc-cloud/loader/` 下缓存文件
- 手动 `curl` manifest / loader / core
- 手动读写 `~/.yc-cloud/config.json`（必须用 `config set` / `config get`）
- `go run .` / `make dev` 代替正式 CLI
- 启动失败时改用直接 API 或自建 launcher

## Quick Start

```bash
sh ./scripts/yc-cloud.sh config set apiKey <你的 apiKey>
sh ./scripts/yc-cloud.sh health
```

期望输出：`yc-cloud-cli is running`

## Project Facts

- 对外命令名：`yc-cloud`
- 持久化配置项只有 `apiKey`
- `BuildAPIBaseURL` 是构建注入，不可配置
- 配置文件路径：`~/.yc-cloud/config.json`（只读事实，不得手动编辑）

## Command Contract

文档中 `yc-cloud ...` 均等价于 `sh ./scripts/yc-cloud.sh ...`。

命令路径、flag、JSON 输出结构、错误结构、退出码属于外部接口，不得擅自更改。

## Module Routing

详见 `SKILL.md` 的 Routing 和对应 `references/*.md` 模块文件。
