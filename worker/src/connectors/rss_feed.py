import feedparser

from db import insert_source_record, insert_editorial_item
from tagging import infer_city, infer_sector

FEED_SOURCES = [
    {"source_name": "Lviv IT Cluster",      "url": "https://itcluster.lviv.ua/en/feed/",           "city": "Lviv",      "country": "Ukraine"},
    {"source_name": "Ekonomichna Pravda",    "url": "https://www.epravda.com.ua/rss/economics/",    "city": "Kyiv",      "country": "Ukraine"},
    {"source_name": "Ukrinform Economy",     "url": "https://www.ukrinform.net/rss/block-economy",  "city": "Kyiv",      "country": "Ukraine"},
    {"source_name": "Interfax Ukraine",      "url": "https://en.interfax.com.ua/news/economic.rss", "city": "Kyiv",      "country": "Ukraine"},
    {"source_name": "Moldova Business News", "url": "https://www.mold-street.com/?rss=1",            "city": "Chisinau",  "country": "Moldova"},
    {"source_name": "Romania Economica",     "url": "https://www.economica.net/rss",                 "city": "Bucharest", "country": "Romania"},
]


def run_feed(source_name: str, feed_url: str, default_city: str, default_country: str):
    feed = feedparser.parse(feed_url)
    created = 0

    for entry in feed.entries:
        title = entry.get("title", "")
        link = entry.get("link", "")
        summary = entry.get("summary", "")
        entry_id = entry.get("id") or link

        insert_source_record(
            source_name=source_name,
            source_url=link,
            external_id=entry_id,
            raw_text=f"{title}\n{summary}",
        )

        city = infer_city(f"{title} {summary}") or default_city
        sector = infer_sector(f"{title} {summary}")

        insert_editorial_item(
            event_type="rss_article",
            title=title[:500],
            city=city,
            country=default_country,
            sector=sector,
            source_url=link,
            why_it_matters=f"RSS signal from {source_name}.",
            confidence_score=0.50,
        )
        created += 1

    return {"source": source_name, "entries": len(feed.entries), "editorial_items": created}


def run():
    results = []
    for feed in FEED_SOURCES:
        try:
            result = run_feed(
                feed["source_name"],
                feed["url"],
                feed["city"],
                feed["country"],
            )
            results.append(result)
        except Exception as e:
            results.append({"source": feed["source_name"], "error": str(e)})
    return results
