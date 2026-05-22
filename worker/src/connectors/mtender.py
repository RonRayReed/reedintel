import requests

from db import insert_source_record, insert_editorial_item

# MTender's OpenProcurement API is no longer publicly accessible.
# We fall back to Moldova's ANSC open data CKAN portal (achizitii.md).
ANSC_CKAN_URL = "https://date.gov.md/api/3/action/package_search"
KEYWORDS = ["achizitii", "licitatie", "tender", "contract", "constructii", "energie", "infrastructura"]


def run():
    try:
        r = requests.get(ANSC_CKAN_URL, params={"q": "achizitii publice tender", "rows": 100}, timeout=30)
        r.raise_for_status()
        packages = r.json().get("result", {}).get("results", [])
    except Exception as e:
        return {"source": "MTender/ANSC", "status": "connection_error", "error": str(e)}

    created = 0
    for pkg in packages:
        pkg_id = pkg.get("id")
        title = pkg.get("title", "")
        insert_source_record("MTender", pkg.get("url") or ANSC_CKAN_URL, pkg_id, raw_json=pkg)

        if any(kw in title.lower() for kw in KEYWORDS):
            insert_editorial_item(
                event_type="moldova_procurement",
                title=title[:500] or f"ANSC Dataset {pkg_id}",
                city="Chisinau",
                country="Moldova",
                sector="Government Procurement",
                source_url=pkg.get("url") or ANSC_CKAN_URL,
                why_it_matters="Moldova public procurement dataset published on date.gov.md.",
                confidence_score=0.60,
                source_lang="RO",
            )
            created += 1

    return {"source": "MTender/ANSC", "packages": len(packages), "editorial_items": created}
