from telegram import Update
from telegram.ext import ContextTypes
from Core.conversation_logic import start


async def initiate_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start(update, context)
