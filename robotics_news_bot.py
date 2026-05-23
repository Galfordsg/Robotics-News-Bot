import feedparser
import requests
import time
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
    try:
        requests.post(url, json={"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}, timeout=10)
    except:
        pass

def main():
    sent_count = 0
    cutoff = datetime.now() - timedelta(days=2)
    print(f"[{datetime.now()}] Starting improved run...")

    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:30]:
                title = entry.get("title", "").strip()
                link = entry.get("link", "")
                summary = entry.get("summary", entry.get("description", ""))[:350]

                if not title or not link:
                    continue

                # Stronger recency filter to reduce repeats
                if entry.get("published_parsed"):
                    try:
                        pub_date = datetime.fromtimestamp(time.mktime(entry.published_parsed))
                        if pub_date < cutoff:
                            continue
                    except:
                        pass

                # Send article without fake summary
                clean = clean_link(link)
                send_to_telegram(f"📰 **{title}**\n\n🔗 {clean}")
                sent_count += 1
                time.sleep(2)
        except Exception as e:
            print(f"Error: {e}")

    # Final dynamic-style summary (even if simple for now)
    time.sleep(6)
    final_msg = f"📊 **Robotics News Evening Edition** — {datetime.now().strftime('%B %d, %Y')}\n\n{sent_count} robotics articles sent today.\n\nCovered latest developments in humanoid robots, drones, autonomous systems and industry news."
    send_to_telegram(final_msg)

    print(f"Finished. Sent {sent_count} articles.")

if __name__ == "__main__":
    main()
