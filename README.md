# UserbotSebar Simple

Rewrite minimal dari UserbotSebar dengan fokus pada **multi-client yang mudah dipahami, mudah dijalankan di VPS, dan mudah dikembangkan**.

## Kenapa dibuat ulang?

Versi lama memiliki banyak folder, command, plugin, helper, database, dan dependency yang saling terhubung. Versi ini sengaja mengecilkan inti project menjadi empat konsep:

- `app/` — core multi-client dan config.
- `modules/` — semua fitur userbot.
- `data/sessions/` — session Telegram.
- `manage.py` — tambah, cek, dan hapus akun.

Tidak ada MongoDB, bot seller, AI, downloader, voice call, scheduler, atau puluhan plugin bawaan.

## Struktur

```text
UserbotSebar-Simple/
├── app/
│   ├── config.py
│   ├── loader.py
│   └── manager.py
├── modules/
│   ├── basic.py
│   └── broadcast.py
├── data/
│   └── sessions/
├── main.py
├── manage.py
├── install.sh
├── start.sh
├── service.sh
├── requirements.txt
└── .env.example
```

## Fitur yang dipertahankan

- Multi-client: satu proses bisa menjalankan banyak akun Telegram.
- Session file terpisah untuk setiap akun.
- Auto-load module dari folder `modules/`.
- Command dasar: `.ping`, `.me`, `.help`.
- Broadcast grup: `.bc` dan `.bcstop`.
- FloodWait handling dan delay broadcast.
- Systemd service agar otomatis hidup setelah reboot VPS.

## Install di Ubuntu/Debian VPS

```bash
bash install.sh
```

Setelah selesai:

```bash
nano .env
```

Isi minimal:

```env
API_ID=123456
API_HASH=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

API ID dan API hash dibuat di `my.telegram.org`.

## Tambah akun

```bash
.venv/bin/python manage.py add akun1
```

Masukkan nomor Telegram, OTP, dan password 2FA bila diminta.

Tambah akun lain:

```bash
.venv/bin/python manage.py add akun2
.venv/bin/python manage.py add akun3
```

Cek akun:

```bash
.venv/bin/python manage.py list
.venv/bin/python manage.py check
```

Hapus akun:

```bash
bash service.sh stop
.venv/bin/python manage.py remove akun2
bash service.sh start
```

## Jalankan

Foreground untuk testing:

```bash
bash start.sh
```

Production dengan systemd:

```bash
bash service.sh install
```

Perintah berikutnya:

```bash
bash service.sh status
bash service.sh logs
bash service.sh restart
bash service.sh stop
bash service.sh start
```

## Command userbot

```text
.ping
.me
.help
.bc teks yang ingin dikirim
.bcstop
```

Atau reply sebuah pesan lalu kirim:

```text
.bc
```

Pesan yang direply akan di-forward ke grup yang akun tersebut ikuti. Gunakan broadcast hanya pada chat tempat kamu memang diizinkan mengirim pesan dan jangan membuat interval terlalu agresif.

## Menambah fitur baru

Buat satu file baru di `modules/`, misalnya `modules/example.py`:

```python
from telethon import TelegramClient, events
from app.config import Settings


def setup(client: TelegramClient, settings: Settings) -> None:
    async def handler(event):
        await event.edit("Hello")

    client.add_event_handler(
        handler,
        events.NewMessage(outgoing=True, pattern=r"^\.hello$"),
    )
```

Restart:

```bash
bash service.sh restart
```

Module otomatis ditemukan oleh `app/loader.py`. Tidak perlu mengubah `main.py` atau `manager.py`.

## Tempat menambahkan Buyer Collector / OCR nanti

Buat saja:

```text
modules/buyer_collector.py
```

Handler Telegram, OCR, regex user ID, dan penyimpanan hasil bisa ditambahkan di sana tanpa mengubah core multi-client. Jika fitur itu mulai besar, baru tambahkan folder `services/` untuk OCR/database. Jangan menambah abstraksi sebelum memang diperlukan.

## Keamanan

- Jangan commit `.env`.
- Jangan commit file `*.session`. Session Telegram adalah kredensial akun.
- Jika session bocor, cabut session tersebut dari Telegram dan buat ulang.
- Gunakan API ID/API hash milik sendiri.

## Catatan framework

Versi lama memakai Pyrogram. Rewrite ini memakai Telethon supaya core lebih kecil dan tidak bergantung pada Pyrogram yang proyek resminya sudah tidak dipelihara. Seluruh interaksi Telegram tetap menggunakan MTProto user session.
