import requests
from datetime import datetime, timedelta, timezone

from db import insert_source_record, insert_editorial_item

BASE_URL = "https://public.api.openprocurement.org/api/2.5/tenders"
KEYWORDS = ["reconstruction", "repair", "road", "bridge", "energy", "hospital", "port", "infrastructure"]
CITY_TERMS = {
    "Kyiv": ["kyiv", "київ"],
    "Lviv": ["lviv", "львів"],
    "Odesa": ["odesa", "одеса", "odessa"],
}


def infer_city(text: str):
    t = (text or "").lower()
    for city, terms in CITY_TERMS.items():
        if any(term in t for term in terms):
            return city
    return None


def infer_sector(text: str):
    t = (text or "").lower()
    if any(w in t for w in ["road", "bridge", "дорога", "міст"]):     return "Infrastructure"
    if any(w in t for w in ["energy", "electric", "power", "енерг"]): return "Energy"
    if any(w in t for w in ["hospital", "medical", "clinic", "лікар"]): return "Healthcare"
    if any(w in t for w in ["port", "harbor", "terminal", "порт"]):   return "Ports & Logistics"
    return "Government Procurement"


def fetch_recent_tenders():
    since = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
    params = {"offset": since, "descending": "1"}
    r = requests.get(BASE_URL, params=params, timeout=30)
    r.raise_for_status()
    return r.json().get("data", [])


def fetch_tender_detail(tender_id: str):
    url = f"{BASE_URL}/{tender_id}"
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    return r.json().get("data", {})


def run():
    tenders = fetch_recent_tenders()
    created = 0

    for item in tenders:
        tender_id = item.get("id")
        if not tender_id:
            continue

        try:
            detail = fetch_tender_detail(tender_id)
        except Exception:
            continue

        title = detail.get("title", "")
        description = detail.get("description", "")
        combined = f"{title} {description}"

        insert_source_record("ProZorro", f"{BASE_URL}/{tender_id}", tender_id, raw_json=detail)

        city = infer_city(combined)
        sector = infer_sector(combined)
        value = detail.get("value", {}).get("amount")

        if city or any(k in combined.lower() for k in KEYWORDS) or (value and value > 250000):
            insert_editorial_item(
                event_type="procurement_tender",
                title=title[:500] or f"Tender {tender_id}",
                city=city or "Ukraine",
                country="Ukraine",
                sector=sector,
                source_url=f"{BASE_URL}/{tender_id}",
                why_it_matters=f"New public procurement event detected. Estimated value: {value}.",
                confidence_score=0.75,
            )
            created += 1

    return {"source": "ProZorro", "processed": len(tenders), "editorial_items": created}
