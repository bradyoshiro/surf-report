from flask import Flask, render_template, jsonify, request
from surfline import fetch_all, format_report
from notify import send_sms, send_instagram_dm_by_username
from config import SPOTS, PORT, PUSH_SECRET
import threading
import time
import os

app = Flask(__name__)

# Cache — populated either by Mac push or direct fetch fallback
_cache = {"data": [], "ts": 0}
_cache_lock = threading.Lock()


def get_conditions():
    with _cache_lock:
        return _cache["data"]


@app.route("/")
def index():
    conditions = get_conditions()
    return render_template("index.html", conditions=conditions)


@app.route("/api/conditions")
def api_conditions():
    return jsonify(get_conditions())


# Mac pushes fresh data here every 30 min
@app.route("/api/update", methods=["POST"])
def api_update():
    secret = request.headers.get("X-Push-Secret", "")
    if secret != PUSH_SECRET:
        return jsonify({"ok": False, "error": "unauthorized"}), 401
    data = request.get_json(force=True)
    if not isinstance(data, list):
        return jsonify({"ok": False, "error": "expected list"}), 400
    with _cache_lock:
        _cache["data"] = data
        _cache["ts"] = time.time()
    return jsonify({"ok": True, "spots": len(data)})


@app.route("/api/notify", methods=["POST"])
def api_notify():
    body = request.get_json(force=True)
    channel = body.get("channel")
    target  = body.get("target", "").strip()
    spots   = body.get("spots", list(SPOTS.keys()))

    if not channel or not target:
        return jsonify({"ok": False, "error": "channel and target required"}), 400

    conditions = get_conditions()
    if not conditions:
        return jsonify({"ok": False, "error": "No data yet — Mac push pending"}), 503

    filtered = [c for c in conditions if c["name"] in spots]
    message = format_report(filtered)

    if channel == "sms":
        number = target if target.startswith("+") else f"+1{target.replace('-','').replace(' ','')}"
        result = send_sms(number, message)
    elif channel == "instagram":
        result = send_instagram_dm_by_username(target, message)
    else:
        return jsonify({"ok": False, "error": "channel must be 'sms' or 'instagram'"}), 400

    return jsonify(result), 200 if result["ok"] else 502


if __name__ == "__main__":
    print(f"Starting surf report server on http://localhost:{PORT}")
    app.run(host="0.0.0.0", port=PORT, debug=False)
