from sqlalchemy import text

from db import engine


def get_high_priority_queue(limit: int = 25):
    with engine.begin() as conn:
        rows = conn.execute(text("""
            SELECT queue_id, event_type, title, city, country, sector, source_url, why_it_matters, confidence_score
            FROM editorial_queue
            WHERE status IN ('new', 'needs_research')
            ORDER BY confidence_score DESC, created_at DESC
            LIMIT :limit
        """), {"limit": limit}).mappings().all()
    return [dict(r) for r in rows]


def update_status(queue_id: str, status: str, editor_notes: str | None = None):
    with engine.begin() as conn:
        conn.execute(text("""
            UPDATE editorial_queue
            SET status       = :status,
                editor_notes = COALESCE(:editor_notes, editor_notes),
                updated_at   = NOW()
            WHERE queue_id = :queue_id
        """), {"queue_id": queue_id, "status": status, "editor_notes": editor_notes})


def get_queue_stats():
    with engine.begin() as conn:
        row = conn.execute(text("""
            SELECT
                COUNT(*) FILTER (WHERE status = 'new')              AS new_count,
                COUNT(*) FILTER (WHERE status = 'needs_research')   AS needs_research_count,
                COUNT(*) FILTER (WHERE status = 'verified')         AS verified_count,
                COUNT(*) FILTER (WHERE status = 'approved_for_article') AS approved_count,
                COUNT(*) FILTER (WHERE status = 'published')        AS published_count,
                COUNT(*) FILTER (WHERE status = 'rejected')         AS rejected_count
            FROM editorial_queue
        """)).mappings().one()
    return dict(row)
