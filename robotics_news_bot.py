import feedparser
import requests
import time
import os
from datetime import datetime, timedelta

# === CONFIGURATION ===
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

if not TELEGRAM_TOKEN or not CHAT_ID:
    print("❌ Missing credentials!")
    exit(1)

RSS_FEEDS = [
    "https://www.therobotreport.com/feed/",
    "https://roboticsandautomationnews.com/feed/",
    "https://news.google.com/rss/search?q=robotics+OR+humanoid+OR+drone+OR+autonomous&hl=en-US&gl=US&ceid=US:en",
]

MAX_ARTICLES_TO_SEND = 5

def clean_link(link):
    if "news.google.com" in link:
        try:
            r = requests.head(link, allow_redirects=True, timeout=10)
            return r.url.split("?")[0]
        except:
            pass
    return link

def send_to_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload, timeout=10)
    except:
        pass

def is_high_value(title, summary):
    text = (title + " " + summary).lower()
    strong_keywords = ["humanoid", "optimus", "figure ai", "atlas", "drone", "uav", "breakthrough", 
                       "unveils", "launches", "replaces human", "labor", "autonomous system"]
    return any(kw in text for kw in strong_keywords)

def main():
    sent_count = 0
    cutoff_date = datetime.now() - timedelta(days=2)   # Only articles from last 2 days
    print(f"[{datetime.now()}] Starting recency-based check...")

    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:40]:
                title = entry.get("title", "").strip()
                link = entry.get("link", "")
                summary = entry.get("summary", entry.get("description", ""))[:350]
                published = entry.get("published_parsed") or entry.get("updated_parsed")

                if not title or not link:
                    continue

                # Date filter
                if published:
                    try:
                        pub_date = datetime.fromtimestamp(time.mktime(published))
                        if pub_date < cutoff_date:
                            continue
                    except:
                        pass

                if is_high_value(title, summary):
                    clean = clean_link(link)
                    send_to_telegram(f"📰 **{title}**\n\n{summary}\n\n🔗 {clean}")
                    sent_count += 1
                    time.sleep(2)

                    if sent_count >= MAX_ARTICLES_TO_SEND:
                        break
        except Exception as e:
            print(f"Feed error: {e}")

    # Final Summary
    time.sleep(5)
    final_msg = f"📊 **Robotics News Evening Edition** — {datetime.now().strftime('%B %d, %Y')}\n\nSent {sent_count} high-value articles today.\n\nFocused on major breakthroughs in humanoid, drone, and autonomous technology."
    send_to_telegram(final_msg)

    print(f"Finished. Sent {sent_count} articles.")

if __name__ == "__main__":
    main()
