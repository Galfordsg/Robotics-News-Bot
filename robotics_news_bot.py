import feedparser
import requests
import time
from datetime import datetime

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
    print(f"[{datetime.now()}] Script started successfully.")
    sent = 0

    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            print(f"Fetched feed: {feed_url}")
            for entry in feed.entries[:8]:   # Limit to avoid flood
                title = entry.get("title", "").strip()
                link = entry.get("link", "")
                summary = entry.get("summary", entry.get("description", ""))[:300]

                if title and link:
                    send_to_telegram(f"📰 **{title}**\n\n{summary}\n\n🔗 {link}")
                    sent += 1
                    time.sleep(2)
        except Exception as e:
            print(f"Error with feed {feed_url}: {e}")

    time.sleep(4)
    send_to_telegram(f"📊 **Robotics News Evening Edition** — {datetime.now().strftime('%B %d, %Y')}\n\nSent {sent} articles today.")
    print(f"Finished. Sent {sent} articles.")

if __name__ == "__main__":
    main()
