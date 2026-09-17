# Square Integration Plan

## Launch scope

Square fiat checkout only.

Enable individually after merchant testing:

- card
- Apple Pay
- Google Pay
- Cash App Pay

## Browser flow

Square Web Payments SDK renders payment UI and creates a secure single-use token.

Browser sends:

- local order ID
- Square token
- buyer verification data where required

Browser does not send authoritative prices/totals.

## Server flow

1. Load order.
2. Require `PENDING_PAYMENT`.
3. Recalculate trusted total.
4. Get stable payment-attempt idempotency key.
5. Call Square `CreatePayment`.
6. Store Square payment ID.
7. Return safe result to browser.
8. Wait for trusted completed payment state before fulfillment.

## Webhooks

At minimum subscribe to:

- `payment.created`
- `payment.updated`

Handler:

1. preserve raw body
2. verify Square signature using official mechanism
3. reject invalid signature
4. deduplicate event ID
5. retrieve/reconcile Payment if needed
6. match local order
7. verify amount/currency/location/status
8. atomically transition payment state
9. enqueue fulfillment exactly once on `COMPLETED`
10. respond promptly

## Browser security

Square requires secure contexts and an appropriate CSP for Web Payments SDK. Keep CSP restrictive and add only documented Square origins.

## Refunds

Implement an owner/admin refund path before launch.

Payment refund and Printful cancellation are separate operations; refunding Square does not imply Printful production can still be stopped.

## Reconciliation

Run at least daily:

- stale `PENDING_PAYMENT`
- local `PAID` missing fulfillment
- Square completed payments not reflected locally

Do not rely exclusively on webhook delivery.

## Lightning

Out of scope until Square publishes supported developer access.
