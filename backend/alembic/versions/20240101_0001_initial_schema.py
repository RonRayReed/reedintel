"""initial schema

Revision ID: 0001
Revises:
Create Date: 2024-01-01 00:00:00.000000
"""
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        CREATE TABLE IF NOT EXISTS sources (
            source_id   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            source_name TEXT NOT NULL UNIQUE,
            source_type TEXT,
            city        TEXT,
            country     TEXT,
            active      BOOLEAN NOT NULL DEFAULT true
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS source_records (
            record_id    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            source_name  TEXT NOT NULL,
            source_url   TEXT,
            external_id  TEXT,
            raw_json     JSONB,
            raw_text     TEXT,
            content_hash TEXT NOT NULL,
            fetched_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_source_records_source_hash
            ON source_records (source_name, content_hash)
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS companies (
            company_id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            legal_name          TEXT NOT NULL,
            normalized_name     TEXT,
            registration_number TEXT,
            country             TEXT,
            city                TEXT,
            sector              TEXT,
            source_system       TEXT,
            confidence_score    NUMERIC(4,3) NOT NULL DEFAULT 0.5,
            last_updated        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            UNIQUE (country, registration_number)
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS procurement_events (
            procurement_event_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            source_name          TEXT NOT NULL,
            tender_id            TEXT,
            buyer_name           TEXT,
            supplier_name        TEXT,
            title                TEXT,
            description          TEXT,
            value_amount         NUMERIC,
            currency             TEXT,
            city                 TEXT,
            country              TEXT,
            sector               TEXT,
            award_date           DATE,
            publication_date     DATE,
            source_url           TEXT,
            confidence_score     NUMERIC(4,3) NOT NULL DEFAULT 0.5,
            created_at           TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS editorial_queue (
            queue_id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            event_type           TEXT NOT NULL,
            title                TEXT NOT NULL,
            city                 TEXT,
            country              TEXT,
            sector               TEXT,
            company_id           UUID REFERENCES companies(company_id) ON DELETE SET NULL,
            procurement_event_id UUID REFERENCES procurement_events(procurement_event_id) ON DELETE SET NULL,
            source_url           TEXT,
            why_it_matters       TEXT,
            confidence_score     NUMERIC(4,3) NOT NULL DEFAULT 0.75,
            status               TEXT NOT NULL DEFAULT 'new',
            created_at           TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_editorial_queue_status
            ON editorial_queue (status, created_at DESC)
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS weekly_reports (
            report_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            week_start        DATE NOT NULL,
            week_end          DATE NOT NULL,
            title             TEXT,
            executive_summary TEXT,
            report_markdown   TEXT,
            created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)


def downgrade():
    op.execute("DROP TABLE IF EXISTS weekly_reports")
    op.execute("DROP TABLE IF EXISTS editorial_queue")
    op.execute("DROP TABLE IF EXISTS procurement_events")
    op.execute("DROP TABLE IF EXISTS companies")
    op.execute("DROP TABLE IF EXISTS source_records")
    op.execute("DROP TABLE IF EXISTS sources")
