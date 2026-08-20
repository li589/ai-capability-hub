# NOTICE — 相对上游的改动说明

本子技能来自 **[larksuite/meegle-cli](https://github.com/larksuite/meegle-cli) `skills/meegle/`**（MIT），
对齐 CLI 版本 **v1.0.19**，作为 `lark-unified` 飞书套件的按需子技能引入。

原则：**其余文件原样保留，只改真正必须改的部分**（认证流程、与父技能的衔接、实测发现的错误判据）。
业务语义、字段协议、SOP、MQL 语法等一律未改。

## 文件改动总览

| 文件 | 状态 | 说明 |
|------|------|------|
| `SKILL.md` | **已改** | 补 frontmatter；加子技能归属与按需安装前置说明；修正 `workitem +batch-get` 命令名 |
| `references/auth-guard.md` | **已改** | 授权流程由浏览器 OAuth 改为分离式 Device Code；补错误判据 |
| `references/cli-guide.md` | **已改** | 补安装说明、命令注册与登录耦合、退出码判据 |
| 其余 17 个 `references/*.md` | 未改 | 与上游逐字节一致 |

新增的 `scripts/meegle_status.py`（预检）与 `scripts/meegle_setup.py`（非 TTY 登录）为本套件原创，
不属于上游内容。

未改动的文件：`api-examples.md`、`attachment.md`、`error-handling.md`、`field-value-extras.md`、
`misc.md`、`mql-syntax.md`、`performance.md`、`rich-text-editor-markdown-syntax.md`、
`sop-create-workitem.md`、`sop-transition-node.md`、`sop-transition-state.md`、
`sop-update-workitem.md`、`url-kinds.md`、`view.md`、`wbs.md`、`workflow.md`、`workitem.md`。

## 逐项改动理由

### 1. `SKILL.md` — frontmatter、归属与命令名修正

上游该文件只有 `name` + `description` 两个字段。补上 `version` / `parentSkill` /
`allowed-tools` / `metadata.requires.bins` 后，宿主才能识别它是子技能、依赖哪个二进制。

同时加了两段说明：

- **产品边界**：`meegle` 与 `lark-cli` 是两个产品，二进制和凭据都不共享。请求走错产品时回父技能
  第 0 节重新分流。
- **按需安装前置**：`meegle` 不随套件默认安装。

**命令名修正**：上游写作 `workitem batch-get`，真实注册名是 **`workitem +batch-get`**（别名
`+get-batch`）。`+` 前缀标记客户端封装命令（背后没有 1:1 的 MCP tool），见
`internal/products/meegle/batch.go` 的 `Name: "+batch-get"` 与 `batch_test.go` 的断言。同类的
`attachment +upload` / `attachment +download` 上游写对了。照上游抄会得到 `unknown command`。

### 2. `references/auth-guard.md` — 授权流程重写（最实质的改动）

**上游 STEP 2 在 Agent 环境中必然失败。** 上游写的是：

```bash
meegle auth login --host $host        # 「命令会自动打开浏览器完成 OAuth 授权」
```

该路径走 Authorization Code 流程，需要真实 TTY 和一个浏览器能回调的本地 HTTP 端口。CLI 自己在
`internal/products/meegle/commands/auth.go` 里就显式拒绝了这种环境：

```go
if !deviceCode && !term.IsTerminal(int(os.Stdin.Fd())) {
    return meerrors.NewClientError("INTERACTIVE_BROWSER_REQUIRED", ...)
}
```

而同一个 CLI **已经提供了**更适合 Agent 的分离式设备码流程（`--phase init` / `--phase poll`），
上游 skill 通篇没有提到。改动后按实测形状重写：

-新增 **STEP 0**：先确认二进制存在，缺失则回父技能按需安装。
- **STEP 2** 改为 `auth login --device-code --phase init`，输出授权链接后**结束回复轮次**，
  避免在同一轮里既展示链接又阻塞轮询（中间输出被折叠时用户根本看不到链接）。
- 新增 **STEP 3**：`--phase poll --once` 换取 token。
- 补 `auth status` 未登录时的真实输出形状（上游示例里的 `source` / `expires_in_minutes` 字段在未登录
  时实际不出现，返回的是 `{"authenticated":false,"host":null,"reason":"no local token"}`）。
- 补错误处理：`unknown command` 可能只是未登录（见下）；浏览器流程报
  `INTERACTIVE_BROWSER_REQUIRED` 时不要重试。

### 3. `references/cli-guide.md` — 命令发现与退出码

新增两节，都来自实测：

- **命令注册与登录耦合**：未登录时Meegle 只注册 `auth` / `config` / `url` / `inspect` /
  `completion` / `version`，调用业务命令返回 `unknown command "workitem" for "meegle"`（退出码 1）——
  **与命令真的不存在时的报错文本、退出码完全相同**。不写清楚，Agent 会把「没登录」误判成「命令名错」
  并开始瞎猜命令名。
- **退出码**：两处退出码不反映真实状态的坑：
  - `auth login --phase poll --once` 在用户尚未授权时输出 `{"status":"authorization_pending"}` 却
    返回**退出码 0**，必须读 `status` 字段；
  - 未登录时 `inspect` 返回 `No commands available ...` 也是**退出码 0**。
  - 另外强调必须同行捕获退出码（`OUT=$(cmd); RC=$?`），管道后取 `$?` 拿到的是管道末端命令的状态。

「前置条件」一节补了安装命令，并说明 `--no-skills` 为何必需（官方向导默认 `skills add` 会往全局技能
目录再装一份 meegle 技能，与本子技能重复）。

## 实测环境

- `meegle` v1.0.19（`@lark-project/meegle`）
- 设备码 `--phase init` 对 `project.feishu.cn` 发出真实请求并成功返回授权链接
- 未登录状态下逐一验证了 `--help` / `workitem --help` / `auth status` / `inspect` / `config show`
  的输出与退出码
- 配置与 token 目录硬编码在 `$HOME/.meegle`（`internal/products/meegle/config.go`、
  `auth/file_store.go`），**没有**配置目录环境变量，测试隔离靠改写 `HOME` 实现
