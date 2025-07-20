# eSIM Telegram Bot with Crypto Payments

This bot lets Telegram users purchase eSIM plans using cryptocurrency. After selecting a country and plan, the bot creates a payment via NOWPayments. Once the payment is confirmed, the eSIM is ordered automatically from Zendit and the activation details are sent back to the user.

## Setup

### 1. Install Dependencies
```bash
pip install python-telegram-bot requests python-dotenv
```

### 2. Environment Variables
Create a `.env` file with the following keys:
```
API_TOKEN=your_telegram_bot_token
ZENDIT_API_KEY=your_zendit_api_key
NOWPAYMENTS_API_KEY=your_nowpayments_key
# optional URL Telegram opens after successful payment
SUCCESS_URL=https://t.me/your_bot
```

### 3. Run the Bot
```
python main.py
```

Start the bot with `/start` in Telegram and follow the prompts to choose a plan and pay with crypto.
