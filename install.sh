#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

if [[ $EUID -ne 0 ]]; then
  echo "Jalankan install.sh sebagai root di VPS."
  exit 1
fi

apt-get update
apt-get install -y python3 python3-venv python3-pip

if [[ ! -d .venv ]]; then
  python3 -m venv .venv
fi

.venv/bin/python -m pip install --upgrade pip wheel
.venv/bin/pip install -r requirements.txt

mkdir -p data/sessions

if [[ ! -f .env ]]; then
  cp .env.example .env
  echo
  echo "File .env dibuat. Isi API_ID dan API_HASH sebelum menambahkan akun."
fi

echo
echo "Install selesai."
echo "1) nano .env"
echo "2) .venv/bin/python manage.py add akun1"
echo "3) bash service.sh install"
