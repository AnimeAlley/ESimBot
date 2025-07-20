import re
import os
from typing import Dict, Any
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, CallbackQueryHandler, MessageHandler, CommandHandler, filters
from Backend.zendit_api import get_countries, get_plans, order_esim
from nowpayments import create_payment, get_payment_status

# Conversation states
SELECT_COUNTRY, SELECT_PLAN, ASK_EMAIL, WAIT_PAYMENT = range(4)

# simple in-memory session store
user_sessions: Dict[int, Dict[str, Any]] = {}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_sessions[user_id] = {}
    try:
        countries = get_countries()
    except Exception as e:
        await update.message.reply_text(f"Failed to load countries: {e}")
        return ConversationHandler.END

    keyboard = [[InlineKeyboardButton(c['name'], callback_data=c['code'])] for c in countries]
    await update.message.reply_text(
        "Select your destination country:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return SELECT_COUNTRY


async def country_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    code = query.data
    user_id = query.from_user.id
    user_sessions[user_id]['country'] = code

    try:
        plans = get_plans(code)
    except Exception as e:
        await query.edit_message_text(f"Error getting plans: {e}")
        return ConversationHandler.END

    buttons = []
    for p in plans:
        text = f"{p['name']} - ${p['price_usd']}"
        buttons.append([InlineKeyboardButton(text, callback_data=p['id'])])
    await query.edit_message_text("Choose a plan:", reply_markup=InlineKeyboardMarkup(buttons))
    return SELECT_PLAN


async def plan_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    plan_id = query.data
    user_id = query.from_user.id
    session = user_sessions.setdefault(user_id, {})
    session['plan_id'] = plan_id
    try:
        plans = get_plans(session['country'])
        for p in plans:
            if p['id'] == plan_id:
                session['price_usd'] = float(p['price_usd'])
                break
    except Exception:
        session['price_usd'] = 0

    await query.edit_message_text("Please enter your email address:")
    return ASK_EMAIL


async def email_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    email = update.message.text.strip()
    user_id = update.effective_user.id
    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
        await update.message.reply_text("Invalid email. Please send a valid email:")
        return ASK_EMAIL

    session = user_sessions[user_id]
    session['email'] = email
    price = session.get('price_usd', 0)
    order_id = f"{user_id}_{session['plan_id']}"
    success_url = os.getenv('SUCCESS_URL', 'https://t.me/' + context.bot.username)

    try:
        invoice_url, payment_id = create_payment(price, order_id, success_url)
    except Exception as e:
        await update.message.reply_text(f"Failed to create payment: {e}")
        return ConversationHandler.END

    session['payment_id'] = payment_id
    session['payment_status'] = 'waiting'
    await update.message.reply_text(
        "Please pay for your eSIM by clicking the button below:",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Pay", url=invoice_url)]])
    )
    context.job_queue.run_repeating(poll_payment, interval=30, first=30,
                                    data={'user_id': user_id, 'count': 0}, name=str(user_id))
    return WAIT_PAYMENT


async def poll_payment(context: ContextTypes.DEFAULT_TYPE):
    data = context.job.data
    user_id = data['user_id']
    count = data.get('count', 0) + 1
    data['count'] = count
    session = user_sessions.get(user_id)
    if not session:
        context.job.schedule_removal()
        return

    try:
        status = get_payment_status(session['payment_id'])
    except Exception as e:
        await context.bot.send_message(chat_id=user_id, text=f"Error checking payment: {e}")
        user_sessions.pop(user_id, None)
        context.job.schedule_removal()
        return

    session['payment_status'] = status
    if status == 'finished':
        await context.bot.send_message(chat_id=user_id, text="Payment confirmed! Ordering your eSIM...")
        try:
            order = order_esim(session['plan_id'], session['email'])
            msg = (
                "Here are your activation details:\n"
                f"SM-DP+: {order.get('smdp_plus')}\n"
                f"Activation Code: {order.get('activation_code')}"
            )
            qr = order.get('qr_code')
            if qr:
                await context.bot.send_photo(chat_id=user_id, photo=qr, caption=msg)
            else:
                await context.bot.send_message(chat_id=user_id, text=msg)
        except Exception as e:
            await context.bot.send_message(chat_id=user_id, text=f"Failed to order eSIM: {e}")
        user_sessions.pop(user_id, None)
        context.job.schedule_removal()
    elif status in ('expired', 'failed'):
        await context.bot.send_message(chat_id=user_id, text="Payment failed or expired. Use /start to try again.")
        user_sessions.pop(user_id, None)
        context.job.schedule_removal()
    elif count >= 20:
        await context.bot.send_message(chat_id=user_id, text="Payment not received in time. Please try again.")
        user_sessions.pop(user_id, None)
        context.job.schedule_removal()


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_sessions.pop(update.effective_user.id, None)
    await update.message.reply_text("Goodbye!")
    return ConversationHandler.END


def build_conversation_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            SELECT_COUNTRY: [CallbackQueryHandler(country_chosen)],
            SELECT_PLAN: [CallbackQueryHandler(plan_chosen)],
            ASK_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, email_received)],
            WAIT_PAYMENT: []
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
