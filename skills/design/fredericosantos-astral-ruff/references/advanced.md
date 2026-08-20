# Advanced Usage

## Selective Rule Enforcement

### Check Only Specific Rules

```bash
# Only check syntax errors and undefined names
ruff check --select E,F .

# Check everything except style issues
ruff check --select "ALL" --ignore "E,W"
```

### Per-File Overrides

```toml
[tool.ruff.lint.per-file-ignores]
"tests/**/*.py" = ["B011", "S101"]  # assert False, assert used
"scripts/**/*.py" = ["T201"]        # print found
```

## Watching for Changes

```bash
# Watch mode for development
ruff check --watch .
```

## Explain Rules

```bash
# Understand why a rule exists
ruff rule F401  # Module imported but unused
ruff rule E501  # Line too long
```

## Custom Rule Selection

```bash
# Enable additional rule categories
ruff check --select "E,F,I,UP,B" .

# Disable specific rules
ruff check --ignore "E501,F401" .
```