import requests

from db import insert_source_record, insert_editorial_item

BASE_URL = "https://mtender.gov.md"
KEYWORDS = ["energy", "road", "infrastructure", "bank", "it", "construction", "eu"]


def run():
    endpoint = f"{BASE_URL}/api/tenders"

    try:
        r = requests.get(endpoint, timeout=30)
    except Exception as e:
        return {"source": "MTender", "status": "connection_error", "error": str(e)}

    if r.status_code == 404:
        return {"source": "MTender", "status": "endpoint_not_configured"}

    r.raise_for_status()
    data = r.json()
    count = 0

    for tender in data.get("data", []):
        tender_id = tender.get("id")
        title = tender.get("title", "")
        insert_source_record("MTender", endpoint, tender_id, raw_json=tender)

        if any(word in title.lower() for word in KEYWORDS):
            insert_editorial_item(
                event_type="moldova_procurement",
                title=title[:500] or f"MTender {tender_id}",
                city="Chisinau",
                country="Moldova",
                sector="Government Procurement",
                source_url=endpoint,
                why_it_matters="Moldova public procurement event detected for editorial review.",
                confidence_score=0.65,
            )
            count += 1

    return {"source": "MTender", "editorial_items": count}
