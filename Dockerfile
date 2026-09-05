# syntax=docker/dockerfile:1
# Vantage Backend Production Containerfile
# Base: Python 3.12 slim (Debian-based)
FROM python:3.12-slim

# Prevent Python from buffering stdout/stderr and writing bytecode
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8000 \
    HOST=0.0.0.0

# Install minimal OS dependencies for network operations & healthchecks
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Create unprivileged system user & group (UID 10001)
RUN groupadd -g 10001 vantage && \
    useradd -u 10001 -g vantage -s /bin/sh -d /app vantage

# Install Python production dependencies
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

# Copy application source code
COPY backend /app/backend

# Copy tracked runtime artifacts (features, encoder, hotspot summary, GNN risk)
# NOTE: The 7.80 GB Student A model binary (accident_severity_model.pkl) is
# INTENTIONALLY EXCLUDED and mounted externally or fetched on-demand.
COPY student_A/models/features.pkl student_A/models/severity_encoder.pkl /app/student_A/models/
COPY data/output/hotspot_summary.csv /app/data/output/hotspot_summary.csv
COPY student_C/gnn_risk_predictions.json /app/student_C/gnn_risk_predictions.json

# Copy acquisition utility and container entrypoint
COPY scripts/acquire_model.py /app/scripts/acquire_model.py
COPY entrypoint.sh /app/entrypoint.sh

RUN chmod +x /app/entrypoint.sh /app/scripts/acquire_model.py && \
    chown -R vantage:vantage /app

USER vantage:vantage

EXPOSE 8000

# Container healthcheck using standard /health endpoint
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/health || exit 1

ENTRYPOINT ["/app/entrypoint.sh"]
