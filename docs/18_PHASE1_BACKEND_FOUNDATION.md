# Phase 1 Backend Foundation

This is the first transactional backend slice. It is intentionally safe to build before physical sample approval.

## Implemented

- SQLAlchemy order database
- Alembic initial schema migration
- product variant records with server-owned price and Printful mapping
- immutable order-item snapshots
- Square Checkout / Payment Links client
- Square webhook HMAC verification
- exact amount/currency verification before paid transition
- idempotent payment-event storage
- exactly-one fulfillment job per paid order
- Printful v2 draft-order client
- Printful external-ID reconciliation before draft creation
- Printful v2 webhook HMAC verification
- fulfillment lifecycle updates for order and shipment events
- retrying background worker
- customer-safe noindex order status page
- CI migration test and Phase 1 unit tests

## Safety defaults

Nothing in this branch enables a real store transaction by default.

```
PHASE1_API_ENABLED=false
PRINTFUL_MODE=disabled
PHASE0_5_APPROVED=false
SQUARE_ENVIRONMENT=sandbox
```

The foundation also **refuses to start with production checkout enabled**. A later PR must deliberately remove that block after:

- shipping calculation exists
- tax behavior is decided and tested
- physical variants/prices are approved
- Printful draft flow is proven
- live Square/Printful credentials are configured
- production canary procedure is approved

Printful `production` mode is also not capable of confirming an order in this foundation; `PrintfulClient.create_draft_order` deliberately refuses that mode.

## Sandbox flow

Once PostgreSQL (or SQLite for local development) is migrated and a test ProductVariant exists:

1. set `APP_ENV=development`
2. set `PHASE1_API_ENABLED=true`
3. configure Square Sandbox credentials/webhook
4. leave `PRINTFUL_MODE=disabled` to test Square only, or set `draft` with real Printful test-safe mappings
5. create an order through `POST /api/v1/orders`
6. create a hosted checkout link through `POST /api/v1/orders/{order_number}/square-checkout`
7. complete Square Sandbox checkout
8. verified `payment.updated` transitions the order to PAID and creates the fulfillment job
9. in Printful draft mode, the worker checks `@BMB-order-number` before creating a draft

## Important unfinished launch work

The foundation deliberately does **not** yet provide:

- live product variants/prices
- shipping-rate calculation
- sales-tax calculation
- buyer-edited Square shipping-address reconciliation
- production Printful confirmation
- refunds
- transactional email
- owner/admin UI
- periodic Square reconciliation

Those are subsequent Phase 1 increments.

## Migrations

Development:

```bash
DATABASE_URL=sqlite:///./dev.db APP_ENV=development alembic upgrade head
```

Production eventually:

```bash
alembic upgrade head
```

Do not run the Phase 1 worker against production until its environment is intentionally configured.
