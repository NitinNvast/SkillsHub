#!/usr/bin/env bash
# Runs after Claude edits a Python file — quick ruff check (non-blocking, advisory only)
if [[ "$CLAUDE_TOOL_INPUT_FILE_PATH" == *backend*.py ]]; then
  cd "$(git rev-parse --show-toplevel)/backend" 2>/dev/null || exit 0
  uv run ruff check --quiet "$CLAUDE_TOOL_INPUT_FILE_PATH" 2>&1 || true
fi
