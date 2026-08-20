---
name: create-plugin
description: >-
  Create a Qoder-native plugin directory from an external or local source.
  Convert GitHub SKILL.md files, local SKILL.md files, Qoder marketplace skill
  URLs, skills.sh entries, pasted Skill content, or existing plugin-like
  folders into distributable Qoder-native plugins.
---

# Create Plugin

Create a Qoder-native plugin directory from an external or local source. The
goal is a copyable, valid, distributable plugin package, not a standalone
`SKILL.md` dump.

ARGUMENTS: GitHub URL, raw `SKILL.md` URL, Qoder marketplace skill URL, local
file/directory, `www.skills.sh` entry, pasted `SKILL.md`, existing plugin-like
folder, or target plugin name.

## Core Workflow

1. Resolve the source and provenance.
   - Normalize noisy URLs such as full-width `Https：//` into normal URLs.
   - Find the real `SKILL.md` file and same-directory support files.
   - For GitHub, Qoder marketplace, skills.sh, local paths, and pasted content,
     follow `references/source-resolution.md`.
2. Decide the plugin shape before writing files.
   - Default to one user-visible skill for one coherent workflow.
   - Create multiple skills only when the source contains multiple independent,
     user-invocable workflows or a clear internal helper skill.
   - Treat Qoder agents, rules, hooks, commands, and MCP as optional plugin
     components, not as reasons by themselves to split the skill.
   - Follow `references/qoder-components.md` for component packaging.
3. Create the Qoder plugin skeleton.
   - Always create `.qoder-plugin/plugin.json`, `README.md`, and `skills/`.
   - Create `assets/`, `rules/`, `agents/`, `commands/`, `hooks/`, `mcp.json`,
     `CONNECTORS.md`, or `canvases/` only when they are actually needed.
4. Copy and adapt `SKILL.md`.
   - Preserve the source workflow, trigger conditions, references, safety
     constraints, and support-file relationships.
   - Keep relative links valid by copying or rewriting referenced
     `references/`, `scripts/`, `assets/`, templates, or examples.
   - Record any omitted or missing support files in `README.md`; do not fake
     evidence or invent referenced files.
5. Write `plugin.json`.
   - Use the manifest rules and examples in
     `references/qoder-plugin-manifest.md`.
   - Declare only components that exist in the generated plugin.
6. Write `README.md`.
   - Include what the plugin does, source provenance, logo provenance, included
     skills/support files, omitted files and why, setup notes, and validation
     evidence.
7. Validate offline first, then run optional Qoder smoke tests only when useful.
   - Follow `references/validation-and-packaging.md`.

## Hard Rules

- Generate Qoder plugin structure only. Do not create `.codex-plugin`,
  `.cursor-plugin`, or `.claude-plugin` mirrors unless the user explicitly asks
  to keep them as reference files; even then, never use them as the Qoder
  manifest.
- `.qoder-plugin/plugin.json` must exist.
- The plugin root directory and `plugin.json.name` must use the same
  normalized kebab-case name.
- Manifest component paths must start with `./`, stay inside the plugin root,
  and point to files or directories that actually exist.
- JSON paths end in `.json`; Markdown command sources end in `.md`.
- Do not declare `hooks`, `mcpServers`, `commands`, `rules`, `agents`, `skills`,
  or `logo` unless the referenced files were created or copied.
- Do not hard-code private credentials. Use placeholders, `CONNECTORS.md`, or
  setup notes for personal tokens, MCP endpoints, SaaS accounts, or connector
  requirements.
- Do not include local runtime state such as `.qoder/settings.local.json`,
  `.DS_Store`, `__MACOSX/`, temporary downloads, caches, or smoke-test settings
  in the final package.
- Do not convert Canvas into a mandatory output. Use Canvas only when the user
  asks for an interactive UI or when the source workflow produces reports,
  graphs, dashboards, logs, design contracts, workflow state, or other artifacts
  that benefit from inspection.
- Keep the source's meaningful constraints. Do not flatten a domain-specific
  workflow into generic marketing copy.

## Skill Split Policy

Use a single skill when:

- The source has one primary user task, even if it also ships scripts,
  references, hooks, rules, agents, commands, or MCP.
- The optional components support the same workflow.
- Splitting would force users to choose between implementation details instead
  of intent.

Use multiple skills when:

- The source exposes multiple independent workflows with different triggers,
  inputs, outputs, or safety constraints.
- Different user roles would naturally invoke different capabilities.
- One skill is an internal reference/helper and should be hidden or invoked only
  by another skill.
