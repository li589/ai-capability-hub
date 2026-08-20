# Codex Conversion Notes: linear

- Source path: /home/bytedance
- Source had .app.json: yes
- Source had skills: yes
- Source had .mcp.json: no
- Inferred MCP source: claude:claude-plugins-official/external_plugins/linear/.mcp.json
- Unresolved app connector: no

## Generated Shape

- Original Codex plugin files are copied as-is, including `.codex-plugin/` and `.app.json` when present.
- `.trae-plugin/plugin.json` is generated from `.codex-plugin/plugin.json` with unsupported app references removed.
- `connector.json` is generated for remote HTTP MCP servers.
- `.mcp.json` Authorization headers reference the generated connector keys.
