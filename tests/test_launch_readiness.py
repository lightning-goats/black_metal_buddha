import json

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.catalog_ops import (
    assert_production_catalog,
    catalog_errors,
    catalog_fingerprint,
    catalog_manifest,
    import_catalog_manifest,
)
from app.db import Base
from app.models import ProductVariant
from app.orders import create_order
from app.schemas import CreateOrderIn
from app.settings import Settings


def session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, expire_on_commit=False)
    return Session()


def add_launch_variants(db):
    for index, slug in enumerate(
        ["lotus-of-the-void", "dharma-of-decay", "meditate-on-death"],
        start=1,
    ):
        db.add(
            ProductVariant(
                product_slug=slug,
                sku=f"BMB-{index}-M",
                size="M",
                color="Black",
                currency="USD",
                retail_price_cents=3200 + index,
                active=True,
                sellable=True,
                printful_product_id=str(1000 + index),
                printful_variant_id=str(4000 + index),
            )
        )
    db.commit()


def settings(**overrides):
    data = dict(
        app_env="production",
        public_base_url="https://blackmetalbuddha.com",
        database_url="postgresql+psycopg://example",
        phase1_api_enabled=False,
        square_environment="production",
        square_api_version="2026-09-16",
        square_access_token="sq",
        square_location_id="loc",
        square_webhook_signature_key="wh",
        square_webhook_notification_url="https://blackmetalbuddha.com/api/v1/webhooks/square",
        printful_token="pf",
        printful_store_id="store",
        printful_mode="production",
        printful_webhook_secret_key="aa" * 32,
        printful_webhook_public_key=None,
        phase0_5_approved=True,
        email_mode="smtp",
        smtp_host="smtp.example",
        smtp_port=587,
        smtp_username=None,
        smtp_password=None,
        email_from="orders@example.com",
        printful_confirm_enabled=True,
        app_secret_key="secret",
        admin_username="owner",
        admin_password="password",
        production_catalog_approved=True,
        production_catalog_fingerprint="a" * 64,
        production_canary_mode=True,
        production_checkout_enabled=False,
        app_secret_key="secret",
        admin_username="owner",
        admin_password="password",
        support_email="support@example.com",
    )
    data.update(overrides)
    return Settings(**data)


def test_catalog_fingerprint_is_deterministic_and_detects_price_drift():
    with session() as db:
        add_launch_variants(db)
        first = catalog_fingerprint(db)
        second = catalog_fingerprint(db)
        assert first == second
        assert not catalog_errors(db)

        row = db.query(ProductVariant).filter_by(sku="BMB-1-M").one()
        row.retail_price_cents += 100
        db.commit()
        assert catalog_fingerprint(db) != first


def test_production_catalog_asserts_exact_approved_fingerprint():
    with session() as db:
        add_launch_variants(db)
        fingerprint = catalog_fingerprint(db)
        assert assert_production_catalog(db, fingerprint) == fingerprint
        with pytest.raises(RuntimeError):
            assert_production_catalog(db, "0" * 64)


def test_manifest_round_trip():
    with session() as source:
        add_launch_variants(source)
        manifest = catalog_manifest(source)
        source_fingerprint = catalog_fingerprint(source)

    with session() as target:
        result = import_catalog_manifest(target, json.loads(json.dumps(manifest)), apply=True)
        assert result["count"] == 3
        assert catalog_fingerprint(target) == source_fingerprint
        assert not catalog_errors(target)


def test_canary_safety_requires_public_checkout_off():
    cfg = settings(phase1_api_enabled=True)
    with pytest.raises(ValueError) as exc:
        cfg.validate_canary_safety()
    assert "PHASE1_API_ENABLED=false" in str(exc.value)

    settings().validate_canary_safety()


def test_canary_order_marker_is_persisted():
    with session() as db:
        add_launch_variants(db)
        order = create_order(
            db,
            CreateOrderIn(
                recipient={
                    "name": "Owner",
                    "email": "owner@example.com",
                    "address1": "1 Test Way",
                    "city": "Denver",
                    "state": "CO",
                    "postal_code": "80202",
                    "country_code": "US",
                },
                items=[{"sku": "BMB-1-M", "quantity": 1}],
            ),
            is_canary=True,
        )
        assert order.is_canary is True


def test_invalid_catalog_import_rolls_back_atomically():
    manifest = {
        "version": 1,
        "currency": "USD",
        "variants": [{
            "product_slug": "lotus-of-the-void",
            "sku": "ONLY-ONE",
            "size": "M",
            "color": "Black",
            "retail_price_cents": 3200,
            "active": True,
            "sellable": True,
            "printful_product_id": "1000",
            "printful_variant_id": "4011",
        }],
    }
    with session() as db:
        with pytest.raises(ValueError):
            import_catalog_manifest(db, manifest, apply=True)
        assert db.query(ProductVariant).count() == 0
