# Quality Guardian — 质量工程师

AI 质量工程师工具包：降低幻觉、优化上下文质量、消除 AI 感 UI、强制修改后验证。

## Modules

| Module | Purpose | When Active |
|--------|---------|-------------|
| **Evidence Guard** | Reduces hallucinations via evidence-based reasoning | Always — every factual claim must have a source |
| **Context Cartographer** | Optimizes context quality (not just quantity) | When exploring codebases or reading multiple files |
| **UI Taste Guard** | Eliminates AI-generated UI patterns | When generating or modifying web/UI code |
| **Verification Runner** | Enforces post-change verification | After any code modification |

## Priority Order

```
Final quality > Correctness > Evidence grounding > Context optimization > Token saving
```

Token saving is a secondary goal. Never sacrifice output quality to save tokens.

## Installation

### Method 1: Install as Qoder Plugin

1. Copy the `quality-guardian` directory to your Qoder plugins location:
   ```
   ~/.qoder/plugins/quality-guardian/
   ```

2. Enable in `~/.qoder/settings.json`:
   ```json
   {
     "plugins": {
       "quality-guardian": { "enabled": true }
     }
   }
   ```

### Method 2: Install as Project-Level Skills and Rules

Copy skills and rules to your project:

```bash
# Skills
cp -r quality-guardian/skills/* .qoder/skills/

# Rules
cp -r quality-guardian/rules/* .qoder/rules/
```

### Method 3: Install as User-Level Skills

For global availability across all projects:

```bash
# Skills
cp -r quality-guardian/skills/* ~/.qoder/skills/
```

## Directory Structure

```
quality-guardian/
├── .qoder-plugin/
│   └── plugin.json                          # Plugin manifest
├── skills/
│   ├── evidence-guard/
│   │   ├── SKILL.md                         # Evidence-based reasoning
│   │   └── references/
│   │       └── evidence-ledger-examples.md  # Usage examples
│   ├── context-cartographer/
│   │   ├── SKILL.md                         # Context optimization
│   │   └── references/
│   │       └── context-mapping-examples.md  # Mapping examples
│   ├── ui-taste-guard/
│   │   ├── SKILL.md                         # Anti-AI UI patterns
│   │   └── references/
│   │       └── anti-pattern-catalog.md      # Visual anti-patterns
│   └── verification-runner/
│       ├── SKILL.md                         # Post-change verification
│       └── references/
│           └── verification-templates.md    # Report templates
├── rules/
│   ├── evidence-guard.md                    # Evidence rules (always apply)
│   ├── context-cartographer.md              # Context rules (model decision)
│   ├── ui-taste-guard.md                    # UI rules (always apply for UI)
│   └── verification-runner.md               # Verification rules (always apply)
├── agents/
│   └── quality-reviewer.md                  # Quality review agent
├── commands/
│   └── quality-check.md                     # /quality-check command
├── hooks/
│   ├── hooks.json                           # Hook configuration
│   ├── check-ui-anti-patterns.js            # PreToolUse: UI anti-pattern warnings
│   └── post-task-reminder.js                # Stop: verification reminder
├── demo/
│   └── settings-page-walkthrough.md         # Full demo walkthrough
├── scripts/
│   └── self-check.js                        # Plugin validation script
├── config.template.json                     # Configuration template
└── README.md                                # This file
```

## Configuration

Copy `config.template.json` values into your `.qoder/settings.json`:

| Setting | Default | Description |
|---------|---------|-------------|
| `maxContextFiles` | 30 | Max files to read (soft limit, can exceed with reason) |
| `maxFileReadLines` | 200 | Max lines per file read (prefer targeted segments) |
| `enableEvidenceLedger` | true | Track sources of factual claims |
| `enableUiAntiAiReview` | true | Check for AI-generated UI patterns |
| `enableBrowserVerification` | true | Use browser to verify UI changes |
| `enableTokenBudgetReport` | false | Output context usage stats |
| `preferredDesignSystem` | auto | auto / shadcn/ui / antd / mui / custom |
| `forbiddenUiPatterns` | [...] | UI patterns to avoid |
| `requiredVerificationCommands` | [] | Commands that must always run |

## Usage

### Automatic (via Rules)

The rules files activate automatically during conversations:
- `evidence-guard.md` and `verification-runner.md` always apply
- `ui-taste-guard.md` applies when generating UI code
- `context-cartographer.md` applies when exploring codebases

### Manual (via Command)

```
/quality-guardian:quality-check           # Full project quality check
/quality-guardian:quality-check src/auth   # Check specific area
```

### Via Agent

Use the `quality-reviewer` agent for dedicated quality reviews:
```
@quality-reviewer Review the latest changes
```

### Via Skills

Skills are automatically invoked by the agent based on task context. You can also reference them directly in conversation.

## Commands

### /quality-check

Runs all four modules and produces a comprehensive quality report.

## Hooks

Two optional hooks are provided (require Qoder hooks support):

### PreToolUse: UI Anti-Pattern Checker

Intercepts `Write` and `SearchReplace` tool calls. When UI code (`.tsx`, `.jsx`, `.vue`, etc.) is being written, checks for common AI-generated patterns (purple gradients, glassmorphism, giant text, decorative blobs, excessive border-radius) and outputs warnings to stderr. Non-blocking by default.

### Stop: Post-Task Verification Reminder

Runs when the agent stops responding. If code changes were detected but no verification report was produced, outputs a reminder to stderr. Non-blocking.

### Installing Hooks

Hooks require manual setup in `~/.qoder/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Write|SearchReplace",
        "hooks": [{ "type": "command", "command": "node <plugin-path>/hooks/check-ui-anti-patterns.js" }]
      }
    ],
    "Stop": [
      {
        "matcher": "",
        "hooks": [{ "type": "command", "command": "node <plugin-path>/hooks/post-task-reminder.js" }]
      }
    ]
  }
}
```

Replace `<plugin-path>` with the actual path to the installed plugin.

## Self-Check

Validate the plugin structure:

```bash
node scripts/self-check.js
```

Expected output: `✅ Self-check PASSED. Plugin structure is valid.` with 55+ checks passing.

## Demo

See [demo/settings-page-walkthrough.md](demo/settings-page-walkthrough.md) for a complete walkthrough showing how all four modules work together when adding a settings page to a React project.

The demo covers:
1. **Context Cartographer** — Repo map generation and context ledger
2. **Evidence Guard** — Evidence ledger and third-party library verification
3. **UI Taste Guard** — Design system detection and anti-pattern review
4. **Verification Runner** — Lint, typecheck, build execution and reporting

## Design Principles

1. **Quality first** — Never sacrifice output quality to save tokens
2. **Evidence-based** — Every claim needs a traceable source
3. **Conservative defaults** — Read less, verify more, but flexible when quality requires more
4. **No fabricated capabilities** — Don't invent APIs, paths, or test results
5. **Real product UI** — Generated pages should look like working products, not AI templates
6. **Verify after change** — Always run available checks after modifications

## Compatibility

- Works with any Qoder version supporting the plugin system (skills + rules + agents + commands)
- Rules work in projects using `.qoder/rules/` directory
- Skills work at user level (`~/.qoder/skills/`) or project level (`.qoder/skills/`)
- If Qoder's plugin system is unavailable, install skills and rules manually (Method 2 or 3)
