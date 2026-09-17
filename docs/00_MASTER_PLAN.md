# Master Implementation Plan

## Success definition

Black Metal Buddha is ready for launch when:

- `https://blackmetalbuddha.com` is live on the VPS.
- The three launch products have approved physical samples.
- Product, size, price, shipping, and availability are server-controlled.
- Square payment data is tokenized client-side; card data never touches our backend.
- Square payment webhooks are verified.
- Only a trusted `COMPLETED` payment can trigger fulfillment.
- Paid orders are automatically submitted to Printful.
- Duplicate webhook delivery cannot cause duplicate charging or fulfillment.
- Printful shipment data updates the local order.
- Customers receive confirmation and tracking notifications.
- Failed/held Printful orders are surfaced.
- Backups, logs, monitoring, and restore procedures exist.
- A real production canary order has completed end-to-end.

## Phase 0 — site and infrastructure

Deliver:

- DNS for apex + `www`
- Nginx + HTTPS
- repository
- staging/production config separation
- PostgreSQL
- systemd app service
- health endpoint
- storefront pages: home, shop, product, cart, checkout shell, order status, about, shipping/returns, privacy, terms/contact
- local catalog

Exit: browsing/cart works on the production domain; real checkout is still disabled.

## Phase 0.5 — physical samples

- choose exact Printful blank
- map sizes/colors
- upload final art
- order one sample per design
- inspect line retention, small text, red reproduction, placement, fabric, fit, wash durability
- revise if needed
- shoot real product photos

Exit: each public SKU is physically approved.

## Phase 1 — Square + Printful

### Square

Use official Square Web Payments SDK + Payments API.

Initial methods may include:

- card
- Apple Pay
- Google Pay
- Cash App Pay

Lightning is not part of Phase 1.

### Fulfillment flow

1. Customer submits shipping/contact details.
2. Server recalculates cart from trusted catalog data.
3. Local order becomes `PENDING_PAYMENT`.
4. Browser obtains Square payment token.
5. Backend calls Square with a stable idempotency key.
6. Verified Square webhook reconciles payment state.
7. Require correct amount/currency and `COMPLETED`.
8. Atomically mark local order `PAID`.
9. Enqueue fulfillment exactly once.
10. Submit to Printful using BMB order number as `external_id`.
11. Store Printful IDs/state.
12. Signed Printful webhooks update production/shipping state.

Exit: one real order goes payment -> Printful -> shipment with no manual data transfer.

## Phase 2 — marketplaces

Recommended sequence:

1. Etsy
2. Amazon
3. eBay
4. TikTok Shop or another channel justified by demand

Use Printful native integrations where appropriate. Keep the direct BMB site canonical for the brand.

## Phase 3 — SEO and marketing

Technical SEO starts in Phase 0; traffic acquisition waits until fulfillment is proven.

Focus:

- original product photography
- structured product data
- sitemap/Search Console
- strong product copy
- editorial content
- marketplace SEO
- social content
- paid campaigns only after unit economics are known

## Future Lightning phase

Revisit only when Square officially supports programmatic online Lightning payments with trustworthy status/webhooks and automatic USD settlement.
