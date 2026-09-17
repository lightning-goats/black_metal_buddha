# Security and Privacy

## Payment handling

Square hosts checkout. Do not store or proxy raw card information.

## Webhooks

### Square

Verify Square's official webhook signature before processing.

### Printful

Verify the current Printful signed-webhook format before processing.

## Idempotency

Database constraints and provider idempotency must prevent:

- duplicate checkout/payment-link operations
- duplicate payment processing
- duplicate Printful orders
- repeated customer notifications

## PII

Store only what fulfillment requires. Avoid unnecessary customer profiles and do not routinely log full shipping details.

## Secrets

Never expose or commit:

- Square access token
- Square webhook secret
- Printful token
- application secret
- DB credentials

## Application

- CSRF protection
- secure cookies
- rate limiting where useful
- trusted server-side totals
- quantity limits
- restrictive security headers
- safe error handling

## Server

- SSH keys
- non-root service
- firewall
- non-public DB
- timely security updates
- off-host backups
