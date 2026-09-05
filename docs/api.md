# Vantage REST API Reference

This document provides a comprehensive technical reference for all active endpoints exposed by the **Vantage** backend.

Interactive OpenAPI documentation and live request testing are available locally at:

- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`
- **OpenAPI JSON Schema:** `http://localhost:8000/openapi.json`

> [!NOTE]
> All functional routes are mounted at both their canonical paths (e.g. `/journey/analyze`) and with the API prefix (e.g. `/api/journey/analyze`). Both forms are identical in behavior.

---

## 1. System Endpoints

### `GET /`

Returns basic service metadata confirming that the backend instance is alive.

- **Status Code:** `200 OK`
- **Response Schema:**

```json
{
  "project": "Road Accident Severity Prediction & Hotspot Analysis",
  "version": "1.0.0",
  "status": "Running",
  "docs": "/docs"
}
```

---

### `GET /health`

Liveness check for uptime monitors, container orchestrators, and load balancers.

- **Status Code:** `200 OK`
- **Response Schema:**

```json
{
  "status": "healthy",
  "timestamp": "2026-09-05T00:15:00.000000+00:00",
  "api_version": "1.0.0"
}
```

---

## 2. Severity Prediction Endpoints

Predicts the post-collision injury severity distribution for a single collision event using the 138-feature Random Forest model (`Student A`).

### `POST /severity/predict` (and `/api/severity/predict`)

- **Method:** `POST`
- **Request Body:** `SeverityPredictionRequest` (Content-Type: `application/json`)

#### Key Request Fields

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `day_of_week` | string | Yes | Day of collision (`Monday` .. `Sunday`). |
| `time_of_day` | string | Yes | Time in 24h format (`HH:MM`). |
| `road_type` | string | Yes | Road category (`Single carriageway`, `Dual carriageway`, `Roundabout`, `One way street`, `Slip road`). |
| `speed_limit` | integer | Yes | Speed limit in mph ($10 \le v \le 70$). |
| `light_conditions` | string | Yes | Lighting context (`Daylight`, `Darkness - lights lit`, etc.). |
| `weather_conditions` | string | Yes | Weather context (`Fine no high winds`, `Raining no high winds`, `Fog or mist`, etc.). |
| `road_surface_conditions` | string | Yes | Surface grip (`Dry`, `Wet or damp`, `Snow`, `Frost or ice`, `Flood`). |
| `urban_or_rural` | string | Yes | Area type (`Urban`, `Rural`). |
| `num_vehicles` | integer | Yes | Total vehicles involved ($\ge 1$). |
| `num_casualties` | integer | Yes | Total casualties involved ($\ge 1$). |
| `first_road_class` | string | Yes | Classification of first road (`Motorway`, `A`, `B`, `C`, `Unclassified`). |
| `junction_detail` | string | Yes | Junction geometry (`Not at junction`, `T or staggered junction`, `Roundabout`, etc.). |
| `latitude` | float | No | Latitude coordinate (defaults to UK centroid `52.23759`). |
| `longitude` | float | No | Longitude coordinate (defaults to UK centroid `-1.362233`). |

#### Response Schema (`SeverityPredictionResponse`)

```json
{
  "predicted_severity": "Serious",
  "probabilities": {
    "Fatal": 0.04,
    "Serious": 0.68,
    "Slight": 0.28
  },
  "risk_score": 68.0,
  "confidence": 0.68,
  "model_version": "Student_A_RandomForest_v1.0"
}
```

---

### `POST /severity/predict-batch` (and `/api/severity/predict-batch`)

Executes vector inference for up to 500 collision scenarios in a single HTTP request.

- **Request Body:** `{ "accidents": [ SeverityPredictionRequest, ... ] }`
- **Constraint:** $1 \le \text{length} \le 500$.
- **Response:** `{ "predictions": [ SeverityPredictionResponse, ... ], "total_processed": 10 }`

---

## 3. Hotspot Analysis Endpoints

Performs spatial queries over 3,705 precomputed empirical DBSCAN accident clusters (`Student B`).

