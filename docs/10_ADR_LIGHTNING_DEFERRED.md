# ADR-001 — Defer Lightning Checkout

**Status:** Accepted  
**Date:** 2026-09-17

## Context

Black Metal Buddha eventually intends to offer a 10% Lightning discount.

Square supports Bitcoin/Lightning in first-party seller products and can settle eligible Bitcoin payments into USD, but its current public custom-online-payment interfaces do not expose Lightning as a Web Payments SDK / Payments API source.

The project requires fully automated fulfillment and no manual BTC-to-USD conversion.

## Decision

Lightning is deferred.

Phase 1 uses official Square fiat-capable APIs only.

We will not:

- reverse engineer undocumented Square endpoints
- accept Lightning through our own CLN node for launch
- add a second crypto processor during launch

## Revisit trigger

Reopen when Square officially supports:

1. programmatic online Lightning initiation
2. reliable USD-denominated reconciliation
3. trustworthy payment status/webhooks
4. automatic USD settlement

## Intended future pricing

```text
Card:       $40.00
Lightning:  $36.00
```

The 10% discount must be server-calculated.
