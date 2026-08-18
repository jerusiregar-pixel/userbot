#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

if [[ ! -x .venv/bin/python ]]; then
  echo "Virtualenv belum ada. Jalankan: bash install.sh"
  exit 1
fi

exec .venv/bin/python main.py
