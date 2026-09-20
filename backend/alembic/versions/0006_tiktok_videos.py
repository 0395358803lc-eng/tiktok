"""Add TikTok video library."""

import sqlalchemy as sa

from alembic import op

revision = "0006_tiktok_videos"
down_revision = "0005_personal_profile_scopes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "tiktok_videos",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "account_id",
            sa.Integer(),
            sa.ForeignKey("tiktok_accounts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("video_id", sa.String(length=128), nullable=False),
        sa.Column("create_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cover_image_url", sa.Text(), nullable=True),
        sa.Column("share_url", sa.Text(), nullable=True),
        sa.Column("video_description", sa.Text(), nullable=True),
        sa.Column("duration", sa.Integer(), nullable=True),
        sa.Column("height", sa.Integer(), nullable=True),
        sa.Column("width", sa.Integer(), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=True),
        sa.Column("embed_link", sa.Text(), nullable=True),
        sa.Column("like_count", sa.BigInteger(), nullable=True),
        sa.Column("comment_count", sa.BigInteger(), nullable=True),
        sa.Column("share_count", sa.BigInteger(), nullable=True),
        sa.Column("view_count", sa.BigInteger(), nullable=True),
        sa.Column("is_aigc", sa.Boolean(), nullable=True),
        sa.Column("synced_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("account_id", "video_id", name="uq_tiktok_video_account_video"),
    )
    op.create_index("ix_tiktok_videos_account_id", "tiktok_videos", ["account_id"])
    op.create_index("ix_tiktok_videos_video_id", "tiktok_videos", ["video_id"])
    op.create_index("ix_tiktok_videos_create_time", "tiktok_videos", ["create_time"])


def downgrade() -> None:
    op.drop_index("ix_tiktok_videos_create_time", table_name="tiktok_videos")
    op.drop_index("ix_tiktok_videos_video_id", table_name="tiktok_videos")
    op.drop_index("ix_tiktok_videos_account_id", table_name="tiktok_videos")
    op.drop_table("tiktok_videos")
