#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PID_FILE="${BROTHERIZER_PID_FILE:-$ROOT_DIR/.runtime/brotherizer_api.pid}"
HOST="${BROTHERIZER_HOST:-127.0.0.1}"
PORT="${BROTHERIZER_PORT:-5555}"

if [ ! -f "$PID_FILE" ]; then
  pids="$(pgrep -f 'python3 api/brotherizer_api.py' || true)"
  if [ -n "${pids:-}" ]; then
    echo "$pids" | xargs kill
    echo "stopped brotherizer_api via process scan"
    exit 0
  fi
  echo "brotherizer_api not running"
  exit 0
fi

pid="$(cat "$PID_FILE" 2>/dev/null || true)"
if [ -z "${pid:-}" ]; then
  rm -f "$PID_FILE"
  echo "stale pid file removed"
  exit 0
fi

if kill -0 "$pid" 2>/dev/null; then
  kill "$pid"
  sleep 1
  if kill -0 "$pid" 2>/dev/null; then
    kill -9 "$pid"
  fi
  echo "stopped brotherizer_api pid=$pid"
else
  echo "process not running; removed stale pid=$pid"
fi

rm -f "$PID_FILE"
