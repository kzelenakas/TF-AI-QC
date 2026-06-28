-- TF AI-QC — Initial Schema
-- PostgreSQL 15+
-- Move this file to db/migrations/ in the repo when development starts.
--
-- NPI note: report_data.raw_data (JSONB) will contain PII from parsed UAD XML.
-- The pii_scrubbed flag on reports MUST be true before report_data is passed
-- to any external AI API. The schema does not strip PII — the application layer does.

-- ============================================================
-- USERS (internal — reviewers, QDS, management)
-- ============================================================

CREATE TABLE users (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    email           TEXT        NOT NULL UNIQUE,
    full_name       TEXT        NOT NULL,
    role            TEXT        NOT NULL CHECK (role IN ('reviewer', 'qds', 'manager', 'admin')),
    is_active       BOOLEAN     NOT NULL DEFAULT true,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============================================================
-- APPRAISERS (external staff — separate from internal users)
-- ============================================================

CREATE TABLE appraisers (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    license_number  TEXT        NOT NULL,
    license_state   CHAR(2)     NOT NULL,
    full_name       TEXT        NOT NULL,
    email           TEXT,
    is_active       BOOLEAN     NOT NULL DEFAULT true,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (license_number, license_state)
);

-- ============================================================
-- REPORTS (one row per submitted appraisal)
-- ============================================================

CREATE TABLE reports (
    id                      UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    order_number            TEXT        NOT NULL,           -- TF internal reference
    report_type             TEXT        NOT NULL CHECK (report_type IN ('URAR', 'restricted')),
    effective_date          DATE        NOT NULL,
    appraiser_id            UUID        NOT NULL REFERENCES appraisers(id),
    assigned_reviewer_id    UUID        REFERENCES users(id),
    status                  TEXT        NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'in_review', 'revision_requested', 'approved', 'rejected')),

    -- Storage reference only — actual file lives in GCS or R2
    file_path               TEXT        NOT NULL,
    file_type               TEXT        NOT NULL CHECK (file_type IN ('xml', 'pdf')),
    file_size_bytes         BIGINT,

    -- PII scrubbing gate — must be true before any AI call
    pii_scrubbed            BOOLEAN     NOT NULL DEFAULT false,
    pii_scrubbed_at         TIMESTAMPTZ,

    submitted_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
    review_started_at       TIMESTAMPTZ,
    review_completed_at     TIMESTAMPTZ,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_reports_appraiser    ON reports(appraiser_id);
CREATE INDEX idx_reports_reviewer     ON reports(assigned_reviewer_id);
CREATE INDEX idx_reports_status       ON reports(status);
CREATE INDEX idx_reports_submitted    ON reports(submitted_at);

-- ============================================================
-- REPORT DATA (parsed UAD 3.6 fields — contains PII)
-- ============================================================

CREATE TABLE report_data (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    report_id       UUID        NOT NULL UNIQUE REFERENCES reports(id) ON DELETE CASCADE,
    uad_version     TEXT        NOT NULL DEFAULT '3.6',
    parsed_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    raw_data        JSONB       NOT NULL,    -- Full parsed UAD structure (contains PII)
    parse_errors    JSONB                   -- Any parsing warnings or failures
);

-- ============================================================
-- COMPLIANCE FINDINGS (one row per rule per report)
-- ============================================================
-- Layer 1 = Fannie Mae / Freddie Mac UAD Compliance API (709+ rules)
-- Layer 2 = USPAP compliance flags
-- Layer 3 = TF internal quality checks (Zen Engine + LLM scoring)

