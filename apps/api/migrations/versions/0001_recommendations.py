"""Persist the manual daily action and its versioned context/decision."""

import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "recommendations",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(255), nullable=False),
        sa.Column("local_date", sa.Date(), nullable=False),
        sa.Column("context", sa.JSON(), nullable=False),
        sa.Column("decision", sa.JSON(), nullable=False),
        sa.Column("feedback", sa.JSON(), nullable=True),
        sa.UniqueConstraint("user_id", "local_date"),
    )
    op.create_index("ix_recommendations_user_id", "recommendations", ["user_id"])


def downgrade():
    op.drop_table("recommendations")
