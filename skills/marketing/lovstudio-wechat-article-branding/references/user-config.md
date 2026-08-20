# User Configuration

Resolve persistent brand and editorial preferences without creating a private implementation branch.

## Resolution order

1. Explicit values in the current request.
2. Skill-specific environment variables.
3. Shared profile JSON.
4. Safe inferred defaults such as the current language.
5. One focused question for a required user-facing value that remains unknown.

Default profile location:

```bash
${LOVSTUDIO_SKILLS_PROFILE:-$HOME/.lovstudio/skills/profile.json}
```

## First run

1. Prefill fields from the request and current project.
2. Load a brand-profile file referenced by the shared profile.
3. Validate it with `scripts/validate_brand_profile.py`.
4. Ask only for a missing field that changes public output.
5. Show values before persisting them with the user's knowledge.

Do not persist article bodies, cookies, edit tokens, private URLs, inferred claims, or temporary browser state.

## Shared profile example

```json
{
  "user": {
    "language": "zh-CN",
    "timezone": "Asia/Shanghai"
  },
  "brand": {
    "profile": "$HOME/.lovstudio/skills/brand.json"
  },
  "wechat_article_branding": {
    "default_pipeline": "full",
    "polish_enabled": false,
    "cover_ratios": ["2.35:1", "1:1"]
  }
}
```
