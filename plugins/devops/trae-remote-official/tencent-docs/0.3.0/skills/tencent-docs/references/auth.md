# 腾讯文档授权

腾讯文档插件通过 Trae connector 完成授权。插件中的四个 MCP 服务共用同一份腾讯文档访问令牌，无需安装命令行工具或写入本地 MCP 配置。

## 授权流程

1. 在 Trae 插件详情页找到腾讯文档连接器。
2. 点击“连接”，在浏览器中完成腾讯文档授权。
3. 返回 Trae，等待连接状态更新为已连接。
4. 直接执行用户请求。Trae 会把授权信息注入 `tencent-docs`、`slide-mcp`、`doc-mcp` 和 `sheet-mcp`。

若调用工具时提示未授权或 Token 失效，引导用户回到插件详情页重新连接。不要要求用户在对话中粘贴 Token，也不要把 Token 写入文件、命令行参数或日志。

## 服务与能力

| MCP 服务 | 能力 |
|---|---|
| `tencent-docs` | 文件管理、空间、智能文档、智能表格、OCR、网页剪藏 |
| `slide-mcp` | PPT 页面、形状、文本、表格、图表、动画和主题 |
| `doc-mcp` | Word 文档内容与格式精细编辑 |
| `sheet-mcp` | Excel 单元格、区域、图表、筛选、透视表等操作 |

## 常见错误

| 错误 | 处理方式 |
|---|---|
| `400006` / Token 鉴权失败 | 回到 Trae 插件详情页断开后重新连接腾讯文档 |
| `400007` / VIP 权限不足 | 引导用户访问腾讯文档 VIP 页面确认权限 |
| `400008` / 积分不足 | 引导用户访问腾讯文档资产中心确认积分 |
| 连接器未连接 | 在 Trae 插件详情页完成腾讯文档授权 |
| 网络错误 | 检查网络后重试；不要改写或暴露授权信息 |

VIP 页面：
https://docs.qq.com/vip?immediate_buy=1?part_aid=persnlspace_mcp

积分页面：
https://docs.qq.com/vip/asset-center?tab=ai
