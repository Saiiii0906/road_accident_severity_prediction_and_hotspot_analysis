# Vantage — Production Infrastructure & Deployment Guide

This document is the authoritative operational guide for deploying **Vantage — AI-Powered Road Safety Intelligence** into production. It details infrastructure topology, container packaging, artifact management, hardware requirements, reverse proxy TLS setup, frontend static hosting, and operational runbooks.

---

## 1. Production Architecture Overview

> [!NOTE]
> All hostnames in this guide referencing `.example.com` (e.g., `vantage.example.com`, `api.vantage.example.com`) are standard RFC 2606 placeholder templates. The deployment operator must replace them with their own registered and DNS-configured production domain names.

Vantage employs a decoupled, production-hardened client-server architecture:

```
                                  [ Internet / Users ]
                                           │
                    ┌──────────────────────┴──────────────────────┐
                    ▼                                             ▼
          [ Frontend (Static/Edge) ]                    [ Backend Host (Linux VM) ]
          Provider: Cloudflare Pages / Vercel           OS: Ubuntu 22.04 / Debian 12
          Runtime: TanStack Start + React               Specs: >= 8GB RAM, 4 vCPU, 50GB SSD
          URL: https://vantage.example.com               │
                                                         ▼
                                                [ Reverse Proxy: Caddy / Nginx ]
                                                Automatic HTTPS (Port 443)
                                                URL: https://api.vantage.example.com
                                                         │
                                                         ▼ (Proxy pass port 8000)
                                                ┌────────────────────────────────┐
                                                │ Backend Container: Docker      │
                                                │ - Uvicorn (1 worker)           │
                                                │ - FastAPI Application Stack    │
                                                │ - Pre-warmed Spatial Trees     │
                                                └───────────────┬────────────────┘
                                                                │
                                                                ▼ (Read-Only Mount)
                                                [ Persistent Disk Volume ]
                                                /app/student_A/models/
                                                accident_severity_model.pkl (7.80 GB)
```

---

## 2. Backend Hosting Requirements

Due to Student A's 7.80 GB Random Forest collision severity model, the backend **cannot** run on low-memory serverless platforms (such as AWS Lambda, Google Cloud Run with standard tiers, or free Vercel serverless functions).

### Server Sizing Specifications

| Component | Minimum Requirement | Recommended Production | Rationale |
| --- | --- | --- | --- |
| **System RAM** | 8 GB | 16 GB | Unpickling 100 deep decision trees consumes ~5.03 GB RSS. |
| **vCPU** | 2 vCPU | 4 vCPU | Model deserialization (~5s) and concurrent telemetry processing. |
| **Disk Storage** | 30 GB SSD | 50+ GB SSD (NVMe) | OS (5GB) + Docker images (1GB) + Model artifact (7.8GB) + Swap (8GB). |
| **Operating System** | Ubuntu 22.04 / 24.04 LTS or Debian 12 | Ubuntu 22.04 LTS | Standard kernel support for Docker and POSIX file locking. |
| **Recommended VPS** | AWS `c6i.xlarge` / `r6i.large`, GCP `e2-standard-4`, Hetzner `CPX41` (16GB RAM, €27/mo), DigitalOcean `16GB Memory-Optimized`. |

---

## 3. Frontend Hosting

The frontend is built with TanStack Start, React 19, and Vite.

- **Deployment Target:** Static / Edge CDN hosting (Cloudflare Pages, Vercel, or AWS S3 + CloudFront).
- **Environment Configuration:**
  - `VITE_API_BASE_URL`: Must point to the backend production domain (e.g. `https://api.vantage.example.com`).
- **Build Command:**
  ```bash
  npm run build
  ```
- **Output Artifacts:** `.output/public` (for Nitro / Cloudflare Pages / Vercel).

---

## 4. Model Storage Strategy

The Student A Random Forest artifact (`student_A/models/accident_severity_model.pkl`) is 7.80 GB (8,374,480,853 bytes). It is intentionally excluded from Git and Docker build contexts.

- **Strategy A — Persistent Host Mount [RECOMMENDED]:**
  The model is uploaded directly to the server host filesystem (e.g. `/opt/vantage/student_A/models/accident_severity_model.pkl`) via SFTP, `rsync`, or object storage CLI (`aws s3 cp` / `gcloud storage cp`). It is mounted read-only into the container.
- **Strategy B — On-Demand Streaming Bootstrap [OPTIONAL]:**
  The container entrypoint runs `scripts/acquire_model.py`. If the model is absent, it streams the binary from `VANTAGE_MODEL_SOURCE_URL` in 8 MB chunks, verifies `VANTAGE_MODEL_SHA256` if configured, and atomically renames the file into place.

