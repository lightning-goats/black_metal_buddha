"""Add Printful cost and confirmation state."""

from alembic import op
import sqlalchemy as sa

revision = "0004_printful_confirmation"
down_revision = "0003_shipments"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("orders", sa.Column("printful_cost_cents", sa.Integer(), nullable=True))
    op.add_column("orders", sa.Column("printful_cost_currency", sa.String(3), nullable=True))
    op.add_column("orders", sa.Column("printful_cost_status", sa.String(32), nullable=True))
    op.add_column("orders", sa.Column("printful_confirmed_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("orders", "printful_confirmed_at")
    op.drop_column("orders", "printful_cost_status")
    op.drop_column("orders", "printful_cost_currency")
    op.drop_column("orders", "printful_cost_cents")
