"""Add durable shipment tracking."""

from alembic import op
import sqlalchemy as sa

revision = "0003_shipments"
down_revision = "0002_checkout_services"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "shipments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("order_id", sa.String(36), sa.ForeignKey("orders.id", ondelete="CASCADE"), nullable=False),
        sa.Column("printful_shipment_id", sa.String(128), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("tracking_number", sa.String(256), nullable=True),
        sa.Column("tracking_url", sa.String(2048), nullable=True),
        sa.Column("reshipment", sa.Boolean(), nullable=False),
        sa.Column("shipped_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("returned_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("printful_shipment_id"),
    )
    op.create_index("ix_shipments_order_id", "shipments", ["order_id"])
    op.create_index("ix_shipments_printful_shipment_id", "shipments", ["printful_shipment_id"])


def downgrade() -> None:
    op.drop_table("shipments")
