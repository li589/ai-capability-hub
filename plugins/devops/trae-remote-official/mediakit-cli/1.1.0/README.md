# MediaKit for TRAE

MediaKit 插件通过 `mediakit-cli` 为 TRAE 提供媒体能力发现、配置检查、本地/云端执行，以及云端异步任务查询指引。

## 能力

- 发现 MediaKit 的 audio、video、image、editing 等领域及工具参数。
- 运行本地或云端媒体处理命令。
- 通过 `shared query-task` 查询云端异步任务。
- 统一处理认证、运行来源标识、输出路径、幂等和错误响应。

## 包结构

```text
mediakit/
├── .trae-plugin/plugin.json
├── connector.json
├── examples/connector-provider-template.json
├── skills/byted-mediakit-shared/
│   ├── SKILL.md
│   └── reference/query_task.md
├── icon.svg
├── README.md
└── LICENSE
```

本插件包含 Skill 与 Connector 声明，不包含 MCP。其运行能力来自用户机器上的 `mediakit-cli`，因此无需为 CLI 本地命令额外声明 MCP。云端认证凭据由 TRAE Connector 托管注入（见下节），CLI 侧仅消费环境变量。

## 依赖

- Node.js 与 npm（用于安装 CLI）
- `@volcengine/mediakit-cli`
- 本地模式按具体能力需要 `ffmpeg` / `ffprobe`
- 云端模式需要有效的 `MEDIAKIT_API_KEY`

安装与验证：

```bash
npm install -g @volcengine/mediakit-cli
mediakit-cli --version
mediakit-cli doctor
```

## 认证和隐私

云端 API Key 通过 TRAE Connector 凭据托管（`manual_token`）注入，不再要求用户手动配置环境变量：

- `connector.json` 声明 `mediakit-cli` Provider（`auth_policy: ON_INVOKE`，首次调用云端能力时弹出授权表单）。
- `.trae-plugin/plugin.json` 的 `env` 将 `${connector.mediakit-cli.ACCESS_TOKEN}` 映射为 `MEDIAKIT_API_KEY`，运行时注入命令进程环境，凭据不落插件包。授权结果为用户账号级、多端复用，云端任务无需每次重新填写。
- `examples/connector-provider-template.json` 为平台侧授权表单模板（弹窗文案、字段、多语言），需单独提交给 TRAE 配置，不会被 `plugin.json` 自动加载。Provider 名称必须与 `connector.json` 中的 `mediakit-cli` 一致。

CLI 侧凭据读取优先级不变：环境变量 > `~/.mediakit/config.json`。`plugin.json.env` 同时固定注入 `MEDIAKIT_SURFACE=plugin` 和 `MEDIAKIT_RUNTIME=trae` 作为请求来源标识。包内不包含 token、secret、private key 或真实用户配置，不会记录或输出 API Key。

## 验证建议

```bash
mediakit-cli --version
MEDIAKIT_SURFACE=plugin MEDIAKIT_RUNTIME=trae mediakit-cli --domains
MEDIAKIT_SURFACE=plugin MEDIAKIT_RUNTIME=trae mediakit-cli shared query-task --schema
```

云端调用的 API Key 由 TRAE Connector 授权表单收集并托管，审核方自测时首次调用云端能力会触发授权弹窗。

## 已知限制

- 插件本身不安装 CLI 或系统媒体依赖。
- `query-task` 仅支持云端模式。
- 可用能力及参数以当前安装版本的 `--schema` 输出为准。

## 来源与许可

本插件基于 MediaKit Skills 的 shared skill 整理，许可证见 `LICENSE`。
