import os
from dotenv import load_dotenv

load_dotenv()  # loads .env locally; no-op on Render (uses env vars directly)

SPOTS = {
    "Pipeline":       "5842041f4e65fad6a7708890",
    "Sunset Beach":   "5842041f4e65fad6a7708891",
    "Haleiwa":        "5842041f4e65fad6a7708898",
    "Waikiki":        "584204204e65fad6a7709148",
    "Sandy Beach":    "5842041f4e65fad6a7708df6",
    "Ala Moana Bowls":"5842041f4e65fad6a7708b42",
    "Kewalos":        "5a983b55ab43c7001a4129d9",
}

# Twilio (SMS)
TWILIO_ACCOUNT_SID  = os.environ.get("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN   = os.environ.get("TWILIO_AUTH_TOKEN", "")
TWILIO_FROM_NUMBER  = os.environ.get("TWILIO_FROM_NUMBER", "")  # e.g. +18001234567

# ManyChat (Instagram DM)
MANYCHAT_API_KEY    = os.environ.get("MANYCHAT_API_KEY", "")

PORT = int(os.environ.get("PORT", 5055))
PUSH_SECRET = os.environ.get("PUSH_SECRET", "changeme")
