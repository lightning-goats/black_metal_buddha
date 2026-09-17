from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.text == "ok"


def test_home_has_seo_and_products():
    response = client.get("/")
    assert response.status_code == 200
    assert "<title>Black Metal Buddha" in response.text
    assert 'rel="canonical"' in response.text
    assert "Lotus of the Void" in response.text
    assert "Dharma of Decay" in response.text
    assert "Meditate on Death" in response.text


def test_product_schema():
    response = client.get("/products/lotus-of-the-void")
    assert response.status_code == 200
    assert 'application/ld+json' in response.text
    assert '"@type": "Product"' in response.text
    assert "Checkout is intentionally disabled" in response.text


def test_robots_and_sitemap():
    robots = client.get("/robots.txt")
    assert robots.status_code == 200
    assert "Disallow: /cart" in robots.text
    sitemap = client.get("/sitemap.xml")
    assert sitemap.status_code == 200
    assert "/products/meditate-on-death" in sitemap.text
