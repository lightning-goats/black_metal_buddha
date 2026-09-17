# ADR-001 — Lightning Deferred Until Square Provides Automated Fiat Settlement

**Status:** Accepted  
**Date:** 2026-09-17

## Requirement

Black Metal Buddha eventually wants to offer Lightning payments, potentially with a 10% discount.

However, the required production flow is:

```text
customer Lightning payment
        ↓
Square
        ↓
automatic fiat/USD settlement
        ↓
normal BMB paid-order flow
        ↓
Printful
```

There must be **no manual BTC-to-USD conversion** and no human step required before Printful fulfillment.

## Current limitation

Square supports Bitcoin/Lightning in first-party Square products, but its public custom-ecommerce APIs do not currently expose the complete programmatic Lightning checkout flow required by BMB.

## Decision

Do not implement Lightning through:

- LNbits
- Strike
- Core Lightning
- BTCPay
- another crypto processor
- undocumented Square endpoints
- external crypto payments merely recorded in Square

These approaches do not satisfy the project's required Square-mediated automated Lightning-to-fiat flow.

## Revisit criteria

Reopen Lightning implementation only when Square officially provides APIs that can:

1. create/initiate an online Lightning payment
2. tie it to the BMB/Square order
3. report payment status via trustworthy API/webhook events
4. automatically settle proceeds to USD/fiat
5. integrate without manual conversion before Printful fulfillment

## Future UX

When all criteria are met:

```text
Card / wallet:      $40.00
Lightning:          $36.00
                    Save 10%
```

The discount must be calculated server-side.

Until then, no Lightning payment option should be shown on the BMB storefront.
