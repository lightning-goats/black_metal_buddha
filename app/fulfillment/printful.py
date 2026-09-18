from __future__ import annotations

import hashlib
import hmac
from typing import Any

import httpx

from ..models import Order
from ..settings import Settings, settings


class PrintfulConfigurationError(RuntimeError):
    pass


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

        payload = {
            "external_id": order.order_number,
            "shipping": "STANDARD",
            "recipient": {
                "name": order.customer_name,
                "email": order.email,
                "phone": order.phone,
                "address1": order.ship_address1,
                "address2": order.ship_address2,
                "city": order.ship_city,
                "state_name": order.ship_state,
                "country_code": order.ship_country,
                "zip": order.ship_postal_code,
            },
            "order_items": order_items,
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
