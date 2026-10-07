#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
if [ -f logs/receiver.pid ] && kill -0 "$(cat logs/receiver.pid)" 2>/dev/null; then
  kill "$(cat logs/receiver.pid)" && echo "stopped pid $(cat logs/receiver.pid)"
else
  echo "not running"
fi
rm -f logs/receiver.pid
