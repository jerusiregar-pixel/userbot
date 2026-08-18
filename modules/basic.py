from __future__ import annotations

import re
import time

from telethon import TelegramClient, events

from app.config import Settings


def setup(client: TelegramClient, settings: Settings) -> None:
    prefix = settings.command_prefix
    escaped_prefix = re.escape(prefix)

    async def ping_handler(event: events.NewMessage.Event) -> None:
        started = time.perf_counter()
        await event.edit("Pinging...")
        elapsed_ms = (time.perf_counter() - started) * 1000
        await event.edit(f"Pong! `{elapsed_ms:.0f} ms`")

    async def me_handler(event: events.NewMessage.Event) -> None:
        me = await client.get_me()
        username = f"@{me.username}" if me.username else "-"
        await event.edit(
            "**Account**\n"
            f"ID: `{me.id}`\n"
            f"Name: {me.first_name or '-'}\n"
            f"Username: {username}"
        )

    async def help_handler(event: events.NewMessage.Event) -> None:
        await event.edit(
            "**UserbotSebar Simple**\n\n"
            f"`{prefix}ping` - cek client\n"
            f"`{prefix}me` - info akun\n"
            f"`{prefix}help` - bantuan\n"
            f"`{prefix}bc <text>` - sebar text ke grup\n"
            f"Reply pesan + `{prefix}bc` - forward pesan ke grup\n"
            f"`{prefix}bcstop` - hentikan broadcast aktif"
        )

    client.add_event_handler(
        ping_handler,
        events.NewMessage(outgoing=True, pattern=rf"^{escaped_prefix}ping$"),
    )
    client.add_event_handler(
        me_handler,
        events.NewMessage(outgoing=True, pattern=rf"^{escaped_prefix}me$"),
    )
    client.add_event_handler(
        help_handler,
        events.NewMessage(outgoing=True, pattern=rf"^{escaped_prefix}help$"),
    )
