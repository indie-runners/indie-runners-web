#!/bin/bash
# Start the Cloud SQL Auth Proxy (if not already running) and launch the app.
# Usage: bash scripts/dev.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$ROOT_DIR"

INSTANCE="indie-runners-dev-470411:europe-west10:indie-runners-db"
PORT=5432
PROXY_BIN="$ROOT_DIR/cloud-sql-proxy"

# Download proxy binary if missing
if [ ! -f "$PROXY_BIN" ]; then
    echo "Downloading Cloud SQL Auth Proxy..."
    wget https://dl.google.com/cloudsql/cloud_sql_proxy.linux.amd64 -O "$PROXY_BIN"
    chmod +x "$PROXY_BIN"
fi

# Check gcloud auth
if ! gcloud auth application-default print-access-token &>/dev/null; then
    echo "Not authenticated. Running gcloud auth..."
    gcloud auth application-default login
fi

# Start proxy only if nothing is already listening on the port
if lsof -ti tcp:"$PORT" &>/dev/null; then
    echo "Port $PORT already in use — assuming proxy is running, skipping."
    PROXY_STARTED=false
else
    echo "Starting Cloud SQL Auth Proxy on port $PORT..."
    "$PROXY_BIN" -instances="$INSTANCE=tcp:$PORT" &
    PROXY_PID=$!
    PROXY_STARTED=true
    # Give it a moment to bind
    sleep 1
fi

# Shut down the proxy we started when the script exits
cleanup() {
    if [ "$PROXY_STARTED" = true ] && kill -0 "$PROXY_PID" 2>/dev/null; then
        echo ""
        echo "Stopping Cloud SQL Auth Proxy (pid $PROXY_PID)..."
        kill "$PROXY_PID"
    fi
}
trap cleanup EXIT INT TERM

echo "Starting uvicorn on http://localhost:8000 ..."
echo ""
uvicorn app.main:app --reload --port 8000
