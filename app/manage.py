from __future__ import annotations

import argparse

from sqlalchemy import select

from .catalog import PRODUCT_BY_SLUG
from .db import SessionLocal
from .fulfillment.printful import PrintfulClient
from .models import Order, ProductVariant
from .orders import (
    create_order,
    set_shipping_rate,
    set_square_checkout,
    sync_square_pricing,
)
from .payments.square import SquareClient
from .reconcile import reconcile_orders
from .refunds import request_refund
from .schemas import CreateOrderIn
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
                order.refund_state,
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


def sandbox_checkout(args: argparse.Namespace) -> None:
    if settings.app_env == "production" or settings.square_environment != "sandbox":
        raise SystemExit("sandbox-checkout requires APP_ENV != production and Square sandbox")
    if not settings.printful_token:
        raise SystemExit("PRINTFUL_TOKEN is required to quote shipping")

    data = CreateOrderIn(
        recipient={
            "name": args.name,
            "email": args.email,
            "phone": args.phone,
            "address1": args.address1,
            "address2": args.address2,
            "city": args.city,
            "state": args.state,
            "postal_code": args.postal_code,
            "country_code": args.country,
        },
        items=[{"sku": args.sku, "quantity": args.quantity}],
    )

    with SessionLocal() as session:
        order = create_order(session, data)
        printful = PrintfulClient()
        rates = printful.get_shipping_rates(order)
        if not rates:
            raise SystemExit("Printful returned no shipping rates")

        selected = next((r for r in rates if r["shipping"] == args.shipping), None)
        if selected is None:
            available = ", ".join(r["shipping"] for r in rates)
            raise SystemExit(f"Shipping method {args.shipping!r} unavailable. Available: {available}")

        set_shipping_rate(
            session,
            order,
            shipping_method=selected["shipping"],
            shipping_cents=selected["rate_cents"],
            currency=selected["currency"],
        )

        square = SquareClient()
        link = square.create_payment_link(order)
        square_order = square.get_order(link["order_id"])
        sync_square_pricing(session, order, square_order)
        set_square_checkout(
            session,
            order,
            payment_link_id=link["id"],
            square_order_id=link["order_id"],
            checkout_url=link["url"],
        )

        print(f"Order: {order.order_number}")
        print(f"Subtotal: {order.currency} {order.subtotal_cents / 100:.2f}")
        print(f"Shipping: {order.currency} {order.shipping_cents / 100:.2f} ({order.shipping_method})")
        print(f"Square tax: {order.currency} {order.tax_cents / 100:.2f}")
        print(f"Total: {order.currency} {order.total_cents / 100:.2f}")
        print(f"Checkout: {order.square_checkout_url}")


def refund_order(args: argparse.Namespace) -> None:
    if settings.square_environment != "sandbox":
        raise SystemExit("refund-order is sandbox-only in this phase")

    with SessionLocal() as session:
        order = session.scalar(select(Order).where(Order.order_number == args.order_number))
        if order is None:
            raise SystemExit("Order not found")

        refund = request_refund(
            session,
            order,
            amount_cents=args.amount_cents,
            reason=args.reason,
            client=SquareClient(),
        )
        print(
            refund.square_refund_id,
            refund.status,
            f"{refund.currency} {refund.amount_cents / 100:.2f}",
        )


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

    checkout = sub.add_parser("sandbox-checkout")
    checkout.add_argument("--sku", required=True)
    checkout.add_argument("--quantity", type=int, default=1)
    checkout.add_argument("--shipping", default="STANDARD")
    checkout.add_argument("--name", required=True)
    checkout.add_argument("--email", required=True)
    checkout.add_argument("--phone")
    checkout.add_argument("--address1", required=True)
    checkout.add_argument("--address2")
    checkout.add_argument("--city", required=True)
    checkout.add_argument("--state", required=True)
    checkout.add_argument("--postal-code", required=True)
    checkout.add_argument("--country", default="US")
    checkout.set_defaults(func=sandbox_checkout)

    refund = sub.add_parser("refund-order")
    refund.add_argument("order_number")
    refund.add_argument("--amount-cents", type=int)
    refund.add_argument("--reason", default="Customer refund")
    refund.set_defaults(func=refund_order)

    return p


def main() -> None:
    args = parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
