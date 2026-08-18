from __future__ import annotations

import argparse
import asyncio
import re
from pathlib import Path

from telethon import TelegramClient

from app.config import load_settings

NAME_RE = re.compile(r"^[A-Za-z0-9_-]{1,40}$")


def validate_name(name: str) -> str:
    if not NAME_RE.fullmatch(name):
        raise SystemExit("Nama session hanya boleh berisi huruf, angka, _ dan - (maks. 40 karakter).")
    return name


async def add_account(name: str) -> None:
    settings = load_settings()
    name = validate_name(name)
    session_path = settings.session_dir / name

    if session_path.with_suffix(".session").exists():
        raise SystemExit(f"Session '{name}' sudah ada.")

    client = TelegramClient(str(session_path), settings.api_id, settings.api_hash)
    print(f"Login session: {name}")
    print("Telethon akan meminta nomor telepon, OTP, dan password 2FA bila diperlukan.\n")

    await client.start()
    me = await client.get_me()
    print(f"\nBerhasil: {me.first_name or '-'} | id={me.id} | session={name}")
    await client.disconnect()


async def check_accounts() -> None:
    settings = load_settings()
    sessions = sorted(settings.session_dir.glob("*.session"))
    if not sessions:
        print("Belum ada session.")
        return

    for path in sessions:
        client = TelegramClient(
            str(path.with_suffix("")), settings.api_id, settings.api_hash
        )
        try:
            await client.connect()
            if not await client.is_user_authorized():
                print(f"[INVALID] {path.stem}")
                continue
            me = await client.get_me()
            username = f"@{me.username}" if me.username else "-"
            print(f"[OK] {path.stem}: {me.first_name or '-'} | {username} | {me.id}")
        except Exception as exc:
            print(f"[ERROR] {path.stem}: {exc}")
        finally:
            if client.is_connected():
                await client.disconnect()


def list_accounts() -> None:
    settings = load_settings()
    sessions = sorted(settings.session_dir.glob("*.session"))
    if not sessions:
        print("Belum ada session.")
        return
    for path in sessions:
        print(path.stem)


def remove_account(name: str) -> None:
    settings = load_settings()
    name = validate_name(name)
    base = settings.session_dir / name
    targets = [
        base.with_suffix(".session"),
        Path(str(base.with_suffix(".session")) + "-journal"),
    ]

    removed = False
    for target in targets:
        if target.exists():
            target.unlink()
            removed = True

    if removed:
        print(f"Session '{name}' dihapus.")
    else:
        print(f"Session '{name}' tidak ditemukan.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Kelola akun UserbotSebar Simple")
    sub = parser.add_subparsers(dest="command", required=True)

    add = sub.add_parser("add", help="Login dan tambahkan akun")
    add.add_argument("name", help="Nama session, contoh: akun1")

    remove = sub.add_parser("remove", help="Hapus session akun")
    remove.add_argument("name", help="Nama session")

    sub.add_parser("list", help="Tampilkan session lokal")
    sub.add_parser("check", help="Validasi semua session ke Telegram")
    return parser


def main() -> None:
    args = build_parser().parse_args()

    if args.command == "add":
        asyncio.run(add_account(args.name))
    elif args.command == "remove":
        remove_account(args.name)
    elif args.command == "list":
        list_accounts()
    elif args.command == "check":
        asyncio.run(check_accounts())


if __name__ == "__main__":
    main()
