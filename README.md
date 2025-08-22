# 🛍️ Merch Stock Bot – macOS + Telegram

This project is a **Python 3.12** bot that monitors one or more web pages for **new or available merchandise** (e.g., a band’s merch on a clothing brand’s website).  
It runs in the background on macOS via `launchd` and sends **Telegram** notifications as soon as availability is detected.

## ✨ Features
- 🔎 Monitors any set of URLs you configure (new arrivals pages, search pages, product/landing pages, etc.).
- ⏱️ Runs on a schedule (default every 15 minutes, configurable).
- 📲 Sends instant Telegram notifications when availability keywords are found.
- 🗂️ Logs activity to `log.txt` for troubleshooting.
- ⚡ Works headless in the background using `launchd` (no manual start needed).

## 🛠️ Tech
- Python 3.12
- Requests / urllib3
- Telegram Bot API
- macOS `launchd`

## 🚀 Quick start
1. **Clone the repo**
   ```bash
   git clone https://github.com/<your-username>/merch-stock-bot.git
   cd merch-stock-bot
   ````

2. **Create a virtual environment & install dependencies**

   ```bash
   /usr/local/bin/python3.12 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   deactivate
   ```

3. **Configure**

   ```bash
   cp config.example.toml config.toml
   ```

   Fill in your Telegram Bot Token, Chat ID, and the pages/keywords you want to monitor.

4. **Install the LaunchAgent (macOS)**
   Copy `com.merchbot.plist` to `~/Library/LaunchAgents/`
   Edit the file to update the path `/Users/your-username/...` with your own macOS username.
   Then load & start:

   ```bash
   launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.merchbot.plist
   launchctl enable gui/$(id -u)/com.merchbot
   launchctl kickstart -k gui/$(id -u)/com.merchbot
   ```

   Logs: `log.txt`, `launchd.out.log`, `launchd.err.log`

## 📝 Configuration example (`config.toml`)

```toml
[telegram]
# Your Telegram bot token and the chat ID to notify
bot_token = "123456789:ABCdefGHIjklMNOpqrSTUvwxYZ"
chat_id   = "987654321"

# Each [[products]] block defines one page to monitor
# "available_keywords" are matched (case-insensitive) to decide availability
# "soldout_keywords" are used to avoid false positives

[[products]]
name = "New arrivals"
url  = "https://example.com/new-arrivals"
available_keywords = ["add to cart", "in stock", "buy now"]
soldout_keywords   = ["sold out", "no stock", "unavailable"]

[[products]]
name = "Band merch search"
url  = "https://example.com/search?q=band+name"
available_keywords = ["add to cart", "in stock", "buy now"]
soldout_keywords   = ["sold out", "no stock", "unavailable"]
```

## 🔧 Useful commands

**Check agent status**

```bash
launchctl list | grep com.merchbot
```

**Restart now**

```bash
launchctl kickstart -k gui/$(id -u)/com.merchbot
```

**Tail logs**

```bash
tail -n 50 log.txt
tail -n 50 launchd.err.log
```

## ⚠️ Disclaimer

This bot is for personal/educational use. You are responsible for complying with the terms of the websites you monitor.

```

---
