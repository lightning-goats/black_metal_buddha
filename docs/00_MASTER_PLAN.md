# Master Plan

## Objective

Build `blackmetalbuddha.com` as a small, self-hosted print-on-demand store.

The customer should be able to:

1. browse products
2. select size/quantity
3. check out through Square
4. receive confirmation
5. have the order automatically submitted to Printful
6. receive fulfillment and tracking updates

No order should require manual transfer from Square to Printful.

## Launch collection

Initial designs:

1. **Lotus of the Void** — *No Self • No Fear*
2. **Dharma of Decay** — *All Things Pass*
3. **Meditate on Death** — *Emptiness Is Freedom*

## Research conclusion

Square's public APIs support normal online fiat checkout and hosted payment links.

The preferred launch pattern is Square's hosted Checkout / Payment Links API:

```text
BMB cart
   ↓
local BMB order
   ↓
Square CreatePaymentLink
   ↓
Square-hosted checkout
   ↓
verified Square webhook
   ↓
Square payment = COMPLETED
   ↓
BMB order = PAID
   ↓
Printful
```

This pattern was independently validated by LNbits' Square fiat-provider implementation, but Black Metal Buddha will implement it directly rather than route ecommerce orders through LNbits.

## Why hosted Square checkout

It reduces payment-front-end complexity while preserving our own storefront and order system.

Benefits:

- Square hosts the payment UI
- Square handles sensitive payment data
- simpler PCI/security boundary
- Square order/payment IDs remain available for reconciliation
- payment status is webhook/API driven
- card and eligible Square wallet methods can be enabled according to current Square support
- easier future adaptation if Square later adds Lightning to hosted checkout

## Phase 0 — website and infrastructure

Deliver:

- DNS for `blackmetalbuddha.com`
- HTTPS
- Nginx
- application service
- PostgreSQL
- home/shop/product/cart/checkout-shell/order-status pages
- product catalog
- staging environment
- logging/backups/health checks

No real payment processing is required to exit Phase 0.

## Phase 0.5 — sample approval

Before public launch:

- select exact Printful garment blank
- configure variants
- upload final artwork
- order samples
- inspect print quality, fine detail, placement, red reproduction, fit, and wash durability
- revise artwork if needed
- photograph approved products

## Phase 1 — Square fiat + Printful automation

Implement:

- local BMB order state machine
- Square hosted Checkout/Payment Links API
- signed Square webhooks
- server-side amount verification
- idempotent Square checkout creation
- Printful product/variant mapping
- Printful order creation
- signed Printful webhooks
- retry/reconciliation jobs
- transactional confirmation/tracking notifications
- refund/admin workflow

### Phase 1 exit criteria

A real order must complete:

```text
customer
  ↓
Square
  ↓
BMB verified paid state
  ↓
Printful
  ↓
production
  ↓
shipment
  ↓
tracking
```

with no manual copying of order data.

## Phase 2 — additional channels

After Phase 1 is stable, add marketplaces/ecommerce platforms supported by Printful.

Candidate order:

1. Etsy
2. Amazon
3. eBay
4. TikTok Shop or other channel justified by demand

Native Printful integrations should be used where they reduce operational burden.

## Phase 3 — SEO and marketing

Technical SEO begins during Phase 0.

Active acquisition starts only after checkout and fulfillment are proven.

Focus on:

- real product photography
- structured product data
- sitemap/Search Console
- product storytelling
- original content
- marketplace SEO
- social content
- paid promotion only after unit economics are known

## Future Lightning

Lightning remains outside the active implementation plan.

Revisit only when Square exposes an official developer API that can:

1. initiate/accept an online Lightning payment
2. associate it with a Square/BMB order
3. expose reliable server-verifiable status/webhooks
4. automatically settle the payment to fiat/USD
5. require no manual BTC sale/conversion before Printful fulfillment

See `10_ADR_LIGHTNING_DEFERRED.md`.
