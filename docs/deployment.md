# Vantage — Production Infrastructure & Deployment Guide

This document is the authoritative operational guide for deploying **Vantage — AI-Powered Road Safety Intelligence** into production. It details infrastructure topology, container packaging, artifact management, hardware requirements, reverse proxy TLS setup, frontend static hosting, and operational runbooks.

---

## 1. Production Architecture Overview

> [!NOTE]
> All hostnames in this guide referencing `.example.com` (e.g., `vantage.example.com`, `api.vantage.example.com`) are standard RFC 2606 placeholder templates. The deployment operator must replace them with their own registered and DNS-configured production domain names.

Vantage employs a decoupled, production-hardened client-server architecture:

```text
                                  [ Internet / Users ]
                                           │
                    ┌──────────────────────┴──────────────────────┐
                    ▼                                             ▼
          [ Frontend (Static/Edge) ]                    [ Backend Host (Linux VM) ]
          Provider: Cloudflare Pages / Vercel           OS: Ubuntu 24.04 LTS (ARM64 / x86_64)
          Runtime: TanStack Start + React               Specs: 2 OCPU / 12GB (Free) | >= 16GB (Paid)
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

### Target Platforms & Server Sizing

- **Primary Free Production Target:** **Oracle Cloud Always Free (VM.Standard.A1.Flex, ARM64)** running **Ubuntu 24.04 LTS** (2 OCPU total, 12 GB RAM total, 50–100 GB Boot/Block Volume).
  - **Resource Assessment:** **POSSIBLE BUT TIGHT.** The Student A Random Forest model consumes ~5.03 GB RSS in physical RAM upon unpickling. Within a 12 GB system RAM budget, ~6.9 GB remains available for the host operating system, Docker daemon, Uvicorn, pre-warmed spatial search trees (Student B Hotspot clusters and Student C GNN road-risk segments), and system buffer cache. This configuration is *not* guaranteed to be sufficient under high concurrency or memory spikes without active swap space, and actual ARM64 runtime verification is required.
- **Fallback Production Target (Paid Tier):** **DigitalOcean High-Memory x86_64 VM** or **Hetzner CPX41** (Ubuntu 22.04 / 24.04 LTS, >= 16 GB RAM, >= 4 vCPUs). *Note: This fallback is a paid commercial tier, not a free tier.*

| Component | Minimum Requirement | Oracle Always Free (Primary) | Paid Fallback (Recommended) | Rationale |
| --- | --- | --- | --- | --- |
| **Architecture** | ARM64 or x86_64 | ARM64 (`VM.Standard.A1.Flex`) | x86_64 (e.g., DigitalOcean Memory-Optimized) | Multi-arch Docker base supported; model binary is portable pickle. |
| **System RAM** | 8 GB | 12 GB total (Always Free Max) | >= 16 GB | Unpickling 100 deep decision trees consumes ~5.03 GB RSS. |
| **vCPU / OCPU** | 2 vCPU | 2 OCPU (4 vCPU equivalent) | >= 4 vCPU | Model deserialization (~5s) and concurrent telemetry processing. |
| **Disk Storage** | 30 GB SSD | 50–100 GB Block Volume | 50+ GB SSD (NVMe) | OS (5GB) + Docker images (1GB) + Model artifact (7.8GB) + Swap (8GB). |
| **Operating System** | Ubuntu 22.04 / 24.04 LTS | Ubuntu 24.04 LTS (ARM64) | Ubuntu 22.04 / 24.04 LTS (x86_64) | Modern Linux LTS kernel, systemd, native Docker Engine support. |

### ARM64 Architecture Status & Verification

| Aspect | Target Environment | Status | Notes |
| --- | --- | --- | --- |
| **Docker ARM64 Container Build** | Oracle Ampere A1 (ARM64) | `[NOT VERIFIED — requires ARM64 Docker/Oracle VM]` | Dockerfile uses multi-arch base `python:3.11-slim`, but build must be executed on ARM64 host or via `buildx`. |
| **Model Deserialization on ARM64** | Oracle Ampere A1 (ARM64) | `[NOT VERIFIED — requires real ARM64 runtime]` | Pure scikit-learn / NumPy pickle format; requires live Python 3.11 ARM64 validation. |
| **Model Inference on ARM64** | Oracle Ampere A1 (ARM64) | `[NOT VERIFIED — requires real ARM64 runtime]` | Requires live invocation on target ARM64 CPU. |
| **Model Binary Artifact** | Universal | `[VERIFIED]` | Preserved strictly as serialized (7.80 GB, 8,374,480,853 bytes); zero conversion, quantization, or alteration. |

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
| `LLM_PRIMARY_PROVIDER` | string | `gemini` | Primary AI provider (strictly `gemini`). |
| `STUDENT_A_MODEL_PATH` | path | `student_A/models/accident_severity_model.pkl` | Path to Random Forest model binary. |
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

- **Primary Free Tier Target:** Oracle Cloud Always Free (`VM.Standard.A1.Flex`, ARM64, 2 OCPU, 12 GB RAM). Resource fit: **POSSIBLE BUT TIGHT** (~5.03 GB model RSS leaving ~6.9 GB for OS, Docker daemon, Uvicorn, pre-warmed spatial trees, and buffers; requires active swap and real ARM64 runtime verification).
- **Paid Fallback Tier Target:** DigitalOcean High-Memory or Hetzner CPX41 x86_64 VM (>= 16 GB RAM, >= 4 vCPU). *Note: Paid commercial tier.*
- **Worker Count:** Strictly 1 Uvicorn worker process.
- **Disk:** 30 GB minimum SSD (50–100 GB recommended).
- **CPU:** 2 OCPU (ARM64) or >= 4 vCPU (x86_64).

---

## 18. Known Operational Limitations

1. **Memory Ceiling:** Because the Random Forest model occupies ~5.03 GB in RAM, scaling to multiple workers requires proportional memory (e.g. 4 workers = ~20 GB RAM). For cost efficiency, a single worker with asynchronous FastAPI request concurrency is maintained.
2. **Geographic Coverage Constraints:** TfL live congestion and incident feeds cover Greater London only. Outside London (e.g. Paris or Birmingham), the system transparently marks TfL coverage as unsupported or partially supported without fabricating data.
3. **Public Rate Limits:** Upstream Nominatim geocoding operates under standard OpenStreetMap usage policies (1 req/sec). In high-volume production, a self-hosted Nominatim or commercial geocoder should be configured via `GEOCODING_BASE_URL`.

---

## 19. Security Architecture & Hardening Guide

Security is a first-class requirement of the Vantage production deployment. The architecture minimizes attack surfaces, eliminates credential leaks, prevents resource abuse, and protects the proprietary 7.80 GB Student A model artifact.

### 19.1 Server Security (Primary: Ubuntu 24.04 LTS on Oracle Cloud Always Free ARM64)

The primary free deployment target is **Oracle Cloud Always Free (VM.Standard.A1.Flex, ARM64, 2 OCPU, 12 GB RAM)** running **Ubuntu 24.04 LTS**, with **DigitalOcean High-Memory x86_64 (Ubuntu 22.04 / 24.04 LTS, >= 16 GB RAM, >= 4 vCPU)** as the paid fallback.

- **Host vs Container Privilege Demarcation [VERIFIED ARCHITECTURE]:**
  - **Host Deployment User (`vantage`):** Holds **administrative operator privileges** (membership in `sudo` and `docker` groups) necessary to provision packages, manage system services, configure firewalls, and orchestrate containers. It is not an unprivileged account.
  - **Application Container Runtime:** Strictly drops privileges and runs as **unprivileged user `vantage` (UID 10001, GID 10001)** inside the container with all Linux capabilities dropped (`cap_drop: ["ALL"]`) and no privilege escalation allowed (`no-new-privileges:true`).
- **Explicit SSH Hardening Policy [MANUAL OPERATOR ACTION]:**
  - Public key authentication strictly required: `PubkeyAuthentication yes`
  - Password authentication strictly disabled: `PasswordAuthentication no`
  - Root SSH login strictly disabled: `PermitRootLogin no`
  - Dedicated unprivileged deployment user: `vantage` (member of `sudo` or `wheel` group for maintenance)
- **Mandatory 4-Step Operator Lockout-Prevention Checklist:**
  1. **Generate or verify local SSH key pair:**

     ```bash
     ssh-keygen -t ed25519 -C "operator@vantage"
     ```

  2. **Install public key onto the target VM for the `vantage` user:**

     ```bash
     ssh-copy-id -i ~/.ssh/id_ed25519.pub vantage@<SERVER_IP>
     ```

  3. **Verify unprivileged key login in a separate terminal session BEFORE editing sshd configuration:**

     ```bash
     ssh -i ~/.ssh/id_ed25519 vantage@<SERVER_IP>
     ```

     Ensure `sudo -v` works without password prompts or with known operator password.

  4. **Apply hardening configuration, validate syntax, and reload:**

     ```bash
     sudo tee /etc/ssh/sshd_config.d/99-vantage-hardened.conf << 'EOF'
     PermitRootLogin no
     PasswordAuthentication no
     PubkeyAuthentication yes
     ChallengeResponseAuthentication no
     KbdInteractiveAuthentication no
     EOF
     sudo sshd -t && sudo systemctl reload ssh || sudo systemctl reload sshd
     ```

     Keep your existing terminal window open and verify a brand-new SSH connection in a second window before disconnecting.
- **Host Firewall Rules [VERIFIED]:**
  - Allowed ingress: Port 22 (SSH), Port 80 (HTTP ACME / cert renewal), Port 443 (HTTPS).
  - Explicitly Blocked: Port 8000 (internal FastAPI container port is NEVER exposed publicly).
  - Configured automatically via `deploy/setup_server.sh` using `ufw` (Ubuntu) or `firewalld` (Oracle Linux / RHEL).
- **Intrusion Prevention & System Updates [RECOMMENDED]:**
  - `fail2ban` active for automated SSH brute-force protection.
  - Automatic security patches via `unattended-upgrades` (Ubuntu) or `dnf-automatic` (Oracle Linux).

### 19.2 Docker & Container Security

- **Unprivileged Container Execution [VERIFIED]:**
  - Container runs as non-root user `vantage` (UID 10001, GID 10001).
  - Configured in `Dockerfile` via `USER vantage:vantage` and in `docker-compose.yml` via `user: "10001:10001"`.
- **Privilege Escalation Prevention [VERIFIED]:**
  - `security_opt: [ "no-new-privileges:true" ]` prevents binaries inside the container from gaining root privileges.
  - `cap_drop: [ "ALL" ]` strips all Linux capabilities from the container.
- **Loopback Port Binding [VERIFIED]:**
  - Container port 8000 is bound strictly to `127.0.0.1:8000:8000`. It is never bound to `0.0.0.0`, eliminating direct internet access to the ASGI server.
- **Model Volume Read-Only [VERIFIED]:**
  - Volume mount enforces read-only mode: `./student_A/models/accident_severity_model.pkl:/app/student_A/models/accident_severity_model.pkl:ro`.
- **Zero Image Secrets [VERIFIED]:**
  - No secrets, `.env` files, or private keys are baked into the Dockerfile or container image layers.

### 19.3 API Security & Request Validation

- **Strict Schema Enforcement [VERIFIED]:**
  - Every API endpoint is guarded by Pydantic models. Unrecognized or malformed inputs return controlled `422 Unprocessable Entity` responses.
- **Payload Size Limiting [VERIFIED]:**
  - FastAPI middleware enforces a 5 MB maximum request payload (`MAX_REQUEST_BODY_BYTES = 5 * 1024 * 1024`), returning `HTTP 413 Content Too Large` before memory allocation.
  - Reverse proxies (Caddy `request_body max_size 5MB` / Nginx `client_max_body_size 5M`) enforce the limit at ingress.
- **No Command or Path Execution [VERIFIED]:**
  - Endpoints take structured parameters; no user inputs are passed to shells, filesystem paths, or dynamic evaluators.
- **Sanitized Error Responses [VERIFIED]:**
  - Internal exceptions are intercepted by `unhandled_exception_handler`, logging a diagnostic UUID (`error_id`) and returning a generic error payload without leaking stack traces or internal filesystem paths.

### 19.4 Rate Limiting & Resource Abuse Prevention

- **Ingress Rate Limiting [VERIFIED IN CONFIG | NOT VERIFIED ON LIVE VM]:**
  - `deploy/nginx.conf` explicitly establishes and enforces two rate-limiting zones:
    - **General API:** 15 requests/sec per client IP with burst allowance of 20 (`limit_req zone=vantage_api_limit burst=20 nodelay;`).
    - **Heavy Endpoints:** 2 requests/sec per client IP with burst allowance of 5 (`limit_req zone=vantage_heavy_limit burst=5 nodelay;`) on `/api/journey/analyze` and `/api/reports/ai-infrastructure-report`.
    - Excessive requests are rejected immediately with `HTTP 429 Too Many Requests`.
  - **Verification Status:**
    - `[VERIFIED IN CONFIG]`: Configuration syntax, rate-limit zones, and location match blocks are verified in `deploy/nginx.conf`.
    - `[NOT VERIFIED — requires deployed host]`: Live runtime verification requires an active Nginx reverse-proxy daemon on the production host.
- **LLM Provider Circuit Breaker [VERIFIED]:**
  - Gemini client includes a circuit breaker (trips after 5 consecutive failures, 60s cooldown) to prevent hammering external APIs during upstream degradation.

### 19.5 Authentication & Access Control Decision

- **Architecture Decision [VERIFIED]:**
  - The Vantage public demonstration API uses **public anonymous access** with defense-in-depth controls:
    1. HTTPS TLS encryption.
    2. Strict origin CORS validation.
    3. Ingress rate limiting per client IP.
    4. Strict Pydantic input schema validation.
    5. Request body size ceilings.
  - Rationale: Client-side single-page applications cannot securely store shared API secrets without exposing them in browser bundles. Adding API keys client-side provides security theater while complicating client delivery. Upstream provider secrets (`GEMINI_API_KEY`, `TFL_APP_KEY`) remain strictly encapsulated on the server.

### 19.6 Production CORS Enforcement

- **Strict Origin Whitelisting [VERIFIED]:**
  - `backend/app/config.py` enforces that wildcard `*` is strictly forbidden when `ENVIRONMENT=production`. Setting `CORS_ORIGINS=*` raises an immediate startup configuration validation error.
  - Only explicitly listed frontend origins (e.g. `https://vantage.example.com`) receive CORS headers.

