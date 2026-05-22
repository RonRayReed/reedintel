import hashlib
import json

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from config import settings

engine = create_engine(settings.db_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine)


def content_hash(payload) -> str:
    if not isinstance(payload, str):
        payload = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def insert_source_record(source_name, source_url, external_id, raw_json=None, raw_text=None):
    h = content_hash(raw_json if raw_json is not None else raw_text or "")
    with engine.begin() as conn:
        existing = conn.execute(text("""
            SELECT record_id FROM source_records
            WHERE source_name = :source_name AND content_hash = :content_hash
            LIMIT 1
        """), {"source_name": source_name, "content_hash": h}).fetchone()
        if existing:
            return str(existing[0])
        result = conn.execute(text("""
            INSERT INTO source_records (source_name, source_url, external_id, raw_json, raw_text, content_hash)
            VALUES (:source_name, :source_url, :external_id, CAST(:raw_json AS jsonb), :raw_text, :content_hash)
            RETURNING record_id
        """), {
            "source_name": source_name,
            "source_url": source_url,
            "external_id": external_id,
            "raw_json": json.dumps(raw_json, ensure_ascii=False) if raw_json is not None else None,
            "raw_text": raw_text,
            "content_hash": h,
        })
        return str(result.scalar())


def upsert_company(
    legal_name,
    normalized_name=None,
    registration_number=None,
    country=None,
    city=None,
    sector=None,
    source_system=None,
    confidence_score=0.5,
):
    with engine.begin() as conn:
        result = conn.execute(text("""
            INSERT INTO companies
                (legal_name, normalized_name, registration_number, country, city, sector, source_system, confidence_score, last_updated)
            VALUES
                (:legal_name, :normalized_name, :registration_number, :country, :city, :sector, :source_system, :confidence_score, NOW())
            ON CONFLICT (country, registration_number)
            DO UPDATE SET
                legal_name          = EXCLUDED.legal_name,
                normalized_name     = EXCLUDED.normalized_name,
                city                = COALESCE(EXCLUDED.city, companies.city),
                sector              = COALESCE(EXCLUDED.sector, companies.sector),
                source_system       = EXCLUDED.source_system,
                confidence_score    = GREATEST(companies.confidence_score, EXCLUDED.confidence_score),
                last_updated        = NOW()
            RETURNING company_id
        """), {
            "legal_name": legal_name,
            "normalized_name": normalized_name,
            "registration_number": registration_number,
            "country": country,
            "city": city,
            "sector": sector,
            "source_system": source_system,
            "confidence_score": confidence_score,
        })
        return str(result.scalar())


def get_unenriched_edrpou_codes(limit: int = 20) -> list[str]:
    """Return EDRPOU codes from ProZorro tenders not yet enriched by OpenDataBot."""
    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT DISTINCT raw_json->'procuringEntity'->'identifier'->>'id' AS edrpou
            FROM source_records
            WHERE source_name = 'ProZorro'
              AND raw_json->'procuringEntity'->'identifier'->>'scheme' = 'UA-EDR'
              AND raw_json->'procuringEntity'->'identifier'->>'id' IS NOT NULL
              AND raw_json->'procuringEntity'->'identifier'->>'id' NOT IN (
                  SELECT registration_number FROM companies
                  WHERE source_system = 'OpenDataBot' AND registration_number IS NOT NULL
              )
            LIMIT :limit
        """), {"limit": limit}).fetchall()
        return [row[0] for row in rows if row[0]]


def insert_editorial_item(
    event_type,
    title,
    city,
    country,
    sector,
    source_url,
    why_it_matters,
    confidence_score,
    company_id=None,
    procurement_event_id=None,
    source_lang: str = None,
):
    from translation import translate_pair
    title, why_it_matters = translate_pair(title, why_it_matters, source_lang=source_lang)

    with engine.begin() as conn:
        result = conn.execute(text("""
            INSERT INTO editorial_queue
                (event_type, title, city, country, sector, company_id, procurement_event_id, source_url, why_it_matters, confidence_score)
            VALUES
                (:event_type, :title, :city, :country, :sector, :company_id, :procurement_event_id, :source_url, :why_it_matters, :confidence_score)
            RETURNING queue_id
        """), {
            "event_type": event_type,
            "title": title,
            "city": city,
            "country": country,
            "sector": sector,
            "company_id": company_id,
            "procurement_event_id": procurement_event_id,
            "source_url": source_url,
            "why_it_matters": why_it_matters,
            "confidence_score": confidence_score,
        })
        return str(result.scalar())
