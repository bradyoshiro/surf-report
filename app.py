from flask import Flask, render_template, jsonify, request
from surfline import fetch_all, format_report
from notify import send_sms, send_instagram_dm_by_username
from config import SPOTS, PORT
import threading
import time

app = Flask(__name__)

# Simple in-memory cache: refresh every 15 minutes
_cache = {"data": [], "ts": 0}
_cache_lock = threading.Lock()
CACHE_TTL = 900  # seconds


def get_conditions(force=False):
    now = time.time()
    with _cache_lock:
        if force or now - _cache["ts"] > CACHE_TTL or not _cache["data"]:
            _cache["data"] = fetch_all(SPOTS)
            _cache["ts"] = now
        return _cache["data"]


@app.route("/")
def index():
    conditions = get_conditions()
    return render_template("index.html", conditions=conditions)


@app.route("/api/conditions")
def api_conditions():
    force = request.args.get("refresh") == "1"
    conditions = get_conditions(force=force)
    return jsonify(conditions)


@app.route("/api/notify", methods=["POST"])
def api_notify():
    body = request.get_json(force=True)
    channel = body.get("channel")          # "sms" or "instagram"
    target  = body.get("target", "").strip()  # phone number or @username
    spots   = body.get("spots", list(SPOTS.keys()))  # optional filter

    if not channel or not target:
        return jsonify({"ok": False, "error": "channel and target required"}), 400

    conditions = get_conditions()
    filtered = [c for c in conditions if c["name"] in spots]
    message = format_report(filtered)

    if channel == "sms":
        # Normalize to E.164 if needed
        number = target if target.startswith("+") else f"+1{target.replace('-','').replace(' ','')}"
        result = send_sms(number, message)
    elif channel == "instagram":
        result = send_instagram_dm_by_username(target, message)
    else:
        return jsonify({"ok": False, "error": "channel must be 'sms' or 'instagram'"}), 400

    return jsonify(result), 200 if result["ok"] else 502


if __name__ == "__main__":
    # Pre-warm cache on startup
    print("Fetching initial conditions...")
    get_conditions(force=True)
    print(f"Starting surf report server on http://localhost:{PORT}")
    app.run(host="0.0.0.0", port=PORT, debug=False)
