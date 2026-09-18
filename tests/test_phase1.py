import base64
import hashlib
import hmac
import json

import httpx
import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.db import Base
from app.fulfillment.printful import PrintfulClient, verify_printful_webhook
from app.models import Job, ProductVariant
from app.orders import create_order, mark_paid_and_enqueue
from app.payments.square import SquareClient, verify_square_webhook
from app.schemas import CreateOrderIn
from app.settings import Settings


@pytest.fixture()
def session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, expire_on_commit=False)
    with Session() as session:
        yield session


def config(**overrides):
    data = dict(
        app_env="development",
        public_base_url="https://blackmetalbuddha.com",
        database_url="sqlite://",
        phase1_api_enabled=True,
        square_environment="sandbox",
        square_api_version="2026-09-16",
        square_access_token="sq-token",
        square_location_id="LOC",
        square_webhook_signature_key="square-secret",
        square_webhook_notification_url="https://example.com/api/v1/webhooks/square",
        printful_token="pf-token",
        printful_store_id="123",
        printful_mode="draft",
        printful_webhook_secret_key="aa" * 32,
        printful_webhook_public_key=None,
        phase0_5_approved=False,
    )
    data.update(overrides)
    return Settings(**data)


def order_input():
    return CreateOrderIn(
        recipient={
            "name": "Test Buyer",
            "email": "buyer@example.com",
            "address1": "1 Test Way",
            "city": "Denver",
            "state": "CO",
            "postal_code": "80202",
            "country_code": "US",
        },
        items=[{"sku": "BMB-LOTUS-BLK-M", "quantity": 2}],
    )


def seed_variant(session):
    variant = ProductVariant(
        product_slug="lotus-of-the-void",
        sku="BMB-LOTUS-BLK-M",
        size="M",
        color="Black",
        currency="USD",
        retail_price_cents=3200,
        active=True,
        sellable=True,
        printful_product_id="1000",
        printful_variant_id="4011",
    )
    session.add(variant)
    session.commit()
    return variant


def test_order_snapshots_server_price(session):
    seed_variant(session)
    order = create_order(session, order_input())
    assert order.subtotal_cents == 6400
    assert order.total_cents == 6400
    assert order.items[0].sku_snapshot == "BMB-LOTUS-BLK-M"
    assert order.items[0].unit_price_cents == 3200
    assert order.printful_external_id == order.order_number


def test_paid_transition_enqueues_once(session):
    seed_variant(session)
    order = create_order(session, order_input())
    assert mark_paid_and_enqueue(session, order, square_payment_id="PAY1") is True
    assert order.payment_state == "COMPLETED"
    assert len(session.scalars(select(Job)).all()) == 1

    assert mark_paid_and_enqueue(session, order, square_payment_id="PAY1") is False
    assert len(session.scalars(select(Job)).all()) == 1


def test_square_signature():
    body = b'{"event_id":"evt"}'
    url = "https://example.com/api/v1/webhooks/square"
    key = "secret"
    expected = base64.b64encode(
        hmac.new(key.encode(), url.encode() + body, hashlib.sha256).digest()
    ).decode()
    assert verify_square_webhook(body, expected, signature_key=key, notification_url=url)
    assert not verify_square_webhook(body + b"x", expected, signature_key=key, notification_url=url)


def test_square_payment_link_payload(session):
    seed_variant(session)
    order = create_order(session, order_input())
    captured = {}

    def handler(request: httpx.Request):
        captured["json"] = json.loads(request.content)
        return httpx.Response(
            200,
            json={"payment_link": {
                "id": "LINK", "order_id": "SQORDER", "url": "https://square.link/u/test"
            }},
        )

    client = httpx.Client(transport=httpx.MockTransport(handler))
    link = SquareClient(config(), client=client).create_payment_link(order)
    assert link["id"] == "LINK"
    assert captured["json"]["order"]["reference_id"] == order.order_number
    assert captured["json"]["order"]["line_items"][0]["base_price_money"]["amount"] == 3200
    assert captured["json"]["checkout_options"]["ask_for_shipping_address"] is True


def test_printful_draft_payload(session):
    seed_variant(session)
    order = create_order(session, order_input())
    captured = {}

    def handler(request: httpx.Request):
        captured["json"] = json.loads(request.content)
        return httpx.Response(
            200,
            json={"data": {"id": 777, "external_id": order.order_number, "status": "draft"}},
        )

    client = httpx.Client(transport=httpx.MockTransport(handler))
    data = PrintfulClient(config(), client=client).create_draft_order(order)
    assert data["status"] == "draft"
    assert captured["json"]["external_id"] == order.order_number
    item = captured["json"]["order_items"][0]
    assert item["source"] == "product"
    assert item["product_id"] == 1000
    assert item["variant_id"] == 4011
    assert item["quantity"] == 2


def test_printful_signature():
    body = b'{"type":"order_updated"}'
    secret = bytes.fromhex("ab" * 32)
    sig = hmac.new(secret, body, hashlib.sha256).hexdigest()
    assert verify_printful_webhook(body, sig, secret_key_hex="ab" * 32)
    assert not verify_printful_webhook(body + b"x", sig, secret_key_hex="ab" * 32)


def test_production_printful_requires_phase0_5():
    cfg = config(printful_mode="production", phase0_5_approved=False)
    with pytest.raises(ValueError):
        cfg.validate_safety()
