import os
from dotenv import load_dotenv
from telegram.ext import Application
from Core.conversation_logic import build_conversation_handler
from Core.error_handling import log_error

load_dotenv()
API_TOKEN = os.getenv('API_TOKEN')


def start_bot():
    app = Application.builder().token(API_TOKEN).build()
    app.add_handler(build_conversation_handler())
    app.add_error_handler(log_error)
    print('Starting polling...')
    app.run_polling(poll_interval=2)
