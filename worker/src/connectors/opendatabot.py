import requests

from config import settings
from db import insert_source_record, upsert_company
from tagging import normalize_company_name

BASE_URL = "https://opendatabot.ua/api/v2/company"


def fetch_company(edrpou: str):
    if not settings.opendatabot_api_key:
        raise RuntimeError("Missing OPENDATABOT_API_KEY")
    url = f"{BASE_URL}/{edrpou}"
    headers = {"Authorization": f"Bearer {settings.opendatabot_api_key}"}
    r = requests.get(url, headers=headers, timeout=30)
    r.raise_for_status()
    return r.json()


def enrich_company(edrpou: str):
    payload = fetch_company(edrpou)
    insert_source_record("OpenDataBot", f"{BASE_URL}/{edrpou}", edrpou, raw_json=payload)
    name = payload.get("name") or payload.get("full_name") or edrpou
    return upsert_company(
        legal_name=name,
        normalized_name=normalize_company_name(name),
        registration_number=edrpou,
        country="Ukraine",
        source_system="OpenDataBot",
        confidence_score=0.90,
    )


def run():
    return {"source": "OpenDataBot", "status": "ready — call enrich_company(edrpou) to enrich a company"}
