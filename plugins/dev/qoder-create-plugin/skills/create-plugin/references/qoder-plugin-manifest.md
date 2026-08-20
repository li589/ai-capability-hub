# Qoder Plugin Manifest

Write `.qoder-plugin/plugin.json` with only the fields needed for the generated
plugin. Keep paths local, explicit, and backed by real files.

## Required Defaults

The smallest valid generated manifest should include `name`, `version`, and
the components the plugin actually ships. For skill conversions, prefer:

```json
{
  "name": "<plugin-name>",
  "displayName": "<Display Name>",
  "version": "0.1.0",
  "description": "<one sentence in English>",
  "descriptionZh": "<一句话中文描述>",
  "author": {
    "name": "<author or Qoder>"
  },
  "homepage": "<source or plugin homepage>",
  "repository": "<source repo when known>",
  "logo": "./assets/avatar.svg",
  "keywords": ["qoder-plugin", "skill"],
  "category": "developer-tools",
  "tags": ["skill"],
  "skills": "./skills/"
}
```

## Path Rules

- Component paths must start with `./`.
- Component paths must not contain `..`.
- Component paths must not be absolute.
- JSON component paths must end in `.json`.
- Markdown command sources must end in `.md`.
- Prefer local assets over remote logo URLs. If a remote URL is the only
  available source, download the asset or use a generated local fallback.

## Component Fields

Add these only when the corresponding files exist:

```json
{
  "rules": "./rules/",
  "agents": "./agents/",
  "commands": "./commands/",
  "hooks": "./hooks/hooks.json",
  "mcpServers": "./mcp.json"
}
```

For commands, either a directory or command object is acceptable when the files
exist. Keep command sources as Markdown files.

## Naming

- Plugin folder and `plugin.json.name` must match.
- Use normalized kebab-case for `plugin.json.name`.
- Use a readable, source-language display name for `displayName`.
- Keep `description` concise and in English when possible.
- Add `descriptionZh` when the source or user request is Chinese.

## Interface Metadata

`interface` is optional. Do not add marketplace/UI presentation fields just to
make the manifest look richer. Add them only when the user explicitly requests
marketplace presentation metadata or the publishing process requires it.

## Unsupported Or Unsafe Content

Do not include:

- `.codex-plugin`, `.cursor-plugin`, or `.claude-plugin` as active manifests.
- Placeholder TODOs in manifest fields.
- Private local paths, credentials, personal tokens, or account-specific MCP
  endpoints.
- Component declarations whose target files were omitted.
- Local runtime state such as `.qoder/settings.local.json`, `.DS_Store`,
  `__MACOSX/`, caches, temporary downloads, or smoke-test settings.

## Preserving Upstream Metadata

For imports where the user explicitly wants the upstream project preserved
as-is, do not rewrite upstream implementation files just to satisfy Qoder
frontmatter rules. Add Qoder-specific wrappers under `.qoder-plugin/` and keep
the upstream files intact.

Preserve upstream repository and platform metadata such as `.github/`,
`.claude/`, `.claude-plugin/`, `.cursor-plugin/`, `.cursor-mcp.json`,
`.gemini/`, and `.plugin/` when they exist. These files are retained as upstream
content; they are not automatically Qoder component declarations.

If the upstream project intentionally ships `.cursor-plugin` or
`.claude-plugin`, set:

```json
{
  "preserveUpstreamMetadata": true
}
```

This opt-in only allows `.cursor-plugin` and `.claude-plugin` through the local
validator. It does not allow `.codex-plugin` or local runtime state.

If upstream hooks are specific to another runtime, preserve them as upstream
files. Do not activate them as Qoder hooks unless they have been verified to run
correctly in Qoder. When Qoder convention loading would otherwise pick them up,
add a Qoder-specific wrapper or empty hook map under `.qoder-plugin/` and point
the manifest `hooks` field there.
