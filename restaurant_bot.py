import os
import json
import requests
from datetime import datetime, timedelta

# -----------------------
# CONFIG from env
# -----------------------
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = int(os.environ["TELEGRAM_CHAT_ID"])

# -----------------------
# Logging
# -----------------------
def log(msg):
    t = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    line = f"[{t}] {msg}"
    print(line)
    with open("bot.log", "a") as f:
        f.write(line + "\n")

# -----------------------
# Telegram
# -----------------------
def send_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML"
    }
    try:
        r = requests.post(url, data=payload)
        if r.status_code != 200:
            log(f"Telegram error: {r.text}")
    except Exception as e:
        log(f"Telegram send failed: {e}")

# -----------------------
# Load / save
# -----------------------
def load_restaurants():
    try:
        with open("restaurants.json") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def save_restaurants(data):
    with open("restaurants.json", "w") as f:
        json.dump(data, f, indent=2)

# -----------------------
# OSM fetch
# -----------------------
def fetch_restaurants(days_back=0):
    url = "https://overpass-api.de/api/interpreter"
    # compute timestamp filter if days_back > 0
    time_filter = ""
    if days_back > 0:
        dt = datetime.utcnow() - timedelta(days=days_back)
        # Overpass uses ISO timestamp format: YYYY-MM-DDTHH:MM:SSZ
        time_filter = f'(if:timestamp() > "{dt.strftime("%Y-%m-%dT%H:%M:%SZ")}")'

    query = f"""
    [out:json];
    area["name"="Berlin"]->.searchArea;
    (
      node["amenity"="restaurant"](area.searchArea){time_filter};
    );
    out;
    """
    try:
        r = requests.post(url, data=query)
        data = r.json()
        return data.get("elements", [])
    except ValueError:
        log("Error: could not parse JSON from Overpass API")
        return []

# -----------------------
# Main logic
# -----------------------
def run():
    log("Starting restaurant check")

    saved = load_restaurants()
    saved_dict = {r["osm_id"]: r for r in saved}

    # Step 1: fetch last 4 months initially
    if not saved:
        log("First run: fetching last 4 months (~120 days)")
        elements = fetch_restaurants(days_back=120)
    else:
        # Step 2: fetch last 1 day for updates
        elements = fetch_restaurants(days_back=1)

    new_restaurants = []
    updated_restaurants = []

    for el in elements:
        tags = el.get("tags", {})
        osm_id = f"{el['type']}_{el['id']}"
        ts = el.get("timestamp")
        if not ts:
            continue
        t = datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ")

        if osm_id not in saved_dict:
            # new restaurant
            r = {
                "osm_id": osm_id,
                "name": tags.get("name", "Unnamed"),
                "lat": el.get("lat"),
                "lon": el.get("lon"),
                "timestamp": ts
            }
            new_restaurants.append(r)
            saved_dict[osm_id] = r
        else:
            # check if modified
            prev = saved_dict[osm_id]
            prev_time = datetime.strptime(prev["timestamp"], "%Y-%m-%dT%H:%M:%SZ")
            if t > prev_time:
                r = {
                    "osm_id": osm_id,
                    "name": tags.get("name", "Unnamed"),
                    "lat": el.get("lat"),
                    "lon": el.get("lon"),
                    "timestamp": ts
                }
                updated_restaurants.append(r)
                saved_dict[osm_id] = r

    save_restaurants(list(saved_dict.values()))

    # Build message
    msg = ""
    if new_restaurants:
        msg += "🍽️ <b>New restaurants added:</b>\n"
        for r in new_restaurants:
            msg += f"- {r['name']} ({r['lat']:.5f}, {r['lon']:.5f})\n"
        msg += "\n"
    if updated_restaurants:
        msg += "🔄 <b>Restaurants modified:</b>\n"
        for r in updated_restaurants:
            msg += f"- {r['name']} ({r['lat']:.5f}, {r['lon']:.5f})\n"

            if msg:
                send_message(msg)
            else:
                log("No changes, nothing sent")
    send_message(msg)
    log(f"Sent {len(new_restaurants)} new and {len(updated_restaurants)} updated restaurants")

if __name__ == "__main__":
    run()