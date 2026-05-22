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

# Gemini Setup
try:
    from google import genai
    client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None
    print("✅ Gemini ready" if client else "⚠ Gemini disabled")
except:
    client = None
    print("⚠ Could not import google-genai")

KEYWORDS = ["robot", "robots", "drone", "drones", "autonomous", "robotics", "uav", "unmanned", "humanoid"]

RSS_FEEDS = [
    "https://www.therobotreport.com/feed/",
    "https://roboticsandautomationnews.com/feed/",
    "https://news.google.com/rss/search?q=robotics+OR+robots+OR+drones+OR+autonomous+OR+UAV+OR+humanoid&hl=en-US&gl=US&ceid=US:en",
]

SEEN_FILE = "seen_articles.txt"
articles_today = []
MAX_ARTICLES_PER_RUN = 7

def clean_link(link):
    if "news.google.com" in link:
        try:
            r = requests.head(link, allow_redirects=True, timeout=10)
            clean = r.url.split("?")[0]
            return clean
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

def generate_summary(articles):
    if not client or not articles:
        return "No AI summary available this run."
    
    article_list = "\n".join([f"- {a}" for a in articles])
    prompt = f"""Summarize these robotics news articles in a clear, engaging way:

{article_list}

Structure:
- One opening highlight
- Bullet points of key news"""

    try:
        response = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
        return response.text
    except Exception as e:
        print(f"Gemini error: {e}")
        return "Summary generation failed."

def main():
    global articles_today
    seen = load_seen_articles()
    new_count = 0
    print(f"[{datetime.now()}] Starting check...")

    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:25]:
                title = entry.get("title", "").strip()
                link = entry.get("link", "")
                summary = entry.get("summary", entry.get("description", ""))[:320]

                if not title or not link or link in seen:
                    continue

                if any(kw in (title + summary).lower() for kw in KEYWORDS):
                    clean_link = clean_link(link)
                    
                    send_to_telegram(f"📰 **{title}**\n\n{summary}\n\n🔗 {clean_link}")

                    articles_today.append(title)
                    save_seen_article(link)
                    new_count += 1
                    time.sleep(1.6)

                    if new_count >= MAX_ARTICLES_PER_RUN:
                        break
        except Exception as e:
            print(f"Error: {e}")

    # Summary at the end
    time.sleep(6)
    summary_text = generate_summary(articles_today)
    final_msg = f"📊 **Robotics News Evening Edition** — {datetime.now().strftime('%B %d, %Y')}\n\n{summary_text}\n\n📌 Total articles: {len(articles_today)}"
    send_to_telegram(final_msg)

    print(f"Finished. Sent {new_count} articles.")

if __name__ == "__main__":
    main()
