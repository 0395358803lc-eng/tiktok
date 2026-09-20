"""Add dynamic OAuth scopes and extended personal profile fields."""

import sqlalchemy as sa

from alembic import op

revision = "0005_personal_profile_scopes"
down_revision = "0004_audit_events"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "oauth_sessions",
        sa.Column("requested_scopes", sa.Text(), nullable=True),
    )

    op.add_column("tiktok_accounts", sa.Column("username", sa.String(length=255), nullable=True))
    op.add_column("tiktok_accounts", sa.Column("bio_description", sa.Text(), nullable=True))
    op.add_column("tiktok_accounts", sa.Column("profile_deep_link", sa.Text(), nullable=True))
    op.add_column("tiktok_accounts", sa.Column("is_verified", sa.Boolean(), nullable=True))
    op.add_column("tiktok_accounts", sa.Column("follower_count", sa.BigInteger(), nullable=True))
    op.add_column("tiktok_accounts", sa.Column("following_count", sa.BigInteger(), nullable=True))
    op.add_column("tiktok_accounts", sa.Column("likes_count", sa.BigInteger(), nullable=True))
    op.add_column("tiktok_accounts", sa.Column("video_count", sa.BigInteger(), nullable=True))


def downgrade() -> None:
    op.drop_column("tiktok_accounts", "video_count")
    op.drop_column("tiktok_accounts", "likes_count")
    op.drop_column("tiktok_accounts", "following_count")
    op.drop_column("tiktok_accounts", "follower_count")
    op.drop_column("tiktok_accounts", "is_verified")
    op.drop_column("tiktok_accounts", "profile_deep_link")
    op.drop_column("tiktok_accounts", "bio_description")
    op.drop_column("tiktok_accounts", "username")
    op.drop_column("oauth_sessions", "requested_scopes")