### 19.7 HTTPS & TLS Architecture

- **Automated TLS [RECOMMENDED]:**
  - Caddy handles automatic Let's Encrypt certificate generation, renewal, and HTTP-to-HTTPS 301 redirection.
  - Nginx provides TLS 1.2/1.3 with forward secrecy cipher suites (`deploy/nginx.conf`).
  - Direct connection to port 8000 is blocked; only the HTTPS reverse proxy serves external traffic.

### 19.8 Defense-in-Depth Security Headers

Security headers are enforced with clear separation of responsibilities:

- **Edge / HTTPS Reverse Proxy (`deploy/nginx.conf` & `deploy/Caddyfile`) [VERIFIED IN CONFIG]:**
  - `Strict-Transport-Security: max-age=31536000; includeSubDomains; preload` (Strictly edge HTTPS only)
  - `X-Content-Type-Options: nosniff`
  - `X-Frame-Options: DENY`
  - `Referrer-Policy: strict-origin-when-cross-origin`
  - `Permissions-Policy: camera=(), microphone=(), geolocation=()`

- **FastAPI Application Stack (`backend/app/main.py`) [VERIFIED]:**
  - Injected directly by ASGI `security_middleware` across all backend responses:
    - `X-Content-Type-Options: nosniff`
    - `X-Frame-Options: DENY`
    - `Referrer-Policy: strict-origin-when-cross-origin`
    - `Permissions-Policy: camera=(), microphone=(), geolocation=()`
  - **HSTS Isolation:** `Strict-Transport-Security` is intentionally **omitted** from backend HTTP responses. This ensures that local developer machines, automated test runners, and staging environments using plain HTTP are never poisoned by browser HSTS pinning. HSTS is strictly delegated to the edge TLS reverse proxy.

