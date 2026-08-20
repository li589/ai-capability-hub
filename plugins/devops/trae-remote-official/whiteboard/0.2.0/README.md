# 画板（Whiteboard）TRAE Plugin

画板是一款可编辑图示插件。用户只需描述想法，即可创建、调整并交付架构图、流程图、思维导图、时间线、泳道图和视觉化总结。

默认交付一个自包含、可继续编辑的 Whiteboard HTML；`.excalidraw` 保留为源文件。只有用户明确要求仅提供源文件时，才省略 HTML。

## 目录

```text
whiteboard/
├── .trae-plugin/
│   └── plugin.json
├── skills/
│   └── whiteboard-design/
│       ├── SKILL.md
│       ├── assets/
│       ├── references/
│       └── scripts/
├── icon.svg
├── README.md
├── LICENSE
└── THIRD_PARTY_NOTICES.md
```

## 运行要求

- Node.js 18 或更高版本
- 允许启动本地子进程并访问 `127.0.0.1`
- 首次执行 Whiteboard 命令时可访问 npm Registry
- 用户工作区具有写入权限，用于保存场景和 HTML

插件默认采用无需浏览器的快速生成、校验和 HTML 构建流程。只有用户明确要求预览、截图，或内容存在浏览器兼容性要求时，才启动本地 Whiteboard Workbench。

## 依赖与能力边界

主题工具、HTML 生成器和编辑器模板已随插件打包。受控命令入口首次执行时通过 `npx` 获取固定版本的 `mcp-excalidraw-server@1.1.0`，因此需要网络连接和可写的临时缓存目录。

插件为 Skills-only，不注册 `.mcp.json` 或 `connector.json`，也不包含 Remote MCP、OAuth Connector、访问令牌或第三方服务凭据。

## 来源与许可

插件本体为 `UNLICENSED`；所含第三方组件的许可信息见 `THIRD_PARTY_NOTICES.md`。
