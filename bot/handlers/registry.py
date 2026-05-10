from telegram.ext import CommandHandler, CallbackQueryHandler

COMMAND_HANDLERS = []


def command(name: str):
    def decorator(func):
        COMMAND_HANDLERS.append(
            CommandHandler(name, func)
        )
        return func

    return decorator


CALLBACK_HANDLERS = []


def callback(pattern: str):
    def decorator(func):
        CALLBACK_HANDLERS.append(
            CallbackQueryHandler(func, pattern=pattern)
        )
        return func

    return decorator
