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
        print("✅ Gemini initialized")
    except:
        print("⚠ Gemini not available")

RSS_FEEDS = [
    "https://www.therobotreport.com/feed/",
    "https://roboticsandautomationnews.com/feed/",
    "https://news.google.com/rss/search?q=robotics+OR+humanoid+OR+drone+OR+autonomous&hl=en-US&gl=US&ceid=US:en",
]

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

def generate_dynamic_summary(sent_articles):
    if not client or not sent_articles:
        return "No AI summary available today."
    
    articles_list = "\n".join([f"- {a}" for a in sent_articles])
    
    prompt = f"""You are a robotics industry analyst. Write a natural, insightful daily evening summary based on today's articles.

Articles sent today:
{articles_list}

Write 3-5 paragraphs that:
- Highlight the main themes of the day
- Point out any interesting developments or connections
- Give context on what this means for the robotics field"""

    try:
        response = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
        return response.text
    except Exception as e:
        print(f"Summary failed: {e}")
        return "Summary generation encountered an issue today."

def main():
    sent_articles = []
    cutoff = datetime.now() - timedelta(days=2)
    print(f"[{datetime.now()}] Starting run...")

    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:50]:   # Increased to allow more articles
                title = entry.get("title", "").strip()
                link = entry.get("link", "")
                summary = entry.get("summary", entry.get("description", ""))[:400]

                if not title or not link:
                    continue

                # Recency filter to reduce repeats
                if entry.get("published_parsed"):
                    try:
                        pub_date = datetime.fromtimestamp(time.mktime(entry.published_parsed))
                        if pub_date < cutoff:
                            continue
                    except:
                        pass

                # Send most robotics-related articles
                if any(kw in (title + summary).lower() for kw in ["robot", "drone", "humanoid", "autonomous", "uav"]):
                    clean = clean_link(link)
                    send_to_telegram(f"📰 **{title}**\n\n{summary}\n\n🔗 {clean}")
                    sent_articles.append(title)
                    time.sleep(2)
        except Exception as e:
            print(f"Feed error: {e}")

    # Dynamic AI Summary at the end
    time.sleep(6)
    dynamic_summary = generate_dynamic_summary(sent_articles)
    
    final_msg = f"📊 **Robotics News Evening Edition** — {datetime.now().strftime('%B %d, %Y')}\n\n{dynamic_summary}"
    send_to_telegram(final_msg)

    print(f"Finished. Sent {len(sent_articles)} articles + dynamic summary.")

if __name__ == "__main__":
    main()
