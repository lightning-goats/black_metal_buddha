from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.text == "ok"


def test_home_has_seo_products_and_branding():
    response = client.get("/")
    assert response.status_code == 200
    assert "<title>Black Metal Buddha" in response.text
    assert 'rel="canonical"' in response.text
    assert "/static/brand/black-metal-buddha-logo.webp" in response.text
    assert '"@type": "Organization"' in response.text
    assert '"@type": "WebSite"' in response.text
    assert '"logo": "https://blackmetalbuddha.com/static/brand/black-metal-buddha-logo.webp"' in response.text
    assert "Lotus of the Void" in response.text
    assert "Dharma of Decay" in response.text
    assert "Meditate on Death" in response.text


def test_logo_asset_is_served():
    response = client.get("/static/brand/black-metal-buddha-logo.webp")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("image/webp")
    assert len(response.content) > 1000


def test_product_schema():
    response = client.get("/products/lotus-of-the-void")
    assert response.status_code == 200
    assert 'application/ld+json' in response.text
    assert '"@type": "Product"' in response.text
    assert "Checkout is intentionally disabled" in response.text


def test_branded_404_is_noindex():
    response = client.get("/products/does-not-exist")
    assert response.status_code == 404
    assert "Nothing remains here." in response.text
    assert 'content="noindex,nofollow"' in response.text


def test_robots_and_sitemap():
    robots = client.get("/robots.txt")
    assert robots.status_code == 200
    assert "Disallow: /cart" in robots.text
    sitemap = client.get("/sitemap.xml")
    assert sitemap.status_code == 200
    assert "/products/meditate-on-death" in sitemap.text


def test_security_headers():
    response = client.get("/")
    assert response.headers["x-content-type-options"] == "nosniff"
    assert "script-src 'self' 'nonce-" in response.headers["content-security-policy"]
    assert 'nonce="' in response.text


def test_checkout_is_hidden_while_phase1_disabled():
    response = client.get("/checkout")
    assert response.status_code == 404


def test_robots_blocks_transactional_utility_paths():
    response = client.get("/robots.txt")
    assert "Disallow: /checkout" in response.text
    assert "Disallow: /orders/" in response.text
    assert "Disallow: /admin" in response.text
    assert "Disallow: /api/" in response.text


def test_admin_is_hidden_when_not_configured():
    response = client.get("/admin")
    assert response.status_code == 404
