from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor
import calendar
import time
import os
import re
import html
import requests
import feedparser

# Load the secret values from the .env file
load_dotenv()
API_KEY = os.getenv("NEWS_API_KEY")

# NewsAPI address, used for countries other than the Philippines
HEADLINES_URL = "https://newsapi.org/v2/top-headlines"

# Some sites block scripts, so we introduce ourselves like a normal browser
BROWSER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
)

# Philippine RSS feeds. Each category has a list of (source name, feed address).
PH_FEEDS = {
    "general": [
        ("Rappler", "https://www.rappler.com/feed/"),
        ("PhilStar", "https://www.philstar.com/rss/headlines"),
        ("Inquirer", "https://newsinfo.inquirer.net/feed"),
        ("Manila Times", "https://www.manilatimes.net/news/feed"),
        # Optional: mostly Filipino-language. Remove the # to turn it on.
        # ("GMA News", "https://data.gmanetwork.com/gno/rss/news/feed.xml"),
    ],
    "business": [
        ("PhilStar", "https://www.philstar.com/rss/business"),
        ("BusinessWorld", "https://www.bworldonline.com/feed/"),
        ("Rappler", "https://www.rappler.com/business/feed/"),
    ],
    "technology": [
        ("Rappler", "https://www.rappler.com/technology/feed/"),
        ("Interaksyon", "https://interaksyon.philstar.com/feed"),
    ],
    "sports": [
        ("PhilStar", "https://www.philstar.com/rss/sports"),
        ("Rappler", "https://www.rappler.com/sports/feed/"),
    ],
    "science": [
        ("Rappler", "https://www.rappler.com/environment/feed/"),
    ],
    "health": [
        ("Rappler", "https://www.rappler.com/health/feed/"),
    ],
    "entertainment": [
        ("PhilStar", "https://www.philstar.com/rss/entertainment"),
        ("Rappler", "https://www.rappler.com/entertainment/feed/"),
    ],
}

# A small memory so we don't re-download feeds on every click
CACHE = {}
CACHE_SECONDS = 300  # 5 minutes

# Create the Flask app
app = Flask(__name__)

# Allow our frontend page to talk to this backend
CORS(app)


def clean_text(text):
    """Remove HTML tags and shorten long descriptions."""
    text = re.sub(r"<[^>]+>", "", text or "")
    text = html.unescape(text).strip()
    if len(text) > 200:
        text = text[:200].rstrip() + "..."
    return text


def find_image(entry):
    """Look for an image in the different places a feed might hide it."""
    if entry.get("media_content"):
        return entry["media_content"][0].get("url")
    if entry.get("media_thumbnail"):
        return entry["media_thumbnail"][0].get("url")
    for enc in entry.get("enclosures", []):
        if enc.get("type", "").startswith("image"):
            return enc.get("href")
    for link in entry.get("links", []):
        if link.get("type", "").startswith("image"):
            return link.get("href")
    # Last try: an <img> tag inside the article text
    text = entry.get("summary", "") + str(entry.get("content", ""))
    match = re.search(r'<img[^>]+src="([^"]+)"', text)
    if match:
        return match.group(1)
    return None


def read_feed(source_and_url):
    """Read ONE feed and return its articles. Never crashes the whole page."""
    name, url = source_and_url
    try:
        feed = feedparser.parse(url, agent=BROWSER_AGENT)
    except Exception as e:
        print(f"RSS {name}: FAILED ({e})")
        return []

    print(f"RSS {name}: status={feed.get('status')}, entries={len(feed.entries)}")

    articles = []
    for entry in feed.entries[:15]:
        published = entry.get("published_parsed")
        articles.append({
            "title": entry.get("title"),
            "source": name,
            "url": entry.get("link"),
            "image": find_image(entry),
            "description": clean_text(entry.get("summary")),
            "publishedAt": entry.get("published"),
            "timestamp": calendar.timegm(published) if published else 0,
        })
    return articles


def get_ph_news(category):
    """Read all feeds for a category, merge them, newest first."""
    feeds = PH_FEEDS.get(category, PH_FEEDS["general"])

    # Use the saved copy if it is still fresh
    saved = CACHE.get(category)
    if saved and time.time() - saved["time"] < CACHE_SECONDS:
        return saved["articles"]

    # Read all the feeds at the same time (faster than one by one)
    with ThreadPoolExecutor(max_workers=len(feeds)) as pool:
        results = list(pool.map(read_feed, feeds))

    # Merge, skipping duplicate links
    merged = []
    seen = set()
    for batch in results:
        for article in batch:
            if article["url"] in seen:
                continue
            seen.add(article["url"])
            merged.append(article)

    # Newest first, keep the top 24
    merged.sort(key=lambda a: a["timestamp"], reverse=True)
    merged = merged[:24]
    for article in merged:
        del article["timestamp"]

    # Only remember results that actually contain articles
    if merged:
        CACHE[category] = {"time": time.time(), "articles": merged}
    return merged


@app.route("/")
def home():
    return "Hello! The news backend is running."


@app.route("/api/test")
def test():
    return jsonify({"status": "ok", "message": "Backend is working!"})


@app.route("/api/news")
def get_news():
    category = request.args.get("category", "general")

    # Only allow countries we have chosen
    allowed_countries = ["us", "ph", "gb", "au", "sg"]
    country = request.args.get("country", "ph")
    if country not in allowed_countries:
        country = "ph"

    # Philippines: read from the RSS feeds
    if country == "ph":
        return jsonify({"articles": get_ph_news(category)})

    # Other countries: ask NewsAPI
    params = {
        "country": country,
        "category": category,
        "pageSize": 20,
        "apiKey": API_KEY,
    }

    try:
        response = requests.get(HEADLINES_URL, params=params, timeout=20)
        data = response.json()
    except requests.exceptions.RequestException as e:
        print("NewsAPI request failed:", e)
        return jsonify({"error": "Could not reach the news service."}), 502

    if data.get("status") != "ok":
        return jsonify({"error": data.get("message", "Unknown error")}), 400

    articles = []
    for item in data.get("articles", []):
        if item.get("title") == "[Removed]":
            continue
        articles.append({
            "title": item.get("title"),
            "source": item.get("source", {}).get("name"),
            "url": item.get("url"),
            "image": item.get("urlToImage"),
            "description": item.get("description"),
            "publishedAt": item.get("publishedAt"),
        })

    return jsonify({"articles": articles})


if __name__ == "__main__":
    app.run(debug=True)