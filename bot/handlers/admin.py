from telegram import Update
from telegram.ext import ContextTypes

from config import OWNER_ID
from db import reset_user_limit
from script import main as script_main


async def reborn(update: Update, _: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return

    await reset_user_limit(OWNER_ID)

    await update.message.reply_text("Reborn OK")


async def release(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return

    await update.message.reply_text("Running release tasks...")

    try:
        await script_main(context.application)
        await update.message.reply_text("Release finished OK")
    except Exception as e:
        await update.message.reply_text(f"Release failed: {e}")