from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from .db import SessionLocal
from .fulfillment.printful import PrintfulClient, verify_printful_webhook
from .models import FulfillmentEvent, Order, PaymentEvent
from .orders import (
    OrderError,
    create_order,
    enqueue_job,
    get_order,
    get_order_by_square_order_id,
    mark_paid_and_enqueue,
    set_shipping_rate,
    set_square_checkout,
    shipping_quote_is_fresh,
    sync_square_pricing,
)
from .payments.square import SquareClient, verify_square_webhook
from .refunds import apply_refund_status, get_refund_by_square_id
from .schemas import CatalogVariantOut, CreateOrderIn, OrderOut, SelectShippingIn, ShippingRateOut
from .settings import settings
from .storefront import sellable_catalog
from .shipments import upsert_printful_shipment

router = APIRouter(prefix="/api/v1", tags=["phase1"])


def db_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def _require_phase1() -> None:
    if not settings.phase1_api_enabled:
        raise HTTPException(status_code=503, detail="Phase 1 API is disabled")


def _get_order_or_404(session: Session, order_number: str) -> Order:
    order = get_order(session, order_number)
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


def _order_out(order: Order, checkout_url: str | None = None) -> OrderOut:
    return OrderOut(
        order_number=order.order_number,
        order_state=order.order_state,
        payment_state=order.payment_state,
        fulfillment_state=order.fulfillment_state,
        currency=order.currency,
        subtotal_cents=order.subtotal_cents,
        discount_cents=order.discount_cents,
        shipping_cents=order.shipping_cents,
        shipping_method=order.shipping_method,
        tax_cents=order.tax_cents,
        total_cents=order.total_cents,
        refunded_cents=order.refunded_cents,
        refund_state=order.refund_state,
        square_checkout_url=checkout_url or order.square_checkout_url,
    )


@router.get("/catalog", response_model=list[CatalogVariantOut])
def api_catalog(session: Session = Depends(db_session)):
    _require_phase1()
    return [
        CatalogVariantOut(
            sku=item.sku,
            product_slug=item.product_slug,
            product_name=item.product_name,
            size=item.size,
            color=item.color,
            currency=item.currency,
            retail_price_cents=item.retail_price_cents,
        )
        for item in sellable_catalog(session)
    ]


@router.post("/orders", response_model=OrderOut)
def api_create_order(data: CreateOrderIn, session: Session = Depends(db_session)):
    _require_phase1()
    try:
        order = create_order(session, data)
    except OrderError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _order_out(order)


@router.get("/orders/{order_number}", response_model=OrderOut)
def api_get_order(order_number: str, session: Session = Depends(db_session)):
    _require_phase1()
    return _order_out(_get_order_or_404(session, order_number))


@router.get(
    "/orders/{order_number}/shipping-rates",
    response_model=list[ShippingRateOut],
)
def api_shipping_rates(order_number: str, session: Session = Depends(db_session)):
    _require_phase1()
    order = _get_order_or_404(session, order_number)
    if order.square_payment_link_id:
        raise HTTPException(status_code=409, detail="Checkout already created")

    try:
        rates = PrintfulClient().get_shipping_rates(order)
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Unable to quote shipping") from exc

    return [ShippingRateOut(**rate) for rate in rates]


@router.post("/orders/{order_number}/shipping", response_model=OrderOut)
def api_select_shipping(
    order_number: str,
    data: SelectShippingIn,
    session: Session = Depends(db_session),
):
    _require_phase1()
    order = _get_order_or_404(session, order_number)
    if order.square_payment_link_id:
        raise HTTPException(status_code=409, detail="Checkout already created")

    try:
        rates = PrintfulClient().get_shipping_rates(order)
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Unable to quote shipping") from exc

    selected = next((rate for rate in rates if rate["shipping"] == data.shipping), None)
    if selected is None:
        raise HTTPException(status_code=400, detail="Shipping method is not currently available")

    try:
        set_shipping_rate(
            session,
            order,
            shipping_method=selected["shipping"],
            shipping_cents=selected["rate_cents"],
            currency=selected["currency"],
        )
    except OrderError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    return _order_out(order)


@router.post("/orders/{order_number}/square-checkout", response_model=OrderOut)
def api_square_checkout(order_number: str, session: Session = Depends(db_session)):
    _require_phase1()
    order = _get_order_or_404(session, order_number)
    if order.square_payment_link_id:
        return _order_out(order, order.square_checkout_url)
    if not shipping_quote_is_fresh(order):
        raise HTTPException(status_code=409, detail="Shipping quote is missing or expired")

    client = SquareClient()
    try:
        payment_link = client.create_payment_link(order)
        square_order = client.get_order(payment_link["order_id"])
        sync_square_pricing(session, order, square_order)
        set_square_checkout(
            session,
            order,
            payment_link_id=payment_link["id"],
            square_order_id=payment_link["order_id"],
            checkout_url=payment_link["url"],
        )
    except OrderError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Unable to create Square checkout") from exc

    return _order_out(order, payment_link["url"])


