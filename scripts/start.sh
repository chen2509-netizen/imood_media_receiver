#!/usr/bin/env bash
# Start the receiver in the background (default :8030). Env: RECEIVER_PORT, LT_URL, LT_TIMEOUT_S.
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p logs
PORT="${RECEIVER_PORT:-8030}"
if [ -f logs/receiver.pid ] && kill -0 "$(cat logs/receiver.pid)" 2>/dev/null; then
  echo "already running (pid $(cat logs/receiver.pid))"; exit 0
fi
if ss -ltn "sport = :$PORT" | grep -q LISTEN; then echo "port $PORT is already in use"; exit 1; fi
nohup .venv/bin/python -u receiver/server.py >> logs/receiver.log 2>&1 &
echo $! > logs/receiver.pid
for _ in $(seq 20); do
  curl -fs "http://127.0.0.1:$PORT/health" >/dev/null && { echo "receiver up on :$PORT (pid $(cat logs/receiver.pid))"; exit 0; }
  sleep 0.25
done
echo "receiver did not come up, see logs/receiver.log"; tail -n 20 logs/receiver.log; exit 1