- The source already has multiple well-scoped `SKILL.md` files.

When multiple source skills are found in a local directory, list candidates and
ask the user to choose unless their request clearly asks to package the whole
plugin. Do not merge unrelated skills into one large file.

## Target Layout

```text
<plugin-name>/
  .qoder-plugin/plugin.json
  README.md
  assets/logo.<ext> or assets/avatar.svg
  skills/<skill-name>/SKILL.md
  skills/<skill-name>/references/        # copied only when referenced
  skills/<skill-name>/scripts/           # copied only when referenced
  rules/                                 # optional
  agents/                                # optional
  commands/                              # optional
  hooks/hooks.json                       # optional
  mcp.json                               # optional
  CONNECTORS.md                          # optional setup notes
  canvases/<surface>/                    # optional Canvas surface
```

For project-local discovery while developing this repo, a plugin may also keep
`.qoder/skills -> ../skills` or another explicit alias, but do not duplicate a
second copy of `SKILL.md`.

## Name Rules

Use these defaults:

- Plugin folder: normalized kebab-case `<plugin-name>`.
- `plugin.json.name`: same normalized `<plugin-name>`.
- `plugin.json.displayName`: human-readable name in the user's/source language.
- Skill folder: source skill name when safe; otherwise a normalized readable id.
- Skill frontmatter `name`: match the skill folder unless preserving the source
  name is important for compatibility.

Normalization for technical identifiers:

- lower-case
- spaces, underscores, and punctuation become `-`
- repeated `-` collapse to one
- trim leading/trailing `-`
- keep under 64 characters when practical

For Chinese sources, keep user-facing display text in Chinese, but keep plugin
directory and manifest `name` as technical kebab-case.

## Minimal Manifest

Use this as the default shape and extend only with real components:

```json
{
  "name": "<plugin-name>",
  "displayName": "<Display Name>",
  "version": "0.1.0",
  "description": "<one sentence in English>",
  "descriptionZh": "<一句话中文描述>",
  "author": { "name": "<author or Qoder>" },
  "homepage": "<source or plugin homepage>",
  "repository": "<source repo when known>",
  "logo": "./assets/avatar.svg",
  "keywords": ["qoder-plugin", "skill"],
  "category": "developer-tools",
  "tags": ["skill"],
  "skills": "./skills/"
}
```

Add these fields only when the corresponding files exist:

- `"rules": "./rules/"`
- `"agents": "./agents/"`
- `"commands": "./commands/"` or a commands object
- `"hooks": "./hooks/hooks.json"`
- `"mcpServers": "./mcp.json"`

`interface` is optional. Add it only when the user explicitly wants marketplace
or UI presentation metadata, or the target publishing process requires it.

## Optional Canvas

If the user wants an interactive UI, or the converted plugin produces artifacts
that should be inspected visually, tell the user the plugin can be extended with
Qoder Canvas. Use Qoder's `/canvas` skill to create or adapt the Canvas UI
instead of inventing the Canvas runtime inside this conversion skill.

Keep Canvas narrow and artifact-driven. A good surface previews a concrete
plugin output such as a report, graph, design contract, dashboard data file, log
summary, or workflow state. Do not create a decorative landing page or generic
marketing UI.

## Validation

Always run the bundled offline validator before handing back a generated plugin:

```bash
python3 create-plugin/skills/create-plugin/scripts/validate_qoder_plugin.py <plugin-root-or-zip>
```

When running from the skill directory itself:

```bash
python3 scripts/validate_qoder_plugin.py <plugin-root-or-zip>
```

Run `qodercli` checks only when available and relevant to the user's requested
proof level. For install, discovery, MCP, command, zip, and cleanup details, use
`references/validation-and-packaging.md`.

## Output Summary

Finish with:

```markdown
### Qoder Plugin
- **Plugin**: <absolute plugin root>
- **Skill(s)**: <absolute skills/<skill-name>/SKILL.md or list>
- **Source**: <url/path/pasted content>
- **Copied Support Files**: <files or none>
- **Omitted**: <platform-specific or missing files>
- **Validation**: <commands run and result>
```

## References

- `references/source-resolution.md` - GitHub, Qoder marketplace, skills.sh,
  local path, and pasted-content resolution.
- `references/qoder-plugin-manifest.md` - manifest fields, paths, and
  component declaration rules.
- `references/qoder-components.md` - when and how to package skills, agents,
  rules, hooks, commands, MCP, connectors, and Canvas.
- `references/validation-and-packaging.md` - offline validation, optional
  install smoke, zip packaging, and cleanup.
