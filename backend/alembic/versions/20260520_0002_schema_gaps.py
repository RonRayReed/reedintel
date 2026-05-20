"""schema gaps: missing columns, tables, extension, and indexes

Revision ID: 0002
Revises: 0001
Create Date: 2026-05-20 00:00:00.000000
"""
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade():
    # ------------------------------------------------------------------ #
    # Extension                                                            #
    # ------------------------------------------------------------------ #
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    # ------------------------------------------------------------------ #
    # sources — missing columns                                            #
    # ------------------------------------------------------------------ #
    op.execute("ALTER TABLE sources ADD COLUMN IF NOT EXISTS manual_url TEXT")
    op.execute("ALTER TABLE sources ADD COLUMN IF NOT EXISTS api_endpoint TEXT")
    op.execute("ALTER TABLE sources ADD COLUMN IF NOT EXISTS auth_required BOOLEAN DEFAULT FALSE")
    op.execute("ALTER TABLE sources ADD COLUMN IF NOT EXISTS refresh_frequency TEXT")
    op.execute("ALTER TABLE sources ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()")

    # ------------------------------------------------------------------ #
    # source_records — missing columns                                     #
    # ------------------------------------------------------------------ #
    op.execute("ALTER TABLE source_records ADD COLUMN IF NOT EXISTS source_id UUID REFERENCES sources(source_id)")
    op.execute("ALTER TABLE source_records ADD COLUMN IF NOT EXISTS processed_at TIMESTAMPTZ")
    op.execute("ALTER TABLE source_records ADD COLUMN IF NOT EXISTS processing_status TEXT DEFAULT 'new'")

    # ------------------------------------------------------------------ #
    # companies — missing columns + indexes                                #
    # ------------------------------------------------------------------ #
    op.execute("ALTER TABLE companies ADD COLUMN IF NOT EXISTS tax_number TEXT")
    op.execute("ALTER TABLE companies ADD COLUMN IF NOT EXISTS vat_number TEXT")
    op.execute("ALTER TABLE companies ADD COLUMN IF NOT EXISTS address TEXT")
    op.execute("ALTER TABLE companies ADD COLUMN IF NOT EXISTS website TEXT")
    op.execute("ALTER TABLE companies ADD COLUMN IF NOT EXISTS verification_status TEXT DEFAULT 'unverified'")
    op.execute("ALTER TABLE companies ADD COLUMN IF NOT EXISTS first_seen_at TIMESTAMPTZ NOT NULL DEFAULT NOW()")

    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_companies_normalized_name
            ON companies USING gin (normalized_name gin_trgm_ops)
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_companies_city_sector
            ON companies (city, sector)
    """)

    # ------------------------------------------------------------------ #
    # procurement_events — missing FK columns                              #
    # ------------------------------------------------------------------ #
    op.execute("""
        ALTER TABLE procurement_events
            ADD COLUMN IF NOT EXISTS supplier_company_id UUID REFERENCES companies(company_id)
    """)
    op.execute("""
        ALTER TABLE procurement_events
            ADD COLUMN IF NOT EXISTS raw_record_id UUID REFERENCES source_records(record_id)
    """)

    # ------------------------------------------------------------------ #
    # editorial_queue — missing columns                                    #
    # ------------------------------------------------------------------ #
    op.execute("ALTER TABLE editorial_queue ADD COLUMN IF NOT EXISTS assigned_editor TEXT")
    op.execute("ALTER TABLE editorial_queue ADD COLUMN IF NOT EXISTS editor_notes TEXT")
    op.execute("ALTER TABLE editorial_queue ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()")

    # ------------------------------------------------------------------ #
    # weekly_reports — missing column                                      #
    # ------------------------------------------------------------------ #
    op.execute("ALTER TABLE weekly_reports ADD COLUMN IF NOT EXISTS report_json JSONB")

    # ------------------------------------------------------------------ #
    # New tables                                                           #
    # ------------------------------------------------------------------ #
    op.execute("""
        CREATE TABLE IF NOT EXISTS company_aliases (
            alias_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            company_id       UUID REFERENCES companies(company_id) ON DELETE CASCADE,
            alias_name       TEXT NOT NULL,
            source_name      TEXT,
            confidence_score NUMERIC(4,3) NOT NULL DEFAULT 0.0,
            created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS executives (
            executive_id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            full_name           TEXT NOT NULL,
            normalized_name     TEXT,
            title               TEXT,
            linkedin_url        TEXT,
            email               TEXT,
            phone               TEXT,
            verification_status TEXT DEFAULT 'unverified',
            first_seen_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            last_updated        TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS relationships (
            relationship_id   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            from_entity_type  TEXT NOT NULL,
            from_entity_id    UUID NOT NULL,
            to_entity_type    TEXT NOT NULL,
            to_entity_id      UUID NOT NULL,
            relationship_type TEXT NOT NULL,
            source_name       TEXT,
            confidence_score  NUMERIC(4,3) NOT NULL DEFAULT 0.0,
            start_date        DATE,
            end_date          DATE,
            created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS ai_drafts (
            draft_id       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            queue_id       UUID REFERENCES editorial_queue(queue_id) ON DELETE SET NULL,
            headline       TEXT,
            deck           TEXT,
            body           TEXT,
            model_name     TEXT,
            prompt_version TEXT,
            status         TEXT DEFAULT 'draft',
            created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            audit_id    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            actor       TEXT,
            action      TEXT,
            entity_type TEXT,
            entity_id   UUID,
            details     JSONB,
            created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)


def downgrade():
    op.execute("DROP TABLE IF EXISTS audit_logs")
    op.execute("DROP TABLE IF EXISTS ai_drafts")
    op.execute("DROP TABLE IF EXISTS relationships")
    op.execute("DROP TABLE IF EXISTS executives")
    op.execute("DROP TABLE IF EXISTS company_aliases")

    op.execute("ALTER TABLE weekly_reports DROP COLUMN IF EXISTS report_json")

    op.execute("ALTER TABLE editorial_queue DROP COLUMN IF EXISTS updated_at")
    op.execute("ALTER TABLE editorial_queue DROP COLUMN IF EXISTS editor_notes")
    op.execute("ALTER TABLE editorial_queue DROP COLUMN IF EXISTS assigned_editor")

    op.execute("ALTER TABLE procurement_events DROP COLUMN IF EXISTS raw_record_id")
    op.execute("ALTER TABLE procurement_events DROP COLUMN IF EXISTS supplier_company_id")

    op.execute("DROP INDEX IF EXISTS idx_companies_city_sector")
    op.execute("DROP INDEX IF EXISTS idx_companies_normalized_name")
    op.execute("ALTER TABLE companies DROP COLUMN IF EXISTS first_seen_at")
    op.execute("ALTER TABLE companies DROP COLUMN IF EXISTS verification_status")
    op.execute("ALTER TABLE companies DROP COLUMN IF EXISTS website")
    op.execute("ALTER TABLE companies DROP COLUMN IF EXISTS address")
    op.execute("ALTER TABLE companies DROP COLUMN IF EXISTS vat_number")
    op.execute("ALTER TABLE companies DROP COLUMN IF EXISTS tax_number")

    op.execute("ALTER TABLE source_records DROP COLUMN IF EXISTS processing_status")
    op.execute("ALTER TABLE source_records DROP COLUMN IF EXISTS processed_at")
    op.execute("ALTER TABLE source_records DROP COLUMN IF EXISTS source_id")

    op.execute("ALTER TABLE sources DROP COLUMN IF EXISTS created_at")
    op.execute("ALTER TABLE sources DROP COLUMN IF EXISTS refresh_frequency")
    op.execute("ALTER TABLE sources DROP COLUMN IF EXISTS auth_required")
    op.execute("ALTER TABLE sources DROP COLUMN IF EXISTS api_endpoint")
    op.execute("ALTER TABLE sources DROP COLUMN IF EXISTS manual_url")

    op.execute("DROP EXTENSION IF EXISTS pg_trgm")
