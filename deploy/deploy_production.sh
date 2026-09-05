#!/usr/bin/env bash
# =================================================================
# Vantage Automated Production Deployment Runner
# Execute from the repository root on the production Linux VM.
# =================================================================
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

echo "================================================================="
echo " Vantage — Production Container Deployment"
echo "================================================================="

# 1. Verify Docker and Compose availability
if ! command -v docker >/dev/null 2>&1; then
    echo "ERROR: Docker is not installed or not in PATH." >&2
    echo "Run 'sudo bash deploy/setup_server.sh' first." >&2
    exit 1
fi

if docker compose version >/dev/null 2>&1; then
    COMPOSE_CMD="docker compose"
elif command -v docker-compose >/dev/null 2>&1; then
    COMPOSE_CMD="docker-compose"
else
    echo "ERROR: Neither 'docker compose' plugin nor 'docker-compose' standalone found." >&2
    exit 1
fi

# 2. Check Backend Environment Configuration
if [ ! -f backend/.env ]; then
    echo "ERROR: backend/.env not found." >&2
    echo "Create backend/.env from backend/.env.example and populate GEMINI_API_KEY." >&2
    exit 1
fi

if ! grep -q "GEMINI_API_KEY" backend/.env || grep -q "your_gemini_api_key_here" backend/.env; then
    echo "ERROR: GEMINI_API_KEY is not configured in backend/.env." >&2
    exit 1
fi

# 3. Model Presence & Integrity Check
MODEL_PATH="${STUDENT_A_MODEL_PATH:-student_A/models/accident_severity_model.pkl}"
if [ ! -f "$MODEL_PATH" ]; then
    echo "==> Student A model missing at $MODEL_PATH."
    if [ -n "${VANTAGE_MODEL_SOURCE_URL:-}" ]; then
        echo "==> Acquiring model from VANTAGE_MODEL_SOURCE_URL..."
        python3 scripts/acquire_model.py --target-path "$MODEL_PATH"
    else
        echo "ERROR: $MODEL_PATH is missing and VANTAGE_MODEL_SOURCE_URL is not set." >&2
        echo "Upload the 7.80 GB accident_severity_model.pkl to $MODEL_PATH before deploying." >&2
        exit 1
    fi
fi

MODEL_SIZE=$(ls -lh "$MODEL_PATH" | awk '{print $5}')
echo "==> Student A model verified: $MODEL_PATH ($MODEL_SIZE)"

# 4. Build Container Image
echo "==> Building Vantage backend container image via $COMPOSE_CMD..."
$COMPOSE_CMD build

# 5. Launch Backend Service
echo "==> Launching backend container with 1 Uvicorn worker..."
$COMPOSE_CMD up -d

# 6. Poll Health Endpoint
echo "==> Awaiting container startup and model loading (up to 60 seconds)..."
HEALTH_URL="http://127.0.0.1:8000/health"
MAX_ATTEMPTS=30
ATTEMPT=0
HEALTHY=false

while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
    ATTEMPT=$(( ATTEMPT + 1 ))
    if curl -s -f "$HEALTH_URL" | grep -q '"status":\s*"healthy"'; then
        HEALTHY=true
        break
    fi
    sleep 2
done

if [ "$HEALTHY" = true ]; then
    echo "✓ Vantage backend is healthy at $HEALTH_URL!"
else
    echo "ERROR: Backend failed to report healthy within 60 seconds." >&2
    echo "Container logs:" >&2
    docker compose logs --tail 50 backend >&2
    exit 1
fi

# 7. Execute Live Smoke Test against Severity Endpoint
echo "==> Executing real inference smoke test (POST /api/severity/predict)..."
SMOKE_RESULT=$(curl -s -X POST http://127.0.0.1:8000/api/severity/predict \
  -H "Content-Type: application/json" \
  -d '{
    "accident_date": "2024-10-15",
    "accident_time": "18:45",
    "day_of_week": "Tuesday",
    "speed_limit": 30,
    "number_of_vehicles": 2,
    "number_of_casualties": 1,
    "road_type": "single_carriageway",
    "road_surface": "wet",
    "weather": "raining",
    "light_conditions": "darkness_lights_lit",
    "urban_or_rural_area": "urban"
  }')

echo "Smoke Test Result:"
echo "$SMOKE_RESULT"

if echo "$SMOKE_RESULT" | grep -q '"predicted_severity"'; then
    echo "================================================================="
    echo "✓ VANTAGE BACKEND DEPLOYMENT & SMOKE TEST SUCCESSFUL!"
    echo "================================================================="
else
    echo "ERROR: Severity smoke test failed to return predicted_severity." >&2
    exit 1
fi
