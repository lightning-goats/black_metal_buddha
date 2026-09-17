# Security and Privacy Requirements

## Payment scope

Use Square Web Payments SDK.

Never:

- build our own raw-card form
- log card numbers
- proxy raw card fields through backend
- store CVV
- expose secrets to browser code

## Webhooks

Verify both providers before trusted state changes.

- Square: official Square webhook signature verification
- Printful: v2 HMAC-SHA256 signed webhook verification

## Idempotency

Duplicates must not:

- charge twice
- fulfill twice
- send repeated customer messages
- corrupt state

Enforce uniqueness at database level as well as in code.

## Sessions/forms

- `Secure`
- `HttpOnly`
- appropriate `SameSite`
- CSRF protection
- server-side price calculation
- quantity limits

## CSP

Use restrictive CSP compatible with current Square requirements.

## PII

Store only operationally necessary customer data:

- email
- name
- shipping address
- optional phone only if genuinely required

Define a retention policy before launch.

## Logs

Never log:

- access tokens
- webhook secrets
- raw authorization headers
- payment-source tokens

Avoid routine shipping-address logging.

## Server

- SSH keys
- minimal firewall exposure
- unprivileged app
- non-public database
- timely security updates
- encrypted off-host backups

## Policies required before launch

- privacy
- shipping
- returns/refunds
- terms of sale
- contact method

Policies should accurately disclose Square processing and Printful fulfillment.
