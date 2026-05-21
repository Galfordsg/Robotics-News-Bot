import feedparser
import requests
import time
import os
from datetime import datetime
from google import genai # ← New recommended way

# === CONFIGURATION ===
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not TELEGRAM_TOKEN or not CHAT_ID:
    print("❌ Missing Telegram credentials!")
    exit(1)

# Gemini Setup (New SDK)
client = None
if GEMINI_API_KEY:
    client = genai.Client(api_key=GEMINI_API_KEY)
else:
    print("⚠ No Gemini API key → Daily summary will be skipped")

KEYWORDS = ["robot", "robots", "drone", "drones", "autonomous", 
            "robotics", "uav", "unmanned", "humanoid", "cobots"]

RSS_FEEDS = [
    "https://www.therobotreport.com/feed/",
    "https://roboticsandautomationnews.com/feed/",
    "https://news.google.com/rss/search?q=robotics+OR+robots+OR+drones+OR+autonomous+OR+UAV+OR+humanoid&hl=en-US&gl=US&ceid=US:en",
]

SEEN_FILE = "seen_articles.txt"
articles_today = []

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

def generate_daily_summary(articles):
    if not client or not articles:
        return None
    
    article_list = "\n".join([f"- {a['title']}" for a in articles])
    
    prompt = f"""You are a robotics expert. Create a clean, engaging daily summary of today's robotics news.

Articles:
{article_list}

Structure your summary nicely:
- One opening highlight sentence
- Bullet points of the most important news
- Keep it concise and readable for Telegram."""

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )
        return response.text
    except Exception as e:
        print(f"Gemini error: {e}")
        return None

def main():
    global articles_today
    seen = load_seen_articles()
    print(f"[{datetime.now()}] Starting robotics news check...")

    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries:
                title = entry.get("title", "")
                link = entry.get("link", "")
                summary_text = entry.get("summary", entry.get("description", ""))[:300]

                if link in seen or not link:
                    continue

                if any(kw in (title + summary_text).lower() for kw in KEYWORDS):
                    send_to_telegram(f"📰 **{title}**\n\n{summary_text}\n\n🔗 {link}")
                    save_seen_article(link)
                    articles_today.append({"title": title})
                    time.sleep(1.5)
        except Exception as e:
            print(f"Feed error: {e}")

    # Send Daily Summary
    if articles_today and client:
        print("🤖 Generating daily summary with Gemini...")
        summary = generate_daily_summary(articles_today)
        if summary:
            final_msg = f"📊 **Robotics News Daily Summary** — {datetime.now().strftime('%B %d, %Y')}\n\n{summary}\n\n📌 Total articles today: {len(articles_today)}"
            send_to_telegram(final_msg)
            print("✅ Daily summary sent!")

    print(f"[{datetime.now()}] Finished.")

if __name__ == "__main__":
    main()
