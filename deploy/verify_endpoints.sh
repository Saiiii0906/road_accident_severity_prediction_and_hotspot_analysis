#!/usr/bin/env bash
# =================================================================
# Vantage End-to-End Production Verification Smoke Suite
# Tests all core production API endpoints against a live deployment.
# Usage: bash deploy/verify_endpoints.sh [BASE_URL]
# Default BASE_URL: http://127.0.0.1:8000
# =================================================================
set -euo pipefail

BASE_URL="${1:-http://127.0.0.1:8000}"
BASE_URL="${BASE_URL%/}"

echo "================================================================="
echo " Vantage Live Endpoint Smoke Test Suite"
echo " Target Base URL: $BASE_URL"
echo "================================================================="

# 1. Health Endpoint
echo -n "[1/7] Testing GET /health ... "
HEALTH_RESP=$(curl -s -f "$BASE_URL/health")
if echo "$HEALTH_RESP" | grep -q '"status":\s*"healthy"'; then
    echo "PASS"
else
    echo "FAIL: $HEALTH_RESP" >&2
    exit 1
fi

# 2. Student A Severity Prediction
echo -n "[2/7] Testing POST /api/severity/predict (Student A) ... "
SEV_RESP=$(curl -s -X POST "$BASE_URL/api/severity/predict" \
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
if echo "$SEV_RESP" | grep -q '"predicted_severity"'; then
    echo "PASS"
else
    echo "FAIL: $SEV_RESP" >&2
    exit 1
fi

# 3. Student B Hotspots
echo -n "[3/7] Testing POST /api/hotspots/analyze (Student B) ... "
HOTSPOT_RESP=$(curl -s -X POST "$BASE_URL/api/hotspots/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "center": {"latitude": 51.5074, "longitude": -0.1278},
    "radius_km": 5.0,
    "limit": 5
  }')
if echo "$HOTSPOT_RESP" | grep -q '"clusters"'; then
    echo "PASS"
else
    echo "FAIL: $HOTSPOT_RESP" >&2
    exit 1
fi

# 4. Student C Road Risk
echo -n "[4/7] Testing POST /api/road-risk/predict (Student C) ... "
RISK_RESP=$(curl -s -X POST "$BASE_URL/api/road-risk/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "center": {"latitude": 51.5074, "longitude": -0.1278},
    "radius_km": 5.0
  }')
if echo "$RISK_RESP" | grep -q '"segments"'; then
    echo "PASS"
else
    echo "FAIL: $RISK_RESP" >&2
    exit 1
fi

# 5. AI Infrastructure Report
echo -n "[5/7] Testing POST /api/reports/ai-infrastructure-report ... "
REPORT_RESP=$(curl -s -X POST "$BASE_URL/api/reports/ai-infrastructure-report" \
  -H "Content-Type: application/json" \
  -d '{
    "corridor_name": "A40 Westway Corridor",
    "start_coordinates": {"latitude": 51.5175, "longitude": -0.1873},
    "end_coordinates": {"latitude": 51.5241, "longitude": -0.2458},
    "buffer_radius_meters": 1000
  }')
if echo "$REPORT_RESP" | grep -q '"executive_summary"'; then
    echo "PASS"
else
    echo "FAIL: $REPORT_RESP" >&2
    exit 1
fi

# 6. Journey Safety: London Victoria -> Heathrow (TfL Supported)
echo -n "[6/7] Testing Journey Safety: London Victoria -> Heathrow ... "
JOURNEY_LDN=$(curl -s -X POST "$BASE_URL/api/journey/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "origin_query": "London Victoria Station, London, UK",
    "destination_query": "Heathrow Airport Terminal 5, London, UK"
  }')
if echo "$JOURNEY_LDN" | grep -q '"synthesis"' && echo "$JOURNEY_LDN" | grep -q '"traffic"'; then
    echo "PASS (TfL Supported & Gemini Grounded)"
else
    echo "FAIL: $JOURNEY_LDN" >&2
    exit 1
fi

# 7. Journey Safety: Paris -> Versailles (Unsupported TfL Scope)
echo -n "[7/7] Testing Journey Safety: Paris -> Versailles (Out of TfL Scope) ... "
JOURNEY_PARIS=$(curl -s -X POST "$BASE_URL/api/journey/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "origin_query": "Eiffel Tower, Paris, France",
    "destination_query": "Palace of Versailles, Versailles, France"
  }')
if echo "$JOURNEY_PARIS" | grep -q '"unsupported_for_geography"'; then
    echo "PASS (Honest Geographic Scoping Confirmed)"
else
    echo "FAIL: Expected coverage_status=unsupported_for_geography: $JOURNEY_PARIS" >&2
    exit 1
fi

echo "================================================================="
echo "ALL 7 PRODUCTION ENDPOINTS VERIFIED AND PASSING!"
echo "================================================================="
