# bot/handlers/registry.py

from importlib import import_module
import pkgutil

from telegram.ext import (
    CommandHandler,
    CallbackQueryHandler,
)

import bot.handlers

_COMMAND_HANDLERS: list[CommandHandler] = []
_CALLBACK_HANDLERS: list[CallbackQueryHandler] = []

_LOADED = False


# =========================
# DECORATORS
# =========================
def command(name: str):
    def decorator(func):
        _COMMAND_HANDLERS.append(
            CommandHandler(name, func)
        )
        return func

    return decorator


def callback(pattern: str):
    def decorator(func):
        _CALLBACK_HANDLERS.append(
            CallbackQueryHandler(func, pattern=pattern)
        )
        return func

    return decorator


# =========================
# AUTOLOAD
# =========================
def _load_handlers():
    for module in pkgutil.iter_modules(bot.handlers.__path__):
        if module.name in {
            "__init__",
            "registry",
            "text",
        }:
            continue

        import_module(f"bot.handlers.{module.name}")


def _ensure_loaded():
    global _LOADED

    if _LOADED:
        return

    _load_handlers()
    _LOADED = True


# =========================
# GETTERS
# =========================
def get_handlers():
    _ensure_loaded()

    return [
        *_COMMAND_HANDLERS,
        *_CALLBACK_HANDLERS,
    ]
