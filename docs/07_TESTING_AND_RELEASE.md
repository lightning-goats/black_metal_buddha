# Testing and Release Plan

## Unit tests

Cover:

- money calculations
- order states
- Square mapping
- Printful mapping
- webhook dedupe
- idempotent fulfillment
- retry/backoff
- signature-verification wrappers

## Square integration tests

Use Sandbox:

- approval
- decline
- duplicate submit
- timeout after request
- duplicate webhook
- webhook before browser response
- webhook after browser closes
- amount mismatch
- wrong currency

## Printful tests

Use safe draft/test behavior first.

Test:

- create draft
- existing external ID
- timeout after create
- hold
- failure
- duplicate webhook
- shipment update

## Production canary

1. Place one real order.
2. Verify Square completion.
3. Verify exactly one Printful order.
4. Allow production.
5. Verify shipment webhook.
6. Verify tracking notification.
7. Reconcile dashboards/database.

## Critical failure expectations

### Customer charged; Printful unavailable

Order stays `PAID`; job retries; no second charge.

### Customer charged; Printful billing fails

Order becomes `FULFILLMENT_FAILED`; alert loudly.

### Printful timeout after creation

Retry checks `@external_id`; no duplicate shirt.

### Duplicate Square webhook

One fulfillment job only.

### App offline for webhook

Provider retry and/or reconciliation repairs local state.

## Launch gate

- [ ] samples approved
- [ ] production Square payment tested
- [ ] production Printful fulfillment tested
- [ ] duplicate handling tested
- [ ] refund tested
- [ ] backup restore tested
- [ ] monitoring tested
- [ ] policies published
- [ ] mobile checkout tested
- [ ] major browser smoke test
- [ ] accessibility smoke test
