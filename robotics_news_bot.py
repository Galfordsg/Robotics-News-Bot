import feedparser
import requests
import time
import os
from datetime import datetime

# === CONFIGURATION ===
TELEGRAM_TOKEN = "8677362823:AAEbBojzYBCcDOSV4FSI0B4b86Gk14DFqB8"
CHAT_ID = "809404258"

# Keywords (you can add/remove)
KEYWORDS = ["robot", "robots", "ugv", "drones", "autonomous", 
            "robotics", "uav", "unmanned", "humanoid", "cobots"]

# RSS Feeds - Now includes Google News search
RSS_FEEDS = [
    "https://www.therobotreport.com/feed/",
    "https://roboticsandautomationnews.com/feed/",
    # Add more specific feeds here if you want
    
    # === Google News Search (Highly Recommended) ===
    "https://news.google.com/rss/search?q=robotics+OR+robots+OR+drones+OR+autonomous+OR+UGV+OR+UAV+OR+humanoid&hl=en-US&gl=US&ceid=US:en",
    
    # You can add more Google News searches if needed, for example:
    # "https://news.google.com/rss/search?q=autonomous+vehicles+OR+self-driving&hl=en-US&gl=US&ceid=US:en",
]

SEEN_FILE = "seen_articles.txt"

def load_seen_articles():
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE, "r", encoding="utf-8") as f:
            return set(line.strip() for line in f)
    return set()

def save_seen_article(link):
    with open(SEEN_FILE, "a", encoding="utf-8") as f:
        f.write(link + "\n")

def send_to_telegram(title, link, summary=""):
    # Clean up summary for Telegram
    if summary:
        summary = summary[:400] + "..." if len(summary) > 400 else summary
    message = f"📰 **{title}**\n\n{summary}\n\n🔗 {link}"
    
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            print(f"✅ Sent: {title[:60]}...")
        else:
            print(f"❌ Failed ({response.status_code}): {response.text[:200]}")
    except Exception as e:
        print(f"Error sending to Telegram: {e}")

def main():
    seen = load_seen_articles()
    print(f"[{datetime.now()}] Checking {len(RSS_FEEDS)} feeds...")

    for feed_url in RSS_FEEDS:
        try:
            print(f" → Fetching: {feed_url[:70]}...")
            feed = feedparser.parse(feed_url)
            
            if not feed.entries:
                print(f" ⚠ No entries found in {feed_url}")
                continue
                
            for entry in feed.entries:
                title = entry.get("title", "")
                link = entry.get("link", "")
                summary = entry.get("summary", entry.get("description", ""))[:350]
                
                # Skip if already sent
                if link in seen or not link:
                    continue
                
                # Keyword check (case-insensitive)
                text_to_check = (title + " " + summary).lower()
                if any(kw.lower() in text_to_check for kw in KEYWORDS):
                    send_to_telegram(title, link, summary)
                    save_seen_article(link)
                    time.sleep(1.5) # Be gentle with APIs
                    
        except Exception as e:
            print(f"❌ Error processing {feed_url}: {e}")

    print(f"[{datetime.now()}] Check completed.\n")

if __name__ == "__main__":
    main()