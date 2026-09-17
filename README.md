# Black Metal Buddha

Planning and implementation repository for `blackmetalbuddha.com`.

## Current architecture decision

Black Metal Buddha owns its own storefront, cart, order database, Square integration, and Printful fulfillment.

- **Square fiat checkout is the launch payment path.**
- **Printful is the launch fulfillment provider.**
- **LNbits and Strike are not part of the Black Metal Buddha payment architecture.**
- **Lightning is explicitly on hold** until Square provides an official API that can accept Lightning for an online order, report payment status reliably, and automatically settle proceeds into fiat/USD without manual conversion.

## Phases

- **Research:** verify current Square and Printful APIs and limitations
- **Phase 0:** deploy the Black Metal Buddha website on the VPS
- **Phase 0.5:** approve physical samples
- **Phase 1:** Square fiat checkout + fully automated Printful fulfillment
- **Phase 2:** expand to Printful-supported marketplaces/ecommerce platforms
- **Phase 3:** SEO, content, analytics, and marketing
- **Future Lightning:** only after the Square API satisfies the automated Lightning-to-fiat requirement

See `docs/`.
