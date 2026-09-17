# Black Metal Buddha — Project Planning Package

**Domain:** `blackmetalbuddha.com`  
**Planning date:** 2026-09-17  
**Primary storefront:** self-hosted on the existing VPS  
**Payments:** Square fiat payments at launch  
**Fulfillment:** Printful  
**Lightning:** deferred until Square exposes a supported Bitcoin/Lightning API suitable for online checkout

## Goal

Launch a small, automated print-on-demand ecommerce site. A customer selects a product, pays through Square, and the order is submitted to Printful without manual transfer.

## Launch collection

1. **Lotus of the Void** — *No Self • No Fear*
2. **Dharma of Decay** — *All Things Pass*
3. **Meditate on Death** — *Emptiness Is Freedom*

## Phases

- **Research:** Square + Printful capabilities
- **Phase 0:** deploy `blackmetalbuddha.com` on the VPS
- **Phase 0.5:** order and approve physical samples
- **Phase 1:** Square fiat checkout + automated Printful fulfillment
- **Phase 2:** add Printful-supported marketplaces/ecommerce channels
- **Phase 3:** SEO, content, analytics, and marketing
- **Future:** add Square Lightning only when an official API supports it

## Recommended reference stack

- Nginx
- Python + FastAPI
- Jinja2 templates
- Minimal browser JavaScript
- Square Web Payments SDK on checkout
- PostgreSQL
- systemd
- Printful API + signed v2 webhooks
- Square signed webhooks

Containerization is optional.

## Launch non-goals

- customer accounts
- saved cards
- loyalty
- custom product designer
- subscriptions
- cryptocurrency custody
- custom Lightning node integration
- native mobile app