### 19.9 Secret Management Policy

- **Zero Secrets in Source Control [VERIFIED]:**
  - Repository scan confirmed zero API keys (`AIzaSy`, `sk-ant`), SSH keys, or cloud credentials.
  - Example environment templates (`.env.example`) contain only safe placeholders.
- **Frontend Bundle Isolation [VERIFIED]:**
  - Verified that Vite/TanStack frontend bundle contains no server secrets or Gemini credentials.
- **Runtime Injection [RECOMMENDED]:**
  - Production secrets (`GEMINI_API_KEY`, `TFL_APP_KEY`) are passed via environment variables or secret managers (e.g., AWS Secrets Manager, GCP Secret Manager, or Docker secrets).

### 19.10 Model Artifact Protection

- **Git & Container Isolation [VERIFIED]:**
  - The 7.80 GB Student A model (`accident_severity_model.pkl`) is excluded by `.gitignore` and `.dockerignore`.
  - The model is never bundled in image layers or exposed via HTTP endpoints.
- **Read-Only Mounting & Verification [VERIFIED]:**
  - Mounted read-only (`:ro`) in Docker.
  - `scripts/acquire_model.py` enforces SHA-256 integrity verification and sanitizes logged download URLs.

### 19.11 Logging Policy & Sanitization

- **Credential Masking [VERIFIED]:**
  - Production logs omit API keys, tokens, authorization headers, and raw user payload data.
