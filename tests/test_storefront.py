from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db import Base
from app.models import ProductVariant
from app.orders import new_order_number
from app.storefront import price_floor_by_product, sellable_variants_for_product


def make_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, expire_on_commit=False)
    return Session()


def test_sellable_storefront_variants_hide_inactive_and_unsellable():
    with make_session() as session:
        session.add_all([
            ProductVariant(
                product_slug="lotus-of-the-void",
                sku="LOTUS-L",
                size="L",
                color="Black",
                currency="USD",
                retail_price_cents=3500,
                active=True,
                sellable=True,
            ),
            ProductVariant(
                product_slug="lotus-of-the-void",
                sku="LOTUS-S",
                size="S",
                color="Black",
                currency="USD",
                retail_price_cents=3200,
                active=True,
                sellable=True,
            ),
            ProductVariant(
                product_slug="lotus-of-the-void",
                sku="LOTUS-HIDDEN",
                size="M",
                color="Black",
                currency="USD",
                retail_price_cents=100,
                active=True,
                sellable=False,
            ),
        ])
        session.commit()

        variants = sellable_variants_for_product(session, "lotus-of-the-void")
        assert [item.sku for item in variants] == ["LOTUS-S", "LOTUS-L"]
        assert price_floor_by_product(session)["lotus-of-the-void"] == 3200


def test_public_order_number_has_high_entropy_shape():
    order_number = new_order_number()
    assert order_number.startswith("BMB-")
    token = order_number.removeprefix("BMB-")
    assert len(token) == 20
    int(token, 16)
