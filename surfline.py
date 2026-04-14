import requests
from datetime import datetime, timezone

BASE = "https://services.surfline.com/kbyg/spots/forecasts"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Referer": "https://www.surfline.com/",
}

_COMPASS = ["N","NNE","NE","ENE","E","ESE","SE","SSE","S","SSW","SW","WSW","W","WNW","NW","NNW"]

def _deg_to_compass(deg):
    if deg is None:
        return "—"
    return _COMPASS[int((deg + 11.25) / 22.5) % 16]

RATING_LABELS = {
    "FLAT": "Flat",
    "VERY_POOR": "Very Poor",
    "POOR": "Poor",
    "POOR_TO_FAIR": "Poor to Fair",
    "FAIR": "Fair",
    "FAIR_TO_GOOD": "Fair to Good",
    "GOOD": "Good",
    "VERY_GOOD": "Very Good",
    "GOOD_TO_EPIC": "Good to Epic",
    "EPIC": "Epic",
}


def _get(endpoint, spot_id, days=1):
    params = {"spotId": spot_id, "days": days, "intervalHours": 1}
    r = requests.get(f"{BASE}/{endpoint}", params=params, headers=HEADERS, timeout=10)
    r.raise_for_status()
    return r.json()


def _closest_now(entries, key=None):
    now = datetime.now(timezone.utc).timestamp()
    best = min(entries, key=lambda x: abs(x["timestamp"] - now))
    return best[key] if key else best


def fetch_spot(name, spot_id):
    try:
        wave_data   = _get("wave",   spot_id)["data"]["wave"]
        wind_data   = _get("wind",   spot_id)["data"]["wind"]
        rating_data = _get("rating", spot_id)["data"]["rating"]

        wave   = _closest_now(wave_data)
        wind   = _closest_now(wind_data)
        rating = _closest_now(rating_data)

        surf = wave.get("surf", {})
        swell_primary = wave.get("swells", [{}])[0]

        return {
            "name": name,
            "spot_id": spot_id,
            "updated": datetime.now().strftime("%I:%M %p"),
            "surf_min": surf.get("min", 0),
            "surf_max": surf.get("max", 0),
            "surf_label": surf.get("humanRelation", "—"),
            "swell_height": round(swell_primary.get("height", 0), 1),
            "swell_period": swell_primary.get("period", 0),
            "swell_direction": round(swell_primary.get("direction", 0)),
            "swell_dir_label": _deg_to_compass(swell_primary.get("direction")),
            "wind_speed": round(wind.get("speed", 0), 1),
            "wind_direction": wind.get("direction", 0),
            "wind_dir_type": wind.get("directionType", "—"),
            "wind_gust": round(wind.get("gust", 0), 1),
            "rating_key": rating.get("rating", {}).get("key", "FLAT"),
            "rating_label": RATING_LABELS.get(
                rating.get("rating", {}).get("key", "FLAT"), "—"
            ),
            "rating_value": rating.get("rating", {}).get("value", 0),
            "error": None,
        }
    except Exception as e:
        return {"name": name, "spot_id": spot_id, "error": str(e)}


def fetch_all(spots: dict):
    results = []
    for name, spot_id in spots.items():
        results.append(fetch_spot(name, spot_id))
    return results


def format_report(conditions: list) -> str:
    lines = [f"Oahu Surf Report — {datetime.now().strftime('%b %d %I:%M %p')}", ""]
    for c in conditions:
        if c.get("error"):
            lines.append(f"{c['name']}: error fetching data")
        else:
            lines.append(
                f"{c['name']}: {c['surf_min']}-{c['surf_max']}ft "
                f"({c['rating_label']}) | "
                f"Wind: {c['wind_speed']}mph {c['wind_dir_type']} | "
                f"Swell: {c['swell_height']}ft @ {c['swell_period']}s {c['swell_dir_label']}"
            )
    return "\n".join(lines)
