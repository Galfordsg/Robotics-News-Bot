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
    print("✅ Gemini ready for smart filtering")
else:
    print("⚠ No Gemini key - falling back to basic mode")

KEYWORDS = ["robot", "robots", "drone", "drones", "autonomous", "robotics", "uav", "humanoid", "cobots"]

RSS_FEEDS = [
    "https://www.therobotreport.com/feed/",
    "https://roboticsandautomationnews.com/feed/",
    "https://news.google.com/rss/search?q=robotics+OR+robots+OR+drones+OR+autonomous+OR+UAV+OR+humanoid&hl=en-US&gl=US&ceid=US:en",
]

SEEN_FILE = "seen_articles.txt"
MAX_ARTICLES_TO_SEND = 5   # Only send the best ones

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

def analyze_article(title, summary):
    """Use Gemini to score how important/innovative the article is"""
    if not client:
        return 5  # Default score if no AI
    
    prompt = f"""Rate this robotics article from 1 to 10 based on how groundbreaking or important it is.

Title: {title}
Summary: {summary}

Focus especially on:
- Humanoids / replacing human labor
- Major drone / UAV breakthroughs
- New autonomous systems
- Fundamental technology leaps
- Industry-changing news

Return only a number (1-10) and nothing else."""

    try:
        response = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
        score = int(''.join(filter(str.isdigit, response.text or "5"))) 
        return min(max(score, 1), 10)
    except:
        return 5

def main():
    seen = load_seen_articles()
    candidates = []
    print(f"[{datetime.now()}] Starting smart robotics news check...")

    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:30]:
                title = entry.get("title", "").strip()
                link = entry.get("link", "")
                summary = entry.get("summary", entry.get("description", ""))[:400]

                if not title or not link or link in seen:
                    continue

                if any(kw in (title + summary).lower() for kw in KEYWORDS):
                    score = analyze_article(title, summary)
                    candidates.append({
                        "title": title,
                        "link": clean_link(link),
                        "summary": summary,
                        "score": score
                    })
                    save_seen_article(link)
                    time.sleep(1.2)
        except Exception as e:
            print(f"Feed error: {e}")

    # Sort by importance and take top ones
    candidates.sort(key=lambda x: x["score"], reverse=True)
    top_articles = candidates[:MAX_ARTICLES_TO_SEND]

    # Send only the best articles
    for article in top_articles:
        send_to_telegram(f"📰 **{article['title']}** (Score: {article['score']}/10)\n\n{article['summary'][:300]}...\n\n🔗 {article['link']}")
        time.sleep(2)

    # Final Summary
    time.sleep(5)
    if top_articles:
        summary_text = "Today's top robotics developments focused on high-impact innovations."
        final_msg = f"📊 **Robotics News Evening Edition** — {datetime.now().strftime('%B %d, %Y')}\n\n{summary_text}\n\nFeatured {len(top_articles)} most important articles."
        send_to_telegram(final_msg)
    else:
        send_to_telegram(f"📊 **Robotics News Evening Edition** — {datetime.now().strftime('%B %d, %Y')}\n\nNo major groundbreaking articles found today.")

    print(f"Finished. Selected {len(top_articles)} high-quality articles out of {len(candidates)} candidates.")

if __name__ == "__main__":
    main()
