import feedparser

# Some sites block scripts, so we introduce ourselves like a normal browser
BROWSER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
)

# Candidate feeds: (name, address)
CANDIDATES = [
    ("Rappler", "https://www.rappler.com/feed/"),
    ("PhilStar headlines", "https://www.philstar.com/rss/headlines"),
    ("PhilStar business", "https://www.philstar.com/rss/business"),
    ("PhilStar sports", "https://www.philstar.com/rss/sports"),
    ("PhilStar entertainment", "https://www.philstar.com/rss/entertainment"),
    ("Inquirer", "https://newsinfo.inquirer.net/feed"),
    ("Inquirer full", "https://www.inquirer.net/fullfeed"),
    ("GMA News", "https://data.gmanetwork.com/gno/rss/news/feed.xml"),
    ("Daily Tribune", "https://tribune.net.ph/feed"),
    ("SunStar", "https://www.sunstar.com.ph/rss"),
    ("BusinessWorld", "https://www.bworldonline.com/feed/"),
    ("Manila Bulletin", "https://mb.com.ph/feed"),
    ("Manila Times", "https://www.manilatimes.net/news/feed"),
    ("Interaksyon", "https://interaksyon.philstar.com/feed"),
]

print(f"{'SOURCE':<24} {'STATUS':<8} {'ARTICLES':<9} FIRST HEADLINE")
print("-" * 90)

for name, url in CANDIDATES:
    try:
        feed = feedparser.parse(url, agent=BROWSER_AGENT)
        status = feed.get("status", "none")
        count = len(feed.entries)
        first = feed.entries[0].get("title", "")[:45] if count else ""
        verdict = "OK " if count > 0 else "-- "
        print(f"{verdict}{name:<21} {str(status):<8} {count:<9} {first}")
    except Exception as e:
        print(f"-- {name:<21} error: {e}")