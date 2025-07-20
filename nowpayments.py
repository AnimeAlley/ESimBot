import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("NOWPAYMENTS_API_KEY")
BASE_URL = "https://api.nowpayments.io/v1"
HEADERS = {
    "x-api-key": API_KEY,
    "Content-Type": "application/json"
}


def create_payment(price_usd: float, order_id: str, success_url: str):
    payload = {
        "price_amount": price_usd,
        "price_currency": "usd",
        "order_id": order_id,
        "success_url": success_url
    }
    response = requests.post(f"{BASE_URL}/payment", json=payload, headers=HEADERS)
    response.raise_for_status()
    data = response.json()
    return data.get("invoice_url"), data.get("payment_id")


def get_payment_status(payment_id: str):
    response = requests.get(f"{BASE_URL}/payment/{payment_id}", headers=HEADERS)
    response.raise_for_status()
    return response.json().get("payment_status")
