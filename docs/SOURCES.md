# Technical Sources Checked

Research date: **2026-09-17**

Recheck during implementation because APIs evolve.

## Square

- https://developer.squareup.com/reference/sdks/web/payments
- https://developer.squareup.com/docs/web-payments/overview
- https://developer.squareup.com/docs/web-payments/quickstart
- https://developer.squareup.com/docs/payments-refunds
- https://developer.squareup.com/reference/square/payments/create-payment
- https://developer.squareup.com/docs/webhooks/overview
- https://developer.squareup.com/docs/payments-api/webhooks
- https://developer.squareup.com/reference/square

## Printful

- https://developers.printful.com/docs/
- https://developers.printful.com/docs/v2-preview/
- https://www.printful.com/integrations/etsy
- https://www.printful.com/integrations/amazon
- https://www.printful.com/integrations/ebay

## Verified planning facts

At the research date:

- Square Web Payments SDK supports card, ACH, Apple Pay, Google Pay, gift card, Afterpay/Clearpay, and Cash App Pay.
- Square requires a secure context and appropriate CSP for Web Payments SDK.
- Payments API exposes payment-created/updated webhooks.
- Printful Orders API supports unique `external_id` and lookup by `@external_id`.
- Printful can create and confirm orders for fulfillment.
- Printful orders can fail/hold/return to draft and need reconciliation.
- Printful v2 webhooks support HMAC-SHA256 event signing.
- Printful directly integrates with Etsy, Amazon, and eBay.