---

## 5. Environment Variables

### Backend Environment Variables (`backend/.env`)

| Variable | Type | Default | Purpose |
| --- | --- | --- | --- |
| `ENVIRONMENT` | string | `production` | Declares operational environment. |
| `PORT` | integer | `8000` | Internal port Uvicorn listens on. |
| `HOST` | string | `0.0.0.0` | Bind address. |
| `LOG_LEVEL` | string | `INFO` | Logging verbosity (`INFO`, `WARNING`, `DEBUG`). |
| `CORS_ORIGINS` | string / JSON | Required in prod | Comma-separated allowed frontend domains (e.g. `https://vantage.example.com`). |
| `GEMINI_API_KEY` | secret | Required | Mandatory secret for grounded Gemini synthesis. |
| `GEMINI_MODEL` | string | `gemini-3.6-flash` | Selected Gemini generation model. |
| `LLM_PRIMARY_PROVIDER`| string | `gemini` | Primary AI provider (strictly `gemini`). |
| `STUDENT_A_MODEL_PATH`| path | `student_A/models/accident_severity_model.pkl` | Path to Random Forest model binary. |
| `VANTAGE_MODEL_SOURCE_URL` | URL | None | Remote URL for bootstrap download if unpopulated. |
| `VANTAGE_MODEL_SHA256` | hex | None | Optional SHA-256 for strict checksum validation. |

### Frontend Environment Variables (`frontend/.env`)

| Variable | Type | Default | Purpose |
| --- | --- | --- | --- |
| `VITE_API_BASE_URL` | URL | None | Production HTTPS endpoint of Vantage backend. |

---

## 6. Secret Handling & Security Posture

- **Zero Secrets in Git:** `backend/.env` is excluded in `.gitignore`. A sanitized template is provided at `backend/.env.example`.
- **Zero Secrets in Docker:** Dockerfile and Docker layers do not contain or inject any API keys.
- **No Client-Side Secrets:** Gemini API keys and provider tokens are never referenced in frontend code and never exposed to the browser.
- **Exception Sanitization:** Unhandled runtime exceptions are intercepted by `unhandled_exception_handler` in `backend/app/main.py`. Stack traces are suppressed from client responses and replaced with an opaque UUID (`error_id`).

> [!NOTE]
> All hostnames in this guide referencing `.example.com` (e.g., `vantage.example.com`, `api.vantage.example.com`) are standard RFC 2606 placeholder templates. The deployment operator must replace them with their own registered and DNS-configured production domain names.

---

## 7. Docker Build [VERIFIED SPECIFICATION]

Build the production backend image from the repository root:

```bash
docker build -t vantage-backend:latest -f Dockerfile .
```

- **Base Image:** `python:3.12-slim`
- **Image Size:** ~800 MB uncompressed (~260 MB compressed transfer size).
- **Security Check:** Verifies that `.dockerignore` prevents `accident_severity_model.pkl` (7.8 GB), raw CSVs (777 MB + 47 MB), and virtualenvs from entering the image layers.

---

## 8. Docker Run & Compose Deployment [VERIFIED SPECIFICATION]

### Using Docker Compose (Recommended)

```bash
# Start backend in detached mode
docker compose up -d

# View live container logs
docker compose logs -f backend

# Stop backend
docker compose down
```

### Direct Docker Run

```bash
docker run -d \
  --name vantage-backend \
  --restart unless-stopped \
  -p 8000:8000 \
  -v "/path/to/accident_severity_model.pkl:/app/student_A/models/accident_severity_model.pkl:ro" \
  --env-file backend/.env \
  vantage-backend:latest
```

---

## 9. Model Acquisition & Upload Procedures

### Uploading the 7.80 GB Model to the Server [REQUIRED MANUAL STEP]

From your local development machine:

```bash
# Via SCP
scp student_A/models/accident_severity_model.pkl user@your-server-ip:/opt/vantage/student_A/models/

# Via Rsync (Resumable with progress)
rsync -avzP student_A/models/accident_severity_model.pkl user@your-server-ip:/opt/vantage/student_A/models/
```

---

## 10. HTTPS & Reverse Proxy Configuration

To expose the backend securely under TLS on port 443:

### Option 1: Caddy (Automatic Let's Encrypt HTTPS) [RECOMMENDED]

Install Caddy (`sudo apt install -y caddy`) and use `deploy/Caddyfile`:

```caddy
api.vantage.example.com {
    reverse_proxy localhost:8000
    encode zstd gzip
}
```

Reload Caddy: `sudo systemctl reload caddy`.

