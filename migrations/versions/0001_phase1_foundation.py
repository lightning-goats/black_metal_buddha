"""Phase 1 order/payment/fulfillment foundation."""

from alembic import op
import sqlalchemy as sa

revision = "0001_phase1"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "product_variants",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("product_slug", sa.String(128), nullable=False),
        sa.Column("sku", sa.String(128), nullable=False),
        sa.Column("size", sa.String(32), nullable=False),
        sa.Column("color", sa.String(64), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("retail_price_cents", sa.Integer(), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("sellable", sa.Boolean(), nullable=False),
        sa.Column("printful_product_id", sa.String(128), nullable=True),
        sa.Column("printful_variant_id", sa.String(128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("sku"),
    )
    op.create_index("ix_product_variants_product_slug", "product_variants", ["product_slug"])
    op.create_index("ix_product_variants_sku", "product_variants", ["sku"])

    op.create_table(
        "orders",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("order_number", sa.String(32), nullable=False),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("customer_name", sa.String(200), nullable=False),
        sa.Column("phone", sa.String(64), nullable=True),
        sa.Column("ship_address1", sa.String(255), nullable=False),
        sa.Column("ship_address2", sa.String(255), nullable=True),
        sa.Column("ship_city", sa.String(128), nullable=False),
        sa.Column("ship_state", sa.String(128), nullable=False),
        sa.Column("ship_postal_code", sa.String(32), nullable=False),
        sa.Column("ship_country", sa.String(2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("subtotal_cents", sa.Integer(), nullable=False),
        sa.Column("discount_cents", sa.Integer(), nullable=False),
        sa.Column("shipping_cents", sa.Integer(), nullable=False),
        sa.Column("tax_cents", sa.Integer(), nullable=False),
        sa.Column("total_cents", sa.Integer(), nullable=False),
        sa.Column("payment_state", sa.String(32), nullable=False),
        sa.Column("fulfillment_state", sa.String(32), nullable=False),
        sa.Column("order_state", sa.String(32), nullable=False),
        sa.Column("square_payment_link_id", sa.String(128), nullable=True),
        sa.Column("square_checkout_url", sa.String(1024), nullable=True),
        sa.Column("square_order_id", sa.String(128), nullable=True),
        sa.Column("square_payment_id", sa.String(128), nullable=True),
        sa.Column("printful_order_id", sa.String(128), nullable=True),
        sa.Column("printful_external_id", sa.String(64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("submitted_to_printful_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("shipped_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("order_number"),
        sa.UniqueConstraint("square_order_id"),
        sa.UniqueConstraint("square_payment_id"),
    )
    op.create_index("ix_orders_order_number", "orders", ["order_number"])

    op.create_table(
        "order_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("order_id", sa.String(36), sa.ForeignKey("orders.id", ondelete="CASCADE"), nullable=False),
        sa.Column("product_variant_id", sa.Integer(), sa.ForeignKey("product_variants.id"), nullable=False),
        sa.Column("sku_snapshot", sa.String(128), nullable=False),
        sa.Column("name_snapshot", sa.String(200), nullable=False),
        sa.Column("size_snapshot", sa.String(32), nullable=False),
        sa.Column("color_snapshot", sa.String(64), nullable=False),
        sa.Column("unit_price_cents", sa.Integer(), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("line_total_cents", sa.Integer(), nullable=False),
        sa.Column("printful_product_id_snapshot", sa.String(128), nullable=True),
        sa.Column("printful_variant_id_snapshot", sa.String(128), nullable=True),
    )
    op.create_index("ix_order_items_order_id", "order_items", ["order_id"])

    op.create_table(
        "payment_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("provider", sa.String(32), nullable=False),
        sa.Column("provider_event_id", sa.String(128), nullable=False),
        sa.Column("provider_payment_id", sa.String(128), nullable=True),
        sa.Column("event_type", sa.String(128), nullable=False),
        sa.Column("event_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("payload_hash", sa.String(64), nullable=False),
        sa.Column("processing_result", sa.String(64), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("provider", "provider_event_id"),
    )

    op.create_table(
        "fulfillment_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("provider", sa.String(32), nullable=False),
        sa.Column("provider_event_id", sa.String(128), nullable=False),
        sa.Column("provider_order_id", sa.String(128), nullable=True),
        sa.Column("event_type", sa.String(128), nullable=False),
        sa.Column("payload_hash", sa.String(64), nullable=False),
        sa.Column("processing_result", sa.String(64), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("provider", "provider_event_id"),
    )

    op.create_table(
        "jobs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("job_type", sa.String(64), nullable=False),
        sa.Column("order_id", sa.String(36), sa.ForeignKey("orders.id", ondelete="CASCADE"), nullable=False),
        sa.Column("state", sa.String(32), nullable=False),
        sa.Column("attempt_count", sa.Integer(), nullable=False),
        sa.Column("next_attempt_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("locked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("job_type", "order_id"),
    )
    op.create_index("ix_jobs_job_type", "jobs", ["job_type"])
    op.create_index("ix_jobs_order_id", "jobs", ["order_id"])
    op.create_index("ix_jobs_state", "jobs", ["state"])


def downgrade() -> None:
    op.drop_table("jobs")
    op.drop_table("fulfillment_events")
    op.drop_table("payment_events")
    op.drop_table("order_items")
    op.drop_table("orders")
    op.drop_table("product_variants")
