# Migration Examples

## From Black + Flake8 + isort

```bash
# Old workflow
black .
flake8 .
isort .

# New workflow
ruff check --fix .
ruff format .
```

## From autopep8 + flake8

```bash
# Old workflow
autopep8 --in-place --aggressive --aggressive .
flake8 .

# New workflow
ruff check --fix .
ruff format .
```