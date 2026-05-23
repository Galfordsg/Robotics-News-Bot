import feedparser
import requests
import time
import os
from datetime import datetime, timedelta
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
        print("✅ Gemini client initialized")
    except Exception as e:
        print(f"Gemini init failed: {e}")

RSS_FEEDS = [
    "https://www.therobotreport.com/feed/",
    "https://roboticsandautomationnews.com/feed/",
    "https://news.google.com/rss/search?q=robotics+OR+humanoid+OR+drone+OR+autonomous&hl=en-US&gl=US&ceid=US:en",
]

MAX_ARTICLES_TO_SEND = 6

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
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload, timeout=10)
    except:
        pass

def is_interesting(title, summary):
    text = (title + " " + summary).lower()
    return any(kw in text for kw in ["humanoid", "drone", "autonomous", "breakthrough", "unveils", "launches", "optimus", "atlas"])

def generate_dynamic_summary(sent_articles):
    if not client or not sent_articles:
        return "No AI summary available this run."
    
    articles_text = "\n".join([f"- {a['title']}" for a in sent_articles])
    
    prompt = f"""You are a robotics industry analyst. Write a coherent, insightful evening summary based on today's articles.

Articles sent today:
{articles_text}

Write in a natural, professional style (like your example). Highlight main themes, compare where relevant, and mention implications for the future of robotics."""

    try:
        response = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
        return response.text
    except Exception as e:
        print(f"Summary generation failed: {e}")
        return "Summary generation encountered an issue today."

def main():
    sent_articles = []
    sent_count = 0
    print(f"[{datetime.now()}] Starting run...")

    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:40]:
                title = entry.get("title", "").strip()
                link = entry.get("link", "")
                summary = entry.get("summary", entry.get("description", ""))[:400]

                if not title or not link:
                    continue

                if is_interesting(title, summary) and sent_count < MAX_ARTICLES_TO_SEND:
                    clean = clean_link(link)
                    send_to_telegram(f"📰 **{title}**\n\n{summary}\n\n🔗 {clean}")
                    
                    sent_articles.append({"title": title})
                    sent_count += 1
                    time.sleep(2)
        except Exception as e:
            print(f"Feed error: {e}")

    # === Dynamic AI Summary at the End ===
    time.sleep(6)
    dynamic_summary = generate_dynamic_summary(sent_articles)
    
    final_msg = f"📊 **Robotics News Evening Edition** — {datetime.now().strftime('%B %d, %Y')}\n\n{dynamic_summary}"
    send_to_telegram(final_msg)

    print(f"Finished. Sent {sent_count} articles + dynamic summary.")

if __name__ == "__main__":
    main()
