# Architecture

## Core principle

Black Metal Buddha owns the ecommerce state.

Square owns payment processing.

Printful owns fulfillment.

LNbits and Strike are not in the production architecture.

## Topology

```text
                       Internet
                          |
                    blackmetalbuddha.com
                          |
                       Nginx/TLS
                          |
                    BMB application
          +---------------+---------------+
          |               |               |
       catalog          orders         admin/ops
          |               |
          |               +-------------------+
          |                                   |
          v                                   v
      PostgreSQL                         Square Checkout
                                              |
                                    Square-hosted payment
                                              |
                                        Square webhook
                                              |
                                              v
                                     verified BMB PAID
                                              |
                                              v
                                           Printful
                                              |
                                       Printful webhook
                                              |
                                              v
                                         BMB status
```

## Recommended stack

- Nginx
- Python + FastAPI
- Jinja2/server-rendered pages
- minimal JavaScript
- PostgreSQL
- systemd
- Square Checkout/Payment Links API
- Printful API
- database-backed retry jobs

A dedicated queue service is optional at launch.

## Application modules

```text
app/
  main.py
  config.py
  catalog/
  cart/
  orders/
  checkout/
  payments/
    base.py
    square.py
  fulfillment/
    printful.py
  webhooks/
    square.py
    printful.py
  jobs/
  notifications/
  admin/
  templates/
  static/
```

Do not add an LNbits payment provider module.
Do not add a Lightning provider module until the Square Lightning ADR is reopened.

## Order state

Keep payment and fulfillment states separate.

Suggested top-level order states:

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

## Provider identifiers

For each order keep:

```text
BMB order number
Square order ID
Square payment-link ID
Square payment ID
Printful external ID
Printful order ID
```

Example:

```text
BMB-000041
  ↕
Square order: ...
  ↕
Square payment: ...
  ↕
Printful external_id: BMB-000041
```

## Trust boundaries

### Browser is not authoritative for

- product price
- discount
- shipping
- tax
- total
- payment status
- fulfillment status

### Square is authoritative for

- payment completion
- Square payment/order identity

### Printful is authoritative for

- fulfillment lifecycle
- shipment/tracking lifecycle

### Local BMB database is authoritative for

- ecommerce order
- product snapshot
- customer shipment request
- correlation of Square + Printful records
