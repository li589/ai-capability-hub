#!/bin/bash
# KB Framework CLI Wrapper
# Usage: kb <command> [args]

# Find KB installation
KB_DIR="${KB_DIR:-$HOME/.openclaw/kb}"

# If not in expected location, try to find it
if [ ! -d "$KB_DIR" ]; then
    # Check alternative locations
    if [ -d "$HOME/projects/kb-framework" ]; then
        KB_DIR="$HOME/projects/kb-framework"
    elif [ -d "$HOME/kb-framework" ]; then
        KB_DIR="$HOME/kb-framework"
    fi
fi

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 is required but not installed"
    exit 1
fi

# Run the Python CLI
python3 -m kb "$@"
