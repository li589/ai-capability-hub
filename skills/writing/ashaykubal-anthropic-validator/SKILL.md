---
name: anthropic-validator
description: Validates Claude Code assets (skills, hooks, agents, commands, MCP servers, plugins) against official Anthropic standards. Fetches latest docs dynamically and produces structured validation reports.
user-invocable: true
install_source: official
install_method: download
skill_id: official_NVthR3lQ
enabled_at: 1787231513866
version: 1.0.0
name_zh: 代理报告
---

# Anthropic Validator

Validates Claude Code assets against official Anthropic standards using dynamic documentation fetching and critical analysis.

---

## Overview

### The Problem

Claude Code evolves rapidly. Static checklists become outdated. Assets created months ago may violate current standards, and new features may not be reflected in embedded validation rules.

### The Solution

This skill provides **dynamic validation** by:

1. **Fetching latest standards** from official Claude Code documentation
2. **Critically analyzing** assets against those standards
3. **Producing actionable reports** with specific violations and remediation

### Design Pattern: Main Context Orchestration

This skill uses **Main Context Orchestration** - you (Claude) follow the instructions below to orchestrate sub-agents sequentially. This is required because sub-agents cannot spawn other sub-agents.

```
┌─────────────────────────────────────────────────────────────┐
│                   MAIN CONTEXT (You)                         │
│                                                             │
│  1. Load this skill (anthropic-validator)                   │
│  2. Follow section instructions for asset type              │
│  3. Spawn claude-code-guide → fetch latest standards        │
│  4. Read output (direct response)                           │
│  5. Spawn bulwark-standards-reviewer → analyze asset        │
│  6. Read validation report from logs/validations/           │
│  7. Present summary to user                                 │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Invocation

```bash
# Single asset validation
/anthropic-validator skills/my-skill/SKILL.md

# Batch validation (directory)
/anthropic-validator skills/

# Context inference (validates current file in context)
/anthropic-validator
```

---

## Validation Workflow

### Step 0: Resolve Target Asset

**IMPORTANT**: When this skill is invoked, first resolve what to validate:

```
IF $ARGUMENTS is provided (e.g., /anthropic-validator path/to/file):
    target_path = $1

    IF target_path ends with "/" OR is a directory:
        mode = "batch"
        → Skip to "Batch Validation" section below
    ELSE:
        mode = "single"
        → Continue with Step 1 for single-file validation

ELSE (no arguments, context inference):
    Look for Claude Code assets in recent conversation context
    IF found: validate that asset (single mode)
    ELSE: Ask user what to validate
