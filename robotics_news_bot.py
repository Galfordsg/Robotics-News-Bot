import feedparser
import requests
import time
import os
from datetime import datetime, timedelta

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

if not TELEGRAM_TOKEN or not CHAT_ID:
    print("❌ Missing credentials!")
    exit(1)

RSS_FEEDS = [
    "https://www.therobotreport.com/feed/",
    "https://roboticsandautomationnews.com/feed/",
]

def send_to_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}, timeout=10)
    except:
        pass

def main():
    sent = 0
    cutoff = datetime.now() - timedelta(days=1)   # Only last 24 hours
    print(f"[{datetime.now()}] Starting 24h filter run...")

    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:40]:
                title = entry.get("title", "").strip()
                link = entry.get("link", "")
                summary = entry.get("summary", entry.get("description", ""))[:400]

                if not title or not link:
                    continue

                # Strict date filter
                if entry.get("published_parsed"):
                    try:
                        pub_date = datetime.fromtimestamp(time.mktime(entry.published_parsed))
                        if pub_date < cutoff:
                            continue
                    except:
                        pass

                send_to_telegram(f"📰 **{title}**\n\n{summary}\n\n🔗 {link}")
                sent += 1
                time.sleep(2)
        except Exception as e:
            print(f"Error: {e}")

    time.sleep(6)
    final_msg = f"📊 **Robotics News Evening Edition** — {datetime.now().strftime('%B %d, %Y')}\n\n{sent} articles sent today."
    send_to_telegram(final_msg)

    print(f"Finished. Sent {sent} articles.")

if __name__ == "__main__":
    main()
