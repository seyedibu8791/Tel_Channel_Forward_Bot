# Telegram Signal Forwarder Bot

A lightweight Telegram bot that:
- Reads signals from a source channel (by username)
- Reformats them into a clean structured message
- Sends to a target channel
- Filters duplicates, cancelled signals, and handles flexible formats

---

## 🧩 Features

✅ Works with channel usernames (no numeric IDs needed)  
✅ Filters duplicates within time window  
✅ Converts “Manually Cancelled” → `/close #PAIR`  
✅ Supports flexible signal text formats  
✅ Auto Flask keep-alive and GitHub Actions ping  
✅ Deployable on Render (Free Tier)

---

## 🚀 Setup Steps

1. **Fork this repo** to your GitHub account.
2. Go to [Render.com](https://render.com) → **New Web Service**.
3. Connect your GitHub repo.
4. Set environment variables in Render:

| Key | Example |
|-----|----------|
| `BOT_TOKEN` | `123456789:ABCdefGHIJKlmnoPQRstuVWxyz` |
| `SOURCE_CHANNEL_USERNAME` | `@mysignalsource` |
| `TARGET_CHANNEL_USERNAME` | `@mytargetchannel` |

5. Deploy → watch logs → you’ll see:
