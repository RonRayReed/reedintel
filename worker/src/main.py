import json

from connectors import prozorro, mtender, anaf, opendatabot
from connectors.generic_ckan import run_city_portal
from connectors import rss_feed
from editorial import get_high_priority_queue, get_queue_stats


CKAN_PORTALS = [
    ("Lviv Open Data",  "https://opendata.city-adm.lviv.ua",  "business permits construction"),
    ("Kyiv Open Data",  "https://data.kyivcity.gov.ua",        "procurement tender contracts"),
    ("Romania OpenData","https://data.gov.ro",                  "achizitii publice"),
]


def run_all():
    results = []

    try:
        results.append(prozorro.run())
    except Exception as e:
        results.append({"source": "ProZorro", "error": str(e)})

    try:
        results.append(mtender.run())
    except Exception as e:
        results.append({"source": "MTender", "error": str(e)})

    try:
        results.append(anaf.run())
    except Exception as e:
        results.append({"source": "ANAF", "error": str(e)})

    try:
        results.append(opendatabot.run())
    except Exception as e:
        results.append({"source": "OpenDataBot", "error": str(e)})

    for source_name, base_url, query in CKAN_PORTALS:
        try:
            results.append(run_city_portal(source_name, base_url, query))
        except Exception as e:
            results.append({"source": source_name, "error": str(e)})

    try:
        results.extend(rss_feed.run())
    except Exception as e:
        results.append({"source": "RSS Feeds", "error": str(e)})

    try:
        queue = get_high_priority_queue(limit=10)
        stats = get_queue_stats()
        results.append({"editorial_queue_preview": queue, "editorial_stats": stats})
    except Exception as e:
        results.append({"source": "Editorial Queue", "error": str(e)})

    return results


if __name__ == "__main__":
    print(json.dumps(run_all(), indent=2, ensure_ascii=False, default=str))
