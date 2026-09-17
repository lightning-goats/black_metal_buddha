# Coding Agent Handoff

## Mission

Implement Black Metal Buddha Phase 0 and Phase 1.

Repository:

```text
lightning-goats/black_metal_buddha
```

Domain:

```text
blackmetalbuddha.com
```

## Architecture

- self-hosted BMB storefront/order service
- Square hosted Checkout/Payment Links
- verified Square webhooks
- local BMB database
- automatic Printful fulfillment
- no LNbits
- no Strike
- no Lightning implementation

## Read first

1. `00_MASTER_PLAN.md`
2. `01_ARCHITECTURE.md`
3. `02_DATA_MODEL.md`
4. `03_SQUARE_INTEGRATION.md`
5. `04_PRINTFUL_INTEGRATION.md`
6. `05_PHASE0_VPS_DEPLOYMENT.md`
7. `06_SECURITY_PRIVACY.md`
8. `07_TESTING_AND_RELEASE.md`
9. `10_ADR_LIGHTNING_DEFERRED.md`

## First milestone

Staging flow:

```text
one SKU
  ↓
local cart/order
  ↓
Square Sandbox payment link
  ↓
Square-hosted checkout
  ↓
verified payment webhook
  ↓
BMB PAID
  ↓
Printful draft/test-safe order
```

No production Printful fulfillment until explicitly enabled by the release plan.

## Rules

- server controls all totals
- browser return is never proof of payment
- verify Square webhooks
- use Square idempotency
- use Printful `external_id`
- verify Printful webhooks
- duplicate events must be harmless
- no undocumented Square APIs
- no Lightning code until ADR-001 is reopened
