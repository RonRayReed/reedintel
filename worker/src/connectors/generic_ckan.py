import requests

from db import insert_source_record


def package_search(base_url: str, query: str = "", rows: int = 100):
    url = base_url.rstrip("/") + "/api/3/action/package_search"
    r = requests.get(url, params={"q": query, "rows": rows}, timeout=30)
    r.raise_for_status()
    return r.json().get("result", {}).get("results", [])


def run_city_portal(source_name: str, base_url: str, query: str):
    packages = package_search(base_url, query=query)
    for package in packages:
        insert_source_record(
            source_name=source_name,
            source_url=package.get("url") or base_url,
            external_id=package.get("id"),
            raw_json=package,
        )
    return {"source": source_name, "packages": len(packages)}
