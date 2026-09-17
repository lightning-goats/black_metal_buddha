# Printful Integration Plan

## Authentication

Use a Printful **Private Token** for our own store. Keep it server-side and scope it as narrowly as practical.

## Catalog

Use preconfigured Printful products/variants.

For every sellable BMB SKU verify:

- exact garment
- color
- size
- print placement
- print file
- current availability
- Printful variant mapping

## Fulfillment

1. BMB order becomes `PAID`.
2. Enqueue `SUBMIT_PRINTFUL_ORDER`.
3. Check for existing Printful order using BMB `external_id`.
4. If none exists, create order.
5. Confirm for fulfillment.
6. Store Printful ID and status.
7. Signed webhooks update state.

For initial production, create then explicitly confirm for easier auditability. Later a create-with-confirm path is acceptable.

## External ID

Use BMB order number:

```text
BMB-000041
```

Printful supports unique external IDs and retrieval by:

```text
GET /orders/@BMB-000041
```

## Holds/failures

Printful orders can enter review/hold/failure states or return to draft.

Never assume API acceptance means production has started.

## Webhooks

Use **Printful Webhook v2** and verify its HMAC-SHA256 event signature.

Validate:

- `x-pf-webhook-public-key`
- `x-pf-webhook-signature`

Subscribe to relevant order/hold/shipment/return events after checking the exact current v2 names during implementation.

## Shipping

Choose and document one deterministic launch strategy before payment capture:

- BMB flat-rate rules, or
- server-side Printful rate/cost estimation

## Billing

Printful charges our configured billing source when an order is submitted.

Monitor:

- billing-source validity
- failed charges
- paid customer orders blocked from fulfillment

## Reconciliation

Regularly find:

- `PAID` without Printful order
- Printful `failed`
- Printful hold/draft regressions
- Printful shipped but local not shipped
- missing tracking
