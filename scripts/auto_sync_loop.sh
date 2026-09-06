#!/usr/bin/env bash
# ==============================================================================
# Vantage Continuous Sync Loop: Local -> GitHub -> GCP VM
# ==============================================================================
# Continuously monitors local files for changes.
# 1. Adds and commits changes (honoring .gitignore).
# 2. Pushes directly to GitHub (origin main).
# 3. Pulls and updates the remote GCP VM (reloads PM2 / Docker as needed).
# ==============================================================================

set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT" || exit 1

REMOTE_HOST="vantage"
REMOTE_REPO_PATH="/home/yahydhksidh/road_accident_severity_prediction_and_hotspot_analysis"
CHECK_INTERVAL_SEC=3
DEBOUNCE_WAIT_SEC=2

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[$(date '+%H:%M:%S')]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[$(date '+%H:%M:%S')]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[$(date '+%H:%M:%S')]${NC} $1"
}

log_error() {
    echo -e "${RED}[$(date '+%H:%M:%S')]${NC} $1"
}

cleanup() {
    echo ""
    log_info "Stopping auto-sync loop. Goodbye!"
    exit 0
}
trap cleanup SIGINT SIGTERM

echo -e "${CYAN}================================================================${NC}"
echo -e "${CYAN}       VANTAGE CONTINUOUS SYNC LOOP (Local -> GitHub -> GCP)   ${NC}"
echo -e "${CYAN}================================================================${NC}"
log_info "Repository:  $REPO_ROOT"
log_info "Remote Host: $REMOTE_HOST ($REMOTE_REPO_PATH)"
log_info "Interval:    Every ${CHECK_INTERVAL_SEC}s"
log_info "Press Ctrl+C to stop."
echo ""

while true; do
    # Check for unstaged, staged, or untracked changes in git (excluding gitignored files)
    CHANGES=$(git status --porcelain 2>/dev/null)

    if [ -n "$CHANGES" ]; then
        log_warn "Changes detected locally:"
        echo "$CHANGES" | sed 's/^/  /'

        # Debounce: wait a short moment in case multiple files are being saved
        sleep "$DEBOUNCE_WAIT_SEC"

        # Determine which components were touched
        FRONTEND_CHANGED=false
        BACKEND_CHANGED=false

        if echo "$CHANGES" | grep -q " frontend/"; then
            FRONTEND_CHANGED=true
        fi
        if echo "$CHANGES" | grep -q -E " backend/|Dockerfile|docker-compose.yml"; then
            BACKEND_CHANGED=true
        fi

        # 1. Stage and commit locally
        TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
        COMMIT_MSG="chore(sync): auto-update $TIMESTAMP"

        git add -A
        if git commit -m "$COMMIT_MSG"; then
            log_success "Created local commit: $COMMIT_MSG"

            # 2. Push to GitHub
            log_info "Pushing commit to GitHub (origin main)..."
            if git push origin main; then
                log_success "Pushed to GitHub successfully!"
            else
                log_error "Failed to push to GitHub. Will retry on next loop."
                sleep "$CHECK_INTERVAL_SEC"
                continue
            fi

            # 3. Pull and update on GCP VM
            log_info "Updating GCP VM ($REMOTE_HOST)..."
            SSH_CMD="cd $REMOTE_REPO_PATH && \
                sudo -u yahydhksidh git stash 2>/dev/null && \
                sudo -u yahydhksidh git pull origin main && \
                sudo -u yahydhksidh git stash pop 2>/dev/null || true"

            if ssh "$REMOTE_HOST" "$SSH_CMD"; then
                log_success "Pulled latest commits on GCP VM!"
            else
                log_error "Failed to pull on GCP VM."
            fi

            # Rebuild frontend if frontend files were touched
            if [ "$FRONTEND_CHANGED" = true ]; then
                log_info "Frontend changes detected. Rebuilding on VM and reloading PM2..."
                REBUILD_CMD="cd $REMOTE_REPO_PATH/frontend && \
                    sudo -u yahydhksidh NITRO_PRESET=node-server npm run build && \
                    pm2 reload vantage-frontend"
                if ssh "$REMOTE_HOST" "$REBUILD_CMD"; then
                    log_success "Frontend rebuilt and PM2 reloaded on VM!"
                else
                    log_error "Failed to rebuild frontend on VM."
                fi
            fi

            # Restart backend container if backend files were touched
            if [ "$BACKEND_CHANGED" = true ]; then
                log_info "Backend changes detected. Restarting Docker container on VM..."
                if ssh "$REMOTE_HOST" "sudo docker restart vantage-backend"; then
                    log_success "Backend container restarted on VM!"
                else
                    log_error "Failed to restart backend container on VM."
                fi
            fi

            echo -e "${CYAN}----------------------------------------------------------------${NC}"
        fi
    fi

    sleep "$CHECK_INTERVAL_SEC"
done

