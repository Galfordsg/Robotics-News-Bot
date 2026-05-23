import feedparser
import requests
import time
from datetime import datetime

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

if not TELEGRAM_TOKEN or not CHAT_ID:
    print("❌ Missing credentials!")
    exit(1)

# Only reliable feeds
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
    print(f"[{datetime.now()}] Starting run...")

    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:30]:
                title = entry.get("title", "").strip()
                link = entry.get("link", "")
                summary = entry.get("summary", entry.get("description", ""))[:400]

                if not title or not link:
                    continue

                # Prioritize more interesting articles
                if any(kw in (title + summary).lower() for kw in ["humanoid", "drone", "autonomous", "breakthrough", "unveils", "launches", "optimus", "atlas"]):
                    send_to_telegram(f"📰 **{title}**\n\n{summary}\n\n🔗 {link}")
                    sent += 1
                    time.sleep(2)
        except Exception as e:
            print(f"Error: {e}")

    # Evening summary
    time.sleep(5)
    final_msg = f"📊 **Robotics News Evening Edition** — {datetime.now().strftime('%B %d, %Y')}\n\n{sent} articles sent today.\n\nCovered latest developments in humanoid robots, drones, autonomous systems and other key robotics news."
    send_to_telegram(final_msg)

    print(f"Finished. Sent {sent} articles.")

if __name__ == "__main__":
    main()
