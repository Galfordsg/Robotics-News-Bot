import feedparser
import requests
import time
import os
from datetime import datetime

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

SEEN_FILE = "seen_articles.txt"
MAX_ARTICLES_TO_SEND = 5   # Keep it reasonable

def clean_link(link):
    if "news.google.com" in link:
        try:
            r = requests.head(link, allow_redirects=True, timeout=10)
            return r.url.split("?")[0]
        except:
            pass
    return link

def load_seen_articles():
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE, "r", encoding="utf-8") as f:
            return set(line.strip() for line in f if line.strip())
    return set()

def save_seen_article(link):
    try:
        with open(SEEN_FILE, "a", encoding="utf-8") as f:
            f.write(link + "\n")
        print(f"SAVED: {link[:70]}...")
    except:
        pass

def send_to_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload, timeout=10)
    except:
        pass

def is_high_value(title, summary):
    """Improved smart filtering"""
    text = (title + " " + summary).lower()
    
    high_value_keywords = [
        "humanoid", "figure ai", "tesla optimus", "atlas", "agility robotics",
        "replaces human", "labor", "workforce", "breakthrough", "unveils", 
        "launches", "new generation", "drone", "uav", "swarm", "autonomous",
        "milestone", "revolutionary", "first ever", "advances"
    ]
    
    medium_value = ["new robot", "partnership", "acquire", "investment"]
    
    # Strong matches
    if any(kw in text for kw in high_value_keywords):
        return True
    # Medium matches (only if not too generic)
    if any(kw in text for kw in medium_value) and len(text) > 100:
        return True
    
    return False

def main():
    seen = load_seen_articles()
    sent_count = 0
    print(f"[{datetime.now()}] Starting improved filtering...")

    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:40]:
                title = entry.get("title", "").strip()
                link = entry.get("link", "")
                summary = entry.get("summary", entry.get("description", ""))[:400]

                if not title or not link or link in seen:
                    continue

                if is_high_value(title, summary):
                    clean = clean_link(link)
                    send_to_telegram(f"📰 **{title}**\n\n{summary}\n\n🔗 {clean}")
                    save_seen_article(link)
                    seen.add(link)
                    sent_count += 1
                    time.sleep(2)

                    if sent_count >= MAX_ARTICLES_TO_SEND:
                        break
        except Exception as e:
            print(f"Feed error: {e}")

    # Evening Summary
    time.sleep(5)
    final_msg = f"📊 **Robotics News Evening Edition** — {datetime.now().strftime('%B %d, %Y')}\n\nSent {sent_count} high-value articles today.\n\nFocused on breakthroughs in humanoid robots, drones, and major autonomous tech."
    send_to_telegram(final_msg)

    print(f"Finished run. Sent {sent_count} articles.")

if __name__ == "__main__":
    main()
