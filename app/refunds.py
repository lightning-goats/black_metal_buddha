from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import Order, Refund
from .orders import enqueue_job
from .payments.square import SquareClient


class RefundError(ValueError):
    pass


def apply_refund_status(
    session: Session,
    refund: Refund,
    order: Order,
    *,
    status: str,
) -> None:
    status = status.upper()
    previously_completed = refund.status == "COMPLETED"
    refund.status = status

    if status == "COMPLETED" and not previously_completed:
        order.refunded_cents += refund.amount_cents
        if order.refunded_cents >= order.total_cents:
            order.refund_state = "COMPLETED"
            order.order_state = "REFUNDED"
        else:
            order.refund_state = "PARTIAL"
        enqueue_job(session, order, "SEND_REFUND_CONFIRMATION")
    elif status == "FAILED":
        order.refund_state = "FAILED"
    elif status in {"PENDING", "APPROVED"}:
        order.refund_state = "PENDING"

    session.commit()


def request_refund(
    session: Session,
    order: Order,
    *,
    amount_cents: int | None,
    reason: str,
    client: SquareClient,
) -> Refund:
    if order.payment_state != "COMPLETED" or not order.square_payment_id:
        raise RefundError("Only completed Square payments can be refunded")

    remaining = order.total_cents - order.refunded_cents
    if remaining <= 0:
        raise RefundError("Order is already fully refunded")

    amount = remaining if amount_cents is None else amount_cents
    if amount <= 0 or amount > remaining:
        raise RefundError("Refund amount exceeds the refundable balance")

    existing_count = len(
        session.scalars(select(Refund).where(Refund.order_id == order.id)).all()
    )
    idempotency_key = f"refund-{order.order_number}-{existing_count + 1}"

    data = client.refund_payment(
        payment_id=order.square_payment_id,
        amount_cents=amount,
        currency=order.currency,
        reason=reason,
        idempotency_key=idempotency_key,
    )

    refund = Refund(
        order_id=order.id,
        square_refund_id=str(data["id"]),
        amount_cents=amount,
        currency=order.currency,
        status=str(data["status"]).upper(),
        reason=reason,
    )
    session.add(refund)
    session.flush()
    apply_refund_status(session, refund, order, status=refund.status)
    return refund


def get_refund_by_square_id(session: Session, square_refund_id: str) -> Refund | None:
    return session.scalar(
        select(Refund).where(Refund.square_refund_id == square_refund_id)
    )
