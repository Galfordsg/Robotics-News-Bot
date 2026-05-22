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
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        print("✅ Gemini client connected")
    except Exception as e:
        print(f"Gemini init failed: {e}")

RSS_FEEDS = [
    "https://www.therobotreport.com/feed/",
    "https://roboticsandautomationnews.com/feed/",
    "https://news.google.com/rss/search?q=robotics+OR+humanoid+OR+drone+OR+autonomous&hl=en-US&gl=US&ceid=US:en",
]

SEEN_FILE = "seen_articles.txt"
MAX_ARTICLES_TO_SEND = 5

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

def evaluate_article(title, summary):
    if not client:
        return "**Score: 6/10**\nAI evaluation unavailable."

    prompt = f"""Rate this article's importance (1-10) for robotics enthusiasts interested in breakthroughs.

Title: {title}
Summary: {summary}

Focus on humanoid robots, labor replacement, drone tech, and major innovations.

Reply exactly in this format:
Score: X/10
Reason: One short sentence."""

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash", 
            contents=prompt,
            generation_config={"temperature": 0.3}
        )
        return response.text.strip()
    except Exception as e:
        print(f"Evaluation failed: {e}")
        return "**Score: 5/10**\nEvaluation temporarily unavailable."

def main():
    seen = load_seen_articles()
    candidates = []
    print(f"[{datetime.now()}] Starting analysis...")

    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:30]:
                title = entry.get("title", "").strip()
                link = entry.get("link", "")
                summary = entry.get("summary", entry.get("description", ""))[:400]

                if not title or not link or link in seen:
                    continue

                evaluation = evaluate_article(title, summary)
                candidates.append({
                    "title": title,
                    "link": clean_link(link),
                    "evaluation": evaluation
                })
                save_seen_article(link)
                time.sleep(1.5)
        except Exception as e:
            print(f"Feed error: {e}")

    # Send top articles
    top_articles = candidates[:MAX_ARTICLES_TO_SEND]
    for article in top_articles:
        msg = f"📰 **{article['title']}**\n\n{article['evaluation']}\n\n🔗 {article['link']}"
        send_to_telegram(msg)
        time.sleep(2)

    # Simple summary
    time.sleep(5)
    count = len(top_articles)
    final_msg = f"📊 **Robotics News Evening Edition** — {datetime.now().strftime('%B %d, %Y')}\n\nProcessed {count} articles today.\n\nAI analysis is being tuned."
    send_to_telegram(final_msg)

    print(f"Finished. Sent {count} articles.")

if __name__ == "__main__":
    main()
