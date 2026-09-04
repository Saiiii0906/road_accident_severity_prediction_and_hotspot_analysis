# Vantage Local Setup & Developer Guide

This guide provides complete instructions for configuring, running, and verifying the **Vantage** platform in a local development environment.

---

## 1. System Prerequisites

Before starting, ensure your host system has the following installed:

- **Python:** Version `3.12` or higher (verified with Python 3.12/3.14).
- **Node.js:** Version `18.x` or higher (recommended: Node 20 LTS or Node 22).
- **Package Manager:** `npm` (v9+) or `pnpm`.
- **System Memory:** Minimum **12 GB RAM** recommended due to the 7.8 GB Student A Random Forest model artifact deserialization.

---

## 2. Repository Cloning & Structure

Clone the repository and enter the project root:

```bash
git clone <repository-url>
cd road_accident_severity_prediction_and_hotspot_analysis
```

---

## 3. Backend Setup

### Step 3.1: Create & Activate Virtual Environment

```bash
cd backend
python3 -m venv venv

# On macOS / Linux:
source venv/bin/activate

# On Windows (PowerShell):
.\venv\Scripts\Activate.ps1
```

### Step 3.2: Install Python Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 3.3: Configure Environment Variables

Copy the template configuration file:

```bash
cp .env.example .env
```

Edit `backend/.env` to configure your API keys and parameters:

```dotenv
# API Configuration
PROJECT_NAME="Road Accident Severity Prediction & Hotspot Analysis"
DEBUG=false

# CORS Allowed Origins
CORS_ORIGINS=http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173

# External Geospatial & Live Providers
NOMINATIM_BASE_URL=https://nominatim.openstreetmap.org
OSRM_BASE_URL=https://router.project-osrm.org
OPEN_METEO_BASE_URL=https://api.open-meteo.com
TFL_BASE_URL=https://api.tfl.gov.uk
TFL_APP_KEY=  # Optional: leave blank for unauthenticated public rate limits

# Google Gemini API (Required for Journey AI Synthesis & Reports)
GEMINI_API_KEY=<your-google-gemini-api-key>
GEMINI_MODEL=gemini-3.6-flash
```

### Step 3.4: Verify Model Artifacts

Ensure the empirical model files are present in their designated paths:

- `student_A/models/accident_severity_model.pkl` (7.8 GB)
- `student_A/models/severity_encoder.pkl`
- `data/output/hotspot_summary.csv` (3,705 DBSCAN clusters)
- `student_C/gnn_risk_predictions.json` (13,921 GNN road segments)

### Step 3.5: Launch the Backend Server

```bash
uvicorn app.main:app --reload --port 8000
```

The backend API is now running at `http://localhost:8000`. You can inspect the interactive documentation at `http://localhost:8000/docs`.

---

## 4. Frontend Setup

In a new terminal window:

### Step 4.1: Install Dependencies

```bash
cd frontend
npm install
```

### Step 4.2: Start the Development Server

```bash
npm run dev
```

The frontend Vite server starts at `http://localhost:5173`. Open your browser and navigate to `http://localhost:5173` to access the Vantage web application.

---

## 5. Running Automated Test Suites

### Backend Unit & Integration Tests

The backend test suite contains 202 unit and integration tests covering routing, geocoding, live context, historical corridor matching, deterministic assessment, and Gemini synthesis:

```bash
# Run from repository root with active virtual environment:
python3 -m unittest discover -s backend/tests -v
```

Expected output:

```text
Ran 202 tests in 2.7s
OK
```

### Frontend TypeScript Compilation & Build

To verify that all frontend TypeScript types and bundles compile cleanly:

```bash
# Run from frontend directory:
npm run build
```

Expected output:

```text
vite v8.2.0 building for production...
✓ built in 1.4s
```

---

## 6. Service URL Summary

| Service / Interface | Local Address |
| --- | --- |
| **Vantage Frontend App** | `http://localhost:5173` |
| **Backend REST API** | `http://localhost:8000` |
| **API Health Check** | `http://localhost:8000/health` |
| **Interactive Swagger Docs** | `http://localhost:8000/docs` |
| **ReDoc Technical Schema** | `http://localhost:8000/redoc` |
