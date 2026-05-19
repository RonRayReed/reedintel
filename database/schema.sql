CREATE EXTENSION IF NOT EXISTS pg_trgm;

CREATE TABLE IF NOT EXISTS sources (
    source_id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_name      TEXT NOT NULL,
    source_type      TEXT NOT NULL,
    city             TEXT,
    country          TEXT,
    manual_url       TEXT,
    api_endpoint     TEXT,
    auth_required    BOOLEAN DEFAULT FALSE,
    refresh_frequency TEXT,
    active           BOOLEAN DEFAULT TRUE,
    created_at       TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS source_records (
    record_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id         UUID REFERENCES sources(source_id),
    source_name       TEXT NOT NULL,
    external_id       TEXT,
    source_url        TEXT,
    raw_json          JSONB,
    raw_text          TEXT,
    content_hash      TEXT,
    fetched_at        TIMESTAMP DEFAULT NOW(),
    processed_at      TIMESTAMP,
    processing_status TEXT DEFAULT 'new'
);

CREATE TABLE IF NOT EXISTS companies (
    company_id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    legal_name          TEXT NOT NULL,
    normalized_name     TEXT,
    registration_number TEXT,
    tax_number          TEXT,
    vat_number          TEXT,
    country             TEXT,
    city                TEXT,
    address             TEXT,
    website             TEXT,
    sector              TEXT,
    source_system       TEXT,
    confidence_score    NUMERIC DEFAULT 0,
    verification_status TEXT DEFAULT 'unverified',
    first_seen_at       TIMESTAMP DEFAULT NOW(),
    last_updated        TIMESTAMP DEFAULT NOW(),
    UNIQUE(country, registration_number)
);

CREATE INDEX IF NOT EXISTS idx_companies_normalized_name
    ON companies USING gin (normalized_name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_companies_city_sector
    ON companies(city, sector);

CREATE TABLE IF NOT EXISTS company_aliases (
    alias_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id       UUID REFERENCES companies(company_id),
    alias_name       TEXT NOT NULL,
    source_name      TEXT,
    confidence_score NUMERIC DEFAULT 0,
    created_at       TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS procurement_events (
    event_id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_name         TEXT NOT NULL,
    tender_id           TEXT,
    buyer_name          TEXT,
    supplier_name       TEXT,
    supplier_company_id UUID REFERENCES companies(company_id),
    title               TEXT,
    description         TEXT,
    value_amount        NUMERIC,
    currency            TEXT,
    city                TEXT,
    country             TEXT,
    sector              TEXT,
    award_date          DATE,
    publication_date    DATE,
    source_url          TEXT,
    raw_record_id       UUID REFERENCES source_records(record_id),
    confidence_score    NUMERIC DEFAULT 0,
    created_at          TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS executives (
    executive_id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    full_name           TEXT NOT NULL,
    normalized_name     TEXT,
    title               TEXT,
    linkedin_url        TEXT,
    email               TEXT,
    phone               TEXT,
    verification_status TEXT DEFAULT 'unverified',
    first_seen_at       TIMESTAMP DEFAULT NOW(),
    last_updated        TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS relationships (
    relationship_id   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    from_entity_type  TEXT NOT NULL,
    from_entity_id    UUID NOT NULL,
    to_entity_type    TEXT NOT NULL,
    to_entity_id      UUID NOT NULL,
    relationship_type TEXT NOT NULL,
    source_name       TEXT,
    confidence_score  NUMERIC DEFAULT 0,
    start_date        DATE,
    end_date          DATE,
    created_at        TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS editorial_queue (
    queue_id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type           TEXT NOT NULL,
    title                TEXT NOT NULL,
    city                 TEXT,
    country              TEXT,
    sector               TEXT,
    company_id           UUID REFERENCES companies(company_id),
    procurement_event_id UUID REFERENCES procurement_events(event_id),
    source_url           TEXT,
    why_it_matters       TEXT,
    confidence_score     NUMERIC DEFAULT 0,
    status               TEXT DEFAULT 'new',
    assigned_editor      TEXT,
    editor_notes         TEXT,
    created_at           TIMESTAMP DEFAULT NOW(),
    updated_at           TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ai_drafts (
    draft_id       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    queue_id       UUID REFERENCES editorial_queue(queue_id),
    headline       TEXT,
    deck           TEXT,
    body           TEXT,
    model_name     TEXT,
    prompt_version TEXT,
    status         TEXT DEFAULT 'draft',
    created_at     TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS weekly_reports (
    report_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    week_start        DATE,
    week_end          DATE,
    title             TEXT,
    executive_summary TEXT,
    report_json       JSONB,
    report_markdown   TEXT,
    created_at        TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS audit_logs (
    audit_id    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    actor       TEXT,
    action      TEXT,
    entity_type TEXT,
    entity_id   UUID,
    details     JSONB,
    created_at  TIMESTAMP DEFAULT NOW()
);
