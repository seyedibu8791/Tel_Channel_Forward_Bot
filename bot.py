import os, re, time, threading, asyncio
from datetime import datetime, timedelta, timezone
from flask import Flask, jsonify
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

# --- CONFIG ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
SOURCE_CHANNEL_USERNAME = os.getenv("SOURCE_CHANNEL_USERNAME")  # e.g. @sourcechannel
TARGET_CHANNEL_USERNAME = os.getenv("TARGET_CHANNEL_USERNAME")  # e.g. @targetchannel
LOCAL_TZ = timezone(timedelta(hours=5, minutes=30))

# --- GLOBALS ---
app = Flask(__name__)
processed_pairs = {}

# --- PARSER ---
def parse_signal(text: str):
    try:
        pair_match = re.search(r"([A-Z]{2,})\/USDT", text)
        direction_match = re.search(r"(LONG|SHORT)", text, re.IGNORECASE)
        lev_match = re.search(r"Leverage\s*[-:]?\s*(\d+)\s*x", text, re.IGNORECASE)
        entry_match = re.search(r"Entries?\s*[-:]?\s*([\d.]+)", text, re.IGNORECASE)
        target_match = re.search(r"Target\s*1\s*[-:]?\s*([\d.]+)", text, re.IGNORECASE)
        sl_match = re.search(r"SL\s*[-:]?\s*([\d.]+)", text, re.IGNORECASE)

        pair = pair_match.group(1).upper() if pair_match else "UNKNOWN"
        direction = direction_match.group(1).upper() if direction_match else "UNKNOWN"
        leverage = lev_match.group(1) if lev_match else "?"
        entry = entry_match.group(1) if entry_match else "?"
        target = target_match.group(1) if target_match else "?"
        sl = sl_match.group(1) if sl_match else "?"

        formatted = (
            f"Action: {direction}\n"
            f"Symbol: #{pair}USDT\n"
            f"--- ⌁ ---\n"
            f"Exchange: Binance Futures\n"
            f"Leverage: Cross ({leverage}x)\n"
            f"--- ⌁ ---\n"
            f"☑️ Entry Price: {entry}\n"
            f"☑️ Take-Profit: {target}\n"
            f"☑️ Stop Loss: {sl}"
        )
        return formatted
    except Exception:
        return None


async def forward_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if not message or not message.text:
        return
    text = message.text.strip()

    now = datetime.now(LOCAL_TZ)

    # --- Skip duplicates for same pair within 20s ---
    pair_match = re.search(r"([A-Z]{2,})\/USDT", text)
    if pair_match:
        pair = pair_match.group(1)
        if pair in processed_pairs and (now - processed_pairs[pair]).total_seconds() < 20:
            return
        processed_pairs[pair] = now

    # --- Manually Cancelled ---
    if "Manually Cancelled" in text:
        pair_match = re.search(r"#?([A-Z]{2,})\/USDT", text)
        if pair_match:
            pair = pair_match.group(1)
            await context.bot.send_message(chat_id=context.bot_data["target_id"], text=f"/close #{pair}USDT")
        return

    # --- Forward only signals with leverage ---
    if "Leverage" not in text:
        return

    formatted_msg = parse_signal(text)
    if formatted_msg:
        await context.bot.send_message(chat_id=context.bot_data["target_id"], text=formatted_msg)


@app.route('/')
def home():
    now = datetime.now(LOCAL_TZ).strftime("%Y-%m-%d %H:%M:%S")
    return jsonify(status="alive", time=now)


async def get_channel_id(bot, username):
    chat = await bot.get_chat(username)
    return chat.id


def run_flask():
    app.run(host="0.0.0.0", port=10000)


def run_telegram():
    async def main():
        application = ApplicationBuilder().token(BOT_TOKEN).build()
        bot = application.bot

        # Resolve usernames → chat IDs
        source_id = await get_channel_id(bot, SOURCE_CHANNEL_USERNAME)
        target_id = await get_channel_id(bot, TARGET_CHANNEL_USERNAME)
        application.bot_data["target_id"] = target_id

        # Add handler for messages from source channel
        application.add_handler(MessageHandler(filters.Chat(source_id), forward_message))

        print(f"✅ Source ID: {source_id}, Target ID: {target_id}")
        await application.run_polling()

    asyncio.run(main())


if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    run_telegram()
