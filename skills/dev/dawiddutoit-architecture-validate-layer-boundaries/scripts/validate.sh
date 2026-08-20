#!/usr/bin/env bash
# Validate Clean Architecture layer boundaries
# Usage: ./validate.sh [file_or_directory]

set -euo pipefail

TARGET="${1:-.}"

echo "Validating Clean Architecture boundaries in: $TARGET"

# Find all Python files
if [[ -f "$TARGET" ]]; then
    FILES="$TARGET"
else
    FILES=$(find "$TARGET" -name "*.py" -path "*/src/project_watch_mcp/*" 2>/dev/null || true)
fi

if [[ -z "$FILES" ]]; then
    echo "No Python files found in project_watch_mcp"
    exit 0
fi

VIOLATIONS=0

for file in $FILES; do
    # Determine layer from path
    if [[ $file == */domain/* ]]; then
        LAYER="domain"
    elif [[ $file == */application/* ]]; then
        LAYER="application"
    elif [[ $file == */infrastructure/* ]]; then
        LAYER="infrastructure"
    elif [[ $file == */interfaces/* ]]; then
        LAYER="interfaces"
    else
        continue  # Not in a layer directory
    fi

    # Check imports based on layer
    case $LAYER in
        domain)
            # Domain cannot import from application, infrastructure, or interfaces
            if grep -nE "from (project_watch_mcp\.)?(application|infrastructure|interfaces)" "$file" 2>/dev/null; then
                echo "❌ Domain layer violation in $file"
                ((VIOLATIONS++))
            fi
            ;;
        application)
            # Application cannot import from interfaces
            if grep -nE "from (project_watch_mcp\.)?interfaces" "$file" 2>/dev/null; then
                echo "❌ Application layer violation in $file"
                ((VIOLATIONS++))
            fi
            ;;
        interfaces)
            # Interfaces cannot import from domain or infrastructure directly
            if grep -nE "from (project_watch_mcp\.)?(domain\.models|infrastructure)" "$file" 2>/dev/null; then
                echo "❌ Interface layer violation in $file"
                ((VIOLATIONS++))
            fi
            ;;
    esac
done

if [[ $VIOLATIONS -eq 0 ]]; then
    echo "✅ Clean Architecture validation: PASSED"
    exit 0
else
    echo "❌ Clean Architecture validation: FAILED ($VIOLATIONS violations)"
    echo ""
    echo "For fix patterns, see: .claude/skills/validate-layer-boundaries/references/violation-fixes.md"
    echo "For examples, see: .claude/skills/validate-layer-boundaries/examples/examples.md"
    exit 1
fi
