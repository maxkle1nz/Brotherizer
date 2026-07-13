#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PID_FILE="${BROTHERIZER_PID_FILE:-$ROOT_DIR/.runtime/brotherizer_api.pid}"
LOG_FILE="${BROTHERIZER_LOG_FILE:-$ROOT_DIR/.runtime/brotherizer_api.log}"
HOST="${BROTHERIZER_HOST:-127.0.0.1}"
PORT="${BROTHERIZER_PORT:-5555}"
HEALTH_URL="http://$HOST:$PORT/health"
ENV_FILE="${BROTHERIZER_ENV_FILE:-$ROOT_DIR/.runtime/brotherizer.env}"

mkdir -p "$(dirname "$PID_FILE")"

if [ -f "$ENV_FILE" ]; then
  # shellcheck disable=SC1090
  . "$ENV_FILE"
fi

if curl -fsS "$HEALTH_URL" >/dev/null 2>&1; then
  echo "brotherizer_api already responding on $HEALTH_URL"
  exit 0
fi

if [ -f "$PID_FILE" ]; then
  existing_pid="$(cat "$PID_FILE" 2>/dev/null || true)"
  if [ -n "${existing_pid:-}" ] && kill -0 "$existing_pid" 2>/dev/null; then
    echo "brotherizer_api already running (pid=$existing_pid)"
    exit 0
  fi
  rm -f "$PID_FILE"
fi

(
  cd "$ROOT_DIR"
  export BROTHERIZER_HOST="$HOST"
  export BROTHERIZER_PORT="$PORT"
  nohup python3 api/brotherizer_api.py >>"$LOG_FILE" 2>&1 &
  echo $! > "$PID_FILE"
)

sleep 2
if curl -fsS "$HEALTH_URL" >/dev/null 2>&1; then
  echo "started brotherizer_api pid=$(cat "$PID_FILE") host=$HOST port=$PORT log=$LOG_FILE"
  exit 0
fi

echo "brotherizer_api failed to respond after start; check log=$LOG_FILE" >&2
exit 1
