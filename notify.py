import requests
from config import (
    TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM_NUMBER,
    MANYCHAT_API_KEY,
)


# ── SMS via Twilio ────────────────────────────────────────────────────────────

def send_sms(to_number: str, message: str) -> dict:
    if not all([TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM_NUMBER]):
        return {"ok": False, "error": "Twilio credentials not configured"}

    try:
        r = requests.post(
            f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_ACCOUNT_SID}/Messages.json",
            auth=(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN),
            data={
                "From": TWILIO_FROM_NUMBER,
                "To": to_number,
                "Body": message[:1600],
            },
            timeout=10,
        )
        data = r.json()
        if r.status_code in (200, 201):
            return {"ok": True, "sid": data.get("sid")}
        return {"ok": False, "error": data.get("message", "Twilio error")}
    except Exception as e:
        return {"ok": False, "error": str(e)}


# ── Instagram DM via ManyChat ─────────────────────────────────────────────────

def _manychat_headers():
    return {
        "Authorization": f"Bearer {MANYCHAT_API_KEY}",
        "Content-Type": "application/json",
    }


def find_subscriber_by_instagram(username: str) -> dict:
    """
    Look up a ManyChat subscriber by their Instagram username.
    The user must have previously messaged your connected Instagram account.
    """
    if not MANYCHAT_API_KEY:
        return {"ok": False, "error": "ManyChat API key not configured"}

    username = username.lstrip("@")
    try:
        r = requests.get(
            "https://api.manychat.com/fb/subscriber/findByInstagramUsername",
            params={"username": username},
            headers=_manychat_headers(),
            timeout=10,
        )
        data = r.json()
        if data.get("status") == "success" and data.get("data"):
            return {"ok": True, "subscriber_id": data["data"]["id"]}
        return {"ok": False, "error": "Subscriber not found — they must DM your Instagram first"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def send_instagram_dm(subscriber_id: int, message: str) -> dict:
    if not MANYCHAT_API_KEY:
        return {"ok": False, "error": "ManyChat API key not configured"}

    payload = {
        "subscriber_id": subscriber_id,
        "data": {
            "version": "v2",
            "content": {
                "messages": [{"type": "text", "text": message[:1000]}],
                "actions": [],
                "quick_replies": [],
            },
        },
    }
    try:
        r = requests.post(
            "https://api.manychat.com/fb/sending/sendContent",
            json=payload,
            headers=_manychat_headers(),
            timeout=10,
        )
        data = r.json()
        if data.get("status") == "success":
            return {"ok": True}
        return {"ok": False, "error": data.get("message", "ManyChat error")}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def send_instagram_dm_by_username(username: str, message: str) -> dict:
    result = find_subscriber_by_instagram(username)
    if not result["ok"]:
        return result
    return send_instagram_dm(result["subscriber_id"], message)
