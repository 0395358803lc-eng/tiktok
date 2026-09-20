"""Add account and video analytics snapshots."""

import sqlalchemy as sa

from alembic import op

revision = "0007_analytics_snapshots"
down_revision = "0006_tiktok_videos"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "account_stat_snapshots",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "account_id",
            sa.Integer(),
            sa.ForeignKey("tiktok_accounts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("follower_count", sa.BigInteger(), nullable=True),
        sa.Column("following_count", sa.BigInteger(), nullable=True),
        sa.Column("likes_count", sa.BigInteger(), nullable=True),
        sa.Column("video_count", sa.BigInteger(), nullable=True),
    )
    op.create_index(
        "ix_account_stat_snapshots_account_time",
        "account_stat_snapshots",
        ["account_id", "captured_at"],
    )

    op.create_table(
        "video_metric_snapshots",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "video_pk",
            sa.Integer(),
            sa.ForeignKey("tiktok_videos.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("account_id", sa.Integer(), nullable=False),
        sa.Column("video_id", sa.String(length=128), nullable=False),
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("like_count", sa.BigInteger(), nullable=True),
        sa.Column("comment_count", sa.BigInteger(), nullable=True),
        sa.Column("share_count", sa.BigInteger(), nullable=True),
        sa.Column("view_count", sa.BigInteger(), nullable=True),
    )
    op.create_index(
        "ix_video_metric_snapshots_video_time",
        "video_metric_snapshots",
        ["video_pk", "captured_at"],
    )
    op.create_index(
        "ix_video_metric_snapshots_account_time",
        "video_metric_snapshots",
        ["account_id", "captured_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_video_metric_snapshots_account_time",
        table_name="video_metric_snapshots",
    )
    op.drop_index(
        "ix_video_metric_snapshots_video_time",
        table_name="video_metric_snapshots",
    )
    op.drop_table("video_metric_snapshots")
    op.drop_index(
        "ix_account_stat_snapshots_account_time",
        table_name="account_stat_snapshots",
    )
    op.drop_table("account_stat_snapshots")
