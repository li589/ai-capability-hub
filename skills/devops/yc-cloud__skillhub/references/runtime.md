# runtime 模块硬约束

## 模块合同

本文件约束 agent 如何启动和执行 `yc-cloud` CLI。

必须遵守：

1. 本 Skill 包**不含**二进制；所有命令只能通过包内启动脚本执行。
2. 只允许使用 `sh ./scripts/yc-cloud.sh <子命令> [参数...]`。
3. 不得自行下载、校验或执行 loader / core。
4. 不得绕过启动脚本直接调用缓存二进制或手写 HTTP 请求。
5. 文档中所有 `yc-cloud ...` 均表示 `sh ./scripts/yc-cloud.sh ...`。

## 事实源

只按以下顺序取事实：

1. `workbuddy/AGENTS.md`
2. `workbuddy/scripts/yc-cloud.sh`
3. `workbuddy/references/runtime.md`
4. `workbuddy/SKILL.md`

以下材料不是事实源：

- `dist/` 下副本
- `~/.yc-cloud/` 下的缓存文件结构
- 其他仓库的启动脚本或二进制路径
- agent 自行推断的 CDN / manifest / loader 下载逻辑

## 唯一允许的启动方式

```bash
sh ./scripts/yc-cloud.sh <子命令> [参数...]
```

示例：

```bash
sh ./scripts/yc-cloud.sh config set apiKey <你的 apiKey>
sh ./scripts/yc-cloud.sh health
sh ./scripts/yc-cloud.sh flash summary --date 2026-06-25 --json
```

首次执行时，启动脚本会按 manifest 从 CDN 下载 loader，并在本地校验 SHA256 后执行。这是**正式发布链路的一部分**，agent 只需调用脚本，不得复刻其内部步骤。

## 严格禁止

以下行为一律禁止：

| 禁止行为 | 原因 |
|---------|------|
| `which yc-cloud` / `find ~ -name "yc-cloud"` | 全局搜索二进制，可能落到非官方缓存 |
| 直接执行 `~/.yc-cloud/loader/**/yc-cloud-loader` | 绕过 manifest 校验与版本治理 |
| 手动 `curl` manifest / loader / core | 复刻启动脚本内部逻辑，易被判定为恶意下载执行 |
| 手动读写 `~/.yc-cloud/config.json` | 配置必须通过 `config set/get/delete` |
| `go run .` / `make dev` 代替正式 CLI | 开发入口，不是 agent 执行面 |
| 为「CLI 不可用」自行编写下载脚本 | 应报告启动失败，不得自建 launcher |

## 配置规则

持久化配置项只有 `apiKey`。

```bash
sh ./scripts/yc-cloud.sh config set apiKey <值>
sh ./scripts/yc-cloud.sh config get apiKey
sh ./scripts/yc-cloud.sh config delete apiKey
sh ./scripts/yc-cloud.sh config list
```

禁止：

- `cat ~/.yc-cloud/config.json`
- 用编辑器或脚本直接改配置文件

## 缓存清理

如需清空本地缓存，只允许：

```bash
sh ./scripts/yc-cloud.sh clear-env
```

禁止手动删除 `~/.yc-cloud/` 下目录来「修复」启动问题，除非用户明确要求且已说明风险。

## 执行状态机

所有 CLI 调用必须按以下顺序执行：

1. 确认当前在 WorkBuddy 包目录下，且存在 `scripts/yc-cloud.sh`
2. 将文档中的 `yc-cloud ...` 改写为 `sh ./scripts/yc-cloud.sh ...`
3. 校验子命令属于目标业务模块 allowlist
4. 执行命令
5. 仅在失败时回看 `AGENTS.md`、目标模块文件和 `docs/COMMAND_SPEC.md`

禁止：

- 在启动失败时改用 curl 调业务 API
- 在启动失败时自行下载 loader/core
- 用源码编译产物冒充正式发布 CLI

## 失败处理

启动脚本失败时，只允许输出：

- 启动脚本不存在或不可执行
- manifest / loader 下载失败
- SHA256 校验失败
- 缺少 `apiKey`
- 当前环境不支持（OS / 架构）

然后停止，不得改用直接 API 调用或自建 launcher。

## Windows

Windows 环境仍通过包内 `scripts/yc-cloud.sh` 入口分发；脚本会转交 CDN 上的 PowerShell launcher。agent 不得自行寻找 `.exe` 缓存路径替代官方入口。

## Non-Goals

本模块不负责：

- 解释 loader / encrypted core 的构建与发布细节
- 指导 agent 修改 manifest、CDN 地址或 SHA256
- 提供 manifest / loader 的手动下载命令
- 把启动脚本逻辑改写成 curl / wget 示例
