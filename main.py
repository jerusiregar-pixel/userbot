from __future__ import annotations

import asyncio
import logging
import signal

from app.config import load_settings
from app.manager import ClientManager


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    logging.getLogger("telethon.network.mtprotosender").setLevel(logging.WARNING)


async def main() -> None:
    settings = load_settings()
    manager = ClientManager(settings)
    stop_event = asyncio.Event()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, stop_event.set)
        except NotImplementedError:
            pass

    await manager.start_all()

    print("\nUserbotSebar Simple aktif. Tekan Ctrl+C untuk berhenti.\n")

    wait_clients = asyncio.create_task(manager.wait_forever())
    wait_stop = asyncio.create_task(stop_event.wait())

    done, pending = await asyncio.wait(
        {wait_clients, wait_stop}, return_when=asyncio.FIRST_COMPLETED
    )

    for task in pending:
        task.cancel()
    if pending:
        await asyncio.gather(*pending, return_exceptions=True)

    for task in done:
        if task is wait_clients:
            exc = task.exception()
            if exc:
                raise exc

    await manager.stop_all()


if __name__ == "__main__":
    configure_logging()
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    except Exception as exc:
        logging.getLogger(__name__).error("Fatal: %s", exc)
        raise SystemExit(1)