### Option 2: Nginx with Certbot

Use the provided template at `deploy/nginx.conf`:

```bash
sudo cp deploy/nginx.conf /etc/nginx/sites-available/vantage
sudo ln -s /etc/nginx/sites-available/vantage /etc/nginx/sites-enabled/
sudo certbot --nginx -d api.vantage.example.com
sudo systemctl reload nginx
```

---

## 11. CORS Configuration

In `backend/.env`, set:

```env
CORS_ORIGINS=https://vantage.example.com
```

If testing across preview environments, provide a comma-separated list:

```env
CORS_ORIGINS=https://vantage.example.com,https://staging.vantage.example.com
```

---

## 12. Health Check & Monitoring

The container exposes a standard lightweight health check:

```bash
curl -f http://127.0.0.1:8000/health
```

Expected JSON response:
```json
{
  "status": "healthy",
  "timestamp": "2026-09-05T17:28:42.505211+00:00",
  "api_version": "1.0.0"
}
```

---

## 13. Production Verification Suite [VERIFIED]

The repository provides an automated smoke test suite at `deploy/verify_endpoints.sh`. Run it against any deployed URL:

```bash
bash deploy/verify_endpoints.sh https://api.vantage.example.com
```

Tests executed:
1. `GET /health` (Status 200)
2. `POST /api/severity/predict` (Student A Random Forest inference)
3. `POST /api/hotspots/analyze` (Student B DBSCAN clusters)
4. `POST /api/road-risk/predict` (Student C GNN topological risks)
5. `POST /api/reports/ai-infrastructure-report` (Multi-model decision support)
6. `POST /api/journey/analyze` (London Victoria → Heathrow, TfL live traffic + Gemini)
7. `POST /api/journey/analyze` (Paris → Versailles, out-of-TfL geographic scoping)

---

## 14. Update & Redeployment Procedure

When pulling new code changes to the production server:

```bash
cd /opt/vantage
git pull origin main
docker compose build
docker compose up -d
bash deploy/verify_endpoints.sh http://127.0.0.1:8000
```

---

## 15. Backup Considerations

- **Model Backup:** Ensure `accident_severity_model.pkl` is safely backed up in private cloud object storage (S3/GCS/R2).
- **Data Artifacts:** `features.pkl`, `severity_encoder.pkl`, `hotspot_summary.csv`, and `gnn_risk_predictions.json` are version-controlled in Git and require no external backup.
- **Stateless Operation:** The Vantage backend does not write to a persistent database; it is fully stateless aside from loading static models into memory.

---

## 16. Troubleshooting Runbook

| Symptom | Cause | Remedy |
| --- | --- | --- |
| Container exits with code 1 immediately | Student A model missing on disk | Verify volume mount path or configure `VANTAGE_MODEL_SOURCE_URL`. |
| Container exits with code 137 (`SIGKILL`) | Linux OOM killer terminated process | Ensure server has at least 8 GB RAM (or create an 8 GB swapfile via `deploy/setup_server.sh`). Enforce `--workers 1`. |
| `503 Service Unavailable` on API calls | Frontend `VITE_API_BASE_URL` not configured | Configure `VITE_API_BASE_URL=https://api.vantage.example.com` in frontend environment. |
| Gemini synthesis reports fallback | Missing or invalid `GEMINI_API_KEY` | Set `GEMINI_API_KEY` in `backend/.env` and restart container. |
| CORS block in browser | Frontend origin not listed in `CORS_ORIGINS` | Add frontend origin to `CORS_ORIGINS` in `backend/.env`. |

---

## 17. Resource Requirements Summary

- **Host RAM:** 8 GB minimum, 16 GB recommended.
- **Worker Count:** Strictly 1 Uvicorn worker process.
- **Disk:** 30 GB minimum SSD.
- **CPU:** 2 to 4 vCPU.

---

## 18. Known Operational Limitations

1. **Memory Ceiling:** Because the Random Forest model occupies ~5.03 GB in RAM, scaling to multiple workers requires proportional memory (e.g. 4 workers = ~20 GB RAM). For cost efficiency, a single worker with asynchronous FastAPI request concurrency is maintained.
2. **Geographic Coverage Constraints:** TfL live congestion and incident feeds cover Greater London only. Outside London (e.g. Paris or Birmingham), the system transparently marks TfL coverage as unsupported or partially supported without fabricating data.
3. **Public Rate Limits:** Upstream Nominatim geocoding operates under standard OpenStreetMap usage policies (1 req/sec). In high-volume production, a self-hosted Nominatim or commercial geocoder should be configured via `GEOCODING_BASE_URL`.
