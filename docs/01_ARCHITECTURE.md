# Architecture

## Principles

1. Local database is canonical for ecommerce orders.
2. Square is canonical for payments.
3. Printful is canonical for fulfillment.
4. Payment and fulfillment are separate state machines.
5. External actions are idempotent.
6. Webhooks are verified before trusted state changes.
7. Browser never decides price, tax, shipping, payment completion, or fulfillment eligibility.
8. No card data reaches our backend.
9. Lightning is a future adapter, not a launch dependency.

## Topology

```text
Internet
   |
Nginx / TLS
   |
FastAPI app
 |-- storefront/cart/checkout
 |-- order service
 |-- Square adapter
 |-- Printful adapter
 |-- webhook handlers
 |-- jobs/reconciliation
 |
PostgreSQL

FastAPI <--> Square APIs
FastAPI <--> Printful API
Square webhooks  --> FastAPI
Printful webhooks --> FastAPI
```

A database-backed jobs table is enough at launch; a separate queue product is optional.

## Suggested modules

```text
app/
  main.py
  config.py
  db/
  catalog/
  cart/
  orders/
  checkout/
  payments/
    base.py
    square.py
    square_lightning.py   # disabled placeholder
  fulfillment/
    printful.py
  webhooks/
    square.py
    printful.py
  jobs/
  notifications/
  templates/
  static/
```

## Suggested order states

```text
CART
PENDING_PAYMENT
PAYMENT_FAILED
PAID
FULFILLMENT_QUEUED
FULFILLMENT_SUBMITTED
FULFILLMENT_HOLD
FULFILLMENT_FAILED
IN_PRODUCTION
PARTIALLY_SHIPPED
SHIPPED
CANCELED
REFUNDED
```

Also keep independent `payment_state` and `fulfillment_state`.

## Fulfillment duplicate protection

Use the BMB order number as Printful `external_id`.

Before retrying creation, retrieve by `@external_id`. If it already exists, reconcile instead of creating another order.

## Future payment-provider interface

```python
class PaymentProvider:
    def create_payment(self, order, payment_source): ...
    def get_payment(self, payment_id): ...
    def refund(self, payment_id, amount): ...
    def verify_webhook(self, request): ...
```

Launch: `SquareFiatPaymentProvider`  
Future: `SquareLightningPaymentProvider`
