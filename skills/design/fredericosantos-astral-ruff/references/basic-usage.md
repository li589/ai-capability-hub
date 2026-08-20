# Basic Linting and Formatting

## Check All Files

```bash
# Check for linting issues
ruff check .

# Check specific file
ruff check my_script.py
```

## Auto-Fix Issues

```bash
# Fix safe issues automatically
ruff check --fix .

# Preview unsafe fixes first
ruff check --fix --unsafe-fixes --diff .

# Apply unsafe fixes
ruff check --fix --unsafe-fixes .
```

## Format Code

```bash
# Format all files
ruff format .

# Check if files need formatting
ruff format --check .

# Preview formatting changes
ruff format --diff .
```