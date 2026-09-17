# Phase 0 Storefront

This implementation makes Black Metal Buddha publishable as a pre-launch catalog site while intentionally keeping checkout disabled.

## Included

- FastAPI + Jinja2 server-rendered storefront
- home, shop, product, about, FAQ, cart, shipping/returns, privacy
- existing shirt mockups served directly from `black_metal_buddhist_prints/05_original_mockups`
- localStorage preview cart (no customer data sent to the server)
- human-readable UI typography with black/bone/red visual system
- responsive layout
- canonical metadata, OpenGraph basics, Organization/Product JSON-LD
- `robots.txt` and XML sitemap
- `/healthz`
- pytest smoke tests
- systemd and Nginx deployment examples
- checkout visibly disabled pending Phase 1

## Local run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install pytest httpx
PUBLIC_BASE_URL=http://127.0.0.1:8088 uvicorn app.main:app --reload --port 8088
```

## Test

```bash
pytest
```

## Production notes

The Nginx file deliberately omits certificate paths because the VPS already has its own certificate workflow. Add the existing certificate directives before enabling the vhost.

Do not enable checkout in Phase 0. Square and Printful credentials are intentionally absent from this implementation.
