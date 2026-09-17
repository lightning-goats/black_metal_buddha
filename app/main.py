from __future__ import annotations

import json
import os
import secrets
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import PlainTextResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .catalog import PRODUCT_BY_SLUG, PRODUCTS

ROOT = Path(__file__).resolve().parents[1]
BASE_URL = os.getenv("PUBLIC_BASE_URL", "https://blackmetalbuddha.com").rstrip("/")
SITE_NAME = "Black Metal Buddha"
DEFAULT_DESCRIPTION = (
    "Black Metal Buddha creates dark ritual apparel inspired by impermanence, mortality, "
    "non-self, and contemplative Buddhist themes."
)

app = FastAPI(
    title=SITE_NAME,
    docs_url=None if os.getenv("APP_ENV") == "production" else "/docs",
    redoc_url=None,
)

app.mount("/static", StaticFiles(directory=ROOT / "app" / "static"), name="static")
app.mount(
    "/prints",
    StaticFiles(directory=ROOT / "black_metal_buddhist_prints" / "05_original_mockups"),
    name="prints",
)

templates = Jinja2Templates(directory=ROOT / "app" / "templates")


@app.middleware("http")
async def security_headers(request: Request, call_next):
    nonce = secrets.token_urlsafe(18)
    request.state.csp_nonce = nonce
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "img-src 'self' data:; "
        "style-src 'self'; "
        f"script-src 'self' 'nonce-{nonce}'; "
        "base-uri 'self'; frame-ancestors 'none'; form-action 'self'"
    )
    return response


def page_context(request: Request, **kwargs):
    return {
        "request": request,
        "site_name": SITE_NAME,
        "base_url": BASE_URL,
        "default_description": DEFAULT_DESCRIPTION,
        "products": PRODUCTS,
        **kwargs,
    }


@app.get("/healthz", response_class=PlainTextResponse, include_in_schema=False)
def healthz() -> str:
    return "ok"


@app.get("/", include_in_schema=False)
def home(request: Request):
    organization_schema = {
        "@context": "https://schema.org",
        "@type": "Organization",
        "name": SITE_NAME,
        "url": f"{BASE_URL}/",
        "description": DEFAULT_DESCRIPTION,
    }
    return templates.TemplateResponse(
        request,
        "home.html",
        page_context(
            request,
            title="Black Metal Buddha | Ritual Apparel for a Fleeting World",
            description=DEFAULT_DESCRIPTION,
            canonical=f"{BASE_URL}/",
            structured_data=json.dumps(organization_schema),
        ),
    )


@app.get("/shop", include_in_schema=False)
def shop(request: Request):
    return templates.TemplateResponse(
        request,
        "shop.html",
        page_context(
            request,
            title="Shop Black Metal Buddha | Dark Buddhist-Inspired Apparel",
            description=(
                "Explore the Black Metal Buddha launch collection: Lotus of the Void, "
                "Dharma of Decay, and Meditate on Death."
            ),
            canonical=f"{BASE_URL}/shop",
        ),
    )


@app.get("/products/{slug}", include_in_schema=False)
def product_detail(request: Request, slug: str):
    product = PRODUCT_BY_SLUG.get(slug)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")

    product_schema = {
        "@context": "https://schema.org",
        "@type": "Product",
        "name": product.name,
        "description": product.description,
        "sku": product.sku,
        "brand": {"@type": "Brand", "name": SITE_NAME},
        "image": [f"{BASE_URL}{product.image}"],
        "url": f"{BASE_URL}/products/{product.slug}",
    }
    return templates.TemplateResponse(
        request,
        "product.html",
        page_context(
            request,
            product=product,
            title=f"{product.name} | Black Metal Buddha",
            description=product.summary,
            canonical=f"{BASE_URL}/products/{product.slug}",
            structured_data=json.dumps(product_schema),
        ),
    )


@app.get("/about", include_in_schema=False)
def about(request: Request):
    return templates.TemplateResponse(
        request,
        "about.html",
        page_context(
            request,
            title="About Black Metal Buddha | Art, Impermanence, and Ritual Apparel",
            description=(
                "About Black Metal Buddha, an independent apparel project exploring impermanence, "
                "mortality, non-self, and contemplative symbolism through black-metal visual language."
            ),
            canonical=f"{BASE_URL}/about",
        ),
    )


@app.get("/faq", include_in_schema=False)
def faq(request: Request):
    return templates.TemplateResponse(
        request,
        "faq.html",
        page_context(
            request,
            title="FAQ | Black Metal Buddha",
            description="Answers about Black Metal Buddha products, printing, shipping, and launch status.",
            canonical=f"{BASE_URL}/faq",
        ),
    )


@app.get("/cart", include_in_schema=False)
def cart(request: Request):
    return templates.TemplateResponse(
        request,
        "cart.html",
        page_context(
            request,
            title="Cart | Black Metal Buddha",
            description="Black Metal Buddha shopping cart.",
            canonical=f"{BASE_URL}/cart",
            robots="noindex,nofollow",
        ),
    )


@app.get("/shipping-returns", include_in_schema=False)
def shipping_returns(request: Request):
    return templates.TemplateResponse(
        request,
        "shipping_returns.html",
        page_context(
            request,
            title="Shipping & Returns | Black Metal Buddha",
            description="Black Metal Buddha shipping and returns information for the pre-launch storefront.",
            canonical=f"{BASE_URL}/shipping-returns",
        ),
    )


@app.get("/privacy", include_in_schema=False)
def privacy(request: Request):
    return templates.TemplateResponse(
        request,
        "privacy.html",
        page_context(
            request,
            title="Privacy | Black Metal Buddha",
            description="Black Metal Buddha privacy information.",
            canonical=f"{BASE_URL}/privacy",
        ),
    )


@app.get("/robots.txt", response_class=PlainTextResponse, include_in_schema=False)
def robots() -> str:
    return f"User-agent: *\nAllow: /\nDisallow: /cart\nSitemap: {BASE_URL}/sitemap.xml\n"


@app.get("/sitemap.xml", include_in_schema=False)
def sitemap() -> Response:
    paths = ["/", "/shop", "/about", "/faq", "/shipping-returns", "/privacy"]
    paths.extend(f"/products/{product.slug}" for product in PRODUCTS)
    urls = "".join(f"<url><loc>{BASE_URL}{path}</loc></url>" for path in paths)
    xml = f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>'
    return Response(content=xml, media_type="application/xml")
