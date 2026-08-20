# Workspace Model

## Purpose

Define the practical workspace layers that this collaboration skill should reason about.

This model is intended to keep onboarding, diagnosis, and configuration guidance grounded in real OpenClaw layouts without assuming every directory in one machine is a universal standard.

## Recommended logical layers

### 1. Agent instance layer

Typical path pattern:
- `~/.openclaw/agents/<agent-name>`

Role:
- isolate agent runtime instances
- hold agent-level sessions, runtime state, and instance-specific material
- represent the runtime/container side of an agent

This is not the main canonical knowledge workspace by itself.

### 2. Main control workspace

Typical path pattern:
- `~/.openclaw/workspace`

Role:
- serve as the main canonical workspace for the control agent
- hold shared rules, docs, memory, skills, and long-term coordination logic
- act as the primary governance/knowledge layer

Typical markers:
- `AGENTS.md`
- `SOUL.md`
- `USER.md`
- `MEMORY.md`
- `HEARTBEAT.md`
- `docs/`
- `skills/`
- `memory/`

### 3. Child agent workspaces

Typical path pattern:
- `~/.openclaw/workspaces/<agent-name>`

Role:
- hold the business/knowledge workspace for each non-main agent
- store the agent's own docs, memory, and role-specific behavior
- serve as the canonical workspace layer for that child agent

Examples:
- `~/.openclaw/workspaces/feishu-planner`
- `~/.openclaw/workspaces/feishu-moltbook`

## Two-workspace model per agent

In some environments, an agent effectively participates in two layers at once:
- an agent-side runtime workspace or instance directory
- a project/business workspace

When this pattern exists, onboarding and diagnostics should verify both layers.

Examples:
- runtime/instance side under `~/.openclaw/agents/<agent-name>`
- business/knowledge side under `~/.openclaw/workspaces/<agent-name>` or another configured workspace path

## Compatibility / migration directories

Some machines may contain historical or compatibility workspaces, such as older main-workspace variants.

Guidance:
- do not automatically treat every similarly named directory as a current canonical workspace
- verify whether it is active, legacy, compatibility-only, or migration residue
- do not recommend legacy/compatibility paths as the default template for new users unless they are still the active standard

## Recommended default guidance for new users

Unless the local environment clearly uses a different active standard, prefer this model:
- main control workspace: `~/.openclaw/workspace`
- child agent workspaces: `~/.openclaw/workspaces/<agent-name>`
- agent instance layer: `~/.openclaw/agents/<agent-name>`

This keeps the model simple:
- `agents` = runtime instance layer
- `workspace` = main control workspace
- `workspaces` = child agent workspace collection

## Diagnostic implications

When troubleshooting collaboration setup, check separately:
- whether the agent instance exists
- whether the canonical workspace exists
- whether the workspace contains the expected role files
- whether permissions and structure are consistent across agents
- whether the system is accidentally reading from a legacy compatibility directory instead of the intended canonical workspace
