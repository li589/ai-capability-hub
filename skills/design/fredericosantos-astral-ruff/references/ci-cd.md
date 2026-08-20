# CI/CD Integration

## GitHub Actions Example

```yaml
- name: Lint with ruff
  run: |
    ruff check .
    ruff format --check .

- name: Fix with ruff
  run: |
    ruff check --fix .
    ruff format .
```

## Pre-commit Hook

```yaml
repos:
  - repo: https://github.com/charliermarsh/ruff-pre-commit
    rev: v0.1.6
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
```