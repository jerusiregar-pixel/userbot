from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from pathlib import Path

from telethon import TelegramClient

from app.config import Settings
from app.loader import register_modules

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class RunningClient:
    name: str
    client: TelegramClient
    user_id: int
    display_name: str


class ClientManager:
    """Discover, start, and stop all Telegram user sessions."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.clients: list[RunningClient] = []

    def discover_sessions(self) -> list[Path]:
        return sorted(
            path
            for path in self.settings.session_dir.glob("*.session")
            if path.is_file() and not path.name.endswith("-journal")
        )

    async def _start_one(self, session_path: Path) -> RunningClient | None:
        session_name = session_path.stem
        client = TelegramClient(
            str(session_path.with_suffix("")),
            self.settings.api_id,
            self.settings.api_hash,
            auto_reconnect=True,
            connection_retries=5,
        )

        try:
            await client.connect()
            if not await client.is_user_authorized():
                logger.error(
                    "Session %s tidak valid/belum login. Jalankan: python3 manage.py add %s",
                    session_name,
                    session_name,
                )
                await client.disconnect()
                return None

            me = await client.get_me()
            register_modules(client, self.settings)

            display_name = " ".join(
                value for value in [me.first_name, me.last_name] if value
            ).strip() or (me.username or str(me.id))

            logger.info(
                "Client aktif: %s | id=%s | session=%s",
                display_name,
                me.id,
                session_name,
            )
            return RunningClient(
                name=session_name,
                client=client,
                user_id=me.id,
                display_name=display_name,
            )
        except Exception:
            logger.exception("Gagal menyalakan session %s", session_name)
            if client.is_connected():
                await client.disconnect()
            return None

    async def start_all(self) -> None:
        sessions = self.discover_sessions()
        if not sessions:
            raise RuntimeError(
                "Belum ada session. Tambahkan akun dengan: python3 manage.py add akun1"
            )

        results = await asyncio.gather(*(self._start_one(path) for path in sessions))
        self.clients = [item for item in results if item is not None]

        if not self.clients:
            raise RuntimeError("Tidak ada session Telegram yang berhasil dijalankan.")

        logger.info("Total client aktif: %d", len(self.clients))

    async def wait_forever(self) -> None:
        await asyncio.gather(
            *(running.client.run_until_disconnected() for running in self.clients)
        )

    async def stop_all(self) -> None:
        if not self.clients:
            return

        await asyncio.gather(
            *(running.client.disconnect() for running in self.clients),
            return_exceptions=True,
        )
        logger.info("Semua client dihentikan.")
