# main.py for GitHub Actions (single-run)
import os
import asyncio
from telegram import Bot
from scanner import scan_market
from poster import generate_signal_message
import requests

# ---- Get secrets from GitHub Actions ----
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_ID = os.environ.get("CHANNEL_ID")

if not BOT_TOKEN or not CHANNEL_ID:
    raise ValueError("Missing BOT_TOKEN or CHANNEL_ID in GitHub Secrets")

bot = Bot(token=BOT_TOKEN)

# ---- Async function to safely send Telegram message ----
async def send_message_safe(message):
    try:
        await bot.send_message(chat_id=CHANNEL_ID, text=message)
    except Exception as e:
        print("Telegram error:", e)

# ---- Fetch all USDT pairs from Binance ----
def fetch_usdt_pairs():
    try:
        resp = requests.get("https://api.binance.us/api/v3/exchangeInfo", timeout=10)
        data = resp.json()
        usdt_pairs = [s['symbol'] for s in data['symbols'] if s['symbol'].endswith("USDT")]
        print(f"Fetched {len(usdt_pairs)} USDT pairs")
        return usdt_pairs
    except Exception as e:
        print("Error fetching exchange info:", e)
        return []

# ---- Main bot run ----
async def run_bot():
    posted = set()  # Track already posted signals for this run
    symbols = fetch_usdt_pairs()
    if not symbols:
        print("No symbols fetched, exiting this run")
        return

    signals = scan_market(symbols)

    for s in signals:
        key = f"{s['coin']}_{s['trade_type']}"
        if key in posted:
            continue
        msg = generate_signal_message(
            s['coin'], s['entry'], s['sl'], s['tp1'], s['tp2'], s['tp3'],
            s['trade_type'], s['confidence']
        )
        print("Posting:", s['coin'], s['trade_type'])
        await send_message_safe(msg)
        posted.add(key)

    print("✅ Bot run completed. Exiting.")

# ---- Run the bot ----
if __name__ == "__main__":
    asyncio.run(run_bot())