@router.post("/webhooks/square", include_in_schema=False)
async def square_webhook(request: Request, session: Session = Depends(db_session)):
    body = await request.body()
    signature = request.headers.get("x-square-hmacsha256-signature")
    if not verify_square_webhook(body, signature):
        raise HTTPException(status_code=401, detail="Invalid Square signature")

    event = json.loads(body)
    event_id = event.get("event_id") or event.get("id")
    event_type = event.get("type") or ""
    if not event_id:
        raise HTTPException(status_code=400, detail="Square event ID missing")

    existing = session.scalar(
        select(PaymentEvent).where(
            PaymentEvent.provider == "square",
            PaymentEvent.provider_event_id == event_id,
        )
    )
    if existing:
        return {"ok": True, "duplicate": True}

    obj = event.get("data", {}).get("object", {})
    payment = obj.get("payment") or {}
    refund_data = obj.get("refund") or {}
    provider_payment_id = payment.get("id") or refund_data.get("payment_id")
    result = "IGNORED"

    if event_type in {"payment.created", "payment.updated"}:
        payment_id = payment.get("id")
        square_order_id = payment.get("order_id")
        status = (payment.get("status") or "").upper()
        amount_money = payment.get("amount_money") or {}

        if square_order_id:
            order = get_order_by_square_order_id(session, square_order_id)
            if order is not None:
                try:
                    square_order = SquareClient().get_order(square_order_id)
                    sync_square_pricing(session, order, square_order)
                except OrderError as exc:
                    raise HTTPException(status_code=409, detail=str(exc)) from exc

                if amount_money.get("currency") != order.currency:
                    raise HTTPException(status_code=409, detail="Square currency mismatch")
                if int(amount_money.get("amount", -1)) != order.total_cents:
                    raise HTTPException(status_code=409, detail="Square amount mismatch")

                if status == "COMPLETED" and payment_id:
                    mark_paid_and_enqueue(session, order, square_payment_id=payment_id)
                    result = "PAID"
                elif status in {"FAILED", "CANCELED"}:
                    order.payment_state = status
                    order.order_state = "PAYMENT_FAILED"
                    session.commit()
                    result = status
                else:
                    result = status or "PENDING"

    elif event_type in {"refund.created", "refund.updated"}:
        refund_id = refund_data.get("id")
        if refund_id:
            refund = get_refund_by_square_id(session, str(refund_id))
            if refund is not None:
                order = session.get(Order, refund.order_id)
                if order is not None:
                    apply_refund_status(
                        session,
                        refund,
                        order,
                        status=str(refund_data.get("status") or refund.status),
                    )
                    result = refund.status

    event_time = None
    if event.get("created_at"):
        try:
            event_time = datetime.fromisoformat(event["created_at"].replace("Z", "+00:00"))
        except ValueError:
            event_time = None

    session.add(
        PaymentEvent(
            provider="square",
            provider_event_id=event_id,
            provider_payment_id=provider_payment_id,
            event_type=event_type,
            event_time=event_time,
            payload_hash=hashlib.sha256(body).hexdigest(),
            processing_result=result,
        )
    )
    session.commit()
    return {"ok": True, "result": result}


@router.post("/webhooks/printful", include_in_schema=False)
async def printful_webhook(request: Request, session: Session = Depends(db_session)):
    body = await request.body()
    signature = request.headers.get("x-pf-webhook-signature")
    public_key = request.headers.get("x-pf-webhook-public-key")

    if settings.printful_webhook_public_key and public_key != settings.printful_webhook_public_key:
        raise HTTPException(status_code=401, detail="Unexpected Printful public key")
    if not verify_printful_webhook(body, signature):
        raise HTTPException(status_code=401, detail="Invalid Printful signature")

    event = json.loads(body)
    event_type = event.get("type") or ""
    event_hash = hashlib.sha256(body).hexdigest()

    existing = session.scalar(
        select(FulfillmentEvent).where(
            FulfillmentEvent.provider == "printful",
            FulfillmentEvent.provider_event_id == event_hash,
        )
    )
    if existing:
        return {"ok": True, "duplicate": True}

    data = event.get("data") or {}
    pf_order = data.get("order") or {}
    external_id = pf_order.get("external_id")
    order = None
    if external_id:
        order = session.scalar(select(Order).where(Order.order_number == external_id))

    result = "IGNORED"
    if order is not None:
        pf_status = (pf_order.get("status") or "").upper()
        if pf_order.get("id") is not None:
            order.printful_order_id = str(pf_order["id"])

        if event_type in {"order_created", "order_updated"}:
            order.fulfillment_state = pf_status or "DRAFT"
            if pf_status == "FULFILLED":
                order.order_state = "SHIPPED"
            elif pf_status == "PARTIAL":
                order.order_state = "PARTIALLY_SHIPPED"
            elif pf_status == "INPROCESS":
                order.order_state = "IN_PRODUCTION"
            elif order.order_state == "PAID":
                order.order_state = "FULFILLMENT_SUBMITTED"
            result = order.fulfillment_state
        elif event_type == "order_put_hold":
            order.fulfillment_state = "HOLD"
            order.order_state = "FULFILLMENT_HOLD"
            result = "HOLD"
        elif event_type == "order_failed":
            order.fulfillment_state = "FAILED"
            order.order_state = "FULFILLMENT_FAILED"
            result = "FAILED"
        elif event_type == "order_canceled":
            order.fulfillment_state = "CANCELED"
            result = "CANCELED"
        elif event_type in {"shipment_sent", "shipment_delivered", "shipment_returned"}:
            shipment = upsert_printful_shipment(
                session,
                order,
                data.get("shipment") or {},
                event_type=event_type,
                printful_order_status=pf_order.get("status"),
            )
            if shipment is not None and event_type == "shipment_sent":
                order.shipped_at = order.shipped_at or shipment.shipped_at or datetime.now(timezone.utc)
            result = shipment.status if shipment is not None else "SHIPMENT_MISSING"

    session.add(
        FulfillmentEvent(
            provider="printful",
            provider_event_id=event_hash,
            provider_order_id=str(pf_order.get("id")) if pf_order.get("id") is not None else None,
            event_type=event_type,
            payload_hash=event_hash,
            processing_result=result,
        )
    )
    session.commit()
    return {"ok": True, "result": result}