### `POST /hotspots/analyze` (and `/api/hotspots/analyze`)

- **Method:** `POST`
- **Request Body:** `HotspotQueryRequest`

#### Query Modes (At least one required)

1. **Center + Radius:** Provide `center: { "latitude": 51.5074, "longitude": -0.1278 }` and `radius_km: 10.0`.
2. **Bounding Box:** Provide `min_lat`, `max_lat`, `min_lon`, `max_lon`.

#### Optional Filters

- `min_severity`: Filter by minimum cluster severity (`Slight`, `Serious`, `Fatal`).
- `limit`: Maximum clusters to return ($1 \le \text{limit} \le 100$, default 20).

#### Response Schema (`HotspotAnalysisResponse`)

```json
{
  "clusters": [
    {
      "cluster_id": 42,
      "center": { "latitude": 51.512, "longitude": -0.098 },
      "accident_count": 87,
      "severity_breakdown": { "Fatal": 2, "Serious": 19, "Slight": 66 },
      "dominant_severity": "Serious",
      "radius_meters": 350.5
    }
  ],
  "total_clusters_found": 1,
  "analyzed_at": "2026-09-05T00:15:00Z"
}
```

---

## 4. Road Risk Prediction Endpoints

Queries continuous topological risk predictions produced by the Graph Neural Network (`Student C`) over 13,921 road segments.

### `POST /road-risk/predict` (and `/api/road-risk/predict`)

- **Method:** `POST`
- **Request Body:** `RoadRiskQueryRequest`

#### Query Modes

- **By UK Road Number:** e.g. `{ "road_number": 1 }` for the A1 corridor.
- **By Center & Radius:** e.g. `{ "center": { "latitude": 53.48, "longitude": -2.24 }, "radius_km": 15.0 }`.
- **By Bounding Box:** `min_lat`, `max_lat`, `min_lon`, `max_lon`.
- **Threshold & Pagination:** `min_risk: 0.08` (filter to high risk), `limit: 50`.

#### Response Schema (`RoadRiskPredictionResponse`)

```json
{
  "segments": [
    {
      "segment_id": 10452,
      "road_number": 1,
      "start": { "latitude": 53.82, "longitude": -1.54 },
      "end": { "latitude": 53.84, "longitude": -1.52 },
      "predicted_risk": 0.092,
      "risk_category": "high"
    }
  ],
  "total_segments": 13921,
  "total_segments_matched": 1,
  "generated_at": "2026-09-05T00:15:00Z"
}
```

---

### `POST /risk/assess` (and `/api/risk/assess`)

Legacy backward-compatibility endpoint mapping a single coordinate to the nearest GNN road segment risk.

---

## 5. AI Infrastructure Report Endpoints

Synthesizes multi-model empirical evidence into an evidence-grounded decision-support report for transport planners and highway authorities.

### `POST /reports/ai-infrastructure-report` (and `/api/reports/ai-infrastructure-report`)

- **Method:** `POST`
- **Request Body:** `AIInfrastructureReportRequest`

```json
{
  "region": "south",
  "period": "last_12_months",
  "threshold": "moderate",
  "focus": "junction_safety"
}
```

#### Response Schema (`AIInfrastructureReportResponse`)

```json
{
  "meta": {
    "region": "south",
    "period": "last_12_months",
    "threshold": "moderate",
    "generated_at": "2026-09-05T00:15:00Z"
  },
  "executive_summary": "Transport infrastructure analysis indicates...",
  "risk_signals": [
    {
      "id": "sig-01",
      "label": "High-Density Cluster Corridors",
      "value": "14 Active Clusters",
      "note": "Concentrated along arterial junctions",
      "level": "high"
    }
  ],
  "priority_interventions": [
    {
      "rank": 1,
      "title": "Upgrade Junction Lighting & Sightlines",
      "category": "junction_safety",
      "priority": "high",
      "rationale": "Empirical collision clustering demonstrates...",
      "affected_corridors": ["A23", "A205"]
    }
  ],
  "implementation_matrix": [
    {
      "intervention": "Adjust Signal Phasing",
      "impact": "high",
      "effort": "low",
      "timeline": "Immediate (1-3 months)"
    }
  ]
}
```

