# Testing and Release

## Square tests

Use Square Sandbox.

Test:

- payment-link creation
- idempotent retry
- successful payment
- declined/abandoned checkout
- duplicate webhook
- invalid webhook signature
- webhook before customer returns
- customer never returns
- amount mismatch
- currency mismatch
- delayed webhook
- reconciliation repair

## Printful tests

Test safely before production:

- create draft
- confirm
- duplicate external ID
- timeout after create
- failed/held state
- duplicate webhook
- shipment update

## Critical invariant

A customer returning from Square must never be enough to mark an order paid.

Only authoritative Square state can do that.

## Production canary

1. place one real order
2. verify Square order/payment IDs
3. verify Square payment `COMPLETED`
4. verify BMB order `PAID`
5. verify exactly one Printful order
6. verify production
7. verify shipment/tracking
8. verify reconciliation

## Launch gate

- [ ] physical samples approved
- [ ] Square production canary
- [ ] Printful production canary
- [ ] refund flow
- [ ] duplicate protections
- [ ] failed fulfillment alert
- [ ] backup restore
- [ ] policies
- [ ] mobile checkout
- [ ] accessibility smoke test
