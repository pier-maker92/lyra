#!/usr/bin/env bash
set -uo pipefail

# Production launcher for the API server.
#
# In an autoscale "application router" deployment only the registered artifacts are
# started. The Python lyrics engine (services/lyrics-engine) is NOT an artifact, so
# without this it never runs in production and /api/analyze fails with
# ECONNREFUSED 127.0.0.1:8000. We start it here as an in-container sidecar that the
# Express proxy reaches over localhost. uvicorn binds the port immediately and warms
# the TinyCLIP model in its lifespan, so the api-server health check (/api/healthz)
# stays fast while the first analyze request waits for the model to be ready.

cd "$(dirname "$0")/../.." || exit 1

# Start the engine sidecar. `python3 -m uvicorn` avoids depending on the uvicorn
# console script being on PATH in the production image.
(
  cd services/lyrics-engine || exit 1
  exec python3 -m uvicorn main:app --host 127.0.0.1 --port 8000
) &
ENGINE_PID=$!

# Supervise the sidecar: if it ever exits (failed import, crash, missing dep), bring
# the whole instance down so the platform recycles it instead of silently serving
# 502s from /api/analyze behind a healthy /api/healthz.
(
  while kill -0 "$ENGINE_PID" 2>/dev/null; do
    sleep 5
  done
  echo "[start-prod] lyrics engine exited unexpectedly; stopping api-server" >&2
  kill -TERM "$$" 2>/dev/null
) &

# Run the API server in the foreground so it receives shutdown signals directly.
exec node --enable-source-maps artifacts/api-server/dist/index.mjs
