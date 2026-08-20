# Qoder Components

Use this reference when the source includes more than a plain skill. Qoder
plugins can package skills, commands, and MCP capabilities; this conversion
workflow also preserves compatible local plugin directories for agents, rules,
hooks, connectors, and optional Canvas surfaces when they are real source
components.

When adapting a scaffold from another ecosystem, distinguish real component
content from placeholders. Empty directories, empty MCP/app manifests, and
template-only metadata are provenance, not Qoder capabilities. Document them in
README when useful, but do not declare them in `.qoder-plugin/plugin.json`.

## Skills

Use skills for reusable task workflows and domain expertise. A skill should have
one clear trigger surface and a `SKILL.md` with `name` and `description`.

Create multiple skills only when workflows are independently invocable. Do not
split because a workflow happens to mention agents, rules, hooks, MCP, or
commands.

Recommended frontmatter:

```yaml
---
name: <skill-name>
version: 1.0.0
description: What this skill does in English
description_zh: 这个技能做什么的中文描述
user-invocable: true
argument-hint: <expected input>
---
```

If a source skill is internal reference material rather than a user command,
preserve that intent and keep it separate from user-visible workflows.

## Custom Agents

Use `agents/` when the source defines a specialized subagent with its own
system prompt, tool permissions, model choice, skill allow-list, or MCP
allow-list.

Package custom agents as Markdown files such as:

```text
agents/code-review.md
```

The agent file should keep frontmatter fields such as `name`, `description`,
`tools`, `model`, `skills`, and `mcpServers` when they are present and safe.
Keep referenced skill and MCP names aligned with the generated plugin.

Do not turn an agent prompt into a separate skill unless users should invoke it
directly as a standalone workflow. If the agent is only an execution role behind
the main plugin workflow, keep it in `agents/`.

Reference: https://docs.qoder.com/extensions/subagent

## Rules And AGENTS.md

Use `rules/` when the source includes project standards, coding conventions,
file-specific constraints, or model-selection context that should be injected as
rules rather than invoked as a task.

Use rules for:

- project-wide standards
- file-pattern-specific guidance
- scenario guidance that the model should decide to apply
- manually applied prompts that are not full workflows

Keep `AGENTS.md` compatibility in mind: if a source repo already has
`AGENTS.md`, do not blindly duplicate the same content into both `AGENTS.md`
and rules. Prefer the packaging format requested by the user, and document the
source of truth in README.

Qoder rules are stored under `.qoder/rules` for projects, have a documented
100,000-character active-content limit, support natural language only, and
take precedence over `AGENTS.md` on conflicts. Keep rules concise and do not
put scripts, images, or link-only content there.

Reference: https://docs.qoder.com/user-guide/rules

## Hooks

Use `hooks/` only for deterministic lifecycle automation that should run during
agent execution, such as blocking dangerous commands, linting after edits,
logging failures, or notifications.

Package hooks as:

```text
hooks/hooks.json
hooks/<script>.sh
```

`plugin.json` should declare:

```json
{
  "hooks": "./hooks/hooks.json"
}
```

Hook scripts receive JSON on stdin and communicate through exit codes:

- `0`: allow/continue
- `2`: block when the event is blockable
- other: non-blocking error

Prefer portable scripts. Make scripts executable when the filesystem supports
it. Do not package hooks that depend on another product runtime or local-only
paths without documenting the limitation.

Reference: https://docs.qoder.com/extensions/hooks

## MCP

Use `mcp.json` when the source needs external tools or data exposed through MCP.
Qoder supports STDIO for local command tools and SSE/Streamable HTTP for remote
servers.

Package MCP as:

```text
mcp.json
CONNECTORS.md        # when credentials or setup are required
```

`plugin.json` should declare:

```json
{
  "mcpServers": "./mcp.json"
}
```

Keep credentials out of `mcp.json`. Use placeholders such as
`<YOUR_TOKEN>` only when paired with setup instructions in `CONNECTORS.md`.
If an MCP server requires dependencies or environment variables, validate
discovery separately from runtime invocation.

Do not carry over empty scaffold placeholders such as `{ "mcpServers": {} }`.
They can make a directory look installable while providing no usable capability.

Reference: https://docs.qoder.com/user-guide/chat/model-context-protocol

## Commands

Use `commands/` for agent-executable Markdown command files and shortcuts.
Command sources must be `.md` files. Do not execute commands during validation
unless they are safe, non-mutating, and the user asked for runtime proof.

## Connectors

Add `CONNECTORS.md` when the source depends on:

- personal access tokens
- SaaS accounts
- MCP servers requiring environment variables
- organization-specific endpoints
- connectors that the receiving user must configure manually

Keep setup instructions explicit and credential-free.

## Canvas

Use Canvas only when the user asks for an interactive UI or the plugin produces
visual artifacts worth inspecting. Build one narrow Canvas surface around the
plugin's real output. Use Qoder's `/canvas` workflow rather than embedding a
bespoke runtime in this skill.
