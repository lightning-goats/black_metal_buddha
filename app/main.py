from __future__ import annotations

import json
import os
import secrets
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import PlainTextResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.exceptions import HTTPException as StarletteHTTPException

from .api_phase1 import router as phase1_router
from .catalog import PRODUCT_BY_SLUG, PRODUCTS
from .db import SessionLocal, init_db
from .orders import get_order
from .settings import settings as phase1_settings

ROOT = Path(__file__).resolve().parents[1]
BASE_URL = os.getenv("PUBLIC_BASE_URL", "https://blackmetalbuddha.com").rstrip("/")
SITE_NAME = "Black Metal Buddha"
LOGO_PATH = "/static/brand/black-metal-buddha-logo.webp"
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
app.include_router(phase1_router)


@app.on_event("startup")
def phase1_dev_database_bootstrap() -> None:
    # Production schema changes are applied with Alembic. Development and tests
    # may auto-create the foundation schema for convenience.
    if phase1_settings.app_env != "production":
        init_db()


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
        "logo_path": LOGO_PATH,
        "default_description": DEFAULT_DESCRIPTION,
        "products": PRODUCTS,
        **kwargs,
    }


@app.exception_handler(StarletteHTTPException)
async def http_error_page(request: Request, exc: StarletteHTTPException):
    if exc.status_code == 404:
        return templates.TemplateResponse(
            request,
            "404.html",
            page_context(
                request,
                title="Page Not Found | Black Metal Buddha",
                description="The requested Black Metal Buddha page could not be found.",
                canonical=f"{BASE_URL}{request.url.path}",
                robots="noindex,nofollow",
            ),
            status_code=404,
        )
    return PlainTextResponse(str(exc.detail), status_code=exc.status_code)


@app.get("/healthz", response_class=PlainTextResponse, include_in_schema=False)
def healthz() -> str:
    return "ok"


@app.get("/", include_in_schema=False)
def home(request: Request):
    structured_data = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "Organization",
                "@id": f"{BASE_URL}/#organization",
                "name": SITE_NAME,
                "url": f"{BASE_URL}/",
                "logo": f"{BASE_URL}{LOGO_PATH}",
                "description": DEFAULT_DESCRIPTION,
            },
            {
                "@type": "WebSite",
                "@id": f"{BASE_URL}/#website",
                "url": f"{BASE_URL}/",
                "name": SITE_NAME,
                "publisher": {"@id": f"{BASE_URL}/#organization"},
                "description": DEFAULT_DESCRIPTION,
            },
        ],
    }
    return templates.TemplateResponse(
        request,
        "home.html",
        page_context(
            request,
            title="Black Metal Buddha | Ritual Apparel for a Fleeting World",
            description=DEFAULT_DESCRIPTION,
            canonical=f"{BASE_URL}/",
            structured_data=json.dumps(structured_data),
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


@app.get("/orders/{order_number}", include_in_schema=False)
def order_status(request: Request, order_number: str):
    if not phase1_settings.phase1_api_enabled:
        raise HTTPException(status_code=404, detail="Order status unavailable")

    with SessionLocal() as session:
        order = get_order(session, order_number)
        if order is None:
            raise HTTPException(status_code=404, detail="Order not found")

        if order.order_state == "PAID":
            heading = "Payment received."
            message = "Your payment is confirmed. Fulfillment is queued."
        elif order.order_state in {"FULFILLMENT_SUBMITTED", "IN_PRODUCTION"}:
            heading = "Your order is being prepared."
            message = "Payment is confirmed and fulfillment is in progress."
        elif order.order_state == "SHIPPED":
            heading = "Your order has shipped."
            message = "Shipment information will be added as the fulfillment integration is completed."
        elif order.order_state == "PAYMENT_FAILED":
            heading = "Payment was not completed."
            message = "No fulfillment will occur for this order."
        else:
            heading = "Payment pending."
            message = "If you just completed Square checkout, this page will update after payment confirmation."

        return templates.TemplateResponse(
            request,
            "order_status.html",
            page_context(
                request,
                order=order,
                status_heading=heading,
                status_message=message,
                title=f"Order {order.order_number} | Black Metal Buddha",
                description="Black Metal Buddha order status.",
                canonical=f"{BASE_URL}/orders/{order.order_number}",
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
