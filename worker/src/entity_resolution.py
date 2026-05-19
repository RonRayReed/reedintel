from rapidfuzz import fuzz
from sqlalchemy import text

from db import engine
from tagging import normalize_company_name


def find_candidate_company(name: str, country: str | None = None):
    normalized = normalize_company_name(name)
    with engine.begin() as conn:
        rows = conn.execute(text("""
            SELECT company_id, legal_name, normalized_name, country
            FROM companies
            WHERE (:country IS NULL OR country = :country)
            ORDER BY similarity(normalized_name, :normalized) DESC
            LIMIT 25
        """), {"country": country, "normalized": normalized}).fetchall()

    best = None
    for row in rows:
        score = fuzz.token_sort_ratio(normalized, row.normalized_name or "")
        if best is None or score > best["score"]:
            best = {"company_id": str(row.company_id), "legal_name": row.legal_name, "score": score}
    return best


def resolution_decision(score: float) -> str:
    if score >= 95:
        return "automatic_match"
    if score >= 85:
        return "human_review_likely_match"
    if score >= 70:
        return "possible_match"
    return "new_entity"