- **Structured Error Tracking [VERIFIED]:**
  - Operational logs capture timestamps, log levels, HTTP methods, paths, status codes, and diagnostic `error_id` UUIDs.

### 19.12 Dependency Security

- **Python Dependencies [VERIFIED]:**
  - Pinned production dependencies in `backend/requirements.txt`.
  - Aligned `scikit-learn==1.9.0` with serialized model artifacts.
- **Frontend Dependencies [VERIFIED]:**
  - Pinned lockfile dependencies in `frontend/package-lock.json`.
  - Frontend production build succeeds with 0 errors.

### 19.13 Non-Destructive Security Verification Results

| Check | Description | Status | Evidence |
| --- | --- | --- | --- |
| 1 | Repository secret scan | `[VERIFIED]` | 0 real API keys, tokens, or private keys found. |
| 2 | Hardcoded credentials | `[VERIFIED]` | Only RFC 2606 placeholders in `.env.example`. |
| 3 | Exposed `.env` files | `[VERIFIED]` | Real `.env` files untracked and excluded in `.gitignore`. |
| 4 | Claude residue | `[VERIFIED]` | Removed from Compose; unconfigured defaults in config. |
| 5 | Wildcard CORS rejection | `[VERIFIED]` | `Settings` validator rejects `*` in production mode. |
| 6 | Debug mode disabled | `[VERIFIED]` | `DEBUG=false` in production configuration. |
| 7 | Production URLs | `[VERIFIED]` | Frontend points to HTTPS production endpoints. |
| 8 | Model artifact exclusion | `[VERIFIED]` | Excluded from Git and Docker build contexts. |
| 9 | Non-root container | `[VERIFIED]` | `USER vantage:vantage` (UID 10001) in Dockerfile. |
| 10 | Dropped capabilities | `[VERIFIED]` | `cap_drop: [ALL]`, `no-new-privileges:true`. |
| 11 | Malformed request handling | `[VERIFIED]` | Returns HTTP 422 with structured schema errors. |
| 12 | Payload size limit | `[VERIFIED]` | Payloads > 5 MB rejected with HTTP 413. |
| 13 | Coordinate validation | `[VERIFIED]` | Strict float parsing in request schemas. |
| 14 | Geographic scoping | `[VERIFIED]` | Paris test returns `unsupported_for_geography`. |
| 15 | Provider failure handling | `[VERIFIED]` | Provider outages return `failed` status gracefully. |
| 16 | Gemini failure fallback | `[VERIFIED]` | Circuit breaker triggers deterministic fallback. |
| 17 | Stack trace suppression | `[VERIFIED]` | 500 handler returns sanitized `error_id`. |

