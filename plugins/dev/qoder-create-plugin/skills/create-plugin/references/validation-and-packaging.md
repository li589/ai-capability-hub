# Validation And Packaging

Validate generated plugins offline first. Use Qoder runtime checks only when
they add the proof the user asked for.

## Offline Validator

From this repository root:

```bash
python3 create-plugin/skills/create-plugin/scripts/validate_qoder_plugin.py <plugin-root-or-zip>
```

From the `create-plugin/skills/create-plugin` skill directory:

```bash
python3 scripts/validate_qoder_plugin.py <plugin-root-or-zip>
```

The validator checks:

- `.qoder-plugin/plugin.json` exists and is valid JSON.
- Required manifest fields `name` and `version` exist.
- Manifest component paths stay inside the plugin root.
- Declared `skills`, `commands`, `mcpServers`, `hooks`, `rules`, `agents`, and
  `logo` point to existing files or directories.
- Every declared `SKILL.md` has frontmatter with `name` and `description`.
- Command sources exist and use Markdown files.
- MCP JSON exists and contains server definitions.
- Plugin zip roots contain `.qoder-plugin/plugin.json` directly.
- Local runtime state and non-Qoder manifest directories are not packaged.

If the bundled validator is unavailable, run equivalent static checks:

```bash
test -f <plugin-name>/.qoder-plugin/plugin.json
test -f <plugin-name>/skills/<skill-name>/SKILL.md
python3 -m json.tool <plugin-name>/.qoder-plugin/plugin.json >/dev/null
```

Then manually check that all manifest paths start with `./`, contain no `..`,
and point to existing files.

## Optional qodercli Compatibility Check

If `qodercli` is available, this is an additional compatibility check:

```bash
qodercli plugin validate "$(pwd)/<plugin-name>"
```

To verify project discovery from the plugin root before installation:

```bash
qodercli --cwd "$(pwd)/<plugin-name>" --setting-sources project skills list
```

The success signal is that each converted skill appears in the list.

Treat `qodercli plugin validate` as compatibility evidence, not as the package
quality gate. It may accept convention-only directories that do not contain
`.qoder-plugin/plugin.json`, and local install may still produce no discoverable
skills. The offline validator is intentionally stricter for generated packages:
it requires the Qoder manifest, declared component paths, and real `SKILL.md`
frontmatter before a plugin is considered ready.

## Optional Install Smoke Test

Run install smoke only when the user asks for install verification, trigger
verification, MCP/command discovery, or end-to-end proof.

Use a temporary cwd and local scope by default:

```bash
PLUGIN_ROOT="$(pwd)/<plugin-name>"
SMOKE_CWD="$(mktemp -d)"
qodercli --cwd "$SMOKE_CWD" plugin install --scope local "$PLUGIN_ROOT"
qodercli --cwd "$SMOKE_CWD" plugin list --json
```

Confirm:

- plugin name matches `<plugin-name>`
- status is enabled
- installed scope matches the requested scope
- version matches `.qoder-plugin/plugin.json`

Validate declared components:

```bash
# Skills
qodercli --cwd "$SMOKE_CWD" skills list

# MCP servers, only when plugin.json declares mcpServers and mcp.json exists
qodercli --cwd "$SMOKE_CWD" mcp list

# External commands, only when plugin.json declares commands and commands exist
qodercli --cwd "$SMOKE_CWD" external list
```

Success signals:

- Each copied skill appears in `qodercli skills list`.
- Each declared MCP server appears in `qodercli mcp list`.
- Each declared command appears in `qodercli external list`.

If an MCP server requires credentials or network access, discovery is enough
unless the user explicitly asks for invocation. If a command mutates files,
deploys, publishes, deletes, or spends credits, do not run it without explicit
approval.

Clean up temporary installs:

```bash
qodercli --cwd "$SMOKE_CWD" plugin uninstall --scope local <plugin-name>
```

Only leave the plugin installed when the user asked to keep it installed.

## Zip Packaging

Zip only when the user asks for a distributable archive:

```bash
cd <plugin-name>
zip -r "../<plugin-name>-<version>.zip" . \
  -x "**/.DS_Store" "__MACOSX/*" ".qoder/settings.local.json" ".qoder/**"
```

The zip root must contain `.qoder-plugin/plugin.json` directly.

Validate the zip after creating it:

```bash
python3 create-plugin/skills/create-plugin/scripts/validate_qoder_plugin.py <plugin-name>-<version>.zip
```
