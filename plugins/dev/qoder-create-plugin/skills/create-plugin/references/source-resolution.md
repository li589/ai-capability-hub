# Source Resolution

Resolve the input into a real `SKILL.md`, support files, and provenance before
creating plugin files.

## Input Cleanup

- Normalize full-width URL prefixes such as `Https：//` and `HTTP：//`.
- Strip surrounding Chinese punctuation, angle brackets, quotes, and Markdown
  link wrappers.
- Preserve the original user-provided source string for README provenance.

## Local File Or Directory

1. If the argument is a `SKILL.md` file, read it directly.
2. If the argument is a directory, search in this order:
   - `SKILL.md`
   - `*/SKILL.md`
   - `skills/*/SKILL.md`
   - `.agents/skills/*/SKILL.md`
   - `.qoder/skills/*/SKILL.md`
3. If multiple skills are found, ask the user to choose unless the request
   clearly asks to package the whole plugin.
4. Copy same-directory support files that are referenced by the selected
   `SKILL.md`.

## GitHub URL

Support raw, blob, tree, and repository URLs.

1. `raw.githubusercontent.com/.../SKILL.md`: read directly.
2. `github.com/<owner>/<repo>/blob/<branch>/<path>/SKILL.md`: convert to raw
   URL and read.
3. `github.com/<owner>/<repo>/tree/<branch>/<path>`: look for `SKILL.md` in
   that directory.
4. Repository root URL: probe these paths first:
   - `SKILL.md`
   - `<skill-id>/SKILL.md`
   - `skills/<skill-id>/SKILL.md`
   - `.agents/skills/<skill-id>/SKILL.md`
   - `.qoder/skills/<skill-id>/SKILL.md`
5. If probing fails or the API is rate limited, use:

```bash
git clone --depth 1 --filter=blob:none --single-branch <repo-url> <tmp-dir>
```

Then apply the local directory rules.

## Qoder Marketplace URL

For `https://qoder.com/marketplace/skill?id=<skill_id>`:

1. Extract `skill_id`.
2. Request the detail API:

```bash
curl -L "https://qoder.com/api/v1/marketplace/skills/<skill_id>/detail"
```

3. Read `skill_name`, `description`, `version`, `author`, `category`,
   `icon_url`, `github_repo`, `github_path`, `download_url`, and `file_tree`
   when present.
4. If `icon_url` exists, download it into `assets/logo.<ext>` and point
   `plugin.json.logo` to that local file.
5. If `icon_url` is missing, a rendered marketplace page may be inspected for a
   real skill logo. Accept only an image that is clearly the skill logo, such as
   an image with the skill name in alt text or a skill-icon DOM context. Do not
   use `og:image`, `twitter:image`, Qoder site logos, download icons, or generic
   marketplace artwork as the plugin logo.
6. Prefer the files API for exact file contents:

```bash
curl -L "https://qoder.com/api/v1/marketplace/skills/<skill_id>/files?path=%2FSKILL.md"
```

If `SKILL.md` is not at root, use the actual path from `file_tree`.
7. If the files API is unavailable, download `download_url`, unzip it, find
   `SKILL.md`, and copy its parent-directory support files.
8. If `github_path` is present, the GitHub URL flow can be used as a fallback.
   Record the actual source used.

## skills.sh Or www.skills.sh

Bare `skill.sh` may be unrelated. Prefer `www.skills.sh` data or the exact
entry provided by the user.

1. For list discovery, use:

```bash
curl -L "https://www.skills.sh/api/skills/all-time/1"
```

2. Entries usually include `source` and `skillId`. Probe:
   - `https://raw.githubusercontent.com/<source>/main/<skillId>/SKILL.md`
   - `https://raw.githubusercontent.com/<source>/master/<skillId>/SKILL.md`
   - `https://raw.githubusercontent.com/<source>/main/skills/<skillId>/SKILL.md`
   - `https://raw.githubusercontent.com/<source>/master/skills/<skillId>/SKILL.md`
3. If probing fails, clone the source repository and apply the local directory
   rules.

## Pasted Content

1. If content starts with YAML frontmatter, preserve it and fill missing
   required fields.
2. If frontmatter is absent, infer `name` and `description` from the content.
3. Set README provenance to pasted content.
4. If the pasted body references unavailable `references/`, `scripts/`, images,
   or templates, record an evidence gap instead of inventing files.
