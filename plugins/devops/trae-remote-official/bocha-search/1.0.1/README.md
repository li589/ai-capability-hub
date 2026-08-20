# 博查搜索 TRAE Plugin

通过 OAuth 2.0 将博查搜索接入 TRAE。安装并完成授权后，TRAE 会将 OAuth access token 放入访问博查 Remote MCP 的 `Authorization` 请求头；插件包不包含 API Key、access token、OAuth client secret 或其他测试凭据。

## 包含内容

- OAuth Connector：`bocha-oauth`，在安装时发起授权。
- Remote MCP：`https://mcp.bochaai.com/mcp`。
- Skill：帮助代理在需要联网检索时正确使用博查搜索工具。

## 使用方式

1. 在 TRAE 中安装此插件。
2. 按授权页面指引登录博查并确认授权。
3. 授权完成后，直接在 TRAE 中提出需要联网检索的问题。可用工具和参数以 Remote MCP 返回的 `tools/list` 为准。

授权结果由 TRAE 的 `bocha-oauth` Connector 保存。插件通过 HTTP 请求头引用 `${connector.bocha-oauth.ACCESS_TOKEN}`；无需也不应配置本地环境变量或手动粘贴 API Key。

## 平台配置要求

TRAE 市场需为 `bocha-oauth` 配置 OAuth Provider Template。博查通过安全渠道提供 `client_id`、`client_secret`、授权端点、令牌端点、撤销端点及精确的回调地址。客户端使用 Authorization Code Grant 和 `client_secret_basic`，access token 有效期为 30 天；到期后请重新授权。

## 安全与隐私

- 本插件仅访问 `https://mcp.bochaai.com/mcp`。
- 请勿在问题、日志、截图、提交包或代码中记录 access token、authorization code、API Key 或 client secret。
- 撤销授权或令牌失效后，重新连接即可再次完成授权。

## 发布校验

从干净目录构建发布包，且仅包含 `.trae-plugin/plugin.json`、`.mcp.json`、`connector.json`、`skills/`、`icon.svg`、`README.md` 与 `LICENSE`。不要将服务端源码、部署文件、软链接、`.idea`、临时文件或任何凭据打入 zip。

在项目根目录执行以下命令生成提交给 TRAE 的 zip：

```bash
make package
```

压缩包会输出到 `dist/bocha-search-<version>.zip`。该命令会检查必需文件、拒绝软链接，并在创建后验证 zip 只包含发布白名单中的文件。
