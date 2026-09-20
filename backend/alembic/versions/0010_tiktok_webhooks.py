"""Add idempotent TikTok webhook event ingestion."""

import sqlalchemy as sa

from alembic import op

revision = "0010_tiktok_webhooks"
down_revision = "0009_direct_post"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "tiktok_webhook_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("dedup_hash", sa.String(length=64), nullable=False, unique=True),
        sa.Column("client_key", sa.String(length=255), nullable=False),
        sa.Column("event_type", sa.String(length=100), nullable=False),
        sa.Column("user_open_id", sa.String(length=128), nullable=True),
        sa.Column("event_created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("content_json", sa.Text(), nullable=False),
        sa.Column("signature_timestamp", sa.BigInteger(), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_detail", sa.Text(), nullable=True),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_tiktok_webhook_events_status",
        "tiktok_webhook_events",
        ["status"],
    )
    op.create_index(
        "ix_tiktok_webhook_events_event_type",
        "tiktok_webhook_events",
        ["event_type"],
    )
    op.create_index(
        "ix_tiktok_webhook_events_received_at",
        "tiktok_webhook_events",
        ["received_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_tiktok_webhook_events_received_at",
        table_name="tiktok_webhook_events",
    )
    op.drop_index(
        "ix_tiktok_webhook_events_event_type",
        table_name="tiktok_webhook_events",
    )
    op.drop_index(
        "ix_tiktok_webhook_events_status",
        table_name="tiktok_webhook_events",
    )
    op.drop_table("tiktok_webhook_events")
