import feedparser
import requests
import time
import os
from datetime import datetime
from google import genai

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not TELEGRAM_TOKEN or not CHAT_ID:
    print("❌ Missing credentials!")
    exit(1)

client = None
if GEMINI_API_KEY:
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
    except:
        pass

RSS_FEEDS = [
    "https://www.therobotreport.com/feed/",
    "https://roboticsandautomationnews.com/feed/",
]

def send_to_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}, timeout=10)
    except:
        pass

def generate_dynamic_summary(sent_titles):
    if not client or not sent_titles:
        return "No AI summary available today."
    
    articles = "\n".join([f"- {title}" for title in sent_titles])
    
    prompt = f"""You are a robotics analyst. Write a natural, insightful daily summary based on today's articles.

Articles:
{articles}

Write 2-4 paragraphs highlighting the main themes, notable developments, and implications."""

    try:
        response = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
        return response.text
    except:
        return "Summary generation encountered an issue today."

def main():
    sent_titles = []
    print(f"[{datetime.now()}] Starting run...")

    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:25]:
                title = entry.get("title", "").strip()
                link = entry.get("link", "")
                summary = entry.get("summary", entry.get("description", ""))[:380]

                if title and link:
                    send_to_telegram(f"📰 **{title}**\n\n{summary}\n\n🔗 {link}")
                    sent_titles.append(title)
                    time.sleep(2)
        except Exception as e:
            print(f"Error: {e}")

    # Dynamic AI Summary
    time.sleep(6)
    dynamic_summary = generate_dynamic_summary(sent_titles)
    
    final_msg = f"📊 **Robotics News Evening Edition** — {datetime.now().strftime('%B %d, %Y')}\n\n{dynamic_summary}"
    send_to_telegram(final_msg)

    print(f"Finished. Sent {len(sent_titles)} articles.")

if __name__ == "__main__":
    main()
