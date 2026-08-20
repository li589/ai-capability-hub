---
name: pipeworx-patents
description: Patents MCP — wraps PatentsView API (https://api.patentsview.org/)
version: 1.0.0
metadata:
  openclaw:
    homepage: https://pipeworx.io/packs/patents
install_source: official
install_method: download
skill_id: official_uxg84U2I
enabled_at: 1787231779527
name_zh: 专利数据服务
---

# pipeworx-patents

Patents MCP — wraps PatentsView API (https://api.patentsview.org/). Free, no API key. Part of [Pipeworx](https://pipeworx.io).

## Tools

- `search_patents`
- `get_patent`
- `search_inventors`

## Connect

```json
{
  "mcpServers": {
    "pipeworx-patents": {
      "command": "npx",
      "args": ["-y", "mcp-remote@latest", "https://gateway.pipeworx.io/patents/mcp"]
    }
  }
}
```

More at [pipeworx.io/packs/patents](https://pipeworx.io/packs/patents)
