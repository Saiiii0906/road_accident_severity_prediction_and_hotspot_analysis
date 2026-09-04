# Vantage System Architecture

This document describes the end-to-end architecture of **Vantage**, including component interactions, service boundaries, data pipelines, external integrations, and persistence mechanisms.

---

## 1. High-Level Architecture

Vantage is organized into a modular decoupled architecture comprising a TypeScript/React frontend, a Python/FastAPI analytical backend, precomputed and real-time machine learning inference engines, external geospatial/telemetry feeds, and grounded generative AI synthesis.

```mermaid
flowchart TB
    subgraph Client ["Client Layer (Browser)"]
        UI["TanStack Start + React 19 UI"]
        HistoryStore["LocalStorage (vantage_analysis_history)"]
        PDFGen["Client-Side PDF Generator (jspdf)"]
    end

    subgraph Gateway ["API & Application Gateway"]
        FastAPI["FastAPI ASGI Server (:8000)"]
        CORS["CORS Middleware & Exception Handlers"]
    end

    subgraph CoreServices ["Backend Analytical Services"]
        GeoService["Geocoding Service (Nominatim OSM)"]
        RouteService["Routing Service (OSRM Driving)"]
        LiveService["Live Context (Open-Meteo Weather + TfL Traffic/Incidents)"]
        CorridorService["Corridor Matching Service (Vectorized Spatial Buffers)"]
        DetAssessment["Deterministic Safety Assessment Engine"]
        ReportService["AI Infrastructure Report Service"]
        PromptService["Journey Prompt Engineering Service"]
        LLMRouter["LLM Provider Router (Gemini / Claude)"]
    end

    subgraph MLEngines ["Empirical & Machine Learning Models"]
        ModelA["Severity Prediction (Student A: Random Forest)"]
        ModelB["Hotspot Explorer (Student B: DBSCAN Spatial Clusters)"]
        ModelC["Road Risk Analysis (Student C: Graph Neural Network)"]
    end

    subgraph ExternalFeeds ["External Providers & Cloud APIs"]
        NominatimAPI["OpenStreetMap Nominatim API"]
        OSRMAPI["OSRM Routing Engine"]
        MeteoAPI["Open-Meteo Weather API"]
        TfLAPI["Transport for London (TfL) Unified API"]
        GeminiAPI["Google Gemini API (gemini-3.6-flash)"]
    end

    UI <-->|"JSON over HTTP /api/*"| FastAPI
    FastAPI --> CORS
    CORS --> CoreServices

    GeoService <--> NominatimAPI
    RouteService <--> OSRMAPI
    LiveService <--> MeteoAPI
    LiveService <--> TfLAPI
    LLMRouter <--> GeminiAPI

    CorridorService --> ModelB
    CorridorService --> ModelC
    FastAPI --> ModelA

    CoreServices --> DetAssessment
    DetAssessment --> PromptService
    PromptService --> LLMRouter

    UI --> HistoryStore
    UI --> PDFGen
```

---

## 2. Frontend Layer

The frontend application is built using **TanStack Start** (full-stack framework powered by Vite and Nitro) and **React 19**.

- **Routing:** File-based routing implemented via `@tanstack/react-router` in `frontend/src/routes/`.
- **Layout Hierarchy:** `__root.tsx` mounts the global theme and HTML skeleton. `AppShell` encapsulates the collapsible navigation sidebar (`AppSidebar`) and top action bar (`AppNavbar`).
- **State Management & Data Fetching:** Server communication is handled using `@tanstack/react-query` mutations and native fetch clients in `frontend/src/lib/api/client.ts`.
- **UI Components:** Styled with **Tailwind CSS v4** and accessible primitives from **Radix UI**, with iconography from **Lucide React**.
- **Interactive Mapping:** Geographic coordinates and journey corridors are rendered using **Leaflet** with custom tile layers.
- **Client-Side Document Export:** PDF reports are compiled entirely client-side using `jspdf` and `jspdf-autotable`, rendering two-page deterministic documents without server-side headless browser overhead.
- **History Storage:** Analysis runs and queries are saved locally in the browser's `localStorage` (`vantage_analysis_history`) with zero backend user-session tracking.

