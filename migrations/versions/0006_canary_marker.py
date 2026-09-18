"""Add production canary order marker."""

from alembic import op
import sqlalchemy as sa

revision = "0006_canary_marker"
down_revision = "0005_audit_log"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "orders",
        sa.Column("is_canary", sa.Boolean(), nullable=False, server_default=sa.false()),
    )


def downgrade() -> None:
    op.drop_column("orders", "is_canary")