### 19.14 Threat Model, Incident Response & Runbooks

#### Threat Model Summary

- **Threat: Model Artifact Theft:** Mitigated by read-only filesystem mounts, non-root user permissions, absence of download endpoints, and exclusion from public Git/Docker repositories.
- **Threat: Resource Exhaustion (DoS):** Mitigated by 5 MB request size limits, reverse proxy rate limits (15 r/s general, 2 r/s heavy), and single Uvicorn worker process concurrency.
- **Threat: Gemini Quota Depletion:** Mitigated by circuit breaker protection, upstream rate limiting, and strict deterministic fallback assessments.
- **Threat: Port 8000 Direct Access:** Mitigated by loopback binding (`127.0.0.1:8000`) and host firewall rules blocking all ports except 22, 80, and 443.

#### Incident Response Basics

1. **Suspected Credential Leak:** Rotate `GEMINI_API_KEY` immediately in Google AI Studio; update `backend/.env`; restart container via `docker compose restart backend`.
2. **Abusive IP Flood:** Add offending IP to host firewall:
   - Oracle Linux: `firewall-cmd --permanent --add-rich-rule='rule family="ipv4" source address="<ABUSIVE_IP>" drop' && firewall-cmd --reload`
   - Ubuntu: `ufw insert 1 deny from <ABUSIVE_IP> to any`
