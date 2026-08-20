# 安装指导

**仅在执行购物操作时发现工具不可用才需要安装**，平常正常使用不必触发：

- CLI 方式：PATH 中的 `utp` 不存在，或执行报 `command not found`
- MCP 方式：环境中找不到 `utp` MCP Server，或 MCP 工具调用失败

安装完成后回到原本的购物流程继续执行，不要因为安装打断用户。

---

## CLI 安装（npm 全局安装，主路径）

CLI 通过 npm 全局安装：

```bash
npm i -g @ut-protocol/utp
```

安装后，`utp` 位于 npm 全局 bin 目录（通常为 `npm config get prefix`/bin/utp）。

本 skill **自带跨平台安装脚本**，一行搞定上述安装 + `utp install`：

**macOS / Linux**：
```bash
bash <skill-dir>/scripts/install.sh
```

**Windows（Git Bash）**：
```bash
bash <skill-dir>/scripts/install-win.sh
```

- 脚本幂等，重复运行会升级为最新版本。
- 脚本会自动探测目标 Host，并通过 `utp install` 写入 Skill 文件与 MCP 配置。
- **加 `--reset`** 可清除 `~/.utp/` 本地数据和各 Host 的 skill 目录/MCP 配置，然后全新安装。

**手动安装 CLI**：若只想装 CLI 本身，执行上面的 `npm i -g` 命令即可。

---

## MCP Server 配置

MCP 方式依赖 `utp` CLI（MCP Server 由 CLI 启动），请先完成上面的 CLI 安装。

MCP 是面向用户的**唯一主路径**。Server 未接入时，Agent 应**主动帮用户完成接入**——可直接读写当前 Host 的 MCP 配置文件，无需让用户手动操作。配置的**位置和格式因 Host 而异**（Claude Code、Cursor、Claude Desktop 等各不相同），由 Agent 按所在 Host 判断格式，把下面这台 server 写进去：

| 项 | 值 |
|----|----|
| Server 名称 | `utp`（Host 可加前缀，以环境中可用的为准） |
| 启动命令 | `utp`（npm 全局安装后在 PATH 中；安装脚本会自动写入解析后的绝对路径） |
| 启动参数 | `mcp serve`（可选追加 `--session-id <id>`） |
| 传输方式 | stdio |
| 环境变量 | 无 |

> 安装脚本会自动解析 npm 全局 bin 的绝对路径并写入 MCP 配置，无需手动填写。若手动配置，确保路径指向 npm 全局安装的 `utp` 可执行文件。

配置样例（以 JSON 类 Host 为例，实际键名/结构按所在 Host 调整）：

```json
{
  "mcpServers": {
    "utp": {
      "command": "utp",
      "args": ["mcp", "serve"]
    }
  }
}
```

Agent 应**主动**用当前 Host 的标准 MCP 接入手段（配置文件、接入命令、扩展面板等）完成接入。**写完配置后必须引导用户重新加载 MCP server**——改配置只是落盘，server 不会自动启动，绝大多数 Host 需用户手动重载/重启才会加载新 server（Claude Code：`/mcp` 重连或重启会话；Cursor：设置里 reload/toggle 该 server；其它 Host 按其方式）。按所在 Host 给出对应重载方式，用户重载后即走 MCP。

**仅当**确实无法接入（Host 不支持 MCP、无权限改配置、或反复接入失败）才回退 CLI 兜底，并把上表接入信息清楚告知用户以便其手动配置——不要主动向用户提议走 CLI。

---

## 渠道门禁

渠道门禁已移除。所有 host 均无需额外配置即可访问。
