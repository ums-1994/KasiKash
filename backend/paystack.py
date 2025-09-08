import os
import requests


PAYSTACK_SECRET = os.getenv("PAYSTACK_SECRET_KEY", "")
BASE_URL = os.getenv("PAYSTACK_BASE_URL", "https://api.paystack.co")


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {PAYSTACK_SECRET}",
        "Content-Type": "application/json",
    }


def initialize_add_card(email: str, amount_kobo: int, reference: str, callback_url: str, metadata: dict | None = None) -> str:
    """Initialize a small verification transaction to capture reusable authorization.

    Returns the authorization_url that the user should be redirected to.
    """
    url = f"{BASE_URL}/transaction/initialize"
    payload = {
        "email": email,
        "amount": amount_kobo,
        "reference": reference,
        "callback_url": callback_url,
        "metadata": metadata or {},
        # currency defaults to NGN on Paystack; include if ZAR supported for your account
    }
    resp = requests.post(url, headers=_headers(), json=payload, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    return data["data"]["authorization_url"]


def verify_transaction(reference: str) -> dict:
    """Verify a transaction by reference and return Paystack JSON."""
    url = f"{BASE_URL}/transaction/verify/{reference}"
    resp = requests.get(url, headers=_headers(), timeout=30)
    resp.raise_for_status()
    return resp.json()


def charge_authorization(email: str, amount_kobo: int, authorization_code: str, reference: str, currency: str = "ZAR", metadata: dict | None = None) -> dict:
    """Charge a saved authorization (recurring charge). Returns Paystack JSON.

    Docs: POST /transaction/charge_authorization with email, amount, authorization_code, reference.
    """
    url = f"{BASE_URL}/transaction/charge_authorization"
    payload = {
        "email": email,
        "amount": amount_kobo,
        "authorization_code": authorization_code,
        "reference": reference,
        "currency": currency,
        "metadata": metadata or {},
    }
    resp = requests.post(url, headers=_headers(), json=payload, timeout=30)
    resp.raise_for_status()
    return resp.json()


