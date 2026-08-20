# using-superpowers — Claude Code Skill

A meta-skill that ensures Claude Code **always checks and invokes relevant skills** before responding. It acts as a discipline enforcer — preventing the agent from skipping workflows, rationalizing away skill usage, or diving into code without proper process.

## What It Does

- Forces skill invocation **before any response**, even clarifying questions
- Provides a decision flowchart for skill selection
- Lists "red flag" rationalizations that indicate the agent is about to skip a skill
- Establishes priority order when multiple skills apply
- Distinguishes rigid vs flexible skill types

## Install

### One-liner

```bash
git clone https://github.com/itsdik/using-superpowers-skill.git ~/.claude/skills/using-superpowers
```

### Claude Code agent install

If your Claude Code agent is installing this for you, it should:

```bash
# 1. Clone into the skills directory
git clone https://github.com/itsdik/using-superpowers-skill.git ~/.claude/skills/using-superpowers

# 2. Verify installation
cat ~/.claude/skills/using-superpowers/SKILL.md | head -5
```

The skill is automatically available on the next Claude Code session — no further configuration needed. Claude Code discovers skills by scanning `~/.claude/skills/*/SKILL.md`.

### Manual install

1. Download `SKILL.md` from this repo
2. Place it at `~/.claude/skills/using-superpowers/SKILL.md`
3. Restart Claude Code

## File Structure

```
~/.claude/skills/using-superpowers/
└── SKILL.md          # The skill definition
```

## Usage

This skill is designed to be **always active**. Once installed, Claude Code will:

1. Check for applicable skills before every response
2. Invoke skills via the `Skill` tool when they match
3. Announce which skill it's using and why
4. Follow the skill's instructions exactly

You can also invoke it explicitly:

```
/using-superpowers
```

## License

MIT