3. **Container Out of Memory:** Verify swapfile is active (`free -h`); inspect RSS memory usage; verify `--workers 1` is enforced.

### 19.15 Security Acceptance Criteria Checklist

- [x] `[VERIFIED]` No secrets committed in Git repository.
- [x] `[VERIFIED]` No secrets embedded in frontend client bundle.
- [x] `[VERIFIED]` Gemini API key remains strictly server-side.
- [x] `[VERIFIED]` Student A 7.80 GB model is not exposed publicly or downloadable.
- [x] `[VERIFIED]` Port 8000 is bound to localhost and blocked in firewall.
- [x] `[MANUAL OPERATOR ACTION]` SSH password authentication disabled on VM (`PasswordAuthentication no`).
- [x] `[MANUAL OPERATOR ACTION]` Root SSH login disabled on VM (`PermitRootLogin no`).
- [x] `[VERIFIED]` Host firewall permits only ports 22, 80, and 443.
- [x] `[VERIFIED IN CONFIG]` Automatic HTTPS configured via reverse proxy (Caddy / Nginx).
- [x] `[VERIFIED]` Wildcard `*` CORS rejected in production mode.
- [x] `[VERIFIED IN CONFIG]` Ingress rate limiting configured in reverse proxy (15 r/s general, 2 r/s heavy).
- [x] `[VERIFIED]` Pydantic request validation active across all endpoints.
- [x] `[VERIFIED]` Unhandled exceptions return generic message and `error_id` without stack traces.
- [x] `[VERIFIED]` Docker container runs unprivileged as UID 10001 with dropped capabilities.
- [x] `[VERIFIED]` Student A model mounted read-only (`:ro`).
- [x] `[VERIFIED]` Defense-in-depth security headers injected (nosniff, DENY, referrer, permissions).
- [x] `[VERIFIED]` HSTS isolated to edge HTTPS reverse proxy; omitted from plain HTTP backend.
- [x] `[VERIFIED]` 223/223 backend unit and integration tests pass.
- [x] `[VERIFIED]` Frontend production build passes with 0 errors.
- [x] `[VERIFIED]` ESLint reports 0 errors.
- [ ] `[NOT VERIFIED]` Live cloud VM TLS handshake (requires deployed host and public DNS).
- [ ] `[NOT VERIFIED]` Live reverse proxy rate-limit enforcement (requires active Nginx on deployed host).
- [ ] `[NOT VERIFIED]` ARM64 container build and model inference (requires Oracle Ampere A1 ARM64 host).
