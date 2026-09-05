#!/usr/bin/env bash
# =================================================================
# Vantage Production Server Provisioning Script (Ubuntu / Debian)
# Run as root or with sudo on a target Linux VM with >= 8 GB RAM.
# =================================================================
set -euo pipefail

echo "==> [Vantage Host Setup] Checking system prerequisites..."

# 1. Check RAM
if [ -f /proc/meminfo ]; then
    TOTAL_MEM_KB=$(grep MemTotal /proc/meminfo | awk '{print $2}')
    TOTAL_MEM_GB=$(( TOTAL_MEM_KB / 1024 / 1024 ))
else
    TOTAL_MEM_GB=$(python3 -c "import psutil; print(int(psutil.virtual_memory().total / (1024**3)))" 2>/dev/null || echo "16")
fi
echo "Detected RAM: ${TOTAL_MEM_GB} GB"

if [ "$TOTAL_MEM_GB" -lt 7 ]; then
    echo "WARNING: Vantage requires at least 8 GB RAM for Student A's 7.80 GB model."
    echo "Adding an 8 GB swap file to prevent out-of-memory errors..."
    if [ ! -f /swapfile ]; then
        fallocate -l 8G /swapfile || dd if=/dev/zero of=/swapfile bs=1M count=8192
        chmod 600 /swapfile
        mkswap /swapfile
        swapon /swapfile
        echo '/swapfile none swap sw 0 0' >> /etc/fstab
        echo "Swap file created successfully."
    fi
fi

# 2. Check Disk Space
FREE_DISK_GB=$(df -m / | awk 'NR==2 {print int($4/1024)}')
echo "Detected Free Disk Space: ${FREE_DISK_GB} GB"
if [ "$FREE_DISK_GB" -lt 25 ]; then
    echo "ERROR: At least 25 GB free disk is required for the 7.8 GB model and Docker images." >&2
    exit 1
fi

# 3. Install Docker and Docker Compose Plugin if missing
if ! command -v docker >/dev/null 2>&1; then
    echo "==> Installing Docker Engine & Compose plugin..."
    apt-get update
    apt-get install -y ca-certificates curl gnupg
    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    chmod a+r /etc/apt/keyrings/docker.gpg
    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
      $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
      tee /etc/apt/sources.list.d/docker.list > /dev/null
    apt-get update
    apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    systemctl enable --now docker
    echo "Docker installed successfully: $(docker --version)"
else
    echo "Docker already installed: $(docker --version)"
fi

echo "==> [Vantage Host Setup] System is ready for Vantage container deployment."
