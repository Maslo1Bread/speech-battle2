#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [ ! -d .venv ]; then
  python3 -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate
pip install -q -r requirements.txt

if [ ! -f .env ]; then
  cp .env.example .env
fi

echo "Speech-Battle API: http://127.0.0.1:9201"
echo "Админ: admin / admin123"
exec uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 9201
