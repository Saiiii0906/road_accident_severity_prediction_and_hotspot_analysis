# Vantage Deployment & Infrastructure Guide

This document provides a comprehensive operational guide to deploying **Vantage — AI-Powered Road Safety Intelligence**, detailing container packaging, artifact acquisition, volume mount strategies, hardware prerequisites, and runtime configuration.

---

## 1. Container Architecture & Packaging

The Vantage backend is containerized as a portable, production-grade container image using `Dockerfile` at the repository root.

### Packaging Strategy

- **Base Image:** `python:3.12-slim` (Debian Linux)
- **Lean Image Footprint:** The Docker image packages the application source, runtime dependencies (`backend/requirements.txt`), and small static data artifacts (`features.pkl`, `severity_encoder.pkl`, `hotspot_summary.csv`, `gnn_risk_predictions.json`).
- **External Model Management:** The 7.80 GB Student A Random Forest artifact (`accident_severity_model.pkl`) is **intentionally excluded** from the image build via `.dockerignore`. It is provided at runtime via either:
  1. Persistent Volume Mount (Recommended)
  2. On-Demand Stream Acquisition via `scripts/acquire_model.py`
- **Resulting Image Size:** ~800 MB uncompressed (~260 MB compressed transfer size), avoiding multi-gigabyte container registries and slow deployments.

### Building the Production Image

To build the container image:

```bash
docker build -t vantage-backend:latest -f Dockerfile .
```

*Note: The build does not require the 7.80 GB model, credentials, or cloud access.*

---

## 2. Model Artifact & Acquisition Strategy

Student A's Random Forest collision severity model (`student_A/models/accident_severity_model.pkl`) is 7.80 GB (8,374,480,853 bytes). Because it is untracked by Git, production infrastructure must supply it deterministically.

### Lifecycle & Invariants

1. **Storage Provisioning:** A persistent cloud volume or local directory is mounted to `/app/student_A/models/accident_severity_model.pkl`.
2. **Pre-Flight Integrity Check:** On startup, `entrypoint.sh` executes `scripts/acquire_model.py`.
3. **Skip if Valid:** If the model file already exists on disk and passes integrity checks, acquisition is skipped immediately.
4. **Streaming Download (If absent):** If absent and `VANTAGE_MODEL_SOURCE_URL` is set, the utility streams the artifact in 8 MB chunks to a temporary file (`.tmp`), computes SHA-256 on the fly, verifies integrity, and atomically replaces the file using `os.replace`.
5. **Fail-Fast Behavior:** If the model is missing and `VANTAGE_MODEL_SOURCE_URL` is unset, container startup aborts immediately with exit code 1. The application **never** falls back to mock or fabricated severity predictions.
6. **Persistence Across Restarts:** Once acquired or mounted on persistent disk, the model remains available across container restarts without re-downloading.

### Configuration Environment Variables

| Variable | Description | Default | Required |
| --- | --- | --- | --- |
| `STUDENT_A_MODEL_PATH` | Path to Student A model binary | `student_A/models/accident_severity_model.pkl` | No |
| `VANTAGE_MODEL_SOURCE_URL` | Remote URL (S3/GCS/HTTP) to acquire model if absent | `None` | Only if volume unpopulated |
| `VANTAGE_MODEL_SHA256` | Expected SHA-256 checksum for integrity validation | `None` | Recommended in production |
| `VANTAGE_MODEL_CHUNK_SIZE_MB` | Streaming chunk size for acquisition | `8` | No |
| `VANTAGE_MODEL_TIMEOUT_SECONDS`| Download socket timeout | `3600` | No |

---

## 3. Worker Concurrency & Memory Constraints

> [!CRITICAL]
> **Single Worker Mandate (`--workers 1`)**  
> Unpickling the 7.80 GB Student A model consumes approximately **5.03 GB resident set size (RSS)** in process memory.  
> Standard multi-worker process pools (e.g. `--workers 4`) would duplicate the model 4 times, requiring over 20 GB of RAM and triggering immediate Out-Of-Memory (`SIGKILL` / exit code 137).  
> The container entrypoint enforces strictly **one Uvicorn worker process**.

### Hardware & Resource Sizing

| Metric | Minimum Requirement | Recommended Production |
| --- | --- | --- |
| **System RAM** | 8 GB | 16 GB |
| **vCPU** | 2 vCPU | 4 vCPU |
| **Disk Storage** | 20 GB SSD | 50 GB SSD (NVMe preferred) |
| **Worker Count** | 1 worker | 1 worker |
| **Model Load Time** | ~5.0 to 7.0 seconds | ~4.0 to 5.5 seconds (NVMe) |

---

## 4. Local Container Testing & Docker Compose

For local testing with the real 7.80 GB model artifact:

### Using Docker Run (Mounting Local Model)

```bash
docker run -d \
  --name vantage-backend \
  -p 8000:8000 \
  -v "$(pwd)/student_A/models/accident_severity_model.pkl:/app/student_A/models/accident_severity_model.pkl:ro" \
  -e GEMINI_API_KEY="your-gemini-key" \
  vantage-backend:latest
```

### Using Docker Compose

A pre-configured `docker-compose.yml` is provided for local production-like verification:

```bash
docker compose up -d --build
```

### Verifying Container Health & Inference

1. **Liveness / Healthcheck:**
   ```bash
   curl http://localhost:8000/health
   # Response: {"status": "healthy", "timestamp": "...", "api_version": "1.0.0"}
   ```

2. **Severity Prediction Inference:**
   ```bash
   curl -X POST http://localhost:8000/api/severity/predict \
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
     }'
   ```

---

## 5. Security & Configuration Audit

- **Zero Hardcoded Secrets:** Dockerfile, compose files, and acquisition scripts contain no API keys, tokens, or private endpoints.
- **Environment Isolation:** Secrets (`GEMINI_API_KEY`, `CLAUDE_API_KEY`) are injected via environment variables or secret managers.
- **Sanitized Logging:** `scripts/acquire_model.py` automatically strips query parameters and authorization headers before logging URLs.
- **CORS Configuration:** `CORS_ORIGINS` defaults to development localhost origins and must be updated to the production frontend domain in deployment settings.
