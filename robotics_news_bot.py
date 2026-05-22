import feedparser
import requests
import time
import os
from datetime import datetime

# CONFIG
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

RSS_FEEDS = [
    "https://www.therobotreport.com/feed/",
    "https://roboticsandautomationnews.com/feed/",
]

SEEN_FILE = "seen_articles.txt"
MAX_ARTICLES = 5

def main():
    print(f"[{datetime.now()}] Script started. Working directory: {os.getcwd()}")
    
    # Force create seen file
    if not os.path.exists(SEEN_FILE):
        with open(SEEN_FILE, "w", encoding="utf-8") as f:
            f.write("# Seen articles\n")
        print("Created new seen_articles.txt file")

    seen = set()
    try:
        with open(SEEN_FILE, "r", encoding="utf-8") as f:
            seen = set(line.strip() for line in f if line.strip() and not line.startswith("#"))
        print(f"Loaded {len(seen)} previously seen articles")
    except Exception as e:
        print(f"Error loading seen file: {e}")

    sent = 0

    for feed_url in RSS_FEEDS:
        try:
            print(f"Fetching: {feed_url}")
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:20]:
                title = entry.get("title", "").strip()
                link = entry.get("link", "")
                if not title or not link or link in seen:
                    continue

                summary = entry.get("summary", entry.get("description", ""))[:300]
                clean_link = link

                send_to_telegram(f"📰 **{title}**\n\n{summary}\n\n🔗 {clean_link}")
                save_seen_article(link)
                seen.add(link)
                sent += 1
                time.sleep(2)

                if sent >= MAX_ARTICLES:
                    break
        except Exception as e:
            print(f"Error processing feed: {e}")

    # Final message
    time.sleep(4)
    send_to_telegram(f"📊 **Robotics News Evening Edition** — {datetime.now().strftime('%B %d, %Y')}\n\nSent {sent} articles this run.")

    print(f"Finished. Total sent this run: {sent}")

def send_to_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload, timeout=10)
    except:
        pass

def save_seen_article(link):
    try:
        with open(SEEN_FILE, "a", encoding="utf-8") as f:
            f.write(link + "\n")
        print(f"SAVED TO SEEN: {link[:80]}...")
    except Exception as e:
        print(f"FAILED to save: {e}")

if __name__ == "__main__":
    main()
