import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("ZENDIT_API_KEY")
BASE_URL = "https://api.zendit.io/v1"
HEADERS = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}


def get_countries():
    resp = requests.get(f"{BASE_URL}/esim/countries", headers=HEADERS)
    resp.raise_for_status()
    return resp.json()


def get_plans(country_code: str):
    resp = requests.get(f"{BASE_URL}/esim/plans", params={"country": country_code}, headers=HEADERS)
    resp.raise_for_status()
    return resp.json()


def order_esim(plan_id: str, email: str):
    payload = {"plan_id": plan_id, "user_email": email}
    resp = requests.post(f"{BASE_URL}/esim/order", json=payload, headers=HEADERS)
    resp.raise_for_status()
    return resp.json()
