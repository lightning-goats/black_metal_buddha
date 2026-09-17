# Phase 0 — VPS Deployment

## DNS

```text
A/AAAA blackmetalbuddha.com -> VPS
A/AAAA www.blackmetalbuddha.com -> VPS
```

Only publish AAAA if IPv6 is actually reachable.

Canonical hostname recommendation:

```text
https://blackmetalbuddha.com
```

Redirect `www`.

## Example layout

```text
/opt/blackmetalbuddha/
  app/
  venv/
  releases/
  shared/

/etc/blackmetalbuddha/
  blackmetalbuddha.env

/var/lib/blackmetalbuddha/
/var/log/blackmetalbuddha/
```

## Service account

Run as an unprivileged dedicated user:

```text
blackmetalbuddha
```

## App service

systemd-managed app:

- localhost-only bind, e.g. `127.0.0.1:8088`
- restart on failure
- environment file
- non-root user
- compatible systemd hardening

## Nginx

Provide:

- TLS
- HTTP->HTTPS
- canonical host redirect
- reverse proxy
- static assets
- security headers
- webhook paths
- access/error logs
- reasonable rate limits

## PostgreSQL

- dedicated database/user
- non-public bind
- nightly logical backup
- encrypted off-host copy
- periodic restore test

## Expected configuration

```text
APP_ENV
APP_SECRET_KEY
DATABASE_URL

SQUARE_ENVIRONMENT
SQUARE_APPLICATION_ID
SQUARE_LOCATION_ID
SQUARE_ACCESS_TOKEN
SQUARE_WEBHOOK_SIGNATURE_KEY
SQUARE_WEBHOOK_NOTIFICATION_URL

PRINTFUL_TOKEN
PRINTFUL_STORE_ID
PRINTFUL_WEBHOOK_PUBLIC_KEY
PRINTFUL_WEBHOOK_SECRET_KEY

PUBLIC_BASE_URL
MAIL/NOTIFICATION SETTINGS
```

Never commit secret values.

## Staging

Prefer:

```text
staging.blackmetalbuddha.com
```

Protect it. Use separate DB and Square Sandbox. Prevent accidental production Printful fulfillment.

## Phase 0 checklist

- [ ] DNS
- [ ] TLS
- [ ] redirects
- [ ] repo
- [ ] Python env
- [ ] PostgreSQL
- [ ] migrations
- [ ] systemd
- [ ] Nginx
- [ ] health endpoint
- [ ] staging
- [ ] secret handling
- [ ] backup job
- [ ] restore test
- [ ] deploy/rollback procedure
