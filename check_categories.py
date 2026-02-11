import feedparser

feed = feedparser.parse("https://cdn.aitimes.com/rss/gn_rss_allArticle.xml")

categories = set()

for entry in feed.entries:
    if "tags" in entry:
        for tag in entry.tags:
            categories.add(tag.term)

print(f"Categories: {categories}")