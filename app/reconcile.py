from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from .fulfillment.printful import PrintfulClient
from .models import Order
from .orders import mark_paid_and_enqueue, sync_square_pricing
from .payments.square import SquareClient


class ReconciliationError(RuntimeError):
    pass


def _validate_square_amount(order: Order, payment: dict) -> None:
    amount = payment.get("amount_money") or {}
    if amount.get("currency") != order.currency:
        raise ReconciliationError(
            f"Square currency mismatch for {order.order_number}: "
            f"{amount.get('currency')} != {order.currency}"
        )
    if int(amount.get("amount", -1)) != order.total_cents:
        raise ReconciliationError(
            f"Square amount mismatch for {order.order_number}: "
            f"{amount.get('amount')} != {order.total_cents}"
        )


def reconcile_square_order(
    session: Session,
    order: Order,
    *,
    client: SquareClient,
) -> str:
    if not order.square_order_id:
        return "NO_SQUARE_ORDER"

    square_order = client.get_order(order.square_order_id)
    sync_square_pricing(session, order, square_order)
    payment_id = client.payment_id_from_order(square_order)
    if not payment_id:
        return "NO_PAYMENT"

    payment = client.get_payment(payment_id)
    _validate_square_amount(order, payment)
    status = (payment.get("status") or "").upper()

    if status == "COMPLETED":
        mark_paid_and_enqueue(session, order, square_payment_id=payment_id)
        return "PAID"

    if status in {"FAILED", "CANCELED"}:
        order.payment_state = status
        order.order_state = "PAYMENT_FAILED"
        session.commit()
        return status

    if payment_id and not order.square_payment_id:
        order.square_payment_id = payment_id
        session.commit()

    return status or "PENDING"


def reconcile_printful_order(
    session: Session,
    order: Order,
    *,
    client: PrintfulClient,
) -> str:
    data = client.get_order_by_external_id(order.order_number)
    if data is None:
        return "MISSING"

    if data.get("id") is not None:
        order.printful_order_id = str(data["id"])

    status = (data.get("status") or "").upper()
    if status == "FAILED":
        order.fulfillment_state = "FAILED"
        order.order_state = "FULFILLMENT_FAILED"
    elif status == "CANCELED":
        order.fulfillment_state = "CANCELED"
    elif status in {"PENDING", "INREVIEW"}:
        order.fulfillment_state = status
        order.order_state = "IN_PRODUCTION"
    elif status == "DRAFT":
        order.fulfillment_state = "DRAFT"
        if order.order_state == "PAID":
            order.order_state = "FULFILLMENT_SUBMITTED"
    else:
        order.fulfillment_state = status or order.fulfillment_state

    session.commit()
    return status or "UNKNOWN"


def reconcile_orders(
    session: Session,
    *,
    square_client: SquareClient | None = None,
    printful_client: PrintfulClient | None = None,
    limit: int = 100,
) -> dict[str, int]:
    counts = {
        "square_checked": 0,
        "square_errors": 0,
        "printful_checked": 0,
        "printful_errors": 0,
    }

    orders = session.scalars(
        select(Order).order_by(Order.created_at.desc()).limit(limit)
    ).all()

    for order in orders:
        if square_client is not None and order.square_order_id:
            try:
                reconcile_square_order(session, order, client=square_client)
                counts["square_checked"] += 1
            except Exception:
                session.rollback()
                counts["square_errors"] += 1

        if (
            printful_client is not None
            and order.payment_state == "COMPLETED"
            and order.printful_external_id
        ):
            try:
                reconcile_printful_order(session, order, client=printful_client)
                counts["printful_checked"] += 1
            except Exception:
                session.rollback()
                counts["printful_errors"] += 1

    return counts
