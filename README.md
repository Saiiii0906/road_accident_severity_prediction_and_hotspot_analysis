# Vantage — AI-Powered Road Safety & Traffic Intelligence

**Vantage** is an advanced road safety intelligence and traffic risk analysis platform. It combines empirical machine learning models, spatial clustering, road-network graph analysis, real-time atmospheric and traffic telemetry, and grounded generative AI synthesis to deliver explainable, evidence-backed journey safety assessments and transport infrastructure insights.

---

## Key Capabilities

- **Journey Safety Analysis:** Multi-source route corridor evaluation uniting real-time geocoding, route planning, atmospheric conditions, live traffic congestion, active road disruptions, historical accident clusters, and structural network risks.
- **Severity Prediction:** 138-feature Random Forest classifier predicting post-collision injury severity distributions (`Fatal`, `Serious`, `Slight`) given empirical environmental, road, and vehicle parameters.
- **Hotspot Explorer:** In-memory density-based spatial clustering (DBSCAN) over 3,700+ historical accident clusters across Great Britain with radius and bounding box filters.
- **Road Risk Analysis:** Graph Neural Network (GNN) modeling structural and topological crash vulnerability over 13,900+ road segments across the primary UK road network.
- **AI Infrastructure Report:** Evidence-grounded multi-model decision-support report synthesizing regional collision patterns into prioritized transport safety interventions.
- **Deterministic PDF Export:** Instant, client-side vector PDF generation producing structured, two-page executive safety briefings with zero server-side rendering dependencies.
- **Transparent Risk Communication:** Rejects arbitrary, uncalibrated composite risk percentages in favor of verified categorical hazard factors and an itemized evidence inventory.

---

## High-Level Journey Safety Workflow

```text
[Origin & Destination Input]
             │
             ▼
   [Geocoding & Routing] ────────── Nominatim OSM & Project OSRM
             │
             ▼
  [Live Context Telemetry] ──────── Open-Meteo (Weather) & TfL Unified API (Traffic/Incidents)
             │
             ▼
[Historical Corridor Alignment] ─── 1,000m Buffer Matching vs. DBSCAN Hotspots & GNN Graph
             │
             ▼
[Deterministic Risk Assessment] ── Calibrated Hazard Categorization (overall_score = None)
             │
             ▼
  [Grounded Gemini Synthesis] ───── Structured Narrative & Actionable Precaution Synthesis
             │
             ▼
   [Interactive UI & PDF Export] ── Dynamic Map, Telemetry Cards & 2-Page Vector PDF
```

---

## System Architecture & Module Overview

Vantage standardizes its public interfaces around six intuitive domain modules:

| Public Module Name | Primary Function | Underlying Engine / Model |
| --- | --- | --- |
| **Journey Safety Analysis** | Route corridor multi-source safety assessment | Multi-provider pipeline + Deterministic Assessment + Gemini |
| **Severity Prediction** | Collision injury severity classification | 138-feature Random Forest Classifier (`Student A`) |
| **Hotspot Explorer** | Spatial accident cluster density mapping | DBSCAN Density-Based Clustering (`Student B`) |
| **Road Risk Analysis** | Structural network topological risk evaluation | Graph Neural Network (GNN) on Road Graphs (`Student C`) |
| **AI Infrastructure Report** | Transport planning decision-support report | Multi-Model Grounding + Grounded Gemini Synthesis |
| **History** | Persistent record of user analysis runs | Browser Structured LocalStorage (`vantage_analysis_history`) |

---

## Technology Stack

