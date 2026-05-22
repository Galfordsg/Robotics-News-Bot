import feedparser
import requests
import time
import os
from datetime import datetime

# === CONFIGURATION ===
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not TELEGRAM_TOKEN or not CHAT_ID:
    print("❌ Missing Telegram credentials!")
    exit(1)

# Gemini (optional)
try:
    from google import genai
    client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None
    print("✅ Gemini initialized" if client else "⚠ Gemini not configured")
except ImportError:
    client = None
    print("⚠ google-genai library not available - summaries disabled")

KEYWORDS = ["robot", "robots", "drone", "drones", "autonomous", "robotics", "uav", "unmanned", "humanoid"]

RSS_FEEDS = [
    "https://www.therobotreport.com/feed/",
    "https://roboticsandautomationnews.com/feed/",
    "https://news.google.com/rss/search?q=robotics+OR+robots+OR+drones+OR+autonomous+OR+UAV+OR+humanoid&hl=en-US&gl=US&ceid=US:en",
]

SEEN_FILE = "seen_articles.txt"
articles_today = []
MAX_ARTICLES_PER_RUN = 7

def clean_google_news_link(link):
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
            return set(line.strip() for line in f)
    return set()

def save_seen_article(link):
    with open(SEEN_FILE, "a", encoding="utf-8") as f:
        f.write(link + "\n")

def send_to_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload, timeout=10)
    except:
        pass

def main():
    global articles_today
    seen = load_seen_articles()
    new_count = 0
    print(f"[{datetime.now()}] Starting robotics news check...")

    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:20]:
                title = entry.get("title", "").strip()
                link = entry.get("link", "")
                summary = entry.get("summary", entry.get("description", ""))[:300]

                if not title or not link or link in seen:
                    continue

                if any(kw in (title + " " + summary).lower() for kw in KEYWORDS):
                    clean_link = clean_google_news_link(link)
                    send_to_telegram(f"📰 **{title}**\n\n{summary}\n\n🔗 {clean_link}")

                    articles_today.append({"title": title})
                    save_seen_article(link)
                    new_count += 1
                    time.sleep(1.5)

                    if new_count >= MAX_ARTICLES_PER_RUN:
                        break
        except Exception as e:
            print(f"Feed error: {e}")

# Summary at the end
    time.sleep(5)
    if articles_today:
        summary_msg = f"📊 **Robotics News Evening Edition** — {datetime.now().strftime('%B %d, %Y')}\n\nTotal articles today: {len(articles_today)}\n\n(Full AI summary coming soon)"
    else:
        summary_msg = f"📊 **Robotics News Evening Edition** — {datetime.now().strftime('%B %d, %Y')}\n\nNo new articles found today."
    
    send_to_telegram(summary_msg)
    print(f"✅ Summary sent. Processed {new_count} articles.")

if __name__ == "__main__":
    main()
