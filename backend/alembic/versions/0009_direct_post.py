"""Add Direct Post jobs and media duration metadata."""

import sqlalchemy as sa

from alembic import op

revision = "0009_direct_post"
down_revision = "0008_draft_uploads"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "media_assets",
        sa.Column("duration_seconds", sa.Float(), nullable=True),
    )

    op.create_table(
        "tiktok_publish_jobs",
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
        sa.Column("title", sa.Text(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("privacy_level", sa.String(length=40), nullable=False),
        sa.Column("disable_comment", sa.Boolean(), nullable=False),
        sa.Column("disable_duet", sa.Boolean(), nullable=False),
        sa.Column("disable_stitch", sa.Boolean(), nullable=False),
        sa.Column("auto_add_music", sa.Boolean(), nullable=False),
        sa.Column("brand_content_toggle", sa.Boolean(), nullable=False),
        sa.Column("brand_organic_toggle", sa.Boolean(), nullable=False),
        sa.Column("is_aigc", sa.Boolean(), nullable=False),
        sa.Column("video_cover_timestamp_ms", sa.Integer(), nullable=True),
        sa.Column("consent_music_usage", sa.Boolean(), nullable=False),
        sa.Column("consent_branded_policy", sa.Boolean(), nullable=False),
        sa.Column("creator_info_json", sa.Text(), nullable=False),
        sa.Column("publish_id", sa.String(length=128), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("fail_reason", sa.Text(), nullable=True),
        sa.Column("uploaded_bytes", sa.BigInteger(), nullable=True),
        sa.Column("downloaded_bytes", sa.BigInteger(), nullable=True),
        sa.Column("public_post_ids", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_tiktok_publish_jobs_account_id", "tiktok_publish_jobs", ["account_id"])
    op.create_index("ix_tiktok_publish_jobs_status", "tiktok_publish_jobs", ["status"])
    op.create_index("ix_tiktok_publish_jobs_publish_id", "tiktok_publish_jobs", ["publish_id"])


def downgrade() -> None:
    op.drop_index("ix_tiktok_publish_jobs_publish_id", table_name="tiktok_publish_jobs")
    op.drop_index("ix_tiktok_publish_jobs_status", table_name="tiktok_publish_jobs")
    op.drop_index("ix_tiktok_publish_jobs_account_id", table_name="tiktok_publish_jobs")
    op.drop_table("tiktok_publish_jobs")
    op.drop_column("media_assets", "duration_seconds")
