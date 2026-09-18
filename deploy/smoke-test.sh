#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${1:-https://blackmetalbuddha.com}"
BASE_URL="${BASE_URL%/}"

fail() {
  printf 'FAIL: %s\n' "$*" >&2
  exit 1
}

printf 'Smoke testing %s\n' "$BASE_URL"

health="$(curl -fsS "$BASE_URL/healthz")"
[[ "$health" == "ok" ]] || fail "health endpoint did not return ok"

home="$(curl -fsS "$BASE_URL/")"
grep -q "Black Metal Buddha" <<<"$home" || fail "homepage branding missing"
grep -q "/static/brand/black-metal-buddha-logo.webp" <<<"$home" || fail "approved logo missing from homepage"
grep -q 'application/ld+json' <<<"$home" || fail "structured data missing"

headers="$(curl -fsSI "$BASE_URL/" | tr -d '\r')"
grep -qi '^x-content-type-options: nosniff$' <<<"$headers" || fail "nosniff header missing"
grep -qi '^content-security-policy:' <<<"$headers" || fail "Content-Security-Policy missing"

logo_headers="$(curl -fsSI "$BASE_URL/static/brand/black-metal-buddha-logo.webp" | tr -d '\r')"
grep -qi '^content-type: image/webp' <<<"$logo_headers" || fail "logo content type is not image/webp"

robots="$(curl -fsS "$BASE_URL/robots.txt")"
grep -q 'Sitemap:' <<<"$robots" || fail "robots sitemap declaration missing"

sitemap="$(curl -fsS "$BASE_URL/sitemap.xml")"
grep -q '/products/lotus-of-the-void' <<<"$sitemap" || fail "product missing from sitemap"

product="$(curl -fsS "$BASE_URL/products/lotus-of-the-void")"
grep -q 'Checkout is intentionally disabled' <<<"$product" || fail "Phase 0 checkout guard missing"

printf 'PASS: Phase 0 storefront is healthy.\n'
