# MCP Validation Checklist (Fallback)

This checklist is used when dynamic documentation fetch fails. May be outdated - prefer fetched standards.

**Last Updated**: 2026-01-17

---

## MCP Overview

Model Context Protocol (MCP) servers extend Claude Code with custom tools via a standardized protocol.

---

## Configuration

### Location

MCP servers are configured in `.claude/mcp.json` or via settings.

### Configuration Format

```json
{
  "mcpServers": {
    "server-name": {
      "command": "node",
      "args": ["path/to/server.js"],
      "env": {
        "API_KEY": "${API_KEY}"
      }
    }
  }
}
```

---

## Transport Types

| Type | Description | Use Case |
|------|-------------|----------|
| `stdio` | Standard input/output | Local servers, scripts |
| `http` | HTTP requests | Remote servers |
| `sse` | Server-Sent Events | Streaming responses |

---

## Tool Definition

MCP servers expose tools with this schema:

```json
{
  "name": "tool-name",
  "description": "What the tool does",
  "inputSchema": {
    "type": "object",
    "properties": {
      "param1": {
        "type": "string",
        "description": "Parameter description"
      }
    },
    "required": ["param1"]
  }
}
```

---

## Critical Rules

- [ ] Configuration JSON is valid
- [ ] Server command/path exists
- [ ] Required environment variables available
- [ ] Tools have valid schemas

## High Priority

- [ ] No secrets hardcoded (use `${ENV_VAR}`)
- [ ] Tool names are unique
- [ ] Descriptions are clear
- [ ] Input schemas are valid JSON Schema

## Medium Priority

- [ ] Server handles errors gracefully
- [ ] Timeout configuration appropriate
- [ ] Resource cleanup on shutdown

## Low Priority

- [ ] Consistent naming conventions
- [ ] Documentation for custom tools
- [ ] Example usage provided

---

## Security Considerations

### Critical

- [ ] No API keys or secrets in config files
- [ ] Use environment variable interpolation: `${API_KEY}`
- [ ] Validate all inputs in server code
- [ ] Limit file system access

### High

- [ ] Network requests only to trusted hosts
- [ ] No command injection vulnerabilities
- [ ] Proper permission scoping

---

## Common Violations

| Violation | Severity | Remediation |
|-----------|----------|-------------|
| Invalid JSON | Critical | Fix JSON syntax |
| Hardcoded secrets | Critical | Use `${ENV_VAR}` |
| Missing server file | Critical | Check path |
| Invalid tool schema | High | Fix JSON Schema |
| Missing descriptions | Medium | Add tool descriptions |
| Missing env vars | High | Set required variables |

---

## Testing MCP Servers

1. Verify server starts without errors
2. Test each tool with valid inputs
3. Test error handling with invalid inputs
4. Verify no secrets in logs
5. Check resource cleanup
