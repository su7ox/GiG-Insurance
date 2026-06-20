-- ==========================================================================
-- GigInsurance – Initial Schema
-- Run this against the "giginsurance" database in pgAdmin 4
-- (Query Tool → open this file → Execute)
-- ==========================================================================

-- --------------------------------------------------------------------------
-- ENUM TYPES
-- --------------------------------------------------------------------------

CREATE TYPE platform_enum AS ENUM ('zepto', 'blinkit');

CREATE TYPE onboarding_status_enum AS ENUM (
    'pending_platform',
    'pending_partner_id',
    'pending_phone',
    'pending_otp',
    'verified'
);

CREATE TYPE policy_status_enum AS ENUM ('active', 'expired', 'cancelled');

CREATE TYPE disruption_type_enum AS ENUM (
    'heavy_rain',
    'flood',
    'extreme_heat',
    'severe_aqi',
    'cyclone',
    'curfew_section_144',
    'unknown'
);

CREATE TYPE claim_decision_enum AS ENUM (
    'approved',
    'denied',
    'manual_review',
    'pending'
);

CREATE TYPE payout_status_enum AS ENUM (
    'pending',
    'processing',
    'success',
    'failed'
);

CREATE TYPE payout_channel_enum AS ENUM ('razorpay', 'upi', 'wallet');

-- --------------------------------------------------------------------------
-- TABLE: workers
-- --------------------------------------------------------------------------

