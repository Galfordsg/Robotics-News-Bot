import feedparser
import requests
import time
from datetime import datetime

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

RSS_FEEDS = [
    "https://www.therobotreport.com/feed/",                    # Good quality
    "https://roboticsandautomationnews.com/feed/",             # Good quality
]

def clean_link(link):
    return link  # These feeds have cleaner links

def send_to_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}, timeout=10)
    except:
        pass

def main():
    sent_count = 0
    print(f"[{datetime.now()}] Starting simplified run...")

    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:30]:
                title = entry.get("title", "").strip()
                link = entry.get("link", "")
                summary = entry.get("summary", entry.get("description", ""))[:350]

                if not title or not link:
                    continue

                send_to_telegram(f"📰 **{title}**\n\n{summary}\n\n🔗 {clean_link(link)}")
                sent_count += 1
                time.sleep(2)
        except Exception as e:
            print(f"Error: {e}")

    # Guaranteed simple but useful summary
    time.sleep(6)
    final_msg = f"📊 **Robotics News Evening Edition** — {datetime.now().strftime('%B %d, %Y')}\n\n{sent_count} articles sent today from reputable robotics sources.\n\nFocus areas: Humanoids, drones, autonomous systems, and industry developments."
    send_to_telegram(final_msg)

    print(f"Finished. Sent {sent_count} articles.")

if __name__ == "__main__":
    main()
