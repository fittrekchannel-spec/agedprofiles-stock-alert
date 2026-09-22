"""AgedProfiles stock monitor.

Opens the product page(s) in a headless Chromium, reads "N In Stock" /
"Out of Stock", and sends a Discord and/or WhatsApp alert when stock
appears or goes up. Runs in a loop for LOOP_MINUTES (GitHub Actions
restarts it every hour), checking every CHECK_SECONDS.
"""
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright

PRODUCTS = {
    "Aged YouTube Accounts 2006 - 2009 with Videos":
        "https://agedprofiles.com/product/aged-youtube-accounts-2006-2009-with-videos",
}

STATE_FILE = Path(__file__).with_name("state.json")
CHECK_SECONDS = int(os.environ.get("CHECK_SECONDS", "60"))
LOOP_MINUTES = float(os.environ.get("LOOP_MINUTES", "0"))  # 0 = check once
DISCORD_WEBHOOK = os.environ.get("DISCORD_WEBHOOK", "").strip()
WA_PHONE = os.environ.get("WHATSAPP_PHONE", "").strip()      # e.g. +923001234567
WA_APIKEY = os.environ.get("WHATSAPP_APIKEY", "").strip()    # from CallMeBot
NTFY_TOPIC = os.environ.get("NTFY_TOPIC", "").strip()        # ntfy.sh topic, no account needed
DISCORD_MENTION = os.environ.get("DISCORD_MENTION", "@everyone").strip()


try:  # emoji in the log shouldn't crash a Windows console
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


def log(msg):
    print(time.strftime("%H:%M:%S"), msg, flush=True)


def read_stock(page, url):
    """Return int stock (0 = out of stock) or None if the page couldn't be read."""
    page.goto(url, wait_until="domcontentloaded", timeout=60000)
    # The site shows a short "Please wait..." JS check, then reloads itself.
    for _ in range(30):
        text = page.inner_text("body")
        if "Add to Cart" in text or "Out of Stock" in text:
            break
        page.wait_for_timeout(1000)
    else:
        return None
    # The first stock line belongs to the main product ("Commonly Bought
    # Together" items come after it).
    main = text.split("Commonly Bought Together")[0]
    m = re.search(r"([\d,]+)\s+In Stock", main, re.I)
    if m:
        return int(m.group(1).replace(",", ""))
    if re.search(r"Out of Stock", main, re.I):
        return 0
    return None


def send_discord(msg):
    if not DISCORD_WEBHOOK:
        return
    body = json.dumps({"content": f"{DISCORD_MENTION} {msg}".strip(),
                       "allowed_mentions": {"parse": ["everyone"]}}).encode()
    req = urllib.request.Request(DISCORD_WEBHOOK, data=body, method="POST",
                                 headers={"Content-Type": "application/json",
                                          "User-Agent": "stock-alert"})
    urllib.request.urlopen(req, timeout=20).read()


def send_whatsapp(msg):
    if not (WA_PHONE and WA_APIKEY):
        return
    q = urllib.parse.urlencode({"phone": WA_PHONE, "text": msg, "apikey": WA_APIKEY})
    urllib.request.urlopen(f"https://api.callmebot.com/whatsapp.php?{q}", timeout=30).read()


def send_ntfy(msg):
    if not NTFY_TOPIC:
        return
    req = urllib.request.Request(
        f"https://ntfy.sh/{NTFY_TOPIC}", data=msg.encode("utf-8"), method="POST",
        headers={"Title": "AgedProfiles stock", "Priority": "urgent", "Tags": "rotating_light"})
    urllib.request.urlopen(req, timeout=20).read()


def notify(msg):
    log("ALERT: " + msg.replace("\n", " | "))
    for fn in (send_ntfy, send_discord, send_whatsapp):
        try:
            fn(msg)
        except Exception as e:  # one channel failing shouldn't stop the other
            log(f"{fn.__name__} failed: {e}")


def load_state():
    try:
        return json.loads(STATE_FILE.read_text())
    except Exception:
        return {}


def check_all(page, state):
    changed = False
    for name, url in PRODUCTS.items():
        try:
            stock = read_stock(page, url)
        except Exception as e:
            log(f"{name}: error {e}")
            continue
        if stock is None:
            log(f"{name}: could not read stock")
            continue
        prev = state.get(name, 0)
        log(f"{name}: {stock} in stock (was {prev})")
        if stock > prev:
            if prev == 0:
                head = "🟢 IN STOCK AA GAYE!"
            else:
                head = f"🟢 Aur aa gaye (+{stock - prev})"
            notify(f"{head}\n{name}\n📦 {stock} accounts available\n🛒 {url}")
        elif stock == 0 and prev > 0:
            notify(f"🔴 Khatam ho gaye: {name} ab Out of Stock hai.")
        if stock != prev:
            state[name] = stock
            changed = True
    return changed


def main():
    if os.environ.get("TEST_ALERT") == "1":
        notify("✅ Test: AgedProfiles stock alert chal raha hai.")
        return
    state = load_state()
    deadline = time.time() + LOOP_MINUTES * 60
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        while True:
            if check_all(page, state):
                STATE_FILE.write_text(json.dumps(state, indent=2))
            if time.time() + CHECK_SECONDS > deadline:
                break
            time.sleep(CHECK_SECONDS)
        browser.close()


if __name__ == "__main__":
    main()
