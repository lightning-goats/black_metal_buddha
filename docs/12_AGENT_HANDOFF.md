# Coding Agent Handoff

## Mission

Implement Phase 0 and Phase 1 for:

```text
blackmetalbuddha.com
```

Target:

- custom self-hosted store
- existing VPS
- Square fiat checkout
- automated Printful fulfillment
- no Lightning checkout yet

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

## P0 implementation order

1. deploy skeleton
2. schema/migrations
3. catalog
4. cart
5. checkout shell
6. Square Sandbox
7. verified Square webhooks
8. idempotent order/payment state
9. Printful integration
10. signed Printful v2 webhooks
11. database-backed jobs
12. reconciliation
13. tests

## Constraints

- no Bitcoin/Lightning checkout
- no undocumented Square endpoints
- no browser-authoritative totals
- no fulfillment from browser callback
- no fulfillment without trusted completed payment
- no duplicate Printful order on retry
- use Printful external IDs
- verify both providers' webhooks
- keep card data out of backend
- never log secrets

## First milestone

On staging:

1. configure one SKU
2. add to cart
3. complete Square Sandbox payment
4. verified webhook marks it paid
5. job creates a Printful draft/test-safe order
6. save Printful ID
7. prevent any production fulfillment until explicitly enabled by test plan
