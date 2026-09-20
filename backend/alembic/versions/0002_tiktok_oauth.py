"""Add TikTok OAuth sessions and accounts."""

import sqlalchemy as sa

from alembic import op

revision = "0002_tiktok_oauth"
down_revision = "0001_admin_sessions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "oauth_sessions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("state_hash", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_oauth_sessions_state_hash", "oauth_sessions", ["state_hash"], unique=True)
    op.create_index("ix_oauth_sessions_expires_at", "oauth_sessions", ["expires_at"])

    op.create_table(
        "tiktok_accounts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("open_id", sa.String(length=128), nullable=False),
        sa.Column("scopes", sa.Text(), nullable=False, server_default=""),
        sa.Column("access_token_enc", sa.Text(), nullable=False),
        sa.Column("refresh_token_enc", sa.Text(), nullable=False),
        sa.Column("access_token_expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("refresh_token_expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="CONNECTED"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_token_refresh_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_tiktok_accounts_open_id", "tiktok_accounts", ["open_id"], unique=True)
    op.create_index("ix_tiktok_accounts_status", "tiktok_accounts", ["status"])


def downgrade() -> None:
    op.drop_index("ix_tiktok_accounts_status", table_name="tiktok_accounts")
    op.drop_index("ix_tiktok_accounts_open_id", table_name="tiktok_accounts")
    op.drop_table("tiktok_accounts")
    op.drop_index("ix_oauth_sessions_expires_at", table_name="oauth_sessions")
    op.drop_index("ix_oauth_sessions_state_hash", table_name="oauth_sessions")
    op.drop_table("oauth_sessions")
