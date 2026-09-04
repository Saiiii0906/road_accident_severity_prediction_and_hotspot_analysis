# Vantage Deployment & Infrastructure Guide

This document provides an honest, comprehensive evaluation of the current deployment posture of **Vantage**, detailing infrastructure prerequisites, external egress requirements, security controls, and the critical memory constraints imposed by large machine learning artifacts.

---

## 1. Current Deployment Status

> [!IMPORTANT]
> **Status: Planned / Not Yet Implemented for Production**  
> Vantage is currently structured and validated for local and staging environments. No automated containerization (`Dockerfile` or `docker-compose.yml`), continuous deployment (CI/CD) pipelines, or production cloud infrastructure are checked into the repository at this time.

The application components, however, compile cleanly into production-ready binaries:

- **Frontend:** Compiles to static distribution assets via `npm run build` using Vite.
- **Backend:** Serves production traffic via standard ASGI runners (e.g. `uvicorn`, `gunicorn -k uvicorn.workers.UvicornWorker`).

---

## 2. The 7.8 GB Model Artifact Constraint

The single largest architectural hurdle to standard containerized or serverless deployment is the **Student A Severity Prediction model artifact**:

- **File Path:** `student_A/models/accident_severity_model.pkl`
- **File Size:** **7.8 GB** (contains 100 deep decision trees trained on 138 one-hot features).
- **Deserialization Memory Overhead:** Unpickling this artifact during FastAPI startup requires approximately **10 GB to 12 GB of peak RAM**.

### Implications for Cloud Hosting

1. **Serverless Incompatibility:** AWS Lambda, Google Cloud Functions, and Azure Functions have strict deployment package limits (typically $\le 500\text{ MB}$) and memory limits, making serverless hosting impossible without major architectural restructuring.
2. **Standard Container OOM:** Standard container instances provisioned with 2 GB to 4 GB RAM will immediately trigger an Out-Of-Memory (`SIGKILL` / Exit Code 137) during startup when `SeverityModelManager.load()` is invoked.
3. **Storage & CI/CD Overhead:** Pushing a 7.8 GB binary through standard Git LFS or Docker build steps results in slow image builds and expensive image registries.

### Recommended Future Architectural Solutions (Planned)

To achieve scalable, cost-effective production deployment, one of the following approaches should be implemented in a future phase:

- **Option A: Memory-Optimized Compute Instances (Short-term):** Deploy the backend container to a dedicated cloud VM or Kubernetes node pool with $\ge 16\text{ GB RAM}$ (e.g. AWS `r6i.large` or GCP `n2-highmem-2`).
- **Option B: Artifact Compression & Tree Pruning (Medium-term):** Retrain or prune the Random Forest model using tree depth limits, quantization, or conversion to ONNX format to reduce the binary footprint to $<500\text{ MB}$.
- **Option C: Microservice Decoupling (Architectural):** Decouple Student A into an isolated model-serving microservice (e.g. using Triton Inference Server or TorchServe), allowing the core Journey Safety pipeline to run in lightweight, rapid-scaling web containers.

---

## 3. External Service Egress Requirements

The backend requires outbound HTTPS (port 443) network connectivity to communicate with external APIs:

| Provider | Hostname / Endpoint | Protocol | SLA / Authentication |
| --- | --- | --- | --- |
| **OpenStreetMap Nominatim** | `nominatim.openstreetmap.org` | HTTPS | Free, rate-limited to 1 req/sec. Custom `User-Agent` header required. |
| **Project OSRM** | `router.project-osrm.org` | HTTPS | Public demo routing server. Subject to demo cluster availability. |
| **Open-Meteo** | `api.open-meteo.com` | HTTPS | Free for non-commercial use up to 10,000 daily calls. |
| **Transport for London** | `api.tfl.gov.uk` | HTTPS | Supports unauthenticated rate-limited access or `app_key` credential. |
| **Google Gemini API** | `generativelanguage.googleapis.com` | HTTPS | Requires valid `GEMINI_API_KEY`. |

---

## 4. Production Security & Configuration Hardening

Before deploying to a public-facing environment, the following configuration steps must be applied:

1. **CORS Lockdown:** Update `CORS_ORIGINS` in `.env` to restrict cross-origin requests exclusively to the verified production frontend domain (e.g. `https://vantage.example.com`).
2. **API Key Isolation:** Ensure `GEMINI_API_KEY` and optional `TFL_APP_KEY` are mounted via secure secret managers (e.g. AWS Secrets Manager, GCP Secret Manager, or HashiCorp Vault), never hardcoded or committed to git.
3. **Exception Sanitization:** Ensure `DEBUG=false` so that internal exceptions are intercepted by `unhandled_exception_handler` in `main.py`, logging traces internally while returning only an opaque `error_id` to clients.
4. **Rate Limiting:** Implement reverse-proxy rate limiting (e.g. via NGINX or Cloudflare) on `/journey/analyze` to prevent external quota exhaustion against upstream geocoding and Gemini APIs.
