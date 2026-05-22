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
    print("✅ Gemini client initialized")
else:
    print("⚠ No Gemini API key")

KEYWORDS = ["robot", "robots", "drone", "drones", "autonomous", 
            "robotics", "uav", "unmanned", "humanoid", "cobots"]

RSS_FEEDS = [
    "https://www.therobotreport.com/feed/",
    "https://roboticsandautomationnews.com/feed/",
    "https://news.google.com/rss/search?q=robotics+OR+robots+OR+drones+OR+autonomous+OR+UAV+OR+humanoid&hl=en-US&gl=US&ceid=US:en",
]

SEEN_FILE = "seen_articles.txt"
articles_today = []
MAX_ARTICLES_PER_RUN = 8   # Reduced to avoid huge gluts

def clean_google_news_link(link):
    if "news.google.com" in link:
        try:
            resp = requests.head(link, allow_redirects=True, timeout=8)
            clean_link = resp.url.split("?")[0]
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
        return "No articles to summarize today."
    
    article_details = [f"Title: {a['title']}\nSummary: {a.get('summary', '')[:250]}" for a in articles]
    
    prompt = f"""You are a robotics expert. Create one concise and engaging overall summary for all the articles below.

Articles:
{chr(10).join(article_details)}

Structure your response as:
- One strong opening highlight
- 4-7 key bullet points
- Keep it professional yet readable"""

    try:
        response = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
        return response.text
    except Exception as e:
        print(f"Gemini failed: {e}")
        return "Summary generation failed. Please check logs."

def main():
    global articles_today
    seen = load_seen_articles()
    new_count = 0
    print(f"[{datetime.now()}] Starting evening check...")

    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:25]:
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
                    time.sleep(1.8)

                    if new_count >= MAX_ARTICLES_PER_RUN:
                        break
        except Exception as e:
            print(f"Feed error: {e}")

    # === Overall Summary at the VERY END ===
    print(f"Collected {len(articles_today)} articles for summary.")
    time.sleep(5)   # Extra delay to ensure articles arrive first

    if client:
        summary_text = generate_daily_summary(articles_today)
        final_msg = f"📊 **Robotics News Evening Edition** — {datetime.now().strftime('%B %d, %Y')}\n\n{summary_text}\n\n📌 Total articles in this run: {len(articles_today)}"
        send_to_telegram(final_msg)
        print("✅ Overall summary sent at the end!")
    else:
        print("No Gemini available for summary.")

    print(f"[{datetime.now()}] Finished. Sent {new_count} articles.")

if __name__ == "__main__":
    main()
