from __future__ import annotations

import importlib
import logging
import pkgutil
from types import ModuleType

from telethon import TelegramClient

from app.config import Settings

logger = logging.getLogger(__name__)


def _iter_modules() -> list[ModuleType]:
    """Load every public Python module inside ./modules."""
    package = importlib.import_module("modules")
    loaded: list[ModuleType] = []

    for info in sorted(pkgutil.iter_modules(package.__path__), key=lambda item: item.name):
        if info.name.startswith("_"):
            continue
        loaded.append(importlib.import_module(f"modules.{info.name}"))

    return loaded


MODULES = _iter_modules()


def register_modules(client: TelegramClient, settings: Settings) -> None:
    """Register handlers from each module on one Telegram client."""
    for module in MODULES:
        setup = getattr(module, "setup", None)
        if setup is None:
            logger.warning("Module %s dilewati: tidak memiliki setup().", module.__name__)
            continue

        setup(client, settings)
        logger.debug("Loaded %s on %s", module.__name__, client.session.filename)
