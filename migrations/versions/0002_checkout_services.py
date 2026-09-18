"""Add checkout services: shipping/refunds."""

from alembic import op
import sqlalchemy as sa

revision = "0002_checkout_services"
down_revision = "0001_phase1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("orders", sa.Column("shipping_method", sa.String(64), nullable=True))
    op.add_column("orders", sa.Column("shipping_quoted_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("orders", sa.Column("refunded_cents", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("orders", sa.Column("refund_state", sa.String(32), nullable=False, server_default="NONE"))

    op.create_table(
        "refunds",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("order_id", sa.String(36), sa.ForeignKey("orders.id", ondelete="CASCADE"), nullable=False),
        sa.Column("square_refund_id", sa.String(128), nullable=False),
        sa.Column("amount_cents", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("reason", sa.String(192), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("square_refund_id"),
    )
    op.create_index("ix_refunds_order_id", "refunds", ["order_id"])
    op.create_index("ix_refunds_square_refund_id", "refunds", ["square_refund_id"])


def downgrade() -> None:
    op.drop_table("refunds")
    op.drop_column("orders", "refund_state")
    op.drop_column("orders", "refunded_cents")
    op.drop_column("orders", "shipping_quoted_at")
    op.drop_column("orders", "shipping_method")