CREATE TABLE workers (
    id                 SERIAL PRIMARY KEY,
    platform           platform_enum            NOT NULL,
    partner_id         VARCHAR(64)              NOT NULL,
    phone_number       VARCHAR(15)              NOT NULL UNIQUE,
    whatsapp_id        VARCHAR(32)              NOT NULL UNIQUE,
    zone               VARCHAR(128)             NOT NULL,
    vehicle_type       VARCHAR(32),                                       -- bicycle | motorcycle | e-bike
    tier               VARCHAR(16),                                       -- bronze | silver | gold
    preferred_language VARCHAR(8)               NOT NULL DEFAULT 'en',    -- en | hi | mr | te
    onboarding_status  onboarding_status_enum   NOT NULL DEFAULT 'pending_platform',
    created_at         TIMESTAMPTZ              NOT NULL DEFAULT NOW(),
    updated_at         TIMESTAMPTZ              NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_workers_phone_number  ON workers (phone_number);
CREATE INDEX ix_workers_whatsapp_id   ON workers (whatsapp_id);
CREATE INDEX ix_workers_partner_id    ON workers (partner_id);

COMMENT ON TABLE  workers                   IS 'Verified gig delivery worker profiles (Zepto and Blinkit).';
COMMENT ON COLUMN workers.partner_id        IS 'Platform-issued ID validated against the platform mock API.';
COMMENT ON COLUMN workers.whatsapp_id       IS 'The WhatsApp sender ID that binds to this worker profile.';
COMMENT ON COLUMN workers.tier              IS 'Risk/premium tier: bronze | silver | gold. Set by XGBoost weekly model.';
COMMENT ON COLUMN workers.preferred_language IS 'Language for Smart Receipt generation: en | hi | mr | te.';

-- --------------------------------------------------------------------------
-- TABLE: sessions
-- --------------------------------------------------------------------------

CREATE TABLE sessions (
    id                SERIAL PRIMARY KEY,
    whatsapp_id       VARCHAR(32)  NOT NULL UNIQUE,
    worker_id         INTEGER      REFERENCES workers(id) ON DELETE CASCADE,   -- NULL until onboarding complete
    is_active         BOOLEAN      NOT NULL DEFAULT FALSE,
    pending_otp_hash  VARCHAR(128),                                            -- bcrypt hash; cleared on verify
    otp_expires_at    TIMESTAMPTZ,
    otp_attempts      SMALLINT     NOT NULL DEFAULT 0,
    onboarding_step   VARCHAR(32)  NOT NULL DEFAULT 'pending_platform',
    created_at        TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    last_active_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    invalidated_at    TIMESTAMPTZ                                              -- set when chat is deleted/cleared
);

CREATE INDEX ix_sessions_whatsapp_id ON sessions (whatsapp_id);

COMMENT ON TABLE  sessions                IS 'One row per WhatsApp sender. Deleting the chat sets invalidated_at and is_active = false.';
COMMENT ON COLUMN sessions.pending_otp_hash IS 'Hashed OTP stored only during the onboarding/re-auth window.';
COMMENT ON COLUMN sessions.invalidated_at   IS 'Populated when session is invalidated; worker must re-verify to regain access.';

-- --------------------------------------------------------------------------
-- TABLE: policies
-- --------------------------------------------------------------------------

CREATE TABLE policies (
    id               SERIAL PRIMARY KEY,
    worker_id        INTEGER        NOT NULL REFERENCES workers(id) ON DELETE CASCADE,
    week_start       DATE           NOT NULL,
    week_end         DATE           NOT NULL,
    risk_score       NUMERIC(5, 4)  NOT NULL,                                 -- 0.0000 – 1.0000 from XGBoost
    base_premium     NUMERIC(8, 2)  NOT NULL,                                 -- INR base before risk adjustment
    weekly_premium   NUMERIC(8, 2)  NOT NULL,                                 -- PHR × base_premium
    daily_max_payout NUMERIC(8, 2)  NOT NULL DEFAULT 500.00,                  -- cap per claim in INR
    status           policy_status_enum NOT NULL DEFAULT 'active',
    created_at       TIMESTAMPTZ    NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_policies_worker_id  ON policies (worker_id);
CREATE INDEX ix_policies_week_start ON policies (week_start);

COMMENT ON COLUMN policies.risk_score       IS 'Predicted disruption risk 0–1 from the XGBoost weekly model.';
COMMENT ON COLUMN policies.weekly_premium   IS 'Computed as risk_score × k × base_premium (PHR formula).';
COMMENT ON COLUMN policies.daily_max_payout IS 'Hard cap on any single claim payout. Default ₹500.';

-- --------------------------------------------------------------------------
-- TABLE: claims
-- --------------------------------------------------------------------------

CREATE TABLE claims (
    id                    SERIAL PRIMARY KEY,
    worker_id             INTEGER              NOT NULL REFERENCES workers(id) ON DELETE CASCADE,
    policy_id             INTEGER              REFERENCES policies(id) ON DELETE SET NULL,
    raw_message           TEXT                 NOT NULL,                         -- original WhatsApp text / voice transcript
    disruption_type       disruption_type_enum NOT NULL,
    claimed_window_start  TIMESTAMPTZ,
    claimed_window_end    TIMESTAMPTZ,
    -- Agent tool outputs stored as JSONB: one key per tool call
    tool_results          JSONB,
    -- {
    --   "shift_verified": true,
    --   "weather": { "rainfall_mm": 62.3, "aqi": null, "temp_c": null },
    --   "gov_feed": { "curfew_active": false },
    --   "policy_rule": { "threshold": 40, "matched": true },
    --   "fraud_history": { "suspicious": false }
    -- }
    anomaly_score         NUMERIC(6, 4),                                        -- Isolation Forest output (higher = more anomalous)
    effective_hours       NUMERIC(4, 2),
    decision              claim_decision_enum  NOT NULL DEFAULT 'pending',
    decision_reason       TEXT,
    smart_receipt_text    TEXT,                                                  -- LLM-generated localized receipt sent via WhatsApp
    created_at            TIMESTAMPTZ          NOT NULL DEFAULT NOW(),
    resolved_at           TIMESTAMPTZ
);

CREATE INDEX ix_claims_worker_id       ON claims (worker_id);
CREATE INDEX ix_claims_disruption_type ON claims (disruption_type);
CREATE INDEX ix_claims_decision        ON claims (decision);
CREATE INDEX ix_claims_created_at      ON claims (created_at);
CREATE INDEX ix_claims_tool_results    ON claims USING GIN (tool_results);      -- fast JSONB queries for analytics

COMMENT ON COLUMN claims.tool_results       IS 'JSONB bag of every agent tool output for this claim (one key per tool).';
COMMENT ON COLUMN claims.anomaly_score      IS 'Isolation Forest score; values above threshold trigger manual_review.';
COMMENT ON COLUMN claims.smart_receipt_text IS 'Localized (Hindi/Marathi/Telugu) Smart Receipt generated by the LLM and sent over WhatsApp.';

-- --------------------------------------------------------------------------
-- TABLE: payouts
-- --------------------------------------------------------------------------

CREATE TABLE payouts (
    id               SERIAL PRIMARY KEY,
    claim_id         INTEGER             NOT NULL UNIQUE REFERENCES claims(id) ON DELETE CASCADE,
    amount           NUMERIC(8, 2)       NOT NULL,                              -- final INR amount credited
    slf              NUMERIC(5, 4),                                             -- Surge Loss Factor (0.0 – 1.0)
    phr              NUMERIC(8, 2),                                             -- Per Hour Rate used in calc
    channel          payout_channel_enum NOT NULL DEFAULT 'razorpay',
    status           payout_status_enum  NOT NULL DEFAULT 'pending',
    external_txn_id  VARCHAR(128),                                              -- Razorpay / UPI reference
    failure_reason   VARCHAR(256),
    initiated_at     TIMESTAMPTZ         NOT NULL DEFAULT NOW(),
    settled_at       TIMESTAMPTZ
);

CREATE INDEX ix_payouts_claim_id ON payouts (claim_id);
CREATE INDEX ix_payouts_status   ON payouts (status);

COMMENT ON TABLE  payouts         IS 'One payout per approved claim. Stores full PHR × SLF × hours breakdown.';
COMMENT ON COLUMN payouts.slf     IS 'Surge Loss Factor applied: payout = PHR × SLF × effective_hours.';
COMMENT ON COLUMN payouts.phr     IS 'Per Hour Rate = risk_score × k × base_premium.';

-- --------------------------------------------------------------------------
-- TRIGGER: auto-update workers.updated_at
-- --------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_workers_updated_at
    BEFORE UPDATE ON workers
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();


INSERT INTO workers (platform, partner_id, phone_number, whatsapp_id, zone, vehicle_type, tier, preferred_language, onboarding_status)
VALUES
    ('zepto',   'ZEP1001', '+919876543210', 'wa_zep1001', 'Koramangala, Bengaluru', 'motorcycle', 'silver', 'hi', 'verified'),
    ('zepto',   'ZEP1002', '+919876543211', 'wa_zep1002', 'Indiranagar, Bengaluru', 'bicycle',    'bronze', 'en', 'verified'),
    ('blinkit', 'BLK2001', '+919876543212', 'wa_blk2001', 'Dwarka, New Delhi',      'motorcycle', 'gold',   'hi', 'verified'),
    ('blinkit', 'BLK2002', '+919876543213', 'wa_blk2002', 'Andheri, Mumbai',        'e-bike',     'silver', 'mr', 'verified');
