#!/usr/bin/env bash
set -euo pipefail

echo "================================================================="
echo " Vantage — Production Backend Container Entrypoint"
echo "================================================================="

# Detect Python runtime
PYTHON_BIN="${PYTHON_BIN:-}"
if [ -z "$PYTHON_BIN" ]; then
    if command -v python3 >/dev/null 2>&1; then
        PYTHON_BIN="python3"
    elif command -v python >/dev/null 2>&1; then
        PYTHON_BIN="python"
    else
        echo "==> [ERROR] Neither python3 nor python found in PATH." >&2
        exit 1
    fi
fi

# 1. Acquire / verify model artifact
echo "==> Step 1: Validating Student A model presence and integrity..."
TARGET_MODEL="${STUDENT_A_MODEL_PATH:-student_A/models/accident_severity_model.pkl}"
if ! "$PYTHON_BIN" scripts/acquire_model.py --target-path "$TARGET_MODEL"; then
    echo "==> [ERROR] Model acquisition failed. Exiting container startup." >&2
    exit 1
fi

# 2. Confirm model file exists on disk
if [ ! -f "$TARGET_MODEL" ]; then
    echo "==> [ERROR] Student A model not found at $TARGET_MODEL." >&2
    echo "    Please mount a persistent volume or configure VANTAGE_MODEL_SOURCE_URL." >&2
    exit 1
fi

MODEL_SIZE=$(ls -lh "$TARGET_MODEL" | awk '{print $5}')
echo "==> Step 2: Student A model verified at $TARGET_MODEL (size: $MODEL_SIZE)"

# 3. Configure runtime networking & worker concurrency
APP_HOST="${HOST:-0.0.0.0}"
APP_PORT="${PORT:-8000}"

echo "==> Step 3: Launching Uvicorn on http://${APP_HOST}:${APP_PORT} with 1 worker..."
echo "    NOTE: Student A model consumes ~5 GB RAM in memory. Single worker is enforced."

# Ensure backend directory is in PYTHONPATH
export PYTHONPATH="backend:${PYTHONPATH:-}"

cd backend
exec uvicorn app.main:app --host "$APP_HOST" --port "$APP_PORT" --workers 1