---

## 6. Journey Safety Analysis Endpoint

The primary end-to-end analytical pipeline evaluating origin-to-destination corridors.

### `POST /journey/analyze` (and `/api/journey/analyze`)

- **Method:** `POST`
- **Request Body:** `JourneyAnalyzeRequest`

```json
{
  "source": "London Victoria Station",
  "destination": "Heathrow Airport Terminal 5",
  "travel_date": "2026-09-02",
  "travel_time": "14:30"
}
```

#### Pipeline Execution Stages

1. **Geocoding:** Resolves `source` and `destination` queries into coordinates via Nominatim.
2. **Routing:** Requests driving route, step-by-step corridor geometry, and duration via OSRM.
3. **Provider Geographic Scoping & Live Telemetry:**
   - Tests route intersection against provider bounding boxes (`ProviderCoverageService`).
   - Open-Meteo provides atmospheric telemetry globally.
   - TfL traffic delays and incident feeds are queried **only** if the route intersects Greater London `[51.25, 51.72] x [-0.55, 0.35]`.
   - Outside Greater London (e.g. Paris or Edinburgh), TfL calls are skipped and marked `provider_unsupported_for_geography`.
   - Partially traversing routes (e.g. London to Birmingham) are marked `provider_partially_supported`; TfL data covers the London portion only.
4. **Historical Corridor Matching:**
   - Evaluates route intersection with Great Britain boundary `[50.0, 60.5] x [-6.5, 2.0]`.
   - Within GB, buffers the route polyline (1,000m) against DBSCAN clusters (`Student B`) and GNN segments (`Student C`). Outside GB, marked `out_of_coverage`.
5. **Deterministic Assessment:** Evaluates verified hazard factors and assigns categorical severity tiers (`overall_score` is strictly `None`).
6. **Gemini Synthesis:** Synthesizes structured narrative, takeaways, and precautions using Gemini 1.5/2.5 Flash, abiding by 18 strict grounding rules.

#### Key Telemetry & Provenance Fields (`ProviderCoverageStatus`)

To prevent falsely conflating "unmonitored" regions with "zero incidents", the API returns explicit provider status values:

- `provider_supported`: Provider active, fully covers route, and returned data.
- `provider_partially_supported`: Provider monitors only a portion of the route (e.g. London portion of London-Birmingham).
- `provider_returned_no_results`: Provider fully monitored the route and verified zero active incidents.
- `provider_unsupported_for_geography`: Route outside physical coverage area (e.g. TfL queried for Paris).
- `provider_failed`: Provider was eligible but failed due to network error, timeout, or HTTP 5xx.
- `provider_not_configured`: Provider credentials or settings not supplied.

These states are reported in:

- `live_context.incidents_coverage`
- `live_context.traffic.coverage_status`
- `live_context.weather.coverage_status`
- `provenance.incident_coverage_status`
- `provenance.traffic_coverage_status`
- `provenance.weather_coverage_status`

#### Standard Error Responses

| HTTP Status | Exception Type | Cause | Client Action |
| --- | --- | --- | --- |
| `404 Not Found` | `LocationNotFoundError` | Address could not be resolved by geocoder. | Check query spelling; verify location is in Great Britain. |
| `404 Not Found` | `RouteNotFoundError` | OSRM cannot construct a drivable route between points. | Check if points are on disconnected road networks (e.g. islands). |
| `504 Gateway Timeout` | `GeocodingTimeoutError`, `RoutingTimeoutError` | Upstream provider (Nominatim or OSRM) timed out. | Retry request; check upstream network reachability. |
| `502 Bad Gateway` | `GeocodingProviderError`, `RoutingProviderError` | Upstream provider returned HTTP 5xx or invalid payload. | Wait for upstream service recovery. |
