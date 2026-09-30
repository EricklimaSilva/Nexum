"""add xp events

Revision ID: f84b9a4d1e2a
Revises: 312364f85d52
Create Date: 2026-09-30 00:00:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "f84b9a4d1e2a"
down_revision = "312364f85d52"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "xp_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("source_type", sa.String(length=50), nullable=False),
        sa.Column("source_id", sa.Integer(), nullable=False),
        sa.Column("delta", sa.Integer(), nullable=False),
        sa.Column("reason", sa.String(length=200), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_xp_events_user_id_users"),
        sa.PrimaryKeyConstraint("id", name="pk_xp_events"),
        sa.CheckConstraint("delta > 0", name="ck_xp_event_delta_positive"),
        sa.UniqueConstraint("user_id", "source_type", "source_id", name="uq_xp_event_user_source"),
    )
    op.create_index("ix_xp_event_user_created_at", "xp_events", ["user_id", "created_at"], unique=False)
    op.create_index("ix_xp_events_user_id", "xp_events", ["user_id"], unique=False)


def downgrade():
    op.drop_index("ix_xp_events_user_id", table_name="xp_events")
    op.drop_index("ix_xp_event_user_created_at", table_name="xp_events")
    op.drop_table("xp_events")
