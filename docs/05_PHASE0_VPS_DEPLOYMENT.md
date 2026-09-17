# Phase 0 — VPS Deployment

## Domain

Canonical:

```text
https://blackmetalbuddha.com
```

Redirect `www`.

## Runtime

Recommended:

- Nginx
- FastAPI
- PostgreSQL
- systemd

Example app bind:

```text
127.0.0.1:8088
```

Only Nginx is internet-facing for the app.

## Example filesystem

```text
/opt/blackmetalbuddha/
/etc/blackmetalbuddha/blackmetalbuddha.env
/var/lib/blackmetalbuddha/
/var/log/blackmetalbuddha/
```

Run under a dedicated non-root account.

## Staging

Prefer:

```text
staging.blackmetalbuddha.com
```

Use:

- separate DB
- Square Sandbox
- test-safe Printful behavior

Protect staging from public indexing/access.

## Required secrets/config

```text
DATABASE_URL
APP_SECRET_KEY
PUBLIC_BASE_URL

SQUARE_APPLICATION_ID
SQUARE_LOCATION_ID
SQUARE_ACCESS_TOKEN
SQUARE_WEBHOOK_SIGNATURE_KEY
SQUARE_WEBHOOK_NOTIFICATION_URL

PRINTFUL_TOKEN
PRINTFUL_STORE_ID
PRINTFUL_WEBHOOK_SECRET_KEY

MAIL SETTINGS
```

No LNbits/Strike configuration is part of BMB.

## Backups

- nightly PostgreSQL dump
- encrypted off-host copy
- artwork backup
- restore test
- deployment rollback procedure
