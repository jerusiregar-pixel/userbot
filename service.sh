#!/usr/bin/env bash
set -euo pipefail

NAME="userbotsebar"
ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
SERVICE_FILE="/etc/systemd/system/${NAME}.service"

need_root() {
  if [[ $EUID -ne 0 ]]; then
    echo "Perintah ini membutuhkan root."
    exit 1
  fi
}

install_service() {
  need_root
  cat > "$SERVICE_FILE" <<EOF
[Unit]
Description=UserbotSebar Simple
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=$ROOT_DIR
ExecStart=$ROOT_DIR/.venv/bin/python $ROOT_DIR/main.py
Restart=on-failure
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

  systemctl daemon-reload
  systemctl enable --now "$NAME"
  echo "Service terpasang dan dijalankan."
  systemctl --no-pager --full status "$NAME" || true
}

case "${1:-}" in
  install) install_service ;;
  start) need_root; systemctl start "$NAME" ;;
  stop) need_root; systemctl stop "$NAME" ;;
  restart) need_root; systemctl restart "$NAME" ;;
  status) systemctl --no-pager --full status "$NAME" ;;
  logs) journalctl -u "$NAME" -f -n 100 ;;
  *)
    echo "Usage: bash service.sh {install|start|stop|restart|status|logs}"
    exit 1
    ;;
esac
