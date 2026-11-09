#!/bin/bash
# Starts the Cloud SQL Auth Proxy for local development.
# Run this in a separate terminal before starting the app.

set -e

INSTANCE="indie-runners-dev-470411:europe-west10:indie-runners-db"
PORT=5432

if [ ! -f "cloud-sql-proxy" ]; then
    echo "Downloading Cloud SQL Auth Proxy..."
    wget https://dl.google.com/cloudsql/cloud_sql_proxy.linux.amd64 -O cloud-sql-proxy
    chmod +x cloud-sql-proxy
    echo "Downloaded cloud-sql-proxy"
else
    echo "cloud-sql-proxy already exists"
fi

echo "Checking gcloud authentication..."
if gcloud auth application-default print-access-token &>/dev/null; then
    echo "Already authenticated with gcloud"
else
    echo "Not authenticated. Running gcloud auth..."
    gcloud auth application-default login
fi

echo ""
echo "Starting proxy on port $PORT for instance: $INSTANCE"
echo "Make sure your .env DATABASE_URL points to localhost:"
echo "  DATABASE_URL=postgresql+psycopg://postgres:PASSWORD@localhost:$PORT/postgres"
echo ""
echo "Starting proxy now (Ctrl+C to stop)..."
echo ""
./cloud-sql-proxy -instances="$INSTANCE=tcp:$PORT"
