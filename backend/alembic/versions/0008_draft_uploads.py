"""Add local media assets and TikTok draft upload jobs."""

import sqlalchemy as sa

from alembic import op

revision = "0008_draft_uploads"
down_revision = "0007_analytics_snapshots"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "media_assets",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("kind", sa.String(length=16), nullable=False),
        sa.Column("original_name", sa.String(length=255), nullable=False),
        sa.Column("stored_name", sa.String(length=255), nullable=False, unique=True),
        sa.Column("mime_type", sa.String(length=100), nullable=False),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("sha256", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "tiktok_draft_jobs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "account_id",
            sa.Integer(),
            sa.ForeignKey("tiktok_accounts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "media_asset_id",
            sa.Integer(),
            sa.ForeignKey("media_assets.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("media_type", sa.String(length=16), nullable=False),
        sa.Column("source_type", sa.String(length=32), nullable=False),
        sa.Column("source_json", sa.Text(), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("publish_id", sa.String(length=128), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("fail_reason", sa.Text(), nullable=True),
        sa.Column("uploaded_bytes", sa.BigInteger(), nullable=True),
        sa.Column("downloaded_bytes", sa.BigInteger(), nullable=True),
        sa.Column("public_post_ids", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_tiktok_draft_jobs_account_id", "tiktok_draft_jobs", ["account_id"])
    op.create_index("ix_tiktok_draft_jobs_status", "tiktok_draft_jobs", ["status"])
    op.create_index("ix_tiktok_draft_jobs_publish_id", "tiktok_draft_jobs", ["publish_id"])


def downgrade() -> None:
    op.drop_index("ix_tiktok_draft_jobs_publish_id", table_name="tiktok_draft_jobs")
    op.drop_index("ix_tiktok_draft_jobs_status", table_name="tiktok_draft_jobs")
    op.drop_index("ix_tiktok_draft_jobs_account_id", table_name="tiktok_draft_jobs")
    op.drop_table("tiktok_draft_jobs")
    op.drop_table("media_assets")
