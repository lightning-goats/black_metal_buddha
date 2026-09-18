from __future__ import annotations

import argparse

from sqlalchemy import select

from .catalog import PRODUCT_BY_SLUG
from .db import SessionLocal
from .fulfillment.printful import PrintfulClient
from .models import Order, ProductVariant
from .payments.square import SquareClient
from .reconcile import reconcile_orders
from .settings import settings


def seed_sandbox_variant(args: argparse.Namespace) -> None:
    if settings.app_env == "production":
        raise SystemExit("Sandbox variant seeding is disabled in production.")
    if args.product_slug not in PRODUCT_BY_SLUG:
        raise SystemExit(f"Unknown product slug: {args.product_slug}")

    with SessionLocal() as session:
        existing = session.scalar(select(ProductVariant).where(ProductVariant.sku == args.sku))
        if existing:
            raise SystemExit(f"SKU already exists: {args.sku}")

        variant = ProductVariant(
            product_slug=args.product_slug,
            sku=args.sku,
            size=args.size,
            color=args.color,
            currency="USD",
            retail_price_cents=args.price_cents,
            active=True,
            sellable=True,
            printful_product_id=args.printful_product_id,
            printful_variant_id=args.printful_variant_id,
        )
        session.add(variant)
        session.commit()
        print(f"Created sandbox SKU {variant.sku} at ${variant.retail_price_cents / 100:.2f}")


def list_orders(_: argparse.Namespace) -> None:
    with SessionLocal() as session:
        orders = session.scalars(select(Order).order_by(Order.created_at.desc()).limit(100)).all()
        if not orders:
            print("No orders.")
            return
        for order in orders:
            print(
                order.order_number,
                order.order_state,
                order.payment_state,
                order.fulfillment_state,
                f"{order.currency} {order.total_cents / 100:.2f}",
            )


def reconcile(_: argparse.Namespace) -> None:
    square = None
    printful = None

    if settings.square_access_token and settings.square_location_id:
        square = SquareClient()
    if settings.printful_mode != "disabled" and settings.printful_token:
        printful = PrintfulClient()

    if square is None and printful is None:
        raise SystemExit("No configured provider is available for reconciliation.")

    with SessionLocal() as session:
        counts = reconcile_orders(
            session,
            square_client=square,
            printful_client=printful,
        )
    print(counts)


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Black Metal Buddha backend management")
    sub = p.add_subparsers(dest="command", required=True)

    seed = sub.add_parser("seed-sandbox-variant")
    seed.add_argument("--product-slug", required=True, choices=sorted(PRODUCT_BY_SLUG))
    seed.add_argument("--sku", required=True)
    seed.add_argument("--size", required=True)
    seed.add_argument("--color", default="Black")
    seed.add_argument("--price-cents", type=int, required=True)
    seed.add_argument("--printful-product-id")
    seed.add_argument("--printful-variant-id")
    seed.set_defaults(func=seed_sandbox_variant)

    ls = sub.add_parser("list-orders")
    ls.set_defaults(func=list_orders)

    rec = sub.add_parser("reconcile")
    rec.set_defaults(func=reconcile)

    return p


def main() -> None:
    args = parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
