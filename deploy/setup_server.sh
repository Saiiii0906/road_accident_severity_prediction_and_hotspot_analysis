#!/usr/bin/env bash
# =================================================================
# Vantage Production Server Provisioning & Security Hardening Script
# Target Platforms: Oracle Linux 8/9, RHEL 8/9, Rocky Linux, Ubuntu 22/24 LTS
# Run with sudo or as root on a target Linux VM with >= 8 GB RAM.
# =================================================================
set -euo pipefail

echo "=================================================================="
echo "    Vantage Host Provisioning & Security Hardening"
echo "=================================================================="

# Detect OS Distribution
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS_ID="${ID:-unknown}"
    OS_VERSION_ID="${VERSION_ID:-}"
else
    OS_ID="unknown"
fi
echo "Detected OS: ${OS_ID} ${OS_VERSION_ID:-}"

# 1. Hardware Prerequisites (RAM & Swap)
echo "==> [1/7] Verifying Memory & Swap..."
if [ -f /proc/meminfo ]; then
    TOTAL_MEM_KB=$(grep MemTotal /proc/meminfo | awk '{print $2}')
    TOTAL_MEM_GB=$(( TOTAL_MEM_KB / 1024 / 1024 ))
else
    TOTAL_MEM_GB=$(python3 -c "import psutil; print(int(psutil.virtual_memory().total / (1024**3)))" 2>/dev/null || echo "16")
fi
echo "Detected RAM: ${TOTAL_MEM_GB} GB"

if [ "$TOTAL_MEM_GB" -lt 7 ]; then
    echo "WARNING: Vantage requires at least 8 GB RAM for Student A's 7.80 GB model in RAM."
    echo "Creating an 8 GB swapfile to ensure safe buffer..."
    if [ ! -f /swapfile ]; then
        fallocate -l 8G /swapfile || dd if=/dev/zero of=/swapfile bs=1M count=8192
        chmod 600 /swapfile
        mkswap /swapfile
        swapon /swapfile
        echo '/swapfile none swap sw 0 0' >> /etc/fstab
        echo "Swapfile created and activated successfully."
    fi
fi

# 2. Disk Space Verification
echo "==> [2/7] Verifying Storage Space..."
FREE_DISK_GB=$(df -m / | awk 'NR==2 {print int($4/1024)}')
echo "Detected Free Disk Space: ${FREE_DISK_GB} GB"
if [ "$FREE_DISK_GB" -lt 25 ]; then
    echo "ERROR: At least 25 GB free disk is required for the 7.8 GB model and Docker images." >&2
    exit 1
fi

# 3. Package Management & Security Updates
echo "==> [3/7] Installing Security Tools & Setting Automatic Updates..."
case "$OS_ID" in
    ol*|rhel*|centos*|rocky*|almalinux*)
        dnf update -y --security
        dnf install -y curl ca-certificates gnupg2 tar fail2ban firewalld dnf-automatic
        systemctl enable --now firewalld
        systemctl enable --now fail2ban
        systemctl enable --now dnf-automatic.timer
        ;;
    ubuntu*|debian*)
        export DEBIAN_FRONTEND=noninteractive
        apt-get update
        apt-get upgrade -y --with-new-pkgs
        apt-get install -y ca-certificates curl gnupg ufw fail2ban unattended-upgrades
        systemctl enable --now fail2ban
        systemctl enable --now unattended-upgrades
        ;;
    *)
        echo "Note: Generic Linux distribution detected. Ensure firewall, fail2ban, and auto-updates are configured manually."
        ;;
esac

# 4. Host Firewall Configuration (Allow ONLY 22, 80, 443; NEVER 8000)
echo "==> [4/7] Hardening Host Firewall (Ports: 22, 80, 443; Port 8000 EXCLUDED)..."
case "$OS_ID" in
    ol*|rhel*|centos*|rocky*|almalinux*)
        firewall-cmd --permanent --zone=public --add-service=ssh
        firewall-cmd --permanent --zone=public --add-service=http
        firewall-cmd --permanent --zone=public --add-service=https
        firewall-cmd --permanent --zone=public --remove-port=8000/tcp 2>/dev/null || true
        firewall-cmd --reload
        echo "Firewalld configured: SSH, HTTP, HTTPS enabled. Port 8000 blocked."
        ;;
    ubuntu*|debian*)
        ufw default deny incoming
        ufw default allow outgoing
        ufw allow 22/tcp comment 'SSH Key Access'
        ufw allow 80/tcp comment 'HTTP ACME challenge'
        ufw allow 443/tcp comment 'HTTPS Production'
        ufw deny 8000/tcp comment 'FastAPI Internal Container Port'
        ufw --force enable
        echo "UFW configured: Ports 22, 80, 443 allowed. Port 8000 denied."
        ;;
esac

# 5. Host Deployment User Setup (Docker / Sudo Privileges)
echo "==> [5/7] Configuring Host Deployment User with Docker Privileges (vantage)..."
if ! id -u vantage >/dev/null 2>&1; then
    useradd -m -s /bin/bash -U -G wheel,docker vantage 2>/dev/null || \
    useradd -m -s /bin/bash -U vantage
    echo "Created host deployment user 'vantage' with administrative Docker permissions."
fi

# 6. Docker Engine & Compose Installation
echo "==> [6/7] Ensuring Docker Engine & Compose are Ready..."
if ! command -v docker >/dev/null 2>&1; then
    echo "Installing Docker..."
    case "$OS_ID" in
        ol*|rhel*|centos*|rocky*|almalinux*)
            dnf config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
            dnf install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
            systemctl enable --now docker
            ;;
        ubuntu*|debian*)
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
            ;;
    esac
fi
usermod -aG docker vantage 2>/dev/null || true
echo "Docker Version: $(docker --version)"

# 7. SSH Security Hardening Guidance [MANUAL OPERATOR ACTION]
echo "==> [7/7] SSH Security Verification..."
echo "------------------------------------------------------------------"
echo "CRITICAL MANUAL OPERATOR CHECKLIST FOR PRODUCTION SSH HARDENING:"
echo "Do NOT blindly disable password or root access without verification!"
echo ""
echo "Step 1: Confirm your public key is copied to the non-root vantage user:"
echo "        ssh-copy-id -i ~/.ssh/id_ed25519.pub vantage@<YOUR_VM_IP>"
echo ""
echo "Step 2: From your workstation, open a NEW terminal and confirm SSH key login works:"
echo "        ssh -i ~/.ssh/id_ed25519 vantage@<YOUR_VM_IP>"
echo "        sudo whoami  # verify sudo access works"
echo ""
echo "Step 3: Keep your original session open, and only then write drop-in config:"
echo "        sudo tee /etc/ssh/sshd_config.d/50-vantage-hardening.conf <<'EOF'"
echo "PermitRootLogin no"
echo "PasswordAuthentication no"
echo "PubkeyAuthentication yes"
echo "EOF"
echo ""
echo "Step 4: Validate SSH syntax before reloading:"
echo "        sudo sshd -t"
echo "        sudo systemctl reload sshd 2>/dev/null || sudo systemctl reload ssh"
echo "------------------------------------------------------------------"

echo "==> [Vantage Host Setup] VM successfully hardened and ready for deployment."
