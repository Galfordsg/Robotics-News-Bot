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

if not TELEGRAM_TOKEN or not CHAT_ID or not GEMINI_API_KEY:
    print("❌ Missing credentials!")
    exit(1)

client = genai.Client(api_key=GEMINI_API_KEY)

RSS_FEEDS = [
    "https://www.therobotreport.com/feed/",
    "https://roboticsandautomationnews.com/feed/",
    "https://news.google.com/rss/search?q=robotics+OR+humanoid+OR+drone+OR+autonomous&hl=en-US&gl=US&ceid=US:en",
]

SEEN_FILE = "seen_articles.txt"
MAX_ARTICLES_TO_SEND = 6

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
    prompt = f"""Rate this robotics article's importance (1-10) for people interested in technological breakthroughs.

Title: {title}
Summary: {summary}

Especially value:
- Humanoid robots replacing/supplementing human labor
- Major drone or autonomous tech advances
- Fundamental new capabilities or industry shifts

Reply in this exact format:
Score: X/10
Reason: Short 1-sentence explanation"""

    try:
        response = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
        text = response.text.strip()
        # More robust parsing
        score_line = [line for line in text.split('\n') if "Score:" in line]
        reason_line = [line for line in text.split('\n') if "Reason:" in line]
        
        score = 5
        if score_line:
            try:
                score = int(''.join(filter(str.isdigit, score_line[0])))
            except:
                pass
                
        reason = reason_line[0] if reason_line else text[:200]
        return f"**Score: {min(max(score, 1), 10)}/10**\n{reason}"
        
    except Exception as e:
        print(f"Evaluation error: {e}")
        return "**Score: 5/10**\nEvaluation temporarily unavailable."

def generate_overall_summary(top_articles):
    if not top_articles:
        return "No major articles today."
    
    articles_list = "\n".join([f"- {a['title']}" for a in top_articles])
    prompt = f"""Write a concise, insightful evening summary on today's robotics developments.

Articles:
{articles_list}

Highlight the main trends and implications for the future."""

    try:
        response = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
        return response.text
    except:
        return "Summary generation encountered an issue today."

def main():
    seen = load_seen_articles()
    candidates = []
    print(f"[{datetime.now()}] Starting advanced analysis...")

    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:35]:
                title = entry.get("title", "").strip()
                link = entry.get("link", "")
                summary = entry.get("summary", entry.get("description", ""))[:450]

                if not title or not link or link in seen:
                    continue

                evaluation = evaluate_article(title, summary)
                candidates.append({
                    "title": title,
                    "link": clean_link(link),
                    "evaluation": evaluation
                })
                save_seen_article(link)
                time.sleep(1.3)
        except Exception as e:
            print(f"Feed error: {e}")

    # Take top articles
    top_articles = candidates[:MAX_ARTICLES_TO_SEND]

    # Send articles
    for article in top_articles:
        msg = f"📰 **{article['title']}**\n\n{article['evaluation']}\n\n🔗 {article['link']}"
        send_to_telegram(msg)
        time.sleep(2.5)

    # Overall Summary
    time.sleep(6)
    overall = generate_overall_summary(top_articles)
    final_msg = f"📊 **Robotics News Evening Edition** — {datetime.now().strftime('%B %d, %Y')}\n\n{overall}"
    send_to_telegram(final_msg)

    print(f"Completed. Sent {len(top_articles)} selected articles.")

if __name__ == "__main__":
    main()
