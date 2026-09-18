from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .catalog import PRODUCT_BY_SLUG
from .models import Job, Order, OrderItem, ProductVariant
from .schemas import CreateOrderIn


class OrderError(ValueError):
    pass


def new_order_number() -> str:
    return f"BMB-{uuid4().hex[:12].upper()}"


def create_order(session: Session, data: CreateOrderIn) -> Order:
    order_id = str(uuid4())
    order_number = new_order_number()
    items: list[OrderItem] = []
    subtotal = 0
    currency: str | None = None

    for line in data.items:
        variant = session.scalar(
            select(ProductVariant).where(
                ProductVariant.sku == line.sku,
                ProductVariant.active.is_(True),
                ProductVariant.sellable.is_(True),
            )
        )
        if variant is None or variant.retail_price_cents is None:
            raise OrderError(f"SKU is not currently sellable: {line.sku}")

        product = PRODUCT_BY_SLUG.get(variant.product_slug)
        if product is None:
            raise OrderError(f"Unknown product for SKU: {line.sku}")

        if currency is None:
            currency = variant.currency
        if currency != variant.currency:
            raise OrderError("Mixed-currency orders are not supported")

        line_total = variant.retail_price_cents * line.quantity
        subtotal += line_total
        items.append(
            OrderItem(
                order_id=order_id,
                product_variant_id=variant.id,
                sku_snapshot=variant.sku,
                name_snapshot=product.name,
                size_snapshot=variant.size,
                color_snapshot=variant.color,
                unit_price_cents=variant.retail_price_cents,
                quantity=line.quantity,
                line_total_cents=line_total,
                printful_product_id_snapshot=variant.printful_product_id,
                printful_variant_id_snapshot=variant.printful_variant_id,
            )
        )

    # Shipping/tax remain zero in this backend-foundation slice.
    # Public checkout must not be enabled until server-side shipping/tax
    # calculation is implemented and validated.
    shipping_cents = 0
    tax_cents = 0
    discount_cents = 0
    total = subtotal - discount_cents + shipping_cents + tax_cents

    order = Order(
        id=order_id,
        order_number=order_number,
        email=str(data.recipient.email),
        customer_name=data.recipient.name,
        phone=data.recipient.phone,
        ship_address1=data.recipient.address1,
        ship_address2=data.recipient.address2,
        ship_city=data.recipient.city,
        ship_state=data.recipient.state,
        ship_postal_code=data.recipient.postal_code,
        ship_country=data.recipient.country_code.upper(),
        currency=currency or "USD",
        subtotal_cents=subtotal,
        discount_cents=discount_cents,
        shipping_cents=shipping_cents,
        tax_cents=tax_cents,
        total_cents=total,
        printful_external_id=order_number,
        items=items,
    )
    session.add(order)
    session.commit()
    session.refresh(order)
    return order


def get_order(session: Session, order_number: str) -> Order | None:
    return session.scalar(select(Order).where(Order.order_number == order_number))


def get_order_by_square_order_id(session: Session, square_order_id: str) -> Order | None:
    return session.scalar(select(Order).where(Order.square_order_id == square_order_id))


def set_square_checkout(
    session: Session,
    order: Order,
    *,
    payment_link_id: str,
    square_order_id: str,
    checkout_url: str,
) -> None:
    if order.order_state != "PENDING_PAYMENT":
        raise OrderError("Square checkout can only be attached to a pending order")
    order.square_payment_link_id = payment_link_id
    order.square_order_id = square_order_id
    order.square_checkout_url = checkout_url
    session.commit()


def mark_paid_and_enqueue(
    session: Session,
    order: Order,
    *,
    square_payment_id: str,
) -> bool:
    if order.payment_state == "COMPLETED":
        return False

    order.payment_state = "COMPLETED"
    order.order_state = "PAID"
    order.square_payment_id = square_payment_id
    order.paid_at = datetime.now(timezone.utc)
    session.add(Job(job_type="SUBMIT_PRINTFUL_ORDER", order_id=order.id, state="PENDING"))

    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        current = get_order(session, order.order_number)
        if current is not None and current.payment_state == "COMPLETED":
            return False
        raise
    return True
