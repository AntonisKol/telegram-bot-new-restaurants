import json
import requests
from datetime import datetime, timedelta

# -------------------------------
# Telegram configuration from config.json
# -------------------------------
with open("config.json") as f:
    config = json.load(f)

TELEGRAM_BOT_TOKEN = config["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = int(config["TELEGRAM_CHAT_ID"])  # ensure numeric

# -------------------------------
# Logging
# -------------------------------
def log(msg):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {msg}"
    print(line)
    with open("bot.log", "a") as f:
        f.write(line + "\n")

# -------------------------------
# Telegram messaging
# -------------------------------
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

# -------------------------------
# Load / save previous restaurants
# -------------------------------
def load_restaurants():
    try:
        with open("restaurants.json") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def save_restaurants(data):
    with open("restaurants.json", "w") as f:
        json.dump(data, f, indent=2)

# -------------------------------
# Fetch restaurants from Overpass
# -------------------------------
def fetch_restaurants():
    url = "https://overpass-api.de/api/interpreter"
    query = """
    [out:json];
    area["name"="Berlin"]->.searchArea;
    (
      node["amenity"="restaurant"](area.searchArea);
    );
    out;
    """
    r = requests.post(url, data=query)
    data = r.json()
    return data.get("elements", [])

# -------------------------------
# Main bot logic
# -------------------------------
def run():
    log("Starting daily restaurant check")

    saved = load_restaurants()
    saved_ids = {r["osm_id"] for r in saved}

    elements = fetch_restaurants()
    cutoff = datetime.utcnow() - timedelta(days=1)

    new_restaurants = []

    for el in elements:
        tags = el.get("tags", {})
        osm_id = f"{el['type']}_{el['id']}"
        ts = el.get("timestamp")
        if not ts:
            continue
        t = datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ")
        if osm_id not in saved_ids and t > cutoff:
            restaurant = {
                "osm_id": osm_id,
                "name": tags.get("name", "Unnamed"),
                "lat": el.get("lat"),
                "lon": el.get("lon"),
                "timestamp": ts
            }
            new_restaurants.append(restaurant)
            saved.append(restaurant)

    save_restaurants(saved)

    if new_restaurants:
        msg = "🍽️ <b>Restaurants added in last 24h</b>\n\n"
        for r in new_restaurants:
            msg += f"- {r['name']} ({r['lat']:.5f}, {r['lon']:.5f})\n"
        send_message(msg)
        log(f"Sent {len(new_restaurants)} restaurants")
    else:
        send_message("No new restaurants were added today.")
        log("No new restaurants")

# -------------------------------
# Run immediately when executed
# -------------------------------
if __name__ == "__main__":
    run()