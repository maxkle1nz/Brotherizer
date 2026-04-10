#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PID_FILE="${BROTHERIZER_PID_FILE:-$ROOT_DIR/.runtime/brotherizer_api.pid}"
LOG_FILE="${BROTHERIZER_LOG_FILE:-$ROOT_DIR/.runtime/brotherizer_api.log}"
HOST="${BROTHERIZER_HOST:-127.0.0.1}"
PORT="${BROTHERIZER_PORT:-5555}"
HEALTH_URL="http://$HOST:$PORT/health"

pid=""
if [ -f "$PID_FILE" ]; then
  pid="$(cat "$PID_FILE" 2>/dev/null || true)"
fi

if [ -n "${pid:-}" ] && kill -0 "$pid" 2>/dev/null; then
  echo "pid=$pid"
  echo "log=$LOG_FILE"
  echo "health:"
  curl -s "$HEALTH_URL" || true
elif curl -fsS "$HEALTH_URL" >/dev/null 2>&1; then
  echo "brotherizer_api running (health responds, pid file stale or missing)"
  echo "log=$LOG_FILE"
  echo "health:"
  curl -s "$HEALTH_URL" || true
else
  echo "brotherizer_api not running"
fi