```

**Argument Reference:**
- `$ARGUMENTS` - Full argument string passed to skill
- `$1` - First positional argument (the path)

**Workflow Routing:**
- Single file → Continue with Steps 1-4 below
- Directory (batch) → Jump to "Batch Validation" section

### Step 1: Determine Asset Type

For the resolved `target_path`, match against these patterns:

| Path Pattern | Asset Type |
|--------------|------------|
| `skills/*/SKILL.md` | Skill |
| `hooks/hooks.json` or `*.hooks.json` | Hooks |
| `agents/*.md` or `.claude/agents/*.md` | Agent |
| `commands/*.md` | Command |
| `mcp/` or `*-mcp-server*` | MCP Server |
| `.claude-plugin/plugin.json` | Plugin |

### Step 2: Fetch Latest Standards

Spawn `claude-code-guide` agent with the appropriate documentation URL:

```
GOAL: Fetch current standards for {asset_type} from official Claude Code docs

CONSTRAINTS:
- Only use official Anthropic documentation
- Report what IS supported vs what is NOT
- Include any recent changes or deprecations

CONTEXT:
- Documentation URL: {see section below for URL}
- Capability being validated: {asset_type}

OUTPUT:
- Current supported fields/features
- Required vs optional elements
- Common pitfalls or mistakes
- Any version-specific notes
```

### Step 2.5: Gather Supporting Files (Skills Only)

For skills, check for supporting subdirectories and files:

```
IF asset_type == "skill":
    1. Check for references/ subdirectory
       - List all files if present
       - Note: references/ is OPTIONAL (not all skills have it)

    2. Check for other common subdirectories
       - examples/, scripts/, templates/, data/
       - List files if present

    3. Scan SKILL.md for file references
       - Look for patterns: `references/*.md`, `examples/*`, etc.
       - Verify referenced files exist

    4. Build supporting_files inventory:
       supporting_files = {
         references: [list of files or "none"],
         examples: [list of files or "none"],
         scripts: [list of files or "none"],
         referenced_but_missing: [any files mentioned but not found]
       }
```

### Step 3: Critical Analysis

Spawn `bulwark-standards-reviewer` agent (Task tool with `subagent_type: bulwark-standards-reviewer`):

```
GOAL: Critically analyze {asset_path} against fetched standards

CONSTRAINTS:
- Be thorough - check every requirement
- Rate findings by severity (Critical/High/Medium/Low)
- Provide specific remediation for each finding
- Do NOT modify the asset, only report
- Only flag missing references/ if the skill explicitly references files that don't exist
- Validate tools/fields against DOCUMENTATION, not by attempting to use them
  (The reviewer may not have access to all tools - don't conflate "I can't use this" with "this is invalid")

CONTEXT:
- Asset to validate: {asset_content}
- Current standards: {fetched_standards from Step 2}
- Asset type: {asset_type}
- Supporting files inventory: {supporting_files from Step 2.5, if skill}
- Referenced files verified: {yes/no with details}
- Known conventions (DO NOT flag as high/critical — classify as informational):
  The following patterns are intentional conventions backed by empirical testing.
  LLM agents reliably ignore behavioral-register instructions ("You always verify...")
  but comply with imperative-register instructions ("You MUST verify..."). These
  patterns have been validated across Opus and Sonnet models. Treat as informational
  only — note the divergence from pure Anthropic style but do NOT elevate severity:
  * Pre-Flight Gate sections with MUST/MUST NOT binding language
  * Imperative Protocol sections (step-by-step operational instructions)
  * Permissions Setup sections documenting settings.json configuration
  * Completion Checklists with checkbox items
  * DO/DO NOT mission sections
  * Tool Usage Constraints with Allowed/Forbidden per tool

OUTPUT:
Write structured YAML to logs/validations/{asset-name}-{timestamp}.yaml
```

### Step 4: Present Results

Summarize findings to user in human-readable format (see Output Format section).

---

## Skills Validation

### Official Documentation

https://docs.anthropic.com/en/docs/claude-code/skills

### Validation Workflow

1. Read the skill's `SKILL.md` file
2. **Check for supporting subdirectories**:
   - `references/` - list files if present (OPTIONAL - not all skills need this)
   - `examples/`, `scripts/`, `templates/`, `data/` - list if present
3. **Verify referenced files** - scan SKILL.md for file mentions (`references/*.md`, etc.) and confirm they exist
4. Spawn `claude-code-guide` with prompt:
   ```
   Fetch current standards for Claude Code skills from https://docs.anthropic.com/en/docs/claude-code/skills
   Focus on: frontmatter fields, SKILL.md structure, user-invocable, agent field, context field
   ```
5. Spawn `bulwark-standards-reviewer` with:
   - Skill content
   - Fetched standards
   - **Supporting files inventory** (list of files in references/, examples/, etc.)
   - **Referenced files verification** (which mentioned files exist/missing)
6. Write report to `logs/validations/`

**Important**: A missing `references/` folder is NOT a violation unless the skill explicitly references files that don't exist. Many skills are self-contained and don't need supporting files.

### Key Validation Points

| Field | Requirement |
|-------|-------------|
| `name` | Required, matches directory name |
| `description` | Required, concise explanation |
| `user-invocable` | Boolean, controls `/` menu visibility |
| `agent` | Optional: `haiku`, `sonnet`, or `opus` for model selection |
| `context` | Optional: `fork` for isolated execution |
| `skills` | Optional: array of skills to load |
| `tools` | Optional: array of allowed tools |

### Fallback Checklist

If doc fetch fails, use: `references/skills-checklist.md`

---

## Hooks Validation

### Official Documentation

https://docs.anthropic.com/en/docs/claude-code/hooks

### Validation Workflow

1. Read the hooks configuration file
2. Spawn `claude-code-guide` with prompt:
   ```
   Fetch current standards for Claude Code hooks from https://docs.anthropic.com/en/docs/claude-code/hooks
   Focus on: hook types, matcher patterns, once field, command format, environment variables
   ```
3. Spawn `bulwark-standards-reviewer` with hooks content and fetched standards
4. Write report to `logs/validations/`

### Key Validation Points

| Field | Requirement |
|-------|-------------|
| Hook types | `PreToolUse`, `PostToolUse`, `SubagentStart`, `SubagentStop`, `Notification` |
| `matcher` | Regex pattern for tool/subagent matching |
| `command` | Shell command to execute |
| `once` | Boolean, `true` for run-once hooks (e.g., SessionStart) |
| `timeout` | Optional, milliseconds |

### Environment Variables

| Variable | Available In |
|----------|--------------|
| `$CLAUDE_TOOL_NAME` | PreToolUse, PostToolUse |
| `$CLAUDE_TOOL_INPUT` | PreToolUse, PostToolUse |
| `$CLAUDE_TOOL_OUTPUT` | PostToolUse |
| `$CLAUDE_SUBAGENT_TYPE` | SubagentStart, SubagentStop |
| `$CLAUDE_SUBAGENT_PROMPT` | SubagentStart |

### Fallback Checklist

If doc fetch fails, use: `references/hooks-checklist.md`

---

## Agents Validation

### Official Documentation

https://docs.anthropic.com/en/docs/claude-code/sub-agents

### Validation Workflow

1. Read the agent markdown file
2. Spawn `claude-code-guide` with prompt:
   ```
   Fetch current standards for Claude Code custom sub-agents from https://docs.anthropic.com/en/docs/claude-code/sub-agents
   Focus on: agent definition format, frontmatter fields, model selection, tools array, lookup priority
   ```
3. Spawn `bulwark-standards-reviewer` with agent content and fetched standards
4. Write report to `logs/validations/`

### Key Validation Points

| Field | Requirement |
|-------|-------------|
| `name` | Required, matches filename |
| `description` | Required, explains agent purpose |
| `model` | Optional: `haiku`, `sonnet`, `opus` |
| `tools` | Optional: array of allowed tools |
| `skills` | Optional: array of skills to load |
| File location | `.claude/agents/`, `~/.claude/agents/`, or plugin `agents/` |

### Agent Lookup Priority

1. CLI flag (`--agent`)
2. `.claude/agents/` (project)
3. `~/.claude/agents/` (user)
4. Plugin `agents/` directory
5. Built-in agents

### Fallback Checklist

If doc fetch fails, use: `references/agents-checklist.md`

---

## Commands Validation

### Official Documentation

https://docs.anthropic.com/en/docs/claude-code/skills (commands merged with skills in v2.1.3)

### Validation Workflow

1. Read the command file
2. Spawn `claude-code-guide` with prompt:
   ```
   Fetch current standards for Claude Code commands/skills from https://docs.anthropic.com/en/docs/claude-code/skills
   Focus on: command invocation, argument passing ($ARGUMENTS, $1, $2), user-invocable field
   Note: Commands and skills merged in v2.1.3
   ```
3. Spawn `bulwark-standards-reviewer` with command content and fetched standards
4. Write report to `logs/validations/`

### Key Validation Points

| Aspect | Requirement |
|--------|-------------|
| Invocation | `/skill-name arg1 arg2` |
| Arguments | `$ARGUMENTS` (all), `$1`/`$2` (positional) |
| Environment | `${ENV_VAR}` for environment variables |
| Visibility | `user-invocable: true` for `/` menu |

### Fallback Checklist

If doc fetch fails, use: `references/commands-checklist.md`

---

## MCP Validation

### Official Documentation

https://docs.anthropic.com/en/docs/claude-code/mcp

### Validation Workflow

1. Read MCP server configuration
2. Spawn `claude-code-guide` with prompt:
   ```
   Fetch current standards for Claude Code MCP servers from https://docs.anthropic.com/en/docs/claude-code/mcp
   Focus on: server configuration, tool definitions, transport types, security considerations
   ```
3. Spawn `bulwark-standards-reviewer` with MCP content and fetched standards
4. Write report to `logs/validations/`

### Key Validation Points

| Aspect | Requirement |
|--------|-------------|
| Configuration | Valid JSON in `.claude/mcp.json` |
| Transport | `stdio`, `http`, or `sse` |
| Tools | Properly defined tool schemas |
| Security | No exposed secrets, proper permissions |

### Fallback Checklist

If doc fetch fails, use: `references/mcp-checklist.md`

---

## Plugins Validation

### Official Documentation

https://docs.anthropic.com/en/docs/claude-code/plugins

### Validation Workflow

1. Read plugin manifest and structure
2. Spawn `claude-code-guide` with prompt:
   ```
   Fetch current standards for Claude Code plugins from https://docs.anthropic.com/en/docs/claude-code/plugins
   Focus on: plugin.json manifest, directory structure, registration, flat skills directory
   ```
3. Spawn `bulwark-standards-reviewer` with plugin content and fetched standards
4. Write report to `logs/validations/`

### Key Validation Points

| Aspect | Requirement |
|--------|-------------|
| Manifest | `.claude-plugin/plugin.json` |
| Structure | Flat directories at root (`skills/`, `agents/`, `hooks/`) |
| Registration | All components listed in manifest |
| Naming | Plugin name matches directory |

### Directory Structure

```
plugin-name/
├── .claude-plugin/
│   └── plugin.json          # ONLY manifest here
├── agents/                  # At root, NOT in .claude-plugin/
├── skills/                  # At root, NOT in .claude-plugin/
└── hooks/                   # At root, NOT in .claude-plugin/
```

### Fallback Checklist

If doc fetch fails, use: `references/plugins-checklist.md`

---

## Batch Validation

When validating a directory:

1. **Glob** all matching files based on asset type patterns
2. **For each asset INDIVIDUALLY**:
   - Run the FULL single-asset validation workflow (Steps 1-4)
   - Spawn `bulwark-standards-reviewer` with ONLY that one asset
   - Write individual report to `logs/validations/`
   - **DO NOT** combine multiple assets into one reviewer context
3. **After all assets validated**, aggregate results into summary report

**CRITICAL**: Do NOT frontload all assets into a single reviewer context. This causes shallow analysis due to context overload. Each asset must be validated with full depth individually, then results aggregated.

### Batch Output

```
logs/validations/
├── batch-summary-{timestamp}.yaml    # Aggregate summary
├── skill-one-{timestamp}.yaml        # Individual reports
├── skill-two-{timestamp}.yaml
└── ...
```

### Batch Summary Format

```yaml
batch_validation:
  metadata:
    directory: "{path}"
    timestamp: "{ISO-8601}"
    total_assets: 5

  results:
    passed: 3
    failed: 2

  failures:
    - asset: "skills/broken-skill/SKILL.md"
      critical_count: 1
      report: "logs/validations/broken-skill-{timestamp}.yaml"
```

---

## Output Format

### YAML Report (logs/validations/)

```yaml
validation_report:
  metadata:
    asset: "{file_path}"
    asset_type: skill | hook | agent | command | mcp | plugin
    timestamp: "{ISO-8601}"
    validator: "bulwark-standards-reviewer"
    standards_source: fetched | fallback

  findings:
    - severity: critical | high | medium | low
      rule: "{standard being checked}"
      violation: "{what is wrong}"
      location: "{line or field}"
      remediation: "{how to fix}"

  summary:
    total_findings: 0
    critical: 0
    high: 0
    medium: 0
    low: 0
    verdict: pass | fail
    notes: "{any additional context}"
```

### Human-Readable Summary

```
Validation: skills/my-skill/SKILL.md
Standards: Fetched from official docs (2026-01-17)
Verdict: FAIL (2 critical, 1 high)

Critical:
  - Missing required 'description' field in frontmatter
  - SKILL.md exceeds 500 line limit (612 lines)

High:
  - 'agent' field uses unsupported value 'gpt-4'

Full report: logs/validations/my-skill-2026-01-17T10-30-00.yaml
```

### Severity Definitions

| Severity | Definition | Examples |
|----------|------------|----------|
| **Critical** | Blocks functionality, violates required standards | Missing required frontmatter, wrong file location |
| **High** | Significant issue, should fix before release | Deprecated field, exceeds limits |
| **Medium** | Quality improvement, recommended | Missing optional fields |
| **Low** | Style/naming suggestions | Naming conventions |

### Verdict Logic

```
if any_critical_findings:
    verdict = "FAIL"
else:
    verdict = "PASS"
# Always list ALL findings regardless of verdict
```

---

## Fallback Behavior

When `claude-code-guide` fetch fails:

1. **Log warning**: "Could not fetch latest standards, using embedded checklist"
2. **Set** `standards_source: fallback` in report
3. **Use** embedded checklist from `references/`
4. **Continue** validation
5. **Include note** in summary: "Validated against potentially outdated standards"

---

## Diagnostic Output

All validation runs write diagnostic data to:

```
logs/diagnostics/anthropic-validator-{timestamp}.yaml
```

### Diagnostic Schema

```yaml
diagnostic:
  skill: anthropic-validator
  timestamp: "{ISO-8601}"

  invocation:
    asset_path: "{input}"
    asset_type: "{detected type}"
    batch_mode: true | false

  execution:
    standards_fetch:
      agent: claude-code-guide
      success: true | false
      fallback_used: true | false
    analysis:
      agent: bulwark-standards-reviewer
      findings_count: 0

  output:
    report_path: "logs/validations/{name}.yaml"
    verdict: pass | fail
```

---

## Related Skills

- `subagent-prompting` (P0.1) - 4-part template for agent invocation
- `subagent-output-templating` (P0.2) - Output format for logs

## Related Agents

- `bulwark-standards-reviewer` - Critical analysis agent (invoked by this skill)
- `claude-code-guide` - Built-in agent for documentation fetching
