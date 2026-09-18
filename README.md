# Black Metal Buddha

Self-hosted storefront and ecommerce backend for blackmetalbuddha.com.

## Architecture

Black Metal Buddha owns its storefront, catalog, cart, order database, Square integration, and Printful fulfillment orchestration.

- **Square fiat checkout** is the launch payment path.
- **Printful** is the launch fulfillment provider.
- **LNbits and Strike are not dependencies** of this project.
- **Lightning remains deferred** until Square exposes an official online API that can accept Lightning and automatically settle the merchant side to fiat/USD without manual conversion.

## Implementation status

### Phase 0 — storefront

Implemented:

- responsive Black Metal Buddha storefront
- approved Dzogchen-A black-metal identity
- three launch-design pages
- SEO metadata, structured data, sitemap, robots rules
- security headers and deployment configuration
- preview mode while transactional launch gates are closed

### Phase 0.5 — physical product validation

**In progress.** The first physical test print has been ordered.

Public production checkout remains gated on final physical approval, production SKU mapping, and final pricing.

See docs/16_PHASE0_5_SAMPLE_VALIDATION.md.

### Phase 1 — Square + Printful ecommerce

Software implementation is substantially complete:

- database-backed sellable variants and prices
- customer size/quantity cart
- shipping-address checkout
- live Printful shipping quotes
- Square-hosted checkout
- Square tax synchronization and payment webhooks
- durable orders, jobs, refunds, shipments, and audit logs
- Printful draft + gated production confirmation
- exactly-once / external-ID fulfillment protections
- split-shipment tracking and customer status pages
- transactional email jobs
- provider reconciliation
- owner/admin console
- catalog management and approved-catalog SHA-256 fingerprint
- controlled live production canary
- production launch fail-closed gates
- PostgreSQL backups and restore-verification tooling
- deployment and operational smoke tests

**All real-sales gates remain OFF by default.**

See docs/19 through docs/24 for the Phase 1 implementation and launch runbooks.

## Safe defaults

The example configuration deliberately does not permit a real transaction:

~~~
PHASE1_API_ENABLED=false
PRODUCTION_CHECKOUT_ENABLED=false
PHASE0_5_APPROVED=false
PRODUCTION_CATALOG_APPROVED=false
PRODUCTION_CANARY_APPROVED=false
PRODUCTION_CANARY_MODE=false
PRINTFUL_MODE=disabled
PRINTFUL_CONFIRM_ENABLED=false
ADMIN_REFUNDS_ENABLED=false
ADMIN_CANCEL_FULFILLMENT_ENABLED=false
~~~

Do not bypass launch validation. Use the controlled canary and launch runbook.

## Development

~~~bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt pytest
APP_ENV=development DATABASE_URL=sqlite:///./dev.db alembic upgrade head
APP_ENV=development DATABASE_URL=sqlite:///./dev.db uvicorn app.main:app --reload --port 8088
~~~

Run the test suite:

~~~bash
pytest -q
~~~

## Roadmap

- **Phase 0:** storefront — implemented
- **Phase 0.5:** physical samples — in progress
- **Phase 1:** Square + Printful software — implemented, awaiting physical/canary launch gates
- **Phase 2:** Printful-supported marketplaces/ecommerce channels
- **Phase 3:** SEO/content/marketing expansion
- **Future Lightning:** only when Square provides the required automated Lightning-to-fiat API flow
