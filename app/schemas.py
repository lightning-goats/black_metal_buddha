from __future__ import annotations

from pydantic import BaseModel, Field


class AddressIn(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    email: str = Field(min_length=3, max_length=320)
    phone: str | None = Field(default=None, max_length=64)
    address1: str = Field(min_length=1, max_length=255)
    address2: str | None = Field(default=None, max_length=255)
    city: str = Field(min_length=1, max_length=128)
    state: str = Field(min_length=1, max_length=128)
    postal_code: str = Field(min_length=1, max_length=32)
    country_code: str = Field(default="US", min_length=2, max_length=2)


class OrderLineIn(BaseModel):
    sku: str = Field(min_length=1, max_length=128)
    quantity: int = Field(ge=1, le=10)


class CreateOrderIn(BaseModel):
    recipient: AddressIn
    items: list[OrderLineIn] = Field(min_length=1, max_length=20)


class OrderOut(BaseModel):
    order_number: str
    order_state: str
    payment_state: str
    fulfillment_state: str
    currency: str
    subtotal_cents: int
    discount_cents: int
    shipping_cents: int
    tax_cents: int
    total_cents: int
    square_checkout_url: str | None = None


class ShippingRateOut(BaseModel):
    shipping: str
    name: str
    rate_cents: int
    currency: str
    min_delivery_days: int | None = None
    max_delivery_days: int | None = None


class SelectShippingIn(BaseModel):
    shipping: str = Field(min_length=1, max_length=64)


class RefundRequestIn(BaseModel):
    amount_cents: int | None = Field(default=None, ge=1)
    reason: str = Field(default="Customer refund", min_length=1, max_length=192)
