# Configuration Examples

## Basic pyproject.toml Configuration

```toml
[tool.ruff]
line-length = 88
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "N", "B"]
ignore = ["E501"]  # Line too long

[tool.ruff.lint.isort]
known-first-party = ["myproject"]
```

## Strict Configuration

```toml
[tool.ruff.lint]
select = ["ALL"]
ignore = [
    "COM812",  # Trailing comma missing
    "ISC001",  # Implicitly concatenated string literals
    "T10",     # Debugger statements
    "T20",     # Print statements
]
```