CREATE TABLE compliance_findings (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    report_id       UUID        NOT NULL REFERENCES reports(id) ON DELETE CASCADE,

    rule_layer      INT         NOT NULL CHECK (rule_layer IN (1, 2, 3)),
    rule_source     TEXT        NOT NULL
        CHECK (rule_source IN ('fannie_mae', 'freddie_mac', 'uspap', 'tf_internal')),
    rule_id         TEXT        NOT NULL,    -- e.g. 'UAD-URAR-0042'
    rule_name       TEXT        NOT NULL,

    result          TEXT        NOT NULL
        CHECK (result IN ('pass', 'fail', 'warning', 'info', 'skipped')),
    severity        TEXT
        CHECK (severity IN ('critical', 'major', 'minor', 'informational')),
    finding_text    TEXT,

    -- Layer 3 LLM fields
    ai_generated    BOOLEAN     NOT NULL DEFAULT false,
    ai_model        TEXT,
    ai_reasoning    TEXT,
    ai_confidence   NUMERIC(4,3) CHECK (ai_confidence BETWEEN 0 AND 1),

    -- Reviewer override
    overridden_by   UUID        REFERENCES users(id),
    override_reason TEXT,
    overridden_at   TIMESTAMPTZ,

    checked_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_findings_report       ON compliance_findings(report_id);
CREATE INDEX idx_findings_result       ON compliance_findings(report_id, result);
CREATE INDEX idx_findings_layer_source ON compliance_findings(rule_layer, rule_source);

-- ============================================================
-- QUALITY SCORES (5-dimension scoring per report)
-- ============================================================

CREATE TABLE quality_scores (
    id                      UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    report_id               UUID        NOT NULL UNIQUE REFERENCES reports(id) ON DELETE CASCADE,

    comparable_selection    NUMERIC(5,2) CHECK (comparable_selection    BETWEEN 0 AND 100),
    adjustment_support      NUMERIC(5,2) CHECK (adjustment_support      BETWEEN 0 AND 100),
    market_analysis         NUMERIC(5,2) CHECK (market_analysis         BETWEEN 0 AND 100),
    narrative_quality       NUMERIC(5,2) CHECK (narrative_quality       BETWEEN 0 AND 100),
    reconciliation          NUMERIC(5,2) CHECK (reconciliation          BETWEEN 0 AND 100),
    overall_score           NUMERIC(5,2) CHECK (overall_score           BETWEEN 0 AND 100),

    scored_by       TEXT        NOT NULL CHECK (scored_by IN ('ai', 'reviewer', 'hybrid')),
    scored_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    reviewer_id     UUID        REFERENCES users(id),
    notes           TEXT
);

-- ============================================================
-- REVISION REQUESTS (one per review cycle — a report may have multiple)
-- ============================================================

CREATE TABLE revision_requests (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    report_id       UUID        NOT NULL REFERENCES reports(id) ON DELETE CASCADE,
    created_by      UUID        NOT NULL REFERENCES users(id),
    status          TEXT        NOT NULL DEFAULT 'draft'
        CHECK (status IN ('draft', 'sent', 'responded', 'closed', 'waived')),
    sent_at         TIMESTAMPTZ,
    due_at          TIMESTAMPTZ,
    responded_at    TIMESTAMPTZ,
    closed_at       TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_revision_requests_report  ON revision_requests(report_id);
CREATE INDEX idx_revision_requests_status  ON revision_requests(status);

-- ============================================================
-- REVISION ITEMS (individual line items within a request)
-- ============================================================

CREATE TABLE revision_items (
    id                      UUID    PRIMARY KEY DEFAULT gen_random_uuid(),
    revision_request_id     UUID    NOT NULL REFERENCES revision_requests(id) ON DELETE CASCADE,
    finding_id              UUID    REFERENCES compliance_findings(id),

    description             TEXT    NOT NULL,
    required_action         TEXT    NOT NULL,

    status                  TEXT    NOT NULL DEFAULT 'open'
        CHECK (status IN ('open', 'addressed', 'waived', 'disputed')),

    appraiser_response      TEXT,
    resolved_at             TIMESTAMPTZ,
    resolved_by             UUID    REFERENCES users(id)
);

CREATE INDEX idx_revision_items_request ON revision_items(revision_request_id);

-- ============================================================
-- APPRAISER METRICS (aggregated performance — updated async)
-- ============================================================

CREATE TABLE appraiser_metrics (
    id                          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    appraiser_id                UUID        NOT NULL REFERENCES appraisers(id) ON DELETE CASCADE,

    period_start                DATE        NOT NULL,
    period_end                  DATE        NOT NULL,

    reports_submitted           INT         NOT NULL DEFAULT 0,
    reports_approved            INT         NOT NULL DEFAULT 0,
    reports_with_revisions      INT         NOT NULL DEFAULT 0,
    revision_rate               NUMERIC(5,4),   -- 0.0000–1.0000

    avg_overall_score           NUMERIC(5,2),
    avg_comparable_selection    NUMERIC(5,2),
    avg_adjustment_support      NUMERIC(5,2),
    avg_market_analysis         NUMERIC(5,2),
    avg_narrative_quality       NUMERIC(5,2),
    avg_reconciliation          NUMERIC(5,2),

    top_finding_rule_ids        TEXT[],     -- Most frequently failed rules this period

    computed_at                 TIMESTAMPTZ NOT NULL DEFAULT now(),

    UNIQUE (appraiser_id, period_start, period_end)
);

CREATE INDEX idx_appraiser_metrics_appraiser ON appraiser_metrics(appraiser_id);
CREATE INDEX idx_appraiser_metrics_period    ON appraiser_metrics(period_start, period_end);

-- ============================================================
-- AUDIT LOG (immutable — all state changes)
-- ============================================================

CREATE TABLE audit_log (
    id              BIGSERIAL   PRIMARY KEY,
    entity_type     TEXT        NOT NULL,   -- 'report', 'revision_request', 'finding', etc.
    entity_id       UUID        NOT NULL,
    action          TEXT        NOT NULL,   -- 'created', 'status_changed', 'overridden', 'sent', etc.
    actor_id        UUID        REFERENCES users(id),
    old_value       JSONB,
    new_value       JSONB,
    occurred_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_audit_log_entity   ON audit_log(entity_type, entity_id);
CREATE INDEX idx_audit_log_occurred ON audit_log(occurred_at);
