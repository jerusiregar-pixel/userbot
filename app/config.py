from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


@dataclass(frozen=True, slots=True)
class Settings:
    api_id: int
    api_hash: str
    command_prefix: str
    session_dir: Path
    broadcast_delay: float
    flood_wait_limit: int


def load_settings() -> Settings:
    api_id_raw = os.getenv("API_ID", "").strip()
    api_hash = os.getenv("API_HASH", "").strip()

    if not api_id_raw or not api_hash:
        raise RuntimeError(
            "API_ID dan API_HASH belum diatur. Salin .env.example menjadi .env lalu isi nilainya."
        )

    try:
        api_id = int(api_id_raw)
    except ValueError as exc:
        raise RuntimeError("API_ID harus berupa angka.") from exc

    prefix = os.getenv("COMMAND_PREFIX", ".").strip() or "."
    session_dir_raw = os.getenv("SESSION_DIR", "data/sessions").strip() or "data/sessions"
    session_dir = (BASE_DIR / session_dir_raw).resolve()

    try:
        broadcast_delay = max(0.5, float(os.getenv("BROADCAST_DELAY", "2.5")))
    except ValueError as exc:
        raise RuntimeError("BROADCAST_DELAY harus berupa angka.") from exc

    try:
        flood_wait_limit = max(0, int(os.getenv("FLOOD_WAIT_LIMIT", "60")))
    except ValueError as exc:
        raise RuntimeError("FLOOD_WAIT_LIMIT harus berupa angka bulat.") from exc

    session_dir.mkdir(parents=True, exist_ok=True)

    return Settings(
        api_id=api_id,
        api_hash=api_hash,
        command_prefix=prefix,
        session_dir=session_dir,
        broadcast_delay=broadcast_delay,
        flood_wait_limit=flood_wait_limit,
    )
