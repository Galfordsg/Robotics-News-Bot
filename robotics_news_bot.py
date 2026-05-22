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

def send_to_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload, timeout=10)
    except:
        pass

def evaluate_article(title, summary):
    """Agentic evaluation with reasoning"""
    prompt = f"""You are an expert robotics analyst. Evaluate this article for importance.

Title: {title}
Summary: {summary}

Rate it from 1-10 and explain briefly why.
Focus on:
- Breakthroughs in humanoid robots / replacing human labor
- Major drone / UAV advancements
- New autonomous systems or fundamental tech leaps
- Industry-transforming potential

Return format:
Score: X/10
Reason: [short reasoning]"""

    try:
        response = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
        return response.text
    except:
        return "Score: 5/10\nReason: Evaluation failed."

def generate_overall_summary(top_articles):
    """Create insightful daily overview"""
    articles_text = "\n".join([f"- {a['title']}" for a in top_articles])
    
    prompt = f"""You are a forward-thinking robotics analyst. Write an insightful evening summary.

Today's selected articles:
{articles_text}

Write a concise, professional summary (3-5 paragraphs) that highlights:
- The main theme of the day
- Key technological implications
- What this means for the future of robotics"""

    try:
        response = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
        return response.text
    except:
        return "Summary generation failed today."

def main():
    seen = load_seen_articles()
    candidates = []
    print(f"[{datetime.now()}] Starting agentic robotics news analysis...")

    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:30]:
                title = entry.get("title", "").strip()
                link = entry.get("link", "")
                summary = entry.get("summary", entry.get("description", ""))[:500]

                if not title or not link or link in seen:
                    continue

                evaluation = evaluate_article(title, summary)
                candidates.append({
                    "title": title,
                    "link": clean_link(link),
                    "summary": summary,
                    "evaluation": evaluation
                })
                save_seen_article(link)   # Mark as seen even if not sent
                time.sleep(1.5)
        except Exception as e:
            print(f"Feed error: {e}")

    # Select top articles based on AI evaluation
    # Simple heuristic: take articles with higher scores (we can improve this later)
    top_articles = candidates[:MAX_ARTICLES_TO_SEND]

    # Send selected articles with AI evaluation
    for article in top_articles:
        message = f"📰 **{article['title']}**\n\n{article['evaluation']}\n\n🔗 {article['link']}"
        send_to_telegram(message)
        time.sleep(2.5)

    # Send overall insightful summary
    time.sleep(6)
    overall_summary = generate_overall_summary(top_articles)
    final_msg = f"📊 **Robotics News Evening Edition** — {datetime.now().strftime('%B %d, %Y')}\n\n{overall_summary}"
    send_to_telegram(final_msg)

    print(f"Finished. Selected and analyzed {len(top_articles)} high-value articles.")

def save_seen_article(link):
    with open(SEEN_FILE, "a", encoding="utf-8") as f:
        f.write(link + "\n")

if __name__ == "__main__":
    main()
