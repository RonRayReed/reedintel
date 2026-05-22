import requests
from datetime import date

from db import insert_source_record, upsert_company, insert_editorial_item
from tagging import normalize_company_name

ANAF_VAT_URL = "https://webservicesp.anaf.ro/PlatitorTvaRest/api/v8/ws/tva"
ROMANIA_OPENDATA_URL = "https://data.gov.ro"
PROCUREMENT_KEYWORDS = ["achizitii", "licitatie", "contract", "investitie", "infrastructura", "procurement"]


def lookup_company(cui: int):
    """Look up a Romanian company by CUI (fiscal code) via ANAF webservice."""
    payload = [{"cui": int(cui), "data": date.today().isoformat()}]
    r = requests.post(ANAF_VAT_URL, json=payload, timeout=30)
    r.raise_for_status()
    return r.json().get("found", [])


def enrich_company(cui: int):
    """Fetch and store a Romanian company from ANAF, return company_id."""
    results = lookup_company(cui)
    if not results:
        return None
    data = results[0]
    general = data.get("date_generale", {})
    name = general.get("denumire") or str(cui)
    address = general.get("adresa_sediu_social", {})
    city = address.get("sdenumire_Localitate") or None

    insert_source_record("ANAF", ANAF_VAT_URL, str(cui), raw_json=data)
    return upsert_company(
        legal_name=name,
        normalized_name=normalize_company_name(name),
        registration_number=str(cui),
        country="Romania",
        city=city,
        source_system="ANAF",
        confidence_score=0.85,
    )


def run():
    """Fetch procurement-related open datasets from Romania's data.gov.ro portal."""
    from connectors.generic_ckan import package_search
    try:
        packages = package_search(ROMANIA_OPENDATA_URL, query="achizitii publice licitatie", rows=50)
    except Exception as e:
        return {"source": "ANAF/RO-OpenData", "status": "error", "error": str(e)}

    saved = 0
    signals = 0
    for package in packages:
        pkg_id = package.get("id")
        title = package.get("title", "")
        insert_source_record(
            source_name="ANAF",
            source_url=package.get("url") or ROMANIA_OPENDATA_URL,
            external_id=pkg_id,
            raw_json=package,
        )
        saved += 1

        if any(kw in title.lower() for kw in PROCUREMENT_KEYWORDS):
            insert_editorial_item(
                event_type="romania_opendata",
                title=title[:500] or f"RO Dataset {pkg_id}",
                city="Bucharest",
                country="Romania",
                sector="Government Procurement",
                source_url=package.get("url") or ROMANIA_OPENDATA_URL,
                why_it_matters="Romanian public procurement dataset published on data.gov.ro.",
                confidence_score=0.55,
                source_lang="RO",
            )
            signals += 1

    return {"source": "ANAF/RO-OpenData", "packages": saved, "editorial_items": signals}
