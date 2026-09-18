from __future__ import annotations

import hashlib
import hmac
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

import httpx

from ..models import Order
from ..settings import Settings, settings


class PrintfulConfigurationError(RuntimeError):
    pass


def money_to_cents(value: str | int | float | Decimal) -> int:
    return int((Decimal(str(value)) * Decimal("100")).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


class PrintfulClient:
    API_BASE = "https://api.printful.com"

    def __init__(self, config: Settings = settings, client: httpx.Client | None = None):
        self.config = config
        self.client = client or httpx.Client(timeout=30)

    def _headers(self) -> dict[str, str]:
        if not self.config.printful_token:
            raise PrintfulConfigurationError("PRINTFUL_TOKEN is not configured")
        headers = {
            "Authorization": f"Bearer {self.config.printful_token}",
            "Content-Type": "application/json",
        }
        if self.config.printful_store_id:
            headers["X-PF-Store-Id"] = self.config.printful_store_id
        return headers

    @staticmethod
    def _recipient(order: Order) -> dict[str, Any]:
        recipient = {
            "name": order.customer_name,
            "email": order.email,
            "address1": order.ship_address1,
            "city": order.ship_city,
            "state_name": order.ship_state,
            "state_code": order.ship_state,
            "country_code": order.ship_country,
            "zip": order.ship_postal_code,
        }
        if order.phone:
            recipient["phone"] = order.phone
        if order.ship_address2:
            recipient["address2"] = order.ship_address2
        return recipient

    @staticmethod
    def _order_items(order: Order) -> list[dict[str, Any]]:
        order_items = []
        for item in order.items:
            if not item.printful_product_id_snapshot or not item.printful_variant_id_snapshot:
                raise PrintfulConfigurationError(f"Missing Printful mapping for {item.sku_snapshot}")
            order_items.append(
                {
                    "source": "product",
                    "product_id": int(item.printful_product_id_snapshot),
                    "variant_id": int(item.printful_variant_id_snapshot),
                    "quantity": item.quantity,
                    "external_id": f"{order.order_number}-{item.id}",
                }
            )
        return order_items

    def get_shipping_rates(self, order: Order) -> list[dict[str, Any]]:
        payload = {
            "recipient": self._recipient(order),
            "order_items": self._order_items(order),
            "currency": order.currency,
        }
        response = self.client.post(
            f"{self.API_BASE}/v2/shipping-rates",
            headers=self._headers(),
            json=payload,
        )
        response.raise_for_status()
        data = response.json().get("data") or []
        rates = []
        for rate in data:
            rates.append(
                {
                    "shipping": str(rate.get("shipping") or ""),
                    "name": str(rate.get("shipping_method_name") or rate.get("shipping") or ""),
                    "rate_cents": money_to_cents(rate.get("rate", "0")),
                    "currency": str(rate.get("currency") or order.currency),
                    "min_delivery_days": rate.get("min_delivery_days"),
                    "max_delivery_days": rate.get("max_delivery_days"),
                }
            )
        return rates

    def get_shipments(self, order_id_or_external_id: str) -> list[dict[str, Any]]:
        response = self.client.get(
            f"{self.API_BASE}/v2/orders/{order_id_or_external_id}/shipments",
            headers=self._headers(),
            params={"limit": 100, "offset": 0},
        )
        response.raise_for_status()
        return response.json().get("data") or []

    def get_order_by_external_id(self, external_id: str) -> dict[str, Any] | None:
        response = self.client.get(
            f"{self.API_BASE}/v2/orders/@{external_id}",
            headers=self._headers(),
        )
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return response.json().get("data") or {}

    def create_draft_order(self, order: Order) -> dict[str, Any]:
        if self.config.printful_mode == "disabled":
            raise PrintfulConfigurationError("Printful integration is disabled")
        if self.config.printful_mode == "production":
            raise PrintfulConfigurationError(
                "Backend foundation never confirms production orders directly"
            )
        if not order.shipping_method:
            raise PrintfulConfigurationError("Shipping method has not been selected")

        payload = {
            "external_id": order.order_number,
            "shipping": order.shipping_method,
            "recipient": self._recipient(order),
            "order_items": self._order_items(order),
        }

        response = self.client.post(
            f"{self.API_BASE}/v2/orders",
            headers=self._headers(),
            json=payload,
        )
        response.raise_for_status()
        return response.json().get("data") or {}


def verify_printful_webhook(
    body: bytes,
    signature: str | None,
    *,
    secret_key_hex: str | None = None,
) -> bool:
    secret_hex = secret_key_hex or settings.printful_webhook_secret_key
    if not signature or not secret_hex:
        return False
    try:
        secret = bytes.fromhex(secret_hex)
    except ValueError:
        return False
    expected = hmac.new(secret, body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)
