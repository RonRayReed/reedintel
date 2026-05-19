import json

from connectors import prozorro, mtender, anaf
from connectors.generic_ckan import run_city_portal
from editorial import get_high_priority_queue, get_queue_stats


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
        results.append(run_city_portal(
            "Lviv Open Data",
            "https://opendata.city-adm.lviv.ua",
            "business permits construction",
        ))
    except Exception as e:
        results.append({"source": "Lviv Open Data", "error": str(e)})

    try:
        queue = get_high_priority_queue(limit=10)
        stats = get_queue_stats()
        results.append({"editorial_queue_preview": queue, "editorial_stats": stats})
    except Exception as e:
        results.append({"source": "Editorial Queue", "error": str(e)})

    return results


if __name__ == "__main__":
    print(json.dumps(run_all(), indent=2, ensure_ascii=False, default=str))