---

## 3. Backend Layer

The backend is built with **FastAPI** (Python 3.12+), utilizing **Pydantic v2** for strict data validation and serialization.

### Application Lifecycle & Lifespan Management

FastAPI's `@asynccontextmanager lifespan` in `backend/app/main.py` manages singleton initialization during application startup:

1. **Student A Model:** `SeverityModelManager.get_instance().load()` pre-loads the Random Forest classifier and feature definitions into memory.
2. **Student B Hotspots:** `HotspotDataManager().load()` reads precomputed DBSCAN cluster centroids (`data/output/hotspot_summary.csv`) and caches vectorized radian coordinates for fast Haversine filtering.
3. **Student C Risk Graph:** `RiskDataManager().load()` parses topological road segment risks (`student_C/gnn_risk_predictions.json`) into contiguous NumPy arrays.
4. **Corridor Spatial Indexes:** `CorridorMatchingService.prewarm()` ensures spatial index structures are instantiated prior to serving live traffic.

### Router Architecture

All domain routers are mounted both at the root level and under `/api` for backwards compatibility:

- `severity_route.py` $\rightarrow$ `/severity/predict`, `/severity/predict-batch`
- `hotspot_route.py` $\rightarrow$ `/hotspots/analyze`
- `risk_route.py` $\rightarrow$ `/road-risk/predict`, `/risk/assess` (legacy compatibility)
- `report_route.py` $\rightarrow$ `/reports/ai-infrastructure-report`
- `journey_route.py` $\rightarrow$ `/journey/analyze`

### Error Handling & Security

- **Unhandled Exceptions:** A centralized `unhandled_exception_handler` catches unhandled Python exceptions, generates a unique diagnostic `error_id` (`err-<12hex>`), logs the traceback securely, and returns an HTTP 500 without leaking internal stack traces.
- **CORS Middleware:** Configured via `settings.CORS_ORIGINS` supporting JSON arrays or comma-separated lists, allowing development origins while restricting unauthorized external access.

---

## 4. Machine Learning Model Layer

The analytical foundation of Vantage integrates three empirical models calibrated on the UK Road Safety Dataset:

```mermaid
classDiagram
    class SeverityPredictionEngine {
        +RandomForestClassifier model
        +List~str~ feature_names (138)
        +LabelEncoder encoder
        +predict(features) SeverityResult
    }
    class SpatialHotspotClusterer {
        +DataFrame hotspot_summary (3,705 clusters)
        +ndarray lats_rad, lons_rad
        +query_radius(center, radius_km) List~HotspotCluster~
        +query_bbox(min_lat, max_lat, ...) List~HotspotCluster~
    }
    class RoadRiskGNNTopology {
        +ndarray edge_ids, road_numbers (13,921 segments)
        +ndarray predicted_risks, coords
        +query_corridor(corridor_points, buffer_m) List~RoadSegment~
        +query_road(road_number) List~RoadSegment~
    }
    SeverityPredictionEngine <-- Student_A_Implementation : Internal
    SpatialHotspotClusterer <-- Student_B_Implementation : Internal
    RoadRiskGNNTopology <-- Student_C_Implementation : Internal
```

1. **Severity Prediction (Student A):** Random Forest classifier evaluating 138 transformed features for a specific crash scenario, outputting class probabilities across `Fatal`, `Serious`, and `Slight`.
2. **Hotspot Explorer (Student B):** DBSCAN spatial clustering identifying 3,705 empirical collision concentration zones across Great Britain, indexing cluster centroids, accident counts, and severity breakdowns.
3. **Road Risk Analysis (Student C):** Graph Neural Network (GNN) modeling structural and topological crash likelihood over 13,921 UK road segments, capturing node connectivity and edge betweenness.

---

## 5. External Telemetry & Service Integrations

