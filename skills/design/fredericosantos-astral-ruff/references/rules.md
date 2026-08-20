# Rule-Specific Examples

## Import Sorting

```bash
# Check only import sorting
ruff check --select I .

# Fix import sorting
ruff check --select I --fix .
```

## Python Version Upgrades

```bash
# Check for outdated syntax
ruff check --select UP .

# Upgrade syntax automatically
ruff check --select UP --fix .
```