"""Add publishing scheduler and queue state."""

import sqlalchemy as sa

from alembic import op

revision = "0011_publish_scheduler"
down_revision = "0010_tiktok_webhooks"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "tiktok_publish_jobs",
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "tiktok_publish_jobs",
        sa.Column(
            "schedule_status",
            sa.String(length=24),
            nullable=False,
            server_default="READY",
        ),
    )
    op.add_column(
        "tiktok_publish_jobs",
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "tiktok_publish_jobs",
        sa.Column("max_retries", sa.Integer(), nullable=False, server_default="2"),
    )
    op.add_column(
        "tiktok_publish_jobs",
        sa.Column("next_attempt_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "tiktok_publish_jobs",
        sa.Column("last_attempt_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "tiktok_publish_jobs",
        sa.Column("canceled_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.execute(
        """
        UPDATE tiktok_publish_jobs
        SET schedule_status = CASE
            WHEN status = 'PUBLISH_COMPLETE' THEN 'COMPLETED'
            WHEN status = 'FAILED' THEN 'FAILED'
            WHEN publish_id IS NOT NULL THEN 'RUNNING'
            ELSE 'READY'
        END
        """
    )

    op.create_index(
        "ix_tiktok_publish_jobs_schedule_status",
        "tiktok_publish_jobs",
        ["schedule_status"],
    )
    op.create_index(
        "ix_tiktok_publish_jobs_scheduled_at",
        "tiktok_publish_jobs",
        ["scheduled_at"],
    )
    op.create_index(
        "ix_tiktok_publish_jobs_next_attempt_at",
        "tiktok_publish_jobs",
        ["next_attempt_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_tiktok_publish_jobs_next_attempt_at",
        table_name="tiktok_publish_jobs",
    )
    op.drop_index(
        "ix_tiktok_publish_jobs_scheduled_at",
        table_name="tiktok_publish_jobs",
    )
    op.drop_index(
        "ix_tiktok_publish_jobs_schedule_status",
        table_name="tiktok_publish_jobs",
    )
    op.drop_column("tiktok_publish_jobs", "canceled_at")
    op.drop_column("tiktok_publish_jobs", "last_attempt_at")
    op.drop_column("tiktok_publish_jobs", "next_attempt_at")
    op.drop_column("tiktok_publish_jobs", "max_retries")
    op.drop_column("tiktok_publish_jobs", "retry_count")
    op.drop_column("tiktok_publish_jobs", "schedule_status")
    op.drop_column("tiktok_publish_jobs", "scheduled_at")