| Provider | Service | Integration Type | Fallback / Resilience |
| --- | --- | --- | --- |
| **OpenStreetMap Nominatim** | Forward Geocoding | HTTP REST API | In-memory LRU cache (512 entries, 1 hr TTL), strict UK bounding box validation |
| **OSRM (Project OSRM)** | Vehicle Route Planning | HTTP REST API | Polyline geometry decoding, multi-point coordinate sampling |
| **Open-Meteo** | Atmospheric Telemetry | HTTP REST API | Hourly forecast query at origin, destination, and midpoint |
| **Transport for London (TfL)** | Live Traffic Delays & Incidents | HTTP REST API (Unified) | Scoped strictly to Greater London road network; marks non-London as unmonitored |
| **Google Gemini API** | Evidence Synthesis | Google GenAI SDK | Multi-tier retry, circuit breaker, timeout limits, deterministic fallback |

---

## 6. End-to-End Journey Safety Pipeline

The primary workflow of Vantage is the multi-source **Journey Safety Analysis** pipeline (`backend/app/services/journey_service.py`):

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant Frontend as TanStack Start UI
    participant Backend as FastAPI Gateway
    participant Geocoder as Nominatim OSM
    participant Router as OSRM Engine
    participant Telemetry as Live Feeds (Meteo + TfL)
    participant Corridor as Spatial Corridor Matcher
    participant Models as ML Models (B & C)
    participant Deterministic as Deterministic Assessor
    participant LLM as Gemini (gemini-3.6-flash)

    User->>Frontend: Submit Origin, Destination, Date & Time
    Frontend->>Backend: POST /api/journey/analyze
    Backend->>Geocoder: Geocode Origin & Destination (UK BBox)
    Geocoder-->>Backend: Latitude / Longitude Coordinates
    Backend->>Router: Request Driving Route & Polyline
    Router-->>Backend: Route Distance, Duration & Geometry
    
    par Fetch Live Telemetry
        Backend->>Telemetry: Query Open-Meteo Weather & TfL Status
        Telemetry-->>Backend: Atmospheric Context & Traffic Delays
    and Match Historical Models
        Backend->>Corridor: Sample 1,000m Buffer along Polyline
        Corridor->>Models: Match Hotspots (Student B) & GNN Segments (Student C)
        Models-->>Corridor: Intersected Hotspots & High-Risk Segments
        Corridor-->>Backend: Consolidated Historical Evidence
    end

    Backend->>Deterministic: Evaluate Verified Hazards & Factor Severity
    Note over Deterministic: overall_score = null (Defensible Categorical Assessment)
    Deterministic-->>Backend: Deterministic Safety Assessment

    alt Gemini Synthesis Available
        Backend->>LLM: Pass Structured Evidence Payload + Grounding Rules
        LLM-->>Backend: Structured Executive Summary & Recommendations
    else Synthesis Disabled / Fails Schema
        Backend-->>Backend: Attach Safe Deterministic Fallback Message
    end

    Backend-->>Frontend: JourneyAnalyzeResponse JSON
    Frontend->>User: Render Interactive Map, Factor Cards & Telemetry
    opt User Requests PDF
        Frontend->>Frontend: Generate 2-Page Clean Deterministic PDF
    end
```

---

## 7. Responsibility Boundaries

To maintain scientific integrity and operational stability, strict separation of concerns is enforced:

- **Deterministic Authority:** The backend deterministic scoring engine (`safety_assessment_service.py`) is the sole authority on route risk factors, severity tiers, and hazard identification.
- **Generative Role:** Gemini acts solely as an evidence synthesizer and human-readable communicator. It is bound by 13 negative constraints prohibiting the fabrication of scores, numbers, or unmonitored conditions.
- **Client Responsibilities:** The browser handles presentation, route geometry decoding, interactive map rendering, PDF compilation, and local query history storage.
- **Provider Isolation:** Failures in external live feeds (e.g. TfL outage or weather rate-limit) degrade gracefully to `partial` or `unavailable` statuses without aborting the overall journey analysis.
