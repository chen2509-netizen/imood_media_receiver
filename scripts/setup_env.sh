#!/usr/bin/env bash
# Create the project-only venv (.venv, Python 3.10 via uv - same convention as LiveTalking's .venv-lt).
# Touches nothing outside this folder: no conda base, no system Python.
set -euo pipefail
cd "$(dirname "$0")/.."
UV="${UV:-/root/.local/bin/uv}"
[ -d .venv ] || "$UV" venv --python 3.10 .venv
"$UV" pip install --python .venv/bin/python -r requirements.txt
.venv/bin/python -c "import sys, aiohttp; print(sys.executable, sys.version.split()[0], 'aiohttp', aiohttp.__version__)"
