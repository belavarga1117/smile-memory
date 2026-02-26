#!/bin/bash
# Claude Code PostToolUse hook — auto-rebuild CSS and auto-format Python
# Receives tool info as JSON on stdin (tool_name, tool_input, tool_response)

PROJ="/Users/vargabela/Travel Agency 1"

# Extract file_path from stdin JSON (tries both flat and nested formats)
FILE=$(python3 -c "
import json, sys
try:
    raw = sys.stdin.read()
    d = json.loads(raw)
    # PostToolUse format: {tool_name, tool_input:{file_path}, tool_response}
    fp = (d.get('tool_input') or d).get('file_path', '')
    print(fp)
except Exception:
    print('')
" 2>/dev/null)

if [[ -z "$FILE" ]]; then
    exit 0
fi

# Auto-rebuild CSS when input.css is edited
if [[ "$FILE" == *"/input.css" ]]; then
    echo "[hook] CSS changed — rebuilding..."
    if cd "$PROJ" && npm run css:build 2>&1; then
        echo "[hook] ✓ CSS rebuilt successfully"
    else
        echo "[hook] ✗ CSS build FAILED — run 'npm run css:build' manually to see the error" >&2
        exit 1
    fi
fi

# Auto-format Python files after editing
if [[ "$FILE" == *.py ]]; then
    RUFF="$PROJ/venv/bin/ruff"
    if [[ -x "$RUFF" ]]; then
        "$RUFF" format "$FILE" 2>&1 && echo "[hook] ✓ Formatted: $(basename "$FILE")"
        "$RUFF" check --fix "$FILE" 2>&1 || true
    fi
fi
