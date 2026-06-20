"""Initial schema: workers, sessions, policies, claims, payouts.

Revision ID: 0001
Revises: 
Create Date: 2026-06-16
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── Enum types ────────────────────────────────────────────────────────────
    platform_enum = postgresql.ENUM(
        "zepto", "blinkit", name="platform_enum", create_type=False
    )
    onboarding_status_enum = postgresql.ENUM(
        "pending_platform", "pending_partner_id", "pending_phone",
        "pending_otp", "verified",
        name="onboarding_status_enum", create_type=False,
    )
    policy_status_enum = postgresql.ENUM(
        "active", "expired", "cancelled", name="policy_status_enum", create_type=False
    )
    disruption_type_enum = postgresql.ENUM(
        "heavy_rain", "flood", "extreme_heat", "severe_aqi",
        "cyclone", "curfew_section_144", "unknown",
        name="disruption_type_enum", create_type=False,
    )
    claim_decision_enum = postgresql.ENUM(
        "approved", "denied", "manual_review", "pending",
        name="claim_decision_enum", create_type=False,
    )
    payout_status_enum = postgresql.ENUM(
        "pending", "processing", "success", "failed",
        name="payout_status_enum", create_type=False,
    )
    payout_channel_enum = postgresql.ENUM(
        "razorpay", "upi", "wallet", name="payout_channel_enum", create_type=False
    )

    for e in [
        platform_enum, onboarding_status_enum, policy_status_enum,
        disruption_type_enum, claim_decision_enum,
        payout_status_enum, payout_channel_enum,
    ]:
        e.create(op.get_bind(), checkfirst=True)

    # ── workers ───────────────────────────────────────────────────────────────
    op.create_table(
        "workers",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("platform", sa.Enum(name="platform_enum"), nullable=False),
        sa.Column("partner_id", sa.String(64), nullable=False),
        sa.Column("phone_number", sa.String(15), nullable=False, unique=True),
        sa.Column("whatsapp_id", sa.String(32), nullable=False, unique=True),
        sa.Column("zone", sa.String(128), nullable=False),
        sa.Column("vehicle_type", sa.String(32), nullable=True),
        sa.Column("tier", sa.String(16), nullable=True),
        sa.Column("preferred_language", sa.String(8), server_default="en"),
        sa.Column("onboarding_status", sa.Enum(name="onboarding_status_enum"),
                  server_default="pending_platform"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_workers_phone_number", "workers", ["phone_number"])
    op.create_index("ix_workers_whatsapp_id", "workers", ["whatsapp_id"])
    op.create_index("ix_workers_partner_id", "workers", ["partner_id"])

    # ── sessions ──────────────────────────────────────────────────────────────
    op.create_table(
        "sessions",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("whatsapp_id", sa.String(32), nullable=False, unique=True),
        sa.Column("worker_id", sa.Integer,
                  sa.ForeignKey("workers.id", ondelete="CASCADE"), nullable=True),
        sa.Column("is_active", sa.Boolean, server_default="false"),
        sa.Column("pending_otp_hash", sa.String(128), nullable=True),
        sa.Column("otp_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("otp_attempts", sa.Integer, server_default="0"),
        sa.Column("onboarding_step", sa.String(32), server_default="pending_platform"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("last_active_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("invalidated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_sessions_whatsapp_id", "sessions", ["whatsapp_id"])

    # ── policies ──────────────────────────────────────────────────────────────
    op.create_table(
        "policies",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("worker_id", sa.Integer,
                  sa.ForeignKey("workers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("week_start", sa.Date, nullable=False),
        sa.Column("week_end", sa.Date, nullable=False),
        sa.Column("risk_score", sa.Numeric(5, 4), nullable=False),
        sa.Column("base_premium", sa.Numeric(8, 2), nullable=False),
        sa.Column("weekly_premium", sa.Numeric(8, 2), nullable=False),
        sa.Column("daily_max_payout", sa.Numeric(8, 2), server_default="500.00"),
        sa.Column("status", sa.Enum(name="policy_status_enum"), server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_policies_worker_id", "policies", ["worker_id"])
    op.create_index("ix_policies_week_start", "policies", ["week_start"])

    # ── claims ────────────────────────────────────────────────────────────────
    op.create_table(
        "claims",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("worker_id", sa.Integer,
                  sa.ForeignKey("workers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("policy_id", sa.Integer,
                  sa.ForeignKey("policies.id", ondelete="SET NULL"), nullable=True),
        sa.Column("raw_message", sa.Text, nullable=False),
        sa.Column("disruption_type", sa.Enum(name="disruption_type_enum"), nullable=False),
        sa.Column("claimed_window_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("claimed_window_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("tool_results", postgresql.JSONB, nullable=True),
        sa.Column("anomaly_score", sa.Numeric(6, 4), nullable=True),
        sa.Column("effective_hours", sa.Numeric(4, 2), nullable=True),
        sa.Column("decision", sa.Enum(name="claim_decision_enum"), server_default="pending"),
        sa.Column("decision_reason", sa.Text, nullable=True),
        sa.Column("smart_receipt_text", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_claims_worker_id", "claims", ["worker_id"])
    op.create_index("ix_claims_disruption_type", "claims", ["disruption_type"])
    op.create_index("ix_claims_decision", "claims", ["decision"])
    op.create_index("ix_claims_created_at", "claims", ["created_at"])

    # ── payouts ───────────────────────────────────────────────────────────────
    op.create_table(
        "payouts",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("claim_id", sa.Integer,
                  sa.ForeignKey("claims.id", ondelete="CASCADE"),
                  nullable=False, unique=True),
        sa.Column("amount", sa.Numeric(8, 2), nullable=False),
        sa.Column("slf", sa.Numeric(5, 4), nullable=True),
        sa.Column("phr", sa.Numeric(8, 2), nullable=True),
        sa.Column("channel", sa.Enum(name="payout_channel_enum"), server_default="razorpay"),
        sa.Column("status", sa.Enum(name="payout_status_enum"), server_default="pending"),
        sa.Column("external_txn_id", sa.String(128), nullable=True),
        sa.Column("failure_reason", sa.String(256), nullable=True),
        sa.Column("initiated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("settled_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_payouts_claim_id", "payouts", ["claim_id"])
    op.create_index("ix_payouts_status", "payouts", ["status"])


def downgrade() -> None:
    op.drop_table("payouts")
    op.drop_table("claims")
    op.drop_table("policies")
    op.drop_table("sessions")
    op.drop_table("workers")

    for enum_name in [
        "platform_enum", "onboarding_status_enum", "policy_status_enum",
        "disruption_type_enum", "claim_decision_enum",
        "payout_status_enum", "payout_channel_enum",
    ]:
        op.execute(f"DROP TYPE IF EXISTS {enum_name}")