- **Frontend:** [TanStack Start](https://tanstack.com/start), React 19, TypeScript, Tailwind CSS v4, Radix UI primitives, Lucide React, Leaflet, jsPDF.
- **Backend:** Python 3.12+, FastAPI, Pydantic v2, Uvicorn, NumPy, Pandas, Scikit-Learn.
- **AI & Synthesis:** Google Gemini (configured as `gemini-3.6-flash` via Gemini Developer API, with optional Anthropic Claude multi-provider routing).
- **Geospatial & Telemetry:** OpenStreetMap Nominatim, Project OSRM, Open-Meteo Forecast API, Transport for London (TfL) Unified API.

---

## Repository Structure

```text
.
├── backend/
│   ├── app/
│   │   ├── config.py           # Application settings & environment resolution
│   │   ├── main.py             # FastAPI entrypoint, lifespan & exception handlers
│   │   ├── routes/             # API endpoints (severity, hotspot, risk, report, journey)
│   │   ├── schemas/            # Strict Pydantic v2 data contracts
│   │   └── services/           # Business logic, corridor matching, telemetry, prompt engineering
│   ├── tests/                  # 14 test suites, 202 unit & integration tests
│   ├── requirements.txt        # Backend Python dependencies
│   └── .env.example            # Environment variable template
├── frontend/
│   ├── src/
│   │   ├── components/         # UI primitives, layout, and module views
│   │   ├── constants/          # Navigation and theme tokens
│   │   ├── lib/                # API client, PDF generators, coordinate math
│   │   ├── routes/             # TanStack Start file-based routing
│   │   └── styles.css          # Global Tailwind styles & CSS variables
│   ├── package.json            # Frontend dependencies & scripts
│   └── vite.config.ts          # Vite & TanStack Router configuration
├── student_A/
│   └── models/                 # Random Forest classifier (7.8 GB), feature names, label encoder
├── student_B/
│   ├── generate_hotspots.py    # DBSCAN clustering pipeline script
│   └── results/                # Cluster evaluation outputs
├── student_C/
│   ├── gnn_model.pth           # Trained PyTorch GNN weights
│   └── gnn_risk_predictions.json # Precomputed predictions for 13,921 road segments
├── data/
│   └── output/                 # hotspot_summary.csv (3,705 cluster centroids)
├── docs/                       # Comprehensive documentation suite
└── README.md                   # Repository overview
```

---

## Quickstart & Local Setup

### Prerequisites

- Python 3.12+
- Node.js 18+ (Node 20 LTS recommended) & npm
- $\ge 12\text{ GB RAM}$ recommended (due to the 7.8 GB Student A Random Forest artifact)

### 1. Backend Setup

```bash
# Navigate to backend and create virtual environment
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env and insert your GEMINI_API_KEY

# Start backend server
uvicorn app.main:app --reload --port 8000
```

### 2. Frontend Setup

```bash
# In a separate terminal, navigate to frontend
cd frontend

# Install packages
npm install

# Start Vite development server
npm run dev
```

Open `http://localhost:5173` in your browser. Interactive API documentation is available at `http://localhost:8000/docs`.

---

## Testing & Verification

```bash
# Run all backend unit and integration tests (202 tests):
python3 -m unittest discover -s backend/tests -v

# Verify frontend TypeScript compilation and production build:
cd frontend && npm run build
```

---

## Documentation

Exhaustive technical documentation is available in the [`docs/`](docs/README.md) directory:

- [**System Architecture**](docs/architecture.md) — Component interactions, data flows, and boundaries.
- [**System Overview**](docs/system-overview.md) — Product vision, core analytical concepts, and telemetry layers.
- [**Frontend Architecture**](docs/frontend.md) — TanStack Start, React 19, layouts, state, and PDF export.
- [**Backend Architecture**](docs/backend.md) — FastAPI lifespan, service architecture, and resilience patterns.
- [**REST API Reference**](docs/api.md) — Complete endpoint schemas, request/response models, and error codes.
- [**Machine Learning Models**](docs/models.md) — Methodologies for Severity Prediction, Hotspots, and GNN Risk.
- [**Journey Safety Pipeline**](docs/journey-safety.md) — Detailed 11-step analysis workflow and deterministic guardrails.
- [**Gemini & Generative AI**](docs/ai-gemini.md) — Grounding constraints, prompt engineering, and fallbacks.
- [**Design System**](docs/design-system.md) — Visual tokens, semantic risk colors, and component patterns.
- [**Local Setup Guide**](docs/setup.md) — Step-by-step developer environment installation and troubleshooting.
- [**Deployment Guide**](docs/deployment.md) — Memory constraints, containerization considerations, and security.
- [**System Limitations**](docs/limitations.md) — Geographic boundaries, model scopes, and provider constraints.

---

## Key System Limitations

1. **Crash-Level vs. Route-Level Prediction:** Severity Prediction (Student A) evaluates conditional injury severity assuming a collision occurs. It is **not** a prospective route risk model.
2. **Hotspot Semantics:** Absence of a DBSCAN hotspot (0 clusters) indicates no dense recurring collision clusters; it does **not** indicate zero historical accidents.
3. **Geographic Scoping:** Historical machine learning models are calibrated exclusively on UK Road Safety data $[50.0^\circ\text{ N}, 60.5^\circ\text{ N}] \times [-6.5^\circ\text{ E}, 2.0^\circ\text{ E}]$. Live traffic and incident telemetry are scoped to Greater London via TfL.
4. **No Single Composite Score:** `overall_score` is intentionally `None` (**NOT ASSIGNED**) to avoid arbitrary, uncalibrated scalar weightings across heterogeneous data.
5. **Model Memory Footprint:** The Student A Random Forest artifact is 7.8 GB, requiring $\ge 12\text{ GB RAM}$ during startup unpickling.

For a full treatment, see [System Limitations](docs/limitations.md).

---

## Project Status

- **Version:** `1.0.0`
- **Deployment Status:** Local / Development / Staging Ready. Containerized cloud deployment architecture is planned and requires addressing the 7.8 GB model artifact footprint.
- **License:** MIT License
