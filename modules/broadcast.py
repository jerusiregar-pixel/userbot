from __future__ import annotations

import asyncio
import logging
import re
from collections import defaultdict

from telethon import TelegramClient, errors, events
from telethon.tl.types import Channel, Chat

from app.config import Settings

logger = logging.getLogger(__name__)

# One active broadcast task per Telegram account.
ACTIVE_TASKS: dict[int, asyncio.Task] = {}
LOCKS: defaultdict[int, asyncio.Lock] = defaultdict(asyncio.Lock)


def _is_group(entity: object) -> bool:
    if isinstance(entity, Chat):
        return True
    if isinstance(entity, Channel):
        return bool(getattr(entity, "megagroup", False))
    return False


async def _send_once(
    client: TelegramClient,
    entity: object,
    text: str | None,
    reply_message: object | None,
) -> None:
    if reply_message is not None:
        await client.forward_messages(entity, reply_message)
    elif text:
        await client.send_message(entity, text)


async def _broadcast(
    client: TelegramClient,
    event: events.NewMessage.Event,
    settings: Settings,
    text: str | None,
    reply_message: object | None,
) -> None:
    me = await client.get_me()
    lock = LOCKS[me.id]

    if lock.locked():
        await event.edit("Broadcast lain masih berjalan. Gunakan `.bcstop` terlebih dahulu.")
        return

    sent = 0
    failed = 0
    skipped = 0

    async with lock:
        try:
            await event.edit("Broadcast dimulai...")

            async for dialog in client.iter_dialogs():
                if not _is_group(dialog.entity):
                    skipped += 1
                    continue

                try:
                    await _send_once(client, dialog.entity, text, reply_message)
                    sent += 1
                except errors.FloodWaitError as exc:
                    if exc.seconds > settings.flood_wait_limit:
                        logger.warning(
                            "FloodWait %ss pada %s, dilewati karena melebihi limit %ss.",
                            exc.seconds,
                            dialog.name,
                            settings.flood_wait_limit,
                        )
                        failed += 1
                        continue

                    await asyncio.sleep(exc.seconds)
                    try:
                        await _send_once(client, dialog.entity, text, reply_message)
                        sent += 1
                    except Exception:
                        failed += 1
                except (errors.ChatWriteForbiddenError, errors.UserBannedInChannelError):
                    failed += 1
                except Exception:
                    logger.exception("Gagal broadcast ke %s", dialog.name)
                    failed += 1

                await asyncio.sleep(settings.broadcast_delay)

            await event.edit(
                "**Broadcast selesai**\n"
                f"Berhasil: `{sent}`\n"
                f"Gagal: `{failed}`\n"
                f"Dilewati: `{skipped}`"
            )
        except asyncio.CancelledError:
            await event.edit(
                "**Broadcast dihentikan**\n"
                f"Berhasil sebelum stop: `{sent}`\n"
                f"Gagal: `{failed}`"
            )
            raise
        finally:
            ACTIVE_TASKS.pop(me.id, None)


def setup(client: TelegramClient, settings: Settings) -> None:
    prefix = settings.command_prefix
    escaped_prefix = re.escape(prefix)

    async def bc_handler(event: events.NewMessage.Event) -> None:
        me = await client.get_me()
        existing = ACTIVE_TASKS.get(me.id)
        if existing and not existing.done():
            await event.edit("Broadcast masih berjalan. Gunakan `.bcstop` jika ingin menghentikannya.")
            return

        raw = event.raw_text or ""
        text = raw[len(prefix) + 2 :].strip()  # remove '<prefix>bc'
        reply = await event.get_reply_message()

        if not text and reply is None:
            await event.edit(
                f"Gunakan `{prefix}bc <text>` atau reply sebuah pesan lalu kirim `{prefix}bc`."
            )
            return

        task = asyncio.create_task(_broadcast(client, event, settings, text or None, reply))
        ACTIVE_TASKS[me.id] = task

    async def stop_handler(event: events.NewMessage.Event) -> None:
        me = await client.get_me()
        task = ACTIVE_TASKS.get(me.id)
        if task is None or task.done():
            await event.edit("Tidak ada broadcast yang sedang berjalan.")
            return
        task.cancel()
        await event.edit("Menghentikan broadcast...")

    client.add_event_handler(
        bc_handler,
        events.NewMessage(outgoing=True, pattern=rf"^{escaped_prefix}bc(?:\s|$)"),
    )
    client.add_event_handler(
        stop_handler,
        events.NewMessage(outgoing=True, pattern=rf"^{escaped_prefix}bcstop$"),
    )
