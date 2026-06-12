#!/usr/bin/env bash
# Run all Python and Frontend Linters
# Usage: ./scripts/lint.sh [--fix]

set -euo pipefail

FIX=${1:-}
PYTHON_DIR="apps/mirumoji"
FRONTEND_DIR="apps/frontend"

echo "=== Python: Ruff ==="
if [[ "$FIX" == "--fix" ]]; then
    ruff check --fix "$PYTHON_DIR/src"
    ruff format "$PYTHON_DIR/src"
else
    ruff check "$PYTHON_DIR/src"
    ruff format --check "$PYTHON_DIR/src"
fi

echo "=== Python: MyPy ==="
mypy "$PYTHON_DIR/src"

echo "=== Frontend: eslint ==="
if [[ "$FIX" == "--fix" ]]; then
    (cd "$FRONTEND_DIR" && npm run lint:fix)
else
    (cd "$FRONTEND_DIR" && npm run lint)
fi

echo "=== Frontend: prettier ==="
if [[ "$FIX" == "--fix" ]]; then
    (cd "$FRONTEND_DIR" && npm run format)
else
    (cd "$FRONTEND_DIR" && npx prettier --check src)
fi

echo "All checks passed."
