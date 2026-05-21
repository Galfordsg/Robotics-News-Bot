import feedparser
import requests
import time
import os
from datetime import datetime
from google import genai

# === CONFIGURATION ===
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not TELEGRAM_TOKEN or not CHAT_ID:
    print("❌ Missing Telegram credentials!")
    exit(1)

client = None
if GEMINI_API_KEY:
    client = genai.Client(api_key=GEMINI_API_KEY)

KEYWORDS = ["robot", "robots", "drone", "drones", "autonomous", 
            "robotics", "uav", "unmanned", "humanoid", "cobots"]

RSS_FEEDS = [
    "https://www.therobotreport.com/feed/",
    "https://roboticsandautomationnews.com/feed/",
    "https://news.google.com/rss/search?q=robotics+OR+robots+OR+drones+OR+autonomous+OR+UAV+OR+humanoid&hl=en-US&gl=US&ceid=US:en",
]

SEEN_FILE = "seen_articles.txt"
articles_today = []
MAX_ARTICLES_PER_RUN = 10

def clean_google_news_link(link):
    if "news.google.com" in link:
        try:
            resp = requests.head(link, allow_redirects=True, timeout=8)
            clean_link = resp.url
            if "?" in clean_link:
                clean_link = clean_link.split("?")[0]
            return clean_link
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

def generate_daily_summary(articles):
    if not client or not articles:
        return None
    
    article_details = [f"Title: {a['title']}\nSummary: {a.get('summary', '')[:300]}" for a in articles]
    
    prompt = f"""You are a robotics expert. Create an engaging evening summary of today's robotics news.

Articles:
{chr(10).join(article_details)}

Structure:
- Start with one strong highlight sentence
- Use bullet points for key developments
- Group similar topics if possible"""

    try:
        response = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
        return response.text
    except Exception as e:
        print(f"Gemini error: {e}")
        return None

def main():
    global articles_today
    seen = load_seen_articles()
    new_count = 0
    print(f"[{datetime.now()}] Starting check...")

    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:20]:
                title = entry.get("title", "").strip()
                link = entry.get("link", "")
                summary = entry.get("summary", entry.get("description", ""))[:350]

                if not title or not link or link in seen:
                    continue

                if any(kw in (title + summary).lower() for kw in KEYWORDS):
                    clean_link = clean_google_news_link(link)
                    
                    send_to_telegram(f"📰 **{title}**\n\n{summary}\n\n🔗 {clean_link}")
                    
                    articles_today.append({"title": title, "summary": summary})
                    save_seen_article(link)
                    new_count += 1
                    time.sleep(1.5)

                    if new_count >= MAX_ARTICLES_PER_RUN:
                        break
        except Exception as e:
            print(f"Feed error: {e}")

    # === Summary at the very end ===
    if articles_today and client:
        print("Generating overall summary...")
        time.sleep(4)                    # ← Extra delay so summary comes last
        summary_text = generate_daily_summary(articles_today)
        if summary_text:
            final_msg = f"📊 **Robotics News Evening Edition** — {datetime.now().strftime('%B %d, %Y')}\n\n{summary_text}\n\n📌 Total articles in this batch: {len(articles_today)}"
            send_to_telegram(final_msg)
            print("✅ Evening summary sent at the end!")

    print(f"Finished. Processed {new_count} articles.")

if __name__ == "__main__":
    main()
